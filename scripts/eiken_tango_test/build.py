# -*- coding: utf-8 -*-
"""英検準1級 単語テスト ビルダー（content.py → 問題編 / 解答解説編 HTML → A4 PDF）

  python3 build.py          # HTML を書き出す（check.py を内部で通す。NG なら何も書かない）
  python3 build.py --pdf    # HTML → Chrome --headless=new --print-to-pdf → ~/Desktop

正解位置は content.py に書かない。ここで word の md5 順に 0〜3 を均等配分する
（手で振ると必ず偏る／連番で振ると完全周期になり、英単語を読まずに全問正解できてしまう）。
"""
import os, re, sys, html, json, time, shutil, hashlib, subprocess
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content import TESTS  # noqa: E402

META = {
    "series": "英検準1級 単語テスト",
    "brand": "トリリオンAI塾",
    "note": "本教材は公益財団法人 日本英語検定協会とは無関係の、学習用オリジナル教材です。",
}
CIRCLE = ["①", "②", "③", "④"]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

_TRANS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "―": "-", "　": " "}


def clean(s):
    s = str(s or "")
    for k, v in _TRANS.items():
        s = s.replace(k, v)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)


def esc(s):
    return html.escape(clean(s), quote=False)


# ==================== 印字用の語義（1義に切る） ====================
def brief(s):
    """テスト用紙に刷る選択肢は『主要語義1つ』に切り、丸カッコを外す。
    全4肢に同じ規則で機械的に適用する。

    ★① 語義を1つに切る理由: これをやらないと正解肢だけが長くなる。実測で正解が単独最長の
    問題が 200問中157問（78%）になり、英単語を1つも読まずに「一番長い選択肢」を選ぶだけで
    78点取れてしまった。「、」で並記した第2語義は解答解説編（意味欄）に残るので情報は失われない。

    ★② 丸カッコを外す理由: 「（病気に）かかる」のような限定の補足は正解肢にしか書かないので、
    実測で 39問すべてで“カッコの付いた肢＝正解”になっていた。カッコを探すだけで 19.5% 確定。
    中身は残して括弧記号だけ落とす（「（規則などに）従う」→「規則などに従う」）ので意味は同じ。
    「／」で区切った別系統の2義（sanction＝制裁／認可 など）は語義として必要なので残し、
    代わりに誤答肢の側にも「／」を持たせて目印にならないようにしてある（check.py G12 が監視）。

    ★③ 中黒を「や」に開く理由: ②でカッコを外したあと、今度は列挙の「・」が
    （限定句を持つのは正解肢だけなので）16問中11問で正解の目印になった。記号を1つ潰すたびに
    次の記号が目印になる——追いかけっこを断つため、印字面では列挙記号を残さない。
    「意見の相違・問題を解決する」→「意見の相違や問題を解決する」。解答解説編の意味欄は原文のまま。"""
    return re.sub(r"[（）()]", "", s.split("、")[0]).replace("・", "や").strip()


# ==================== 正解位置の決定論的配分 ====================
def assign(tests):
    """各回ごとに md5(salt+word) 順で 0,1,2,3,0,1,... と振る → 各位置ちょうど5問。
    印字順とは無関係な並びになるので、位置だけを見ても解けない。
    同じ位置が4連続すると生徒が自分の答えを疑うので、salt を回してそれも避ける。"""
    out = []
    for t in tests:
        seq = pos = None
        for salt in range(64):
            order = sorted(range(len(t["items"])),
                           key=lambda i: hashlib.md5(("%d/%s" % (salt, t["items"][i][0]))
                                                     .encode()).hexdigest())
            pos = {idx: rank % 4 for rank, idx in enumerate(order)}
            seq = [pos[i] for i in range(len(t["items"]))]
            longest_run = mx = 1
            for i in range(1, len(seq)):
                longest_run = longest_run + 1 if seq[i] == seq[i - 1] else 1
                mx = max(mx, longest_run)
            cyc = all((seq[i] + 1) % 4 == seq[i + 1] for i in range(len(seq) - 1))
            inc = sum(1 for i in range(len(seq) - 1) if (seq[i] + 1) % 4 == seq[i + 1])
            if mx <= 3 and not cyc and inc <= len(seq) * 0.5:
                break
        items = []
        for i, it in enumerate(t["items"]):
            word, p, gloss, dis, ue, uj, note = it
            p_ans = pos[i]
            ds = [brief(d) for d in dis]
            gb = brief(gloss)
            choices = ds[:p_ans] + [gb] + ds[p_ans:]
            items.append({
                "n": i + 1, "word": word, "pos": p, "gloss": gloss, "gloss_brief": gb,
                "choices": choices, "answer": p_ans,
                "usage_en": ue, "usage_ja": uj, "note": note,
            })
        out.append({"no": t["no"], "title": t["title"], "items": items})
    return out


