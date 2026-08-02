#!/usr/bin/env python3
"""seed-data/*.json 全体の品質実測 (measure-only)。

kyotsu_mogi2026/audit.py は「その模試だけ」を見る。こちらは **リポジトリ内の全教材**
を同じ物差しで測り、どこにどれだけ問題があるかを数えるための道具。

- 何も直さない。exit code は常に 0 (現状把握が目的・CI を壊さない)。
- 解説フォーマットは「正典を1つ決めて全部を叩く」ことはしない。
  リポジトリの実態は **模試プール (server が生成) と ドリルプール (手書き) で慣行が違う**。
  そこで各プールの **実際の多数派 (dominant convention)** を先に測り、
  「そのプール自身の慣行から外れている問題」を数える。
  模試プールについてのみ、多数派が server/main.py の生成プロンプトと一致するかも見る。

Usage:
  python3 scripts/seed_survey.py                     # 人間向けサマリ
  python3 scripts/seed_survey.py --detail            # 違反を1件ずつ列挙
  python3 scripts/seed_survey.py --detail --kind quote
  python3 scripts/seed_survey.py --json out.json     # 機械可読 (後続の修正パス用)
  python3 scripts/seed_survey.py --only kyotsu_mogi2026_eng_manual.json
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(ROOT, 'seed-data')
MAIN_PY = os.path.join(ROOT, 'server', 'main.py')

# ---------------------------------------------------------------- pool 分類
KOKUGO_PARTS = {'kobun', 'kanbun', 'gendai', 'kobun_unit', 'kanbun_unit', 'gendai_unit'}
SHAKAI_PARTS = {'nihonshi', 'sekaishi', 'chiri', 'rinri', 'seiji_keizai',
                'kouminka', 'koukyou', 'gendaishakai'}


def family(exam_id, part_key):
    if exam_id == 'drill':
        return 'drill'
    if exam_id == 'rikei' or (part_key or '').startswith('math'):
        return 'rikei'
    if part_key in KOKUGO_PARTS:
        return 'kokugo'
    if part_key in SHAKAI_PARTS:
        return 'shakai'
    return 'english'


# server/main.py の生成プロンプトが要求するセクション (模試プールの正典)
CANON = {
    'english': ['🎯 コアイメージ', '🔬 文構造分析', '📍 本文の根拠', '❌ 誤答 NG 理由'],
    'kokugo': ['現代語訳', '解答の根拠', '誤答 NG 理由'],
    'rikei': ['考え方|方針', '立式', '計算', '答え'],
    'shakai': [],   # server 側に専用プロンプトが無い (英語プロンプトに相乗り) = 正典未定義
    'drill': [],
}

# 解説の「型」を判定するためのマーカー。多数派の型を測るのに使う。
MARKERS = [
    ('単元', re.compile(r'【単元】')),
    ('考え方', re.compile(r'(?m)^\s*(?:考え方|方針)\s*[:：]')),
    ('立式', re.compile(r'(?m)^\s*立式\s*[:：]')),
    ('計算', re.compile(r'(?m)^\s*計算\s*[:：]')),
    ('答え', re.compile(r'(?m)^\s*(?:答え|正解|解答)\s*[:：]')),
    ('補足', re.compile(r'(?m)^\s*補足\s*[:：]')),
    ('誤答根拠', re.compile(r'(?m)^\s*誤答の根拠\s*[:：]')),
    ('解説', re.compile(r'(?m)^\s*解説\s*[:：]')),
    ('コアイメージ', re.compile(r'🎯\s*コアイメージ')),
    ('文構造分析', re.compile(r'🔬\s*文構造分析')),
    ('本文の根拠', re.compile(r'📍\s*本文の根拠')),
    ('誤答NG', re.compile(r'❌\s*誤答\s*NG\s*理由')),
    ('現代語訳', re.compile(r'##\s*現代語訳')),
    ('解答の根拠', re.compile(r'##\s*解答の根拠')),
]


def signature(expl):
    return tuple(name for name, rx in MARKERS if rx.search(expl or ''))


# ---------------------------------------------------------- 検査用の正規表現
# server/main.py _self_containment_gate Layer A (preflight.py と同一)
COORD = re.compile(r'\(\s*-?\d[^()]*[,，][^()]*-?\d')
VECREF = re.compile(r'\\vec\s*\{|\\overrightarrow\s*\{|ベクトル\s*[A-Za-z\\]')

# 組版事故: 円記号での LaTeX (フォント差し替えで \ が ¥ に化けた残骸) と文字化け
YEN_TEX = re.compile(r'¥\s*[()\[\]]|¥(?:dfrac|frac|sqrt|mathrm|text|angle|circ|cdot|times|le|ge)\b')
MOJIBAKE = re.compile('[\ufffd]|\u00e3\u0083|\u00e2\u0080')
TEX_OPEN = re.compile(r'(?<!\\)\\\(')
TEX_CLOSE = re.compile(r'(?<!\\)\\\)')

# 国語: 傍線部「X」/下線部「X」は passage に verbatim で実在すること (server の絶対ルール)
BOUSEN = re.compile(r'(?:傍線部|下線部)\s*(?:[(（]?[ア-ンA-Za-z0-9]{1,3}[)）]?)?\s*「([^」\n]+)」')

ENG_SEC = ['🎯 コアイメージ', '🔬 文構造分析', '📍 本文の根拠', '❌ 誤答 NG 理由']
CIRCLED = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨']


def norm(s):
    """引用照合用の正規化 (audit.py と同じ方針: 装飾記号を落とし空白を潰す)。"""
    s = (s or '').replace('**', '').replace('`', '')
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('\u3000', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def mock_pools():
    """MOCK_EXAM_TEMPLATES が引くプール = server の生成フォーマットが正典のもの。"""
    try:
        src = open(MAIN_PY, encoding='utf-8').read()
    except OSError:
        return set()
    i = src.find('MOCK_EXAM_TEMPLATES')
    if i < 0:
        return set()
    blk = src[i:i + 14000]
    return {(m.group(1), m.group(2)) for m in re.finditer(
        r'"exam_id":\s*"([^"]+)",\s*"part_key":\s*"([^"]+)",\s*"eiken_grade":\s*"([^"]+)"', blk)}


# ------------------------------------------------------------------ 読み込み
def load_rows(only=None):
    rows, skipped = [], []
    for path in sorted(glob.glob(os.path.join(SEED_DIR, '*.json'))):
        name = os.path.basename(path)
        if only and name not in only:
            continue
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            skipped.append((name, f'JSON parse 失敗: {e}'))
            continue
        qs = data.get('questions') if isinstance(data, dict) else (data if isinstance(data, list) else None)
        if not isinstance(qs, list) or not qs:
            skipped.append((name, 'questions 配列が無い (教材ではない)'))
            continue
        if not any(isinstance(q, dict) and ('question_data' in q or 'stem' in q) for q in qs):
            skipped.append((name, '設問形式ではない (語彙リスト等)'))
            continue
        flat = []
        for gi, q in enumerate(qs):
            if not isinstance(q, dict):
                continue
            if 'question_data' in q:
                qd = q['question_data'] if isinstance(q['question_data'], dict) else {}
                rows.append({'file': name, 'gi': gi, 'label': qd.get('group') or qd.get('format_type') or f'大問{gi + 1}',
                             'exam_id': q.get('exam_id') or '', 'part_key': q.get('part_key') or '',
                             'eiken_grade': q.get('eiken_grade') or '', 'qd': qd})
            elif 'stem' in q:
                flat.append(q)
        if flat:
            # フラットなドリル行 (chu2_grammar / grammar_drill_pool 等) は 1 ファイル =
            # 1 プール扱い。1問=1大問にすると「大問内の偏り」が測れず無意味になる。
            rows.append({'file': name, 'gi': 0, 'label': 'ドリル一括',
                         'exam_id': 'drill', 'part_key': os.path.splitext(name)[0],
                         'eiken_grade': '', 'qd': {'passage': '', 'questions': flat}})
    return rows, skipped


# -------------------------------------------------------------------- 検査群
def survey(rows):
    findings = []
    seen_stem = {}
    MOCK = mock_pools()
    pool_stat = collections.defaultdict(lambda: {'q': 0, 'g': 0, 'sig': collections.Counter(),
                                                 'ans': collections.Counter(), 'fam': ''})

    def add(kind, sev, r, where, msg):
        findings.append({'kind': kind, 'sev': sev, 'file': r['file'],
                         'pool': f"{r['exam_id']}/{r['part_key']}", 'where': where, 'msg': msg})

    # --- pass 1: プールごとの多数派フォーマットを測る -----------------------
    for r in rows:
        pkey = (r['exam_id'], r['part_key'])
        fam = family(*pkey)
        pool_stat[pkey]['fam'] = fam
        for s in (r['qd'].get('questions') or []):
            if isinstance(s, dict):
                pool_stat[pkey]['sig'][signature(s.get('explanation'))] += 1

    dominant = {}
    for pkey, v in pool_stat.items():
        if v['sig']:
            dominant[pkey] = set(v['sig'].most_common(1)[0][0])

    # --- pass 2: 本検査 ----------------------------------------------------
    for r in rows:
        qd, pkey = r['qd'], (r['exam_id'], r['part_key'])
        fam = family(*pkey)
        passage = qd.get('passage') or ''
        subs = qd.get('questions') or []
        if not isinstance(subs, list):
            add('schema', 'high', r, r['label'], 'question_data.questions が配列でない')
            continue
        pool_stat[pkey]['g'] += 1
        dom = dominant.get(pkey, set())

        all_stems = '\n'.join((s.get('stem') or '') for s in subs if isinstance(s, dict))
        coords_visible = bool(COORD.search(passage + '\n' + all_stems))
        np_passage = norm(passage)

        daimon_ans, ids_here = [], {}
        for si, s in enumerate(subs):
            where = f'{r["label"]}/問{si + 1}'
            if not isinstance(s, dict):
                add('schema', 'high', r, where, '小問が dict でない')
                continue
            pool_stat[pkey]['q'] += 1
            stem, expl = s.get('stem') or '', s.get('explanation') or ''
            choices = s.get('choices')
            qtype = s.get('type') or ('multiple_choice' if choices else '')
            qid = s.get('id')

            # --- A. スキーマ / 採点可能性
            if not stem.strip():
                add('schema', 'high', r, where, 'stem が空')
            if not expl.strip():
                add('schema', 'high', r, where, 'explanation が空')
            # id は大問内でユニークであれば良い (server の採番も大問ローカル)
            if qid:
                if qid in ids_here:
                    add('dup-id', 'mid', r, where, f'id「{qid}」が同じ大問内で重複 (問{ids_here[qid] + 1})')
                else:
                    ids_here[qid] = si

            if qtype == 'multiple_choice':
                if not isinstance(choices, list) or len(choices) < 2:
                    add('schema', 'high', r, where, f'multiple_choice なのに choices が {choices!r}')
                else:
                    try:
                        ai = int(s.get('answer'))
                    except (TypeError, ValueError):
                        ai = None
                    if ai is None:
                        add('answer', 'high', r, where, f'answer が index として読めない: {s.get("answer")!r}')
                    elif not (0 <= ai < len(choices)):
                        add('answer', 'high', r, where, f'answer={ai} が choices ({len(choices)}個) の範囲外')
                    else:
                        daimon_ans.append(ai)
                        pool_stat[pkey]['ans'][ai] += 1
                    seen_c = {}
                    for ci, c in enumerate(choices):
                        k = norm(str(c))
                        if not k:
                            add('choices', 'mid', r, where, f'選択肢{ci + 1}が空')
                        elif k in seen_c:
                            add('choices', 'high', r, where,
                                f'選択肢{seen_c[k] + 1}と{ci + 1}が同文 (正解が2つ成立しうる)')
                        else:
                            seen_c[k] = ci
                    if len(choices) != 4:
                        add('choices-n', 'low', r, where, f'選択肢が {len(choices)} 個')
            elif not qtype:
                add('type', 'low', r, where, 'type が無い')

            # --- B. 自己完結ゲート (取込時に server が拒否する条件)
            if VECREF.search(stem) and not coords_visible and COORD.search(expl):
                add('gate-a', 'high', r, where, 'ベクトル成分が解説にしか無い (Layer A で取込拒否)')

            # --- C. 解説フォーマット: そのプール自身の多数派から外れていないか
            if expl.strip() and dom:
                miss = dom - set(signature(expl))
                if miss:
                    add('format', 'mid', r, where,
                        f'プール多数派の型から欠落: {"/".join(sorted(miss))}')
            if fam == 'rikei' and expl.strip() and len([l for l in expl.splitlines() if l.strip()]) < 3:
                add('format-lines', 'mid', r, where, '理系解説が3行未満 (段階分けされていない)')

            # --- D. 組版事故
            for fld, val in (('stem', stem), ('explanation', expl)):
                if YEN_TEX.search(val):
                    add('typeset', 'high', r, where, f'{fld} に ¥ 記法の LaTeX 残骸')
                if MOJIBAKE.search(val):
                    add('typeset', 'high', r, where, f'{fld} に文字化け')
            body = f'{stem}\n{expl}'
            if len(TEX_OPEN.findall(body)) != len(TEX_CLOSE.findall(body)):
                add('typeset', 'mid', r, where, r'\( と \) の数が不一致 (KaTeX が描画できない)')

            # --- E. 引用の実在
            if fam == 'english' and ENG_SEC[2] in expl and np_passage:
                # audit.py と同じ切り出し: 「本文の根拠」の 「」 と 誤答NG の ` ` だけを見る。
                # 文構造分析の ` ` は [S][V] 等の解析記号で逐語引用ではない。
                block = expl.split(ENG_SEC[2])[1].split(ENG_SEC[3])[0]
                ngb = expl.split(ENG_SEC[3])[-1] if ENG_SEC[3] in expl else ''
                for quote in re.findall(r'「(.*?)」', block, re.S) + re.findall(r'`(.*?)`', ngb, re.S):
                    for frag in re.split(r'\s*[~〜…]\s*', quote):
                        frag = norm(frag)
                        if len(re.findall(r'[A-Za-z]', frag)) < 12:
                            continue
                        # 日本語が混ざる断片は逐語引用ではなく訳語まじりの説明。照合対象外。
                        if re.search(r'[ぁ-んァ-ヶ一-龥、。]', frag):
                            continue
                        if frag not in np_passage:
                            add('quote', 'high', r, where, f'解説の引用が本文に無い: {frag[:60]}')
            if fam == 'kokugo' and np_passage:
                for m in BOUSEN.finditer(stem):
                    frag = norm(m.group(1))
                    if frag and frag not in np_passage:
                        add('bousen', 'high', r, where, f'傍線部「{frag[:40]}」が本文に無い (下線が引けない)')

            # --- F. 全教材横断の重複
            ns = norm(stem)
            if ns:
                h = hashlib.sha1(ns.encode()).hexdigest()[:16]
                if h in seen_stem:
                    add('dup-stem', 'mid', r, where,
                        f'stem が {seen_stem[h][0]} {seen_stem[h][1]} と同文')
                else:
                    seen_stem[h] = (r['file'], where)

        # --- G. 大問内の正解番号の偏り (ドリル一括行は「大問」ではないので除外)
        if r['exam_id'] != 'drill' and len(daimon_ans) >= 4:
            c = collections.Counter(daimon_ans)
            top, n = c.most_common(1)[0]
            if n / len(daimon_ans) >= 0.5:
                add('bias', 'mid', r, r['label'],
                    f'{CIRCLED[top]} が {n}/{len(daimon_ans)} 問 (大問内で半数以上)')
            run, best, prev = 1, 1, None
            for a in daimon_ans:
                run = run + 1 if a == prev else 1
                best, prev = max(best, run), a
            if best >= 3:
                add('bias', 'mid', r, r['label'], f'同じ番号が {best} 連続')

    return findings, pool_stat, dominant, MOCK


# -------------------------------------------------------------------- 出力
KIND_LABEL = {
    'schema': 'スキーマ欠損 (stem/解説が空 等)',
    'answer': '正解 index 不正 (採点が壊れる)',
    'choices': '選択肢の不備 (同文=正解が2つ 等)',
    'choices-n': '4択でない',
    'type': 'type 未設定',
    'gate-a': '自己完結ゲートで取込拒否',
    'format': 'プール内で解説の型が不揃い',
    'format-lines': '理系解説が3行未満',
    'typeset': '組版事故 (¥/文字化け/括弧不一致)',
    'quote': '解説の引用が本文に無い (捏造引用)',
    'bousen': '傍線部が本文に無い (国語・出題が破綻)',
    'dup-id': '同一大問内の id 重複',
    'dup-stem': '設問文の重複',
    'bias': '正解番号の偏り',
}
SEV_ORDER = {'high': 0, 'mid': 1, 'low': 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--detail', action='store_true')
    ap.add_argument('--json', dest='json_out')
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--kind', nargs='*')
    ap.add_argument('--limit', type=int, default=30, help='--detail で kind ごとに出す件数')
    args = ap.parse_args()

    rows, skipped = load_rows(set(args.only) if args.only else None)
    findings, pool_stat, dominant, MOCK = survey(rows)

    total_q = sum(v['q'] for v in pool_stat.values())
    total_g = sum(v['g'] for v in pool_stat.values())
    files = sorted({r['file'] for r in rows})

    print('=' * 82)
    print(f'seed-data 実測: {len(files)} ファイル / {total_g} 大問 / {total_q} 小問')
    print('=' * 82)
    if skipped:
        print('\n[対象外]')
        for n, why in skipped:
            print(f'  - {n}: {why}')

    by_kind = collections.Counter(f['kind'] for f in findings)
    by_sev = collections.Counter(f['sev'] for f in findings)
    print(f'\n[検出総数]  高={by_sev["high"]}  中={by_sev["mid"]}  低={by_sev["low"]}  合計={len(findings)}')
    for kind, n in sorted(by_kind.items(), key=lambda x: (-x[1], x[0])):
        print(f'  {n:6d}  {kind:12s} {KIND_LABEL.get(kind, "")}')

    print('\n[深刻度「高」= 出題が壊れる/取込が通らない ものだけ再掲]')
    high = [f for f in findings if f['sev'] == 'high']
    if not high:
        print('  なし')
    for kind, n in collections.Counter(f['kind'] for f in high).most_common():
        print(f'  {n:6d}  {kind:12s} {KIND_LABEL.get(kind, "")}')

    print('\n[ファイル別]  小問数 / 高 / 中 / 低')
    per_file = collections.defaultdict(collections.Counter)
    for f in findings:
        per_file[f['file']][f['sev']] += 1
    fq = collections.Counter()
    for r in rows:
        fq[r['file']] += len(r['qd'].get('questions') or [])
    for fn in files:
        c = per_file[fn]
        print(f'  {fn:46s} {fq[fn]:5d}  {c["high"]:5d} {c["mid"]:5d} {c["low"]:5d}'
              + ('   ← 高' if c['high'] else ''))

    print('\n[プール別 解説フォーマット]  多数派の型 / その型に揃っている割合')
    print('  (模) = MOCK_EXAM_TEMPLATES が引く模試プール。server の生成プロンプトが正典')
    fmt_bad = collections.Counter()
    for f in findings:
        if f['kind'] == 'format':
            fmt_bad[tuple(f['pool'].split('/', 1))] += 1
    for pkey, v in sorted(pool_stat.items(), key=lambda x: -x[1]['q']):
        if not v['q']:
            continue
        dom = sorted(dominant.get(pkey, set()))
        bad = fmt_bad[pkey]
        pct = 100 * (v['q'] - bad) / v['q']
        tag = '(模)' if pkey in MOCK else '   '
        label = '/'.join(pkey)
        print(f'  {tag}{label:34s} {v["q"]:5d}問  揃い {pct:5.1f}%  型= {"+".join(dom) or "(型なし・自由記述)"}')

    print('\n[模試プールの多数派 vs server/main.py の正典]')
    any_mismatch = False
    for pkey, v in sorted(pool_stat.items()):
        if pkey not in MOCK or not v['q']:
            continue
        canon = CANON[v['fam']]
        if not canon:
            print(f'  {"/".join(pkey):34s} 正典が未定義 (server に専用プロンプト無し)')
            any_mismatch = True
            continue
        dom = dominant.get(pkey, set())
        want = {c.split('|')[0] for c in canon}
        keymap = {'🎯 コアイメージ': 'コアイメージ', '🔬 文構造分析': '文構造分析',
                  '📍 本文の根拠': '本文の根拠', '❌ 誤答 NG 理由': '誤答NG',
                  '現代語訳': '現代語訳', '解答の根拠': '解答の根拠', '誤答 NG 理由': '誤答NG',
                  '考え方': '考え方', '立式': '立式', '計算': '計算', '答え': '答え'}
        want = {keymap.get(w, w) for w in want}
        miss = want - dom
        if miss:
            any_mismatch = True
            print(f'  {"/".join(pkey):34s} 正典に対し多数派が欠く: {"/".join(sorted(miss))}')
    if not any_mismatch:
        print('  すべて一致')

    if args.detail:
        print('\n[明細]')
        want = set(args.kind) if args.kind else None
        shown = collections.Counter()
        for f in sorted(findings, key=lambda x: (SEV_ORDER[x['sev']], x['kind'], x['file'])):
            if want and f['kind'] not in want:
                continue
            if shown[f['kind']] >= args.limit:
                continue
            shown[f['kind']] += 1
            print(f'  [{f["sev"]:4s}] {f["kind"]:12s} {f["file"]} {f["where"]}: {f["msg"]}')
        for k, n in shown.items():
            if by_kind[k] > n:
                print(f'  … {k} は他 {by_kind[k] - n} 件 (--kind {k} --limit 9999 で全件)')

    if args.json_out:
        with open(args.json_out, 'w', encoding='utf-8') as f:
            json.dump({'files': len(files), 'groups': total_g, 'questions': total_q,
                       'by_kind': dict(by_kind), 'by_sev': dict(by_sev),
                       'findings': findings}, f, ensure_ascii=False, indent=1)
        print(f'\nJSON 出力: {args.json_out}')

    return 0   # measure-only


if __name__ == '__main__':
    sys.exit(main())
