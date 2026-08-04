#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seed-data で直した内容を、本番 DB の既存行に **上書き** で反映する。

【なぜ要るか】
seed-data は取込 (import) 用のペイロードで、取込 API は INSERT 専用。
UPDATE 経路が無いため、seed を直しても本番 DB の既存行は古いまま。
しかも question_data の内容が変わっているので、そのまま再 import すると
重複防止 (content hash 一致で skip) を素通りして **重複行が増える**。
過去にこの経路で約 2000 件の重複が溜まった記録がコード内に残っている。

【やり方: 既存の差し替え機構をそのまま使う】
新しい server コードは書かない。既に用意されている
  POST /api/admin/exam-questions/replace-explanation
を使う。この endpoint は
  1. 元の question_data を exam_questions_archive に退避
  2. exam_questions.question_data を UPDATE
  3. archive id を返す
を 1 トランザクションで行い、batch_id 単位で
  POST /api/admin/exam-questions/rollback-batch
から 1-click で元に戻せる。

【DB 行の特定: ハッシュではなく内容の完全一致】
question_data は TEXT 列だが、dump API は json.loads して返すので
保存文字列そのものは取れない。整形の違いに影響されないよう、
**パース済みオブジェクトの完全一致**で照合する。
  - 変更前の seed (--base の時点) の question_data == DB 行の question_data
  → その DB 行が「まだ直っていない対象」。変更後の内容で置き換える。
一致しない行は AI 生成分などなので**触らない**。

【安全側の作り】
- 既定は dry-run。--apply を明示しない限り 1 行も書き換えない。
- 変更後の内容と既に一致する行は skip (何度流しても同じ = 冪等)。
- 変更前と一致する行が複数ある (過去の重複) 場合はまとめて更新し、件数を報告。
- 一致 0 件の大問は「未取込 or 既に別物」として報告し、触らない。
- --apply 時は送信するペイロードを先にファイルへ保存する (事後の突き合わせ用)。
- batch_id を必ず出力する。戻すときはこれを rollback-batch に渡す。

【使い方】
  # 1. 何が起きるかを見る (DB には触らない)
  python3 scripts/migrate_seed_to_prod.py --token "$ADMIN_TOKEN"

  # 2. 特定のファイルだけに絞る
  python3 scripts/migrate_seed_to_prod.py --token "$ADMIN_TOKEN" \
      --only dojo_eng_kyotsu2026_graph_manual.json

  # 3. 実行 (archive されるので rollback 可能)
  python3 scripts/migrate_seed_to_prod.py --token "$ADMIN_TOKEN" --apply

  # 4. 戻す
  curl -X POST "$API/api/admin/exam-questions/rollback-batch" \
       -H "Authorization: Bearer $ADMIN_TOKEN" \
       -H 'Content-Type: application/json' \
       -d '{"batch_id":"<出力された batch_id>"}'
