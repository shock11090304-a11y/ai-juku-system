# -*- coding: utf-8 -*-
"""
トリリオン 中学社会 地理演習  共通ビルダー（単一ソース content → 問題編/解答解説編 の2冊 PDF）

  from build_common import build_book
  build_book(META, POINTS, PART1, PART2, PART3)   # ~/Desktop に 問題編.pdf / 解答解説編.pdf

HTML → Chrome --headless=new --print-to-pdf → fitz でノンブル刻印。
視覚 ID は kaki_koushuu_eng / eng_therules を踏襲（明朝本文＋ゴシック見出し＋紺バンド）。

■ 雨温図
  climate_chart(label, temps[12], precs[12]) → inline SVG
  気温軸 -10〜40℃（左）／降水量軸 0〜500mm（右）を全図で共通にしてあるので
  4 図を並べたときの「形の比較」がそのまま判別根拠になる。

■ 問題型（各 dict は "type" を持つ）
  short {"type":"short","q":"...","ans":"...","exp":"..."}            一問一答（短答）
  mc    {"type":"mc","q":"...","choices":[...],"ans":<0起点idx>,"exp":"..."}
  match {"type":"match","q":"...","slots":["A",..],"pool":["ア ...",..],"ans":["ウ",..],"exp":"..."}
  calc  {"type":"calc","q":"...","ans":"...","work":"式","exp":"..."}  時差など計算
  desc  {"type":"desc","q":"...","ans":"模範解答","limit":40,"keys":[..],"exp":"..."}  字数指定記述

■ ポイント整理（POINTS 要素）
  {"h":"見出し","body":"説明","list":["・...","・..."],"rule":"★一言ルール(任意)"}

■ ★このファイルは**意図的な複製**です（共通化していません）
  冊子ごとに図版部品が本当に違う（回路図/透明半球=理科・雨温図=社会）ため、1本にすると
  どの冊子も使わない部品を抱えることになる。ただし **BASE_CSS と組版の部品は同じ**なので、
  CSS や render() を直したときは**必ず全コピーに反映すること**。
  実際に「群見出しの改ページ修正が1コピーにしか入っておらず、他の冊子で事故が残っていた」
  という取りこぼしが起きている。
  複製先: scripts/{rika_enshu, rika_kagaku, rika_butsuri, shakai_chiri, natsu_tokkun}/build_common.py
"""
import os, html, subprocess
import fitz
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DESKTOP = os.path.expanduser("~/Desktop")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

# ---------------------------------------------------------------- 数式の組版マーク
# ★中学教科書・入試は分数を必ず**組分数**（横線の上に分子・下に分母）で組み、根号は
#   **横線が中身に掛かる**。「(x＋2)／3」「√72」のような1行書きは教科書・入試には無い。
#   データは素の文字列なので、esc() のあとで置換できる目印を使う:
#       [[frac:分子|分母]]   →  組分数
#       [[sqrt:中身]]        →  根号（横線が中身を覆う）
#   ★目印は esc() を通しても壊れない文字（[ ] : |）だけで作ってある。
MARK_FRAC = re.compile(r"\[\[frac:([^|\]]+)\|([^\]]+)\]\]")
MARK_SQRT = re.compile(r"\[\[sqrt:([^\]]+)\]\]")


def mathmark(s):
    """esc() 済みの文字列に対して、数式の目印を実際の組版に変える。"""
    # ★根号を先に展開する。[[frac:5±[[sqrt:17]]|2]] のような入れ子があり、
    #   分数を先に処理すると内側の ] で分子の切り出しが壊れる。
    s = MARK_SQRT.sub(r'<span class="radsign">&#8730;</span><span class="rad">\1</span>', s)
    s = MARK_FRAC.sub(
        r'<span class="frac"><span class="num">\1</span>'
        r'<span class="den">\2</span></span>', s)
    return s


_escape = lambda s: html.escape(str(s), quote=False)
# ★esc() 自体に数式マークの展開を通す。個々の描画関数に足して回ると必ず抜けが出る
#   （設問文では組分数になるのに選択肢では [[frac:…]] が生で出る、という事故）。
esc = lambda s: mathmark(_escape(s))
KANA = ["ア", "イ", "ウ", "エ", "オ", "カ", "キ", "ク"]
CIRCLE = ["①", "②", "③", "④", "⑤", "⑥"]

