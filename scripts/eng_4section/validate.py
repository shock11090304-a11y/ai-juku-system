#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語 r_short/r_long プールの解説を 4 セクション形式で検証する。

server/main.py の英語生成プロンプトが正典:
  ## 🎯 コアイメージ → ## 🔬 文構造分析 → ## 📍 本文の根拠 → ## ❌ 誤答 NG 理由
  「1セクションでも欠けたら不合格」

kyotsu_mogi2026/audit.py は自分が作った模試だけを見る。こちらは既存プール
(dojo_eng_kyotsu2026_*) を同じ基準で検証するために切り出した汎用版。

検査項目:
  A. 4 セクションが規定の順で揃っている            ← 正典が明示的に要求する唯一の条件
  B. 冒頭に 「正解は「…」。」 がある場合、その中身が answer と一致する
  C. 📍本文の根拠 が引用した英文が passage に逐語で実在する (捏造引用の検出)
  D. ❌誤答 NG 理由 が誤答の数だけあり、行頭で引く誤答が実際の誤答と対応する
  E. 🔬文構造分析 が「本文/設問文/選択肢のいずれにも無い文」を解析していない

★ 較正の方針: 正典 (server の生成プロンプト) が求めていない“流儀”を条件にしない。
  リポジトリには少なくとも 2 つの流儀があり、どちらも正典に反しない:
    - dojo_eng_kyotsu2026 系: 冒頭に「正解は「X」。」を置き、誤答を本文で引く
    - batch_v* 系:          冒頭宣言なし、誤答を「選択肢1:」と番号で指す
  そのため B は「宣言がある場合だけ」、D は「行数の一致 + 引いている場合の対応」に留める。
  また C と E は性質が違う。本文の根拠は逐語引用なので完全一致を求めるが、
  文構造分析は [S] [V] や (that) を挿し込んで示す節なので逐語一致しない。
  E は語順が復元できるかだけを見る。対象も本文とは限らず、設問文や選択肢
  (部分否定 not always の構造など) を解析するのも正当。

実行: python3 scripts/eng_4section/validate.py [seed ファイル名...]
      省略時は r_short/r_long を持つ seed を全部見る
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED_DIR = os.path.join(ROOT, 'seed-data')

SECTIONS = ('## 🎯 コアイメージ', '## 🔬 文構造分析', '## 📍 本文の根拠', '## ❌ 誤答 NG 理由')
TARGET_POOLS = {('daigaku', 'r_short'), ('daigaku', 'r_long')}


