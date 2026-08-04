# -*- coding: utf-8 -*-
"""英検準1級 対策問題集 ビルダー（単一ソース data/*.json → 問題編/解答解説編 HTML）

HTML → Chrome --headless=new --print-to-pdf でA4 PDF化。
eng_march_gw の BASE_CSS 系譜を土台に、英検4大問レイアウトへ作り替え。

大問1: 短文の語句空所補充（語彙・熟語 4択）  No.1〜40
大問2: 長文の語句空所補充（4択）            No.41〜49（3パッセージ×3空所）
大問3: 長文の内容一致選択（4択）            No.50〜59（3パッセージ・計10問）
大問4: 英作文（要約2題＋意見論述2題）

通し番号は build 冒頭で決定論的に付与し、問題編・解答編で共有する。
"""
import os, re, html, json
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

META = {
    "series": "英検2級 対策問題集",
    "subtitle": "大問1〜4 実戦演習 ── 語彙・熟語／長文読解／英作文",
    "brand": "トリリオンAI塾",
    "note": "本書は日本英語検定協会とは無関係の、学習用オリジナル問題です。",
}

# ==================== データ読込 ====================
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)

def load_all():
    return (load("part1_vocab.json"), load("part2_cloze.json"),
            load("part3_reading.json"), load("part4_writing.json"))

# ==================== 通し番号付与 ====================
def assign_numbers(p1, p2, p3):
    """各設問に通し No を付ける。大問1=1..40, 大問2=41.., 大問3=続き。"""
    n = 0
    for it in p1["items"]:
        n += 1
        it["_no"] = n
    for ps in p2["passages"]:
        for b in ps["blanks"]:
            n += 1
            b["_no"] = n
    for ps in p3["passages"]:
        for q in ps["questions"]:
            n += 1
            q["_no"] = n
    return n

# ==================== テキスト整形 ====================
_TRANS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "―": "-",
          "…": "...", "　": " "}
def clean(s):
    if s is None:
        return ""
    s = str(s)
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)

def esc(s):
    return html.escape(clean(s), quote=False)

CIRCLE = ["①", "②", "③", "④"]

def en(s):
    """英文をGeorgia表示。空所 _______ は下線ボックスに。"""
    s = esc(s)
    s = re.sub(r"_{3,}", '<span class="fill">&nbsp;</span>', s)
    return f'<span class="en">{s}</span>'

def cloze_body(text, blanks):
    """大問2本文。本文中の ( 1 ) を通し番号の強調空所へ置換し、段落化。"""
    safe = esc(text)
    for b in blanks:
        gno = b["_no"]; n = b["n"]
        safe = re.sub(r"\(\s*%d\s*\)" % n,
                      '<span class="cloze">( %d )</span>' % gno, safe, count=1)
    paras = re.split(r"\n\s*\n", safe.strip())
    return "".join('<p>%s</p>' % p.strip().replace("\n", " ") for p in paras if p.strip())

def para_body(paragraphs):
    """大問3本文（段落配列）。"""
    return "".join('<p>%s</p>' % esc(p) for p in paragraphs)

# ==================== CSS ====================
BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 15mm 15mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a; font-size:10.5pt; line-height:1.6; margin:0; }
.en { font-family:Georgia,"Times New Roman",serif; }

