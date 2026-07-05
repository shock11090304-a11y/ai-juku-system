#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
トリリオン @trillion_ai Instagram カルーセル生成器 (MARCH英文シリーズ)。
「MARCHの英文はこう読む vol.02 / クジラ構文 no more A than B」6スライドを
1080x1350 のHTMLで組み、ヘッドレスChromiumで PNG(2x=2160x2700) に描画する。

使い方: python3 build.py   →  out/march_01.png ... march_06.png
"""
import os
import subprocess
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

# ヘッドレスChromium(この環境の Playwright 同梱バイナリ / 一般環境の chromium も探す)
CHROME_CANDIDATES = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    shutil.which("chromium"),
    shutil.which("chromium-browser"),
    shutil.which("google-chrome"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
CHROME = next((c for c in CHROME_CANDIDATES if c and os.path.exists(c)), None)

W, H = 1080, 1350
TITLE = "MARCHの英文はこう読む"
VOL = "vol.02"
HANDLE = "@trillion_ai"
SITE = "trillion-ai-juku.com"
SOURCE = "英文出典: L.S.Park『A Long Walk to Water』(2010) ・ 難関私大 長文空所補充"

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:1080px; height:1350px; overflow:hidden; background:#0b0916; }
body {
  font-family:"Noto Sans CJK JP","Noto Sans JP",sans-serif;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  color:#f4f6ff;
}
.serif { font-family:"Liberation Serif","Times New Roman",serif; }
.stage { position:absolute; inset:0; overflow:hidden;
  padding:54px 64px 42px; display:flex; flex-direction:column;
  background:
    radial-gradient(760px 520px at 12% 6%, rgba(129,140,248,0.20), transparent 62%),
    radial-gradient(720px 560px at 94% 98%, rgba(236,72,153,0.18), transparent 60%),
    radial-gradient(680px 520px at 90% 2%, rgba(45,212,191,0.10), transparent 60%),
    linear-gradient(158deg, #0a0c1a 0%, #10122b 54%, #0b0916 100%); }

/* ---------- header ---------- */
.eyebrow { text-align:center; font-size:26px; font-weight:700; letter-spacing:.34em;
  color:#8b93bd; padding-left:.34em; }
.title-row { display:flex; align-items:center; justify-content:center; gap:20px; margin-top:14px; }
.title { font-size:52px; font-weight:900; color:#fff; letter-spacing:.01em;
  -webkit-text-stroke:.6px #fff; }
.vol { font-size:30px; font-weight:800; color:#fcd34d; border:2.5px solid #fbbf24;
  border-radius:12px; padding:6px 16px; }
.rule { height:3px; margin:22px 0 0; border-radius:3px;
  background:linear-gradient(90deg, rgba(251,191,36,0) 0%, #b8860b 12%, #fbbf24 50%, #b8860b 88%, rgba(251,191,36,0) 100%); }

/* ---------- content ---------- */
.mid { flex:1 1 0; display:flex; flex-direction:column; min-height:0; overflow:hidden; }
.center { justify-content:center; }
.gap { gap:18px; }

.pill { align-self:center; font-weight:900; border-radius:16px; }
.pill.solid { background:#fbbf24; color:#1a1206; font-size:38px; padding:16px 40px;
  border:3px dashed rgba(255,255,255,.55); box-shadow:0 10px 34px rgba(251,191,36,.28); }
.pill.ghost { color:#c7cceb; font-size:32px; font-weight:800; padding:12px 30px;
  border:2px solid rgba(150,160,210,.45); border-radius:999px; background:rgba(255,255,255,.03); }
.pill.ghost b { color:#a5b4fc; }

.quote { font-size:74px; line-height:1.28; color:#fff; text-align:center; margin-top:6px; }
.quote.sm { font-size:60px; }
.u { border-bottom:5px solid rgba(255,255,255,.55); padding-bottom:4px; }

.hl-line { font-size:80px; font-weight:900; color:#fff; text-align:center; -webkit-text-stroke:.7px #fff; }
.hl-line.sm { font-size:62px; }
.uy { background:linear-gradient(transparent 62%, #fbbf24 62%, #fbbf24 92%, transparent 92%); padding:0 4px; }
.pink { color:#f472b6; }
.pinkstrong { color:#ec4899; }
.gold { color:#fcd34d; }
.indigo { color:#a5b4fc; }
.green { color:#34d399; }
.mute { color:#8b93bd; }

.sub2 { font-size:42px; font-weight:800; color:#fff; text-align:center; }
.gloss { text-align:center; font-size:32px; color:#7f87b0; font-weight:600; margin-top:4px; }
.gloss b { color:#aab2dc; }

/* dashed / bordered boxes */
.box { border-radius:26px; padding:36px 40px; }
.box.dash { border:3px dashed rgba(150,160,210,.42); }
.box.gold  { border:3px solid #fbbf24; background:rgba(251,191,36,.05); }
.box.pinkd { border:3px dashed rgba(236,72,153,.6); background:rgba(236,72,153,.05); }
.box.green { border:3px solid #34d399; background:rgba(52,211,153,.07); }

.serif-blk { font-size:60px; line-height:1.4; color:#fff; text-align:center; }
.circle { display:inline-block; position:relative; color:#fcd34d; font-weight:700; }
.circle::after { content:""; position:absolute; inset:-14px -18px; border:4px solid #ec4899;
  border-radius:52% 48% 50% 50%/60% 55% 45% 40%; transform:rotate(-4deg); }

/* choice A/B */
.choice { display:flex; align-items:center; gap:24px; border:2px solid rgba(150,160,210,.4);
  border-radius:20px; padding:20px 26px; background:rgba(255,255,255,.035); }
.choice .mk { flex:none; width:60px; height:60px; border-radius:14px; display:flex; align-items:center;
  justify-content:center; font-size:36px; font-weight:900; color:#fff;
  background:rgba(129,140,248,.9); }
.choice .tx { font-size:34px; font-weight:800; line-height:1.32; color:#eef1ff; }
.choice .tx small { display:block; font-size:25px; font-weight:700; color:#f472b6; margin-bottom:2px; }

.cbig { text-align:center; font-size:180px; font-weight:900; color:#fcd34d; line-height:1;
  position:relative; display:inline-block; align-self:center; }
.cbig::after { content:""; position:absolute; inset:-24px -40px; border:7px solid #ec4899;
  border-radius:50% 48% 52% 50%/56% 52% 48% 44%; transform:rotate(-5deg);
  box-shadow:0 0 0 12px rgba(236,72,153,.12) inset; }

.answer-label { text-align:center; font-size:36px; font-weight:900; letter-spacing:.3em;
  color:#a5b4fc; padding-left:.3em; }

.rule-box { border:3px solid #fbbf24; border-radius:24px; }
.rule-row { display:flex; align-items:center; justify-content:center; gap:16px; padding:22px 26px;
  font-size:33px; font-weight:800; white-space:nowrap; }
.rule-row + .rule-row { border-top:2px solid rgba(251,191,36,.32); }
.rule-row .k { color:#fcd34d; }
.rule-row .arw { color:#8b93bd; font-weight:900; }

.diagram { text-align:center; font-size:52px; line-height:1.5; color:#eef1ff; }
.tag { font-size:34px; font-weight:900; }
.tag.s { color:#f472b6; } .tag.v { color:#f472b6; }

.note { text-align:center; font-size:38px; font-weight:800; color:#fff; }
.note .pink { color:#f472b6; }
.smallnote { text-align:center; font-size:30px; color:#8b93bd; font-weight:600; }

.cta { align-self:flex-end; font-size:36px; font-weight:900; color:#fcd34d;
  border:2.5px solid #fbbf24; border-radius:999px; padding:18px 40px; }
.cta.solid { color:#1a1206; background:#fbbf24; }
.cta.dash { border-style:dashed; }
.cta.pink { color:#fff; border-color:#ec4899; background:rgba(236,72,153,.9); }

.wide { align-self:stretch; text-align:center; border-radius:999px; font-weight:900; }
.wide.gold { background:#fbbf24; color:#1a1206; font-size:44px; padding:24px; border:3px dashed rgba(255,255,255,.5); }
.wide.pink { background:#ec4899; color:#fff; font-size:42px; padding:24px; border:3px solid #f9a8d4; }

.teaser { border:3px dashed rgba(129,140,248,.5); border-radius:22px; padding:26px 34px;
  text-align:center; font-size:34px; font-weight:800; color:#dfe3ff; line-height:1.4; }
.teaser .gold { color:#fcd34d; }

/* ---------- footer ---------- */
.src { flex:none; font-size:26px; color:#6b7299; font-weight:600; margin-top:14px; }
.foot { flex:none; display:flex; align-items:center; justify-content:space-between;
  border-top:1px solid rgba(255,255,255,.08); padding-top:20px; margin-top:16px; }
.foot .h { font-size:30px; color:#8b93bd; font-weight:700; }
.foot .r { display:flex; align-items:center; gap:22px; }
.dots { display:flex; gap:12px; }
.dot { width:14px; height:14px; border-radius:50%; background:rgba(255,255,255,.22); }
.dot.on { background:#fbbf24; }
.pg { font-size:32px; font-weight:900; color:#c7cceb; }
"""


