# -*- coding: utf-8 -*-
"""共通テスト 第4問（古文）類似問題のビルダー
   問題編＝縦書き（本番と同じ体裁）／解答解説編＝横書き（自塾の解説体裁）
   HTML → Headless Chrome → PDF → PyMuPDF でフッター付与"""
import html, re, os, sys, json, subprocess
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND = "TRILLION AI 学習塾"
CIRC = "①②③④⑤"

def E(s): return html.escape(str(s), quote=False)

# ---------------------------------------------------------------- 問題編（縦書き）
CSS_Q = """
@page { size: A4; margin: 15mm 13mm 15mm 13mm; }
* { box-sizing: border-box; }
/* 本文全体を縦組みにする。固定高さの縦ブロックは改ページで内容が落ちるため使わない */
html, body { writing-mode: vertical-rl; margin: 0; color: #111;
             font-family: "Hiragino Mincho ProN", "YuMincho", "MS Mincho", serif;
             font-size: 10.4pt; line-height: 1.95; line-break: strict; word-break: normal; }
p { margin: 0; text-indent: 1em; }
.gothic { font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif; }
.pb { break-before: page; }
.daimon { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 15pt; letter-spacing: .12em;
          margin-left: 6px; text-indent: 0; }
.spec { font-family: "Hiragino Sans", sans-serif; font-size: 9.5pt; color: #333; margin-left: 10px; text-indent: 0; }
.namebox { border: 1px solid #64748b; padding: 5px 4px; margin-left: 10px; font-family: "Hiragino Sans", sans-serif;
           font-size: 9pt; color: #334155; text-indent: 0; }
.lead { border: 1px solid #64748b; padding: 7px 6px; margin-left: 10px; font-size: 9.8pt; line-height: 1.85; text-indent: 0; }
.body-oo { margin-left: 12px; }
.u { text-decoration: underline; text-underline-offset: 5px; }
.w { text-decoration: underline wavy; text-underline-offset: 6px; }
.tcy { text-combine-upright: all; }        /* 数字・ラテン文字は1マスに収める（縦中横） */
.cmb { text-combine-upright: all; }        /* 傍線の (ア)(Ａ) は1マスに収める */
.mk { font-family: "Hiragino Sans", sans-serif; font-size: 8.5pt; }
.rb { white-space: nowrap; }
.ansno { display: inline-block; border: 1.2px solid #0f172a; padding: 0 2px; font-family: "Hiragino Sans", sans-serif;
         font-size: 8.5pt; text-combine-upright: all; }
.qh { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 10.2pt; text-indent: 0; margin-left: 4px; }
.ch { text-indent: 0; padding-top: .6em; break-inside: avoid; }
.ch.gap { margin-right: 22px; }             /* 会話文・資料と選択肢の間を空ける */
.note-t { font-size: 9pt; line-height: 1.75; padding-top: 1.6em; text-indent: -1.6em; }  /* 縦組みの字下げは padding-top で相殺する */
.note-t.qh { padding-top: 0; text-indent: 0; margin-left: 8px; }
.talk { border: 1px solid #64748b; padding: 6px 6px; margin-left: 8px; font-size: 9.6pt; line-height: 1.85; text-indent: 0; }
"""

def tate_text(s):
    """本文の記号を縦書き用のマークアップへ。傍線 a/b/c、波線 w、場面 x/y"""
    t = re.sub(r"(\d+)", r'<span class="tcy">\1</span>', E(s))   # (注12) などの数字を正立させる
    t = re.sub(r"([一-龥々]{1,6}\([ぁ-ん]+\))", r'<span class="rb">\1</span>', t)   # 読み仮名を行またぎさせない
    t = re.sub(r"\{\{a\}\}(.*?)\{\{/a\}\}", r'<span class="u">\1</span><span class="cmb mk">(ア)</span>', t)
    t = re.sub(r"\{\{b\}\}(.*?)\{\{/b\}\}", r'<span class="u">\1</span><span class="cmb mk">(イ)</span>', t)
    t = re.sub(r"\{\{c\}\}(.*?)\{\{/c\}\}", r'<span class="u">\1</span><span class="cmb mk">(ウ)</span>', t)
    t = re.sub(r"\{\{w\}\}(.*?)\{\{/w\}\}", r'<span class="w">\1</span>', t)
    t = re.sub(r"\{\{x\}\}(.*?)\{\{/x\}\}", r'<span class="u">\1</span><span class="cmb mk">(A)</span>', t)
    t = re.sub(r"\{\{y\}\}(.*?)\{\{/y\}\}", r'<span class="u">\1</span><span class="cmb mk">(B)</span>', t)
    return "".join(f"<p>{ln.strip()}</p>" for ln in t.split("\n") if ln.strip())

