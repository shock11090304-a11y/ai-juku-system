# -*- coding: utf-8 -*-
"""content.py から、画面で読める1枚の HTML を書き出す（Artifact 用のプレビュー）。

    python3 make_preview.py [出力先.html]

★PDF は Chrome + Arial Unicode を使うので塾長の Mac でしか刷れない。
  中身を先に確かめたいとき・出先で読みたいときのために、同じ content.py から
  画面用の 1 枚を機械生成する。**紙と画面で中身がずれることはない**（正典が同じ）。
  答えの表示・非表示を切り替えられるので、問題編と解答編の両方の見え方を確かめられる。
"""
import html
import os
import sys

from layout import SYN_VOCAB, parse, plain_text, top_segments
from content import (
    META, NOTATION, PART1, PART2, PART3, RULES, RULE_EXAMPLES, STEPS, SYN_POOL,
)

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
esc = lambda s: html.escape(str(s), quote=False)

LBL_CLS = {"S": "s", "V": "v", "O": "o", "O1": "o", "O2": "o", "C": "c", "M": "m",
           "真S": "s", "真O": "o", "同格": "x", "挿入": "k", "強調": "c", "接": "k", "助": "v"}
BR_CLS = {"(": "adv", "[": "noun", "<": "adj"}


def lbl_cls(lbl):
    return LBL_CLS.get(lbl.replace("'", ""), "x")


def cell(word, label, wcls="", lcls=""):
    return (f'<span class="ck"><span class="wt {wcls}">{word}</span>'
            f'<span class="lb {lcls}">{label}</span></span>')


def bunkai(node):
    """分解図。紙の render_analysis と同じ見た目を画面用の class で出す。"""
    def walk(nd):
        buf = []
        for k in nd.kids:
            if k.kind == "chunk":
                buf.append(cell(esc(k.text), esc(k.label), lcls=lbl_cls(k.label)))
            elif k.kind == "plain":
                buf.append(cell(esc(k.text), "&nbsp;", wcls="pl"))
            else:
                kind = BR_CLS[k.text]
                close = {"(": ")", "[": "]", "<": ">"}[k.text]
                buf.append(cell(esc(k.text), "&nbsp;", wcls=f"br br-{kind}"))
                buf.append(walk(k))
                buf.append(cell(esc(close), esc(k.label) if k.label else "&nbsp;",
                                wcls=f"br br-{kind}", lcls=lbl_cls(k.label)))
        return "".join(buf)
    return f'<div class="bunkai">{walk(node)}</div>'


def drill(segs):
    words = " ".join(
        f'<span class="seg"><span class="mk">{CIRCLED[i]}</span>{esc(t)}</span>'
        for i, (_l, t, _u) in enumerate(segs))
    head = "".join(f'<th>{CIRCLED[i]}</th>' for i in range(len(segs)))
    body = "".join(f'<td class="{lbl_cls(l)}">{esc(l)}</td>' for l, _t, _u in segs)
    return (f'<p class="en drillen">{words}</p>'
            f'<div class="ansbox"><table class="slots"><tr>{head}</tr>'
            f'<tr>{body}</tr></table></div>')


def notes_html(ns):
    return '<ul class="notes">' + "".join(f"<li>{n}</li>" for n in ns) + "</ul>"


def item_card(no, it, kind):
    root = parse(it["dsl"])
    h = [f'<article class="item" id="{esc(it["id"])}">',
         '<div class="ihead">',
         f'<span class="no">{no}</span>',
         f'<span class="syn">{esc(SYN_VOCAB.get(it["syn"], it["syn"]))}</span>',
         f'<span class="ansonly pat">{esc(it["pat"])}</span>',
         f'<span class="ansonly tag">{esc(it["tag"])}</span>',
         '</div>']
    if kind == "drill":
        h.append(drill(top_segments(root)))
    else:
        h.append(f'<p class="en">{esc(it["en"])}</p>')
    if kind == "mcq":
        h.append(f'<p class="q">{it["q"]}</p><ol class="choices">')
        for ci, c in enumerate(it["choices"]):
            mark = " correct ansonly-mark" if ci == it["ans"] else ""
            h.append(f'<li class="{mark.strip()}"><span class="cn">{CIRCLED[ci]}</span>{c}</li>')
        h.append("</ol>")
    h.append('<div class="ansonly">')
    h.append(bunkai(root))
    if kind == "mcq":
        h.append(f'<p class="expl"><b>正解 {CIRCLED[it["ans"]]}</b>　{it["exp"]}</p>')
    h.append(notes_html(it["notes"]))
    h.append(f'<p class="ja"><span class="rubric">和訳</span>{esc(it["ja"])}</p>')
    if it.get("points"):
        h.append('<div class="pts"><span class="rubric">採点ポイント</span><ul>'
                 + "".join(f"<li>{esc(p)}</li>" for p in it["points"]) + "</ul></div>")
    h.append("</div></article>")
    return "\n".join(h)


