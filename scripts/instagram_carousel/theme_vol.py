#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""4:5 「vol シリーズ」カルーセルの意匠 (色・寸法・CSS・インライン記法)。

★意匠の正典はここ。build_vol.py はこれを組み立てるだけ。
  色や字送りを各 vol モジュールに書き写さないこと (vol ごとにブランドがずれる)。

キャンバスは 1080x1350 (4:5)。撮影時に device-scale-factor=2 で 2160x2700 になる。
Instagram のフィードは 4:5 が最も縦に大きく取れるので、読ませる投稿はこれ。
(既存の build.py は 1:1 = 1080x1080 の別シリーズ。混ぜないこと)
"""
import html as _html

W, H = 1080, 1350
SCALE = 2

# ── 色 ────────────────────────────────────────────────────────────────
AMBER = "#f5c542"   # 主アクセント: CTA・下線・vol バッジ
PINK = "#ec4899"    # 警告・誤答・丸囲み
INDIGO = "#5b63d6"  # A./B. バッジ・ANSWER
GREEN = "#22c55e"   # 正解ボックス
WHITE = "#ffffff"
DIM = "#c7cce6"     # 本文の薄い白
MUTED = "#8b93b8"   # ブランド行・語注・出典
BLUEISH = "#a8b4e8" # チップ文字
PAGE = "#94a3d0"    # ページ番号

# ── 書体 ──────────────────────────────────────────────────────────────
# ★Noto を先頭に置く。理由は 2 つ:
#   ① クラウド/CI の Linux には和文フォントが IPAGothic / WenQuanYi(中国語) しか無く、
#      ヒラギノを先頭にすると中国語字形に落ちる (fonts.py の説明を読むこと)。
#   ② 塾長の Mac と CI で**同じ字幅**になる。英文は white-space:nowrap で組むので、
#      環境ごとに字幅が変わると片方だけ版面からはみ出す。
#   Noto が無い環境でも刷れるよう、後ろに和文フォントのフォールバックを必ず残す。
SANS = ('"Noto Sans JP","Hiragino Sans","Hiragino Kaku Gothic ProN",'
        '"Yu Gothic","IPAGothic","Noto Sans CJK JP",sans-serif')
SERIF = ('"Noto Serif JP","Hiragino Mincho ProN",Georgia,"Times New Roman",'
         '"Liberation Serif","DejaVu Serif",serif')

CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; background:#0a0812; }}
/* ★版面は .stage の固定サイズで決める。position:absolute + inset:0 に頼らないこと。
     headless Chrome のビューポート高は --window-size と一致しないことがあり
     (1350 指定で実測 1263)、絶対配置だと版面が縮んで下がずれる。
     .stage を width/height 固定の通常フローの箱にすれば環境に依存しない。
     背景も .stage に持たせる (body に置くと版面外まで塗りが伸びる)。 */
body {{
  position:relative;
  font-family: {SANS};
  -webkit-font-smoothing: antialiased;
  color:{WHITE};
}}
.stage {{ position:relative; width:{W}px; height:{H}px; overflow:hidden;
  padding:46px 54px 38px; display:flex; flex-direction:column;
  background:
    radial-gradient(760px 520px at 12% 2%, rgba(99,102,241,0.20), transparent 62%),
    radial-gradient(680px 480px at 96% 6%, rgba(236,72,153,0.11), transparent 62%),
    linear-gradient(180deg, #16142e 0%, #100e23 48%, #0a0812 100%); }}

/* ── ヘッダー ── */
.brand {{ font-size:23px; font-weight:700; letter-spacing:.34em; color:{MUTED};
  text-align:center; text-transform:uppercase; }}
.title {{ margin-top:12px; display:flex; align-items:center; justify-content:center; gap:18px; }}
.title .t {{ font-size:46px; font-weight:900; letter-spacing:.01em; }}
.title .vol {{ font-size:25px; font-weight:800; color:{AMBER};
  border:2px solid {AMBER}; border-radius:9px; padding:5px 14px; white-space:nowrap; }}
.rule {{ margin-top:15px; height:3px; border-radius:2px;
  background:linear-gradient(90deg, rgba(163,125,26,0.18) 0%, #b98d20 10%, #e0b23c 50%, #b98d20 90%, rgba(163,125,26,0.18) 100%); }}

/* ── 本体 ── */
.mid {{ flex:1; display:flex; flex-direction:column; min-height:0; }}
.mid.center {{ justify-content:center; }}
.mid.top {{ justify-content:flex-start; padding-top:26px; }}

/* ── フッター ── */
.foot {{ margin-top:18px; padding-top:16px; border-top:2px solid rgba(255,255,255,0.08);
  display:flex; align-items:center; justify-content:space-between; }}
.foot .who {{ font-size:23px; color:{MUTED}; font-weight:600; }}
.foot .pg {{ display:flex; align-items:center; gap:14px; }}
.dots {{ display:flex; gap:10px; }}
.dot {{ width:10px; height:10px; border-radius:50%; background:#3a3a55; }}
.dot.on {{ background:{AMBER}; }}
.pgnum {{ font-size:26px; font-weight:800; color:{PAGE}; }}

/* ── インライン記法 ── */
.c-a {{ color:{AMBER}; }}
.c-p {{ color:{PINK}; }}
.c-w {{ color:{WHITE}; font-weight:900; }}
.c-m {{ color:{MUTED}; }}
.serif {{ font-family:{SERIF}; }}
.u {{ border-bottom:7px solid {AMBER}; padding-bottom:1px; }}
.u.thin {{ border-bottom-width:4px; }}
.warn {{ width:.92em; height:.92em; vertical-align:-.10em; margin:0 .06em 0 .18em; }}
.circ {{ position:relative; display:inline-block; padding:0 .30em; color:{AMBER}; font-weight:700; }}
.circ::before {{ content:""; position:absolute; left:0; right:0; top:-.22em; bottom:-.20em;
  border:4px solid {PINK}; border-radius:50%; transform:rotate(-4deg); }}
.grad {{ background:linear-gradient(120deg,#a5b4fc,#f0abdc);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}

/* ── 部品 ── */
.badge-wrap {{ align-self:center; border:3px dashed rgba(245,197,66,0.55);
  border-radius:19px; padding:8px; }}
.badge {{ background:{AMBER}; color:#191408; font-size:34px; font-weight:900;
  border-radius:12px; padding:12px 38px; letter-spacing:.02em; }}

.chip {{ align-self:center; font-size:30px; font-weight:700; color:{BLUEISH};
  border:2px solid rgba(255,255,255,0.22); border-radius:999px; padding:12px 32px;
  white-space:nowrap; }}

/* ★英文は折り返させない。折り返すと「行ごとの下線」が語の途中で切れて
     意匠が壊れる。幅が足りなければ横にはみ出し、fit 検査が落とす。 */
.quote {{ text-align:center; font-family:{SERIF}; }}
.quote .qline {{ font-size:44px; line-height:1.46; color:{WHITE}; white-space:nowrap; }}
.quote .qline span {{ border-bottom:2.5px solid rgba(255,255,255,0.30); padding-bottom:8px; }}
.quote.sm .qline {{ font-size:40px; }}

.bigq {{ text-align:center; font-size:68px; font-weight:900; line-height:1.26; }}
.h {{ font-size:50px; font-weight:900; line-height:1.30; text-align:center; }}
.h.left {{ text-align:left; }}
.h.sm {{ font-size:44px; }}
.lead {{ text-align:center; font-size:42px; font-weight:800; line-height:1.42; }}
.gloss {{ text-align:center; font-size:30px; color:{MUTED}; font-weight:600; }}
.trans {{ text-align:center; font-size:38px; font-weight:800; line-height:1.5; }}
.eyebrow {{ text-align:center; font-size:28px; font-weight:800; letter-spacing:.30em;
  color:#7c83d6; text-transform:uppercase; }}

.dashbox {{ border:3px dashed rgba(255,255,255,0.26); border-radius:22px;
  padding:36px 32px; text-align:center; font-family:{SERIF};
  font-size:42px; line-height:1.52; white-space:nowrap; }}

.opts {{ display:flex; flex-direction:column; gap:20px; }}
.opt {{ display:flex; gap:24px; align-items:center;
  border:2px solid rgba(255,255,255,0.18); border-radius:18px; padding:24px 26px; }}
.opt .k {{ flex:none; width:66px; height:66px; border-radius:12px; background:{INDIGO};
  display:flex; align-items:center; justify-content:center;
  font-size:32px; font-weight:900; color:#fff; }}
.opt .v {{ font-size:34px; font-weight:700; line-height:1.4; }}

.pill-pink {{ align-self:center; border:3px solid {PINK}; border-radius:999px;
  padding:18px 36px; font-size:32px; font-weight:800; }}
.hint {{ align-self:center; border:3px dashed rgba(245,197,66,0.60); border-radius:14px;
  padding:15px 30px; font-size:30px; font-weight:800; color:{AMBER}; }}

.answer {{ align-self:center; position:relative; display:flex;
  align-items:center; justify-content:center; }}
.answer .ch {{ font-family:{SERIF}; font-size:240px; font-weight:700; color:{AMBER};
  line-height:1.12; padding:0 46px; }}
.answer svg {{ position:absolute; inset:-14% -7%; width:114%; height:128%; }}

.goodbox {{ border:3px solid {GREEN}; background:rgba(34,197,94,0.09); border-radius:16px;
  padding:26px 28px; text-align:center; font-size:34px; font-weight:800; line-height:1.45; }}
.badbox {{ border:3px dashed {PINK}; border-radius:16px; padding:24px 26px;
  text-align:center; font-size:31px; font-weight:700; line-height:1.45; }}

.rulebox {{ border:3px solid {AMBER}; border-radius:16px; padding:0 34px; }}
.rulebox .row {{ padding:20px 0; font-size:40px; font-weight:800; line-height:1.32;
  border-bottom:2px solid rgba(245,197,66,0.32); }}
.rulebox .row:last-child {{ border-bottom:none; }}

.notebar {{ border-left:7px solid {PINK}; background:rgba(236,72,153,0.10);
  padding:24px 28px; font-size:36px; font-weight:800; line-height:1.42; }}
.dashnote {{ border:2px dashed rgba(255,255,255,0.22); border-radius:14px;
  padding:18px 26px; color:#9aa1c8; font-size:29px; line-height:1.52; font-weight:600; }}
/* ★修飾子に .mid は使わない。レイアウト用の .mid (flex 縦積み) と衝突して
     中の span が全部改行される事故になる。修飾子は .ctr のように専用名にする。 */
.dashnote.ctr {{ text-align:center; font-size:31px; color:{DIM}; }}

.fig {{ align-self:center; }}
.source {{ font-size:23px; color:#7a80a4; font-weight:600; }}
.cta {{ align-self:flex-end; border:3px solid {AMBER}; border-radius:999px;
  padding:17px 36px; font-size:34px; font-weight:900; color:{AMBER}; white-space:nowrap; }}

/* 縦の間 (部品どうし) */
.gap-s {{ height:18px; }} .gap-m {{ height:28px; }} .gap-l {{ height:42px; }}
.push {{ flex:1; min-height:12px; }}
"""