def shell(n, inner, center=False, src=True):
    dots = "".join(
        f'<span class="dot {"on" if i == n else ""}"></span>' for i in range(1, 7)
    )
    srchtml = f'<div class="src">{SOURCE}</div>' if src else ""
    midcls = "mid center gap" if center else "mid gap"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="stage">
  <div style="flex:none">
    <div class="eyebrow">TRILLION ENGLISH ACADEMY</div>
    <div class="title-row"><span class="title">{TITLE}</span><span class="vol">{VOL}</span></div>
    <div class="rule"></div>
  </div>
  <div class="{midcls}">
    {inner}
  </div>
  {srchtml}
  <div class="foot">
    <div class="h">{HANDLE} ・ {SITE}</div>
    <div class="r"><div class="dots">{dots}</div><div class="pg">{n}/6</div></div>
  </div>
</div></body></html>"""


# ============================ スライド本文 ============================

SLIDES = {}

# --- 1: フック ---
SLIDES[1] = shell(1, """
  <div class="pill solid">実際の入試問題</div>
  <div class="pill ghost" style="margin-top:20px">難関私大 ・ <b>空所補充(文脈)</b></div>
  <div class="quote serif" style="margin-top:30px">
    “There was <span class="u">nothing</span><br>
    to do <span class="u">but</span> wait.”
  </div>
  <div class="hl-line" style="margin-top:20px">この <span class="gold">but</span>、<span class="uy">訳せる？</span></div>
  <div class="sub2" style="margin-top:22px">事故ポイントは、<span class="pinkstrong">この “but” 1語</span>。</div>
  <div class="gloss" style="margin-top:18px"><b>nothing to do but ~</b> ← 今日のカギ</div>
  <div style="flex:1"></div>
  <div class="cta">▶ スワイプして挑戦</div>