def norm(s):
    """引用照合用の正規化 (audit.py と同じ方針)。"""
    s = (s or '').replace('**', '').replace('`', '')
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('　', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def qkey(s):
    """大文字小文字と引用符の種類の差を吸収したキー。"""
    return re.sub(r"['\"]", '', norm(s).lower())


def eng_fragments(block):
    """ブロック中の 「」 / ` ` から、照合対象になる英文断片を取り出す。

    - 中略記号 (… 〜 ~ ...) で切って断片ごとに見る
    - 英字 12 文字未満は語法メモなので対象外
    - 日本語混じりは訳語まじりの説明なので対象外
    - A/B のプレースホルダを含む構文の雛形も対象外
    """
    out = []
    for quote in re.findall(r'「(.*?)」', block, re.S) + re.findall(r'`(.*?)`', block, re.S):
        if re.search(r'[~〜]', quote) and not re.search(r'\.\.\.|…', quote):
            continue
        for frag in re.split(r'\s*(?:\.\.\.|[~〜…])\s*', quote):
            frag = norm(frag)
            if len(re.findall(r'[A-Za-z]', frag)) < 12:
                continue
            if re.search(r'[ぁ-んァ-ヶ一-龥、。]', frag):
                continue
            if len(re.findall(r'(?<![A-Za-z])[A-F](?![A-Za-z])', frag)) >= 2:
                continue
            if ' + ' in frag:
                continue
            out.append(frag)
    return out


def _words_in_order(frag, passage):
    """引用の語が本文に同じ順で、近接して並んでいるか。

    文構造分析は本文の文に [S] [V] [O] や (that) を挿し込んで示すため逐語一致
    しない。挿入記号を飛ばして本文の語順を復元できるかどうかで判定する。
    許容する挿入量は引用語数の 1.5 倍まで。
    """
    # (that) / (which) は「本文では省略されている語」を補って示す注記なので、
    # 本文側には存在しない。照合の前に括弧ごと落とす。
    frag = re.sub(r'\([^)]{0,20}\)', ' ', frag)
    # [S] [V] の角括弧は語の途中にも入る ([I]'d)。先に外さないと語が割れて
    # 本文側の I'd と一致しなくなる。
    frag = frag.replace('[', '').replace(']', '')
    words = re.findall(r"[A-Za-z']+", frag.lower())
    if len(words) < 3:
        return True
    hay = re.findall(r"[A-Za-z']+", (passage or '').lower())
    # 構造分析は本文の文を圧縮して示すこともある (修飾句をまるごと省く)。
    # 見たいのは「本文に無い文を解析していないか」なので窓は広めに取る。
    limit = len(words) * 5 + 20
    for start in range(len(hay)):
        if hay[start] != words[0]:
            continue
        wi, hi = 1, start + 1
        while wi < len(words) and hi < len(hay) and hi - start <= limit:
            if hay[hi] == words[wi]:
                wi += 1
            hi += 1
        if wi == len(words):
            return True
    return False


def check_question(tag, q, passage, errors, figure_svg=''):
    exp = q.get('explanation') or ''
    choices = q.get('choices') or []
    try:
        ans = int(q.get('answer'))
    except (TypeError, ValueError):
        errors.append(f'{tag}: answer が index として読めない')
        return
    if not (0 <= ans < len(choices)):
        errors.append(f'{tag}: answer={ans} が choices の範囲外')
        return

    # A. 4 セクションが規定の順で
    pos = []
    for sec in SECTIONS:
        i = exp.find(sec)
        if i < 0:
            errors.append(f'{tag}: 必須セクション「{sec}」が無い')
            return
        pos.append(i)
    if pos != sorted(pos):
        errors.append(f'{tag}: 4 セクションの順序が規定と違う')

    # B. 冒頭に正答宣言がある場合のみ、それが answer と一致するかを見る。
    #    宣言そのものは正典 (server の生成プロンプト) の要求ではなく
    #    dojo_eng_kyotsu2026 系の慣行なので、無いこと自体は不良としない。
    m = re.match(r'正解は「(.+?)」。', exp, re.S)
    if m and norm(m.group(1)) != norm(choices[ans]):
        errors.append(f'{tag}: 冒頭の「正解は…」が answer と食い違う\n'
                      f'      解説: {m.group(1)[:60]}\n      answer: {choices[ans][:60]}')

    # C. 「本文の根拠」の引用は passage に逐語で実在すること (捏造引用の検出)。
    #    図 (Source B 等) のラベルも根拠として引けるので、図中の <text> も照合先に含める。
    #    図は本文と並ぶ資料であって、本文外の捏造ではない。
    fig_text = ' '.join(re.sub(r'<[^>]+>', '', t)
                        for t in re.findall(r'<text[^>]*>(.*?)</text>', figure_svg or '', re.S))
    npass = qkey(passage + '\n' + fig_text)
    for frag in eng_fragments(exp[pos[2]:pos[3]]):
        if qkey(frag) not in npass:
            errors.append(f'{tag}: 「本文の根拠」の引用が本文に無い\n      引用: {frag[:90]}')

    # E. 「文構造分析」は [S] [V] や (that) といった解析記号を本文に挿し込んで示す節
    #    なので、逐語一致は求めない。語が本文と同じ順に並んでいるか (挿入記号を
    #    飛ばして復元できるか) だけを見る。並んでいなければ、本文に無い文を
    #    構造解析していることになる。
    # 構造分析の対象は本文の文とは限らない。設問文そのもの (設問の読み違い防止) や
    # 選択肢 (部分否定 not always の構造など) を解析するのも正当なので、
    # 照合先は 本文 + stem + choices の 3 つ。
    hay_struct = '\n'.join([passage, fig_text, q.get('stem') or ''] + [str(c) for c in choices])
    for frag in eng_fragments(exp[pos[1]:pos[2]]):
        if not _words_in_order(frag, hay_struct):
            errors.append(f'{tag}: 「文構造分析」が本文に無い文を解析している\n      引用: {frag[:90]}')

    # D. 誤答 NG 理由が誤答の数だけあるか。
    #    指し方はファイルによって違う (誤答の本文を引くもの / 「選択肢1:」と番号で指すもの)。
    #    どちらも正典に反しないので、行数の一致だけを共通の条件にする。
    ng = exp[pos[3]:]
    lines = [l for l in ng.splitlines() if l.strip().startswith(('-', '・'))]
    distractors = [c for i, c in enumerate(choices) if i != ans]
    if len(lines) != len(distractors):
        errors.append(f'{tag}: 誤答 NG 理由が {len(lines)} 行 (誤答は {len(distractors)} 個)')
        return
    # 行頭の 「…」 が「その行が扱う誤答」。前方一致で探すと短い選択肢 (MemoRise 等) や
    # 語順だけ違う選択肢が別の行にも現れて誤検出になるので、行頭の引用を完全一致で見る。
    quoted = [norm(m.group(1)) for m in
              (re.match(r'\s*[-・]\s*「(.+?)」', l) for l in lines) if m]
    if quoted:
        want = {norm(d) for d in distractors}
        missing = want - set(quoted)
        if missing:
            errors.append(f'{tag}: 誤答「{sorted(missing)[0][:45]}」に対応する NG 理由が無い')
        if norm(choices[ans]) in quoted:
            errors.append(f'{tag}: 正答が誤答 NG 理由の見出しに置かれている')


def main():
    names = sys.argv[1:]
    paths = ([os.path.join(SEED_DIR, n) for n in names] if names
             else sorted(glob.glob(os.path.join(SEED_DIR, '*.json'))))
    errors, checked, files = [], 0, 0
    for path in paths:
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            continue
        rows = data.get('questions') if isinstance(data, dict) else None
        if not isinstance(rows, list):
            continue
        hit = False
        for r in rows:
            if not isinstance(r, dict):
                continue
            if (r.get('exam_id'), r.get('part_key')) not in TARGET_POOLS:
                continue
            qd = r.get('question_data') or {}
            passage = qd.get('passage') or ''
            label = qd.get('format_type') or qd.get('group') or '?'
            for i, q in enumerate(qd.get('questions') or []):
                hit = True
                checked += 1
                check_question(f'{os.path.basename(path)}/{label} 問{i + 1}', q, passage, errors,
                               qd.get('figure_svg') or '')
        if hit:
            files += 1

    print(f'点検: {files} ファイル / {checked} 小問')
    if errors:
        print(f'\n❌ {len(errors)} 件:')
        for e in errors[:60]:
            print('   -', e)
        if len(errors) > 60:
            print(f'   … 他 {len(errors) - 60} 件')
        return 1
    print('✅ 4 セクション形式 全項目 OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
