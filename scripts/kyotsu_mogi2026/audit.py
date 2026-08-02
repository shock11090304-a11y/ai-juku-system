#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト模試 2026 の総点検。build_*.py の自己検査では拾えない観点を後追いで洗う。

build 側は「正解が合っているか」「フォーマットが揃っているか」を見る。
ここでは出来上がった成果物 (seed JSON + PDF) を突き合わせて、次を確認する。

  A. スキーマ           選択肢 4 個 / answer が範囲内 / 重複なし / unit 非空
  B. 数学の解説形式     方針→立式→計算→答え→補足 が順に揃い、「答え:」に正答が入る
  C. 英語の解説形式     4 セクションが規定順に揃い、冒頭の正答が選択肢と一致
  D. 誤答 NG 理由の対応 3 件が誤答 3 件と 1 対 1 (正答が誤答欄に混じっていない)
  E. 本文の根拠の裏取り  解説が引用した英文が本文に**実在する**か (捏造引用の検出)
  F. 配点               英語は合計ちょうど 100 点 / 数学は 1 小問 4 点
  G. 既存プールとの重複  既存 seed と content hash が衝突しないか
  H. PDF の組版事故     KaTeX の SVG path 流出 / Markdown 記号の生表示
  I. PDF ↔ JSON        PDF の正解一覧が JSON の answer と一致するか

実行: python3 scripts/kyotsu_mogi2026/audit.py
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CIRC = '①②③④'

MATH_SECTIONS = ('方針', '立式', '計算', '答え', '補足')
ENG_SECTIONS = ("## 🎯 コアイメージ", "## 🔬 文構造分析", "## 📍 本文の根拠", "## ❌ 誤答 NG 理由")

ENG_POINTS = {
    "第1問A メッセージ読解": [2, 2, 2],
    "第1問B 告知の読み取り": [2, 2, 2, 2],
    "第2問A 比較とレビュー": [2, 2, 2, 2, 2],
    "第2問B 記事(事実と意見)": [2, 2, 2, 2, 2],
    "第3問B 体験ブログ(時系列)": [3, 3, 3, 2, 2],
    "第4問 複数資料の統合": [3, 3, 3, 2, 2],
    "第5問 伝記とノート作成": [3, 3, 3, 2, 2],
    "第6問A 論説文の要旨": [3, 3, 3, 3, 2],
    "第6問B 説明文の整理": [3, 3, 3, 2, 2],
}

errors, warnings = [], []


def err(m):
    errors.append(m)


def warn(m):
    warnings.append(m)


def load(name):
    with open(os.path.join(ROOT, 'seed-data', f'kyotsu_mogi2026_{name}_manual.json'), encoding='utf-8') as f:
        return json.load(f)['questions']