""", src=False)

# --- 2: 設問 ---
SLIDES[2] = shell(2, """
  <div class="hl-line sm" style="font-size:54px">Q. この <span class="gold">but</span>、<br>どう訳す？</div>
  <div class="box dash" style="padding:30px 34px">
    <div class="serif-blk" style="font-size:52px">There was nothing to do
      <span class="circle">but</span> wait.</div>
  </div>
  <div class="choice">
    <div class="mk">A</div>
    <div class="tx"><small>珍訳</small>することは無かった。しかし、待った</div>
  </div>
  <div class="choice">
    <div class="mk">B</div>
    <div class="tx">ただ待つ<b>しかなかった</b></div>
  </div>
  <div class="wide pink" style="font-size:34px;padding:18px">💬 直感でOK。AかBをコメントで!</div>
  <div class="cta dash" style="align-self:center;font-size:32px;padding:14px 32px">▶ 次のスライドで答え合わせ</div>
""", src=False)

# --- 3: 解答 ---
SLIDES[3] = shell(3, """
  <div class="answer-label">ANSWER</div>
  <div class="hl-line sm" style="font-size:52px">正解は…</div>
  <div class="cbig">B</div>
  <div class="box green" style="padding:30px 34px">
    <div class="note" style="line-height:1.4;font-size:42px">「ただ、<span class="green">待つしかなかった</span>」</div>
  </div>
  <div class="box pinkd" style="padding:22px 32px">
    <div class="smallnote" style="font-size:32px;color:#e9ecff;font-weight:700;line-height:1.42">
      <span class="pink">but</span> を「しかし」と読むと<br>意味が通らない<span class="pinkstrong">珍訳</span>に ⚠️</div>
  </div>
  <div class="sub2" style="font-size:40px">カギは but の<span class="uy">“本当の顔”</span>。</div>
  <div class="cta" style="align-self:center;font-size:34px;padding:16px 38px">▶ その正体へ</div>
