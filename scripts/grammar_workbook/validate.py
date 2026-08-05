#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全20分野のJSONを検証する。構造・件数・mc整合・order語句一致・禁止文字を点検。

★このゲートは以前 sys.exit を1つも持たず、違反を印字しながら exit 0 を返していた。
  run_all_gates.py は returncode で合否を決めるので、500問の教材がずっと PASS 扱いだった。
  [MC MATCH](choices[answer_index] != answer_text)は青学の教材で実際に紙を壊した型なので、
  1件でも見つかったら必ず落とす。
"""
import json, os, re, sys
from collections import Counter

UNITS_DIR = os.path.join(os.path.dirname(__file__), "units")

EXPECT_ORDER = [
    ("01_sentence-patterns.json", "文型"),
    ("02_tenses.json", "時制"),
    ("03_perfect.json", "完了形"),
    ("04_modals.json", "助動詞"),
    ("05_passive.json", "受動態"),
    ("06_infinitive.json", "不定詞"),
    ("07_gerund.json", "動名詞"),
    ("08_participle.json", "分詞"),
    ("09_participial-construction.json", "分詞構文"),
    ("10_comparison.json", "比較"),
    ("11_relatives.json", "関係詞"),
    ("12_subjunctive.json", "仮定法"),
    ("13_conjunctions.json", "接続詞"),
    ("14_prepositions.json", "前置詞"),
    ("15_nouns-articles.json", "名詞・冠詞"),
    ("16_pronouns.json", "代名詞"),
    ("17_adjectives-adverbs.json", "形容詞・副詞"),
    ("18_interrogatives.json", "疑問文"),
    ("19_negation-inversion.json", "否定・倒置・強調・省略"),
    ("20_reported-speech.json", "話法"),
]

# ---- 検査量の期待値(実データを数えて固定) ----
# ★「何件検査したか印字するだけ」だと、分野ファイルが1つ壊れて読めなくても
#   残り19ファイルが綺麗なら緑になる。数を等式で縛って、減ったら落とす。
EXPECT_FILES = 20
EXPECT_PER_FILE = 25
EXPECT_TOTAL = EXPECT_FILES * EXPECT_PER_FILE          # 500問
# 1問あたり最低このくらいの文字列を禁止文字スキャンに通しているはず(実測の最小値=5)。
# フィールド構成は type で変わるので厳密一致にはできないが、走査が痩せたら気づける。
MIN_STRINGS_PER_Q = 5

# ---- 文字列を持つフィールド。英語と和文で禁止文字の許容範囲が違う ----
# ★下の3群で question の文字列キーを全部覆っている(実データのキー棚卸しで確認:
#   stem/answer_text/original/instruction/prompt_ja/point/explanation/choices/tokens
#   以外の文字列キーは level と type だけ)。増やしたらここに足すこと。
ENG_FIELDS = ("stem", "answer_text", "original", "instruction")
JA_FIELDS = ("prompt_ja", "point", "explanation")
LIST_FIELDS = ("choices", "tokens")   # ★tokens は従来スキャン漏れだった(実データの違反は0件)

# 禁止文字: スマートクオート/各種ダッシュ/三点リーダ/不可視スペース
# ★U+200B/U+FEFF 等の不可視文字は「見えないのに紙で豆腐になる」。
#   U+FEFF は唯一の登録フォント Arial Unicode にグリフが無く、
#   build_pdf.py の clean() の制御文字除去(\x00-\x1f,\x7f)も素通りする。
#   ★ALLOW_IN_JA には入れない（和文でも落とす）。
SMART = "‘’“”–—… 　​‌‍⁠﻿ ­"

# ★和文フィールドでだけ許す文字と、その理由。「黙って除外」にしないため、
#   何をなぜ許したかと件数を毎回出力に出す(下の print)。
#   - '…'(U+2026) は和文として正しい三点リーダで、そもそも defect ではない。
#     実データ23件は全部 point / explanation にあり、build_pdf.py の _TRANS が
#     描画前に '...' へ正規化するので紙にも出ない(配布PDF 101頁で U+2026 は0件、
#     '...' が119個)。落とし続けると雑音になり、ゲート自体が読まれなくなる。
#   - '　'(U+3000) は従来から和文フィールドで許容していた(実データ0件・据え置き)。
#   ★英語フィールドと choices / tokens では上の2文字も違反のまま落とす。
#     英文中の三点リーダや全角スペースは組版事故で、しかも choices と answer_text の
#     文字列一致([MC MATCH])や tokens の語照合([ORDER MATCH])を静かに壊す。
#   ★ここに無い禁止文字(スマートクオート等)は和文でも従来どおり落ちる。
ALLOW_IN_JA = {
    "…": "三点リーダ。和文として正しい表記で、build_pdf.py の _TRANS が '...' に正規化して描画する",
    "　": "和文の全角スペース。従来からの許容を据え置き",
}


def find_bad_chars(s, allow=()):
    """禁止文字を (種別, 文字) で返す。allow に入れた文字だけ見逃す。
    ★以前は repr() の文字列比較で許容判定していて壊れやすかったので、文字そのもので判定する。"""
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
    # 句読点を空白化して語の多重集合を取る(整序の語句一致確認用)
    s = s.lower()
    s = re.sub(r"[.,?!;:\"]", " ", s)
    return sorted([w for w in s.split() if w])


def main():
    total = 0            # 読み込めた問題の総数
    inspected = 0        # 検査を最後まで通した問題数
    halted = 0           # type 不明で検査を打ち切った問題数(=検査していない)
    files_read = 0       # JSON として読めた分野ファイル数
    strings_scanned = 0  # 禁止文字スキャンに通した文字列の本数
    per_field = Counter()  # フィールド別の走査本数（総数の下限だけだと痩せを捕まえられない）
    seen_keys = set()      # データに実在する文字列フィールド名（走査漏れの検出用）
    type_counts = {"mc": 0, "order": 0, "rewrite": 0}
    per_file = []
    problems = []
    all_bad_chars = []
    allowed_hits = {ch: 0 for ch in ALLOW_IN_JA}       # 和文で見逃した文字の件数
    allowed_where = {ch: set() for ch in ALLOW_IN_JA}  # どのフィールドに出たか

    for fname, unit in EXPECT_ORDER:
        path = os.path.join(UNITS_DIR, fname)
        if not os.path.exists(path):
            problems.append(f"[MISSING] {fname}")
            continue
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                problems.append(f"[JSON ERROR] {fname}: {e}")
                continue
        files_read += 1
        if data.get("unit") != unit:
            problems.append(f"[UNIT NAME] {fname}: got {data.get('unit')!r} expected {unit!r}")
        qs = data.get("questions", [])
        per_file.append((fname, len(qs)))
        if len(qs) != EXPECT_PER_FILE:
            problems.append(f"[COUNT] {fname}: {len(qs)} questions (expected {EXPECT_PER_FILE})")
        nos = [q.get("no") for q in qs]
        if sorted(nos) != list(range(1, EXPECT_PER_FILE + 1)):
            problems.append(f"[NO SEQ] {fname}: {nos}")
        for q in qs:
            total += 1
            t = q.get("type")
            tag = f"{unit}#{q.get('no')}"
            if t not in type_counts:
                problems.append(f"[TYPE] {tag}: unknown type {t!r}")
                halted += 1          # ★ここで continue する＝この問題は検査していない。数に残す。
                continue
            type_counts[t] += 1
            if q.get("level") not in ("basic", "standard"):
                problems.append(f"[LEVEL] {tag}: {q.get('level')!r}")
            for k, v in q.items():
                if isinstance(v, str) or (isinstance(v, list)
                                          and all(isinstance(x, str) for x in v) and v):
                    seen_keys.add(k)
            # 禁止文字チェック(英語フィールドは全部禁止・和文フィールドは ALLOW_IN_JA だけ見逃す)
            for fld in ENG_FIELDS + JA_FIELDS:
                v = q.get(fld)
                if not isinstance(v, str):
                    continue
                strings_scanned += 1
                per_field[fld] += 1
                allow = ALLOW_IN_JA if fld in JA_FIELDS else ()
                for ch in v:
                    if fld in JA_FIELDS and ch in ALLOW_IN_JA:
                        allowed_hits[ch] += 1
                        allowed_where[ch].add(fld)
                for kind, ch in find_bad_chars(v, allow):
                    all_bad_chars.append((tag, fld, kind, ch, v[:40]))
            for fld in LIST_FIELDS:
                for item in (q.get(fld) or []):
                    strings_scanned += 1
                    per_field[fld] += 1
                    for kind, ch in find_bad_chars(item):
                        all_bad_chars.append((tag, fld, kind, ch, item))
            # 解説の有無
            if not (q.get("explanation") or "").strip():
                problems.append(f"[NO EXPL] {tag}")
            if not (q.get("point") or "").strip():
                problems.append(f"[NO POINT] {tag}")
            # type別
            if t == "mc":
                ch = q.get("choices") or []
                if len(ch) != 4:
                    problems.append(f"[MC CHOICES] {tag}: {len(ch)} choices")
                ai = q.get("answer_index")
                if not isinstance(ai, int) or not (0 <= ai < len(ch)):
                    problems.append(f"[MC IDX] {tag}: answer_index={ai}")
                elif ch[ai] != q.get("answer_text"):
                    problems.append(f"[MC MATCH] {tag}: choices[{ai}]={ch[ai]!r} != answer_text={q.get('answer_text')!r}")
                if len(set(ch)) != len(ch):
                    problems.append(f"[MC DUP] {tag}: duplicate choices {ch}")
                if "( )" not in (q.get("stem") or "") and "()" not in (q.get("stem") or ""):
                    problems.append(f"[MC BLANK] {tag}: no '( )' in stem: {q.get('stem')!r}")
            elif t == "order":
                toks = q.get("tokens") or []
                ans = q.get("answer_text") or ""
                if len(toks) < 3:
                    problems.append(f"[ORDER TOK#] {tag}: {len(toks)} tokens")
                # 語の多重集合一致
                from_tokens = norm_words(" ".join(toks))
                from_ans = norm_words(ans)
                if from_tokens != from_ans:
                    problems.append(f"[ORDER MATCH] {tag}: tokens words {from_tokens} != answer words {from_ans} | ans={ans!r} toks={toks}")
                if not ans or ans[0].islower():
                    problems.append(f"[ORDER CAP] {tag}: answer not capitalized: {ans!r}")
                if ans and ans[-1] not in ".?!":
                    problems.append(f"[ORDER END] {tag}: answer not terminated: {ans!r}")
            elif t == "rewrite":
                if not (q.get("original") or "").strip():
                    problems.append(f"[RW ORIG] {tag}")
                if not (q.get("instruction") or "").strip():
                    problems.append(f"[RW INSTR] {tag}")
                if not (q.get("answer_text") or "").strip():
                    problems.append(f"[RW ANS] {tag}")
            inspected += 1   # ★ここまで来た問題だけが「検査済み」。上の continue と合わせて等式にする。

    # ---- 検査量の等式。ここが合わないなら、緑でも「検査していない」だけ ----
    ledger = []
    if files_read != EXPECT_FILES:
        ledger.append(f"読めた分野ファイル {files_read} != 期待 {EXPECT_FILES}")
    if total != EXPECT_TOTAL:
        ledger.append(f"読めた問題 {total} != 期待 {EXPECT_TOTAL}")
    if inspected + halted != total:
        ledger.append(f"内訳が合わない: 検査済 {inspected} + 打ち切り {halted} != 読めた {total}")
    if halted:
        ledger.append(f"type が不明で検査を打ち切った問題が {halted} 問(この問題は検査できていない)")
    if sum(type_counts.values()) != inspected:
        ledger.append(f"type別の合計 {sum(type_counts.values())} != 検査済 {inspected}")
    # ★総本数の下限だけでは「1フィールドを外す」1行編集を**1つも**捕まえられない
    #   （実測: 9フィールドどれを単独で外しても下限 2500 を割らなかった。
    #     choices を外すと 3877→2629 で、[MC MATCH] を静かに壊す文字が最も効く欄が消える）。
    #   フィールドごとに「type別の問数から決まる本数」と突き合わせる。
    want_field = {
        "stem": type_counts["mc"], "choices": type_counts["mc"] * 4,
        "prompt_ja": type_counts["order"], "tokens": None,          # tokens は問ごとに語数が違う
        "original": type_counts["rewrite"], "instruction": type_counts["rewrite"],
        "answer_text": inspected, "point": inspected, "explanation": inspected,
    }
    for fld, want in want_field.items():
        got = per_field.get(fld, 0)
        if want is None:
            if got < type_counts["order"] * 3:
                ledger.append(f"走査が痩せている: {fld} {got} 本 < 下限 {type_counts['order'] * 3}")
        elif got != want:
            ledger.append(f"走査が痩せている: {fld} {got} 本 != 期待 {want} 本"
                          "（フィールドを外したか、データの形が変わった）")
    # ★逆向きの穴: データに文字列フィールドが増えても走査に入らず、等式は何も言わない。
    #   実データに出る str/list[str] のキーが、走査対象＋既知のメタキーと一致することを要求する。
    # ★実データに**実在する**文字列キーだけを書く。「これから足しうる名前」を
    #   先回りして書くと、その名前でフィールドを足したとき走査にも入らず検出もされない。
    META_KEYS = {"level", "type"}
    known = set(ENG_FIELDS) | set(JA_FIELDS) | set(LIST_FIELDS) | META_KEYS
    unknown = sorted(seen_keys - known)
    if unknown:
        ledger.append(f"走査対象に入っていない文字列フィールドがある: {unknown}"
                      "（ENG/JA/LIST_FIELDS に足すこと）")

    print("=== 集計 ===")
    print(f"分野ファイル: {files_read} / 期待 {EXPECT_FILES}")
    print(f"読めた問題: {total} / 期待 {EXPECT_TOTAL}")
    print(f"  内訳: 検査済 {inspected} + type不明で打ち切り {halted} = {inspected + halted}")
    print(f"type別: {type_counts} (合計 {sum(type_counts.values())})")
    print(f"禁止文字スキャンに通した文字列: {strings_scanned} 本"
          f"（フィールド別の等式で検算。内訳 {dict(per_field)}）")
    # 分野ごとの問題数も出す。★合計だけ出すと1ファイルの欠けが他の過剰と相殺されうる。
    short = [f"{n}:{c}" for n, c in per_file if c != EXPECT_PER_FILE]
    print(f"分野ごとの問題数: 全 {EXPECT_PER_FILE} 問"
          + ("" if not short else f" …ただし {', '.join(short)}"))
    print()

    # ---- 和文フィールドで見逃した文字を必ず開示する(黙って除外しない) ----
    print("=== 和文フィールドで許容した文字(不合格には数えない) ===")
    for ch, why in ALLOW_IN_JA.items():
        where = ", ".join(sorted(allowed_where[ch])) or "出現なし"
        print(f"  {ch!r} U+{ord(ch):04X}: {allowed_hits[ch]} 個 [{where}] — {why}")
    print(f"  ※英語フィールド({'/'.join(ENG_FIELDS + LIST_FIELDS)})では上の文字も不合格にする。")
    print()

    print(f"=== 禁止文字 (件数 {len(all_bad_chars)}) ===")
    for tag, fld, kind, ch, ctx in all_bad_chars[:60]:
        print(f"  {tag} [{fld}] {kind} {ch!r} U+{ord(ch):04X}: {ctx}")
    if len(all_bad_chars) > 60:
        # ★黙って打ち切らない。残りが何件あるかは必ず出す。
        print(f"  …他 {len(all_bad_chars) - 60} 件(表示を60件で打ち切った)")
    print()
    print(f"=== 問題点 (件数 {len(problems)}) ===")
    for p in problems:
        print("  " + p)
    print()
    print(f"=== 検査量の食い違い (件数 {len(ledger)}) ===")
    for x in ledger:
        print("  " + x)

    ng = len(problems) + len(all_bad_chars) + len(ledger)
    if ng:
        # ★ここが無かったせいで、違反を印字しながら exit 0 を返していた。
        print(f"\n  ✗ 不合格: 上の {ng} 件を直すこと")
        sys.exit(1)
    print("\n  OK: 問題なし(検査量も期待どおり)")


if __name__ == "__main__":
    main()
