#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリリオン @trillion_eng Instagram カルーセル画像ジェネレータ。
16スライド(カルーセルA=8 / B=8)を 1080x1080 のHTMLで組み、
ヘッドレスChromeでPNG(2x=2160px)に描画する。
"""
import os
import sys
import html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chrome  # noqa: E402  撮り方の正典 (build_vol.py と共有)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ★Chrome の在り処と撮り方は chrome.py に寄せた。ここに書き戻さないこと
#   (4:5 の vol シリーズと解像度や下端の扱いが食い違う)。
#   ★out/ の PNG は Mac のヒラギノで刷ったものが git に入っている。
#     別環境で刷り直すと字形が変わって 30MB の差分になるので、
#     刷り直すときは OUT を別の場所に向けること。

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1080px; overflow:hidden; }
body {
  font-family: "Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic",sans-serif;
  -webkit-font-smoothing: antialiased;
  position:relative; color:#eef1ff;
  background:
    radial-gradient(820px 600px at 16% 8%, rgba(129,140,248,0.30), transparent 60%),
    radial-gradient(760px 620px at 92% 96%, rgba(236,72,153,0.26), transparent 60%),
    radial-gradient(700px 560px at 88% 4%, rgba(45,212,191,0.14), transparent 60%),
    linear-gradient(160deg, #0a0e1f 0%, #11132e 52%, #0c0a1d 100%);
}
.stage { position:absolute; inset:0; padding:84px 80px; display:flex; flex-direction:column; }
.brand { display:flex; align-items:center; justify-content:space-between; }
.brand .l { display:flex; align-items:baseline; gap:14px; }
.brand .logo { font-size:38px; font-weight:800; letter-spacing:.01em; }
.brand .logo .em { font-size:34px; }
.brand .sub { font-size:24px; color:#a9b0d6; }
.brand .handle { font-size:27px; color:#c2c7ee; font-weight:600; }
.eyebrow {
  align-self:flex-start; margin-top:40px;
  font-size:30px; font-weight:800; letter-spacing:.04em; color:#fca5a5;
  background:rgba(239,68,68,0.12); border:2px solid rgba(239,68,68,0.42);
  padding:12px 26px; border-radius:999px;
}
.chip {
  align-self:flex-start; margin-top:40px;
  font-size:38px; font-weight:800; color:#fff;
  background:rgba(129,140,248,0.16); border:2px solid rgba(129,140,248,0.5);
  padding:14px 30px; border-radius:18px;
}
.chip.green { color:#bbf7e3; background:rgba(45,212,191,0.16); border-color:rgba(45,212,191,0.55); }
.chip.amber { color:#fde3b3; background:rgba(251,191,36,0.14); border-color:rgba(251,191,36,0.5); }
.chip.time { color:#dfe3ff; background:rgba(255,255,255,0.07); border-color:rgba(255,255,255,0.22); }
.mid { flex:1; display:flex; flex-direction:column; justify-content:center; }
.h { font-size:78px; font-weight:800; line-height:1.18; letter-spacing:.005em; }
.h.sm { font-size:64px; }
.h .grad { background:linear-gradient(120deg,#a5b4fc,#f0abdc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.sub { margin-top:30px; font-size:38px; line-height:1.55; color:#c7cce6; font-weight:500; }
.sub .hl { color:#fff; font-weight:800; }
.note {
  margin-top:34px; align-self:flex-start; font-size:34px; font-weight:700; color:#fcd34d;
  background:rgba(251,191,36,0.10); border-left:6px solid #fcd34d; padding:16px 22px; border-radius:0 12px 12px 0;
}
.items { margin-top:36px; display:flex; flex-direction:column; gap:22px; }
.item { display:flex; gap:22px; align-items:flex-start; font-size:37px; line-height:1.4; font-weight:600; color:#e9ecff; }
.item .mk { flex:none; font-size:40px; font-weight:900; line-height:1.2; width:46px; text-align:center; }
.item .mk.g { color:#34d399; }
.item .mk.a { color:#fbbf24; }
.item b { color:#fff; font-weight:800; }
.steps { margin-top:34px; display:flex; flex-direction:column; gap:20px; }
.step { display:flex; gap:22px; align-items:center; font-size:36px; font-weight:700; color:#e9ecff;
  background:rgba(255,255,255,0.05); border:2px solid rgba(255,255,255,0.12); border-radius:16px; padding:22px 26px; }
.step .n { flex:none; width:58px; height:58px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:32px; font-weight:900; color:#fff; background:linear-gradient(135deg,#818cf8,#ec4899); }
.foot { display:flex; align-items:center; justify-content:space-between; }
.count { font-size:28px; font-weight:800; color:#8b92bd; letter-spacing:.08em; }
.swipe { font-size:30px; font-weight:800; color:#c7cce6; }
.swipe .ar { font-size:34px; }
.cta { align-self:flex-start; margin-top:10px; font-size:40px; font-weight:900; color:#fff;
  background:linear-gradient(135deg,#6366f1,#ec4899); padding:26px 44px; border-radius:20px;
  box-shadow:0 18px 50px rgba(99,102,241,0.45); }
.ctasub { margin-top:26px; font-size:31px; color:#c2c7ee; font-weight:600; }
/* quadrant */
.quad { margin-top:30px; position:relative; width:760px; height:430px; align-self:center; }
.qlabel { position:absolute; font-size:26px; font-weight:800; color:#9aa1cc; }
"""