# ---------------------------------------------------------------- 雨温図
T_MIN, T_MAX = -10, 40        # 気温軸（℃）
P_MAX = 500                   # 降水量軸（mm）
CW, CH = 208, 152             # SVG 全体
PL, PR, PT, PB = 30, 176, 14, 112   # プロット領域


def _ty(t):
    return PB - (t - T_MIN) / (T_MAX - T_MIN) * (PB - PT)


def _py(p):
    return PB - (min(p, P_MAX) / P_MAX) * (PB - PT)


def climate_chart(label, temps, precs, caption=""):
    """雨温図（棒＝降水量／折れ線＝気温）を inline SVG で返す。

    caption を省略すると、年平均気温・年降水量を月別値から自動計算して刻む
    （手で書くと本文データとドリフトするため、必ずここで計算する）。"""
    assert len(temps) == 12 and len(precs) == 12, "雨温図は12か月分必要"
    if not caption:
        caption = f"年平均気温 {sum(temps)/12:.1f}℃　／　年降水量 {sum(precs):.0f}mm"
    step = (PR - PL) / 12.0
    s = [f'<svg class="cc" viewBox="0 0 {CW} {CH}" xmlns="http://www.w3.org/2000/svg">']
    # 目盛（気温 10℃ごと／降水量 100mmごと＝同じ横線を共有）
    for i in range(6):
        t = T_MIN + i * 10          # -10,0,10,20,30,40
        y = _ty(t)
        s.append(f'<line x1="{PL}" y1="{y:.1f}" x2="{PR}" y2="{y:.1f}" '
                 f'stroke="#d7dee8" stroke-width="0.6"/>')
        s.append(f'<text x="{PL-3:.0f}" y="{y+2.6:.1f}" class="ax r">{t}</text>')
        s.append(f'<text x="{PR+3:.0f}" y="{y+2.6:.1f}" class="ax">{i*100}</text>')
    # 0℃ ライン（氷点を強調＝亜寒帯の判別根拠）
    y0 = _ty(0)
    s.append(f'<line x1="{PL}" y1="{y0:.1f}" x2="{PR}" y2="{y0:.1f}" '
             f'stroke="#94a3b8" stroke-width="1.1" stroke-dasharray="2.5 1.5"/>')
    # 降水量バー
    for i, p in enumerate(precs):
        x = PL + step * i + step * 0.18
        w = step * 0.64
        y = _py(p)
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{PB-y:.1f}" '
                 f'fill="#7ea6d8" stroke="#3d6da8" stroke-width="0.4"/>')
    # 気温折れ線
    pts = " ".join(f'{PL+step*i+step/2:.1f},{_ty(t):.1f}' for i, t in enumerate(temps))
    s.append(f'<polyline points="{pts}" fill="none" stroke="#c2410c" stroke-width="1.5" '
             f'stroke-linejoin="round"/>')
    for i, t in enumerate(temps):
        s.append(f'<circle cx="{PL+step*i+step/2:.1f}" cy="{_ty(t):.1f}" r="1.5" '
                 f'fill="#fff" stroke="#c2410c" stroke-width="1"/>')
    # 枠と月目盛
    s.append(f'<rect x="{PL}" y="{PT}" width="{PR-PL}" height="{PB-PT}" fill="none" '
             f'stroke="#64748b" stroke-width="0.9"/>')
    for m in (1, 4, 7, 10, 12):
        x = PL + step * (m - 1) + step / 2
        s.append(f'<line x1="{x:.1f}" y1="{PB}" x2="{x:.1f}" y2="{PB+2.5:.1f}" '
                 f'stroke="#64748b" stroke-width="0.7"/>')
        s.append(f'<text x="{x:.1f}" y="{PB+9:.1f}" class="ax c">{m}</text>')
    s.append(f'<text x="{(PL+PR)/2:.0f}" y="{PB+18:.0f}" class="ax c">月</text>')
    s.append(f'<text x="{PL-3:.0f}" y="{PT-4:.0f}" class="axu r">気温 ℃</text>')
    s.append(f'<text x="{PR+3:.0f}" y="{PT-4:.0f}" class="axu">降水量 mm</text>')
    s.append(f'<text x="{PL+2:.0f}" y="{CH-4:.0f}" class="cclabel">{esc(label)}</text>')
    s.append(f'<text x="{PR:.0f}" y="{CH-4:.0f}" class="ccnote">{esc(caption)}</text>')
    s.append('</svg>')
    return "".join(s)


def chart_grid(items):
    """items = [(label, temps, precs, caption), ...] を 2 列で並べる。"""
    cells = "".join(f'<div class="ccell">{climate_chart(l, t, p, c)}</div>'
                    for l, t, p, c in items)
    return f'<div class="cgrid">{cells}</div>'


