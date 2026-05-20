#!/usr/bin/env python3
"""R2 daily backup (jsonl.gz) → 新 Postgres DB 復元 standalone script。

2026-05-20 Railway 全体障害から学んだ「真の DR」の completion 半分。
server/main.py の `_dump_db_to_jsonl_gz()` が生成した backup を、別 hosting
(Supabase / Neon / Crunchy 等 managed Postgres) の新 DB に restore する。

Usage:
  # 1. 新 Postgres に init_db() で先に schema 構築
  DATABASE_URL='postgresql://...' python3 -c "
  import sys; sys.path.insert(0, 'server')
  import main; main.init_db()
  "
  # 2. R2 から最新 backup を local DL
  # 3. restore (dry-run 推奨)
  DATABASE_URL='postgresql://...' python3 server/restore_from_jsonl.py /path/to/db-X.jsonl.gz --dry-run
  # 4. 本番 restore
  DATABASE_URL='postgresql://...' python3 server/restore_from_jsonl.py /path/to/db-X.jsonl.gz

Critical fix from 3-視点 review (2026-05-20):
  1. **psycopg3 transaction abort**: per-row エラーで transaction 全体が abort される
     仕様 → `conn.autocommit=True` + 各 row 個別 INSERT で savepoint 化なしに対応
  2. **Supabase session_replication_role 権限なし**: managed Postgres の postgres user は
     rolsuper=false で SET session_replication_role 不可 → try/except で fallback +
     FK 順序を topological sort (parent table 先) で解決
  3. **jsonb dict auto-adapt 不可**: psycopg3 は bare dict を jsonb として cast せず
     → `Jsonb(v) if isinstance(v, (dict, list)) else v` で明示 wrap

Flow:
  1. gz decode + JSONL parse (-- skip)
  2. table 別 group (FK 依存解決のため全件 buffer)
  3. 各 table の FK 列を information_schema から取得 → topological sort で table 順序決定
  4. session_replication_role='replica' を試行 (権限 OK なら FK disable・NG なら fallback)
  5. autocommit=True で各 row 独立 INSERT (jsonb は Jsonb wrap)
  6. SET session_replication_role='origin' に戻す (試行成功時のみ)
  7. SERIAL/IDENTITY 列で setval(MAX(col)) — sequence reset
"""
import gzip
import json
import os
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Set

try:
    import psycopg
    from psycopg import sql as psql_sql
    from psycopg.types.json import Jsonb
except ImportError:
    print('ERROR: psycopg not installed. Run: pip install "psycopg[binary]"')
    sys.exit(1)


SAFE_IDENT = re.compile(r'^[a-z_][a-z0-9_]*$')


def parse_jsonl_gz(path: str) -> Dict[str, List[Dict[str, Any]]]:
    """gz decode + JSONL parse → {table_name: [row_dict, ...]}"""
    tables: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    skipped_lines = 0
    total = 0
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f'  [warn] line {line_no} parse error: {e}', file=sys.stderr)
                skipped_lines += 1
                continue
            t = rec.get('_table')
            data = rec.get('_data')
            if not t or not isinstance(data, dict):
                skipped_lines += 1
                continue
            if not SAFE_IDENT.match(t):
                print(f'  [warn] line {line_no} unsafe table name: {t!r}', file=sys.stderr)
                skipped_lines += 1
                continue
            tables[t].append(data)
            total += 1
    print(f'parsed: {len(tables)} tables, {total} rows ({skipped_lines} lines skipped)')
    return dict(tables)


