# -*- coding: utf-8 -*-
"""共通テスト 第4問（古文）演習問題集 ビルダー（基礎→標準→本番の段階別）

   問題編   = 縦書き（本番と同じ体裁）
   解答解説編 = 横書き（自塾の解説体裁）
   HTML -> Headless Chrome -> PDF -> PyMuPDF でフッター付与

   使い方:
     python3 build.py                      # sets/*.json を全部読んで out/ に出す
     python3 build.py <出力先ディレクトリ>
"""
import html, re, os, sys, json, glob, subprocess
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND = "TRILLION AI 学習塾"
CIRC = "①②③④⑤"

# レベルの定義（問題編の見出し・解説編の帯・検査の字数レンジがこの1か所を見る）
LEVELS = {
    1: {"name": "基礎", "band": "#0e7490",
        "aim": "説話の筋を追い、会話と地の文を切り分けて、誰が何をしたかを取り違えないこと。",
        "chars": (400, 700)},
    2: {"name": "標準", "band": "#7c3aed",
        "aim": "和歌のやりとりと敬語から人物の関係をつかみ、心情の移り変わりを本文の言葉で裏づけること。",
        "chars": (640, 900)},
    3: {"name": "本番", "band": "#b45309",
        "aim": "入れ子の引用・長い会話・語り手の評語まで読み切り、本番と同じ分量を本番の持ち時間（20分）で処理しきること。",
        "chars": (840, 1200)},
}

def E(s): return html.escape(str(s), quote=False)

def body_chars(passage):
    """本文の分量。組版用の印（傍線記号・注番号）と、校訂本文が付けている読み仮名は数えない。
       レベルの想定字数（LEVELS[..]["chars"]）はこの数え方で書いてある。"""
    s = re.sub(r"\{\{/?[abcwxy]\}\}", "", passage)
    s = re.sub(r"[（(]注\d+[)）]", "", s)
    s = re.sub(r"[（(][ぁ-んァ-ヶー]+[)）]", "", s)
    return len(re.sub(r"\s", "", s))

