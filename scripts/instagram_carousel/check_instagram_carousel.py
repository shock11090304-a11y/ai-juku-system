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
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_vol as BV      # noqa: E402
import theme_vol as T       # noqa: E402
import fonts as F           # noqa: E402

# ── クラス衝突の見張り ────────────────────────────────────────────
# ★名前の一覧を手で持たない。手で持つと「知っている 9 個」しか守れず、
#   .dashnote.opts のように同じ壊れ方をする組み合わせが素通りする。
#   CSS から「意図して用意された組み合わせ (.a.b)」と
#   「単独で指定を持つクラス」を読み取り、
#   *意図されていない同居* を落とす。


def _css_index(css):
    """CSS から (意図された組み合わせ, 単独指定のあるクラス, レイアウト指定のクラス)。"""
    combos, standalone, layout = set(), set(), set()
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        for one in sel.split(","):
            one = one.strip()
            if not one:
                continue
            last = one.split()[-1]                       # 子孫セレクタの末尾
            names = re.findall(r"\.([A-Za-z0-9_-]+)", last)
            if len(names) >= 2:
                for i in range(len(names)):
                    for j in range(i + 1, len(names)):
                        combos.add(frozenset((names[i], names[j])))
            elif len(names) == 1:
                standalone.add(names[0])
                if re.search(r"\bdisplay\s*:", body):
                    layout.add(names[0])
    return combos, standalone, layout


CSS_COMBOS, CSS_STANDALONE, CSS_LAYOUT = _css_index(T.CSS)

# 2 語以上つながった英文。1 語だけの語注 (consciousness 意識) は拾わない。
# ★語の区切りは空白だけではない。ハイフン・改行・全角空白・スラッシュ・中黒で
#   繋いだ英文が素通りしていたので、走査の前に区切りを空白へ寄せる。
_EN_SEP = re.compile(r"[\-–—/・\u3000\n\t]+")
_EN_RUN = re.compile(r"[A-Za-z][A-Za-z0-9'’]*(?:[ ,:;.]+[A-Za-z][A-Za-z0-9'’]*)+")


def _en_runs(text, vol=None):
    """英文の並びを拾う。自分のハンドルとドメインは「引用した英文」ではないので外す。"""
    if vol:
        for own in (vol.get("site"), vol.get("handle"), vol.get("brand")):
            if own:
                text = text.replace(own, " ")
    return _EN_RUN.findall(_EN_SEP.sub(" ", text))

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
            for run in _en_runs(t, vol):
                if not _en_ok(run, passage, examples):
                    ng(f"p{n}: 本文にも例文にも無い英文 → {run!r} "
                       f"(passage か en_examples に入れること)")

        # ── 3. 組んだ HTML とデータの突き合わせ
        html = BV.render_slide(vol, s)
        total = len(vol["slides"])
        # ★「render_slide が書いた文字列を同じ値で探す」照合は同語反復で、
        #   データを壊しても絶対に発火しない。出力から**位置**を読み戻して、
        #   データの n と突き合わせる (描画側の off-by-one を捕まえる)。
        seq = re.findall(r'class="dot( on)?"', html)
        if len(seq) != total:
            ng(f"p{n}: ドットが {len(seq)} 個 — {total} 個でなければならない")
        lit = [i for i, x in enumerate(seq) if x]
        if len(lit) != 1:
            ng(f"p{n}: 点灯しているドットが {len(lit)} 個 — 1 個であること")
        elif lit[0] != n - 1:
            ng(f"p{n}: 点灯位置が左から {lit[0] + 1} 番目 — {n} 番目であること")
        m = re.search(r'class="pgnum">([^<]*)<', html)
        if not m:
            ng(f"p{n}: ページ番号が出力に無い")
        elif m.group(1) != f"{n}/{total}":
            ng(f"p{n}: ページ番号の表示が {m.group(1)!r} — {n}/{total} であること")
        for field in ("brand", "series", "handle", "site", "label"):
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
            names = sorted(set(cls.split()))
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    a, b = names[i], names[j]
                    if frozenset((a, b)) in CSS_COMBOS:
                        continue          # CSS に .a.b がある = 意図した組み合わせ
                    if a in CSS_LAYOUT or b in CSS_LAYOUT:
                        ng(f"p{n}: .{a} と .{b} が同居しているが CSS に "
                           f".{a}.{b} が無い。片方が display 指定を持つので "
                           f"中身の並びが壊れる")
                    elif a in CSS_STANDALONE and b in CSS_STANDALONE:
                        ng(f"p{n}: .{a} と .{b} が同居しているが CSS に "
                           f".{a}.{b} が無い (意図しない指定の混ざり)")