def esc(s):
    return html.escape(s, quote=False)

def headline(t, sm=False):
    # {grad}...{/grad} -> gradient span
    t = esc(t).replace("&lt;br&gt;", "<br>")
    t = t.replace("[g]", '<span class="grad">').replace("[/g]", "</span>")
    t = t.replace("\n", "<br>")
    cls = "h sm" if sm else "h"
    return f'<div class="{cls}">{t}</div>'

def sub(t):
    t = esc(t).replace("[hl]", '<span class="hl">').replace("[/hl]", "</span>").replace("\n", "<br>")
    return f'<div class="sub">{t}</div>'

def items_html(items):
    rows = []
    for mk, txt in items:
        cls = {"◎": "mk g", "△": "mk a"}.get(mk, "mk")
        t = esc(txt).replace("[b]", "<b>").replace("[/b]", "</b>")
        rows.append(f'<div class="item"><span class="{cls}">{mk}</span><span>{t}</span></div>')
    return '<div class="items">' + "".join(rows) + "</div>"

def steps_html(steps):
    rows = []
    for i, txt in enumerate(steps, 1):
        t = esc(txt).replace("[b]", "<b>").replace("[/b]", "</b>")
        rows.append(f'<div class="step"><span class="n">{i}</span><span>{t}</span></div>')
    return '<div class="steps">' + "".join(rows) + "</div>"

def quadrant_html():
    # x = 続けやすさ(右), y = 伴走の強さ(上). 3 dots.
    def dot(x, y, label, color, big=False):
        r = 20 if big else 13
        ring = f'<circle cx="{x}" cy="{y}" r="{r+10}" fill="none" stroke="{color}" stroke-opacity="0.35" stroke-width="3"/>' if big else ""
        lab_anchor = "start"
        lx = x + 26
        return (f'{ring}<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'
                f'<text x="{lx}" y="{y+9}" font-size="27" font-weight="800" fill="#eef1ff" text-anchor="{lab_anchor}">{label}</text>')
    svg = f'''
    <svg width="760" height="430" viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg">
      <defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M2 1L8 5L2 9" fill="none" stroke="#7b82ad" stroke-width="1.6" stroke-linecap="round"/></marker></defs>
      <line x1="70" y1="370" x2="730" y2="370" stroke="#7b82ad" stroke-width="2.5" marker-end="url(#ah)"/>
      <line x1="70" y1="370" x2="70" y2="30" stroke="#7b82ad" stroke-width="2.5" marker-end="url(#ah)"/>
      <text x="730" y="408" font-size="25" font-weight="800" fill="#9aa1cc" text-anchor="end">続けやすさ →</text>
      <text x="14" y="26" font-size="25" font-weight="800" fill="#9aa1cc" text-anchor="start">↑ 伴走の強さ</text>
      {dot(560, 300, "スタサプ", "#9aa1cc")}
      {dot(180, 95, "武田塾", "#9aa1cc")}
      {dot(580, 110, "トリリオン", "#34d399", big=True)}
    </svg>'''
    return f'<div class="quad">{svg}</div>'

