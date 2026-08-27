#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
過去問 SVOCM 構造解析プリント — ビルド

  python3 scripts/eng_svoc_kaisetsu/build.py             # HTML ＋ PDF
  python3 scripts/eng_svoc_kaisetsu/build.py --no-pdf    # HTML だけ（CI 用）
  STUDENT_NAME="姓 名" python3 ... build.py              # 宛名入りで刷る

★宛名はコードに書かない（このリポジトリは PUBLIC）。環境変数でしか入らない。
★ビルド前に必ず check.py を通す（通らなければ何も出力しない）。
"""
import os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core, check as gate

OUT_DIR = os.environ.get("SVOC_OUT", os.path.join(HERE, "_out"))
STUDENT = os.environ.get("STUDENT_NAME", "")
esc = core.esc

EXTRA_CSS = """
/* Linux（IPAGothic しか無い環境）でも日本語が出るようにフォールバックを足す */
body, .gothic, h1,h2,h3,.band,.qno,.secttl,.partttl,.foot,.plabel,.vhd,.lb,.glb,.sk sub,.stepno,
.rulecard .rh, .acard .apat, .acard .atag, .acard .ano, .jatr b, .skel .lead
  { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic","IPAPGothic","IPAGothic",
    "Noto Sans CJK JP",sans-serif; }
body { font-family:"Hiragino Mincho ProN","Yu Mincho","IPAPGothic","IPAGothic",serif; }
.passage p, .bunkai, .skel, .wsent, .ptitle { font-family:Georgia,"Times New Roman",serif; }