IG_CAPTION_MAX = 2200   # Instagram の本文上限 (ハッシュタグ込み)
IG_HASHTAG_MAX = 30


def check_caption(vol, bad):
    """投稿文を見る。Instagram の制約と、本文と同じ「実在・宣言」の規律をかける。

    ★画像だけ検査して投稿文を野放しにすると、いちばん人目に触れる文章が
      無検査になる。出典の断言も英文の引用も、スライドと同じ規律で見る。
    """
    key = vol["key"]
    cap = vol.get("caption")
    if not cap:
        bad.append(f"{key}: caption が無い (投稿文もデータとして持つこと)")
        return
    tags = cap.get("hashtags") or []
    tag_line = " ".join(tags)

    if len(tags) > IG_HASHTAG_MAX:
        bad.append(f"{key}: ハッシュタグが {len(tags)} 個 — Instagram の上限は {IG_HASHTAG_MAX}")
    if len(set(tags)) != len(tags):
        dup = sorted({t for t in tags if tags.count(t) > 1})
        bad.append(f"{key}: ハッシュタグが重複している → {dup}")
    for t in tags:
        if not t.startswith("#") or len(t) < 2 or any(c.isspace() for c in t):
            bad.append(f"{key}: ハッシュタグの形が不正 → {t!r}")

    passage = BV._norm_en(vol["passage"]).lower()
    examples = [BV._norm_en(x).lower() for x in vol.get("en_examples", [])]
    declared = ([x for x in vol.get("unverified", []) if x]
                + [x for x in vol.get("disclaimers", []) if x])

    for kind in ("full", "short"):
        text = cap.get(kind)
        if not text:
            bad.append(f"{key}: caption[{kind}] が空")
            continue
        total = len(text) + 1 + len(tag_line)
        if total > IG_CAPTION_MAX:
            bad.append(f"{key}: caption[{kind}] がタグ込みで {total} 字 — "
                       f"上限 {IG_CAPTION_MAX} 字を超えている")
        # 記法タグの消し忘れ (投稿文は素のテキスト)
        for name in T.INLINE:
            if f"[{name}]" in text or f"[/{name}]" in text:
                bad.append(f"{key}: caption[{kind}] に記法 [{name}] が残っている "
                           f"(投稿文は素のテキスト)")
        # 英文は正典か例文に実在すること
        for run in _en_runs(text, vol):
            if not _en_ok(run, passage, examples):
                bad.append(f"{key}: caption[{kind}] に本文にも例文にも無い英文 → {run!r}")
        # 出典の断言は行ごとに宣言を要求する
        for line in text.splitlines():
            if BV._is_claim(line) and not any(d in line for d in declared):
                bad.append(f"{key}: caption[{kind}] の未検証の主張が unverified に "
                           f"宣言されていない → {line.strip()[:44]!r}")


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


SHEET_MAD_MAX = 8.0   # 一覧 JPG と刷った PNG の平均絶対差の上限 (実測: 一致 2〜3 / 取り違え 21〜23)