def render(slide):
    car, idx, total = slide["car"], slide["idx"], slide["total"]
    kind = slide["kind"]
    parts = []

    # brand row
    parts.append(
        '<div class="brand"><div class="l">'
        '<span class="logo"><span class="em">🎓</span> トリリオン</span>'
        '<span class="sub">オンライン英語塾</span></div>'
        '<span class="handle">@trillion_eng</span></div>'
    )

    # top chip / eyebrow
    if slide.get("eyebrow"):
        parts.append(f'<div class="eyebrow">{esc(slide["eyebrow"])}</div>')
    if slide.get("chip"):
        ctype = slide.get("chip_type", "")
        parts.append(f'<div class="chip {ctype}">{esc(slide["chip"])}</div>')

    # middle
    mid = []
    if slide.get("headline"):
        mid.append(headline(slide["headline"], slide.get("h_sm", False)))
    if slide.get("sub"):
        mid.append(sub(slide["sub"]))
    if slide.get("items"):
        mid.append(items_html(slide["items"]))
    if slide.get("quadrant"):
        mid.append(quadrant_html())
    if slide.get("steps"):
        mid.append(steps_html(slide["steps"]))
    if slide.get("note"):
        mid.append(f'<div class="note">{esc(slide["note"])}</div>')
    if slide.get("cta"):
        mid.append(f'<div class="cta">{esc(slide["cta"])}</div>')
    if slide.get("ctasub"):
        mid.append(f'<div class="ctasub">{esc(slide["ctasub"])}</div>')
    parts.append('<div class="mid">' + "".join(mid) + "</div>")

    # footer
    swipe = '<span class="swipe">最後まで見る <span class="ar">→</span></span>' if idx < total else '<span class="swipe">保存して見返してね 🔖</span>'
    parts.append(f'<div class="foot"><span class="count">{idx:02d} / {total:02d}　·　カルーセル{car}</span>{swipe}</div>')

    body = '<div class="stage">' + "".join(parts) + "</div>"
    return "<!doctype html><html lang=ja><head><meta charset=utf-8><style>" + CSS + "</style></head><body>" + body + "</body></html>"