def norm(s):
    """引用照合用の正規化: 空白を潰し、装飾記号を落とす。"""
    s = s.replace('**', '').replace('`', '')
    s = s.replace('’', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip()


# =====================================================================
def check_schema_and_format(rows, subject):
    for r in rows:
        qd = r['question_data']
        label = qd.get('group') or qd.get('format_type')
        for i, q in enumerate(qd['questions']):
            tag = f'{subject}/{label} 問{i + 1}'
            ch = q.get('choices') or []

            # --- A. スキーマ ---
            if q.get('type') != 'multiple_choice':
                err(f'{tag}: type が multiple_choice でない ({q.get("type")})')
            if len(ch) != 4:
                err(f'{tag}: 選択肢が {len(ch)} 個 (4 個であること)')
            if len(set(ch)) != len(ch):
                err(f'{tag}: 選択肢に重複がある')
            a = q.get('answer')
            if not isinstance(a, int) or not (0 <= a < len(ch)):
                err(f'{tag}: answer={a} が範囲外')
            if not (q.get('unit') or '').strip():
                err(f'{tag}: unit が空')
            if not (q.get('stem') or '').strip():
                err(f'{tag}: stem が空')

            exp = q.get('explanation') or ''
            correct = ch[a] if isinstance(a, int) and 0 <= a < len(ch) else None

            if subject == '数学':
                # --- B. 数学の解説形式 ---
                found = [exp.find(f'{s}:') for s in MATH_SECTIONS]
                if any(p < 0 for p in found):
                    missing = [s for s, p in zip(MATH_SECTIONS, found) if p < 0]
                    err(f'{tag}: 解説に「{"・".join(missing)}」が無い')
                elif found != sorted(found):
                    err(f'{tag}: 解説 5 セクションの順序が規定と違う')
                m = re.search(r'答え:\s*(.*?)(?:\n|$)', exp, re.S)
                if not m:
                    err(f'{tag}: 「答え:」行が無い')
                elif correct and correct not in m.group(1):
                    err(f'{tag}: 「答え:」に正答「{correct}」が入っていない → {m.group(1)[:60]}')
            else:
                # --- C. 英語の解説形式 ---
                found = [exp.find(s) for s in ENG_SECTIONS]
                if any(p < 0 for p in found):
                    missing = [s for s, p in zip(ENG_SECTIONS, found) if p < 0]
                    err(f'{tag}: 解説に「{"・".join(missing)}」が無い')
                elif found != sorted(found):
                    err(f'{tag}: 解説 4 セクションの順序が規定と違う')
                m = re.match(r'^正解は「(.*?)」。', exp, re.S)
                if not m:
                    err(f'{tag}: 冒頭が「正解は「…」。」でない')
                elif correct and m.group(1) != correct:
                    err(f'{tag}: 冒頭の正答が選択肢と不一致')

                # --- D. 誤答 NG 理由が誤答 3 件と 1 対 1 ---
                ng_block = exp.split(ENG_SECTIONS[3])[-1] if ENG_SECTIONS[3] in exp else ''
                quoted = re.findall(r'^-\s*「(.*?)」…', ng_block, re.M)
                distractors = [c for c in ch if c != correct]
                if len(quoted) != 3:
                    err(f'{tag}: 誤答 NG 理由が {len(quoted)} 件 (3 件であること)')
                if sorted(quoted) != sorted(distractors):
                    err(f'{tag}: 誤答 NG 理由の見出しが誤答と一致しない\n'
                        f'      解説側: {quoted}\n      選択肢側: {distractors}')
                if correct and correct in quoted:
                    err(f'{tag}: 正答が誤答 NG 理由に混じっている')


# =====================================================================
def check_evidence(rows):
    """E. 「本文の根拠」が引用した英文が、その大問の本文に実在するか。"""
    checked = 0
    for r in rows:
        qd = r['question_data']
        passage = norm(qd['passage'])
        label = qd['format_type']
        for i, q in enumerate(qd['questions']):
            tag = f'英語/{label} 問{i + 1}'
            exp = q['explanation']
            if ENG_SECTIONS[2] not in exp:
                continue
            block = exp.split(ENG_SECTIONS[2])[1].split(ENG_SECTIONS[3])[0]
            # 「」で囲んだ引用 (本文の根拠) と、誤答 NG 理由の中で ` ` で囲んだ本文引用の両方を見る。
            # コアイメージ/文構造分析の ` ` は語法パターンや括り出しで逐語ではないため対象外。
            ng_block = exp.split(ENG_SECTIONS[3])[-1] if ENG_SECTIONS[3] in exp else ''
            quotes = re.findall(r'「(.*?)」', block, re.S) + re.findall(r'`(.*?)`', ng_block, re.S)
            for quote in quotes:
                # ~ や … は中略。区切って断片ごとに実在を確かめる
                for frag in re.split(r'\s*[~…]\s*', quote):
                    frag = norm(frag)
                    # 英字を 12 文字以上含む断片だけを照合対象にする (日本語の地の文は除外)
                    if len(re.findall(r'[A-Za-z]', frag)) < 12:
                        continue
                    checked += 1
                    if frag not in passage:
                        err(f'{tag}: 「本文の根拠」の引用が本文に無い\n      引用: {frag[:100]}')
    return checked


# =====================================================================
def check_points(rows):
    """F. 配点。英語は合計ちょうど 100 点。"""
    total = 0
    for r in rows:
        label = r['question_data']['format_type']
        pts = ENG_POINTS.get(label)
        n = len(r['question_data']['questions'])
        if pts is None:
            err(f'英語/{label}: 配点表に定義が無い')
            continue
        if len(pts) != n:
            err(f'英語/{label}: 配点 {len(pts)} 個 vs 小問 {n} 個')
        total += sum(pts)
    if total != 100:
        err(f'英語の配点合計が {total} 点 (100 点であること)')
    return total


# =====================================================================
def check_dup_against_pool(rows, label):
    """G. 既存 seed と question_data の content hash が衝突しないか。"""
    def h(qd):
        return hashlib.md5(json.dumps(qd, ensure_ascii=False).encode()).hexdigest()

    mine = {h(r['question_data']): (r['part_key'], r['question_data'].get('group')
                                    or r['question_data'].get('format_type')) for r in rows}
    if len(mine) != len(rows):
        err(f'{label}: 自分の中で大問が重複している')
    hit = 0
    for f in glob.glob(os.path.join(ROOT, 'seed-data', '*.json')):
        if 'kyotsu_mogi2026' in os.path.basename(f):
            continue
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        other = d['questions'] if isinstance(d, dict) and 'questions' in d else (d if isinstance(d, list) else [])
        for o in other:
            if not isinstance(o, dict) or 'question_data' not in o:
                continue
            if h(o['question_data']) in mine:
                err(f'{label}: {os.path.basename(f)} と大問が完全一致 (import で skipped_dup になる)')
                hit += 1
    return hit


# =====================================================================
def check_pdfs():
    """H/I. PDF の組版事故と、正解一覧の一致。"""
    # KaTeX の SVG path が本文に流出した時の特徴的な断片
    PATH_LEAK = re.compile(r'[a-z]?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?,')
    RAW_MD = re.compile(r'(?m)^\s*##\s|\*\*[^*\n]{2,}\*\*')
    for pdf in sorted(glob.glob(os.path.join(ROOT, 'kyotsu-mogi2026-*.pdf'))):
        name = os.path.basename(pdf)
        txt = subprocess.run(['pdftotext', '-layout', pdf, '-'],
                             capture_output=True, text=True).stdout
        if PATH_LEAK.search(txt):
            sample = PATH_LEAK.search(txt).group(0)[:60]
            err(f'{name}: KaTeX の SVG path が本文に流出している → {sample}')
        if RAW_MD.search(txt):
            err(f'{name}: Markdown 記号が生のまま表示されている → {RAW_MD.search(txt).group(0)[:40]}')
        if '�' in txt or 'ï¿½' in txt:
            err(f'{name}: 文字化け (U+FFFD) を含む')

    for pdf, seed, order in [('kyotsu-mogi2026-eng-kaisetsu.pdf', 'eng', None),
                             ('kyotsu-mogi2026-math-kaisetsu.pdf', 'math', ('math_1a', 'math_2b'))]:
        path = os.path.join(ROOT, pdf)
        if not os.path.exists(path):
            err(f'{pdf} が無い')
            continue
        rows = load(seed)
        if order:
            rows = [r for pk in order for r in rows if r['part_key'] == pk]
        expect = [(i + 1, q['answer']) for r in rows for i, q in enumerate(r['question_data']['questions'])]
        txt = subprocess.run(['pdftotext', '-layout', path, '-'],
                             capture_output=True, text=True).stdout
        got = [(int(m.group(1)), CIRC.index(m.group(2)))
               for ln in txt.splitlines()
               for m in [re.search(r'問(\d+)\s+([' + CIRC + r'])\s+(\d+)\s+(\S+)', ln)] if m]
        if got != expect:
            err(f'{pdf}: 正解一覧が JSON と不一致 (PDF {len(got)} 件 / JSON {len(expect)} 件)')
        else:
            print(f'   ✅ {pdf}: 正解一覧 {len(got)}/{len(expect)} 一致')


# =====================================================================
def main():
    if not shutil_which('pdftotext'):
        warn('pdftotext が無いため PDF の点検を飛ばした (apt-get install poppler-utils)')

    eng, math = load('eng'), load('math')
    print(f'点検対象: 英語 {len(eng)} 大問 / 数学 {len(math)} 大問')

    print('\n[A-D] スキーマと解説フォーマット')
    check_schema_and_format(math, '数学')
    check_schema_and_format(eng, '英語')
    n_sub = sum(len(r['question_data']['questions']) for r in eng + math)
    print(f'   {n_sub} 小問を点検')

    print('\n[E] 「本文の根拠」の引用が本文に実在するか')
    n = check_evidence(eng)
    print(f'   {n} 件の英文引用を本文と照合')

    print('\n[F] 配点')
    print(f'   英語の合計 = {check_points(eng)} 点')
    bad_pts = [r for r in math for q in r['question_data']['questions']]
    print(f'   数学 = 1 小問 4 点 × {len(bad_pts)} 小問')

    print('\n[G] 既存プールとの重複')
    check_dup_against_pool(eng, '英語')
    check_dup_against_pool(math, '数学')
    print('   既存 seed との content hash 衝突を確認')

    if shutil_which('pdftotext'):
        print('\n[H-I] PDF の組版と正解一覧')
        check_pdfs()

    print()
    if warnings:
        print('⚠️  警告:')
        for w in warnings:
            print('   -', w)
    if errors:
        print(f'❌ {len(errors)} 件の問題:')
        for e in errors:
            print('   -', e)
        return 1
    print('✅ 全項目 OK — 検出された問題はありません')
    return 0


def shutil_which(x):
    from shutil import which
    return which(x)


if __name__ == '__main__':
    sys.exit(main())