def build():
    n1 = sum(len(g["items"]) for g in PART1)
    n3 = sum(len(g["items"]) for g in PART3)
    total = n1 + len(PART2) + n3
    nsyn = len({x["syn"] for g in PART1 for x in g["items"]}
               | {q["syn"] for q in PART2}
               | {x["syn"] for g in PART3 for x in g["items"]})

    h = [f'<title>{esc(META["title"])}</title>', STYLE,
         '<header class="top">',
         f'<p class="eyebrow">{esc(META["level"])}</p>',
         f'<h1>{esc(META["title"])}</h1>',
         f'<p class="lede">{esc(META["sub"])}</p>',
         '<div class="topbar">',
         f'<dl class="stats">'
         f'<div><dt>判別</dt><dd>{n1}</dd></div>'
         f'<div><dt>構造4択</dt><dd>{len(PART2)}</dd></div>'
         f'<div><dt>英文解釈</dt><dd>{n3}</dd></div>'
         f'<div><dt>収録構文</dt><dd>{nsyn}</dd></div></dl>',
         '<button id="toggle" type="button" aria-pressed="true">解答を隠す</button>',
         '</div>',
         '<p class="disclaimer">本文は狙った構文を含めるために書き下ろした本教材オリジナルの英文で、'
         '実際の入試問題ではない。</p>',
         '</header>', '<main>']

    # 巻頭
    h.append('<section class="sect"><h2><span class="secno">凡例</span>記号のルール</h2>')
    h.append('<div class="rules">')
    for r in RULES:
        h.append(f'<div class="rule r-{r["cls"][-4:]}"><h3>{r["h"]}</h3><p>{r["b"]}</p>'
                 f'<p class="ex">{r["ex"]}</p></div>')
    h.append("</div>")
    h.append('<ol class="steps">' + "".join(f"<li>{s}</li>" for s in STEPS) + "</ol>")
    h.append('<h3 class="sub">記号の書き方（この教材の約束）</h3>'
             '<div class="scroll"><table class="notation"><tbody>')
    for k, b, ex in NOTATION:
        h.append(f'<tr><th>{esc(k)}</th><td>{b}</td><td class="ex">{ex}</td></tr>')
    h.append("</tbody></table></div>")
    h.append('<h3 class="sub">記号の使い方（見本）</h3>')
    for i, ex in enumerate(RULE_EXAMPLES, 1):
        h.append(f'<div class="sample"><div class="ihead"><span class="no">見本 {i}</span>'
                 f'<span class="pat">{esc(ex["pat"])}</span></div>')
        h.append(bunkai(parse(ex["dsl"])))
        h.append(f'<p class="note">{ex["note"]}</p></div>')
    h.append("</section>")

    # 第1部
    h.append(f'<section class="sect"><h2><span class="secno">第 1 部</span>SVOCM 判別'
             f'<span class="cnt">{n1} 問</span></h2>'
             '<p class="instr">①②③… に区切った各部分が S・V・O・C・M のどれかを答え、'
             '最後に文型を確定する。記号は 1 か所につき 1 つに決まる。</p>')
    n = 0
    for grp in PART1:
        h.append(f'<h3 class="grp">{esc(grp["g"])}<span>{esc(grp["sub"])}</span></h3>')
        for it in grp["items"]:
            n += 1
            h.append(item_card(n, it, "drill"))
    h.append("</section>")

    # 第2部
    h.append(f'<section class="sect"><h2><span class="secno">第 2 部</span>構造判断の 4 択'
             f'<span class="cnt">{len(PART2)} 問</span></h2>'
             '<p class="instr">どの語にかかるか・何が主語か・その語の働きは何かを決める。</p>')
    for qi, q in enumerate(PART2, 1):
        h.append(item_card(qi, q, "mcq"))
    h.append("</section>")

    # 第3部
    h.append(f'<section class="sect"><h2><span class="secno">第 3 部</span>英文解釈'
             f'<span class="cnt">{n3} 文</span></h2>'
             '<p class="instr">( ) [ ] &lt; &gt; でカタマリを囲み、記号を書き込んでから和訳する。'
             '訳が合っていても記号がずれていれば「読めた」ではない。</p>')
    m = 0
    for grp in PART3:
        h.append(f'<h3 class="grp">{esc(grp["g"])}<span>{esc(grp["sub"])}</span></h3>')
        for it in grp["items"]:
            m += 1
            h.append(item_card(m, it, "kaishaku"))
    h.append("</section>")

    # 巻末
    rows = []
    n = 0
    for grp in PART1:
        for it in grp["items"]:
            n += 1
            rows.append((it["syn"], f"第1部 {n}"))
    for qi, q in enumerate(PART2, 1):
        rows.append((q["syn"], f"第2部 {qi}"))
    m = 0
    for grp in PART3:
        for it in grp["items"]:
            m += 1
            rows.append((it["syn"], f"第3部 {m}"))
    by = {}
    for syn, where in rows:
        by.setdefault(syn, []).append(where)
    h.append(f'<section class="sect"><h2><span class="secno">巻末</span>収録構文一覧'
             f'<span class="cnt">{len(by)} 構文</span></h2>'
             '<p class="instr">解き直すときは、間違えた問題と同じ構文の問題をここから探す。</p>'
             '<div class="scroll"><table class="index"><tbody>')
    for syn, where in sorted(by.items(), key=lambda x: SYN_VOCAB.get(x[0], x[0])):
        pool = next((k for k, v in SYN_POOL.items() if syn in v), "")
        h.append(f'<tr><th>{esc(SYN_VOCAB.get(syn, syn))}</th>'
                 f'<td class="where">{esc("　".join(where))}</td>'
                 f'<td class="slug">{esc(syn)}</td><td class="slug">{esc(pool)}</td></tr>')
    h.append("</tbody></table></div></section>")
    h.append("</main>")
    h.append(f'<footer><p>{esc(META["brand"])}　{esc(META["title"])}　'
             f'全 {total} 問　{esc(META["level"])}</p></footer>')
    h.append(SCRIPT)
    return "\n".join(h)