def tcy(s):
    """縦組みの中の半角数字・ラテン文字を正立させる（縦に並べる）"""
    return re.sub(r"([0-9]+|[A-Za-z])", r'<span class="tcy">\1</span>', E(s))

def nums_html(nums):
    return "・".join(f'<span class="ansno">{n.strip()}</span>' for n in re.split(r"[・,、]", nums) if n.strip())

def problem_html(sets):
    b = []
    for si, S in enumerate(sets):
        b.append(f'<p class="daimon{"" if si == 0 else " pb"}">第四問（古文）　類似問題　第<span class="tcy">{S["id"]}</span>回</p>')
        b.append(f'<p class="spec">配点四五点／解答番号 <span class="tcy">23</span>〜<span class="tcy">29</span>／解答時間の目安 <span class="tcy">{S.get("minutes", 20)}</span>分</p>')
        b.append('<p class="namebox">氏名　　　　　　　　　　　　　　　得点　　　　／四五</p>')
        b.append(f'<p class="lead">{tcy(S["lead"])}</p>')
        b.append(f'<div class="body-oo">{tate_text(S["passage"])}</div>')
        b.append('<p class="note-t qh pb">（注）</p>')   # 注は1ページにまとめる（両題で体裁をそろえる）
        for ni, n in enumerate(S["notes"], 1):
            b.append(f'<p class="note-t"><span class="tcy">{ni}</span>　{tcy(n["word"])}　――　{tcy(n["gloss"])}</p>')
        for q in S["questions"]:
            cls = "qh pb" if q["no"] == 1 else "qh"
            b.append(f'<p class="{cls}">問<span class="tcy">{q["no"]}</span>（解答番号{nums_html(q["nums"])}・{tcy(q["points"])}）</p>')
            for line in tcy(q["text"]).split("\n"):
                if line.strip(): b.append(f'<p>{line.strip()}</p>')
            for it in q["items"]:
                if it["label"]: b.append(f'<p class="qh">{E(it["label"])}</p>')
                for i, c in enumerate(it["choices"]):
                    gap = " gap" if (q["no"] == 5 and i == 0) else ""
                    b.append(f'<p class="ch{gap}">{CIRC[i]}　{tcy(c)}</p>')
    return "".join(b)

# ---------------------------------------------------------------- 解答解説編（横書き）
CSS_A = """
@page { size: A4; margin: 12mm 14mm 17mm 14mm; }
* { box-sizing: border-box; }
body { margin: 0; color: #0f172a; font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif; font-size: 12px; line-height: 1.65; line-break: strict; orphans: 2; widows: 2; }
.mincho { font-family: "Hiragino Mincho ProN", "YuMincho", serif; }
.pb { break-before: page; }
.head { background: #1e3a8a; color: #fff; border-radius: 6px; padding: 8px 16px; display: flex; justify-content: space-between; align-items: baseline; }
.head .t { font-size: 17px; font-weight: 700; }
.head .r { font-size: 11px; }
.sub { margin: 7px 0 3px; font-size: 12.5px; color: #1e293b; }
.meta { font-size: 11px; color: #64748b; margin-bottom: 8px; }
.sec { border-left: 5px solid #1e3a8a; padding: 2px 10px; margin: 13px 0 7px; font-size: 14px; font-weight: 700; color: #1e3a8a; break-after: avoid; }
.sec small { color: #64748b; font-weight: 400; font-size: 10.5px; margin-left: 8px; }
table.key { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 11px; }
table.key th, table.key td { border: 1px solid #cbd5e1; padding: 3px 7px; vertical-align: top; }
table.key th { background: #f1f5f9; text-align: center; }
table.key td.c { text-align: center; white-space: nowrap; }
table.key td.a { text-align: center; color: #1e3a8a; font-weight: 700; font-size: 13px; }
.qa { border: 1px solid #cbd5e1; border-radius: 6px; margin: 0 0 9px; }
.qa .qh { background: #eef2ff; color: #1e3a8a; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 6px 6px 0 0; }
.qa .qb { padding: 6px 11px 8px; }
.qa .qt { font-size: 11.5px; color: #334155; margin-bottom: 4px; }
.qa .ans { font-size: 12.5px; font-weight: 700; color: #1e3a8a; margin-bottom: 3px; }
.qa .exp { font-size: 11.4px; line-height: 1.75; }
.qa .rules { font-size: 10.5px; color: #1e3a8a; margin-top: 3px; }
.tr { display: flex; gap: 9px; margin: 0 0 7px; break-inside: avoid; }
.tr .n { flex: 0 0 22px; height: 22px; border-radius: 50%; background: #1e3a8a; color: #fff; font-size: 10.5px; font-weight: 700; text-align: center; line-height: 22px; }
.tr .b { flex: 1; }
.tr .o { font-family: "Hiragino Mincho ProN", serif; font-size: 11.8px; line-height: 1.8; color: #334155; background: #f8fafc; border-left: 3px solid #94a3b8; padding: 4px 9px; }
.nb { white-space: nowrap; }
.tr .j { font-size: 11.6px; line-height: 1.8; margin-top: 3px; }
table.gr { width: 100%; border-collapse: collapse; font-size: 11px; }
table.gr td { border-bottom: 1px solid #e2e8f0; padding: 3px 7px; vertical-align: top; }
table.gr td.w { width: 30%; font-family: "Hiragino Mincho ProN", serif; font-weight: 700; }
table.rl { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 8px; }
table.rl td, table.rl th { border: 1px solid #cbd5e1; padding: 3px 7px; vertical-align: top; }
table.rl th { background: #f1f5f9; text-align: left; }
table.rl td.r { white-space: nowrap; width: 210px; color: #1e3a8a; font-weight: 700; }
.note { border: 1px dashed #94a3b8; border-radius: 5px; padding: 5px 10px; font-size: 10.5px; color: #475569; margin: 6px 0 8px; break-inside: avoid; }
.src { font-size: 10.5px; color: #475569; word-break: break-all; }
"""

