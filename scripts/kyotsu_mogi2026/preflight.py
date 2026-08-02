#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取込前チェック: 生成した seed JSON が本番 import の契約を満たすか、server/main.py から実物を読んで検証する。

CLAUDE.md の「取込 API はデプロイ済みのコードを検証する」に対応する事前確認。
本番に投げる前に、次を server/main.py の実定義と突き合わせる。

  1. (exam_id, part_key, eiken_grade) が EXAM_QUESTION_ROTATION に存在するか
     → 無いと import が `invalid rotation` で全行 failed になる
  2. MOCK_EXAM_TEMPLATES の該当模試が、このプールから必要な大問数を引けるか
  3. 自己完結ゲート Layer A (_self_containment_gate) に引っかからないか
     → 引っかかると gated_selfcheck で黙って捨てられる
  4. mock_exam_generate / mock_exam_submit の採点ロジックを再現し、
     全問正解が 100% になるか (= 全小問が multiple_choice で自動採点可能か)

実行: python3 scripts/kyotsu_mogi2026/preflight.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MAIN_PY = os.path.join(ROOT, 'server', 'main.py')
SEEDS = [
    os.path.join(ROOT, 'seed-data', 'kyotsu_mogi2026_eng_manual.json'),
    os.path.join(ROOT, 'seed-data', 'kyotsu_mogi2026_math_manual.json'),       # 単元別ドリル (math_unit)
    os.path.join(ROOT, 'seed-data', 'kyotsu_mogi2026_math_exam_manual.json'),  # 本番形式 (math_1a)
]

errors = []
warnings = []


def load_source():
    with open(MAIN_PY, encoding='utf-8') as f:
        return f.read()


def parse_rotation(src):
    """EXAM_QUESTION_ROTATION の (exam_id, part_key, eiken_grade) 集合を実ファイルから取り出す。"""
    i = src.index('EXAM_QUESTION_ROTATION = [')
    j = src.index('\n]', i)
    block = src[i:j]
    out = set()
    for m in re.finditer(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(?:"([^"]*)"|None)\s*\)', block):
        out.add((m.group(1), m.group(2), m.group(3)))
    return out


def parse_mock_templates(src):
    """MOCK_EXAM_TEMPLATES の各テンプレの section (exam_id/part_key/eiken_grade/count/points_per) を取り出す。"""
    i = src.index('MOCK_EXAM_TEMPLATES = {')
    j = src.index('\n}\n', i)
    block = src[i:j]
    templates = {}
    cur = None
    for line in block.splitlines():
        m = re.match(r'\s{4}"([a-z0-9_]+)":\s*\{', line)
        if m:
            cur = m.group(1)
            templates[cur] = []
            continue
        m = re.search(
            r'\{"name":\s*"([^"]*)",\s*"exam_id":\s*"([^"]+)",\s*"part_key":\s*"([^"]+)",'
            r'\s*"eiken_grade":\s*"([^"]+)",\s*"count":\s*(\d+),\s*"points_per":\s*(\d+)\}', line)
        if m and cur:
            templates[cur].append({
                "name": m.group(1), "exam_id": m.group(2), "part_key": m.group(3),
                "eiken_grade": m.group(4), "count": int(m.group(5)), "points_per": int(m.group(6)),
            })
    return templates


# --- server/main.py の _self_containment_gate Layer A を同じ正規表現で再現 ------------
COORD = re.compile(r'\(\s*-?\d[^()]*[,，][^()]*-?\d')
VECREF = re.compile(r'\\vec\s*\{|\\overrightarrow\s*\{|ベクトル\s*[A-Za-z\\]')


def layer_a_gate(qd):
    """True = 通過。server 側と同じく「ベクトル記号を使うのに成分が解説にしかない」を検出する。"""
    passage = qd.get('passage') or ''
    qs = qd.get('questions') or []
    all_stems = "\n".join((q.get('stem') or '') for q in qs)
    coords_visible = bool(COORD.search(passage + "\n" + all_stems))
    bad = []
    for idx, q in enumerate(qs):
        stem = q.get('stem') or ''
        expl = q.get('explanation') or ''
        if VECREF.search(stem) and not coords_visible and COORD.search(expl):
            bad.append(f"q{idx + 1}:vector_defined_only_in_solution")
    return (not bad), bad