STYLE = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>
:root{
  --paper:#f5f6f8; --card:#ffffff; --panel:#eceff4; --line:#d7dce4;
  --ink:#171a21; --ink2:#4a5261; --ink3:#79808f;
  --navy:#1e3a8a; --navy-soft:#e6eaf6;
  --s:#1d4ed8; --v:#c62828; --o:#04724d; --c:#a05a06; --m:#616b7d;
  --k:#8127c8; --x:#0d6a63;
  --adv:#616b7d; --noun:#04724d; --adj:#7c3aed;
  --ok:#0f7b52;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#101319; --card:#171b23; --panel:#1e232c; --line:#2c3440;
  --ink:#e6e9ef; --ink2:#aab2c0; --ink3:#7c8593;
  --navy:#9db4ee; --navy-soft:#1c2740;
  --s:#7ba2ff; --v:#ff8a8a; --o:#4fd0a0; --c:#e8b160; --m:#98a2b3;
  --k:#c79bff; --x:#5ec8bf; --adv:#98a2b3; --noun:#4fd0a0; --adj:#c79bff;
  --ok:#4fd0a0;
}}
:root[data-theme="dark"]{
  --paper:#101319; --card:#171b23; --panel:#1e232c; --line:#2c3440;
  --ink:#e6e9ef; --ink2:#aab2c0; --ink3:#7c8593;
  --navy:#9db4ee; --navy-soft:#1c2740;
  --s:#7ba2ff; --v:#ff8a8a; --o:#4fd0a0; --c:#e8b160; --m:#98a2b3;
  --k:#c79bff; --x:#5ec8bf; --adv:#98a2b3; --noun:#4fd0a0; --adj:#c79bff;
  --ok:#4fd0a0;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);
  font-family:"Zen Kaku Gothic New",system-ui,-apple-system,"Hiragino Kaku Gothic ProN",sans-serif;
  line-height:1.8;font-size:15px;margin:0;padding:0 20px 72px;
  -webkit-font-smoothing:antialiased}
main,header.top,footer{max-width:940px;margin:0 auto}
.en,.bunkai,.ex,.slug{font-family:"Source Serif 4",Georgia,"Times New Roman",serif}

header.top{padding:56px 0 26px;border-bottom:2px solid var(--ink)}
.eyebrow{font-size:11.5px;letter-spacing:.16em;color:var(--navy);font-weight:700;margin:0 0 10px}
h1{font-size:clamp(30px,5.4vw,46px);line-height:1.24;margin:0;font-weight:700;
  letter-spacing:-.01em;text-wrap:balance}
