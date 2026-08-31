#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Instagram カルーセル (4:5 vol シリーズ) の検査。

run_all_gates.py が引数なしで拾う。**引数なしの既定は「出す vol 全部」**。
何を見て何を見ていないかを必ず印字する (見ていないものを「通った」と言わないため)。

見るもの:
  1. vol データの整合   … build_vol.verify (記法の閉じ忘れ・ページ番号・図版の禁則・
                          引用英文が passage に実在するか・未検証の主張の宣言漏れ)
  2. 英文の全数照合     … スライドに出る英文を**総なめ**し、正典 passage か
                          en_examples のどちらかに実在することを確かめる。
                          (1) は引用部品だけを見るので、地の文に紛れた英文は
                          ここでしか捕まらない。
  3. 組んだ HTML の照合 … ページ番号・ドットの数と点灯位置・ブランド行が
                          データと一致するか (出力物とデータの突き合わせ)
  4. CSS クラスの衝突   … 部品の修飾子がレイアウト用クラスと同名だと
                          中身が全部改行される。実際に .dashnote.mid でやった。
  5. 和文フォントの順序 … スタックの先頭が和文でないと Linux で中国語字形に落ちる
  6. 刷った PNG        … あれば実寸と天地の余白を見る。無ければ「見ていない」と言う。

見ないもの (ここでは無理なので、そう言う):
  - 版面からのはみ出し … Chrome が要る。build_vol.py が刷る前に必ず測っている。
  - 正解の一意性・日本語の自然さ … 人手 (CLAUDE.md の相互チェック層③)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_vol as BV      # noqa: E402
import theme_vol as T       # noqa: E402
import fonts as F           # noqa: E402

# レイアウト用のクラス名 → そのクラスに付けてよい修飾子。
# ★部品の修飾子がレイアウト用と同名になると、部品が .mid (flex 縦積み) の指定を
#   もらって中身が全部改行される。実際に .dashnote.mid でやった。
#   「レイアウト用クラスに、許した修飾子以外が同居していないか」で捕まえる。
STRUCT_OK = {
    "stage": set(), "mid": {"center", "top"}, "foot": set(),
    "brand": set(), "title": set(), "rule": set(), "push": set(),
    "who": set(), "pg": set(),
}

# 2 語以上つながった英文。1 語だけの語注 (consciousness 意識) は拾わない。
_EN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9'’\-]*(?:[ ,:;.]+[A-Za-z][A-Za-z0-9'’\-]*)+")

# 和文フォントとして数える族 (スタックの先頭がこれでなければ中国語字形に落ちる)
_JA_FAMILIES = ("Noto Sans JP", "Noto Serif JP", "Hiragino", "Yu Gothic",
                "IPAGothic", "Noto Sans CJK JP", "游ゴシック", "Meiryo")

PNG_W, PNG_H = T.W * T.SCALE, T.H * T.SCALE


def _en_ok(run, passage, examples):
    """英文 run が正典か例文のどちらかに実在するか。"""
    s = BV._norm_en(run).strip(" .,:;").lower()
    if not s:
        return True
    if s in passage:
        return True
    return any(s in e for e in examples)


def check_vol(vol, bad):
    key = vol["key"]

    def ng(msg):
        bad.append(f"{key}: {msg}")

    for e in BV.verify(vol):
        bad.append(e)

    passage = BV._norm_en(vol["passage"]).lower()
    examples = [BV._norm_en(x).lower() for x in vol.get("en_examples", [])]

    for s in vol["slides"]:
        n = s["n"]
        # ── 2. 英文の全数照合 (図版の <text> も含める)
        texts = []
        for b in s["blocks"]:
            texts += [BV.plain(t) for t in BV._texts_of(b)]
            if b["kind"] == "fig":
                texts += re.findall(r"<text[^>]*>([^<]*)</text>", b["value"] or "")
        for t in texts:
            for run in _EN_RUN.findall(t):
                if not _en_ok(run, passage, examples):
                    ng(f"p{n}: 本文にも例文にも無い英文 → {run!r} "
                       f"(passage か en_examples に入れること)")

        # ── 3. 組んだ HTML とデータの突き合わせ
        html = BV.render_slide(vol, s)
        total = len(vol["slides"])
        on = html.count('class="dot on"')
        dots = html.count('class="dot"') + on
        if dots != total:
            ng(f"p{n}: ドットが {dots} 個 — {total} 個でなければならない")
        if on != 1:
            ng(f"p{n}: 点灯しているドットが {on} 個 — 1 個であること")
        if f'>{n}/{total}<' not in html:
            ng(f"p{n}: ページ番号 {n}/{total} が出力に無い")
        for field in ("brand", "series", "handle"):
            if vol[field].replace("&", "&amp;") not in html:
                ng(f"p{n}: {field} ({vol[field]!r}) が出力に無い")

        # ── 禁則 (server 側 sanitizer と同じ)
        low = html.lower()
        if "<script" in low:
            ng(f"p{n}: 出力に <script> が入っている")
        for h in (" onload=", " onclick=", " onerror=", " onmouseover="):
            if h in low:
                ng(f"p{n}: 出力に on* 属性が入っている ({h.strip()})")

        # ── 4. クラス名の衝突
        for cls in re.findall(r'class="([^"]+)"', html):
            names = set(cls.split())
            for st in names & set(STRUCT_OK):
                stray = names - {st} - STRUCT_OK[st]
                if stray:
                    ng(f"p{n}: レイアウト用クラス .{st} に許していない修飾子 "
                       f"{sorted(stray)} が同居している (部品が縦積みにされる)")