SLIDES = [
    # ===== カルーセルA：スタサプ/武田塾と、何が違う？ =====
    dict(car="A", idx=1, total=8, kind="cover",
         eyebrow="英語の塾えらび",
         headline="英語の塾、結局\n[g]どれが正解？[/g]",
         sub="スタサプ・武田塾・トリリオンを\nガチで並べて比べてみた。"),
    dict(car="A", idx=2, total=8, kind="statement",
         headline="教材は揃ってた。\nなのに[g]伸びなかった。[/g]",
         sub="安い映像授業も、記録アプリも入れた。\nでも長文も英作も、点はそのまま。",
         note="差がつくのは “毎日の伴走”。"),
    dict(car="A", idx=3, total=8, kind="compare",
         chip="📺 スタディサプリ", chip_type="",
         items=[("◎", "月¥2,178〜・プロの映像授業が見放題"),
                ("◎", "AIが苦手も分析（網羅性が強い）"),
                ("△", "映像中心ゆえ「観て終わり」になりがちな人も")]),
    dict(car="A", idx=4, total=8, kind="compare",
         chip="📚 武田塾", chip_type="amber",
         items=[("◎", "「授業をしない」＝自学を人が管理・確認テスト"),
                ("◎", "伴走の手厚さは折り紙つき"),
                ("△", "月おおむね4〜6万円・対面校舎が中心"),
                ("△", "全科目向けで、英語“専門”ではない")]),
    dict(car="A", idx=5, total=8, kind="compare",
         chip="🟢 トリリオン", chip_type="green",
         items=[("◎", "元大手予備校講師の “生授業”（集団オンライン）"),
                ("◎", "AIが毎日の弱点を管理してくれるマイページ"),
                ("◎", "英語“専門”・続けやすい価格帯")]),
    dict(car="A", idx=6, total=8, kind="position",
         headline="トリリオンは\n[g]“空白地帯”[/g]にいる", h_sm=True,
         quadrant=True,
         note="“安いが伴走弱い” と “伴走強いが高い” の、あいだ。"),
    dict(car="A", idx=7, total=8, kind="features",
         headline="生授業 × AIが\n[g]毎日の弱点を管理[/g]", h_sm=True,
         items=[("🎯", "弱点TOP3をAIが抽出 → 習得まで出し続ける"),
                ("✏️", "共通テスト型・英文法の隙間ドリル（自動採点）"),
                ("🎴", "FSRSの単語帳が「次に復習すべき日」を表示"),
                ("📈", "週次レポート ＆ AIチューター")]),
    dict(car="A", idx=8, total=8, kind="cta",
         headline="まずは[g]¥1,500[/g]の\n本気体験から。",
         sub="冷やかしお断りの “有料体験（1回）”。\n入塾すれば初月謝から全額差引で、実質無料。",
         cta="プロフィールのリンクから →",
         ctasub="@trillion_eng　·　trillion-ai-juku.com"),

    # ===== カルーセルB：AIで英語の弱点を毎日つぶす、1日ルーティン =====
    dict(car="B", idx=1, total=8, kind="cover",
         eyebrow="1日ルーティン公開",
         headline="「がんばってるのに\n[g]伸びない」[/g]の正体。",
         sub="AI × 英語の1日ルーティンを公開。\nスマホ1つ、スキマ時間でOK。"),
    dict(car="B", idx=2, total=8, kind="statement",
         headline="努力の方向が、\n[g]毎日ズレてた[/g]",
         sub="得意なところばかり解いて安心。\n苦手は“なんとなく”後回し。",
         note="足りないのは量じゃなく “正しい1日”。"),
    dict(car="B", idx=3, total=8, kind="routine",
         chip="☀️ 朝 5分", chip_type="time",
         headline="単語帳が“今日の分”\nだけ出す", h_sm=True,
         sub="FSRS（科学的な間隔反復）で、\n忘れかけの単語を最適日に。次回復習日も表示。"),
    dict(car="B", idx=4, total=8, kind="routine",
         chip="🚃 スキマ 5分", chip_type="time",
         headline="隙間ドリルで\n1問サクッと", h_sm=True,
         sub="共通テスト型・英文法を自動採点＆解説。\n移動中の5分が、そのまま得点力に。"),
    dict(car="B", idx=5, total=8, kind="routine",
         chip="🌙 夜", chip_type="time",
         headline="弱点TOP3を\n習得まで出し続ける", h_sm=True,
         sub="AIが解答データから弱点を抽出。\n同じ穴を狙う “クローズドループ”。"),
    dict(car="B", idx=6, total=8, kind="routine",
         chip="📊 週末", chip_type="time",
         headline="レポートで現在地＋\n“生授業”", h_sm=True,
         sub="進捗を可視化。週の数日は\n元大手予備校講師の生授業で質問解消。"),
    dict(car="B", idx=7, total=8, kind="loop",
         headline="だから、毎日が\n[g]前に進む[/g]", h_sm=True,
         steps=["生授業で “正しいやり方” をインプット",
                "AIが毎日の弱点を出題（ドリル・単語・TOP3）",
                "週次レポートで進捗を可視化 → ①へ戻る"],
         note="英検合格はのべ1,000名以上。"),
    dict(car="B", idx=8, total=8, kind="cta",
         headline="この毎日を、\n[g]¥1,500[/g]で試す。",
         sub="有料体験（1回）だから、本気の人だけ。\n入塾すれば初月謝から全額差引で実質無料。",
         cta="プロフィールのリンクから →",
         ctasub="@trillion_eng　·　trillion-ai-juku.com"),
]


def main():
    htmldir = os.path.join(OUT, "html")
    os.makedirs(htmldir, exist_ok=True)
    pngs = []
    for s in SLIDES:
        name = f"carousel_{s['car']}_{s['idx']:02d}"
        hp = os.path.join(htmldir, name + ".html")
        pp = os.path.join(OUT, name + ".png")
        with open(hp, "w", encoding="utf-8") as f:
            f.write(render(s))
        chrome.shot(hp, pp, 1080, 1080, 2)
        pngs.append(pp)
        print("rendered", os.path.basename(pp))
    print(f"\nDONE: {len(pngs)} PNGs in {OUT}")


if __name__ == "__main__":
    main()
