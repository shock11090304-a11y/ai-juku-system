# -*- coding: utf-8 -*-
"""機械ゲート: 原稿（content.py）と、刷られる紙の両方を全数検査する。1 件でも落ちたら刷らない。

    python3 check.py

★DSL の契約そのものは lint.py に 1 本だけ置き、ここから import する（二重に書かない）。
★このゲートは **引数を取らない**。既定で「刷るもの全部」を検査する
  （引数で対象が変わるゲートを引数なしで回して見本だけ検査した事故の再発防止）。
"""
import re
import sys
import unicodedata

from layout import (
    CIRCLE, PATTERN_SYN, SYN_VOCAB, normalize, parse, plain_text, top_segments,
)
from lint import markup_errors, validate_item
from content import (
    META, NOTATION, PART1, PART2, PART3, RULES, RULE_EXAMPLES, STEPS, SYN_POOL,
)

ERR = []
WARN = []
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
# 設問文・選択肢が「本文から引用したつもり」で書いた英語を拾う。
#   ① 明示的な引用（<span class="en">…</span> / 「…」 / "…"）
#   ② 素で 4 語以上つながった英語
# ★A・B・do のような**書き方の型を表す記号**を含むものは引用ではない（not so much A as B）。
#   これを引用として本文に照合すると、正しい選択肢を落とす。
EN_SPAN = re.compile(r'<span class="en">(.*?)</span>|「([^」]*)」|"([^"]*)"')
EN_RUN = re.compile(r"[A-Za-z][A-Za-z'’-]*(?:\s+[A-Za-z][A-Za-z'’-]*){3,}")
ABSTRACT_TOK = {"a", "b", "x", "y", "do", "doing", "done", "sth", "sb", "one", "ones",
                "oneself", "somebody", "something", "v", "s", "o", "c", "m"}


def is_gloss(q):
    """「workers に unable … を与える」のような**説明のための鉤括弧**か。

    ★鉤括弧の中身をすべて「本文からの引用」とみなすと、日本語の言い換えを混ぜた解説を
      片端から落とす（実際に落ちた）。日本語が 1 文字でも混ざっていれば引用ではない。
    """
    return any(ord(ch) > 0x2000 for ch in q)


def is_abstract(run):
    """「書き方の型」か（本文に literal では存在しない書き方か）。"""
    toks = re.findall(r"[A-Za-z'’-]+", run)
    if not toks:
        return True
    if any(len(t) == 1 for t in toks):
        return True
    return all(t.lower() in ABSTRACT_TOK for t in toks)
ANS_CLAIM = re.compile(r"正解は?\s*[①②③④]")
SAFE_SO = "★▲●◆■□◇→←↑↓〜①②③④⑤⑥⑦⑧⑨⑩"
MARU = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]")

# 第1部で必ず 1 問以上出す文型（易→難の並びの土台）
NEED_PATTERNS = ["第1文型", "第2文型", "第3文型", "第4文型", "第5文型"]


def err(where, msg):
    ERR.append(f"[NG] {where}: {msg}")


def scan_glyphs(obj, path, where):
    if isinstance(obj, str):
        for ch in obj:
            if ord(ch) < 0x20 and ch != "\n":
                err(where, f"{path} に制御文字 U+{ord(ch):04X}")
            elif unicodedata.category(ch) == "So" and ch not in SAFE_SO:
                err(where, f"{path} に記号/絵文字 {ch!r}（Arial Unicode に無い恐れ）")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not str(k).startswith("_"):
                scan_glyphs(v, f"{path}.{k}", where)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            scan_glyphs(v, f"{path}[{i}]", where)


def check_item(it, mode, where, need_points=False):
    """DSL の契約（lint.py）＋ この教材ぶんの上乗せ。"""
    probe = dict(it)
    probe["mode"] = mode
    probe["_require_notes"] = True
    probe["_require_ja"] = True
    errs, info = validate_item(probe)
    for e in errs:
        err(where, e)
    if len(it.get("notes", [])) < 3:
        err(where, f"notes が {len(it.get('notes', []))} 項目（3 項目以上にする）")
    for i, n in enumerate(it.get("notes", [])):
        if len(re.sub(r"<[^>]+>", "", n)) < 25:
            err(where, f"notes[{i}] が短すぎる（25 字以上）: {n!r}")
    if need_points:
        pts = it.get("points") or []
        if len(pts) < 3:
            err(where, f"採点ポイントが {len(pts)} 項目（3 項目以上にする）")
        for i, p in enumerate(pts):
            if len(p) < 10:
                err(where, f"points[{i}] が短すぎる: {p!r}")
    if not it.get("tag"):
        err(where, "tag（構文名）が空")
    if not it.get("syn"):
        err(where, "syn（構文カテゴリ）が空。layout.py の SYN_VOCAB から選ぶ")
    # ★丸数字を刷るのは第1部の判別問題だけ（drill_sentence / slot_table）。
    #   第2部・第3部の解答カードは分解図を出すだけで番号を振らないので、
    #   解説が「②did と④notice が」と書いても生徒には何のことか分からない。
    if mode != "drill":
        for field in ("notes", "points"):
            for i, t in enumerate(it.get(field) or []):
                if MARU.search(t):
                    err(where, f"{field}[{i}] が丸数字で位置を指している"
                               "（丸数字が刷られるのは第1部だけ。語そのもので指すこと）")
    return info


