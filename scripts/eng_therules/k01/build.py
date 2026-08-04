# -*- coding: utf-8 -*-
import os, re, html
import content as C

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- word count ----
WORDS = len([w for w in re.split(r"\s+", C.PASSAGE_PLAIN.strip()) if w])
WORDS_ROUND = int(round(WORDS / 10.0) * 10)

# 写真(No.02ポラリス式)準拠: S赤 / V緑 / O橙 / C黄土。M・接・同格はチップ無し。
CHIP = {"S": "#dc2626", "V": "#059669", "O": "#ea580c", "C": "#b45309"}
LOGIC_COLORS = {"因果": "#dc2626", "対比": "#7c3aed", "主張": "#a16207",
                "具体例": "#0891b2", "譲歩": "#64748b", "追加": "#2563eb"}

BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 13mm 15mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  font-family: "Hiragino Mincho ProN","Yu Mincho",serif;
  color: #1a1a1a; font-size: 10.5pt; line-height: 1.66; margin: 0;
}
.gothic { font-family: "Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }
.en { font-family: Georgia,"Times New Roman",serif; }
h1,h2,h3,.band,.qno,.tag,.chip,.role,.secttl,.rulecat,.pts,.foot { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; }

/* header band */
.band { background: linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9.5pt; opacity:.9; margin-left:8px; }
.band .r { text-align:right; font-size:9pt; line-height:1.4; }
.band .r b { font-size:12pt; }
.subline { margin:7px 2px 2px; font-size:9.5pt; color:#334155; }
.subline .theme { display:block; font-weight:700; color:#0f172a; }
.subline .sub2 { display:block; margin-top:2px; font-size:9pt; color:#475569; }
.rulestag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700; border-radius:4px;
  padding:1px 7px; font-size:8.5pt; margin-left:6px; }

.metarow { display:flex; gap:10px; margin:9px 0 6px; font-size:9.5pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 130px; text-align:center; }

.instr { font-size:9.5pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px; border-radius:4px; margin:8px 0; }

/* passage */
.passage { margin-top:6px; }
.para { display:flex; gap:9px; margin:0 0 8px; page-break-inside:avoid; }
.para .num { flex:0 0 22px; height:22px; background:#1e3a8a; color:#fff; border-radius:50%;
  text-align:center; line-height:22px; font-size:9pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; }
.para .body { flex:1; }
.passage .en { line-height:1.95; text-align:justify; }
.blank { display:inline-block; border:1px solid #64748b; border-radius:4px; padding:0 4px; font-weight:700;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; background:#fff; }
.passage u { text-decoration:none; border-bottom:1.6px solid #dc2626; padding-bottom:1px; }
.passage sup { color:#dc2626; font-weight:700; }

/* questions */
.qsec { margin-top:14px; }
.qtitle { font-size:12pt; font-weight:700; text-align:center; letter-spacing:.5em; padding:3px 0;
  border-top:2px solid #0f172a; border-bottom:2px solid #0f172a; margin-bottom:10px; }
.q { margin:0 0 11px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 9px; font-size:9.5pt; font-weight:700; }
.pts { color:#dc2626; font-size:8.5pt; font-weight:700; }
.q .stem { margin:3px 0 3px; font-size:10pt; }
.q .choices div { margin:2px 0 2px 6px; font-size:9.7pt; }
.ansbox { border:1px solid #94a3b8; border-radius:6px; min-height:34px; margin-top:4px; }

/* section titles (解説) */
.secttl { font-size:13pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a;
  padding:3px 0 3px 10px; margin:0 0 10px; page-break-after:avoid; break-after:avoid; }
.keepwith { page-break-inside:avoid; break-inside:avoid; }
.secttl .en2 { font-size:9pt; color:#64748b; font-weight:600; margin-left:8px; }
.section { margin-bottom:10px; }
.pb { page-break-before: always; }

/* answer table */
table.ans { width:100%; border-collapse:collapse; font-size:9.3pt; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:5px 7px; vertical-align:top; }
table.ans th { background:#eef2ff; font-family:"Hiragino Kaku Gothic ProN",sans-serif; white-space:nowrap; }
table.ans td.a { font-weight:700; color:#1e3a8a; white-space:nowrap; }
.wcard { border:1px solid #cbd5e1; border-left:4px solid #047857; border-radius:6px; padding:7px 10px; margin:8px 0;
  page-break-inside:avoid; }
.wcard .wh { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:9.7pt; color:#065f46; }
.wcard .model { background:#f0fdf4; border-radius:4px; padding:5px 8px; margin:4px 0; font-size:9.6pt; }
.wcard .pt { font-size:9pt; color:#334155; }

/* rules index */
.rulecat { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:11pt; margin:10px 0 5px;
  padding:2px 8px; border-radius:5px; display:inline-block; }
.rc-read { background:#eff4ff; color:#1d4ed8; }
.rc-solve { background:#e8f7f0; color:#047857; }
.rc-syntax { background:#f3ecfe; color:#7c3aed; }
.rule { display:flex; gap:8px; padding:3.5px 0; border-bottom:1px dashed #d7dde6; page-break-inside:avoid; }
.rule .rid { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:800; flex:0 0 34px; }
.rid.read { color:#1d4ed8; } .rid.solve { color:#047857; } .rid.syntax { color:#7c3aed; }
.rule .rmain { flex:1; }
.rule .rname { font-weight:700; font-size:9.9pt; }
.rule .rstar { color:#f59e0b; font-size:9pt; margin-left:5px; }
.rule .rwhere { font-size:8.7pt; color:#64748b; }
.ruleintro { font-size:9pt; color:#475569; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:6px 9px; margin-bottom:6px; }

/* logic map */
.lm { }
.lm .legend { font-size:8.8pt; color:#475569; margin-bottom:8px; }
.lm .node { border:1px solid #cbd5e1; border-radius:8px; padding:4px 10px; page-break-inside:avoid; }
.lm .node .rh { display:flex; align-items:center; gap:8px; margin-bottom:1px; }
.role { color:#fff; border-radius:5px; padding:1px 9px; font-size:9pt; font-weight:700; }
.role.intro{background:#64748b;} .role.concession{background:#d97706;} .role.claim{background:#1d4ed8;}
.role.reason{background:#0891b2;} .role.core{background:#dc2626;} .role.conclusion{background:#047857;}
.lm .node .para { color:#94a3b8; font-size:8.6pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.lm .node .txt { font-size:9.6pt; }
.lm .arrow { text-align:center; color:#1e3a8a; font-size:9pt; font-weight:700; margin:1.5px 0; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }

/* figures */
.fig { border:1px solid #cbd5e1; border-radius:8px; padding:7px 10px; margin:8px 0; page-break-inside:avoid; }
.fig .ft { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:10.3pt; color:#0f172a; margin-bottom:5px; }
.fig .cap { font-size:9pt; color:#334155; margin-top:5px; }
.fig .pref { font-size:8.5pt; color:#94a3b8; text-align:right; }
.fig svg { width:100%; height:auto; display:block; }

/* svoc — インライン・フロー式(写真準拠): チップ+色下線のカタマリが横に流れ、直下に直訳 */
.svhead { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:700; font-size:11pt; color:#0f172a;
  border-bottom:1.5px solid #cbd5e1; padding:2px 1px 3px; margin:13px 0 8px; page-break-after:avoid; }
.svhead small { color:#64748b; font-weight:600; font-size:8.8pt; margin-left:6px; }
.svlegend { border:1px solid #dbe2ea; background:#f8fafc; border-radius:6px; padding:6px 10px;
  font-size:8.8pt; color:#334155; margin:2px 0 10px; line-height:1.9;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.sent { background:#fbfcfe; border:1px solid #e6ebf2; border-radius:7px; padding:8px 11px 5px;
  margin:0 0 9px; page-break-inside:avoid; overflow-wrap:break-word; }
.flow { line-height:1.45; }
.ck { display:inline-block; vertical-align:top; margin:0 11px 7px 0; max-width:100%; }
.ctag { display:inline-block; color:#fff; border-radius:3px; padding:0 4.5px; font-size:7.6pt; font-weight:700;
  margin-right:4px; font-family:"Hiragino Kaku Gothic ProN",sans-serif; position:relative; top:-1px; }
.cen { font-family:Georgia,serif; font-size:10pt; padding-bottom:1px; }
.cen.u { border-bottom:1.6px solid; }
.cja { display:block; color:#64748b; font-size:8.2pt; line-height:1.35; margin-top:2px; }
.nclz { color:#1d4ed8; font-weight:700; }
.aclz { color:#b91c1c; }
.lgc { display:inline-block; color:#fff; border-radius:4px; padding:0.5px 8px; font-size:8pt; font-weight:700;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; margin:1px 0 0 2px; vertical-align:top; }
.note { font-size:8.9pt; color:#1f2937; background:#f1f5f9; border-radius:5px; padding:3px 8px; margin-top:2px; line-height:1.55; }

/* translation & vocab */
.tr { display:flex; gap:9px; margin:0 0 4px; page-break-inside:avoid; }
.tr .num { flex:0 0 20px; height:20px; background:#334155; color:#fff; border-radius:50%; text-align:center;
  line-height:20px; font-size:8.5pt; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.tr .t { flex:1; font-size:9.7pt; }
table.vocab { width:100%; border-collapse:collapse; font-size:9pt; }
table.vocab td { border:1px solid #e2e8f0; padding:2px 7px; }
table.vocab tr { page-break-inside:avoid; }
table.vocab td.w { font-family:Georgia,serif; width:26%; }

.foot { text-align:center; color:#64748b; font-size:8.3pt; margin-top:8px; padding-top:4px; border-top:1px solid #e2e8f0;
  font-family:"Hiragino Kaku Gothic ProN",sans-serif; page-break-inside:avoid; }
"""

def doc(title, inner):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<title>{title}</title><style>{BASE_CSS}</style></head><body>{inner}</body></html>"""

def header_band(kind):
    return f"""<div class="band">
  <div class="l">英語長文読解 <small>The Rules 式</small></div>
  <div class="r">{C.META['level']}<br><b>No.{C.META['no']}</b></div>
</div>
<div class="subline">
  <span class="theme">Reading — テーマ：{C.META['theme_ja']}<span class="rulestag">読解ルールで解く</span></span>
  <span class="sub2">{C.META['theme_en']}　／　語数 約{WORDS_ROUND} words ・ 目標 {C.META['minutes']}分</span>
</div>"""

def foot(kind):
    return (f'<div class="foot">トリリオンAI塾 ／ 英語長文 The Rules 式 No.{C.META["no"]} '
            f'・ {C.META["level"]}（{C.META["level_sub"]}）・ {kind}</div>')

# ---------------- 問題編 ----------------
def build_mondai():
    h = header_band("q")
    name = f"　<b>{C.META['student']}</b>" if C.META.get("student") else ""
    h += f"""<div class="metarow">
      <div class="cell">氏名{name}</div>
      <div class="cell">日付　　　　／</div>
      <div class="cell score">得点　　　／ {C.META['full']}</div>
    </div>"""
    h += ('<div class="instr">次の英文を読んで、後の問い（問1〜問7）に答えなさい。'
          '空所【 A 】【 B 】には接続表現が入る。下線部 (1)〜(3) は設問で問われる。</div>')
    h += '<div class="passage">'
    for n, body in C.PASSAGE_HTML:
        h += f'<div class="para"><div class="num">{n}</div><div class="body"><span class="en">{body}</span></div></div>'
    h += '</div>'
    # questions
    h += '<div class="qsec"><div class="qtitle">設　問</div>'
    for q in C.QUESTIONS:
        h += '<div class="q"><div class="h"><span class="qno">'+q["no"]+'</span><span class="pts">（'+q["pts"]+'）</span></div>'
        h += '<div class="stem">'+q["stem"]+'</div>'
        if q["choices"]:
            h += '<div class="choices">'+"".join(f'<div>{c}</div>' for c in q["choices"])+'</div>'
        else:
            h += '<div class="ansbox"></div>'
        h += '</div>'
    h += '</div>'
    h += foot("問題編")
    return doc("英語長文 The Rules 式 No.01 問題編", h)

# ---------------- 図解 SVG ----------------
def svg_fig1():
    return """<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="'Hiragino Kaku Gothic ProN',sans-serif">
    <rect x="20" y="82" width="130" height="46" rx="9" fill="#334155"/>
    <text x="85" y="103" fill="#fff" font-size="14" font-weight="700" text-anchor="middle">受験生の運動</text>
    <text x="85" y="120" fill="#cbd5e1" font-size="10" text-anchor="middle">exercise</text>
    <path d="M150 96 L250 46" stroke="#dc2626" stroke-width="2.5" fill="none" marker-end="url(#ar)"/>
    <path d="M150 114 L250 164" stroke="#1d4ed8" stroke-width="2.5" fill="none" marker-end="url(#ab)"/>
    <defs>
      <marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#dc2626"/></marker>
      <marker id="ab" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#1d4ed8"/></marker>
    </defs>
    <rect x="255" y="22" width="185" height="52" rx="9" fill="#fee2e2" stroke="#dc2626"/>
    <text x="347" y="42" fill="#b91c1c" font-size="12" font-weight="700" text-anchor="middle">〈敵〉という通念</text>
    <text x="347" y="60" fill="#7f1d1d" font-size="10" text-anchor="middle">勉強時間を奪うぜいたく（第1段）</text>
    <rect x="255" y="138" width="185" height="52" rx="9" fill="#dbeafe" stroke="#1d4ed8"/>
    <text x="347" y="158" fill="#1e40af" font-size="12" font-weight="700" text-anchor="middle">〈味方〉という主張</text>
    <text x="347" y="176" fill="#1e3a8a" font-size="10" text-anchor="middle">学ぶ準備を整える友（第3・6段）</text>
    <path d="M440 48 L520 48" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#ag)"/>
    <path d="M440 164 L520 164" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#ag)"/>
    <defs><marker id="ag" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/></marker></defs>
    <rect x="525" y="24" width="175" height="48" rx="9" fill="#f8fafc" stroke="#94a3b8"/>
    <text x="612" y="44" fill="#475569" font-size="11.5" font-weight="700" text-anchor="middle">運動を避ける</text>
    <text x="612" y="61" fill="#64748b" font-size="9.5" text-anchor="middle">一分＝教科書から盗まれた一分</text>
    <rect x="525" y="140" width="175" height="48" rx="9" fill="#eff6ff" stroke="#1d4ed8"/>
    <text x="612" y="160" fill="#1e40af" font-size="11.5" font-weight="700" text-anchor="middle">机の1時間の価値が上がる</text>
    <text x="612" y="177" fill="#1e3a8a" font-size="9.5" text-anchor="middle">時間は価値を付けて戻る（第6段）</text>
  </svg>"""

def svg_fig2():
    return """<svg viewBox="0 0 720 214" xmlns="http://www.w3.org/2000/svg" font-family="'Hiragino Kaku Gothic ProN',sans-serif">
    <rect x="20" y="84" width="150" height="46" rx="9" fill="#1e3a8a"/>
    <text x="95" y="105" fill="#fff" font-size="14" font-weight="700" text-anchor="middle">運動の二つの働き</text>
    <text x="95" y="122" fill="#c7d2fe" font-size="9.5" text-anchor="middle">how exercise helps</text>
    <path d="M170 98 L245 44" stroke="#1d4ed8" stroke-width="2.5" fill="none" marker-end="url(#b2)"/>
    <path d="M170 116 L245 170" stroke="#1d4ed8" stroke-width="2.5" fill="none" marker-end="url(#b2)"/>
    <defs><marker id="b2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#1d4ed8"/></marker>
    <marker id="g2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/></marker></defs>
    <rect x="250" y="16" width="170" height="52" rx="9" fill="#dbeafe" stroke="#1d4ed8"/>
    <text x="335" y="37" fill="#1e40af" font-size="12" font-weight="700" text-anchor="middle">① 脳への効果</text>
    <text x="335" y="55" fill="#1e3a8a" font-size="9.5" text-anchor="middle">more blood to the brain（第3段）</text>
    <rect x="250" y="146" width="170" height="52" rx="9" fill="#dbeafe" stroke="#1d4ed8"/>
    <text x="335" y="167" fill="#1e40af" font-size="12" font-weight="700" text-anchor="middle">② 心への効果</text>
    <text x="335" y="185" fill="#1e3a8a" font-size="9.5" text-anchor="middle">it lifts their mood（第5段）</text>
    <path d="M420 42 L470 42" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#g2)"/>
    <path d="M420 172 L470 172" stroke="#94a3b8" stroke-width="2" fill="none" marker-end="url(#g2)"/>
    <rect x="475" y="18" width="225" height="48" rx="9" fill="#eff6ff" stroke="#93c5fd"/>
    <text x="587" y="38" fill="#1e40af" font-size="11" font-weight="700" text-anchor="middle">「学ぶ準備」＝集中しやすく記憶に残る</text>
    <text x="587" y="55" fill="#1e3a8a" font-size="9.5" text-anchor="middle">ready to learn（第3〜4段）</text>
    <rect x="475" y="148" width="225" height="48" rx="9" fill="#eff6ff" stroke="#93c5fd"/>
    <text x="587" y="168" fill="#1e40af" font-size="11" font-weight="700" text-anchor="middle">不安・ストレスが減り、机に戻る力</text>
    <text x="587" y="185" fill="#1e3a8a" font-size="9.5" text-anchor="middle">the power to try again（第5段）</text>
  </svg>"""

def svg_fig3():
    return """<svg viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg" font-family="'Hiragino Kaku Gothic ProN',sans-serif">
    <rect x="30" y="52" width="200" height="72" rx="10" fill="#fef2f2" stroke="#dc2626"/>
    <text x="130" y="82" fill="#b91c1c" font-size="14" font-weight="700" text-anchor="middle">運動 ＝ 時間泥棒？</text>
    <text x="130" y="104" fill="#7f1d1d" font-size="10.5" text-anchor="middle">✗ 教科書から盗まれた一分（通念）</text>
    <text x="285" y="82" fill="#0f172a" font-size="26" text-anchor="middle">→</text>
    <rect x="330" y="42" width="360" height="94" rx="10" fill="#eff6ff" stroke="#1d4ed8"/>
    <text x="510" y="70" fill="#1e40af" font-size="14" font-weight="700" text-anchor="middle">運動 ＝ 勉強の味方</text>
    <text x="510" y="92" fill="#1e3a8a" font-size="10.5" text-anchor="middle">○ 机に向かう一時間一時間の価値を高める〈友〉</text>
    <text x="510" y="112" fill="#1e3a8a" font-size="10.5" text-anchor="middle">not an enemy but a friend</text>
    <text x="510" y="130" fill="#64748b" font-size="9" text-anchor="middle">前提：長く激しい運動は不要——休憩に10分歩くだけで、この習慣の入口には十分</text>
  </svg>"""

FIG_SVG = {"fig1": svg_fig1, "fig2": svg_fig2, "fig3": svg_fig3}

# ---------------- 解説編 ----------------
def build_kaisetsu():
    h = header_band("a")
    h += '<div style="text-align:center;font-family:\'Hiragino Kaku Gothic ProN\',sans-serif;font-weight:700;font-size:12pt;margin:6px 0 4px;">解答・解説編</div>'
    h += ('<div style="text-align:center;font-size:9pt;color:#475569;margin-bottom:8px;">'
          '解答・配点 ／ この長文で使う The Rules ／ 論理構造マップ ／ 図解 ／ SVOC構文 ／ 全訳 ／ 語彙</div>')

    # --- 解答と配点 ---
    h += '<div class="section"><div class="secttl">解答 と 配点<span class="en2">Answer Key</span>　<span style="font-size:9pt;color:#64748b;">（満点 '+str(C.META["full"])+'点）</span></div>'
    h += '<table class="ans"><tr><th>問</th><th>配点</th><th>解答</th><th>解説</th></tr>'
    for r in C.ANSWERS_TABLE:
        h += f'<tr><td class="a">{r["no"]}</td><td>{r["pts"]}</td><td class="a">{r["ans"]}</td><td>{r["exp"]}</td></tr>'
    h += '</table>'
    for w in C.ANSWERS_WRITTEN:
        h += (f'<div class="wcard"><div class="wh">{w["no"]}（{w["pts"]}）</div>'
              f'<div class="model">〔解答例〕{w["model"]}</div>'
              f'<div class="pt">{w["points"]}</div></div>')
    h += '</div>'

    # --- The Rules 一覧 ---
    h += '<div class="section"><div class="secttl">この長文で使う The Rules<span class="en2">Rules used in this passage</span></div>'
    h += ('<div class="ruleintro">読解ルール（読み方）・解法ルール（解き方）・構文ルール（形）の三種類。'
          '本問で使うものを抜き出した。★は重要度。<b>まずこの表のルールを意識して</b>もう一度本文を読み直すと、'
          '論理の流れが見えてくる。<br><span style="color:#94a3b8;">※関正生『The Rules 英語長文問題集』の“ルールで読む”'
          'アプローチに着想を得た、トリリオンAI塾オリジナルの整理です。</span></div>')
    catmap = [("読解ルール","rc-read","read"),("解法ルール","rc-solve","solve"),("構文ルール","rc-syntax","syntax")]
    for cat, cls, idc in catmap:
        h += f'<div class="rulecat {cls}">{cat}</div>'
        for rid, name, star, where in C.RULES[cat]:
            h += (f'<div class="rule"><div class="rid {idc}">{rid}</div><div class="rmain">'
                  f'<span class="rname">{name}</span><span class="rstar">{star}</span>'
                  f'<div class="rwhere">使いどころ：{where}</div></div></div>')
    h += '</div>'

    # --- 論理構造マップ ---
    h += '<div class="section"><div class="secttl">論理構造マップ<span class="en2">Argument Map</span></div><div class="lm">'
    h += ('<div class="legend">読み方： 各段落の役割（導入／譲歩／主張／★核心／結論）と、'
          '段落間の関係（<b>逆接・因果</b>）を追う。青字は本問の The Rules。</div>')
    for item in C.LOGIC_MAP:
        if "arrow" in item:
            h += f'<div class="arrow">{item["arrow"]}</div>'
        else:
            h += (f'<div class="node"><div class="rh"><span class="role {item["kind"]}">{item["role"]}</span>'
                  f'<span class="para">{item["para"]}</span></div><div class="txt">{item["text"]}</div></div>')
    h += '</div></div>'

    # --- 図解 ---
    h += '<div class="section"><div class="secttl">図解で読む — 論理と主張<span class="en2">Visual Guide</span></div>'
    for f in C.FIGURES:
        h += (f'<div class="fig"><div class="ft">{f["title"]}</div>{FIG_SVG[f["id"]]()}'
              f'<div class="cap">{f["caption"]}</div><div class="pref">{f["para"]}</div></div>')
    h += '</div>'

    # --- SVOC (インライン・フロー式) ---
    def _fmt_en(en):
        en = re.sub(r'\[(.*?)\]', r'<span class="nclz">[\1]</span>', en, flags=re.S)
        en = re.sub(r'&lt;(.*?)&gt;', r'<span class="aclz">&lt;\1&gt;</span>', en, flags=re.S)
        return en
    def _is_nclause(en):
        t = en.strip().rstrip('.,;:')
        return t.startswith('[') and t.endswith(']')
    h += '<div class="section pb"><div class="secttl">構文（SVOC）解説<span class="en2">Sentence Structure Analysis</span></div>'
    lg_chips = "　".join(f'<span class="lgc" style="background:{c}">{k}</span>'
                          for k, c in LOGIC_COLORS.items())
    tag_chips = "　".join(f'<span class="ctag" style="background:{c}">{t}</span>'
                           + {"S":"主語","V":"動詞","O":"目的語","C":"補語"}[t]
                           for t, c in CHIP.items())
    h += (f'<div class="svlegend"><b>記号の凡例：</b> {tag_chips}　／　（ 副詞句・前置詞句 M ）　'
          f'<span class="nclz">[ 名詞節 ]</span>　<span class="aclz">&lt; 形容詞節・関係詞節／分詞句 &gt;</span><br>'
          f'<b>論理の目印 →</b> {lg_chips}　／　各カタマリの下に直訳。〔R番号〕＝「この長文で使う The Rules」参照。</div>')
    for p_idx, p in enumerate(C.SVOC, start=1):
        h += f'<div class="svhead">{p["head"]}</div>'
        for s_idx, s in enumerate(p["sentences"], start=1):
            h += '<div class="sent"><div class="flow">'
            for tag, en, ja in s["chunks"]:
                enf = _fmt_en(en)
                if tag in CHIP and not _is_nclause(en):
                    col = CHIP[tag]
                    top = (f'<span class="ctag" style="background:{col}">{tag}</span>'
                           f'<span class="cen u" style="border-bottom-color:{col}">{enf}</span>')
                elif _is_nclause(en):
                    top = f'<span class="cen">{enf}</span>'  # 名詞節=青太字のみ・チップ/下線なし
                else:  # M / 接 / 同格
                    top = f'<span class="cen" style="color:#334155">{enf}</span>'
                h += f'<span class="ck">{top}<span class="cja">{ja}</span></span>'
            lg = getattr(C, "SVOC_LOGIC", {}).get((p_idx, s_idx))
            if lg:
                h += f'<span class="lgc" style="background:{LOGIC_COLORS[lg]}">{lg}</span>'
            h += '</div>'
            if s.get("note"):
                h += f'<div class="note">{s["note"]}</div>'
            h += '</div>'
    h += '</div>'

    # --- 全訳 ---
    h += '<div class="section">'
    for i, (n, t) in enumerate(C.TRANSLATION):
        row = f'<div class="tr"><div class="num">{n}</div><div class="t">{t}</div></div>'
        if i == 0:
            # 見出しは最初の訳文と同ページに固定 (泣き別れ防止)
            h += ('<div class="keepwith"><div class="secttl">全訳<span class="en2">Translation</span></div>'
                  + row + '</div>')
        else:
            h += row
    h += '</div>'

    # --- 語彙 ---
    h += '<div class="section"><div class="secttl">重要語彙・表現<span class="en2">Key Vocabulary</span></div><table class="vocab">'
    rows = C.VOCAB
    for i in range(0, len(rows), 2):
        h += '<tr>'
        for j in (i, i+1):
            if j < len(rows):
                w, m = rows[j]
                h += f'<td class="w">{w}</td><td>{m}</td>'
            else:
                h += '<td></td><td></td>'
        h += '</tr>'
    h += '</table></div>'

    h += foot("解答・解説編（The Rules＋論理構造＋図解＋SVOC）")
    return doc("英語長文 The Rules 式 No.01 解説編", h)

if __name__ == "__main__":
    m = build_mondai()
    k = build_kaisetsu()
    open(os.path.join(OUT, "mondai.html"), "w").write(m)
    open(os.path.join(OUT, "kaisetsu.html"), "w").write(k)
    print(f"words={WORDS} (round {WORDS_ROUND})")
    print("wrote mondai.html", len(m), "bytes")
    print("wrote kaisetsu.html", len(k), "bytes")
