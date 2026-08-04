# -*- coding: utf-8 -*-
"""
機械ゲート: content モジュール（META, GRAMMAR, READING）の構造・整合を検査。

  python3 check.py chu     # content_chu を検査
  python3 check.py kou     # content_kou を検査
  python3 check.py sample  # sample_content を検査

FAIL（exit 1）が1件でもあればビルド不可。WARN は出力のみ。
"""
import os, sys, re, importlib
from collections import Counter

# 字形の照合に使う cmap（`_print_font_cmap.txt`）。
# ★用途を取り違えないこと。このファイルは **build_common.py の FONT_PATH（Arial Unicode）**
#   の cmap で、それが使われるのは **ノンブル/柱の刻印だけ**（fitz の insert_text）。
#   本文の字を出しているのは CSS の "Hiragino Mincho ProN" / "Hiragino Kaku Gothic ProN" /
#   Georgia で、Chrome がフォールバックする。実測: ㉑ U+3251 と ㊿ U+32BF は Arial Unicode に
#   **無い**がヒラギノには**ある**ので、紙には正常に出る。
#   → cmap に無い＝即 NG ではない。**警告**にとどめる（err にすると正しい原稿を落とす）。
#   絵文字だけは Apple Color Emoji にしか無く PDF で確実に壊れるので、こちらは必ず落とす。
#   ★ファイルを固定するのは、CI に macOS のフォントが無いから。その場にあるフォント
#   （ubuntu の Noto 等）で照合すると環境ごとに判定が変わり、再現しない検査になる。
#   再生成は gen_font_cmap.py（macOS）。
CMAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_print_font_cmap.txt")
_COV = None
_COV_SRC = None