.lede{color:var(--ink2);margin:10px 0 0;font-size:16px;max-width:60ch}
.topbar{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-end;
  justify-content:space-between;margin-top:26px}
.stats{display:flex;gap:26px;margin:0;flex-wrap:wrap}
.stats div{display:flex;flex-direction:column;gap:2px}
.stats dt{font-size:11px;letter-spacing:.1em;color:var(--ink3);font-weight:500}
.stats dd{margin:0;font-size:26px;font-weight:700;line-height:1;
  font-variant-numeric:tabular-nums;color:var(--navy)}
#toggle{font:inherit;font-size:13px;font-weight:700;cursor:pointer;
  background:var(--navy);color:var(--paper);border:2px solid var(--navy);
  border-radius:999px;padding:8px 20px;transition:background .12s,color .12s}
#toggle[aria-pressed="false"]{background:transparent;color:var(--navy)}
#toggle:focus-visible{outline:3px solid var(--c);outline-offset:2px}
.disclaimer{font-size:12px;color:var(--ink3);margin:20px 0 0}

.sect{margin:52px 0 0}
h2{font-size:22px;margin:0 0 6px;display:flex;align-items:baseline;gap:14px;
  flex-wrap:wrap;font-weight:700;padding-bottom:10px;border-bottom:1px solid var(--line)}
.secno{background:var(--navy);color:var(--paper);font-size:12px;font-weight:700;
  padding:4px 12px;border-radius:4px;letter-spacing:.04em}
h2 .cnt{margin-left:auto;font-size:12.5px;color:var(--ink3);font-weight:500;
  font-variant-numeric:tabular-nums}
.instr{color:var(--ink2);font-size:14px;margin:12px 0 22px;max-width:66ch}
h3.grp{font-size:16px;margin:34px 0 14px;font-weight:700;
  border-left:4px solid var(--navy);padding-left:11px}
h3.grp span{font-weight:400;font-size:12.5px;color:var(--ink3);margin-left:12px}
h3.sub{font-size:15px;margin:32px 0 12px;font-weight:700;color:var(--ink)}

.rules{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:18px 0}
.rule{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:13px 15px}
.rule h3{margin:0 0 5px;font-size:14.5px;font-weight:700}
.rule p{margin:0;font-size:13px;color:var(--ink2);line-height:1.72}
.rule .ex{margin-top:7px;color:var(--ink);font-size:13.5px}
.r-svoc h3{color:var(--navy)} .r-adv h3{color:var(--adv)}
.r-noun h3{color:var(--noun)} .r-adj h3{color:var(--adj)}
.steps{margin:20px 0;padding:0;list-style:none;counter-reset:st;
  display:flex;flex-direction:column;gap:9px}
.steps li{counter-increment:st;position:relative;padding-left:44px;font-size:14px;color:var(--ink2)}
.steps li::before{content:"STEP " counter(st);position:absolute;left:0;top:3px;
  font-size:9.5px;font-weight:700;color:var(--paper);background:var(--ink);
  padding:2px 6px;border-radius:3px;letter-spacing:.04em}

.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%}
.notation th,.notation td,.index th,.index td{border:1px solid var(--line);
  padding:8px 12px;vertical-align:top;text-align:left;font-size:13px;line-height:1.7}
.notation th,.index th{background:var(--panel);color:var(--navy);font-weight:700;
  white-space:nowrap;width:1%}
.notation td.ex,.index .slug{color:var(--ink2);font-size:13px}
.index .where{font-variant-numeric:tabular-nums;color:var(--ink2)}
.index .slug{color:var(--ink3);font-size:12px;white-space:nowrap}

.item,.sample{background:var(--card);border:1px solid var(--line);border-radius:8px;
  padding:15px 17px;margin:0 0 12px}
.ihead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:9px}
.no{background:var(--ink);color:var(--paper);font-size:12px;font-weight:700;
  border-radius:4px;padding:2px 10px;font-variant-numeric:tabular-nums}
.syn{font-size:11.5px;font-weight:700;color:var(--navy);background:var(--navy-soft);
  padding:2px 9px;border-radius:4px}
.pat{font-size:13px;font-weight:700;color:var(--ink)}
.tag{font-size:11.5px;color:var(--c);border:1px solid currentColor;
  padding:1px 8px;border-radius:4px}
