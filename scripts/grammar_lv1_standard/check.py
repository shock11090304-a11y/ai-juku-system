#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高校英文法レベル1 標準演習 (偏差値55-60) の機械ゲート。

    python3 scripts/grammar_lv1_standard/check.py

★引数を取らない。引数で対象が変わるゲートは「見本を検査して緑」になる事故を起こすので
  (CLAUDE.md 2026-08-04)、対象は units/ 全部で固定し、何を見たかを必ず印字する。

■ 見るもの
  A 素データ同期  units/*.json が content/*.py から作り直したものと1バイト違わないか
                  (JSON を直接編集すると make_units.py の保証が全部無効になる)
  B 構造          件数・番号・type・level・必須フィールド
  C mc            選択肢4つ・重複なし・answer_index と answer_text の一致・( ) の有無
  D 正解の偏り    単元内で 0-3 が 4-5 回ずつ／同じ位置が3連続していないか
  E 最長肢テル    正解が常に一番長い選択肢になっていないか
  F 整序の漏洩    tokens が答えと同じ並びになっていないか／語の過不足がないか
                  ★既存 scripts/grammar_workbook で実際に4問漏れていた型
  G 語順の一意性  大文字で始まる語(固有名詞と I を除く)が文頭の1語だけか
                  = 生徒が別の正解を作れる余地を機械で潰す
  H 解答漏洩      書き換えの答えが問題編の印字テキストに出ていないか
  I 解説          3文以上／正解の語を含む／**誤答3つすべてに言及**しているか
                  (英語の解説は誤答 NG 理由が必須。CLAUDE.md)
                  ★選択肢は make_units.py が並べ替えるので、解説に丸数字を書いてはいけない
  J 禁止文字      スマートクオート・ダッシュ・不可視スペース・絵文字
  K 重複          同じ設問文・同じ答えを2度聞いていないか

■ 判定
  違反が1件でもあれば sys.exit(1)。「印字するだけ」にしないこと(CLAUDE.md)。
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS_DIR = os.path.join(HERE, "units")
sys.path.insert(0, HERE)

import make_units  # noqa: E402

EXPECT = [
    ("01_tenses.json", "時制"),
    ("02_infinitive.json", "不定詞"),
    ("03_gerund.json", "動名詞"),
    ("04_subjunctive.json", "仮定法"),
]
EXPECT_PER_FILE = 30
EXPECT_TYPE_MIX = {"mc": 18, "order": 7, "rewrite": 5}   # 1単元あたり
EXPECT_TOTAL = len(EXPECT) * EXPECT_PER_FILE
LEVELS = ("standard", "advanced")

ENG_FIELDS = ("stem", "answer_text", "original")
JA_FIELDS = ("prompt_ja", "instruction", "point", "explanation")
LIST_FIELDS = ("choices", "tokens")
META_KEYS = {"level", "type"}

# 禁止文字: スマートクオート/各種ダッシュ/三点リーダ/不可視スペース。
# ★リテラル文字列で書かない。grammar_workbook/validate.py はここを1本の文字列で持っており、
#   写すときに NBSP(U+00A0) が素の空白(U+0020)に化けても目で見て分からない。
#   実際この検査を書き起こしたとき化けて、英文の空白 4190 個を全部違反として数えた。
#   コードポイントで並べれば、化けたら SyntaxError か目視で分かる。
SMART = "".join(chr(c) for c in (
    0x2018, 0x2019, 0x201C, 0x201D,   # スマートクオート
    0x2013, 0x2014, 0x2015, 0x2026,   # en/em ダッシュ・水平線・三点リーダ
    0x00A0, 0x3000, 0x202F,           # NBSP・全角スペース・narrow NBSP
    0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD,   # 不可視文字
))
# 和文フィールドでだけ許す文字(何をなぜ許したかと件数を必ず印字する)
ALLOW_IN_JA = {
    "…": "和文として正しい三点リーダ。build_pdf.py の clean() が描画前に '...' へ直すので紙にも出ない"
         "(grammar_workbook/validate.py と同じ扱い)",
    "　": "和文の全角スペース。grammar_workbook/validate.py の従来の許容に合わせる",
}

# ★整序の「語順の一意性」検査で、文頭候補から除外してよい大文字語。
#   固有名詞は文中でも大文字なので、これを除外しないと誤検出になる。
#   ここに足すのは**実データに出る固有名詞だけ**。黙って足さず、下で件数を印字する。
PROPER_NOUNS = {"Tokyo"}
# I / I am の短縮など、常に大文字になる一人称。
ALWAYS_CAP = {"I"}

# ★整序で「答えが2通りになる」原因の語。英語では位置が動くので、
#   模範解答と違う語順を書いた生徒を不当に×にしてしまう。
#   2026-08-17 の再点検で、120問中6問がこれで2通りの正解を持っていた:
#     had already left / had left already      (時制)
#     is being built now / is now being built  (時制)
#     since I last saw him / since I saw him last (時制)
#     three hours doing ... yesterday / three hours yesterday doing ... (動名詞)
#     would be in Tokyo now / would now be in Tokyo (仮定法)
#     turn down the offer / turn the offer down    (仮定法・分離可能な句動詞)
#   → これらの語を含む整序は**1問ずつ理由を書いて宣言する**。宣言の無いものは落とす。
MOBILE_ADVERBS = {
    "now", "already", "just", "yesterday", "today", "tomorrow", "again",
    "soon", "still", "last", "once", "always", "often", "never", "ever",
    "early", "earlier",
}
# 分離可能な句動詞の副詞小辞。目的語の前後どちらにも置けるので同じ事故を起こす。
PARTICLES = {"down", "up", "off", "out", "away", "back", "over", "on", "in"}

# 宣言済み（位置が動かない、または動かしても別の語順にならないと確認したもの）。
# ★「うるさいから」で足さないこと。1問ずつ英語で確かめてから理由を書く。
ORDER_ADVERB_OK = {
    ("時制", 19): "soon は as soon as という一つの接続詞の一部。単独では動かせない",
    ("時制", 20): "just は助動詞と過去分詞の間にしか置けない (had just left)。文末に出せない",
    ("時制", 21): "back は get back という自動詞句の一部。目的語をとらないので分離しない",
    ("時制", 25): "tomorrow は文末。to the party の間に割り込む語順は英語として作られない",
    ("不定詞", 20): "in は swim in の前置詞が文末に残った形。前に出す先の名詞が tokens に無い",
    ("不定詞", 22): "early は動詞句の直後に固定 (Leave home early)。so as 以下へは動かせない",
    ("不定詞", 25): "up は grow up という自動詞句の一部。目的語をとらないので分離しない",
    ("動名詞", 20): "again は see の目的語の後ろに固定。to seeing の間には入れない",
    ("動名詞", 22): "up は get up の一語扱いで分離しない自動詞句。early はその直後に固定",
    ("動名詞", 25): "On は分詞句を導く前置詞で、答えの文頭語そのもの。動かしようがない",
    ("仮定法", 23): "at once は文末の副詞句。let me know の間に割り込む語順は作られない",
}


def find_bad_chars(s, allow=()):
    bad = []
    for ch in s:
        if ch in allow:
            continue
        o = ord(ch)
        if ch in SMART:
            bad.append(("smart/space", ch))
        elif o < 0x20 and ch not in "\n\t":
            bad.append(("ctrl", ch))
        elif o >= 0x1F000 or (0x2600 <= o <= 0x27BF) or (0x1F300 <= o <= 0x1FAFF):
            bad.append(("emoji", ch))
    return bad


def norm_words(s):
    s = s.lower()
    s = re.sub(r'[.,?!;:"]', " ", s)
    return sorted(w for w in s.split() if w)


def main():
    problems = []
    ledger = []
    bad_chars = []
    total = inspected = halted = files_read = 0
    strings_scanned = 0
    per_field = Counter()
    seen_keys = set()
    type_counts = Counter()
    level_counts = Counter()
    per_file_types = {}
    pos_by_unit = {}
    longest_tell = Counter()   # 正解が最長タイ以上だった数(単元ごと)
    mc_seen = Counter()
    proper_noun_hits = Counter()
    adverb_declared = {}
    allowed_hits = {ch: 0 for ch in ALLOW_IN_JA}
    all_stems = []          # (tag, 設問文) 重複検出用
    all_answers = []        # (tag, 答え)   重複検出用

    # ---- A 素データ同期 ----
    try:
        built = make_units.build_all()
    except Exception as e:                       # noqa: BLE001
        problems.append(f"[SRC BUILD] content/*.py から組み立てられない: {e}")
        built = {}
    for fname, _unit in EXPECT:
        path = os.path.join(UNITS_DIR, fname)
        if fname not in built or not os.path.exists(path):
            continue
        want = json.dumps(built[fname], ensure_ascii=False, indent=1) + "\n"
        with open(path, encoding="utf-8") as f:
            got = f.read()
        if got != want:
            problems.append(f"[SRC SYNC] {fname}: content/*.py から作り直した内容と一致しない"
                            "(units/ を直接編集した。content/ を直して make_units.py を回すこと)")

    # ---- B..K 本体 ----
    for fname, unit in EXPECT:
        path = os.path.join(UNITS_DIR, fname)
        if not os.path.exists(path):
            problems.append(f"[MISSING] {fname}")
            continue
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:               # noqa: BLE001
                problems.append(f"[JSON ERROR] {fname}: {e}")
                continue
        files_read += 1
        if data.get("unit") != unit:
            problems.append(f"[UNIT NAME] {fname}: {data.get('unit')!r} != {unit!r}")
        qs = data.get("questions", [])
        if len(qs) != EXPECT_PER_FILE:
            problems.append(f"[COUNT] {fname}: {len(qs)} 問 (期待 {EXPECT_PER_FILE})")
        if sorted(q.get("no") for q in qs) != list(range(1, len(qs) + 1)):
            problems.append(f"[NO SEQ] {fname}: 番号が 1..{len(qs)} の連番でない")

        ft = Counter(q.get("type") for q in qs)
        per_file_types[fname] = ft
        for t, want in EXPECT_TYPE_MIX.items():
            if ft.get(t, 0) != want:
                problems.append(f"[TYPE MIX] {fname}: {t} が {ft.get(t, 0)} 問 (期待 {want})")

        # 問題編に印字されるテキスト(答えは含まない)。H の解答漏洩で使う
        printed = []
        for q in qs:
            printed += [str(q.get("stem", "")), str(q.get("prompt_ja", "")),
                        str(q.get("original", "")), str(q.get("instruction", ""))]
            printed += [str(c) for c in (q.get("choices") or [])]
            printed += [str(c) for c in (q.get("tokens") or [])]
        printed_text = " ".join(printed)

        positions = []
        for q in qs:
            total += 1
            t = q.get("type")
            tag = f"{unit}#{q.get('no')}"
            if t not in EXPECT_TYPE_MIX:
                problems.append(f"[TYPE] {tag}: 未知の type {t!r}")
                halted += 1
                continue
            type_counts[t] += 1
            lv = q.get("level")
            if lv not in LEVELS:
                problems.append(f"[LEVEL] {tag}: {lv!r} (期待 {LEVELS})")
            else:
                level_counts[lv] += 1

            for k, v in q.items():
                if isinstance(v, str) or (isinstance(v, list) and v
                                          and all(isinstance(x, str) for x in v)):
                    seen_keys.add(k)

            # ---- J 禁止文字 ----
            for fld in ENG_FIELDS + JA_FIELDS:
                v = q.get(fld)
                if not isinstance(v, str):
                    continue
                strings_scanned += 1
                per_field[fld] += 1
                allow = ALLOW_IN_JA if fld in JA_FIELDS else ()
                if fld in JA_FIELDS:
                    for ch in v:
                        if ch in ALLOW_IN_JA:
                            allowed_hits[ch] += 1
                for kind, ch in find_bad_chars(v, allow):
                    bad_chars.append((tag, fld, kind, ch, v[:40]))
            for fld in LIST_FIELDS:
                for item in (q.get(fld) or []):
                    strings_scanned += 1
                    per_field[fld] += 1
                    for kind, ch in find_bad_chars(item):
                        bad_chars.append((tag, fld, kind, ch, item))

            expl = (q.get("explanation") or "").strip()
            point = (q.get("point") or "").strip()
            ans = (q.get("answer_text") or "").strip()
            if not expl:
                problems.append(f"[NO EXPL] {tag}")
            if not point:
                problems.append(f"[NO POINT] {tag}")
            if not ans:
                problems.append(f"[NO ANS] {tag}")

            # ---- I 解説 ----
            if expl:
                if expl.count("。") < 3:
                    problems.append(f"[EXPL SHORT] {tag}: {expl.count('。')} 文 (3文以上必要)")
                for circ in "①②③④":
                    if circ in expl:
                        problems.append(f"[EXPL CIRCLED] {tag}: 解説に {circ} がある"
                                        "(選択肢は make_units.py が並べ替えるので番号参照は必ずズレる)")
                        break
                # ★正解の語そのものを解説に書かせるのは mc だけ。整序・書き換えの答えは
                #   一文まるごとなので、解説に逐語で写させると読みにくくなるだけで質は上がらない。
                if t == "mc" and ans and ans not in expl:
                    problems.append(f"[EXPL NO ANS] {tag}: 解説が正解 {ans!r} に触れていない")

            # ---- C / E / K mc ----
            if t == "mc":
                ch = q.get("choices") or []
                ai = q.get("answer_index")
                stem = q.get("stem") or ""
                if len(ch) != 4:
                    problems.append(f"[MC CHOICES] {tag}: {len(ch)} 個")
                if len(set(ch)) != len(ch):
                    problems.append(f"[MC DUP] {tag}: 選択肢に重複 {ch}")
                if not isinstance(ai, int) or not (0 <= ai < len(ch)):
                    problems.append(f"[MC IDX] {tag}: answer_index={ai}")
                else:
                    positions.append(ai)
                    if ch[ai] != ans:
                        problems.append(f"[MC MATCH] {tag}: choices[{ai}]={ch[ai]!r} != {ans!r}")
                    others = [c for i, c in enumerate(ch) if i != ai]
                    if others:
                        longest_other = max(others, key=len)
                        # ★「正解が一番長い」は Were/Was のように1文字差でも起きるので、
                        #   1件ずつ落とすと雑音になる。見た目で分かる差(3文字超)だけ落とし、
                        #   全体の割合は下の [MC LONGEST RATE] で別に縛る。
                        if len(ans) - len(longest_other) > 3:
                            problems.append(f"[MC LONGEST] {tag}: 正解が目立って最長 "
                                            f"({ans!r} が {longest_other!r} より "
                                            f"{len(ans) - len(longest_other)} 文字長い)")
                        # ★「同点で最長」は数えない。2つ同じ長さなら生徒はどちらも選べず、
                        #   長さは手がかりにならない。手がかりになるのは**単独で最長**のときだけ。
                        if len(ans) > len(longest_other):
                            longest_tell[unit] += 1
                        mc_seen[unit] += 1
                    for d in others:
                        if expl and d not in expl:
                            problems.append(f"[EXPL NO NG] {tag}: 解説が誤答 {d!r} に触れていない")
                if "( )" not in stem:
                    problems.append(f"[MC BLANK] {tag}: stem に '( )' が無い")
                all_stems.append((tag, stem))
                all_answers.append((tag, f"{stem}|{ans}"))

            # ---- F / G 整序 ----
            elif t == "order":
                toks = q.get("tokens") or []
                if len(toks) < 4:
                    problems.append(f"[ORDER TOK#] {tag}: {len(toks)} 語 (4語以上にする)")
                want_words = norm_words(ans)
                got_words = norm_words(" ".join(toks))
                if want_words != got_words:
                    problems.append(f"[ORDER MATCH] {tag}: tokens の語 {got_words} != 答えの語 {want_words}")
                if " ".join(toks) == re.sub(r"[.?!]+$", "", ans):
                    problems.append(f"[ORDER LEAK] {tag}: tokens が答えと同じ並び(問題編に答えが出る)")
                if not ans or not ans[0].isupper():
                    problems.append(f"[ORDER CAP] {tag}: 答えが大文字で始まっていない: {ans!r}")
                if ans and ans[-1] not in ".?!":
                    problems.append(f"[ORDER END] {tag}: 答えが句読点で終わっていない: {ans!r}")
                # 語順の一意性: 文頭になれる大文字語が答えの1語目だけか
                heads = []
                for w in toks:
                    bare = w.strip(",.;:?!")
                    if not bare or not bare[0].isupper():
                        continue
                    if bare in ALWAYS_CAP:
                        continue
                    if bare in PROPER_NOUNS:
                        proper_noun_hits[bare] += 1
                        continue
                    heads.append(w)
                first = ans.split()[0] if ans else ""
                if len(heads) > 1:
                    problems.append(f"[ORDER HEAD] {tag}: 文頭候補が複数ある {heads}"
                                    "(別の語順でも文になりうる)")
                elif len(heads) == 1 and heads[0] != first:
                    problems.append(f"[ORDER HEAD] {tag}: 大文字語 {heads[0]!r} が答えの1語目 {first!r} と違う")
                elif not heads and first not in ALWAYS_CAP:
                    problems.append(f"[ORDER HEAD] {tag}: 大文字で始まる語が tokens に無い")
                # 語順が2通りになりうる語を含むなら、1問ずつ宣言を要求する
                risky = sorted({w for w in (t_.strip(",.;:?!").lower() for t_ in toks)
                                if w in MOBILE_ADVERBS or w in PARTICLES})
                if risky:
                    key = (unit, q.get("no"))
                    if key in ORDER_ADVERB_OK:
                        adverb_declared[key] = (risky, ORDER_ADVERB_OK[key])
                    else:
                        problems.append(
                            f"[ORDER AMBIG] {tag}: 位置が動きうる語 {risky} を含むのに宣言が無い。"
                            "別の語順でも正しい英文になると生徒を不当に×にする。"
                            "英語で確かめて ORDER_ADVERB_OK に理由を書くか、その語を使わない文にすること")
                all_stems.append((tag, q.get("prompt_ja") or ""))
                all_answers.append((tag, ans))

            # ---- H 書き換え ----
            elif t == "rewrite":
                orig = (q.get("original") or "").strip()
                instr = (q.get("instruction") or "").strip()
                if not orig:
                    problems.append(f"[RW ORIG] {tag}: original が空")
                if not instr:
                    problems.append(f"[RW INSTR] {tag}: instruction が空")
                if ans and ans in printed_text:
                    problems.append(f"[RW LEAK] {tag}: 答え {ans!r} が問題編の印字テキストに出ている")
                if orig and ans and orig == ans:
                    problems.append(f"[RW SAME] {tag}: 書き換え前後が同じ文")
                all_stems.append((tag, orig))
                all_answers.append((tag, ans))

            inspected += 1

        pos_by_unit[unit] = positions

    # ---- D 正解位置の偏り ----
    for unit, positions in pos_by_unit.items():
        if not positions:
            continue
        c = Counter(positions)
        n = len(positions)
        lo, hi = n // 4 - 1, n // 4 + 2      # 18問なら 3..6 を許容(狙いは 4-5)
        for i in range(4):
            if not (lo <= c.get(i, 0) <= hi):
                problems.append(f"[POS BIAS] {unit}: 正解位置 {i} が {c.get(i, 0)} 回 "
                                f"(許容 {lo}-{hi}／全 {n} 問)")
        run = 1
        for a, b in zip(positions, positions[1:]):
            run = run + 1 if a == b else 1
            if run >= 3:
                problems.append(f"[POS RUN] {unit}: 同じ正解位置が3連続している {positions}")
                break

    # ---- E' 最長肢テルの割合 ----
    # 1問ずつでは無害な差でも、「迷ったら一番長いのを選べ」で半分以上取れてしまうと
    # 文法を問う問題として成立しない。単元ごとに 60% を上限にする。
    for unit, n in mc_seen.items():
        rate = longest_tell[unit] / n if n else 0
        if rate > 0.60:
            problems.append(f"[MC LONGEST RATE] {unit}: 正解が単独で最長の問題が "
                            f"{longest_tell[unit]}/{n} = {rate:.0%} (上限 60%)")

    # ---- K 重複 ----
    for label, items in (("STEM", all_stems), ("ANS", all_answers)):
        seen = {}
        for tag, s in items:
            key = re.sub(r"\s+", " ", s.strip().lower())
            if not key:
                continue
            if key in seen:
                problems.append(f"[DUP {label}] {tag} と {seen[key]} が同じ内容: {s[:50]!r}")
            else:
                seen[key] = tag

    # ---- 検査量の等式 ----
    if files_read != len(EXPECT):
        ledger.append(f"読めた単元ファイル {files_read} != 期待 {len(EXPECT)}")
    if total != EXPECT_TOTAL:
        ledger.append(f"読めた問題 {total} != 期待 {EXPECT_TOTAL}")
    if inspected + halted != total:
        ledger.append(f"内訳が合わない: 検査済 {inspected} + 打ち切り {halted} != {total}")
    if halted:
        ledger.append(f"type 不明で検査を打ち切った問題が {halted} 問(この問題は検査できていない)")
    if sum(type_counts.values()) != inspected:
        ledger.append(f"type別合計 {sum(type_counts.values())} != 検査済 {inspected}")
    want_field = {
        "stem": type_counts["mc"], "choices": type_counts["mc"] * 4,
        "prompt_ja": type_counts["order"], "tokens": None,
        "original": type_counts["rewrite"], "instruction": type_counts["rewrite"],
        "answer_text": inspected, "point": inspected, "explanation": inspected,
    }
    for fld, want in want_field.items():
        got = per_field.get(fld, 0)
        if want is None:
            if got < type_counts["order"] * 4:
                ledger.append(f"走査が痩せている: {fld} {got} 本 < 下限 {type_counts['order'] * 4}")
        elif got != want:
            ledger.append(f"走査が痩せている: {fld} {got} 本 != 期待 {want} 本")
    known = set(ENG_FIELDS) | set(JA_FIELDS) | set(LIST_FIELDS) | META_KEYS
    unknown = sorted(seen_keys - known)
    if unknown:
        ledger.append(f"走査に入っていない文字列フィールドがある: {unknown}")

    # ---------------- 出力 ----------------
    print("=== 何を検査したか ===")
    print(f"対象: {UNITS_DIR}")
    for fname, unit in EXPECT:
        ft = per_file_types.get(fname, Counter())
        print(f"  {fname} ({unit}): "
              + " / ".join(f"{t} {ft.get(t, 0)}問" for t in ("mc", "order", "rewrite")))
    print(f"単元ファイル {files_read} / 期待 {len(EXPECT)}")
    print(f"読めた問題 {total} / 期待 {EXPECT_TOTAL}"
          f"（検査済 {inspected} + type不明で打ち切り {halted}）")
    print(f"type別 {dict(type_counts)} / 難易度別 {dict(level_counts)}")
    print(f"禁止文字スキャン {strings_scanned} 本（内訳 {dict(per_field)}）")
    print()

    print("=== 正解位置の配り方（単元ごと） ===")
    for unit, positions in pos_by_unit.items():
        c = Counter(positions)
        print(f"  {unit}: " + " ".join(f"{i}→{c.get(i, 0)}回" for i in range(4))
              + f"  並び {positions}")
    print()

    print("=== 最長肢テル（「単独で一番長いのを選べ」で当たる割合・上限60%） ===")
    for unit, n in mc_seen.items():
        print(f"  {unit}: {longest_tell[unit]}/{n} = {longest_tell[unit] / n:.0%}")
    print()

    print("=== 黙って見逃したものの開示 ===")
    for ch, why in ALLOW_IN_JA.items():
        print(f"  和文で許容 {ch!r} U+{ord(ch):04X}: {allowed_hits[ch]} 個 — {why}")
    print(f"  ※英語フィールド({'/'.join(ENG_FIELDS + LIST_FIELDS)})では上の文字も不合格にする。")
    if proper_noun_hits:
        for w, n in sorted(proper_noun_hits.items()):
            print(f"  整序の文頭候補から除外した固有名詞 {w!r}: {n} 回")
    else:
        print("  整序の文頭候補から除外した固有名詞: なし")
    print(f"  整序で位置が動きうる語を含むが「動かない」と宣言した問題: {len(adverb_declared)} 問")
    for (u, no), (words, why) in sorted(adverb_declared.items()):
        print(f"    {u}#{no} {words} — {why}")
    unused = sorted(set(ORDER_ADVERB_OK) - set(adverb_declared))
    if unused:
        # ★使われない宣言を放置すると、次の人が「宣言があるから安全」と誤解する
        ledger.append(f"ORDER_ADVERB_OK に、対象の問題が無い宣言が残っている: {unused}")
    print()

    print(f"=== 禁止文字 ({len(bad_chars)} 件) ===")
    for tag, fld, kind, ch, ctx in bad_chars[:60]:
        print(f"  {tag} [{fld}] {kind} {ch!r} U+{ord(ch):04X}: {ctx}")
    if len(bad_chars) > 60:
        print(f"  …他 {len(bad_chars) - 60} 件")
    print()
    print(f"=== 問題点 ({len(problems)} 件) ===")
    for p in problems:
        print("  " + p)
    print()
    print(f"=== 検査量の食い違い ({len(ledger)} 件) ===")
    for x in ledger:
        print("  " + x)

    ng = len(problems) + len(bad_chars) + len(ledger)
    if ng:
        print(f"\n  ✗ 不合格: 上の {ng} 件を直すこと")
        sys.exit(1)
    print(f"\n  OK: {total} 問すべて合格（検査量も期待どおり）")


if __name__ == "__main__":
    main()