def css_guard(css, tag):
    """CSSに全角文字が紛れるとChromeはその宣言を黙って捨てる（気づけない）ので門で止める"""
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    bad = sorted({c for c in body if ord(c) > 127})
    if bad: raise SystemExit(f"{tag}: CSSに非ASCII文字 {bad}")

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
.lv { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 9.5pt; color: #fff;
      background: #334155; padding: 3px 5px; margin-left: 8px; text-indent: 0; letter-spacing: .1em; }
.spec { font-family: "Hiragino Sans", sans-serif; font-size: 9.5pt; color: #333; margin-left: 10px; text-indent: 0; }
.namebox { border: 1px solid #64748b; padding: 5px 4px; margin-left: 10px; font-family: "Hiragino Sans", sans-serif;
           font-size: 9pt; color: #334155; text-indent: 0; }
.lead { border: 1px solid #64748b; padding: 7px 6px; margin-left: 10px; font-size: 9.8pt; line-height: 1.85; text-indent: 0; }
.body-oo { margin-left: 12px; }
/* 傍線は1字ずつに引く。1つの長い span にすると、改ページで「文字の無い所に罫だけが残る」
   （縦組みの最終列にまるまる1本、実際に起きた）。1字ずつなら空の断片が生まれない。 */
/* ★傍線に text-decoration を使わないこと。縦組みで段や頁をまたぐと、
   文字のない空の断片にも罫だけが描かれる（実際に、本文の無い列に1本まるまる残った）。
   box-shadow なら断片の大きさぶんしか描かれないので、空の断片には何も出ない。 */
.u { box-shadow: inset 1.1px 0 0 0 currentColor; }
.ul { white-space: nowrap; }                /* 傍線の最後の1字と記号（ア）を離さない */
.w { text-decoration: underline wavy; text-underline-offset: 6px; break-inside: avoid; }
.tcy { text-combine-upright: all; }        /* 数字・ラテン文字は1マスに収める（縦中横） */
.cmb { text-combine-upright: all; }        /* 傍線の (ア)(Ａ) は1マスに収める */
/* ★傍線の記号は縦中横にしない。3字を1マスに押し込むと、font-size を上げても
   実寸 6.3pt までしか出ず、注番号より小さいままになる（これを探すのが5問30点の出発点）。 */
.mk { font-family: "Hiragino Sans", sans-serif; font-size: 9.6pt; font-weight: 700;
      white-space: nowrap; }
.nt { font-size: 8.4pt; }                   /* 注番号は本番どおり本文より小さく */
.rb { white-space: nowrap; }
.ansno { display: inline-block; border: 1.2px solid #0f172a; padding: 0 2px; font-family: "Hiragino Sans", sans-serif;
         font-size: 8.5pt; text-combine-upright: all; }
.qh { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 10.2pt; text-indent: 0; margin-left: 4px; }
.ch { text-indent: 0; padding-top: .6em; break-inside: avoid; }
.opts { break-inside: avoid; }              /* 選択肢5つを1つの塊にする（1つだけ次ページに残さない） */
.note-t { font-size: 9pt; line-height: 1.75; padding-top: 1.6em; text-indent: -1.6em; }  /* 縦組みの字下げは padding-top で相殺する */
.note-t.qh { padding-top: 0; text-indent: 0; margin-left: 8px; }
.ind { text-indent: 0; }                    /* 和歌などの字下げ。縦組みでは padding-top が字下げになる */
.talk { border: 1px solid #64748b; padding: 7px 6px; margin-left: 9px; font-size: 9.5pt; line-height: 1.8; text-indent: 0; break-inside: avoid; }
/* 巻頭（使い方） */
.cv-t { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 20pt; letter-spacing: .18em;
        margin-left: 10px; text-indent: 0; }
.cv-s { font-family: "Hiragino Sans", sans-serif; font-size: 10.5pt; color: #334155; margin-left: 14px; text-indent: 0; }
.cv-h { font-family: "Hiragino Sans", sans-serif; font-weight: 700; font-size: 12pt; margin-left: 14px;
        text-indent: 0; border-right: 3px solid #334155; padding-right: 6px; }
.cv-p { font-size: 10pt; line-height: 1.95; margin-left: 6px; text-indent: 1em; }
.cv-l { font-size: 10pt; line-height: 1.95; margin-left: 4px; text-indent: -1.2em; padding-top: 1.2em; }
table.cv { border-collapse: collapse; margin-left: 12px; font-size: 9.6pt; writing-mode: vertical-rl; }
table.cv th, table.cv td { border: 1px solid #94a3b8; padding: 6px 5px; text-align: right; }
table.cv th { background: #f1f5f9; font-family: "Hiragino Sans", sans-serif; }
table.ansbox { border-collapse: collapse; margin-left: 10px; writing-mode: vertical-rl;
               font-family: "Hiragino Sans", sans-serif; font-size: 8.6pt; }
table.ansbox th, table.ansbox td { border: 1px solid #64748b; padding: 4px 3px; text-align: center;
                                   text-combine-upright: all; }
table.ansbox th { background: #f1f5f9; color: #334155; }
table.ansbox td { height: 30px; }
"""

def mark_each(inner, cls):
    """傍線・波線を1字ずつに引く。すでに入っている span（縦中横・読み仮名）は壊さない。
       最後の1字だけは、直後に来る記号（ア）と離れないよう nowrap でくくる。"""
    out, i, last = [], 0, None
    while i < len(inner):
        if inner[i] == "<":
            j = inner.index(">", i)
            if inner.startswith("</", i):
                out.append(inner[i:j + 1]); i = j + 1; continue
            k = inner.index("</span>", j) + len("</span>")
            out.append(f'<span class="{cls}">{inner[i:k]}</span>'); last = len(out) - 1; i = k; continue
        out.append(f'<span class="{cls}">{inner[i]}</span>'); last = len(out) - 1; i += 1
    if cls == "u" and last is not None:
        out[last] = f'<span class="ul">{out[last]}</span>'
    return "".join(out)

def indented(ln):
    """行頭の全角空白を字下げにする（縦組みなので padding-top が字下げにあたる）。
       和歌を本文から一段下げて組むために使う。"""
    n = len(ln) - len(ln.lstrip("\u3000"))
    body = ln.strip()
    if not n: return f"<p>{body}</p>"
    return f'<p class="ind" style="padding-top:{n}em">{body}</p>'

def tate_text(s):
    """本文の記号を縦書き用のマークアップへ。傍線 a/b/c、波線 w、場面 x/y"""
    t = E(s)
    t = re.sub(r"[（(]注(\d+)[)）]",
               lambda m: f'<span class="nt">(注<span class="tcy">{m.group(1)}</span>)</span>', t)
    t = re.sub(r"(\d+)", r'<span class="tcy">\1</span>', t)      # 残りの数字を正立させる
    t = re.sub(r"([一-龥々]{1,6}\([ぁ-ん]+\))", r'<span class="rb">\1</span>', t)   # 読み仮名を行またぎさせない
    for k, lab in (("a", "ア"), ("b", "イ"), ("c", "ウ"), ("x", "Ａ"), ("y", "Ｂ")):
        t = re.sub(r"\{\{" + k + r"\}\}(.*?)\{\{/" + k + r"\}\}",
                   lambda m, lab=lab: mark_each(m.group(1), "u")
                                      + f'<span class="mk">（{lab}）</span>', t, flags=re.S)
    t = re.sub(r"\{\{w\}\}(.*?)\{\{/w\}\}", lambda m: mark_each(m.group(1), "w"), t, flags=re.S)
    return "".join(indented(ln) for ln in t.split("\n") if ln.strip())

def tcy(s):
    """縦組みの中の半角数字・ラテン文字を正立させる（縦に並べる）"""
    return re.sub(r"([0-9]+|[A-Za-z])", r'<span class="tcy">\1</span>', E(s))

def nums_html(nums):
    return "・".join(f'<span class="ansno">{n.strip()}</span>' for n in re.split(r"[・,、]", nums) if n.strip())

COVER_STEPS = [
    ("① 注を先に読む", "人物の名・官職・耳慣れない語は、読み始める前に注で押さえる。誰が出てくる話かを先に知っておくだけで、主語の取り違えが減る。"),
    ("② 会話を「と・とて・など」で閉じる", "「　」の始まりは見えるが、終わりは見えないことがある。引用の「と」「とて」「など」までが会話だと決めてから、その外側の地の文に戻る。"),
    ("③ 主語は「て・を・に・ば」で追う", "「て」でつながる間は主語が変わらないことが多く、「を」「に」「ば」では変わることが多い。変わったと思ったら、敬語の向きで確かめる。"),
    ("④ 敬語で身分の上下を決める", "尊敬語が付く人がその場のいちばん上、謙譲語はその動作の受け手を高める。地の文で敬語が付かない人は、身分が低いか、語り手が近しく扱っている人である。"),
    ("⑤ 和歌は掛詞をほどいてから訳す", "同音の語が二重に働いていないかを先に見る。贈答歌は、前の歌のどの語を受け返したかをたどると、答えの根拠がそのまま出てくる。"),
    ("⑥ 選択肢は二つに絞ってから本文に戻る", "五つを順に本文と照らすのではなく、明らかに違う三つを先に落とす。残った二つの違う部分だけを、本文の一語で決める。"),
]

XREF = {}      # {(冊子, 回): (開始ページ, 終了ページ)} ―― 2度目の組版で入れる

def xref(book, sid, label):
    """相互参照の表示。1度目の組版ではまだ分からないので空にする。"""
    p = XREF.get((book, sid))
    return f"{label} {p[0]}〜{p[1]}ページ" if p else ""

def scan_pages(path, sets, pat):
    """刷り上がりから、各回が何ページ目から始まるかを読む"""
    import fitz
    d = fitz.open(path)
    heads = {}
    for i, page in enumerate(d, 1):
        txt = re.sub(r"\s", "", page.get_text())
        for S in sets:
            if pat(S["id"]) in txt and S["id"] not in heads: heads[S["id"]] = i
    out, ids = {}, sorted(heads)
    for n, sid in enumerate(ids):
        end = heads[ids[n + 1]] - 1 if n + 1 < len(ids) else len(d)
        out[sid] = (heads[sid], end)
    return out

def cover_html(sets):
    b = ['<p class="cv-t">共通テスト形式　国語　第4問（古文）</p>',
         '<p class="cv-t">演習問題集　――　基礎から本番まで</p>',
         f'<p class="cv-s">{E(BRAND)}</p>',
         '<p class="cv-h">この問題集の組み立て</p>',
         '<p class="cv-p">第4問（古文）だけを、やさしい説話から本番の分量まで順に並べた。'
         'どの回も本番と同じ形（5問・45点・解答番号23〜29）で作ってあるので、'
         '形式に慣れながら、読む本文だけを少しずつ重くしていける。前から順に解くこと。'
         '目安の時間は、進むほど一分あたりに読む量が増えるように置いてある。'
         '最後の2回は、本番で古文にあてられる時間（20分）そのものである。</p>',
         '<table class="cv"><tr><th>回</th><th>レベル</th><th>出典</th><th>本文の字数</th><th>目安の時間</th><th>解答解説編</th></tr>']
    for S in sets:
        n = body_chars(S["passage"])
        b.append(f'<tr><td>第{tcy(str(S["id"]))}回</td><td>{E(LEVELS[S["level_no"]]["name"])}</td>'
                 f'<td>{E(S["work"].split()[0])}</td><td>{tcy(str(n))}字</td>'
                 f'<td>{tcy(str(S["minutes"]))}分</td>'
                 f'<td>{tcy(xref("a", S["id"], "p."))}</td></tr>')
    b.append('</table>')
    b.append('<p class="cv-h">第4問の解き方　六手順</p>')
    b.append('<p class="cv-p">どの回でもこの順で解く。時間が足りなくなったら、④まで済ませてから設問に入ること。</p>')
    for h, t in COVER_STEPS:
        b.append(f'<p class="cv-l"><span class="gothic">{tcy(h)}</span>　{tcy(t)}</p>')
    b.append('<p class="cv-h">答え合わせのしかた</p>')
    b.append('<p class="cv-p">丸つけで終わりにしない。別冊の解答解説編には、全文の現代語訳と、'
             'その本文で使った文法・読解のルールを載せてある。間違えた設問は、'
             '「どの語を読み落としたか」を一語まで特定してから次へ進むこと。'
             '合っていた設問も、選んだ理由が解説と同じかどうかを確かめる。'
             'まぐれ当たりを数えたままでは、次の回で同じところを落とす。</p>')
    return "".join(b)

def split_box(text):
    """設問文を「導入」と「囲みに入れる部分（【資料】【生徒のノート】【教師と生徒の会話】）」に分ける"""
    m = re.search(r"^【", text, re.M)
    if not m: return text, ""
    return text[:m.start()].rstrip(), text[m.start():].strip()

def problem_html(sets):
    b = [cover_html(sets)]
    for S in sets:
        L = LEVELS[S["level_no"]]
        b.append(f'<p class="daimon pb">第4問（古文）　第<span class="tcy">{S["id"]}</span>回</p>')
        b.append(f'<p class="lv">{E(L["name"])}レベル</p>')
        b.append(f'<p class="spec">配点45点／解答番号 <span class="tcy">23</span>〜<span class="tcy">29</span>'
                 f'／解答時間の目安 <span class="tcy">{S.get("minutes", 20)}</span>分</p>')
        b.append('<p class="namebox">氏名　　　　　　　　　　　　　　　得点　　　　／45</p>')
        # 解答を書き込む欄。★答え合わせのたびに設問ページをめくり直さなくて済む。
        b.append('<table class="ansbox"><tr>'
                 + "".join(f'<th>{n}</th>' for n in range(23, 30)) + '</tr><tr>'
                 + "<td>　</td>" * 7 + '</tr></table>')
        b.append(f'<p class="lead">{tcy(S["lead"])}</p>')
        b.append(f'<div class="body-oo">{tate_text(S["passage"])}</div>')
        b.append('<p class="note-t qh">（注）</p>')   # 本文の直後に置く（本番と同じ）。
        # ★強制改ページにすると、数行こぼれただけで9割白紙のページができる（実際に3ページ出た）。
        for ni, n in enumerate(S["notes"], 1):
            b.append(f'<p class="note-t"><span class="tcy">{ni}</span>　{tcy(n["word"])}　――　{tcy(n["gloss"])}</p>')
        for q in S["questions"]:
            cls = "qh pb" if q["no"] == 1 else "qh"
            b.append(f'<p class="{cls}">問<span class="tcy">{q["no"]}</span>（解答番号{nums_html(q["nums"])}・{tcy(q["points"])}）</p>')
            head, box = split_box(q["text"])
            for line in tcy(head).split("\n"):
                if line.strip(): b.append(indented(line))
            if box:
                b.append('<div class="talk">'
                         + "".join(indented(l) for l in tcy(box).split("\n") if l.strip())
                         + '</div>')
            for it in q["items"]:
                b.append('<div class="opts">')
                if it["label"]: b.append(f'<p class="qh">{E(it["label"])}</p>')
                for i, c in enumerate(it["choices"]):
                    b.append(f'<p class="ch">{CIRC[i]}　{tcy(c)}</p>')
                b.append('</div>')
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
.lvbar { display: inline-block; color: #fff; border-radius: 4px; padding: 2px 9px; font-size: 11px; font-weight: 700; margin: 7px 8px 0 0; }
.aim { display: inline; font-size: 11.5px; color: #334155; }
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
.qa .rules { font-size: 10.5px; color: #1e3a8a; margin-top: 3px; break-before: avoid; }
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
        L = LEVELS[S["level_no"]]
        pb = "" if si == 0 else "pb"
        b.append(f'<div class="{pb}">')
        b.append(f'<div class="head"><span class="t">第4問（古文）第{S["id"]}回　解答・解説</span>'
                 f'<span class="r">配点45点／解答番号 23〜29'
                 f'{"　｜　問題編 " + xref("q", S["id"], "") if xref("q", S["id"], "") else ""}</span></div>')
        b.append(f'<div><span class="lvbar" style="background:{L["band"]}">{E(L["name"])}レベル</span>'
                 f'<span class="aim">このレベルのねらい：{E(L["aim"])}</span></div>')
        b.append(f'<div class="sub">{E(S["title"])}</div>')
        b.append(f'<div class="meta">出典：{E(S["work"])}（{E(S["genre"])}・{E(S["era"])}）</div>')
        b.append('<div class="meta">この回の中身：解答一覧 ／ 設問別解説 ／ 全文現代語訳 ／ 重要文法 ／ この本文で使うルール</div>')
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
        for r in sorted(S["rules_used"], key=lambda x: x["rule"]):
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
                       capture_output=True, text=True, timeout=600)
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

def load_sets():
    files = sorted(glob.glob(os.path.join(HERE, "sets", "set*.json")))
    sets = [json.load(open(f, encoding="utf-8")) for f in files]
    return sorted(sets, key=lambda x: x["id"])

def build(dest_dir=None):
    css_guard(CSS_Q, "問題編"); css_guard(CSS_A, "解答解説編")
    sets = load_sets()
    if not sets: raise SystemExit("sets/set*.json が無い")
    dest_dir = dest_dir or OUT; os.makedirs(dest_dir, exist_ok=True)
    # ★2度刷る。1度目で各回の開始ページを読み、2度目でそれを相互参照として入れる。
    #   入れたことで改ページがずれていないかを最後に確かめ、ずれていたら落とす。
    for pas in (1, 2, 3):
        paths = render(sets, dest_dir)
        got = {("q", k): v for k, v in scan_pages(paths[0], sets, lambda i: f"第4問（古文）第{i}回").items()}
        got |= {("a", k): v for k, v in scan_pages(paths[1], sets, lambda i: f"第4問（古文）第{i}回解答・解説").items()}
        if got == XREF:
            print(f"相互参照: {pas}回目の組版で安定"); break
        if pas == 3: raise SystemExit("相互参照のページ番号が安定しない（3回組んでもずれる）")
        XREF.clear(); XREF.update(got)
    print("収録:", [(s["id"], LEVELS[s["level_no"]]["name"]) for s in sets])

def render(sets, dest_dir):
    out = []
    for key, body, css, fname, label in (
        ("kobun_q", problem_html(sets), CSS_Q,
         "共通テスト形式_古文_第4問_演習問題集_基礎から本番まで_問題編.pdf",
         "共通テスト形式 国語 第4問（古文）演習問題集 基礎から本番まで　問題編"),
        ("kobun_a", answer_html(sets), CSS_A,
         "共通テスト形式_古文_第4問_演習問題集_基礎から本番まで_解答解説編.pdf",
         "共通テスト形式 国語 第4問（古文）演習問題集 基礎から本番まで　解答解説編"),
    ):
        raw = to_pdf(page(body, css, label), key)
        dest = os.path.join(dest_dir, fname)
        finalize(raw, dest, label)
        out.append(dest)
    return out

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