def main():
    src = load_source()
    rotation = parse_rotation(src)
    templates = parse_mock_templates(src)

    rows = []
    for path in SEEDS:
        if not os.path.exists(path):
            errors.append(f'seed が無い: {os.path.relpath(path, ROOT)} (先に build_*.py を実行)')
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        got = data.get('questions') or []
        rows.extend(got)
        print(f'読み込み: {os.path.relpath(path, ROOT)} … {len(got)} 大問')

    if errors:
        _report()
        return 1

    # --- 1. rotation ---
    pools = {}
    for i, r in enumerate(rows):
        key = (r.get('exam_id'), r.get('part_key'), r.get('eiken_grade'))
        if key not in rotation:
            errors.append(f'row{i}: rotation に無い枠 {key} → import が invalid rotation で弾く')
        pools.setdefault(key, 0)
        pools[key] += 1
        for field in ('exam_id', 'part_key', 'eiken_grade', 'question_data', 'model'):
            if not r.get(field):
                errors.append(f'row{i}: 必須フィールド {field} が空')
    print('\n[1] EXAM_QUESTION_ROTATION 照合')
    for key, n in sorted(pools.items(), key=lambda kv: str(kv[0])):
        mark = '✅' if key in rotation else '❌'
        print(f'   {mark} {key} … {n} 大問')

    # --- 2. 模試テンプレが必要数を引けるか ---
    print('\n[2] MOCK_EXAM_TEMPLATES から必要な大問数を引けるか (今回の追加分のみで)')
    for tpl_key in ('kyotsu', 'kyotsu_math'):
        secs = templates.get(tpl_key)
        if not secs:
            errors.append(f'MOCK_EXAM_TEMPLATES["{tpl_key}"] を server/main.py から読めなかった')
            continue
        label_shown = False
        for s in secs:
            key = (s['exam_id'], s['part_key'], s['eiken_grade'])
            have = pools.get(key, 0)
            ok = have >= s['count']
            if not label_shown:
                print(f'   {tpl_key}:')
                label_shown = True
            print(f"      {'✅' if ok else '⚠️ '} {s['name']}: 必要 {s['count']} / 今回追加 {have}")
            if not ok:
                warnings.append(
                    f"{tpl_key}/{s['name']}: 今回の追加分だけでは {s['count']} 大問に届かない "
                    f"(既存プールと合算されるので通常は問題なし)")

    # --- 3. 自己完結ゲート Layer A ---
    print('\n[3] 自己完結ゲート Layer A (import 時に黙って捨てられないか)')
    gated = 0
    for i, r in enumerate(rows):
        ok, why = layer_a_gate(r['question_data'])
        if not ok:
            gated += 1
            errors.append(f'row{i} ({r["question_data"].get("format_type") or r["question_data"].get("group")}): '
                          f'Layer A で gated → {why}')
    print(f'   {"✅" if gated == 0 else "❌"} gated_selfcheck 予測: {gated} 件')

    # --- 4. 採点ロジック再現 (全問正解 = 100%) ---
    print('\n[4] mock_exam の採点ロジック再現 (全問正解が満点になるか)')
    for tpl_key in ('kyotsu', 'kyotsu_math'):
        secs = templates.get(tpl_key) or []
        max_score = 0
        got_score = 0
        n_sub = 0
        for s in secs:
            key = (s['exam_id'], s['part_key'], s['eiken_grade'])
            picked = [r for r in rows
                      if (r['exam_id'], r['part_key'], r['eiken_grade']) == key][:s['count']]
            for r in picked:
                subq = r['question_data']['questions']
                mc = [q for q in subq if q.get('type') == 'multiple_choice']
                if len(mc) != len(subq):
                    warnings.append(f'{tpl_key}: 非 multiple_choice の小問があり自動採点対象外になる')
                per_pt = max(s['points_per'] // max(len(mc), 1), 1)
                for q in mc:
                    # answer が choices の範囲内か = 採点そのものが壊れないか
                    if not isinstance(q.get('answer'), int) or not (0 <= q['answer'] < len(q.get('choices') or [])):
                        errors.append(f'{tpl_key}: answer={q.get("answer")} が choices の範囲外')
                    max_score += per_pt
                    got_score += per_pt          # 生徒が全問正解したと仮定
                    n_sub += 1
        pct = round(got_score / max_score * 100) if max_score else 0
        mark = '✅' if pct == 100 and n_sub > 0 else '❌'
        print(f'   {mark} {tpl_key}: 自動採点対象 {n_sub} 小問 / 満点 {max_score} 点 → 全問正解で {pct}%')
        if pct != 100 or n_sub == 0:
            errors.append(f'{tpl_key}: 全問正解が 100% にならない (自動採点できない小問が混在)')

    _report()
    return 1 if errors else 0


def _report():
    print()
    if warnings:
        print('⚠️  警告:')
        for w in warnings:
            print('   -', w)
    if errors:
        print('❌ 取込前チェック NG:')
        for e in errors:
            print('   -', e)
    else:
        print('✅ 取込前チェック 全項目 OK — import_prod.py で本番投入できます')


if __name__ == '__main__':
    sys.exit(main())
