#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4:5 「vol シリーズ」Instagram カルーセルを組んで PNG に焼く。

  python3 scripts/instagram_carousel/build_vol.py             # 全 vol を刷る
  python3 scripts/instagram_carousel/build_vol.py vol01       # 1 つだけ
  python3 scripts/instagram_carousel/build_vol.py --html-only # HTML だけ (Chrome 不要)
  ... --desktop        刷ったものを ~/Desktop/trillion-ig/<key>/ にも置く
  ... --out DIR        刷ったものを DIR/<key>/ にも置く
  ... --no-fit         はみ出しの実測を省く (速いが納品には使わない)
  ... --no-font-fetch  和文フォントを取りに行かない (オフライン用)

中身 (文言・図) は vols/<key>.py にデータとして置く。ここには意匠の組み立てしか無い。
vol.02 を作るときは vols/vol02.py を足すだけでよい (このファイルは触らない)。

★ビルド時に verify() が走る。記法の閉じ忘れ・ページ番号のずれ・
  「本文に無い英文を引用している」を見つけたらここで止まる。
  刷ったあとの検査は check_instagram_carousel.py。
"""
import importlib
import math
import os
import pkgutil
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import theme_vol as T  # noqa: E402
from theme_vol import inline, plain, check_markup  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out_vol")


# ── vol データを書くときの糖衣 ────────────────────────────────────────
def B(kind, value=None, **opts):
    d = {"kind": kind, "value": value}
    d.update(opts)
    return d


# ── 手描き風の線 (SVG) ────────────────────────────────────────────────
def _catmull(pts, close_gap=True):
    """点列を Catmull-Rom で滑らかな三次ベジェの path 文字列にする。"""
    d = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[0]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6.0, p1[1] + (p2[1] - p0[1]) / 6.0)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6.0, p2[1] - (p3[1] - p1[1]) / 6.0)
        d.append(f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return " ".join(d)


def rough_ellipse(cx, cy, rx, ry, rot=0.0, jitter=0.055, phase=0.0,
                  start=-0.20, end=2 * math.pi + 0.30, steps=56):
    """手で丸を付けたような楕円の path。始点と終点をわざと重ねて閉じきらない。

    ★決定的 (乱数を使わない)。同じ引数なら常に同じ形になるので、
      刷り直しても図が勝手に変わらない = 差分レビューが効く。
    """
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(steps + 1):
        t = start + (end - start) * i / steps
        w = 1.0 + jitter * math.sin(3 * t + phase) * math.cos(2 * t + phase * 0.7)
        x, y = rx * w * math.cos(t), ry * w * math.sin(t)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return _catmull(pts)


def squiggle(x1, x2, y, amp=3.2, period=17.0):
    """波下線。"""
    pts, x = [], x1
    while x <= x2:
        pts.append((x, y + amp * math.sin((x - x1) / period * math.pi)))
        x += 3.0
    return _catmull(pts)


# ── 部品 ──────────────────────────────────────────────────────────────
def _en_lines(v):
    return v if isinstance(v, (list, tuple)) else [v]


def c_badge(b):
    return f'<div class="badge-wrap"><div class="badge">{inline(b["value"])}</div></div>'


def c_chip(b):
    return f'<div class="chip">{inline(b["value"])}</div>'


def c_quote(b):
    cls = "quote sm" if b.get("sm") else "quote"
    rows = "".join(f'<div class="qline"><span>{inline(l)}</span></div>'
                   for l in _en_lines(b["value"]))
    return f'<div class="{cls}">{rows}</div>'


def c_dashbox_en(b):
    rows = "<br>".join(inline(l) for l in _en_lines(b["value"]))
    return f'<div class="dashbox">{rows}</div>'


def c_dashbox(b):
    return f'<div class="dashbox" style="font-family:inherit">{inline(b["value"])}</div>'


def c_bigq(b):
    return f'<div class="bigq">{inline(b["value"])}</div>'


def c_h(b):
    cls = "h" + (" sm" if b.get("sm") else "") + (" left" if b.get("left") else "")
    return f'<div class="{cls}">{inline(b["value"])}</div>'


def c_lead(b):
    return f'<div class="lead">{inline(b["value"])}</div>'


def c_gloss(b):
    return f'<div class="gloss">{inline(b["value"])}</div>'


def c_trans(b):
    return f'<div class="trans">{inline(b["value"])}</div>'


def c_eyebrow(b):
    return f'<div class="eyebrow">{inline(b["value"])}</div>'


def c_opts(b):
    rows = "".join(
        f'<div class="opt"><span class="k">{inline(k)}</span>'
        f'<span class="v">{inline(v)}</span></div>' for k, v in b["value"])
    return f'<div class="opts">{rows}</div>'


def c_pill_pink(b):
    return f'<div class="pill-pink">{inline(b["value"])}</div>'


def c_hint(b):
    return f'<div class="hint">{inline(b["value"])}</div>'


def c_answer(b):
    """巨大な正解文字 + 手描き風のピンク二重楕円。

    ★preserveAspectRatio="none" が要る。既定 (meet) だと viewBox が縦横比を保って
      縮み、楕円が文字より小さくなって字を串刺しにする。
      代わりに線幅が歪むので vector-effect="non-scaling-stroke" で戻す。
    """
    p1 = rough_ellipse(150, 100, 132, 90, rot=-4, phase=0.0)
    p2 = rough_ellipse(150, 100, 141, 96, rot=3, phase=1.9, jitter=0.075,
                       start=0.15, end=2 * math.pi + 0.05)
    stroke = ('stroke-linecap="round" vector-effect="non-scaling-stroke"')
    svg = (f'<svg viewBox="0 0 300 200" preserveAspectRatio="none" fill="none" '
           f'xmlns="http://www.w3.org/2000/svg">'
           f'<path d="{p1}" stroke="{T.PINK}" stroke-width="7" {stroke}/>'
           f'<path d="{p2}" stroke="{T.PINK}" stroke-width="5" stroke-opacity="0.75" '
           f'{stroke}/></svg>')
    return f'<div class="answer">{svg}<span class="ch">{inline(b["value"])}</span></div>'


def c_goodbox(b):
    return f'<div class="goodbox">{inline(b["value"])}</div>'


def c_badbox(b):
    return f'<div class="badbox">{inline(b["value"])}</div>'


def c_rulebox(b):
    rows = "".join(f'<div class="row">{inline(r)}</div>' for r in b["value"])
    return f'<div class="rulebox">{rows}</div>'


def c_notebar(b):
    return f'<div class="notebar">{inline(b["value"])}</div>'


def c_dashnote(b):
    cls = "dashnote ctr" if b.get("ctr") else "dashnote"
    return f'<div class="{cls}">{inline(b["value"])}</div>'


def c_fig(b):
    return f'<div class="fig">{b["value"]}</div>'


def c_source(b):
    return f'<div class="source">{inline(b["value"])}</div>'


def c_cta(b):
    return f'<div class="cta">{inline(b["value"])}</div>'


def c_gap(b):
    return f'<div class="gap-{b["value"] or "m"}"></div>'


def c_push(b):
    return '<div class="push"></div>'


COMPONENTS = {
    "badge": c_badge, "chip": c_chip, "quote": c_quote, "dashbox_en": c_dashbox_en,
    "dashbox": c_dashbox, "bigq": c_bigq, "h": c_h, "lead": c_lead, "gloss": c_gloss,
    "trans": c_trans, "eyebrow": c_eyebrow, "opts": c_opts, "pill_pink": c_pill_pink,
    "hint": c_hint, "answer": c_answer, "goodbox": c_goodbox, "badbox": c_badbox,
    "rulebox": c_rulebox, "notebar": c_notebar, "dashnote": c_dashnote, "fig": c_fig,
    "source": c_source, "cta": c_cta, "gap": c_gap, "push": c_push,
}

# 本文の英文を「表示している」部品 = 正典の passage に実在しなければならない
EN_COMPONENTS = ("quote", "dashbox_en")


# ── 1 枚を組む ────────────────────────────────────────────────────────
def render_slide(vol, slide):
    n, total = slide["n"], len(vol["slides"])
    body = []
    for b in slide["blocks"]:
        fn = COMPONENTS.get(b["kind"])
        if fn is None:
            raise ValueError(f"{vol['key']} p{n}: 未知の部品 {b['kind']!r}")
        body.append(fn(b))

    dots = "".join(f'<span class="dot{" on" if i == n else ""}"></span>'
                   for i in range(1, total + 1))
    head = (
        f'<div class="brand">{inline(vol["brand"])}</div>'
        f'<div class="title"><span class="t">{inline(vol["series"])}</span>'
        f'<span class="vol">{inline(vol["label"])}</span></div>'
        f'<div class="rule"></div>'
    )
    foot = (
        f'<div class="foot">'
        f'<span class="who">{inline(vol["handle"])}　・　{inline(vol["site"])}</span>'
        f'<span class="pg"><span class="dots">{dots}</span>'
        f'<span class="pgnum">{n}/{total}</span></span></div>'
    )
    mid = f'<div class="mid {slide.get("align", "center")}">' + "".join(body) + "</div>"
    stage = f'<div class="stage">{head}{mid}{foot}</div>'
    return ("<!doctype html><html lang=ja><head><meta charset=utf-8><style>"
            + font_css() + T.CSS + "</style></head><body>" + stage + "</body></html>")


_FONT_CSS = None


def font_css():
    """同梱フォントの @font-face。無ければ空文字でシステムのフォントに任せる。

    ★ここでは取得しない (読むだけ)。検査から呼ばれても外に出ないようにするため。
      取得は build 側 (main) が明示的に行う。
    """
    global _FONT_CSS
    if _FONT_CSS is None:
        import fonts
        _FONT_CSS = fonts.face_css()
    return _FONT_CSS


# ── はみ出し検出 ──────────────────────────────────────────────────────
# ★版面 (1080x1350) に本文が収まらない壊れ方は 2 通りある。両方測る。
#
#   縦: .mid が flex で縮んで「切り落とされる」のではなく**フッターに重なる**。
#       画面の外に出ないので、版面の下を覗くだけでは検出できない (最初これで空振りした)。
#       → .stage の height を auto にし、.mid を flex:0 0 auto にして
#         「本文が本来必要とする高さ」を出し、1350 を超えた分を測る。
#   横: 英文は white-space:nowrap で組むので、幅が足りないと横へ溢れる。
#       ★撮影窓を版面と同じ幅にすると、溢れた分はスクリーンショットに**写らない**。
#         (最初これで「横は必ず 0」という嘘の検査を書いた)
#       → 版面の左右に PAD の余白を作った窓で撮り、その余白に色が乗るかを見る。
#         中央寄せの行は左右どちらにも溢れるので、両側を見る。
_PROBE_PAD = 300          # 版面の左右に取る観測用の余白 (CSS px)
_PROBE_EXTRA_H = 900      # 版面の下に取る観測用の余白 (CSS px)
# ★padding-left は body だけに当てる。html にも当てると版面ごと右にずれ、
#   「右の観測帯」に版面そのものが入って**全スライドが横に溢れている**と誤報する。
_PROBE_CSS = (
    "html,body{background:#ff00ff !important;overflow:visible !important;"
    "width:auto !important;height:auto !important}"
    "body{padding-left:%dpx !important}"
    ".stage{overflow:visible !important;height:auto !important;min-height:%dpx !important}"
    ".mid{flex:0 0 auto !important;min-height:0 !important;justify-content:flex-start !important}"
    ".push{flex:0 0 auto !important;height:12px !important}"
) % (_PROBE_PAD, 1350)


def overflow_px(html_text, work_dir, name):
    """版面からのはみ出しを {"v": 下へ, "l": 左へ, "r": 右へ} で返す (CSS px)。

    ★観測できる幅は左右それぞれ _PROBE_PAD まで。それを超える溢れは
      「_PROBE_PAD」で頭打ちになるが、0 でないことは分かるので用は足りる。
    """
    from PIL import Image, ImageChops
    import chrome
    os.makedirs(work_dir, exist_ok=True)
    hp = os.path.join(work_dir, name + ".probe.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html_text.replace("</style>", _PROBE_CSS + "</style>", 1))
    pp = os.path.join(work_dir, name + ".probe.png")
    win_w = T.W + _PROBE_PAD * 2
    win_h = T.H + _PROBE_EXTRA_H
    chrome.shot(hp, pp, win_w, win_h, T.SCALE)

    im = Image.open(pp).convert("RGB")
    sc = T.SCALE

    def ink(box):
        reg = im.crop(box)
        if reg.size[0] <= 0 or reg.size[1] <= 0:
            return None
        diff = ImageChops.difference(reg, Image.new("RGB", reg.size, (255, 0, 255)))
        return diff.convert("L").point(lambda v: 255 if v > 14 else 0).getbbox()

    x0, x1 = _PROBE_PAD * sc, (_PROBE_PAD + T.W) * sc   # 版面の左右端
    y1 = T.H * sc                                       # 版面の下端

    bb = ink((x0, y1, x1, im.size[1]))
    v = 0 if bb is None else -(-bb[3] // sc)
    bb = ink((0, 0, x0, im.size[1]))
    left = 0 if bb is None else -(-(x0 - bb[0]) // sc)
    bb = ink((x1, 0, im.size[0], im.size[1]))
    right = 0 if bb is None else -(-bb[2] // sc)
    return {"v": v, "l": left, "r": right}


def overflow_message(name, over):
    """はみ出しがあれば人間向けの 1 行を返す。無ければ None。"""
    parts = []
    if over["v"]:
        parts.append(f"下へ {over['v']}px")
    if over["l"]:
        parts.append(f"左へ {over['l']}px")
    if over["r"]:
        parts.append(f"右へ {over['r']}px")
    if not parts:
        return None
    return (f"✗ {name}: 版面から{'・'.join(parts)}はみ出している。"
            f"文字数を減らすか、間 (gap) と字の大きさを詰めること")


# ── ビルド時 verify ───────────────────────────────────────────────────
def _norm_en(s):
    """英文照合用の正規化: 引用符の異体字と空白を潰す。"""
    for a, b in [("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"),
                 ("—", "-"), ("–", "-")]:
        s = s.replace(a, b)
    return " ".join(s.split())


def verify(vol):
    """刷る前に落とす。返り値は違反メッセージのリスト (空なら健全)。"""
    errs = []
    key = vol["key"]

    for f in ("key", "series", "label", "handle", "site", "brand", "passage", "slides"):
        if not vol.get(f):
            errs.append(f"{key}: 必須項目 {f} が無い")
    if errs:
        return errs

    passage = _norm_en(vol["passage"])

    # ページ番号が 1..N で連続しているか
    got = [s.get("n") for s in vol["slides"]]
    want = list(range(1, len(vol["slides"]) + 1))
    if got != want:
        errs.append(f"{key}: ページ番号が {got} — {want} でなければならない")

    for s in vol["slides"]:
        n = s.get("n")
        for b in s.get("blocks", []):
            kind = b.get("kind")
            if kind not in COMPONENTS:
                errs.append(f"{key} p{n}: 未知の部品 {kind!r}")
                continue

            # 記法の閉じ忘れ・未知タグ
            for txt in _texts_of(b):
                for e in check_markup(txt):
                    errs.append(f"{key} p{n} [{kind}]: {e}")

            # ★引用した英文が正典の passage に実在するか。
            #   行ごとに見ると、本文の離れた場所から切り出した行を並べて
            #   「本文に無い主張」を作れてしまう (行の順序も隣接も見ないため)。
            #   引用ブロックは 1 続きの抜き書きなので、**繋げて**照合する。
            if kind in EN_COMPONENTS:
                joined = _norm_en(" ".join(plain(l) for l in _en_lines(b["value"])))
                joined = joined.strip('"').strip()
                if joined and joined not in passage:
                    errs.append(
                        f"{key} p{n} [{kind}]: 本文にその並びで存在しない英文を"
                        f"引用している → {joined!r}")

            # 図版に script / on* が混ざっていないか (server 側 sanitizer と同じ禁則)
            if kind == "fig":
                svg = (b.get("value") or "")
                low = svg.lower()
                if "<script" in low:
                    errs.append(f"{key} p{n} [fig]: <script> は禁止")
                for h in (" onload=", " onclick=", " onerror=", " onmouseover="):
                    if h in low:
                        errs.append(f"{key} p{n} [fig]: on* 属性は禁止 ({h.strip()})")

    # ★外部の事実を断言している箇所は unverified に宣言されていること。
    #   このリポジトリは「作り話を本物として見せない」を明文の規則にしている。
    #   出典表記や「予備校の模範解答が割れた」は機械では裏が取れないので、
    #   せめて「裏を取っていない」ことを宣言させ、宣言漏れをここで落とす。
    # ★宣言は 6 文字以上。「京都大学」「問」のような短い語を 1 つ置くだけで
    #   全部の出典行を黙らせられてしまう (何を検証していないのかも伝わらない)。
    declared = [x for x in vol.get("unverified", []) if x]
    for d in declared:
        if len(d) < 6:
            errs.append(f"{key}: unverified の宣言 {d!r} が短すぎる "
                        f"(6 文字以上で、何を検証していないか分かる形にすること)")
    for s in vol["slides"]:
        for b in s.get("blocks", []):
            for txt in _texts_of(b):
                t = plain(txt)
                if not _is_claim(t):
                    continue
                if not any(d in t for d in declared):
                    errs.append(
                        f"{key} p{s.get('n')}: 未検証の主張が unverified に宣言されていない → {t[:44]!r}")
    # 宣言したのに本文のどこにも出てこないもの (消し忘れ) も落とす
    all_text = " ".join(plain(t) for s in vol["slides"]
                        for b in s.get("blocks", []) for t in _texts_of(b))
    for d in declared:
        if d not in all_text:
            errs.append(f"{key}: unverified に宣言された {d!r} が本文のどこにも無い (消し忘れ)")
    return errs


# ★「出典っぽさ」は語の並びで判じるしかないので、取りこぼす方に倒さない。
#   以前は「出典・模範解答・入試」と「4桁年+大学」だけを見ていて、
#   「京大 2023年 第2問」「赤本」「共通テスト 2025 追試」が素通りした。
_CLAIM_WORDS = (
    "出典", "模範解答", "解答例", "入試", "過去問", "赤本", "青本", "本試", "追試",
    "共通テスト", "センター試験", "二次試験", "実際に出題", "出題された",
)
_CLAIM_SCHOOLS = (
    "大学", "大学院", "東大", "京大", "阪大", "北大", "東北大", "名大", "九大",
    "一橋", "東工大", "早大", "慶大", "早稲田", "慶應", "上智", "明治", "青学",
    "立教", "中央", "法政", "同志社", "立命館", "関学", "関大",
)
_CLAIM_YEAR = re.compile(r"(19|20)\d{2}\s*(年度|年)?")


def _is_claim(t):
    """裏を取っていないと危ない「外部の事実の断言」か。

    ★取りこぼすくらいなら余計に拾う。余計に拾った分は unverified に 1 行
      書けば済むが、取りこぼすと未検証の断言がそのまま刷られる。
    """
    if any(w in t for w in _CLAIM_WORDS):
        return True
    if any(w in t for w in _CLAIM_SCHOOLS) and _CLAIM_YEAR.search(t):
        return True
    return any(w in t for w in _CLAIM_SCHOOLS) and ("問" in t or "第" in t)


def _texts_of(b):
    """部品が表示する文字列を全部拾う (検査用)。

    ★図版 (fig) の中の文字も拾う。以前は fig を丸ごと除外していたので、
      SVG の <text> に書いた出典表記が「未検証の主張」の検査をすり抜けた。
    """
    v = b.get("value")
    if b.get("kind") == "fig":
        return _svg_texts(v or "")
    if isinstance(v, str):
        return [v]
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, (list, tuple)):
                out += [y for y in x if isinstance(y, str)]
        return out
    return []


def write_caption(vol, out_dir):
    """投稿文を貼り付け用のテキストに書き出す (正典は vols/<key>.py の caption)。"""
    cap = vol.get("caption")
    if not cap:
        return None
    tags = " ".join(cap.get("hashtags") or [])
    parts = []
    for label, kind in (("詳細版", "full"), ("短縮版", "short")):
        body = cap.get(kind)
        if not body:
            continue
        n = len(body) + 1 + len(tags)
        parts.append(f"===== {vol['label']} {label} ({n}字 / 上限2200) =====\n\n"
                     f"{body}\n\n{tags}\n")
    if not parts:
        return None
    out = os.path.join(out_dir, f"{vol['key']}_caption.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts))
    return out


DESKTOP_SUBDIR = "trillion-ig"


def deliver(vol, src_dir, dest_root):
    """刷り上がりを配布先へコピーする。

    ★刷る場所そのものは out_vol/ から動かさない。配布先へ「刷る」ようにすると
      検査 (刷り上がりと一覧 JPG の突き合わせ) が見に行く場所を見失う。
      あくまで**出来上がったものを配る**ステップにしてある。
    """
    import shutil
    dest = os.path.join(os.path.expanduser(dest_root), vol["key"])
    os.makedirs(dest, exist_ok=True)
    copied = []
    for name in sorted(os.listdir(src_dir)):
        if name.lower().endswith((".png", ".jpg", ".txt")):
            shutil.copy2(os.path.join(src_dir, name), os.path.join(dest, name))
            copied.append(name)
    return dest, copied


def desktop_root():
    """~/Desktop を返す。無ければ何が起きているか分かる形で落とす。"""
    d = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.isdir(d):
        raise SystemExit(
            f"✗ {d} が無い。--desktop はデスクトップのある端末 (塾長の Mac) 用。\n"
            f"  クラウドや CI では使えないので --out DIR で場所を指定すること")
    return os.path.join(d, DESKTOP_SUBDIR)


def contact_sheet(vol, pngs, out_dir):
    """全スライドを 1 枚に並べた JPG を作る。

    ★これだけは git に入れる。PNG と HTML は .gitignore の
      `scripts/**/*.png` `scripts/**/*.html` で弾かれるので、
      刷った現物はリポジトリに残らない。次のセッションが
      「どういう見た目が正しいのか」を確かめられるように、
      軽い JPG の一覧だけを残す (拡張子が違うので追跡できる)。
    """
    try:
        from PIL import Image
    except ImportError:
        return None
    tw, th = 430, int(430 * T.H / T.W)
    cols = 3
    rows = -(-len(pngs) // cols)
    sheet = Image.new("RGB", (tw * cols + 10 * (cols + 1),
                              th * rows + 10 * (rows + 1)), (24, 22, 40))
    for i, p in enumerate(pngs):
        im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * (tw + 10) + 10, (i // cols) * (th + 10) + 10))
    out = os.path.join(out_dir, f"{vol['key']}_sheet.jpg")
    sheet.save(out, quality=86, optimize=True)
    return out


# ── vol の読み込み ────────────────────────────────────────────────────
def _svg_texts(svg):
    """SVG の <text> が表示する文字列を返す (子要素 <tspan> 等の中身も拾う)。"""
    out = []
    for inner in re.findall(r"<text\b[^>]*>(.*?)</text>", svg, re.S):
        out.append(re.sub(r"<[^>]*>", "", inner).strip())
    return [t for t in out if t]


def load_vols(keys=None):
    import vols
    found = {}
    for m in pkgutil.iter_modules(vols.__path__):
        if m.name.startswith("_"):
            continue
        mod = importlib.import_module(f"vols.{m.name}")
        if hasattr(mod, "VOL"):
            found[mod.VOL["key"]] = mod.VOL
    if keys:
        missing = [k for k in keys if k not in found]
        if missing:
            raise SystemExit(f"そんな vol は無い: {missing} (あるのは {sorted(found)})")
        return [found[k] for k in keys]
    return [found[k] for k in sorted(found)]


# ── main ──────────────────────────────────────────────────────────────
def main(argv):
    html_only = "--html-only" in argv
    fit = "--no-fit" not in argv

    dest_root = None
    if "--desktop" in argv:
        dest_root = desktop_root()
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            raise SystemExit("✗ --out の後ろに置き場所を書くこと")
        dest_root = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    keys = [a for a in argv if not a.startswith("-")]

    global _FONT_CSS
    import fonts
    if "--no-font-fetch" not in argv:
        fonts.fetch()
    _FONT_CSS = fonts.face_css()
    print(fonts.describe())
    vols_ = load_vols(keys or None)
    print(f"刷る対象: {[v['key'] for v in vols_]}"
          f"{' (HTML のみ)' if html_only else ''}")
    if not fit and not html_only:
        print("  ★--no-fit: 版面のはみ出しを測っていない。納品前に外して刷り直すこと")

    import tempfile
    fitdir = tempfile.mkdtemp(prefix="ig-fit-")

    for vol in vols_:
        errs = verify(vol)
        if errs:
            print(f"\n✗ {vol['key']} — ビルド前検査で {len(errs)} 件:")
            for e in errs:
                print("   ", e)
            raise SystemExit(1)

        d = os.path.join(OUT, vol["key"])
        hd = os.path.join(d, "html")
        os.makedirs(hd, exist_ok=True)
        made = []
        for s in vol["slides"]:
            name = f"{vol['key']}_{s['n']:02d}"
            hp = os.path.join(hd, name + ".html")
            html = render_slide(vol, s)
            with open(hp, "w", encoding="utf-8") as f:
                f.write(html)
            if html_only:
                made.append(hp)
                continue
            import chrome
            if fit:
                # ★刷る前に版面に収まるか測る。溢れると overflow:hidden で
                #   黙って切られるか、フッターに重なる。刷ってからでは気づけない。
                # ★測定用の中間物はリポジトリの外に置く。scripts/ の中に置くと
                #   run_all_gates.py の「回したらファイルが変わった」検出に触れる。
                msg = overflow_message(name, overflow_px(html, fitdir, name))
                if msg:
                    raise SystemExit(msg)
            pp = os.path.join(d, name + ".png")
            chrome.shot(hp, pp, T.W, T.H, T.SCALE)
            w, h = chrome.png_size(pp)
            if (w, h) != (T.W * T.SCALE, T.H * T.SCALE):
                raise SystemExit(f"✗ {name}: 実寸が {w}x{h} — "
                                 f"{T.W * T.SCALE}x{T.H * T.SCALE} でなければならない")
            made.append(pp)
            print(f"  {name}.png  {w}x{h}")
        cap = write_caption(vol, d)
        if cap:
            print(f"  投稿文: {os.path.basename(cap)}")
        if not html_only:
            sheet = contact_sheet(vol, made, d)
            if sheet:
                print(f"  一覧: {os.path.basename(sheet)}")
        print(f"✓ {vol['key']}: {len(made)} 枚 → {d}")
        if dest_root:
            dest, copied = deliver(vol, d, dest_root)
            print(f"  配布: {len(copied)} 個 → {dest}")


if __name__ == "__main__":
    main(sys.argv[1:])