def check_fonts(bad):
    for name, stack in (("SANS", T.SANS), ("SERIF", T.SERIF)):
        first = stack.split(",")[0].strip('"\' ')
        if not any(f in first for f in _JA_FAMILIES):
            bad.append(f"書体: {name} の先頭が {first!r} — 和文の族でないと "
                       f"Linux で中国語字形 (WenQuanYi) に落ちる")
        if sum(1 for f in _JA_FAMILIES if f in stack) < 2:
            bad.append(f"書体: {name} に和文のフォールバックが 1 つ以下 — "
                       f"同梱フォントが無い環境で崩れる")


def judge_geometry(name, size, top_css, gap_css):
    """PNG の実寸と天地の余白から違反を列挙する純関数。

    ★変異試験 (check_carousel_guards.py) がここを直接叩けるように、
      ファイル読み込みと判定を分けてある。
    """
    out = []
    if size != (PNG_W, PNG_H):
        out.append(f"{name}: 実寸 {size} — {(PNG_W, PNG_H)} であること")
        return out
    if top_css is None:
        out.append(f"{name}: 中身が真っ暗 — 何も描かれていない")
        return out
    if top_css > 70:
        out.append(f"{name}: 天の余白が {top_css}px — 版面がずれている")
    if not (20 <= gap_css <= 70):
        out.append(f"{name}: 地の余白が {gap_css}px — 20〜70px の外。"
                   f"版面が縮んでいる (chrome.py の UI オフセット補正を疑う)")
    return out


def check_pngs(vol, bad, seen):
    """刷ってあれば見る。無ければ「見ていない」と記録する。"""
    d = os.path.join(BV.OUT, vol["key"])
    pngs = [os.path.join(d, f"{vol['key']}_{s['n']:02d}.png") for s in vol["slides"]]
    have = [p for p in pngs if os.path.exists(p)]
    if not have:
        seen.append(f"{vol['key']}: PNG は刷られていないので紙の検査は外した "
                    f"(手元で build_vol.py を回してから再実行すること)")
        return
    if len(have) != len(pngs):
        bad.append(f"{vol['key']}: PNG が {len(have)}/{len(pngs)} 枚しかない")
    try:
        from PIL import Image
    except ImportError:
        seen.append(f"{vol['key']}: Pillow が無いので PNG の中身は見ていない")
        return
    import chrome
    for p in have:
        nm = os.path.basename(p)
        size = chrome.png_size(p)
        top = gap = None
        if size == (PNG_W, PNG_H):
            im = Image.open(p).convert("L")
            px, (w, h) = im.load(), im.size
            lo = hi = None
            for y in range(h):
                if max(px[x, y] for x in range(0, w, 9)) > 70:
                    if lo is None:
                        lo = y
                    hi = y
            top = None if lo is None else lo // T.SCALE
            gap = None if hi is None else (h - 1 - hi) // T.SCALE
        bad.extend(judge_geometry(nm, size, top, gap if gap is not None else 0))
    seen.append(f"{vol['key']}: PNG {len(have)} 枚を検査した")


def main():
    vols = BV.load_vols()
    bad, seen = [], []
    print(f"検査対象: {[v['key'] for v in vols]} "
          f"(各 {len(vols[0]['slides']) if vols else 0} 枚)")
    print(f"  {F.describe()}")
    if not vols:
        print("[NG] vols/ に vol が 1 つも無い")
        return 1

    check_fonts(bad)
    for v in vols:
        check_vol(v, bad)
        check_pngs(v, bad, seen)

    for line in seen:
        print(f"  - {line}")
    print("  - 版面からのはみ出しは build_vol.py が刷る前に測っている "
          "(Chrome が要るのでここでは見ていない)")
    print("  - 正解の一意性・日本語の自然さは人手で見ること "
          "(CLAUDE.md の相互チェック層③)")

    if bad:
        print(f"\n[NG] 見つかった問題 {len(bad)} 件:")
        for b in bad:
            print(f"  ✗ {b}")
        return 1
    print(f"\n[OK] {len(vols)} vol / 違反 0 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