def get_fk_dependencies(conn) -> Dict[str, Set[str]]:
    """各 table の参照先 (parent) table 集合を返す。
    {child_table: {parent_table_1, parent_table_2}}"""
    deps: Dict[str, Set[str]] = defaultdict(set)
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tc.table_name AS child, ccu.table_name AS parent
            FROM information_schema.table_constraints tc
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
              AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name != ccu.table_name  -- self-ref は無視
        """)
        for child, parent in cur.fetchall():
            if SAFE_IDENT.match(child) and SAFE_IDENT.match(parent):
                deps[child].add(parent)
    finally:
        cur.close()
    return dict(deps)


def topological_sort(tables: List[str], deps: Dict[str, Set[str]]) -> List[str]:
    """Kahn's algorithm: parent table 先 → child table 後の順序を返す。
    循環依存があれば残った table をそのまま末尾に追加。"""
    # in-degree = この table が依存する未処理 parent 数
    table_set = set(tables)
    in_deg = {t: len(deps.get(t, set()) & table_set) for t in tables}
    result: List[str] = []
    # 親が無い (in_deg=0) から処理
    queue = [t for t in tables if in_deg[t] == 0]
    queue.sort()  # determinism
    visited: Set[str] = set()
    while queue:
        t = queue.pop(0)
        if t in visited:
            continue
        visited.add(t)
        result.append(t)
        # この t を parent とする child の in_deg を減らす
        for child in tables:
            if child in visited:
                continue
            if t in deps.get(child, set()):
                in_deg[child] -= 1
                if in_deg[child] == 0:
                    queue.append(child)
                    queue.sort()
    # 残り (循環依存) は末尾に追加
    for t in tables:
        if t not in visited:
            result.append(t)
    return result


def _wrap_jsonb(v: Any) -> Any:
    """psycopg3 は bare dict/list を jsonb として auto-cast せず ProgrammingError。
    明示的に Jsonb() で wrap する。string や int 等は素通り。"""
    if isinstance(v, (dict, list)):
        return Jsonb(v)
    return v


def restore_table(conn, table: str, rows: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """1 table を ON CONFLICT DO NOTHING で INSERT。inserted 件数を返す。
    psycopg3 の transaction abort 対策で **autocommit 前提 + per-row 独立** INSERT。"""
    if not rows:
        return 0
    cols = list(rows[0].keys())
    if dry_run:
        print(f'  [dry-run] {table}: {len(rows)} rows, cols={cols[:5]}{"..." if len(cols) > 5 else ""}')
        return 0
    ident_table = psql_sql.Identifier(table)
    ident_cols = psql_sql.SQL(', ').join(psql_sql.Identifier(c) for c in cols)
    placeholders = psql_sql.SQL(', ').join(psql_sql.Placeholder() * len(cols))
    # PK 自動推定: pg_constraint から PRIMARY KEY 列を取得
    pk_cols: List[str] = []
    try:
        with conn.cursor() as c:
            c.execute("""
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
                ORDER BY array_position(i.indkey, a.attnum)
            """, (f'"{table}"',))
            pk_cols = [r[0] for r in c.fetchall()]
    except Exception:
        pk_cols = []
    if pk_cols and all(SAFE_IDENT.match(c) for c in pk_cols):
        conflict_target = psql_sql.SQL(', ').join(psql_sql.Identifier(c) for c in pk_cols)
        on_conflict = psql_sql.SQL(' ON CONFLICT ({}) DO NOTHING').format(conflict_target)
    else:
        # composite PK 不在 or 未検出 → 衝突は per-row except で warning
        on_conflict = psql_sql.SQL('')
    stmt = psql_sql.SQL('INSERT INTO {} ({}) VALUES ({}){}').format(
        ident_table, ident_cols, placeholders, on_conflict
    )
    inserted = 0
    errors = 0
    for row in rows:
        values = [_wrap_jsonb(row.get(c)) for c in cols]
        try:
            with conn.cursor() as cur:
                cur.execute(stmt, values)
                if cur.rowcount and cur.rowcount > 0:
                    inserted += cur.rowcount
        except Exception as e:
            errors += 1
            if errors <= 3:  # ログ多すぎ防止
                print(f'  [warn] {table} row insert failed: {str(e)[:120]}', file=sys.stderr)
    if errors > 3:
        print(f'  [warn] {table} 残り {errors - 3} 件のエラーは省略', file=sys.stderr)
    return inserted


def try_disable_fk(conn) -> bool:
    """SET session_replication_role='replica' を試行。Supabase 等 managed では
    権限なしで失敗するが、その場合は FK 順序を topological sort で解決して fallback。"""
    try:
        with conn.cursor() as c:
            c.execute("SET session_replication_role = 'replica'")
        print('  [fk] session_replication_role=replica (FK disabled)')
        return True
    except Exception as e:
        print(f'  [fk] SET session_replication_role 不可 ({str(e)[:80]}) → topological sort で対応')
        return False


def reset_sequences(conn) -> int:
    """全 SERIAL/IDENTITY 列で setval(MAX(id)) を実行。reset 件数を返す。"""
    reset = 0
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT t.table_name, c.column_name
            FROM information_schema.tables t
            JOIN information_schema.columns c
              ON c.table_schema = t.table_schema AND c.table_name = t.table_name
            WHERE t.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
              AND (c.column_default LIKE 'nextval%' OR c.is_identity = 'YES')
            ORDER BY t.table_name, c.column_name
        """)
        targets = cur.fetchall()
        for (t, col) in targets:
            if not (SAFE_IDENT.match(t) and SAFE_IDENT.match(col)):
                continue
            try:
                # information_schema 由来 + SAFE_IDENT 通過 = SQL injection 不可
                cur.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence(%s, %s),
                        COALESCE((SELECT MAX("{col}") FROM "{t}"), 1),
                        true
                    )
                """, (t, col))
                reset += 1
                print(f'  [seq] {t}.{col} reset')
            except Exception as e:
                print(f'  [warn] {t}.{col} setval failed: {str(e)[:120]}', file=sys.stderr)
    finally:
        cur.close()
    return reset


def main(path: str, dry_run: bool = False):
    if not os.path.isfile(path):
        print(f'ERROR: file not found: {path}', file=sys.stderr)
        sys.exit(2)
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        print('ERROR: DATABASE_URL env not set', file=sys.stderr)
        sys.exit(3)
    print(f'=== R2 backup restore ===')
    print(f'source: {path}')
    print(f'target: {dsn[:40]}... (truncated)')
    print(f'mode: {"DRY-RUN" if dry_run else "REAL INSERT"}')
    print()
    tables = parse_jsonl_gz(path)
    if dry_run:
        for t in sorted(tables.keys()):
            restore_table(None, t, tables[t], dry_run=True)
        return
    # **autocommit=True** が CRITICAL: psycopg3 の transaction abort 回避
    print(f'\n=== Connecting (autocommit=True) ===')
    conn = psycopg.connect(dsn, connect_timeout=15, autocommit=True)
    try:
        fk_disabled = try_disable_fk(conn)
        if fk_disabled:
            # FK disabled なので alphabet 順で OK
            order = sorted(tables.keys())
        else:
            # FK 依存解決
            print(f'\n=== Resolving FK dependencies ===')
            deps = get_fk_dependencies(conn)
            order = topological_sort(list(tables.keys()), deps)
            print(f'  order: {order[:5]}... ({len(order)} tables total)')
        print(f'\n=== Restoring tables ===')
        for t in order:
            try:
                n = restore_table(conn, t, tables[t])
                print(f'  {t}: {n} inserted (of {len(tables[t])} rows)')
            except Exception as e:
                print(f'  [ERROR] {t} skipped: {e}', file=sys.stderr)
        if fk_disabled:
            print(f'\n=== Re-enabling FK ===')
            try:
                with conn.cursor() as c:
                    c.execute("SET session_replication_role = 'origin'")
                print('  done')
            except Exception as e:
                print(f'  [warn] re-enable failed: {e}', file=sys.stderr)
        print(f'\n=== Resetting sequences ===')
        reset = reset_sequences(conn)
        print(f'  total: {reset} sequences reset')
    finally:
        conn.close()
    print(f'\n=== DONE ===')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    main(args[0], dry_run=dry)