def plain(s):
    return re.sub(r"\{\{/?[abcwxy]\}\}", "", s)

def nb(s):
    """解説編の原文で、読み仮名と注番号が行をまたいで割れないようにする"""
    t = E(s)
    t = re.sub(r"([一-龥々]{1,6}\([ぁ-ん]+\))", r'<span class="nb">\1</span>', t)
    t = re.sub(r"([（(][注＊]\d+[)）])", r'<span class="nb">\1</span>', t)
    return t

def answer_html(sets):
    b = []
    for si, S in enumerate(sets):
        pb = "" if si == 0 else "pb"
        b.append(f'<div class="{pb}">')
        b.append(f'<div class="head"><span class="t">第4問（古文）類似問題 第{S["id"]}回　解答・解説</span>'
                 f'<span class="r">配点45点／解答番号 23〜29</span></div>')
        b.append(f'<div class="sub">{E(S["title"])}</div>')
        b.append(f'<div class="meta">出典：{E(S["work"])}（{E(S["genre"])}・{E(S["era"])}）　／　解答一覧 ／ 設問別解説 ／ 全文現代語訳 ／ 重要文法 ／ 使うルール</div>')
        # 解答一覧
        b.append('<div class="sec">解答一覧<small>Answer Key（満点45点）</small></div>')
        b.append('<table class="key"><tr><th style="width:70px">設問</th><th style="width:80px">解答番号</th><th style="width:60px">配点</th><th style="width:60px">正解</th><th>参照ルール</th></tr>')
        for q in S["questions"]:
            nums = [x.strip() for x in re.split(r"[・,、]", q["nums"]) if x.strip()]
            for i, it in enumerate(q["items"]):
                lab = f'問{q["no"]}{it["label"]}' if it["label"] else f'問{q["no"]}'
                pt = q["points"].replace("各", "") if len(q["items"]) > 1 else q["points"]
                n = nums[i] if i < len(nums) else ""
                topic = "・".join(q["rules"])
                b.append(f'<tr><td class="c">{E(lab)}</td><td class="c">{E(n)}</td><td class="c">{E(pt)}</td>'
                         f'<td class="a">{CIRC[it["answer"]]}</td><td>{E(topic)}</td></tr>')
        b.append('</table>')
        # 設問別解説
        b.append('<div class="sec">設問別解説<small>正解の根拠と、誤答がなぜ不可か</small></div>')
        for q in S["questions"]:
            nums = [x.strip() for x in re.split(r"[・,、]", q["nums"]) if x.strip()]
            ans = "　".join((f'{it["label"]}' if it["label"] else "") + CIRC[it["answer"]] for it in q["items"])
            b.append(f'<div class="qa"><div class="qh">問{q["no"]}（解答番号{E(q["nums"])}・{E(q["points"])}）</div><div class="qb">')
            b.append(f'<div class="qt">{E(plain(q["text"])).replace(chr(10), "<br>")}</div>')
            b.append(f'<div class="ans">正解　{ans}</div>')
            for it in q["items"]:
                opts = "　".join(f'{CIRC[i]}{"★" if i == it["answer"] else ""} {c}' for i, c in enumerate(it["choices"]))
                b.append(f'<div class="qt mincho">{E(it["label"])} {E(opts)}</div>')
            b.append(f'<div class="exp">{E(q["exp"]).replace(chr(10), "<br>")}</div>')
            if q.get("rules"): b.append(f'<div class="rules">〔{E("・".join(q["rules"]))}〕</div>')
            b.append('</div></div>')
        # 現代語訳
        b.append('<div class="sec pb">全文現代語訳<small>原文と対応させて読む</small></div>')
        po = [x.strip() for x in plain(S["passage"]).split("\n") if x.strip()]
        tj = [x.strip() for x in S["translation"].split("\n") if x.strip()]
        for i in range(max(len(po), len(tj))):
            b.append(f'<div class="tr"><div class="n">{i+1}</div><div class="b">')
            if i < len(po): b.append(f'<div class="o">{nb(po[i])}</div>')
            if i < len(tj): b.append(f'<div class="j">{E(tj[i])}</div>')
            b.append('</div></div>')
        # 重要文法
        b.append('<div class="sec">重要文法<small>品詞・活用形・意味・敬意の方向</small></div><table class="gr">')
        for g in S["grammar"]:
            b.append(f'<tr><td class="w mincho">{E(g["phrase"])}</td><td>{E(g["point"])}</td></tr>')
        b.append('</table>')
        # 使うルール
        b.append('<div class="sec">この本文で使うルール<small>古文 文法・読解ルールブック 全20ルールとの対応</small></div>')
        b.append('<table class="rl"><tr><th style="width:210px">ルール</th><th>この本文での使いどころ</th></tr>')
        for r in S["rules_used"]:
            b.append(f'<tr><td class="r">{E(r["rule"])}</td><td>{E(r["where"])}</td></tr>')
        b.append('</table>')
        # 校訂異同の詳細は講師用メモへ回し、ここは1行に収める（丸ごと載せると白紙同然のページが出る）
        b.append(f'<div class="note">本文の典拠：{E(S["work"])}　<span class="src">{E(S.get("source_url",""))}</span>'
                 f'<br>校訂本文との異同や翻刻との照合の記録は、別紙「講師用メモ」に載せた。</div>')
        b.append('</div>')
    return "".join(b)