# ── インライン記法 ────────────────────────────────────────────────────
# [a]琥珀[/a] [p]ピンク[/p] [w]白太[/w] [u]琥珀下線[/u] [m]薄灰[/m] [s]セリフ[/s]
# [o]丸囲み[/o] (ピンクの楕円で囲む) / [g]グラデ[/g] (build.py 互換) / "\n" は <br>
INLINE = {
    "a": "c-a", "p": "c-p", "w": "c-w", "m": "c-m",
    "s": "serif", "u": "u", "g": "grad", "o": "circ",
}

# ★対で閉じない記法。注意マークは**絵文字を使わず線で描く**。
#   ⚠️ は和文フォントに無い環境で豆腐になる (CLAUDE.md「✓/✗ は文字で置かず線で描く」)。
STANDALONE = {
    "!": (f'<svg class="warn" viewBox="0 0 24 22" fill="none" '
          f'xmlns="http://www.w3.org/2000/svg">'
          f'<path d="M12 2.6 L22.4 20.2 H1.6 Z" stroke="{AMBER}" stroke-width="2.2" '
          f'stroke-linejoin="round"/>'
          f'<path d="M12 8.6 V13.6" stroke="{AMBER}" stroke-width="2.4" '
          f'stroke-linecap="round"/>'
          f'<circle cx="12" cy="16.9" r="1.35" fill="{AMBER}"/></svg>'),
}