def main():
    ids, ens = {}, {}
    tag_use, syn_use, subj_use = {}, {}, {}
    syn_by_pool = {}
    all_items = []   # (表示名, item, 割り当て表のキー)

    # ---------------- 巻頭（記号ルールの見本も同じゲートを通す） ----------------
    for i, ex in enumerate(RULE_EXAMPLES, 1):
        w = f"巻頭見本{i}"
        errs, _ = validate_item({"mode": "kaishaku", "dsl": ex["dsl"],
                                 "en": plain_text(parse(ex["dsl"])), "pat": ex["pat"]})
        for e in errs:
            err(w, e)
        for m in markup_errors(ex["note"]):
            err(w, m)
    if len(RULES) < 4:
        err("巻頭", f"記号ルールが {len(RULES)} 件（4 件以上）")
    if len(STEPS) < 4:
        err("巻頭", f"読む手順が {len(STEPS)} 件（4 件以上）")
    # ★表記規約（生徒が答案に書く形の唯一の正典）が痩せていないか。
    #   lint.py の規約と 1 対 1 で対応させているので、片方だけ消えると採点基準が消える。
    if len(NOTATION) < 8:
        err("巻頭", f"記号の書き方が {len(NOTATION)} 行（8 行以上・lint.py の規約と対応させる）")
    for i, row in enumerate(NOTATION):
        if len(row) != 3:
            err("巻頭", f"NOTATION[{i}] は (見出し, 説明, 例) の 3 つで書く")
            continue
        for m in markup_errors(row[1]) + markup_errors(row[2]):
            err("巻頭", f"NOTATION[{i}]: {m}")
        if len(re.sub(r"<[^>]+>", "", row[1])) < 20:
            err("巻頭", f"NOTATION[{i}] の説明が短すぎる: {row[1]!r}")

    # ---------------- 第1部 ----------------
    n1 = 0
    pat_seen = set()
    for gi, grp in enumerate(PART1, 1):
        if grp.get("pool") not in SYN_POOL:
            err(f"第1部 グループ{gi}", f'pool キーが不正: {grp.get("pool")!r}')
        if not grp.get("items"):
            err(f"第1部 グループ{gi}", "問題が 0 問")
        for it in grp["items"]:
            n1 += 1
            w = f'第1部 {n1} ({it["id"]})'
            info = check_item(it, "drill", w)
            all_items.append((w, it, grp["pool"]))
            for p in NEED_PATTERNS:
                if p in it["pat"]:
                    pat_seen.add(p)
            segs = info.get("segs") or []
            if segs:
                # ★問題用紙に刷られる ①②③ は DSL から機械的に切り出す。番号が丸数字の
                #   持ち数を超えると無言で IndexError になるので、ここで止める。
                if len(segs) > len(CIRCLED):
                    err(w, f"切り出しが {len(segs)} 個で丸数字が足りない")
                labels = [lb for lb, _t, _u in segs]
                if labels.count("V") + labels.count("助") != 1:
                    err(w, f"主節の V が {labels.count('V')} 個（第1部は 1 個に限る）")
    missing = [p for p in NEED_PATTERNS if p not in pat_seen]
    if missing:
        err("第1部", f"出題されていない文型がある: {missing}")

    # ---------------- 第2部 ----------------
    hist = [0, 0, 0, 0]
    for qi, q in enumerate(PART2, 1):
        w = f'第2部 {qi} ({q["id"]})'
        check_item(q, "kaishaku", w)
        all_items.append((w, q, "2"))
        if len(q["choices"]) != 4:
            err(w, f"選択肢が {len(q['choices'])} 個")
        if len(set(q["choices"])) != len(q["choices"]):
            err(w, "選択肢が重複している")
        if not (0 <= q["ans"] < len(q["choices"])):
            err(w, "ans が範囲外")
        else:
            hist[q["ans"]] += 1
        for m in markup_errors(q["q"]) + markup_errors(q["exp"]):
            err(w, m)
        for c in q["choices"]:
            for m in markup_errors(c):
                err(w, m)
        if len(re.sub(r"<[^>]+>", "", q["exp"])) < 100:
            err(w, "解説が 100 字未満（誤答 3 つの否定理由まで書く）")
        # 解説が自称する正解と ans のずれ
        for m in ANS_CLAIM.findall(q["exp"]):
            if m[-1] != CIRCLE[q["ans"]]:
                err(w, f"解説が「{m}」と書いているが ans は {CIRCLE[q['ans']]}")
        # 設問文・選択肢が引用した英語が、その文に実在するか（番号ずれ・引用の作文を弾く）
        low = normalize(q["en"]).lower()
        for field, txt in [("設問文", q["q"]), ("解説", q["exp"])] \
                + [("選択肢", c) for c in q["choices"]]:
            quoted = [g for m in EN_SPAN.findall(txt) for g in m
                      if g and re.search(r"[A-Za-z]", g) and not is_gloss(g)]
            plain = re.sub(r"<[^>]+>", " ", txt)
            for run in quoted + EN_RUN.findall(plain):
                if is_abstract(run):
                    continue
                if normalize(run).lower() not in low:
                    err(w, f"{field}が引用した英語がその文に無い: {run!r}")
        # 正解肢だけが極端に長い（長さテル）
        L = [len(re.sub(r"<[^>]+>", "", c)) for c in q["choices"]]
        if L[q["ans"]] == max(L) and L[q["ans"]] >= min(L) * 2.0:
            err(w, f"正解肢が最長かつ他の 2 倍以上（長さテル）: {L}")
    if PART2 and max(hist) - min(hist) > 1:
        err("第2部", f"4 択の正解位置が偏っている: {hist}")

    # ---------------- 第3部 ----------------
    n3 = 0
    for gi, grp in enumerate(PART3, 1):
        if grp.get("pool") not in SYN_POOL:
            err(f"第3部 グループ{gi}", f'pool キーが不正: {grp.get("pool")!r}')
        if not grp.get("items"):
            err(f"第3部 グループ{gi}", "問題が 0 文")
        for it in grp["items"]:
            n3 += 1
            w = f'第3部 {n3} ({it["id"]})'
            check_item(it, "kaishaku", w, need_points=True)
            all_items.append((w, it, grp["pool"]))
            wc = len(re.findall(r"[A-Za-z][A-Za-z'’-]*", it["en"]))
            if not (14 <= wc <= 36):
                err(w, f"語数 {wc} が想定レンジ 14-36 の外（関関同立の 1 文の長さ）")

    # ---------------- 全体（重複・グリフ） ----------------
    for w, it, pool in all_items:
        if it["id"] in ids:
            err(w, f'id {it["id"]!r} が {ids[it["id"]]} と重複')
        ids[it["id"]] = w
        key = normalize(it["en"]).lower()
        if key in ens:
            err(w, f'英文が {ens[key]} と重複: {it["en"]!r}')
        ens[key] = w
        tag_use.setdefault(it["tag"], []).append(w)
        if it.get("syn"):
            if it["syn"] not in SYN_VOCAB:
                err(w, f'syn {it["syn"]!r} が語彙に無い（layout.py の SYN_VOCAB）')
            elif it["syn"] not in SYN_POOL[pool]:
                err(w, f'syn {it["syn"]!r} は割り当て表 {pool} のプールに無い'
                       f'（このグループで使えるのは {SYN_POOL[pool]}）')
            syn_use.setdefault(it["syn"], []).append(w)
            syn_by_pool.setdefault(pool, set()).add(it["syn"])
        for lb, txt, _u in top_segments(parse(it["dsl"])):
            if lb in ("S", "真S"):
                subj_use.setdefault(txt.lower().rstrip(" .,"), []).append(w)
                break
        scan_glyphs(it, "item", w)
    for tag, uses in sorted(tag_use.items()):
        if len(uses) > 2:
            err("全体", f"同じ構文タグ {tag!r} を {len(uses)} 回使っている: {uses}")
    # ★重複は tag（自由文）ではなく**決まった語彙**（syn）で数える。
    #   tag は書き換えるだけでゲートをすり抜けられるが、syn は語彙が閉じている。
    for syn, uses in sorted(syn_use.items()):
        cap = 3 if syn in PATTERN_SYN else 1
        if len(uses) > cap:
            err("全体", f"同じ構文 {syn!r}（{SYN_VOCAB.get(syn, '?')}）を "
                        f"{len(uses)} 回出している（上限 {cap} 回）: {uses}")
    # 割り当て表の消化率。★「入れたつもりで入っていない構文」を機械で見つける。
    # ★プールごとに見る。全体で使われているかだけを見ると、別のグループで使われている構文を
    #   自分のプールに書き足しても素通りする（変異試験で実測した）。
    for pool_key, pool in sorted(SYN_POOL.items()):
        used = syn_by_pool.get(pool_key, set())
        missing = [x for x in pool if x not in used]
        if missing:
            err("全体", f"割り当て表 {pool_key} の構文がこのグループで出題されていない: "
                        f"{[f'{m}（{SYN_VOCAB.get(m, m)}）' for m in missing]}")
    # ★同じ名詞句を主語にした問題が並ぶと、別の構文でも「同じ問題」に見える。
    for subj, uses in sorted(subj_use.items()):
        if len(uses) > 1 and len(subj) >= 8:
            err("全体", f"同じ主語 {subj!r} の問題が {len(uses)} 問ある: {uses}")
    scan_glyphs(RULES, "RULES", "巻頭")
    scan_glyphs(STEPS, "STEPS", "巻頭")
    scan_glyphs(RULE_EXAMPLES, "RULE_EXAMPLES", "巻頭")
    scan_glyphs(NOTATION, "NOTATION", "巻頭")

    # ★巻頭の記号ルール・表記規約・見本に出す例文が、本編の問題の英文と重なっていないか。
    #   重なると「その問題の記号の付け方」を問題編の冒頭で先に見せることになる。
    #   （実測: 表記規約の例 "a growing number ＜M: of manufacturers＞" が第1部Ｂの答えそのものだった）
    head_ex = [r[2] for r in NOTATION] + [r["ex"] for r in RULES]
    head_ex += [plain_text(parse(e["dsl"])) for e in RULE_EXAMPLES]
    for ex in head_ex:
        for run in re.findall(r"[A-Za-z][A-Za-z'’ ]{11,}", re.sub(r"<[^>]+>", " ", ex)):
            run = run.strip()
            for w, it, _p in all_items:
                if run.lower() in it["en"].lower():
                    err("巻頭", f"例文の {run!r} が {w} の英文と重なっている（答えの先出し）")

    # ---------------- 刷られる紙に答えが出ていないか ----------------
    META["_n1"], META["_n2"], META["_n3"] = n1, len(PART2), n3
    try:
        import build
        page = build.build_mondai()
    except Exception as e:                      # noqa: BLE001
        err("問題編", f"組版に失敗した: {type(e).__name__}: {e}")
        page = ""
    if page:
        # 解答編にしか出さない部品が問題編に混ざっていないか（構造で見る）
        for cls, what in [('class="atag"', "構文名タグ"), ('class="jatr"', "和訳"),
                          ('class="skel"', "骨組み"), ('<td class="a">', "解答欄の答え")]:
            if cls in page:
                err("問題編", f"{what}（{cls}）が問題編に出ている＝答えの先出し")
        for w, it, _pool in all_items:
            leaks = [("和訳", it.get("ja"))]
            leaks += [(f"notes[{i}]", n) for i, n in enumerate(it.get("notes", []))]
            leaks += [(f"points[{i}]", p) for i, p in enumerate(it.get("points") or [])]
            if it.get("exp"):
                leaks.append(("解説", it["exp"]))
            for what, txt in leaks:
                if not txt:
                    continue
                body = re.sub(r"<[^>]+>", "", txt)
                if len(body) >= 12 and body in page:
                    err("問題編", f"{w} の{what}が問題編に印字されている")
        # 第3部の英文が、書き込み用にそのまま刷られているか（刷り漏れの検出）
        for grp in PART3:
            for it in grp["items"]:
                if it["en"] not in re.sub(r"<[^>]+>", "", page):
                    err("問題編", f'第3部 {it["id"]} の英文が問題編に出ていない')

    # ---------------- 集計 ----------------
    print("=" * 66)
    print(f"第1部 SVOCM 判別 {n1} 問 / 第2部 構造4択 {len(PART2)} 問 / 第3部 英文解釈 {n3} 文"
          f" = 合計 {n1 + len(PART2) + n3} 問")
    for grp in PART1:
        print(f"  [第1部] {grp['g']:<26} {len(grp['items']):>2} 問")
    for grp in PART3:
        print(f"  [第3部] {grp['g']:<26} {len(grp['items']):>2} 文")
    print(f"第2部 4択の正解位置分布 (1234): {hist}")
    print(f"出題した文型: {sorted(pat_seen)}")
    print("=" * 66)
    for w in WARN:
        print(w)
    if ERR:
        print(f"\n*** 検査に通らなかった項目 {len(ERR)} 件 ***")
        for e in ERR:
            print(e)
        sys.exit(1)
    print("NG 0 件 / ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