"""
import argparse
import collections
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.environ.get('AI_JUKU_API', 'https://ai-juku-api-production.up.railway.app')

# 既定の基準点 = seed-data に手を入れ始める直前のコミット。
# ここから HEAD までの差分が「本番へ反映したい修正」。
DEFAULT_BASE = 'c80809d'

# 自分で作った模試は本番 DB に入れていないので対象外 (塾長の指示による)
SKIP_FILES = {'kyotsu_mogi2026_eng_manual.json',
              'kyotsu_mogi2026_math_manual.json',
              'kyotsu_mogi2026_math_exam_manual.json'}


def git_show(ref, path):
    r = subprocess.run(['git', 'show', f'{ref}:{path}'], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def touching_commits(base, path):
    """base..HEAD の間にそのファイルを触ったコミットを古い順に返す。

    本番 DB の中身は「前回どこまで反映したか」で決まる。base の版だけで照合すると
    途中まで反映済みの行を取りこぼす。実際 756 大問を反映した後に seed を更に直した
    ところ、その 342 問がすべて「DB に該当なし」になった (DB は中間の版を持っていて、
    base の版とも HEAD の版とも一致しないため)。
    そこで base の版と途中の各コミットの版を**すべて**照合候補にする。
    """
    r = subprocess.run(['git', 'log', '--format=%H', '--reverse', f'{base}..HEAD',
                        '--', path], cwd=ROOT, capture_output=True, text=True)
    return [c for c in r.stdout.split() if c]


def changed_files(base):
    r = subprocess.run(['git', 'diff', '--name-only', base, 'HEAD', '--', 'seed-data/'],
                       cwd=ROOT, capture_output=True, text=True)
    return [p for p in r.stdout.split() if p.endswith('.json')]


def rows_of(text):
    """seed JSON から (pool, index, question_data) を取り出す。

    ★ 対象は exam_questions の行として取り込まれる「大問」形式だけ。
      chu2_grammar_v1 / grammar_drill_pool_v1 のようなフラットなドリル配列は
      question_data を持たず、この endpoint (id 指定の差し替え) では扱えないので
      空を返す。呼び出し側が「この経路では移行できないファイル」として報告する。
    """
    try:
        d = json.loads(text)
    except Exception:
        return []
    qs = d.get('questions') if isinstance(d, dict) else (d if isinstance(d, list) else None)
    if not isinstance(qs, list):
        return []
    out = []
    for i, r in enumerate(qs):
        if not isinstance(r, dict) or not isinstance(r.get('question_data'), dict):
            continue
        out.append(((r.get('exam_id') or '', r.get('part_key') or '',
                     r.get('eiken_grade') or ''), i, r['question_data']))
    return out


# 認証の載せ方。server 側は「admin Bearer」と「x-cron-secret」の両方を受け付けるが、
# 渡された値がどちらなのか呼び出し側では分からない。3 通りを実際に試して、
# 通った 1 つを以降ずっと使う (どれも通らなければ理由を出して止まる)。
AUTH_MODES = [
    ('x-cron-secret のみ', lambda c: {'X-Cron-Secret': c}),
    ('Bearer のみ', lambda c: {'Authorization': f'Bearer {c}'}),
    ('Bearer + x-cron-secret', lambda c: {'Authorization': f'Bearer {c}', 'X-Cron-Secret': c}),
]
_auth = {'mode': None}


def auth_headers(cred):
    name, fn = _auth['mode'] or AUTH_MODES[0]
    return fn(cred)


def probe_auth(creds):
    """どの認証情報 × どの載せ方なら 200 が返るかを実際に試して確定する。

    401 が返ったときに「値が違うのか、ヘッダの載せ方が違うのか」を
    切り分けられないと手が止まるので、ここで全部潰しておく。
    通った組み合わせを返す (どれも通らなければ None)。
    """
    url = (f'{API}/api/admin/exam-questions/dump'
           f'?exam=daigaku&part=r_long&eiken_grade=kyotsu&offset=0&limit=1')
    tried = []
    for ci, cred in enumerate(creds, start=1):
        if not cred:
            continue
        for name, fn in AUTH_MODES:
            label = f'値{ci} / {name}'
            try:
                req = urllib.request.Request(url, headers=fn(cred))
                with urllib.request.urlopen(req, timeout=60) as resp:
                    if resp.status == 200:
                        _auth['mode'] = (name, fn)
                        print(f'認証: 「{label}」で通りました')
                        return cred
                    tried.append(f'{label} → HTTP {resp.status}')
            except urllib.error.HTTPError as e:
                tried.append(f'{label} → HTTP {e.code}')
            except Exception as e:
                tried.append(f'{label} → {type(e).__name__}: {e}')
    print('❌ 認証に失敗しました。試した組み合わせ:')
    for t in tried:
        print(f'    {t}')
    print('\n  すべて 401 の場合、渡した値が本番の CRON_SECRET / 管理トークンと')
    print('  一致していません。GitHub の Secrets と Railway の環境変数は別々に')
    print('  設定するものなので、値がズレている可能性があります。')
    print('  Railway の Variables で CRON_SECRET の値を確認し、')
    print('  同じものを GitHub の Secrets にも登録し直してください。')
    return None


def api_get(path, cred, params):
    url = f'{API}{path}?' + '&'.join(f'{k}={urllib.request.quote(str(v))}' for k, v in params.items())
    req = urllib.request.Request(url, headers=auth_headers(cred))
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


def api_post(path, cred, payload):
    headers = dict(auth_headers(cred))
    headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(
        f'{API}{path}', method='POST',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers=headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode('utf-8'))


def fetch_pool(pool, token):
    """プール内の全行を dump API で取り切る。"""
    exam, part, grade = pool
    items, offset = [], 0
    while True:
        params = {'exam': exam, 'part': part, 'offset': offset, 'limit': 200}
        if grade:
            params['eiken_grade'] = grade
        d = api_get('/api/admin/exam-questions/dump', token, params)
        got = d.get('items') or []
        items += got
        offset += len(got)
        if not got or offset >= int(d.get('total') or 0):
            break
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--token', required=True, nargs='+',
                    help='管理トークン / CRON_SECRET。複数渡すと通るものを自動で選ぶ')
    ap.add_argument('--base', default=DEFAULT_BASE, help=f'比較の基準コミット (既定 {DEFAULT_BASE})')
    ap.add_argument('--only', nargs='*', help='対象 seed ファイル名を限定')
    ap.add_argument('--apply', action='store_true', help='実際に差し替える (既定は dry-run)')
    ap.add_argument('--batch-id', help='rollback 用の batch_id (既定は自動生成)')
    ap.add_argument('--out', default='migration_payload.json', help='送信ペイロードの保存先')
    args = ap.parse_args()

    # 認証情報と載せ方を先に確定させる (401 で止まったときの切り分けを省くため)
    cred = probe_auth(args.token)
    if not cred:
        return 2

    files = changed_files(args.base)
    if args.only:
        files = [f for f in files if os.path.basename(f) in set(args.only)]
    files = [f for f in files if os.path.basename(f) not in SKIP_FILES]
    if not files:
        print('対象の変更が無い')
        return 0

    # --- 1. 変更前 → 変更後 の対応表を作る
    #     旧版は base だけでなく途中コミットの版もすべて候補にする (部分反映済み対策)
    plan = collections.defaultdict(list)   # pool -> [(old_qds, new_qd, file, idx)]
    unsupported = []
    for path in files:
        old_txt, new_txt = git_show(args.base, path), git_show('HEAD', path)
        if not old_txt or not new_txt:
            continue
        old_rows, new_rows = rows_of(old_txt), rows_of(new_txt)
        if not old_rows and not new_rows:
            # フラットなドリル配列。exam_questions の行ではないのでこの経路では移行できない
            unsupported.append(os.path.basename(path))
            continue
        if len(old_rows) != len(new_rows):
            print(f'  ⚠ {os.path.basename(path)}: 大問数が変わっている '
                  f'({len(old_rows)} → {len(new_rows)}) ので対象外')
            continue
        # 途中コミットの版 (大問数が同じものだけ。HEAD 自身は末尾なので除く)
        mids = []
        for c in touching_commits(args.base, path)[:-1]:
            txt = git_show(c, path)
            rws = rows_of(txt) if txt else []
            if len(rws) == len(new_rows):
                mids.append(rws)
        for (pool_o, i, qd_o), (pool_n, _j, qd_n) in zip(old_rows, new_rows):
            if pool_o != pool_n or qd_o == qd_n:
                continue
            variants = [qd_o]
            for rws in mids:
                qd_m = rws[i][2]
                if qd_m != qd_n and qd_m not in variants:
                    variants.append(qd_m)
            plan[pool_o].append((variants, qd_n, os.path.basename(path), i))

    total_changed = sum(len(v) for v in plan.values())
    print(f'変更のある大問: {total_changed} 件 / {len(plan)} プール  (基準 {args.base})')
    if unsupported:
        print(f'\n[この経路では移行できないファイル] {len(unsupported)} 件')
        print('  フラットなドリル配列で exam_questions の行ではないため、')
        print('  id 指定の差し替え endpoint では扱えない:')
        for u in unsupported:
            print(f'    - {u}')
    print()

    # --- 2. DB を引いて、変更前の内容と完全一致する行を探す
    replacements, stat = [], collections.Counter()
    detail = []
    for pool, entries in sorted(plan.items(), key=lambda x: -len(x[1])):
        try:
            db_rows = fetch_pool(pool, cred)
        except urllib.error.HTTPError as e:
            print(f'  ❌ {"/".join(pool)}: dump 失敗 HTTP {e.code} ({e.reason})')
            return 2
        except Exception as e:
            print(f'  ❌ {"/".join(pool)}: dump 失敗 {type(e).__name__}: {e}')
            return 2
        by_old, by_new = collections.defaultdict(list), set()
        for row in db_rows:
            qd = row.get('question_data')
            if isinstance(qd, dict):
                by_old[json.dumps(qd, ensure_ascii=False, sort_keys=True)].append(row['id'])
        for qd_os, qd_n, fname, idx in entries:
            k_n = json.dumps(qd_n, ensure_ascii=False, sort_keys=True)
            # base の版 → 途中の版 の順に探す。最初に見つかったものを「変更前」とする。
            hit_old, matched_at = [], 0
            for vi, qd_o in enumerate(qd_os):
                got = by_old.get(json.dumps(qd_o, ensure_ascii=False, sort_keys=True)) or []
                if got:
                    hit_old, matched_at = got, vi
                    break
            hit_new = by_old.get(k_n) or []
            if hit_new and not hit_old:
                stat['既に修正済み (skip)'] += 1
                continue
            if hit_old and matched_at > 0:
                stat['途中まで反映済みの行を更新'] += len(hit_old)
            if not hit_old:
                stat['DB に該当なし (未取込 or 別物)'] += 1
                detail.append(('none', fname, idx, pool, 0))
                continue
            if len(hit_old) > 1:
                stat['重複行あり (まとめて更新)'] += 1
                detail.append(('dup', fname, idx, pool, len(hit_old)))
            for rid in hit_old:
                replacements.append({'id': rid, 'new_question_data': qd_n})
            stat['更新対象'] += len(hit_old)
        print(f'  {"/".join(pool):40s} DB {len(db_rows):4d} 行 / 変更 {len(entries):4d} 大問')

    print('\n[内訳]')
    for k, v in stat.most_common():
        print(f'  {v:5d}  {k}')
    for kind, fname, idx, pool, n in detail[:15]:
        tag = 'DB に無い' if kind == 'none' else f'DB に {n} 行の重複'
        print(f'    - {fname} 大問{idx + 1} ({"/".join(pool)}): {tag}')
    if len(detail) > 15:
        print(f'    … 他 {len(detail) - 15} 件')

    if not replacements:
        print('\n更新対象が無い (すでに反映済みか、DB に該当行が無い)')
        return 0

    batch_id = args.batch_id or f'seedfix_{args.base}_{len(replacements)}'
    payload = {
        'batch_id': batch_id,
        'reason': f'seed-data の是正を本番へ反映 ({args.base}..HEAD)。'
                  f'正解番号の均し / 理系解説の段組み / 引用の是正 / 図ラベルの重なり修正',
        'replacements': replacements,
    }
    out_path = os.path.join(ROOT, args.out)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f'\nペイロード保存: {os.path.relpath(out_path, ROOT)} '
          f'({len(replacements)} 行 / batch_id = {batch_id})')

    if not args.apply:
        print('\n--- dry-run ここまで。DB は 1 行も変更していない ---')
        print('実行するなら --apply を付ける。archive されるので下記で戻せる:')
        print(f'  curl -X POST "{API}/api/admin/exam-questions/rollback-batch" \\')
        print(f'       -H "Authorization: Bearer $ADMIN_TOKEN" -H \'Content-Type: application/json\' \\')
        print(f'       -d \'{{"batch_id":"{batch_id}"}}\'')
        return 0

    print(f'\n差し替えを実行中… ({len(replacements)} 行)')
    try:
        res = api_post('/api/admin/exam-questions/replace-explanation', cred, payload)
    except urllib.error.HTTPError as e:
        print(f'❌ HTTP {e.code}: {e.read().decode("utf-8", "ignore")[:400]}')
        return 2
    print(f'  updated={res.get("updated")} archived={res.get("archived")} '
          f'failed={len(res.get("failed") or [])}')
    for f_ in (res.get('failed') or [])[:10]:
        print(f'    失敗: {f_}')
    print(f'\n✅ 完了。戻すときは batch_id = {batch_id}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