class MarkupError(ValueError):
    pass


def check_markup(text):
    """記法の閉じ忘れ・未知タグを列挙して返す (空なら健全)。

    ★ここが gate の土台。閉じ忘れると以降の文字が全部その色になり、
      刷ってから気づく事故になるので、ビルド時にも落とす。
    """
    errs, stack, i = [], [], 0
    while True:
        s = text.find("[", i)
        if s < 0:
            break
        e = text.find("]", s)
        if e < 0:
            errs.append(f"'[' が閉じていない: ...{text[s:s+20]!r}")
            break
        tok = text[s + 1:e]
        i = e + 1
        # ★ASCII だけを記法とみなす。日本語の角括弧 ([注1] / [3点]) は本文なので通す。
        #   逆に [zz] のような ASCII の綴り間違いは未知タグとして落とす。
        if not tok or " " in tok or not tok.isascii():
            continue
        if tok in STANDALONE:
            continue
        if tok.startswith("/"):
            name = tok[1:]
            if name not in INLINE:
                errs.append(f"未知の閉じタグ [/{name}]")
            elif not stack or stack[-1] != name:
                errs.append(f"閉じタグの対応が合わない [/{name}] (開いているのは {stack or 'なし'})")
            else:
                stack.pop()
        elif tok in INLINE:
            stack.append(tok)
        else:
            errs.append(f"未知のタグ [{tok}]")
    if stack:
        errs.append(f"閉じ忘れ: {['[' + t + ']' for t in stack]}")
    return errs


def inline(text):
    """記法つきテキストを HTML に変換する。壊れていれば例外で止める。"""
    errs = check_markup(text)
    if errs:
        raise MarkupError(f"{text!r}: " + " / ".join(errs))
    out = _html.escape(text, quote=False)
    for tok, svg in STANDALONE.items():
        out = out.replace(f"[{tok}]", svg)
    for name, cls in INLINE.items():
        out = out.replace(f"[{name}]", f'<span class="{cls}">').replace(f"[/{name}]", "</span>")
    return out.replace("\n", "<br>")


def plain(text):
    """記法を剥がして素のテキストにする (照合・検査用)。"""
    out = text
    for tok in STANDALONE:
        out = out.replace(f"[{tok}]", "")
    for name in INLINE:
        out = out.replace(f"[{name}]", "").replace(f"[/{name}]", "")
    return out