def _covered():
    """刷るフォントが字形を持つコードポイントの集合。**無ければ検査失敗**（黙って弱くしない）。"""
    global _COV, _COV_SRC
    if _COV_SRC is not None:
        return _COV
    _COV_SRC = CMAP_FILE
    if not os.path.exists(CMAP_FILE):
        msg = (f"{os.path.basename(CMAP_FILE)} が無い＝字形の照合ができていない"
               "（python3 gen_font_cmap.py で作る）")
        print(f"[FAIL] {msg}")
        ERRORS.append(msg)
        return None
    cov, declared_font, declared_count = set(), None, None
    with open(CMAP_FILE, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.lstrip().startswith("#"):
                if line.strip().startswith("# font:"):
                    declared_font = line.split(":", 1)[1].strip()
                elif line.strip().startswith("# count:"):
                    declared_count = line.split(":", 1)[1].strip()
                continue
            line = line.split("#")[0].strip()
            if not line:
                continue
            try:
                if "-" in line:
                    a, b = line.split("-", 1)
                    cov.update(range(int(a, 16), int(b, 16) + 1))
                else:
                    cov.add(int(line, 16))
            except ValueError:
                # ★素の Traceback で落とすと CRASH 扱いになり、他の失敗と扱いが揃わない。
                msg = f"{os.path.basename(CMAP_FILE)} の {n} 行目が壊れている（gen_font_cmap.py で作り直す）"
                print(f"[FAIL] {msg}")
                ERRORS.append(msg)
                return None
    # ★cmap は「元のフォントを変えたのに作り直し忘れる」と黙って古くなる。
    #   ヘッダに書いた元フォントが build_common.py の FONT_PATH と一致するかを見る
    #   （フォント実体は要らないので CI でも効く）。
    try:
        import build_common
        if declared_font and declared_font != build_common.FONT_PATH:
            msg = (f"cmap の元フォントが build_common.FONT_PATH と違う\n"
                   f"        cmap: {declared_font}\n        実際: {build_common.FONT_PATH}\n"
                   f"        → python3 gen_font_cmap.py で作り直すこと")
            print(f"[FAIL] {msg}")
            ERRORS.append(msg)
            return None
    except Exception:
        pass          # build_common を読めない環境では突合を飛ばす（cmap 自体は使う）
    if declared_count and declared_count.isdigit() and int(declared_count) != len(cov):
        msg = (f"cmap の字数が宣言({declared_count})と実数({len(cov)})で食い違う"
               "（途中で切れている）")
        print(f"[FAIL] {msg}")
        ERRORS.append(msg)
        return None
    if len(cov) < 10000:
        # 壊れたファイルを掴んで「全部未収録」になるのを防ぐ（DejaVu を掴んだときの再発防止）
        msg = f"{os.path.basename(CMAP_FILE)} の字数が {len(cov)} しかない（壊れている）"
        print(f"[FAIL] {msg}")
        ERRORS.append(msg)
        return None
    _COV = cov
    print(f"[info] 字形の照合: 刷るフォントの cmap {len(cov)} 字（{os.path.basename(CMAP_FILE)}）")
    return _COV


_EMOJI_FALLBACK = re.compile("[\U0001F000-\U0001FAFF\U0001F1E6-\U0001F1FF️]")

ERRORS = []
WARNS = []


# 今どの本を検査しているか。★中/高で講の採番が同じ（第1講〜第5講）なので、本の名前を
#   出さないと「chu が落ちた」と「kou が落ちた」の出力がバイト単位で同一になり、
#   追う側は 50% の確率で違うファイルを開くことになる（実測）。
CUR_MOD = ""


def err(ctx, msg):
    ERRORS.append(f"[FAIL] {CUR_MOD} {ctx}: {msg}")


def warn(ctx, msg):
    WARNS.append(f"[warn] {CUR_MOD} {ctx}: {msg}")


def scan_text(ctx, *strings):
    cov = _covered()
    for s in strings:
        if s is None:
            continue
        s = str(s)
        if "�" in s:
            err(ctx, f"置換文字 U+FFFD in {s[:40]!r}")
        if cov is not None:
            seen = set()
            for ch in s:
                o = ord(ch)
                if ch in "\n\r\t\f " or o in seen:
                    continue
                seen.add(o)
                if o < 0x20:
                    err(ctx, f"制御文字 U+{o:04X} in {s[:40]!r}")
                elif o not in cov:
                    # ★これは **警告** にとどめる。cmap は「ノンブル刻印に使う Arial Unicode」の
                    #   ものであって、本文の字を出しているのは CSS の Hiragino 明朝/角ゴ・Georgia。
                    #   Chrome がフォールバックするので、AU に無くても紙に出る字がある
                    #   （㉑ U+3251 / ㊿ U+32BF は AU に無いがヒラギノにあり、実際に正常に刷れる）。
                    #   err にすると **正しく刷れる原稿を落とす誤検出**になる。
                    warn(ctx, f"Arial Unicode 未収録 {ch!r} (U+{o:04X}) in {s[:40]!r}"
                              "（ノンブルには出せない。本文はヒラギノで出る可能性あり・要目視）")
            # 絵文字は Apple Color Emoji にしか無く、PDF では確実に壊れるので **必ず落とす**。
            m = _EMOJI_FALLBACK.search(s)
            if m:
                err(ctx, f"絵文字 {m.group()!r} in {s[:40]!r}")


def norm_tokens(s):
    return sorted(re.sub(r"[.,!?;:]", " ", s).split())


def check_grammar_q(ctx, q, mc_pos):
    t = q.get("type")
    scan_text(ctx, q.get("stem"), q.get("ja"), q.get("exp"), q.get("point"), q.get("note"),
              q.get("given"), q.get("target"), q.get("html"), q.get("correct"))
    if t == "mc":
        ch = q.get("choices", [])
        if len(ch) < 3:
            err(ctx, f"mc choices が {len(ch)} 個（3以上必要）")
        if not isinstance(q.get("ans"), int) or not (0 <= q["ans"] < len(ch)):
            err(ctx, f"mc ans={q.get('ans')} が範囲外 (choices={len(ch)})")
        else:
            mc_pos.append(q["ans"])
        if not q.get("stem"):
            err(ctx, "mc stem 空")
        if not q.get("exp"):
            warn(ctx, "mc 解説空")
    elif t == "fill":
        if "______" not in (q.get("stem") or ""):
            err(ctx, "fill stem に空所 ______ が無い")
        if not str(q.get("ans", "")).strip():
            err(ctx, "fill ans 空")
    elif t == "order":
        toks = q.get("tokens", [])
        ans = q.get("ans", "")
        if len(toks) < 3:
            err(ctx, f"order tokens が {len(toks)} 個")
        if not ans:
            err(ctx, "order ans 空")
        elif norm_tokens(" ".join(toks)) != norm_tokens(ans):
            err(ctx, f"order 語群≠完成文\n     chips={norm_tokens(' '.join(toks))}\n     ans  ={norm_tokens(ans)}")
    elif t == "error":
        marks = re.findall(r"\[([a-e])\|", q.get("html", ""))
        if len(marks) < 3:
            err(ctx, f"error 下線が {len(marks)} 個（3以上必要）")
        if q.get("ans") not in marks:
            err(ctx, f"error ans={q.get('ans')!r} が下線記号 {marks} に無い")
        if not q.get("correct"):
            err(ctx, "error correct 空")
    elif t == "rewrite":
        nb = (q.get("target", "")).count("______")
        blanks = q.get("blanks", [])
        if nb == 0:
            err(ctx, "rewrite target に空所無し")
        if nb != len(blanks):
            err(ctx, f"rewrite 空所数 {nb} ≠ blanks {len(blanks)}")
        if not q.get("given"):
            err(ctx, "rewrite given 空")
    elif t == "ja2en":
        if not q.get("ja"):
            err(ctx, "ja2en ja 空")
        if not q.get("models"):
            err(ctx, "ja2en models 空")
    else:
        err(ctx, f"未知の grammar type {t!r}")


def check_reading_q(ctx, q):
    t = q.get("type")
    scan_text(ctx, q.get("q"), q.get("exp"), q.get("ans"))
    if t == "rc_mc":
        ch = q.get("choices", [])
        if len(ch) < 3:
            err(ctx, f"rc_mc choices {len(ch)} 個")
        if not isinstance(q.get("ans"), int) or not (0 <= q["ans"] < len(ch)):
            err(ctx, f"rc_mc ans={q.get('ans')} 範囲外")
        for c in ch:
            scan_text(ctx, c)
    elif t == "rc_desc":
        if not str(q.get("ans", "")).strip():
            err(ctx, "rc_desc ans 空")
    else:
        err(ctx, f"未知の reading type {t!r}")


def check_module(modname):
    global CUR_MOD
    CUR_MOD = modname
    print(f"--- {modname} ---")
    try:
        m = importlib.import_module(modname)
    except ModuleNotFoundError:
        # ★素の Traceback で落ちるより、何をどう直せばいいかを出す（verify.py と同じ形）。
        err("MODULE", f"{modname} が見つからない（改名したなら check.py の MODS を直すこと）")
        return False
    META, GRAMMAR, READING = m.META, m.GRAMMAR, m.READING
    for k in ("series", "level", "minutes", "grammar_dates", "reading_dates", "intro"):
        if k not in META:
            err("META", f"キー {k} 欠落")

    if len(GRAMMAR) != 5:
        warn("GRAMMAR", f"講が {len(GRAMMAR)} 個（想定5）")
    mc_pos = []
    for s in GRAMMAR:
        gctx = f'文法 第{s.get("no","?")}講'
        for k in ("no", "title", "goal", "points"):
            if k not in s:
                err(gctx, f"キー {k} 欠落")
        if not s.get("points"):
            err(gctx, "points 空")
        for p in s.get("points", []):
            scan_text(gctx + " point", p.get("h"), p.get("body"), p.get("rule"))
        ntier = sum(1 for k in ("kiso", "hyojun", "nyushi") if s.get(k))
        if not s.get("kiso"):
            err(gctx, "基礎問(kiso) が無い（★基礎問は必須）")
        if ntier < 2:
            warn(gctx, "演習ティアが1つのみ")
        nq = 0
        for tier in ("kiso", "hyojun", "nyushi"):
            for i, q in enumerate(s.get(tier, []), start=1):
                check_grammar_q(f'{gctx} {tier}{i}', q, mc_pos)
                nq += 1
        if nq < 8:
            warn(gctx, f"問題数 {nq}（少なめ）")

    if len(READING) != 5:
        warn("READING", f"講が {len(READING)} 個（想定5）")
    for s in READING:
        rctx = f'長文 第{s.get("no","?")}講'
        for k in ("no", "title", "goal", "points", "passage", "questions"):
            if k not in s:
                err(rctx, f"キー {k} 欠落")
        pas = s.get("passage", {})
        paras = pas.get("paras", [])
        nsent = sum(len(p) for p in paras)
        if nsent < 3:
            err(rctx, f"passage 文数 {nsent}")
        for para in paras:
            for sent in para:
                scan_text(rctx + " passage", sent)
        trans = pas.get("trans", {})
        for i in range(1, nsent + 1):
            if str(i) not in trans and i not in trans:
                err(rctx, f"全訳に文({i})が無い")
        if not s.get("questions"):
            err(rctx, "questions 空")
        for i, q in enumerate(s.get("questions", []), start=1):
            check_reading_q(f'{rctx} 問{i}', q)

    # mc 正解位置分布
    if mc_pos:
        dist = Counter(mc_pos)
        n = len(mc_pos)
        print(f"[info] mc 正解位置分布 (0起点): {dict(sorted(dist.items()))}  総数{n}")
        mx = max(dist.values())
        if mx > n * 0.45:
            warn("mc分布", f"偏りあり（最頻 {mx}/{n}）— ローテ推奨")

    print(f"[info] 文法 {len(GRAMMAR)}講 / 長文 {len(READING)}講 検査完了")
    return not ERRORS


MODS = {"chu": "content_chu", "kou": "content_kou", "sample": "sample_content"}


def main():
    # ★引数なしのときは **刷る2冊を両方** 検査する。
    #   以前は既定が "sample" で、1講しかない見本を検査して ALL PASS を出していた。
    #   run_all_gates.py は引数を渡さないので、CI の緑は「見本が無事」という意味しかなく、
    #   content_chu / content_kou が壊れても気づけなかった（2026-08-04 のレビューで発覚）。
    if len(sys.argv) > 1:
        targets = [MODS.get(sys.argv[1], sys.argv[1])]
    else:
        targets = ["content_chu", "content_kou"]
    ok = all([check_module(m) for m in targets])
    for w in WARNS:
        print(w)
    for e in ERRORS:
        print(e)
    seen = "/".join(targets)          # ★何を検査したかを必ず印字する（見本すり替えの再発防止）
    if ok:
        print(f"\n✅ ALL PASS ({seen})  WARN={len(WARNS)}")
        sys.exit(0)
    else:
        print(f"\n❌ FAIL: {len(ERRORS)} 件 ({seen})")
        sys.exit(1)


if __name__ == "__main__":
    main()