/* cover */
.cover { text-align:center; padding-top:38mm; }
.cover .ttl { font-size:30pt; font-weight:800; color:#0f172a; letter-spacing:.04em; }
.cover .sub { font-size:12.5pt; color:#334155; margin-top:10px; font-weight:600; }
.cover .rule { width:120px; height:4px; background:#c8a24e; margin:20px auto; border-radius:2px; }
.cover .spec { font-size:10.5pt; color:#475569; margin-top:6px; line-height:1.9; }
.cover .brand { margin-top:40mm; font-size:12pt; color:#0f172a; font-weight:700; }
.cover .disc { font-size:8.6pt; color:#94a3b8; margin-top:8px; }

/* header band */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:9px 14px; border-radius:8px;
  display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9.5pt; opacity:.9; margin-left:8px; }
.band .r { text-align:right; font-size:9pt; line-height:1.4; }
.metarow { display:flex; gap:10px; margin:9px 0 6px; font-size:9.5pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 130px; text-align:center; }

/* 大問見出し / 指示 */
.partttl { font-size:13pt; font-weight:700; color:#fff; background:#1e3a8a; border-radius:6px;
  padding:5px 13px; margin:15px 0 4px; page-break-after:avoid; }
.partttl small { display:block; font-weight:600; font-size:9pt; opacity:.92; margin-top:3px; }
.instr { font-size:9.3pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:6px 10px;
  border-radius:4px; margin:5px 0 10px; color:#334155; page-break-after:avoid; }
.pb { page-break-before:always; }

/* 設問ブロック */
.q { margin:0 0 9px; page-break-inside:avoid; }
.q .h { display:flex; align-items:baseline; gap:8px; }
.qno { background:#0f172a; color:#fff; border-radius:5px; padding:1px 8px; font-size:9pt; font-weight:700; white-space:nowrap; }
.q .stem { margin:2px 0 2px; font-size:10.2pt; }
.q .qtext { margin:2px 0 2px; font-size:9.9pt; font-weight:600; color:#0f172a; }
.q .choices div { margin:2px 0 1px 10px; font-size:9.8pt; }
.q .choices.inline { display:flex; flex-wrap:wrap; gap:4px 18px; }
.q .choices .en { font-size:10pt; }
.fill { display:inline-block; min-width:70px; border-bottom:1.5px solid #0f172a; text-align:center; font-weight:700; }
.cloze { font-weight:700; color:#1e3a8a; white-space:nowrap; }

/* 大問1を2段組で密に */
.vocab2 { column-count:1; }

/* 長文パッセージ */
.ptitle { font-size:11.5pt; font-weight:700; color:#0f172a; margin:13px 0 4px; border-bottom:2px solid #1e3a8a; padding-bottom:3px; page-break-after:avoid; }
.ptitle .ptheme { font-size:8.6pt; color:#64748b; font-weight:600; margin-left:8px; }
.ptitle .pwc { font-size:8.4pt; color:#94a3b8; font-weight:600; float:right; }
.passage { font-family:Georgia,serif; font-size:10.3pt; line-height:1.72; text-align:justify; margin:4px 0 8px; }
.passage p { margin:0 0 6px; }

/* 英作文 解答欄 */
.srcbox { border:1px solid #cbd5e1; border-radius:6px; padding:9px 13px; background:#f8fafc;
  font-family:Georgia,serif; font-size:10pt; line-height:1.66; text-align:justify; margin:6px 0; }
.srcbox p { margin:0 0 6px; }
.topicbox { border:1.5px solid #1e3a8a; border-radius:6px; padding:8px 13px; margin:6px 0; font-family:Georgia,serif; font-size:10.6pt; font-weight:700; color:#0f172a; }
.points { display:flex; gap:8px; flex-wrap:wrap; margin:6px 0 4px; }
.point { border:1px solid #94a3b8; border-radius:5px; padding:2px 12px; font-size:9.4pt; background:#eef2ff; font-family:Georgia,serif; }
.wlbox { margin:6px 0 4px; }
.wl { border-bottom:1px solid #cbd5e1; height:21px; }
.wcnt { font-size:8.8pt; color:#64748b; margin:2px 0 0; }

/* 解説 */
.secttl { font-size:13pt; font-weight:700; color:#0f172a; border-left:6px solid #1e3a8a; padding:3px 0 3px 10px; margin:14px 0 9px; page-break-after:avoid; }
.secttl .en2 { font-size:9pt; color:#64748b; font-weight:600; margin-left:8px; }

table.ans { width:100%; border-collapse:collapse; font-size:9pt; margin:3px 0 8px; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:3px 5px; text-align:center; }
table.ans th { background:#eef2ff; font-weight:700; }
table.ans td.a { font-weight:700; color:#1e3a8a; }

.ex { border:1px solid #e2e8f0; border-left:4px solid #1e3a8a; border-radius:6px; padding:6px 10px; margin:7px 0; page-break-inside:avoid; }
.ex .exh { display:flex; align-items:baseline; gap:8px; margin-bottom:2px; flex-wrap:wrap; }
.ex .exno { font-weight:700; color:#0f172a; }
.ex .exa { font-family:Georgia,serif; font-weight:700; color:#1e3a8a; }
.ex .tag { display:inline-block; background:#fde68a; color:#7c2d12; font-weight:700; border-radius:4px; padding:0 7px; font-size:8.3pt; }
.ex .exbody { font-size:9.3pt; color:#1f2937; line-height:1.62; }
.ex .exbody .en { font-family:Georgia,serif; }
.ex ul { margin:3px 0 0; padding-left:18px; }
.ex li { font-size:9pt; margin:1px 0; }

.wcard { border:1px solid #cbd5e1; border-left:4px solid #047857; border-radius:6px; padding:8px 11px; margin:9px 0; page-break-inside:avoid; }
.wcard .wh { font-weight:700; font-size:10.4pt; color:#065f46; margin-bottom:4px; }
.wcard .model { background:#f0fdf4; border-radius:4px; padding:6px 10px; margin:4px 0; font-family:Georgia,serif; font-size:9.9pt; line-height:1.55; }
.wcard .ml { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8.4pt; color:#047857; font-weight:700; display:block; margin-bottom:2px; }
.wcard .pt { font-size:9.1pt; color:#334155; margin-top:4px; }
.wcard .pt b { color:#065f46; }
.wcard ul { margin:3px 0 0; padding-left:18px; }
.wcard li { font-size:9pt; margin:1px 0; }
.wcard li .en { font-family:Georgia,serif; }

.foot { text-align:center; color:#64748b; font-size:8.3pt; margin-top:12px; padding-top:5px; border-top:1px solid #e2e8f0; page-break-inside:avoid; }
"""

def doc(title, inner):
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<title>%s</title><style>%s</style></head><body>%s</body></html>'
            % (title, BASE_CSS, inner))

def band(kind):
    return ('<div class="band"><div class="l">%s <small>%s</small></div>'
            '<div class="r">2級 / Grade 2<br>%s</div></div>'
            % (esc(META["series"]), esc(kind), esc(META["brand"])))

def foot(kind):
    return ('<div class="foot">%s ／ %s ・ %s</div>'
            % (esc(META["brand"]), esc(META["series"]), esc(kind)))

# ==================== 問題編 ====================
def render_vocab(items):
    h = ('<div class="partttl">大問1　短文の語句空所補充'
         '<small>次の各文の空所に入れるのに最も適切なものを ①〜④ から一つ選びなさい。</small></div>')
    for it in items:
        h += '<div class="q"><div class="h"><span class="qno">%d</span></div>' % it["_no"]
        h += '<div class="stem">%s</div>' % en(it["sentence"])
        h += '<div class="choices inline">'
        for j, c in enumerate(it["choices"]):
            h += '<div>%s %s</div>' % (CIRCLE[j], en(c))
        h += '</div></div>'
    return h

def render_cloze(passages):
    h = ('<div class="partttl pb">大問2　長文の語句空所補充'
         '<small>本文を読み、各空所に入れるのに最も適切なものを ①〜④ から一つ選びなさい。</small></div>')
    for ps in passages:
        wc = ps.get("word_count")
        wc_s = '<span class="pwc">%d words</span>' % wc if wc else ""
        h += ('<div class="ptitle">%s<span class="ptheme">［%s］</span>%s</div>'
              % (en(ps["title"]) if False else esc(ps["title"]), esc(ps.get("theme","")), wc_s))
        h += '<div class="passage">%s</div>' % cloze_body(ps["text"], ps["blanks"])
        for b in ps["blanks"]:
            h += '<div class="q"><div class="h"><span class="qno">%d</span></div>' % b["_no"]
            h += '<div class="choices inline">'
            for j, c in enumerate(b["choices"]):
                h += '<div>%s %s</div>' % (CIRCLE[j], en(c))
            h += '</div></div>'
    return h

def render_reading(passages):
    h = ('<div class="partttl pb">大問3　長文の内容一致選択'
         '<small>本文の内容に関する各質問に対して最も適切なものを ①〜④ から一つ選びなさい。</small></div>')
    for ps in passages:
        wc = ps.get("word_count")
        wc_s = '<span class="pwc">%d words</span>' % wc if wc else ""
        h += ('<div class="ptitle">%s<span class="ptheme">［%s］</span>%s</div>'
              % (esc(ps["title"]), esc(ps.get("theme","")), wc_s))
        h += '<div class="passage">%s</div>' % para_body(ps["paragraphs"])
        for q in ps["questions"]:
            h += '<div class="q"><div class="h"><span class="qno">%d</span></div>' % q["_no"]
            h += '<div class="qtext">%s</div>' % en(q["q"])
            h += '<div class="choices">'
            for j, c in enumerate(q["choices"]):
                h += '<div>%s %s</div>' % (CIRCLE[j], en(c))
            h += '</div></div>'
    return h

def render_writing(p4):
    h = ('<div class="partttl pb">大問4　ライティング'
         '<small>要約問題（Summary）と意見論述（Opinion）</small></div>')
    # 要約
    h += ('<div class="instr">■ 要約問題：次の英文を読み、その内容を <b>45〜55語</b> の英語で要約しなさい。</div>')
    for i, t in enumerate(p4["summary_tasks"], 1):
        h += '<div class="q"><div class="h"><span class="qno">要約 %d</span></div>' % i
        if t.get("source_title"):
            h += '<div class="ptitle" style="margin-top:4px">%s</div>' % esc(t["source_title"])
        st = esc(t["source_text"])
        paras = re.split(r"\n\s*\n", st.strip())
        body = "".join('<p>%s</p>' % p.strip().replace("\n", " ") for p in paras if p.strip())
        h += '<div class="srcbox">%s</div>' % body
        h += '<div class="wlbox">' + '<div class="wl"></div>'*6 + '</div>'
        h += '<div class="wcnt">語数（　　　　語）　※45〜55語</div></div>'
    # 意見論述（POINTS付き）
    h += ('<div class="instr" style="margin-top:12px">■ 意見論述：以下の TOPIC について、あなたの意見とその理由を2つ、<b>80〜100語</b> の英語で書きなさい。'
          'POINTS は考えを整理する参考にしてよい。</div>')
    for i, t in enumerate(p4["essay_tasks"], 1):
        h += '<div class="q"><div class="h"><span class="qno">意見 %d</span></div>' % i
        h += '<div class="topicbox">TOPIC：%s</div>' % esc(t["topic"])
        pts = t.get("points", [])
        if pts:
            h += '<div class="points">' + "".join('<span class="point">%s</span>' % esc(p) for p in pts) + '</div>'
        h += '<div class="wlbox">' + '<div class="wl"></div>'*9 + '</div>'
        h += '<div class="wcnt">語数（　　　　語）　※80〜100語</div></div>'
    return h

def build_mondai(p1, p2, p3, p4):
    h = band("問題編")
    h += ('<div class="metarow"><div class="cell">氏名　　　　　　　　　　</div>'
          '<div class="cell">日付　　　　／　　　／</div>'
          '<div class="cell score">得点　　　／59</div></div>')
    h += render_vocab(p1["items"])
    h += render_cloze(p2["passages"])
    h += render_reading(p3["passages"])
    h += render_writing(p4)
    h += foot("問題編")
    return h

# ==================== 解答解説編 ====================
def answer_table(items, title, cols=10):
    """No→正解記号 の表。cols問ずつ折り返す。"""
    h = '<div style="font-weight:700;margin:6px 0 3px;color:#0f172a">%s</div>' % esc(title)
    rows = [items[i:i+cols] for i in range(0, len(items), cols)]
    for row in rows:
        h += '<table class="ans"><tr>' + "".join('<th>%d</th>' % no for no, _ in row) + '</tr>'
        h += '<tr>' + "".join('<td class="a">%s</td>' % CIRCLE[a] for _, a in row) + '</tr></table>'
    return h

def build_kaisetsu(p1, p2, p3, p4):
    h = band("解答・解説編")
    h += '<div class="secttl">解答一覧<span class="en2">Answer Key</span></div>'
    h += answer_table([(it["_no"], it["answer"]) for it in p1["items"]], "大問1（語彙・熟語）", 10)
    h += answer_table([(b["_no"], b["answer"]) for ps in p2["passages"] for b in ps["blanks"]], "大問2（長文空所補充）", 9)
    h += answer_table([(q["_no"], q["answer"]) for ps in p3["passages"] for q in ps["questions"]], "大問3（内容一致）", 10)

    # 大問1 解説
    h += '<div class="secttl pb">大問1　解説<span class="en2">Vocabulary</span></div>'
    for it in p1["items"]:
        a = it["answer"]
        tags = esc(it.get("level",""))
        h += ('<div class="ex"><div class="exh">'
              '<span class="exno">%d</span><span class="exa">正解 %s　%s</span>'
              '<span class="tag">%s</span></div>' % (it["_no"], CIRCLE[a], esc(it["choices"][a]), tags))
        body = '<b>%s</b>：%s。 %s' % (esc(it.get("target_word","")), esc(it.get("gloss_ja","")), esc(it.get("why_correct","")))
        wo = it.get("why_others_wrong", {})
        if wo:
            body += '<ul>' + "".join('<li>%s ＝ %s</li>' % (esc(k), esc(v)) for k, v in wo.items()) + '</ul>'
        h += '<div class="exbody">%s</div></div>' % body

    # 大問2 解説
    h += '<div class="secttl pb">大問2　解説<span class="en2">Passage Cloze</span></div>'
    for ps in p2["passages"]:
        h += '<div class="ptitle">%s<span class="ptheme">［%s］</span></div>' % (esc(ps["title"]), esc(ps.get("theme","")))
        for b in ps["blanks"]:
            a = b["answer"]
            h += ('<div class="ex"><div class="exh">'
                  '<span class="exno">%d</span><span class="exa">正解 %s　%s</span></div>'
                  '<div class="exbody">%s</div></div>'
                  % (b["_no"], CIRCLE[a], esc(b["choices"][a]), esc(b.get("rationale",""))))

    # 大問3 解説
    h += '<div class="secttl pb">大問3　解説<span class="en2">Reading Comprehension</span></div>'
    for ps in p3["passages"]:
        h += '<div class="ptitle">%s<span class="ptheme">［%s］</span></div>' % (esc(ps["title"]), esc(ps.get("theme","")))
        for q in ps["questions"]:
            a = q["answer"]
            body = '<b>根拠：</b><span class="en">%s</span>' % esc(q.get("evidence",""))
            wo = q.get("why_others_wrong", {})
            if wo:
                body += '<ul>' + "".join('<li>%s：%s</li>' % (esc(k), esc(v)) for k, v in wo.items()) + '</ul>'
            h += ('<div class="ex"><div class="exh">'
                  '<span class="exno">%d</span><span class="exa">正解 %s</span></div>'
                  '<div class="exbody"><div class="en" style="margin-bottom:3px">%s</div>'
                  '<div style="margin-bottom:2px">%s　%s</div>%s</div></div>'
                  % (q["_no"], CIRCLE[a], esc(q["q"]), CIRCLE[a], esc(q["choices"][a]), body))

    # 大問4 解説
    h += '<div class="secttl pb">大問4　解答・解説<span class="en2">Writing — Model Answers</span></div>'
    for i, t in enumerate(p4["summary_tasks"], 1):
        h += '<div class="wcard"><div class="wh">要約 %d　モデル解答（%s語）</div>' % (i, t.get("summary_word_count",""))
        h += '<div class="model"><span class="ml">Model Summary</span>%s</div>' % esc(t["model_summary"])
        kp = t.get("key_points", [])
        if kp:
            h += '<div class="pt"><b>含めるべき要点：</b></div><ul>' + "".join('<li>%s</li>' % esc(k) for k in kp) + '</ul>'
        if t.get("teaching_notes"):
            h += '<div class="pt"><b>ポイント：</b>%s</div>' % esc(t["teaching_notes"])
        h += '</div>'
    for i, t in enumerate(p4["essay_tasks"], 1):
        h += '<div class="wcard"><div class="wh">意見 %d　モデル解答（%s語）</div>' % (i, t.get("essay_word_count",""))
        h += '<div class="pt" style="margin-bottom:3px"><b>TOPIC：</b><span class="en">%s</span></div>' % esc(t["topic"])
        h += '<div class="model"><span class="ml">Model Essay</span>%s</div>' % esc(t["model_essay"])
        if t.get("structure_note"):
            h += '<div class="pt"><b>構成：</b>%s</div>' % esc(t["structure_note"])
        ue = t.get("useful_expressions", [])
        if ue:
            h += '<div class="pt"><b>使える表現：</b></div><ul>' + "".join('<li><span class="en">%s</span></li>' % esc(x) for x in ue) + '</ul>'
        h += '</div>'

    h += foot("解答・解説編")
    return h

# ==================== 表紙 ====================
def build_cover(total):
    h = ('<div class="cover"><div class="ttl">英検2級</div>'
         '<div class="ttl" style="font-size:22pt;margin-top:4px">対策問題集</div>'
         '<div class="rule"></div>'
         '<div class="sub">%s</div>'
         '<div class="spec">大問1 語彙・熟語 40問　／　大問2 長文空所補充 9問<br>'
         '大問3 内容一致 10問　／　大問4 ライティング（要約2・意見論述2）<br>'
         '客観問題 計%d問 ＋ 記述4題　・　解答解説つき</div>'
         '<div class="brand">%s</div>'
         '<div class="disc">%s<br>本書は筆記（リーディング＋ライティング）対策です。リスニングは別教材で補ってください。<br>'
         '現行の実際の一次試験は 大問1=17問・大問2=6問・大問3=8問・ライティング=要約1＋意見論述1 です（本書は演習量重視で増量）。</div></div>'
         % (esc(META["subtitle"]), total, esc(META["brand"]), esc(META["note"])))
    return h

# ==================== 監査 ====================
def audit(p1, p2, p3):
    print("[audit] 大問1 正解位置分布:", dict(sorted(Counter(it["answer"] for it in p1["items"]).items())))
    print("[audit] 大問2 正解位置分布:", dict(sorted(Counter(b["answer"] for ps in p2["passages"] for b in ps["blanks"]).items())))
    print("[audit] 大問3 正解位置分布:", dict(sorted(Counter(q["answer"] for ps in p3["passages"] for q in ps["questions"]).items())))

# ==================== main ====================
def main():
    p1, p2, p3, p4 = load_all()
    total = assign_numbers(p1, p2, p3)
    audit(p1, p2, p3)
    cover_i = build_cover(total)
    mondai_i = build_mondai(p1, p2, p3, p4)
    kaisetsu_i = build_kaisetsu(p1, p2, p3, p4)
    PB = '<div class="pb"></div>'
    outputs = {
        "mondai.html": doc("%s 問題編" % META["series"], mondai_i),
        "kaisetsu.html": doc("%s 解答解説編" % META["series"], kaisetsu_i),
        "all.html": doc(META["series"], cover_i + PB + mondai_i + PB + kaisetsu_i),
    }
    for fn, content in outputs.items():
        with open(os.path.join(HERE, fn), "w", encoding="utf-8") as f:
            f.write(content)
    print("wrote", " / ".join(outputs), "| total objective =", total)

if __name__ == "__main__":
    main()