# ==================== CSS ====================
BASE_CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 13mm 13mm 12mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a;
       font-size:10pt; line-height:1.5; margin:0; }
.en { font-family:Georgia,"Times New Roman",serif; }
.pb { page-break-after: always; }

/* ---- cover ---- */
.cover { text-align:center; padding-top:42mm; }
.cover .ttl { font-size:31pt; font-weight:800; color:#0f172a; letter-spacing:.04em; }
.cover .ttl2 { font-size:21pt; font-weight:800; color:#0f172a; margin-top:6px; }
.cover .rule { width:120px; height:4px; background:#c8a24e; margin:20px auto; border-radius:2px; }
.cover .sub { font-size:12.5pt; color:#334155; font-weight:600; }
.cover .spec { font-size:10.5pt; color:#475569; margin-top:14px; line-height:2.0; }
.cover .howto { width:132mm; margin:16mm auto 0; text-align:left; border:1px solid #cbd5e1;
                border-radius:8px; padding:10px 16px; font-size:9.4pt; color:#334155; line-height:1.85; }
.cover .howto b { color:#0f172a; }
.cover .brand { margin-top:16mm; font-size:12pt; color:#0f172a; font-weight:700; }
.cover .disc { font-size:8.4pt; color:#94a3b8; margin-top:8px; line-height:1.7; }

/* ---- header band ---- */
.band { background:linear-gradient(90deg,#0f172a,#1e3a8a); color:#fff; padding:7px 13px;
        border-radius:8px; display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:14.5pt; font-weight:700; letter-spacing:.02em; }
.band .l small { font-weight:600; font-size:9pt; opacity:.92; margin-left:9px; }
.band .r { text-align:right; font-size:8.6pt; line-height:1.35; }
.metarow { display:flex; gap:8px; margin:7px 0 5px; font-size:9pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:3px 10px; flex:1; color:#475569; }
.metarow .cell.score { flex:0 0 42mm; text-align:center; font-weight:700; color:#0f172a; }
.instr { font-size:9pt; background:#f1f5f9; border-left:4px solid #1e3a8a; padding:5px 10px;
         border-radius:0 5px 5px 0; margin:0 0 6px; color:#334155; }

/* ---- 設問 ---- */
.qlist { border-top:1px solid #e2e8f0; }
.q { display:flex; align-items:flex-start; gap:6px; padding:1.6px 0;
     border-bottom:1px solid #eef2f7; page-break-inside:avoid; }
.qw { flex:0 0 46mm; display:flex; align-items:baseline; gap:5px; }
.qw .no { flex:0 0 7mm; text-align:right; font-size:9pt; color:#64748b; font-weight:700; }
.qw .wd { font-family:Georgia,serif; font-size:11.3pt; font-weight:700; color:#0f172a; }
.qw .ps { font-size:7.6pt; color:#1e3a8a; border:1px solid #c7d2fe; background:#eef2ff;
          border-radius:3px; padding:0 3px; }
/* ★「1回＝A4 1枚」を守るための級数と欄幅。ここを緩めると回が2ページに割れる。
   選択肢が1行に収まらないと行が2倍になり、20問のどこか1問で溢れると次ページが
   ほぼ空白のまま1枚増える（実測: 全20回で qw=50mm/qc=8.7pt のとき 25ページ・空白4枚）。
   ★hold check: build 後に必ず scripts/_pdf_qa.py を通し「ほぼ空白のページ」が0であること。 */
.qc { flex:1; display:grid; grid-template-columns:1fr 1fr; column-gap:8px; row-gap:0;
      font-size:8.5pt; line-height:1.34; }
.qc div { color:#1f2937; }
.qc .mk { color:#1e3a8a; font-weight:700; margin-right:2px; }

/* ---- 解答欄 ---- */
.ansbox { margin-top:6px; border:1.5px solid #1e3a8a; border-radius:7px; padding:5px 9px;
          page-break-inside:avoid; }
.ansbox .ttl { font-size:9pt; font-weight:700; color:#1e3a8a; margin-bottom:3px; }
table.grid { width:100%; border-collapse:collapse; table-layout:fixed; }
table.grid th, table.grid td { border:1px solid #94a3b8; text-align:center; font-size:9pt; }
table.grid th { background:#eef2ff; color:#1e3a8a; font-weight:700; padding:2px 0; }
table.grid td { height:7.2mm; }

/* ---- 解答解説編 ---- */
table.key { width:100%; border-collapse:collapse; table-layout:fixed; font-size:8.6pt; }
table.key th { background:#1e3a8a; color:#fff; font-weight:700; padding:3px 4px; text-align:left; }
table.key td { border-bottom:1px solid #e2e8f0; padding:2.6px 4px; vertical-align:top; line-height:1.42; }
table.key tr:nth-child(even) td { background:#f8fafc; }
table.key .c-no { text-align:center; color:#64748b; }
table.key .c-a { text-align:center; font-weight:700; color:#b91c1c; font-size:10pt; }
table.key .wd { font-family:Georgia,serif; font-weight:700; font-size:9.4pt; color:#0f172a; }
table.key .ps { font-size:7.4pt; color:#1e3a8a; }
table.key .use { font-family:Georgia,serif; color:#334155; }
table.key .usej { color:#64748b; font-size:8.0pt; }
table.key .note { color:#475569; font-size:8.0pt; }
table.all { width:100%; border-collapse:collapse; table-layout:fixed; font-size:9.4pt; margin-top:5px; }
table.all th, table.all td { border:1px solid #94a3b8; text-align:center; padding:2.6px 0; }
table.all th { background:#eef2ff; color:#1e3a8a; font-weight:700; font-size:8.6pt; }
table.all td.lbl { background:#f1f5f9; font-weight:700; color:#0f172a; font-size:8.8pt; }
.secttl { font-size:12.5pt; font-weight:700; color:#fff; background:#1e3a8a; border-radius:6px;
          padding:4px 12px; margin:0 0 6px; page-break-after:avoid; }
.secttl small { font-weight:600; font-size:8.8pt; opacity:.92; margin-left:8px; }
.foot { text-align:center; color:#94a3b8; font-size:8pt; margin-top:5px; padding-top:3px;
        border-top:1px solid #e2e8f0; page-break-before:avoid; }
"""


def doc(title, inner):
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<title>%s</title><style>%s</style></head><body>%s</body></html>'
            % (esc(title), BASE_CSS, inner))


def band(kind, right):
    return ('<div class="band"><div class="l">%s <small>%s</small></div>'
            '<div class="r">%s</div></div>'
            % (esc(META["series"]), esc(kind), right))


def foot(txt):
    return '<div class="foot">%s ／ %s</div>' % (esc(META["brand"]), esc(txt))


# ==================== 問題編 ====================
def render_test(t):
    # ★満点・目標点・解答欄のマス数も実データから。ベタ書きだと問数を変えたとき
    #   「得点／20」だけ残って紙が矛盾する（表紙で同じ事故を踏んでいる）。
    n = len(t["items"])
    goal = int(n * 0.8)
    h = band("第%d回" % t["no"], "準1級 / Pre-1<br>%s" % esc(META["brand"]))
    h += ('<div class="metarow"><div class="cell">氏　名　　　　　　　　　　　　　　　　　　</div>'
          '<div class="cell">日　付　　　　月　　　　日</div>'
          '<div class="cell score">得点　　　　　／ %d</div></div>' % n)
    h += ('<div class="instr">次の英単語・熟語の意味として最も適切なものを ①〜④ から一つ選び、'
          '<b>番号を下の解答欄に書きなさい</b>。（1問1点・%d点満点／目標 %d点以上）'
          '　　＜%s＞</div>' % (n, goal, esc(t["title"])))
    h += '<div class="qlist">'
    for it in t["items"]:
        h += '<div class="q"><div class="qw"><span class="no">%d</span>' % it["n"]
        h += '<span class="wd">%s</span><span class="ps">%s</span></div>' % (
            esc(it["word"]), esc(it["pos"]))
        h += '<div class="qc">'
        for j, c in enumerate(it["choices"]):
            h += '<div><span class="mk">%s</span>%s</div>' % (CIRCLE[j], esc(c))
        h += '</div></div>'
    h += '</div>'
    # 解答欄（2段。列数は問数から）
    h += '<div class="ansbox"><div class="ttl">解答欄</div>'
    per = (n + 1) // 2
    for lo in range(1, n + 1, per):
        cols = list(range(lo, min(lo + per, n + 1)))
        h += '<table class="grid"><tr>'
        h += "".join('<th>%d</th>' % c for c in cols)
        h += '</tr><tr>' + '<td></td>' * len(cols) + '</tr></table>'
    h += '</div>'
    h += foot("%s 第%d回" % (META["series"], t["no"]))
    return h


def stats(tests):
    """★表紙の数字はここで実データから数える。ハードコードすると、回や語数を変えたときに
    表紙だけ古い数字が残る（この事故は過去の問題集で実際に起きている）。"""
    n_test = len(tests)
    per = sorted({len(t["items"]) for t in tests})
    idi = sum(1 for t in tests for it in t["items"] if it["pos"] == "熟")
    total = sum(len(t["items"]) for t in tests)
    return {"tests": n_test, "per": per[0] if len(per) == 1 else None,
            "total": total, "idiom": idi, "word": total - idi,
            "idiom_per": idi // n_test, "word_per": (total - idi) // n_test}


def cefr_stats(tests):
    """★表紙のレベル記述も実データから数える。_cefr_levels.tsv と突き合わせて
    「リストで裏が取れた語」と「根拠が無い語」を分けて返す。

    ★Oxford 3000/5000 は**頻度上位5000語の抜粋**であって A1〜B1 の網羅リストではない。
      そこに載っていない語を「B2 以上」と断じてはいけない (2026-08-19 のレビュー指摘。
      pillow / kettle / strawberry のような日常語も載っていない)。
      表紙では「リスト内で裏が取れた分」と「リスト外」を必ず分けて書く。
    """
    ORDER = ["A1", "A2", "B1", "B2", "C1"]
    POS = {"動": "verb", "名": "noun", "形": "adjective", "副": "adverb"}
    lv = {}
    with open(os.path.join(HERE, "_cefr_levels.tsv"), encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            w, pos, level = (x.strip() for x in line.rstrip("\n").split("\t"))
            lv[(w.lower(), pos)] = level.upper()
    total = listed = b2plus = notlisted = 0
    for t in tests:
        for it in t["items"]:
            if it["pos"] == "熟":
                continue
            total += 1
            w = it["word"].strip().lower()
            ent = {p: x for (ww, p), x in lv.items() if ww == w}
            if not ent:
                continue                      # check_cefr.py が FAIL させる
            pos_en = POS.get(it["pos"])
            if pos_en in ent:
                cur = ent[pos_en]
            elif "-" in ent:
                cur = ent["-"]
            else:
                cur = sorted(ent.values(), key=lambda x: ORDER.index(x) if x in ORDER else 99)[0]
            if cur == "NOT_LISTED":
                notlisted += 1
            else:
                listed += 1
                if ORDER.index(cur) >= ORDER.index("B2"):
                    b2plus += 1
    return {"total": total, "listed": listed, "b2plus": b2plus, "notlisted": notlisted}


def build_cover(tests):
    s = stats(tests)
    cs = cefr_stats(tests)
    return ('<div class="cover"><div class="ttl">英検準1級</div>'
            '<div class="ttl2">単語テスト</div><div class="rule"></div>'
            '<div class="sub">4択・全%d回 × %d問 = %d問（単語%d・熟語%d）</div>'
            '<div class="spec">品詞とテーマでまとめた全%d回。'
            # ★数字は cefr_stats() が _cefr_levels.tsv から数える (ハードコード禁止)。
            #   check_cefr.py が同じ数を独立に数え直して刷り上がりと突き合わせる。
            '収録語%d語のうち、Oxford 3000/5000 に載る%d語は%d語が CEFR B2 以上。'
            '残り%d語は同リスト外（頻出上位5000語より外）の語です。<br>'
            '各回 単語%d問 ＋ 熟語・句動詞%d問　・　1問1点 %d点満点<br>'
            '解答・用例・派生語メモつき（解答解説編は別冊）</div>'
            '<div class="howto"><b>▶ 使い方</b><br>'
            '① 1回分は5〜7分で解く。辞書は見ない。<br>'
            '② 答えは選択肢の番号を解答欄に書く。<br>'
            '③ 採点したら、<b>間違えた語と「迷って当たった語」に印をつける</b>。<br>'
            '④ <b>返却された解答解説編</b>の用例（コロケーション）を声に出して読む。'
            '単語単体でなく<b>かたまりで覚える</b>のが準1級の語彙対策の要点。<br>'
            '⑤ 3日後にもう一度、印のついた語だけを解き直す。<br>'
            '<b>▶ 目標</b>　%d点／%d点。<b>%d点以下</b>の回は必ず再テストする。</div>'
            '<div class="brand">%s</div>'
            '<div class="disc">%s</div></div>'
            % (s["tests"], s["per"], s["total"], s["word"], s["idiom"],
               s["tests"],
               cs["total"], cs["listed"], cs["b2plus"], cs["notlisted"],
               s["word_per"], s["idiom_per"], s["per"],
               int(s["per"] * 0.8), s["per"], int(s["per"] * 0.8) - 1,
               esc(META["brand"]), esc(META["note"])))


def build_mondai(tests):
    PB = '<div class="pb"></div>'
    return build_cover(tests) + PB + PB.join(render_test(t) for t in tests)


# ==================== 解答解説編 ====================
def build_answer_index(tests):
    # ★このページだけは生徒に渡してはいけない（全回の正解が1枚に載るため）。
    #   冊子を丸ごと渡すと、第1回の返却時点で残り全部の答えが手に渡る。
    h = band("解答一覧", "指導者控え<br>%s" % esc(META["brand"]))
    h += ('<div class="instr"><b>★このページは指導者控えです。生徒に渡さないでください。</b>'
          '全%d回の正解が1枚に載っているため、渡すと以降の回の答えが伝わります。'
          '丸つけはこのページだけで完結します。（縦＝回、横＝問題番号）</div>'
          % len(tests))
    h += '<table class="all"><tr><th style="width:13mm"></th>'
    # 列数は実データから。20固定にすると回ごとの問数を変えたとき表と中身がずれる
    h += "".join('<th>%d</th>' % n for n in range(1, max(len(t["items"]) for t in tests) + 1))
    h += '</tr>'
    for t in tests:
        h += '<tr><td class="lbl">第%d回</td>' % t["no"]
        h += "".join('<td>%d</td>' % (it["answer"] + 1) for it in t["items"])
        h += '</tr>'
    h += '</table>'
    h += foot("%s 解答一覧" % META["series"])
    return h


def render_key(t):
    h = band("第%d回 解答・解説" % t["no"], "準1級 / Pre-1<br>%s" % esc(META["brand"]))
    h += '<div class="secttl">第%d回<small>%s</small></div>' % (t["no"], esc(t["title"]))
    h += ('<table class="key"><tr><th style="width:7mm">No</th><th style="width:33mm">語</th>'
          '<th style="width:8mm">答</th><th style="width:44mm">意味</th>'
          '<th style="width:48mm">用例（かたまりで覚える）</th><th>メモ</th></tr>')
    for it in t["items"]:
        h += ('<tr><td class="c-no">%d</td>'
              '<td><span class="wd">%s</span> <span class="ps">%s</span></td>'
              '<td class="c-a">%d</td><td>%s</td>'
              '<td><span class="use">%s</span><br><span class="usej">%s</span></td>'
              '<td class="note">%s</td></tr>'
              % (it["n"], esc(it["word"]), esc(it["pos"]), it["answer"] + 1, esc(it["gloss"]),
                 esc(it["usage_en"]), esc(it["usage_ja"]), esc(it["note"])))
    h += '</table>'
    h += foot("%s 第%d回 解答・解説" % (META["series"], t["no"]))
    return h


def build_kaisetsu(tests):
    PB = '<div class="pb"></div>'
    s = stats(tests)
    # ★ここも実データから数える。以前「全10回 × 20語 = 200語」とベタ書きしていて、
    #   400語に増やしたとき**解答解説編の表紙だけ 200語のまま**刷られた（問題編は正しかった）。
    cover = ('<div class="cover"><div class="ttl">英検準1級</div>'
             '<div class="ttl2">単語テスト　解答・解説編</div><div class="rule"></div>'
             '<div class="sub">全%d回 × %d語 = %d語　／　用例・派生語つき</div>'
             % (s["tests"], s["per"], s["total"]) +
             '<div class="howto"><b>▶ 指導者の方へ</b><br>'
             '★<b>この冊子を丸ごと生徒に渡さないでください</b>。全%d回分の答えが綴じてあるため、'
             '第1回の返却で渡すと残り%d回の答えが全部伝わります。<br>'
             '<b>生徒には、実施した回のページ（1回＝1ページ）だけを切り離して渡してください。</b>'
             '★この冊子は<b>片面で印刷</b>してください。両面だと1枚の裏に次の回の答えが載ります。<br>'
             '次ページの「解答一覧」は<b>指導者控え</b>です。<br>'
             '「用例」は必ず音読させてください。準1級の語彙は単語単体でなく'
             '<b>コロケーション（かたまり）で問われます</b>。<br>'
             '「メモ」の ★ は綴りや意味が紛らわしく、実際に受験生が取り違える語です。</div>'
             % (s["tests"], s["tests"] - 1) +
             '<div class="brand">%s</div><div class="disc">%s</div></div>'
             % (esc(META["brand"]), esc(META["note"])))
    return (cover + PB + build_answer_index(tests) + PB
            + PB.join(render_key(t) for t in tests))


# ==================== PDF ====================
def to_pdf(pairs):
    """pairs = [(html_path, out_pdf_ascii_name, desktop_japanese_name), ...]
    ★Chrome の file:// キャッシュ対策で毎回「一度も使っていないディレクトリ」経由にする。
    ★日本語ファイル名は NFD/NFC 不一致で読めなくなるので、英数字で生成→最後に mv。"""
    stage = os.path.join(HERE, "_pdfstage", "run%d" % int(time.time()))
    os.makedirs(stage, exist_ok=True)
    desktop = os.path.expanduser("~/Desktop")
    made = []
    for src, ascii_name, ja_name in pairs:
        tmp_html = os.path.join(stage, os.path.basename(src))
        shutil.copyfile(src, tmp_html)
        tmp_pdf = os.path.join(stage, ascii_name)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf=" + tmp_pdf, "--virtual-time-budget=8000",
                        "file://" + tmp_html], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dest = os.path.join(desktop, ja_name)
        shutil.copyfile(tmp_pdf, dest)
        made.append(dest)
        print("  PDF:", dest, "(%.1f KB)" % (os.path.getsize(dest) / 1024))
    return made


# ==================== main ====================
def main():
    tests = assign(TESTS)

    import check
    ok = check.run(tests, verbose=True)
    if not ok:
        print("\n[build] ★ゲート NG のため HTML を書き出しません（壊れたデータを下流へ流さない）")
        sys.exit(1)

    outputs = {
        "mondai.html": doc("%s 問題編" % META["series"], build_mondai(tests)),
        "kaisetsu.html": doc("%s 解答解説編" % META["series"], build_kaisetsu(tests)),
    }
    # ★表紙の数字が実データとずれていないか、書き出した HTML を読み返して確かめる。
    #   200語→400語に増やしたとき、問題編の表紙は stats() 由来で正しかったのに
    #   **解答解説編の表紙だけベタ書きの「全10回 × 20語 = 200語」が残って刷られた**。
    #   「数えて作る」だけでは足りず、「刷る直前に読み返す」層が要る。
    #   ★走査するのは**表紙の中だけ**にすること。HTML 全体に掛けると <style> に埋めた
    #     コメント（「実測: 全20回で qw=50mm…」）まで拾い、表紙を触っていないのにビルドが
    #     止まって犯人を偽る。回数を変えた瞬間に必ず踏む。
    s = stats(tests)
    for fn, content in outputs.items():
        m = re.search(r'<div class="cover">.*?</div>\s*(?=<div class="pb">|$)', content, re.S)
        cover = m.group(0) if m else ""
        if not cover:
            print("[build] ★%s に表紙が見つからない（検査が空回りするので中止）" % fn)
            sys.exit(1)
        stale = [x for x in re.findall(r"全(\d+)回", cover) if int(x) != s["tests"]]
        stale += [x for x in re.findall(r"=\s*(\d+)語", cover) if int(x) != s["total"]]
        stale += [x for x in re.findall(r"=\s*(\d+)問", cover) if int(x) != s["total"]]
        if stale:
            print("[build] ★%s の表紙の数字が実データ（全%d回 %d語）と違う: %s"
                  % (fn, s["tests"], s["total"], stale))
            sys.exit(1)

    for fn, content in outputs.items():
        with open(os.path.join(HERE, fn), "w", encoding="utf-8") as f:
            f.write(content)
    with open(os.path.join(HERE, "resolved.json"), "w", encoding="utf-8") as f:
        json.dump(tests, f, ensure_ascii=False, indent=1)
    n = sum(len(t["items"]) for t in tests)
    print("[build] wrote", " / ".join(outputs), "| 全%d回 %d語" % (len(tests), n))

    if "--pdf" in sys.argv:
        to_pdf([
            (os.path.join(HERE, "mondai.html"), "mondai.pdf",
             "英検準1級_単語テスト_問題編.pdf"),
            (os.path.join(HERE, "kaisetsu.html"), "kaisetsu.pdf",
             "英検準1級_単語テスト_解答解説編.pdf"),
        ])


if __name__ == "__main__":
    main()