.en{font-size:17.5px;line-height:1.85;margin:6px 0 10px;color:var(--ink)}
.drillen .seg{white-space:normal}
.drillen .mk{color:var(--v);font-weight:700;font-size:11px;vertical-align:.42em;
  margin-right:2px;font-family:"Zen Kaku Gothic New",sans-serif}
.slots{width:auto;margin:2px 0 4px}
.slots th,.slots td{border:1px solid var(--line);padding:3px 0;min-width:38px;
  text-align:center;font-size:12px}
.slots th{background:var(--panel);color:var(--ink2);font-weight:500}
.slots td{font-weight:700;font-size:14px}
.slots td.s{color:var(--s)} .slots td.v{color:var(--v)} .slots td.o{color:var(--o)}
.slots td.c{color:var(--c)} .slots td.m{color:var(--m)} .slots td.x{color:var(--x)}
.slots td.k{color:var(--k)}

.bunkai{background:var(--panel);border-radius:7px;padding:10px 12px 6px;margin:10px 0;
  font-size:15.5px;line-height:1.4;overflow-x:auto}
.ck{display:inline-block;text-align:center;vertical-align:bottom;margin:0 1.5px 4px}
.ck .wt{display:block;white-space:nowrap}
.ck .wt.pl{color:var(--ink2)}
.ck .wt.br{font-weight:700}
.wt.br-adv{color:var(--adv)} .wt.br-noun{color:var(--noun)} .wt.br-adj{color:var(--adj)}
.ck .lb{display:block;font-size:9.5px;font-weight:700;line-height:1.2;letter-spacing:.02em;
  font-family:"Zen Kaku Gothic New",sans-serif}
.lb.s{color:var(--s)} .lb.v{color:var(--v)} .lb.o{color:var(--o)} .lb.c{color:var(--c)}
.lb.m{color:var(--m)} .lb.k{color:var(--k)} .lb.x{color:var(--x)}

.q{font-size:14.5px;margin:8px 0 8px;font-weight:500}
.choices{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:5px}
.choices li{font-size:14px;color:var(--ink2);padding:5px 10px;border-radius:5px;
  border:1px solid transparent;display:flex;gap:9px;line-height:1.72}
.choices .cn{color:var(--ink3);font-weight:700;flex:0 0 auto}
.choices li.correct{border-color:var(--ok);background:color-mix(in srgb,var(--ok) 9%,transparent);
  color:var(--ink)}
.choices li.correct .cn{color:var(--ok)}
.expl{font-size:13.5px;color:var(--ink2);margin:10px 0 0;line-height:1.82}
.expl b{color:var(--ok)}
.notes{margin:10px 0 0;padding-left:19px;font-size:13.5px;color:var(--ink2);line-height:1.82}
.notes li{margin:4px 0}
.notes b{color:var(--ink)}
.ja,.pts{background:var(--panel);border-radius:6px;padding:8px 12px;margin:11px 0 0;
  font-size:13.5px;color:var(--ink2);line-height:1.8}
.rubric{display:inline-block;font-size:10.5px;font-weight:700;color:var(--navy);
  letter-spacing:.08em;margin-right:9px}
.pts ul{margin:5px 0 0;padding-left:19px}
.pts li{margin:3px 0}
.sample .note{font-size:13.5px;color:var(--ink2);margin:8px 0 0;line-height:1.8}

body.hide-answers .ansonly{display:none}
body.hide-answers .choices li.correct{border-color:transparent;background:transparent;
  color:var(--ink2)}
body.hide-answers .choices li.correct .cn{color:var(--ink3)}

footer{margin-top:60px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--ink3);font-size:12px;text-align:center}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media (max-width:620px){
  body{font-size:14.5px;padding:0 14px 56px}
  .en{font-size:16px}
  .stats{gap:18px}.stats dd{font-size:21px}
}
</style>"""

SCRIPT = """<script>
(function(){
  var b=document.body, t=document.getElementById('toggle'), KEY='svocm-hide-answers';
  function apply(hide){
    b.classList.toggle('hide-answers',hide);
    t.setAttribute('aria-pressed',String(!hide));
    t.textContent = hide ? '解答を表示' : '解答を隠す';
  }
  var saved=false;
  try{ saved = localStorage.getItem(KEY)==='1'; }catch(e){}
  apply(saved);
  t.addEventListener('click',function(){
    var hide=!b.classList.contains('hide-answers');
    apply(hide);
    try{ localStorage.setItem(KEY,hide?'1':'0'); }catch(e){}
  });
})();
</script>"""


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_preview.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"WROTE {out} ({os.path.getsize(out):,} bytes)")