# ---------------------------------------------------------------- 表・原稿マス
def stat_table(caption, headers, rows, note="", aligns=None):
    aligns = aligns or ["l"] + ["r"] * (len(headers) - 1)
    h = ['<div class="tbl">']
    if caption:
        h.append(f'<div class="tcap">{esc(caption)}</div>')
    h.append('<table class="stat"><tr>' +
             "".join(f'<th>{esc(x)}</th>' for x in headers) + '</tr>')
    for r in rows:
        h.append('<tr>' + "".join(f'<td class="{aligns[i]}">{esc(v)}</td>'
                                  for i, v in enumerate(r)) + '</tr>')
    h.append('</table>')
    if note:
        h.append(f'<div class="tnote">{esc(note)}</div>')
    h.append('</div>')
    return "".join(h)


def genko(limit, cols=20):
    """字数指定記述用のマス目。マスの数を limit 字ぴったりにする
    （多めに敷くと「何字まで書けるのか」が解答欄から読み取れなくなるため）。"""
    cells = "".join('<i></i>' for _ in range(limit))
    return (f'<div class="genko" style="grid-template-columns:repeat({cols},1fr)">'
            f'{cells}</div>')


# ---------------------------------------------------------------- CSS
BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 12mm 15mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:#1a1a1a; font-size:10.2pt;
  line-height:1.62; margin:0; font-variant-numeric: lining-nums; font-feature-settings:"lnum" 1; }
.gothic,h1,h2,h3,.band,.qno,.secttl,.partdiv,.bigno,.plabel,.pbh,.tier,.foot,.tcap,.ax,.axu,.cclabel,.slotlbl
  { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }

/* ヘッダバンド */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:10px 15px;
  border-radius:9px; display:flex; justify-content:space-between; align-items:center; }
/* ★.r に幅を渡さないと flex に押しつぶされ、右上が「中1〜中／3）」のように
   語中で改行する（実測で発生）。.r は縮めない・折り返さない、.l に残りを渡す。 */
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; flex:1 1 auto; min-width:0; }
/* ★サブタイトルは必ず2行目に置く。1行に流すと、冊子名の長さ次第で
   「…電流・運/動」のように1文字だけあふれる（実測）。号ごとに字数を調整するのは
   壊れやすいので、レイアウト側で長さに依存しない形にする。 */
.band .l small { display:block; font-weight:600; font-size:9.4pt; opacity:.92;
  margin:2px 0 0; }
.band .r { text-align:right; font-size:8.8pt; line-height:1.45; flex:0 0 auto;
  white-space:nowrap; padding-left:14px; }
.band .r b { font-size:12pt; }