""", src=False)

# --- 4: 解説(公式) ---
SLIDES[4] = shell(4, """
  <div class="hl-line sm" style="font-size:52px">nothing to do <span class="gold">but</span> ~ は<br>「〜する<span class="uy">しかない</span>」</div>
  <div class="rule-box">
    <div class="rule-row"><span class="k">nothing to do but V</span><span class="arw">→</span>
      <span style="color:#fff">Vする<span class="pink">しかない</span></span></div>
    <div class="rule-row"><span class="k">この but</span><span class="arw">=</span>
      <span style="color:#fff">「〜を除いて / 〜以外」<span class="green">except</span></span></div>
  </div>
  <div class="diagram serif" style="font-size:46px">
    nothing to do <span class="circle">but</span> <span class="u">wait</span>
  </div>
  <div class="smallnote" style="font-size:31px">
    = 「<b>待つこと以外</b>に、することがない」</div>
  <div class="note" style="font-size:36px;line-height:1.4">
    <span class="pink">do の後ろ</span>の but は<br>「しかし」<span class="pink">じゃない</span></div>
  <div class="box dash" style="padding:22px 28px">
    <div class="smallnote serif" style="font-size:32px;color:#eef1ff;font-weight:700">
      I had no choice but to wait.<span style="font-family:'Noto Sans CJK JP'">&nbsp;→&nbsp;「待つしかなかった」</span></div>
  </div>
  <div class="cta dash" style="align-self:center;font-size:33px;padding:14px 32px">▶ 後半に“but の仲間”</div>
""", src=True)

# --- 5: but の仲間(例外のbut) ---
SLIDES[5] = shell(5, """
  <div class="hl-line sm" style="font-size:52px"><span class="gold">“例外の but”</span>で<br>まとめて得する</div>
  <div class="box gold" style="padding:24px 32px">
    <div class="smallnote serif" style="font-size:36px;color:#fff;font-weight:700">have no choice but to do</div>
    <div class="smallnote" style="margin-top:6px;font-size:33px;color:#fcd34d;font-weight:800">→「〜する<b>しかない</b>」</div>
  </div>
  <div class="box dash" style="padding:22px 30px">
    <div class="smallnote serif" style="font-size:36px;color:#fff;font-weight:700">anything but ~</div>
    <div class="smallnote" style="margin-top:6px;font-size:33px;color:#a5b4fc;font-weight:800">→「<b>決して</b>〜ではない」</div>
  </div>
  <div class="box dash" style="padding:22px 30px">
    <div class="smallnote serif" style="font-size:36px;color:#fff;font-weight:700">all but ~</div>
    <div class="smallnote" style="margin-top:6px;font-size:33px;color:#a5b4fc;font-weight:800">→「<b>ほとんど</b>〜」</div>
  </div>
  <div class="note" style="margin-top:8px;font-size:36px;line-height:1.42">
    but に <span class="gold">「除外」の顔</span>があると<br>一気に読める</div>
  <div class="cta dash" style="align-self:center;font-size:33px;padding:14px 32px">▶ 最後にまとめ</div>
""", src=False)

# --- 6: 全訳・まとめ ---
SLIDES[6] = shell(6, """
  <div class="hl-line sm" style="font-size:52px">今日の1文・<span class="uy">全訳</span></div>
  <div class="box gold" style="padding:28px 34px">
    <div class="note" style="font-size:40px;line-height:1.45;font-weight:800">
      「することは、ただ<br>待つことしか<br>なかった。」</div>
  </div>
  <div class="box pinkd" style="padding:22px 30px">
    <div class="note" style="font-size:33px">
      <span class="gold">nothing to do but V</span> = Vする<span class="pink">しかない</span></div>
  </div>
  <div class="smallnote" style="font-size:29px">
    ※ この but =「〜を除いて(except)」。「しかし」ではない</div>
  <div class="smallnote" style="font-size:32px;color:#fcd34d;font-weight:800">
    but の識別は 難関私大・共通テスト・英検で頻出</div>
  <div class="wide gold" style="font-size:40px;padding:18px">📄 保存して復習</div>
  <div class="wide pink" style="font-size:38px;padding:18px">✅ フォローで次の1文 → @trillion_ai</div>
  <div class="teaser" style="font-size:31px;padding:20px 30px">
    次回: 中学単語 “as” だけで受験生を沈めた一文<span class="gold">(難関大)</span></div>
""", src=False)


def render(n, html):
    hp = os.path.join(OUT, f"march_{n:02d}.html")
    pp = os.path.join(OUT, f"march_{n:02d}.png")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    if not CHROME:
        print("!! Chromium not found; wrote HTML only:", hp)
        return
    subprocess.run([
        CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--force-device-scale-factor=2",
        f"--window-size={W},{H}", f"--screenshot={pp}", f"file://{hp}",
    ], check=True, stderr=subprocess.DEVNULL)
    print("rendered", pp)


if __name__ == "__main__":
    for n in range(1, 7):
        render(n, SLIDES[n])
    print("done ->", OUT)