.band .r b { font-size:11pt; }
.fill { background:#fef3c7; border-bottom:1.6px solid #d97706; padding:0 1px; font-weight:700; }
.uline { border-bottom:1.4px solid #1f2937; }
.ulbl { font-size:7pt; font-weight:700; color:#dc2626; vertical-align:super;
  font-family:"Hiragino Kaku Gothic ProN","IPAPGothic",sans-serif; }
.pmark { display:inline-block; background:#0f172a; color:#fff; border-radius:4px;
  font-size:8pt; font-weight:700; padding:0 6px; margin-right:6px; vertical-align:1px;
  font-family:"Hiragino Kaku Gothic ProN","IPAPGothic",sans-serif; }
.psum { font-size:9pt; color:#475569; margin:0 0 5px; }
table.fills { width:100%; border-collapse:collapse; font-size:9.1pt; margin:3px 0 8px; }
table.fills th, table.fills td { border:1px solid #cbd5e1; padding:4px 8px; vertical-align:top;
  text-align:left; }
table.fills th { background:#eef2ff; white-space:nowrap;
  font-family:"Hiragino Kaku Gothic ProN","IPAPGothic",sans-serif; }
table.fills td.k { white-space:nowrap; font-weight:700; color:#1e3a8a; }
table.fills td.a { white-space:nowrap; font-weight:700; font-family:Georgia,serif; }

/* 設問解説カード */
.qcard { border:1.4px solid #cbd5e1; border-radius:9px; padding:9px 13px; margin:9px 0 12px;
  page-break-inside:avoid; }
.qcard .qh { display:flex; align-items:baseline; gap:9px; flex-wrap:wrap; margin-bottom:4px; }
.qcard .qn { background:#1e3a8a; color:#fff; border-radius:6px; padding:2px 11px; font-size:10.5pt;
  font-weight:700; }
.qcard .qk { background:#e0e7ff; color:#1e3a8a; border-radius:4px; padding:1px 8px; font-size:8.4pt;
  font-weight:700; }
.qcard .qq { font-size:9.4pt; color:#334155; margin:2px 0 5px; line-height:1.65; }
.qcard .qt { font-family:Georgia,serif; font-size:9.9pt; background:#f8fafc; border-radius:5px;
  padding:5px 9px; margin:3px 0 6px; border-left:3px solid #94a3b8; line-height:1.6; }
.ansbox { background:#ecfdf5; border:1.4px solid #10b981; border-radius:7px; padding:6px 11px;
  margin:5px 0 7px; }
.ansbox .al { font-size:8.4pt; font-weight:700; color:#047857; margin-bottom:2px;
  font-family:"Hiragino Kaku Gothic ProN","IPAPGothic",sans-serif; }
.ansbox .av { font-size:10.4pt; font-weight:700; color:#064e3b; line-height:1.65; }
.ansbox .av .en { font-family:Georgia,serif; }
.ansbox .an { font-size:8.8pt; color:#065f46; margin-top:3px; line-height:1.6; }
.sec { margin:6px 0 0; }
.sec .sh { font-size:9.5pt; font-weight:700; margin:5px 0 2px; padding:1px 0 1px 8px;
  border-left:4px solid #1e3a8a; color:#0f172a;
  font-family:"Hiragino Kaku Gothic ProN","IPAPGothic",sans-serif; page-break-after:avoid; }
.sec.s-core .sh { border-color:#d97706; }
.sec.s-struct .sh { border-color:#dc2626; }
.sec.s-evi .sh { border-color:#047857; }
.sec.s-ng .sh { border-color:#7c3aed; }
.sec ul { margin:2px 0 0; padding-left:17px; font-size:9.2pt; line-height:1.66; color:#1f2937; }
.sec li { margin:2px 0; }
.sec .mono { font-family:Georgia,serif; font-size:9.1pt; background:#f8fafc; border-radius:4px;
  padding:4px 8px; margin:2px 0; line-height:1.62; white-space:pre-wrap; }
.evi { font-size:9.1pt; margin:3px 0; line-height:1.62; }
.evi .q { font-family:Georgia,serif; color:#065f46; font-weight:700; }
.howto { font-size:9.3pt; line-height:1.72; color:#334155; }
.howto b { color:#0f172a; }
.selfcheck { border:1.4px dashed #1e3a8a; border-radius:8px; padding:7px 12px; margin:7px 0 4px;
  font-size:9.2pt; line-height:1.7; color:#1f2937; background:#f8fafc; }
.selfcheck b { color:#1e3a8a; }
"""

RULES = [
    ("rc-svoc", "S V O C M … 文の骨組み",
     "主語 S・述語動詞 V・目的語 O・補語 C。それ以外の飾り（副詞・前置詞句）は M。"
     "従属節の中は S′ V′ O′ C′、さらに内側は S″ V″ とダッシュを増やす。"
     "助動詞は 助 として V と分けて示した。",
     "she＝S　left＝V　her silence＝O　open＝C"),
    ("rc-adv", "( ) … 副詞のカタマリ",
     "前置詞句・副詞節・分詞構文。多くは外しても文が成立するので、まず外して骨組みを見る。",
     "( under his gaze ) , ( though she didn't feel … )"),
    ("rc-noun", "[ ] … 名詞のカタマリ",
     "that 節・what 節・whether / if 節・動名詞句・不定詞の名詞用法。S / O / C になれる。外すと文が壊れる。",
     "She felt [ she'd gone past the age ] ."),
    ("rc-adj", "&lt; &gt; … 形容詞のカタマリ",
     "関係詞節・分詞の後置修飾・形容詞用法の不定詞や前置詞句。直前の名詞に線で結ぶと構造が見える。",
     "the call &lt; she'd made &gt;"),
]

STEPS = [
    "① 前から読んで <b>( ) [ ] &lt; &gt; の切れ目</b>に印を入れる。目印は「前置詞・接続詞・関係詞・-ing / -ed / to」。",
    "② カタマリを全部外し、残った<b>裸の骨組み</b>を見る。まず <b>V（述語動詞）を 1 つ</b>確定させる。",
    "③ V の前の名詞が S、後ろの名詞が O、後ろの形容詞・名詞で「S ＝ それ」なら C。",
    "④ 骨組みが決まってから<b>文型を確定</b>し、外したカタマリを「どの語にかかるか」を決めながら戻す。",
    "⑤ 最後に和訳する。<b>訳せたかではなく、S V O C を指させるか</b>で自己採点する。",
]


def band(title, sub, right):
    name = f'<div style="font-size:8.6pt;opacity:.9;margin-top:3px">{esc(STUDENT)} 君へ</div>' if STUDENT else ""
    return (f'<div class="band"><div class="l">{esc(title)}<small>{sub}</small></div>'
            f'<div class="r">{right}{name}</div></div>')


def intro_block():
    cards = "".join(
        f'<div class="rulecard {c}"><div class="rh">{h}</div><div class="rb">{b}</div>'
        f'<div class="rex">{ex}</div></div>' for c, h, b, ex in RULES)
    steps = "".join(f'<div class="step"><span class="stepno">{i}</span><div>{s[2:]}</div></div>'
                    for i, s in enumerate(STEPS, 1))
    return f"""
<div class="intro">
 <b>この冊子の使い方。</b>自分でふった文型と、ここに載っている分解図を <b>1 文ずつ</b>突き合わせること。
 ずれた文には印を付けて、<b>なぜそう取ったのか</b>を言葉にしてから解説を読む。
 それをやらずに読むと「読めば分かる」で終わって、次の初見の英文で同じ所を間違える。
 <br>★君の課題は毎回<b>「記号の範囲」</b>と<b>「訳語の精度」</b>。
 だから各文に<b>骨組み</b>（カタマリを外した後に残るもの）と<b>訳</b>を必ず付けた。
 記号を書いた後、<b>カタマリの終わりがどこか</b>を指で押さえて確認する癖をつけること。
</div>
<div class="secttl">記号のルール<span class="en2">notation</span></div>
<div class="rulegrid">{cards}</div>
<div class="secttl">構造の取り方（この順番でやる）<span class="en2">procedure</span></div>
<div class="steps">{steps}</div>
<div class="selfcheck">
 <b>自己採点の基準。</b>○＝ S V O C と文型が完全一致／△＝文型は合っているがカタマリの範囲がずれた／
 ×＝ V の取り違え・文型そのものが違う。<b>△を数えることが一番大事</b>。
 △が多い文型（特に第 5 文型と、関係詞・分詞が絡む文）が、そのまま次にやるべき単元になる。
</div>"""


def passage_html(mod):
    """本文。空所は埋めた語を黄色で、下線部は下線で示す。"""
    filled = core.apply_fills(mod.RAW, mod.FILLS)
    raw_disp = []
    placed = set()
    for i, (r, f) in enumerate(zip(mod.RAW, filled), 1):
        s = esc(r)
        for marker, word in mod.FILLS.items():
            if not word:
                s = s.replace(marker, "")
            else:
                s = s.replace(marker, f'<span class="fill">{esc(word)}</span>')
        # 印を消した跡に二重スペースが残るとアンカーが当たらない。先に潰す。
        s = re.sub(r"\s+", " ", s)
        for label, anchor, target in getattr(mod, "UNDERLINE", []):
            ea, et = esc(anchor), esc(target)
            if ea not in s:
                # ★黙って飛ばさない。飛ばすと紙から下線が消えたことに誰も気づかない
                #   （2026-08-27 に (5) の下線が実際に消えた）。
                continue
            marked = ea.replace(et, f'<span class="uline">{et}</span>'
                                    f'<span class="ulbl">({label})</span>', 1)
            s = s.replace(ea, marked, 1)
            placed.add(label)
        mark = f'<span class="pmark">{i}</span>' if len(mod.RAW) > 12 else \
               f'<span class="pmark">{"①②③④⑤⑥⑦⑧⑨⑩"[i - 1]}</span>'
        scene = getattr(mod, "SCENES", {}).get(i)
        if scene:
            raw_disp.append(f'<p style="margin-top:9px"><b>── {esc(scene)} ──</b></p>')
        raw_disp.append(f"<p>{mark}{s}</p>")
    want = {lb for lb, _a, _t in getattr(mod, "UNDERLINE", [])}
    if want - placed:
        raise ValueError(f"[{mod.META['key']}] 下線部を本文に置けなかった: "
                         f"{sorted(want - placed)}（アンカーが本文と一致していない）")
    n = len(" ".join(filled).split())
    return (f'<div class="passage">{"".join(raw_disp)}</div>'
            f'<div class="wcount">約 {n} 語　／　'
            f'<span class="fill">黄色</span>＝空所に入る語　'
            f'<span class="uline">下線</span>＝設問の下線部</div>')


def fills_table(mod):
    notes = getattr(mod, "FILL_NOTES", None)
    if not notes:
        return ""
    rows = "".join(f'<tr><td class="k">{esc(k)}</td><td class="a">{esc(a)}</td>'
                   f'<td>{n}</td></tr>' for k, a, n in notes)
    return (f'<div class="instr">構造を取るために空所を埋めてある。'
            f'（設問そのものの解説は依頼の範囲外なので、ここでは<b>根拠だけ</b>を短く示す。）</div>'
            f'<table class="fills"><tr><th>空所</th><th>入る語</th><th>根拠</th></tr>{rows}</table>')


def sent_card(no, s):
    node = core.parse(s["dsl"])
    tag = f'<span class="atag">{s["tag"]}</span>' if s.get("tag") else ""
    notes = ""
    if s.get("notes"):
        notes = ('<div class="notes"><ul>'
                 + "".join(f"<li>{n}</li>" for n in s["notes"]) + "</ul></div>")
    skel = core.render_skeleton(node)
    skel_html = (f'<div class="skel"><span class="lead">骨組み</span>{skel}</div>') if skel.strip() else ""
    return (f'<div class="acard"><div class="ah"><span class="ano">{esc(no)}</span>'
            f'<span class="apat">{esc(s["pat"])}</span>{tag}</div>'
            f'{core.render_analysis(node)}{skel_html}{notes}'
            f'<div class="jatr"><b>訳</b>{esc(s["ja"])}</div></div>')


def analysis_html(mod):
    out = []
    for para in mod.PARAS:
        scene = getattr(mod, "SCENES", {}).get(para["no"])
        if scene:
            out.append(f'<div class="partttl">{esc(scene)}</div>')
        label = ("①②③④⑤⑥⑦⑧⑨⑩"[para["no"] - 1] if len(mod.PARAS) <= 10
                 else f'第 {para["no"]} 段落')
        head = f'第 {label} 段落' if len(mod.PARAS) <= 10 else label
        out.append(f'<div class="vhd">{esc(head)}</div>')
        if para.get("sum"):
            out.append(f'<div class="psum">{esc(para["sum"])}</div>')
        for j, s in enumerate(para["sents"], 1):
            out.append(sent_card(f'{para["no"]}-{j}', s))
    return "".join(out)


def question_html(mod):
    if not getattr(mod, "QUESTIONS", None):
        return ""
    out = ['<div class="secttl">設問 解答・解説<span class="en2">answers &amp; commentary</span></div>',
           '<div class="instr">解説の形は塾の標準（<b>🎯 コアイメージ → 🔬 文構造分析 → '
           '📍 本文の根拠 → ❌ 誤答 NG 理由</b>）。記述問題には誤答の選択肢が無いので、'
           '4 つ目は「よくある誤り」として同じ位置に置いてある。</div>']
    for q in mod.QUESTIONS:
        secs = []
        secs.append('<div class="sec s-core"><div class="sh">🎯 コアイメージ</div><ul>'
                    + "".join(f"<li>{x}</li>" for x in q["core"]) + "</ul></div>")
        secs.append('<div class="sec s-struct"><div class="sh">🔬 文構造分析</div>'
                    + "".join(f'<div class="mono">{x}</div>' for x in q["struct"]) + "</div>")
        evi = "".join(f'<div class="evi">・<span class="q">"{esc(a)}"</span> — {b}</div>'
                      for a, b in q["evidence"])
        secs.append(f'<div class="sec s-evi"><div class="sh">📍 本文の根拠</div>{evi}</div>')
        ng_title = "❌ 誤答 NG 理由" if q["kind"].startswith(("空所", "内容補充")) else "❌ よくある誤り"
        secs.append(f'<div class="sec s-ng"><div class="sh">{ng_title}</div><ul>'
                    + "".join(f"<li>{x}</li>" for x in q["ng"]) + "</ul></div>")
        an = f'<div class="an">{q["ansnote"]}</div>' if q.get("ansnote") else ""
        out.append(
            f'<div class="qcard"><div class="qh"><span class="qn">{esc(q["no"])}</span>'
            f'<span class="qk">{esc(q["kind"])}</span></div>'
            f'<div class="qq">{esc(q["q"])}</div>'
            f'<div class="qt">{esc(q["target"])}</div>'
            f'<div class="ansbox"><div class="al">解答</div>'
            f'<div class="av">{esc(q["ans"])}</div>{an}</div>'
            + "".join(secs) + "</div>")
    return "".join(out)


def part_html(mod, first=False):
    m = mod.META
    cls = "partdiv first" if first else "partdiv"
    out = [f'<div class="{cls}"><div class="pt1">{esc(m["school"])} {esc(m["year"])} '
           f'{esc(m["qno"])}</div><div class="pt2">{esc(m["title"])}　{esc(m["author"])}</div></div>',
           f'<div class="ptitle">{esc(m["title"])}</div>'
           f'<div class="pjtitle">{esc(m["jtitle"])}</div>',
           f'<div class="instr">{m["lead"]}</div>',
           '<div class="secttl">本文<span class="en2">passage</span></div>',
           passage_html(mod), fills_table(mod),
           '<div class="secttl pb">全文 構造解析<span class="en2">SVOCM breakdown</span></div>',
           analysis_html(mod)]
    q = question_html(mod)
    if q:
        out.append('<div class="pb"></div>')
        out.append(q)
    return "".join(out)


def main():
    no_pdf = "--no-pdf" in sys.argv

    print("=" * 68)
    print("ビルド前ゲート")
    print("=" * 68)
    if gate.main() != 0:
        print("\n✗ ゲートが落ちたのでビルドしない。")
        return 1

    import content_keio2018 as K, content_todai2018 as T
    n_sent = sum(len(p["sents"]) for m in (K, T) for p in m.PARAS)

    body = (band("英文構造解析 ─ SVOCM 総ざらい",
                 "慶應義塾大学 経済学部 2018 大問 I ／ 東京大学 2018 第 5 問",
                 f"<b>解析 {n_sent} 文</b><br>全文・全設問")
            + intro_block()
            + part_html(K, first=True)
            + part_html(T)
            + '<div class="foot">トリリオン AI 塾　英文構造解析プリント　'
              '／ 本文は配布された過去問プリントの印字に一致（機械照合済み）</div>')

    os.makedirs(OUT_DIR, exist_ok=True)
    doc = core.hb.doc("英文構造解析 SVOCM ─ 慶應経済2018 I ／ 東大2018 第5問", body)
    doc = doc.replace("</style>", EXTRA_CSS + "</style>")

    html_path = os.path.join(OUT_DIR, "svoc_kaisetsu.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"\n✓ HTML: {html_path}  ({len(doc):,} bytes)")

    if no_pdf:
        print("  （--no-pdf なので PDF は作らない）")
        return 0
    pdf_path = os.path.join(OUT_DIR, "英文構造解析_慶應経済2018-1_東大2018-5.pdf")
    if core.render_pdf(doc, pdf_path, "トリリオン AI 塾 ／ 英文構造解析 SVOCM"):
        print(f"✓ PDF : {pdf_path}  ({os.path.getsize(pdf_path):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