# ---------------------------------------------------------------- 出力
def page(body, css, title):
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{E(title)}</title><style>{css}</style></head><body>{body}</body></html>'

def to_pdf(html_str, name):
    hp = os.path.join(OUT, name + ".html"); pp = os.path.join(OUT, name + "_raw.pdf")
    open(hp, "w", encoding="utf-8").write(html_str)
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=10000", f"--print-to-pdf={pp}", "file://" + hp],
                       capture_output=True, text=True, timeout=300)
    if not os.path.exists(pp): print(r.stderr[-1500:]); raise SystemExit("chrome failed: " + name)
    return pp

FONT = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"
def finalize(raw, dest, label):
    d = fitz.open(raw); n = len(d); grey = (0.42, 0.47, 0.56)
    for i, p in enumerate(d):
        w, h = p.rect.width, p.rect.height; y = h - 20
        p.insert_text((40, y), BRAND + "　" + label, fontsize=7.5, fontname="hira", fontfile=FONT, color=grey)
        s = f"{i+1} / {n}"; tw = fitz.get_text_length(s, fontname="helv", fontsize=8)
        p.insert_text((w - 40 - tw, y), s, fontsize=8, fontname="helv", color=grey)
    d.set_metadata({"title": label, "author": BRAND})
    d.subset_fonts(); d.save(dest, garbage=4, deflate=True)
    print(f"{os.path.basename(dest)}: {n}p  {os.path.getsize(dest)//1024}KB")
    return n

def build(path, dest_dir=None):
    data = json.load(open(path, encoding="utf-8"))
    sets = sorted(data["sets"], key=lambda x: x["id"])
    dest_dir = dest_dir or OUT; os.makedirs(dest_dir, exist_ok=True)
    for key, body, css, fname, label in (
        ("kobun_q", problem_html(sets), CSS_Q, "共通テスト形式_古文_第4問_類似問題_問題編.pdf", "共通テスト形式 国語 第4問（古文）類似問題　問題編"),
        ("kobun_a", answer_html(sets), CSS_A, "共通テスト形式_古文_第4問_類似問題_解答解説編.pdf", "共通テスト形式 国語 第4問（古文）類似問題　解答解説編"),
    ):
        raw = to_pdf(page(body, css, label), key)
        finalize(raw, os.path.join(dest_dir, fname), label)
    print("題数:", [s["id"] for s in sets])

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