def judge_content(key, items, sheet):
    """刷り上がりの中身を判定する純関数。

    items: [(名前, PIL.Image(RGB))] を版面の順に。sheet: 一覧 JPG の Image か None。
    ★ファイル読み込みと判定を分けてあるのは、変異試験 (check_carousel_guards.py) が
      壊した画像を**メモリ上で**作って直接叩けるようにするため。
    """
    from PIL import Image, ImageChops, ImageStat
    out, seen_bytes = [], {}
    for nm, im in items:
        g = im.convert("L")
        px, (w, h) = g.load(), g.size
        if not any(max(px[x, y] for x in range(0, w, 9)) > 70
                   for y in range(int(h * 0.22), int(h * 0.78), 7)):
            out.append(f"{nm}: 本文の帯に何も無い (ヘッダとフッタだけ刷れている)")
        seen_bytes.setdefault(im.convert("RGB").tobytes(), []).append(nm)
    for names in seen_bytes.values():
        if len(names) > 1:
            out.append(f"{key}: 中身が同一の刷り上がりがある → {names} "
                       f"(刷り直し漏れか取り違え)")
    if sheet is None:
        out.append(f"{key}: 一覧 JPG が無い (build_vol.py が作る。"
                   f"これだけがリポジトリに残る成果物)")
        return out
    tw = 430
    th = int(tw * T.H / T.W)
    for i, (nm, im) in enumerate(items):
        x, y = (i % 3) * (tw + 10) + 10, (i // 3) * (th + 10) + 10
        if x + tw > sheet.size[0] or y + th > sheet.size[1]:
            out.append(f"{key}: 一覧の大きさ {sheet.size} が {len(items)} 枚と合わない")
            break
        a = im.convert("RGB").resize((tw, th), Image.LANCZOS)
        m = ImageStat.Stat(ImageChops.difference(
            a, sheet.convert("RGB").crop((x, y, x + tw, y + th)))).mean[0]
        if m > SHEET_MAD_MAX:
            out.append(f"{nm}: コミットしてある一覧 JPG の {i + 1} 枚目と一致しない "
                       f"(平均差 {m:.1f})。刷り直したら一覧も作り直すこと")
    return out


def check_pngs(vol, bad, seen):
    """刷ってあれば見る。無ければ「見ていない」と記録する。

    ★寸法と天地の余白だけでは足りない。本文帯が空でも、6 枚すべてが同じ画像でも
      通ってしまう。中身・互いの相違・コミットしてある一覧 JPG との一致まで見る。
    """
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
        bad.append(f"{vol['key']}: Pillow が無いので刷り上がりを検査できない。"
                   f"入れるか、PNG を消してから回すこと")
        return
    import chrome
    items = []
    for p in have:
        nm = os.path.basename(p)
        size = chrome.png_size(p)
        top = gap = None
        if size == (PNG_W, PNG_H):
            im = Image.open(p).convert("RGB")
            g = im.convert("L")
            px, (w, h) = g.load(), g.size
            lo = hi = None
            for y in range(h):
                if max(px[x, y] for x in range(0, w, 9)) > 70:
                    if lo is None:
                        lo = y
                    hi = y
            top = None if lo is None else lo // T.SCALE
            gap = None if hi is None else (h - 1 - hi) // T.SCALE
            items.append((nm, im))
        bad.extend(judge_geometry(nm, size, top, gap if gap is not None else 0))
    sheet_p = os.path.join(d, f"{vol['key']}_sheet.jpg")
    sheet = Image.open(sheet_p) if os.path.exists(sheet_p) else None
    if len(items) == len(pngs):
        bad.extend(judge_content(vol["key"], items, sheet))
        seen.append(f"{vol['key']}: 一覧 JPG と刷り上がり {len(items)} 枚を突き合わせた")
    seen.append(f"{vol['key']}: PNG {len(have)} 枚を検査した")


def main():
    vols = BV.load_vols()
    bad, seen = [], []
    print("検査対象: " + ", ".join(f"{v['key']}({len(v['slides'])}枚)" for v in vols))

    # ★vols/ に置いたのに読み込まれていない冊が無いか。load_vols は
    #   VOL が無いモジュールを黙って捨て、key が衝突すると後勝ちで消える。
    #   刷る側も同じ関数を使うので、突き合わせないと誰も気づけない。
    import glob
    files = [f for f in glob.glob(os.path.join(HERE, "vols", "*.py"))
             if not os.path.basename(f).startswith("_")]
    if len(files) != len(vols):
        bad.append(f"vols/ に {len(files)} 本あるのに読み込めたのは {len(vols)} 冊 "
                   f"({sorted(os.path.basename(f) for f in files)} / "
                   f"{[v['key'] for v in vols]}) — VOL の書き忘れか key の重複")
    print(f"  {F.describe()}")
    if not vols:
        print("[NG] vols/ に vol が 1 つも無い")
        return 1

    check_fonts(bad)
    for v in vols:
        check_vol(v, bad)
        check_caption(v, bad)
        check_pngs(v, bad, seen)

    for line in seen:
        print(f"  - {line}")
    print("  - 版面からのはみ出しは build_vol.py が刷る前に測っている "
          "(Chrome が要るのでここでは見ていない)")
    print("  - 正解の一意性・日本語の自然さは人手で見ること "
          "(CLAUDE.md の相互チェック層③)")
    for v in vols:
        for note in v.get("editorial_notes", []):
            print(f"    · [{v['key']}] {note}")

    if bad:
        print(f"\n[NG] 見つかった問題 {len(bad)} 件:")
        for b in bad:
            print(f"  ✗ {b}")
        return 1
    print(f"\n[OK] {len(vols)} vol / 違反 0 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