.intro { border:1px solid #cbd5e1; border-radius:8px; padding:8px 13px; margin:9px 0 4px;
  font-size:9.4pt; line-height:1.7; color:#334155; }
.intro b { color:#0f172a; }
.metarow { display:flex; gap:9px; margin:8px 0 6px; font-size:9.3pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 132px; text-align:center; }

/* 部 見出し */
/* ★帯の中で割れると、前ページ末が「文字の無い色ベタ」・次ページ頭が
   「タイトルの無い色帯」になり刷り損ないに見える（物理p5末・化学解答編p9末で実測）。 */
.partdiv { background:#1e3a8a; color:#fff; border-radius:8px; padding:10px 15px; margin:15px 0 6px;
  page-break-before:always; page-break-after:avoid;
  break-inside:avoid; page-break-inside:avoid; }
.partdiv.first { page-break-before:auto; margin-top:10px; }
.partdiv .pt1 { font-size:14.5pt; font-weight:700; }
.partdiv .pt2 { font-size:9.2pt; opacity:.93; margin-top:3px; }

/* ポイント整理 */
.plabel { font-size:11.5pt; font-weight:700; color:#0f172a; margin:10px 0 5px;
  border-left:6px solid #1e3a8a; padding-left:9px; page-break-after:avoid; }
.pbox { border:1px solid #dbe3ef; border-left:4px solid #2563eb; border-radius:7px;
  padding:7px 12px; margin:0 0 7px; page-break-inside:avoid; }
.pbh { font-weight:700; font-size:10.2pt; color:#1e3a8a; margin-bottom:2px; }
.pbody { font-size:9.5pt; line-height:1.62; color:#1f2937; }
.plist { margin:3px 0 0; font-size:9.4pt; color:#1f2937; line-height:1.6; }
.plist div { margin:1px 0; }
.prule { margin-top:4px; font-size:9.2pt; color:#b91c1c; font-weight:700; }

/* 大問 */
.big { margin:8px 0 0; page-break-inside:auto; }
.bighd { display:flex; align-items:baseline; gap:9px; border-bottom:2.2px solid #1e3a8a;
  padding-bottom:4px; margin:9px 0 5px; page-break-after:avoid; }
.bigno { background:#0f172a; color:#fff; border-radius:6px; padding:2px 11px; font-size:10.5pt;
  font-weight:700; white-space:nowrap; }
.bigttl { font-size:12.5pt; font-weight:700; color:#0f172a; }
.bigpt { margin-left:auto; font-size:8.6pt; color:#dc2626; font-weight:700; white-space:nowrap; }
/* ★導入文が語中で改ページ分断され、水色の箱が上辺なし/下辺なしに割れる事故があった。
   実験条件を読んだページと図のページが分かれると設問が解けない。 */
.instr { font-size:9.2pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px;
  border-radius:4px; margin:5px 0 8px; color:#334155; line-height:1.6;
  break-inside:avoid; page-break-inside:avoid; }
.glue { break-inside:avoid; page-break-inside:avoid; }

/* 一問一答 */
/* ★display:inline-block だと Chrome は page-break-after:avoid を無視する。
   群見出しがページ最下部に独りで残り、その群の1問目だけが次ページ頭に飛ぶ事故が
   実際に起きた（物理の解答解説編 p5）。ブロックレベルにして宣言を効かせる。 */
.qagrp { font-size:10.3pt; font-weight:700; color:#fff; background:#047857; border-radius:5px;
  padding:2px 12px; margin:11px 0 5px; display:block; width:fit-content;
  break-after:avoid; page-break-after:avoid; }
/* ★1行あたり0.4pt詰める。40問で16pt浮き、第1部の最後の1問が次ページへこぼれて
   「1問だけの8%ページ」になるのを防ぐ（第2部が強制改ページなので、こぼれた1問が
   まるまる1ページを占めてしまう）。 */
.qarow { display:flex; align-items:baseline; gap:7px; padding:2.0px 0; font-size:9.7pt;
  border-bottom:1px dotted #dbe3ef; page-break-inside:avoid; }
.qarow .n { flex:0 0 30px; color:#1e3a8a; font-weight:700;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:9pt; }
.qarow .t { flex:1; }
/* ★解答欄118px＝31mmでは「フェノールフタレイン液」(11字)が1字2.8mmになり書けず、140px＝37mm
   （11字なら1字3.4mm）に広げた。理想は152px＝40mm だが、152pxにすると設問文の折返しが増えて
   地理No.02が7→8ページになったため140pxで妥協している。
   ★11字を超える答えを第1部に入れないこと（入れるならここを広げてページ数を再確認する）。 */
.qarow .b { flex:0 0 140px; border-bottom:1.2px solid #94a3b8; height:14px; }

/* 設問 */
.q { margin:0 0 5px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:7px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:8.8pt;
  font-weight:700; white-space:nowrap; }
.q .stem { flex:1; font-size:9.9pt; }
.q .choices div { margin:2px 0 1px 12px; font-size:9.6pt; }
.qpt { flex:0 0 auto; color:#dc2626; font-size:8.2pt; font-weight:700; white-space:nowrap;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.pool { display:flex; flex-wrap:wrap; gap:5px 12px; margin:4px 0 5px 12px; font-size:9.5pt; }
.pool span { white-space:nowrap; }
.slots { display:flex; gap:9px; margin:5px 0 2px 12px; }
.slots .s { border:1px solid #94a3b8; border-radius:5px; min-width:56px; text-align:center; }
.slotlbl { background:#eef2ff; color:#1e3a8a; font-size:8.4pt; font-weight:700;
  border-bottom:1px solid #cbd5e1; padding:1px 0; }
.slots .s .in { height:19px; }
.ansline { margin:4px 0 0 12px; display:flex; align-items:baseline; gap:6px; font-size:9.4pt; }
.ansline .bl { flex:0 0 190px; border-bottom:1.2px solid #94a3b8; height:15px; }
.ansline .bl.w { flex:0 0 300px; }
.unit { color:#475569; font-size:9pt; }

/* 記述マス目 */
/* マス目は中学生が「排」「済」「較」を書ける大きさが要る（旧 5.7×4.8mm は小さすぎた）。
   幅 560px/20列 ≒ 7.4mm、高さ 26px ≒ 6.9mm でほぼ正方形。 */
.genko { display:grid; gap:0; margin:4px 0 1px 12px; width:calc(100% - 12px); max-width:560px;
  border-left:1px solid #94a3b8; border-top:1px solid #94a3b8; page-break-inside:avoid; }
.genko i { display:block; height:24px; border-right:1px solid #94a3b8;
  border-bottom:1px solid #94a3b8; }
.lim { color:#dc2626; font-size:8.8pt; font-weight:700; margin-left:2px; white-space:nowrap;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }

/* 雨温図 */
.cgrid { display:flex; flex-wrap:wrap; gap:6px 8px; margin:6px 0 8px; page-break-inside:avoid; }
.ccell { flex:0 0 calc(50% - 4px); border:1px solid #cbd5e1; border-radius:6px; padding:3px 2px 1px; }
svg.cc { width:100%; height:auto; display:block; }
svg.cc text.ax { font-size:5.6px; fill:#475569; }
svg.cc text.axu { font-size:5.2px; fill:#64748b; }
svg.cc text.r { text-anchor:end; }
svg.cc text.c { text-anchor:middle; }
svg.cc text.e { text-anchor:end; }
svg.cc text.cclabel { font-size:9px; font-weight:700; fill:#0f172a; }
svg.cc text.ccnote { font-size:6.2px; fill:#334155; text-anchor:end;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }

/* 統計表 */
.tbl { margin:6px 0 8px; page-break-inside:avoid; }
.tcap { font-size:9.3pt; font-weight:700; color:#0f172a; margin-bottom:3px; }
table.stat { width:100%; border-collapse:collapse; font-size:9.2pt; }
table.stat th, table.stat td { border:1px solid #cbd5e1; padding:3px 7px; }
table.stat th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
  text-align:center; font-size:8.9pt; }
table.stat td.r { text-align:right; } table.stat td.c { text-align:center; }
.tnote { font-size:8.2pt; color:#64748b; margin-top:2px; }

/* 解答解説編 */
.secttl { font-size:12.5pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a;
  padding:3px 0 3px 10px; margin:0 0 8px; page-break-after:avoid; }
.secttl .en2 { font-size:8.8pt; color:#64748b; font-weight:600; margin-left:8px; }
table.ans { width:100%; border-collapse:collapse; font-size:8.9pt; margin:2px 0 8px; }
table.ans.fixed { table-layout:fixed; margin:0 0 -1px; }   /* 語中改行を防ぐ等幅レイアウト */
table.ans.fixed th { width:44px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:3px 4px; text-align:center;
  vertical-align:middle; word-break:keep-all; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif;
  white-space:nowrap; font-size:8.4pt; }
table.ans td.a { font-weight:700; color:#1e3a8a; }
.ex { border:1px solid #e2e8f0; border-left:4px solid #1e3a8a; border-radius:6px; padding:6px 11px;
  margin:5px 0; page-break-inside:avoid; }
.ex .exh { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; flex-wrap:wrap; }
.ex .exno { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; color:#0f172a;
  white-space:nowrap; }
.ex .exa { font-weight:700; color:#1e3a8a; }
.ex .exbody { font-size:9.3pt; color:#1f2937; line-height:1.6; margin-top:2px; }
.ex .work { font-size:9.2pt; background:#f8fafc; border-radius:4px; padding:4px 9px; margin:3px 0;
  color:#0f172a; }
.keys { font-size:9pt; background:#fff7ed; border-radius:4px; padding:4px 9px; margin-top:4px;
  color:#7c2d12; }
.keys b { color:#9a3412; }
.tag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700; border-radius:4px;
  padding:0 7px; font-size:8.2pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }

/* 組分数と根号（中学教科書・入試の組み方） */
.frac { display:inline-block; vertical-align:-0.42em; text-align:center; margin:0 2px;
  line-height:1.15; }
.frac .num { display:block; border-bottom:1.1px solid currentColor; padding:0 3px; }
.frac .den { display:block; padding:0 3px; }
.radsign { margin-right:-1px; }
.rad { border-top:1.1px solid currentColor; padding:0 2px 0 1px; }

/* 奥付だけが最終ページに独りで飛ぶのを防ぐ（break-before:avoid ＋ 余白を詰める） */
.foot { text-align:center; color:#64748b; font-size:8.1pt; margin-top:7px; padding-top:4px;
  border-top:1px solid #e2e8f0; page-break-inside:avoid;
  break-before:avoid; page-break-before:avoid; }
"""


# ---------------------------------------------------------------- 部品
def band(M, sub):
    return (f'<div class="band"><div class="l">{esc(M["title"])}'
            f'<small>{esc(M["subtitle"])}</small></div>'
            f'<div class="r"><b>{esc(sub)}</b><br>{esc(M["level"])}</div></div>')


def meta_row(M):
    return ('<div class="metarow">'
            f'<div class="cell">氏名　　　　　　　　　　　　　　　</div>'
            f'<div class="cell">実施日　　　　月　　　日</div>'
            f'<div class="cell score">得点　　　／{M["total"]}点</div></div>')


def foot(M, label):
    return (f'<div class="foot">{esc(M["title"])}　{esc(label)}　'
            f'／　{esc(M["org"])}　{esc(M["stat_note"])}</div>')


def pointbox(POINTS):
    h = ['<div class="plabel">この回のポイント整理（解き終わってから読む）</div>']
    for p in POINTS:
        b = [f'<div class="pbox"><div class="pbh">{esc(p["h"])}</div>']
        if p.get("body"):
            b.append(f'<div class="pbody">{esc(p["body"])}</div>')
        if p.get("list"):
            b.append('<div class="plist">' +
                     "".join(f'<div>{esc(x)}</div>' for x in p["list"]) + '</div>')
        if p.get("rule"):
            b.append(f'<div class="prule">★ {esc(p["rule"])}</div>')
        b.append('</div>')
        h.append("".join(b))
    return "".join(h)


def _q_body(q):
    """設問1つ分の解答欄（問題編）。"""
    t = q["type"]
    if t == "mc":
        return ('<div class="choices">' +
                "".join(f'<div>{CIRCLE[i]}　{esc(c)}</div>' for i, c in enumerate(q["choices"])) +
                '</div><div class="ansline"><span>答</span><span class="bl"></span></div>')
    if t == "match":
        pool = ('<div class="pool">' +
                "".join(f'<span>{esc(x)}</span>' for x in q["pool"]) + '</div>')
        slots = ('<div class="slots">' +
                 "".join(f'<div class="s"><div class="slotlbl">{esc(s)}</div>'
                         f'<div class="in"></div></div>' for s in q["slots"]) + '</div>')
        return pool + slots
    if t == "calc":
        return ('<div class="ansline"><span>答</span><span class="bl w"></span>'
                f'<span class="unit">{esc(q.get("unit",""))}</span></div>')
    if t == "desc":
        return genko(q["limit"], q.get("cols", 20))
    return '<div class="ansline"><span>答</span><span class="bl"></span></div>'


def q_problem(q, no):
    # 字数制限は設問文の末尾に置く（独立した行にすると記述1問につき1行むだになる）
    lim = f'<span class="lim">（{q["limit"]}字以内）</span>' if q["type"] == "desc" else ""
    # 小問ごとの配点。無いと大問の配点しか分からず 100 点満点を自己採点できない。
    pt = f'<span class="qpt">{q["pt"]}点</span>' if q.get("pt") else ""
    return (f'<div class="q"><div class="h"><span class="qno">{esc(no)}</span>'
            f'<span class="stem">{esc(q["q"])}{lim}</span>{pt}</div>{_q_body(q)}</div>')


def big_block(b):
    """大問1つ分（問題編）。"""
    h = [f'<div class="big"><div class="bighd"><span class="bigno">{esc(b["no"])}</span>'
         f'<span class="bigttl">{esc(b["title"])}</span>'
         f'<span class="bigpt">配点 {b["point"]}点</span></div>']
    if b.get("intro"):
        h.append(f'<div class="instr">{esc(b["intro"])}</div>')
    for blk in b.get("figs", []):
        h.append(blk)
    for i, q in enumerate(b["qs"], start=1):
        h.append(q_problem(q, f'問{i}'))
    h.append('</div>')
    return "".join(h)


def qa_rows(items, start=1):
    h = []
    for i, it in enumerate(items, start=start):
        h.append(f'<div class="qarow"><span class="n">({i})</span>'
                 f'<span class="t">{esc(it["q"])}</span><span class="b"></span></div>')
    return "".join(h), start + len(items)


# ---------------------------------------------------------------- 問題編
def build_mondai(M, POINTS, PART1, PART2, PART3):
    h = [band(M, "問題編"), meta_row(M)]
    h.append(f'<div class="intro"><b>この演習の進め方：</b>{esc(M["intro"])}</div>')
    # ★ポイント整理は問題編に載せない。島名・数値・方位が第1部の解答そのものになり、
    #   40問中15問が知識ゼロで取れてしまうため（解答解説編の巻頭へ移動）。
    h.append('<div class="partdiv first"><div class="pt1">第1部　一問一答（基礎用語の確認）</div>'
             f'<div class="pt2">{esc(M["part1_lead"])}</div></div>')
    n = 1
    for g in PART1:
        rows, n = qa_rows(g["items"], n)
        h.append(f'<div class="qagrp">{esc(g["group"])}</div>{rows}')

    h.append('<div class="partdiv"><div class="pt1">第2部　資料の読み取り</div>'
             f'<div class="pt2">{esc(M["part2_lead"])}</div></div>')
    for b in PART2:
        h.append(big_block(b))

    # 第3部は改ページを強制しない（強制すると大問4の残り数問だけの空白ページが出る）
    h.append('<div class="partdiv first"><div class="pt1">第3部　短文記述</div>'
             f'<div class="pt2">{esc(M["part3_lead"])}</div></div>')
    for i, q in enumerate(PART3, start=1):
        h.append(q_problem(q, f'記述{i}'))

    h.append(foot(M, "問題編"))
    return "\n".join(h)


# ---------------------------------------------------------------- 解答解説編
def _fmt_ans(q):
    t = q["type"]
    if t == "mc":
        return CIRCLE[q["ans"]] + "　" + esc(q["choices"][q["ans"]])
    if t == "match":
        # ★和文の中なので全角の＝を使う。半角にすると、冊子の他の式（＝で統一）と
        #   見た目がそろわず、解答一覧だけ書体が違って見える。
        return "／".join(f'{s}＝{a}' for s, a in zip(q["slots"], q["ans"]))
    return esc(q["ans"])


def qa_key_table(PART1, cols=5):
    """一問一答の解答一覧。
    ★1つの table に全ブロックを入れると列幅が共有され、最長語（例:ＡＳＥＡＮ…）が1列を占有して
      他が「サンベル／ト」のように語中改行する。ブロックごとに table を分け、table-layout:fixed で
      等幅にする。列数も 8→5 に減らして1セルの幅を確保する。"""
    rows = []
    n = 1
    for g in PART1:
        for it in g["items"]:
            rows.append((f'({n})', it["ans"]))
            n += 1
    out = []
    for i in range(0, len(rows), cols):
        ch = rows[i:i + cols]
        pad = cols - len(ch)
        out.append('<table class="ans fixed">')
        out.append('<tr><th>番号</th>' + "".join(f'<td>{esc(r[0])}</td>' for r in ch)
                   + '<td></td>' * pad + '</tr>')
        out.append('<tr><th>解答</th>' + "".join(f'<td class="a">{esc(r[1])}</td>' for r in ch)
                   + '<td></td>' * pad + '</tr>')
        out.append('</table>')
    return "".join(out)


def build_kaisetsu(M, POINTS, PART1, PART2, PART3):
    h = [band(M, "解答・解説編")]
    h.append(f'<div class="intro"><b>使い方：</b>{esc(M["kaisetsu_intro"])}</div>')
    h.append(pointbox(POINTS))   # ★問題編ではなくこちらに載せる（問題編に置くと解答漏洩になる）

    # 第1部
    h.append('<div class="partdiv"><div class="pt1">第1部　一問一答　解答</div>'
             '<div class="pt2">まず解答一覧で丸つけ→まちがえた番号だけ下の解説を読む。</div></div>')
    h.append(qa_key_table(PART1))
    n = 1
    for g in PART1:
        h.append(f'<div class="qagrp">{esc(g["group"])}　解説</div>')
        for it in g["items"]:
            if it.get("exp"):
                h.append(f'<div class="ex"><div class="exh"><span class="exno">({n})</span>'
                         f'<span class="exa">{esc(it["ans"])}</span></div>'
                         f'<div class="exbody">{esc(it["exp"])}</div></div>')
            n += 1

    # 第2部（改ページ強制なし：一問一答の解説が数個だけ残ったページの下が空になるため）
    h.append('<div class="partdiv first"><div class="pt1">第2部　資料の読み取り　解答・解説</div>'
             '<div class="pt2">資料問題は「答え」より「どこを見て決めたか」を確認すること。</div></div>')
    for b in PART2:
        h.append(f'<div class="secttl">{esc(b["no"])}　{esc(b["title"])}'
                 f'<span class="en2">配点 {b["point"]}点</span></div>')
        for i, q in enumerate(b["qs"], start=1):
            body = [f'<div class="ex"><div class="exh"><span class="exno">問{i}</span>'
                    f'<span class="exa">{_fmt_ans(q)}</span>']
            if q["type"] == "desc":
                body.append(f'<span class="tag">{q["limit"]}字以内</span>')
            body.append('</div>')
            if q.get("work"):
                body.append(f'<div class="work">{esc(q["work"])}</div>')
            body.append(f'<div class="exbody">{esc(q["exp"])}</div>')
            if q.get("keys"):
                body.append('<div class="keys"><b>採点のポイント（この要素が入っていれば○）：</b>' +
                            "／".join(esc(k) for k in q["keys"]) + '</div>')
            body.append('</div>')
            h.append("".join(body))

    # 第3部（同上）
    h.append('<div class="partdiv first"><div class="pt1">第3部　短文記述　解答・解説</div>'
             '<div class="pt2">記述は一字一句同じでなくてよい。採点のポイントが入っているかで丸つけする。</div></div>')
    for i, q in enumerate(PART3, start=1):
        h.append(f'<div class="ex"><div class="exh"><span class="exno">記述{i}</span>'
                 f'<span class="tag">{q["limit"]}字以内</span></div>'
                 f'<div class="work">{esc(q["ans"])}（{len(q["ans"])}字）</div>'
                 f'<div class="exbody">{esc(q["exp"])}</div>'
                 '<div class="keys"><b>採点のポイント（この要素が入っていれば○）：</b>' +
                 "／".join(esc(k) for k in q["keys"]) + '</div></div>')

    h.append(foot(M, "解答・解説編"))
    return "\n".join(h)


# ---------------------------------------------------------------- 出力
def doc(title, body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{BASE_CSS}</style></head><body>{body}</body></html>')


def render(body, out_path, foot_label):
    tmp = os.path.join(HERE, "_" + os.path.basename(out_path).replace(".pdf", ".html"))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc(foot_label, body))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={out_path}", "file://" + tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = fitz.open(out_path)
    _font = fitz.Font(fontfile=FONT_PATH)
    for i, page in enumerate(d):
        n = str(i + 1)
        tw = _font.text_length(n, fontsize=9)
        cx = page.rect.width / 2
        # ★柱（書名）はページ中央のノンブルに届く長さになりうる。実際に化学・物理の
        #   解答解説編で柱が x=311 まで伸び、x=295 のノンブルに16pt重なって
        #   ページ番号が読めなくなっていた。書名の長さは号ごとに変わるので、
        #   刻印する側で「届かない長さまで詰める」のが唯一の恒久策。
        avail = cx - tw / 2 - 8 - 36        # 左マージン36 〜 ノンブルの手前8pt
        label = foot_label
        if _font.text_length(label, fontsize=7.2) > avail:
            while label and _font.text_length(label + "…", fontsize=7.2) > avail:
                label = label[:-1]
            label += "…"
        page.insert_text((cx - tw / 2, page.rect.height - 20), n,
                         fontfile=FONT_PATH, fontname="AU", fontsize=9, color=(0.45, 0.45, 0.45))
        page.insert_text((36, page.rect.height - 20), label,
                         fontfile=FONT_PATH, fontname="AU", fontsize=7.2, color=(0.55, 0.55, 0.55))
    d.subset_fonts()
    tmp2 = out_path + ".tmp"
    d.save(tmp2, garbage=4, deflate=True, clean=True)
    d.close()
    os.replace(tmp2, out_path)
    d = fitz.open(out_path)
    pc = d.page_count
    d.close()
    print(f"WROTE {out_path} | pages: {pc}")
    return pc


def build_book(M, POINTS, PART1, PART2, PART3, outdir=DESKTOP):
    base = f'トリリオン_中学社会_地理演習_{M["no"]}'
    q_pdf = os.path.join(outdir, f'{base}_問題編.pdf')
    a_pdf = os.path.join(outdir, f'{base}_解答解説編.pdf')
    fl = f'中学社会 地理演習 {M["subtitle"]}'   # subtitle に既に No.xx が入っている
    render(build_mondai(M, POINTS, PART1, PART2, PART3), q_pdf, fl + " 問題編")
    render(build_kaisetsu(M, POINTS, PART1, PART2, PART3), a_pdf, fl + " 解答・解説編")
    return q_pdf, a_pdf
