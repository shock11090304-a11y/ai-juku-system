# -*- coding: utf-8 -*-
"""英検準1級 ライティング対策プリント ビルダー (3 冊)

    python3 scripts/eiken_junichi/writing/build.py          # _out/ に 3 冊を書き出す
    OUT_DIR=~/Desktop python3 scripts/eiken_junichi/writing/build.py

    ① コツと進め方   … 全体像・要約/意見論述のコツ (例題つき)・よくあるミス・表現集・進め方・10週間プラン・チェックリスト
    ② 問題 6セット   … Set ごとに 大問4 要約 1 題 + 大問5 意見論述 1 題 (書き込み式)
    ③ 解答例と解説   … 解答例・段落の要点・言い換え表・削った情報・構成・使える表現・逆の立場の骨子

★ data/*.json が**唯一の正典**。3 冊とも同じデータから作るので、問題と解答例の食い違いは構造的に起きない。
★ 相互チェック (CLAUDE.md 2026-08-16):
  ① check_pdf.py が刷り上がり PDF から本文・解答例を抜き出して data と全数照合
  ② check.py が語数・丸写し・言い換えの実在・POINTS・立場の一貫性を機械検査
  ③ 英文の校閲と、本文だけを渡した盲検 (段落の要点の抽出) を別担当が行い、指摘を data に反映
★ 公開リポジトリ: 生徒の氏名は書かない (宛名なしの汎用版)。
"""
import glob
import html
import json
import os
import shutil
import subprocess
import sys

import guide

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.expanduser(os.environ.get("OUT_DIR", os.path.join(HERE, "_out")))

BRAND = "トリリオンAI塾"
NOTE = ("本書は公益財団法人 日本英語検定協会とは無関係の、学習用オリジナル問題です。"
        "英検®は公益財団法人 日本英語検定協会の登録商標です。")
SERIES = "英検準1級 ライティング対策"

# ★check_pdf.py もこの名前で PDF を探す
BOOKS = {
    "guide": "英検準1級ライティング_1_コツと進め方.pdf",
    "mondai": "英検準1級ライティング_2_問題6セット.pdf",
    "kaitou": "英検準1級ライティング_3_解答例と解説.pdf",
}

SUMMARY_LINES = 10
ESSAY_LINES = 18

esc = html.escape


def wc(text):
    return len(text.split())


def load():
    ex = json.load(open(os.path.join(DATA, "examples.json"), encoding="utf-8"))
    sets = [json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(DATA, "set*.json"))]
    return ex, sorted(sets, key=lambda d: d["no"])


def highlight(text, phrases):
    """text の中の phrases (重ならないもの) に蛍光ペンをかけた HTML を返す。"""
    spans = []
    for ph in sorted(set(phrases), key=len, reverse=True):
        i = text.find(ph)
        if i >= 0 and all(i >= b or i + len(ph) <= a for a, b in spans):
            spans.append((i, i + len(ph)))
    out, pos = [], 0
    for a, b in sorted(spans):
        out.append(esc(text[pos:a]))
        out.append(f'<span class="hl">{esc(text[a:b])}</span>')
        pos = b
    out.append(esc(text[pos:]))
    return "".join(out)


# ------------------------------------------------------------------ 部品
# 指示文は本番と同じく英語 (2025年度から要約の語数は「目安」ではなく指定: Summarize it between 60 and 70 words.)
SUMMARY_INSTR = ('<span class="en">● Read the article below and summarize it in your own words as far as possible in English.'
                 '<br>● Summarize it between 60 and 70 words.</span>'
                 '<br><span class="small">（英文を読み、できるだけ<b>自分の言葉で</b>英語で要約する。語数は <b>60〜70語</b>'
                 '（2025年度からは「目安」ではなく<b>指定</b>）。）</span>')
ESSAY_INSTR = ('<span class="en">● Write an essay on the given TOPIC.<br>● Use TWO of the POINTS below to support your answer.'
               '<br>● Structure: introduction, main body, and conclusion<br>● Suggested length: 120–150 words</span>'
               '<br><span class="small">（TOPIC について意見を書く。理由には POINTS から <b>2つ</b> を使う。'
               '構成は序論・本論・結論。語数の目安は <b>120〜150語</b>。）</span>')


def time_label(no, kind):
    """② の帯に出す時間。① の「6 問題演習の進め方」「7 10週間プラン」と同じ段階にする。"""
    if no == 1:
        return "時間無制限・辞書OK"
    if no <= 3:
        return "目安 20分" if kind == "summary" else "目安 25分"
    return "本番ペース 15分" if kind == "summary" else "本番ペース 20分"


def lines(n):
    return ('<div class="lines">' +
            "".join(f'<div class="ln" data-n="{i}"></div>' for i in range(1, n + 1)) + "</div>")


def summary_problem(band, s, no):
    paras = "".join(f"<p>{esc(p)}</p>" for p in s["paras"])
    return (f'<div class="qband"><span class="set">{band}</span><span class="kind">大問4　要約</span>'
            f'<span class="lim">60〜70語 ／ {time_label(no, "summary")}</span></div>'
            f'<div class="instr">{SUMMARY_INSTR}</div>'
            f'<div class="psg en">{paras}</div>'
            f'<div class="memo" style="min-height:21mm">メモ（第1段落 ／ 第2段落 ／ 第3段落 の要点を日本語で1行ずつ）</div>'
            f'{lines(SUMMARY_LINES)}<div class="wcbox">語数 <span></span> 語　／　かかった時間 <span></span> 分</div>')


def topic_box(e):
    pts = "".join(f"<li>{esc(p)}</li>" for p in e["points"])
    return (f'<div class="topicbox"><div class="lab">TOPIC</div><div class="topic en">{esc(e["topic"])}</div>'
            f'<div class="lab">POINTS</div><ul class="en">{pts}</ul></div>')


def essay_problem(band, e, no):
    return (f'<div class="qband"><span class="set">{band}</span><span class="kind">大問5　意見論述</span>'
            f'<span class="lim">120〜150語 ／ {time_label(no, "essay")}</span></div>'
            f'<div class="instr">{ESSAY_INSTR}</div>{topic_box(e)}'
            f'<div class="memo">メモ（立場 ／ 使う POINTS 2つ ／ それぞれの説明と具体例）</div>'
            f'{lines(ESSAY_LINES)}<div class="wcbox">語数 <span></span> 語　／　かかった時間 <span></span> 分</div>')


def roles_table(s):
    tr = "".join(f'<tr><td style="width:17%"><b>第{i}段落</b><br><span class="tag">{esc(r["role"])}</span></td>'
                 f'<td>{esc(r["point_ja"])}</td></tr>' for i, r in enumerate(s["para_roles"], 1))
    return f'<table class="t">{tr}</table>'


def paraphrase_table(s):
    tr = "".join(f'<tr><td class="en src">{esc(p["src"])}</td><td class="arrow">→</td>'
                 f'<td class="en"><b>{esc(p["dst"])}</b></td><td style="width:19%" class="small">{esc(p["how"])}</td></tr>'
                 for p in s["paraphrases"])
    return (f'<table class="t pp"><tr><th>本文</th><th class="arrow"></th><th>解答例</th><th>技</th></tr>{tr}</table>')


def omitted_list(s):
    li = "".join(f'<li><span class="en">{esc(o["src"])}</span>　…　{esc(o["why_ja"])}</li>' for o in s["omitted"])
    return f"<ul>{li}</ul>"


def model_box(title, text, phrases):
    return (f'<div class="model"><div class="mh">{title}（{wc(text)}語）</div>'
            f'<div class="en">{highlight(text, phrases)}</div></div>')


def essay_map(e):
    tags = [("intro", "序論", ""), ("body1", "本論1", e["used_points"][0]),
            ("body2", "本論2", e["used_points"][1]), ("concl", "結論", "")]
    rows = []
    phrases = [x["en"] for x in e["expressions"]]
    for (cls, name, pt), para in zip(tags, e["paras"]):
        ptxt = f'<span class="wc">POINT: <span class="en">{esc(pt)}</span></span>' if pt else ""
        rows.append(f'<div class="pr"><div class="side"><span class="tag {cls}">{name}</span>{ptxt}'
                    f'<span class="wc">{wc(para)}語</span></div>'
                    f'<div class="en">{highlight(para, phrases)}</div></div>')
    total = sum(wc(p) for p in e["paras"])
    return (f'<div class="model"><div class="mh">解答例（{total}語・立場：'
            f'{"賛成" if e["stance"] == "agree" else "反対"}）</div><div class="pmap">{"".join(rows)}</div></div>')


def expressions_table(e):
    tr = "".join(f'<tr><td class="en" style="width:48%"><b>{esc(x["en"])}</b></td><td>{esc(x["ja"])}</td></tr>'
                 for x in e["expressions"])
    return f'<table class="t">{tr}</table>'


def opposite_box(e):
    o = e["opposite"]
    side = "反対" if e["stance"] == "agree" else "賛成"
    rs = "".join(f'<li><b>POINT: <span class="en">{esc(r["point"])}</span></b><br>'
                 f'<span class="en">{esc(r["topic_en"])}</span><br><span class="small">{esc(r["support_ja"])}</span></li>'
                 for r in o["reasons"])
    return (f'<div class="opp"><div class="oh">逆の立場（{side}）で書くなら — 骨子</div>'
            f'<div class="en">{esc(o["stance_en"])}</div><ol>{rs}</ol>'
            f'<div class="small muted">★ 第8〜9週に、この骨子を使って自分で120〜150語に仕上げる。</div></div>')


# ------------------------------------------------------------------ ① コツと進め方
def book_guide(ex, sets):
    s, e = ex["summary"], ex["essay"]
    h = []
    h.append(f"""
<div class="cover-top"><div class="kicker">EIKEN GRADE PRE-1 ／ WRITING</div>
<div class="title">英検準1級<br>ライティング対策プリント</div>
<div class="vol">① コツと進め方</div>
<div class="lead">要約（60〜70語）と意見論述（120〜150語）の「型」と「言い換え」を身につけ、<br>6セットの演習で本番の点を取りにいくためのプリントです。</div></div>
<div class="brand">{BRAND}</div>
<div class="box"><div class="bh">このプリントは3冊セット</div>
<table class="t"><tr><th style="width:26%">① コツと進め方</th><td>いちばん最初に読む。例題2つを自分でも書いてみる</td></tr>
<tr><th>② 問題 6セット</th><td>1週間に1セット（要約1題＋意見論述1題）。書き込み式なので印刷して使う</td></tr>
<tr><th>③ 解答例と解説</th><td>書き終えてから開く。言い換え表・構成・逆の立場の骨子つき</td></tr></table></div>
<div class="box tip"><div class="bh">目次</div>
<table class="t" style="margin:0"><tr><td>1　ライティングの全体像</td><td>5　使える表現集</td></tr>
<tr><td>2　要約のコツ（例題つき）</td><td>6　問題演習の進め方</td></tr>
<tr><td>3　意見論述のコツ（例題つき）</td><td>7　試験までの10週間プラン</td></tr>
<tr><td>4　よくあるミス</td><td>8　セルフチェックリスト</td></tr></table></div>
<div class="box key"><div class="bh">今日からやること</div><ol>
<li>このプリントの 1〜5 を読む（全部覚えなくてよい。「型」と「言い換えの3つの技」だけは押さえる）</li>
<li>例題の要約・意見論述を自分でも書いてみる（時間無制限。難しければ解答例を読んでから、何も見ずに書く形でOK）</li>
<li>来週から ② の Set 1 へ。書き直した答案を LINE で送ってください</li></ol></div>
<p class="foot-note">{NOTE}</p>""")
    h.append('<div class="pb"></div>' + guide.overview())
    h.append('<div class="pb"></div>' + guide.summary_tips())
    paras = "".join(f'<p><span class="tag" style="font-family:\'Noto Sans JP\',sans-serif">第{i}段落</span> {esc(p)}</p>'
                    for i, p in enumerate(s["paras"], 1))
    memo = "".join(f"<li>{esc(m)}</li>" for m in s["memo_ja"])
    h.append(f"""<div class="pb"></div>
<h2 class="sec"><span class="no">2</span>要約の例題<small>{esc(s["type_ja"])}</small></h2>
<div class="instr">{SUMMARY_INSTR}</div>
<div class="psg en">{paras}</div>
<div class="step"><div class="s">STEP 1</div><div><b>段落の役割をつかむ</b>{roles_table(s)}</div></div>
<div class="step"><div class="s">STEP 2</div><div><b>要点を日本語でメモ（3行）</b><ul>{memo}</ul></div></div>""")
    h.append(f"""<div class="step"><div class="s">STEP 3</div><div><b>言い換える</b>（本文の表現を自分の言葉に）{paraphrase_table(s)}
<b>削った情報</b>{omitted_list(s)}</div></div>
<div class="step"><div class="s">STEP 4</div><div><b>書いて、語数を数える</b>
{model_box("解答例", s["model"], [p["dst"] for p in s["paraphrases"]])}
<p class="small">★ 黄色の部分が言い換え。{esc(s["note_ja"])}</p></div></div>""")
    h.append('<div class="pb"></div>' + guide.essay_tips())
    memo = "".join(f"<li>{esc(m)}</li>" for m in e["memo_ja"])
    h.append(f"""<div class="pb"></div><div class="compact">
<h2 class="sec"><span class="no">3</span>意見論述の例題</h2>
<div class="instr">{ESSAY_INSTR}</div>{topic_box(e)}
<div class="step"><div class="s">STEP 1</div><div><b>POINTS を見て立場を決め、メモを作る</b>（4分）<ul>{memo}</ul></div></div>
<div class="step"><div class="s">STEP 2</div><div><b>型に流し込んで書く</b>（黄色は使える表現）{essay_map(e)}</div></div>
<div class="step"><div class="s">STEP 3</div><div><b>見直す</b>　{esc(e["note_ja"])}</div></div>
{opposite_box(e)}</div>""")
    h.append('<div class="pb"></div>' + guide.mistakes())
    h.append('<div class="pb"></div><div class="compact">' + guide.expressions() + '</div>')
    h.append('<div class="pb"></div>' + guide.howto())
    h.append('<div class="pb"></div>' + guide.plan())
    h.append('<div class="pb"></div>' + guide.checklist())
    return "\n".join(h)


# ------------------------------------------------------------------ ② 問題
def book_mondai(ex, sets):
    tr = "".join(f'<tr><td><b>Set {d["no"]}</b></td><td>{esc(d["summary"]["theme_ja"])}</td>'
                 f'<td class="en">{esc(d["essay"]["topic"])}</td><td></td><td></td></tr>' for d in sets)
    h = [f"""
<div class="cover-top"><div class="kicker">EIKEN GRADE PRE-1 ／ WRITING</div>
<div class="title">英検準1級<br>ライティング対策プリント</div>
<div class="vol">② 問題 6セット</div>
<div class="lead">1セット＝大問4 要約 1題 ＋ 大問5 意見論述 1題（本番の筆記と同じ組み合わせ）。<br>印刷して、解答欄に直接書き込んで使います。</div></div>
<div class="brand">{BRAND}</div>
<h3 class="sub">進み具合の記録</h3>
<table class="t"><tr><th style="width:9%">Set</th><th style="width:22%">要約のテーマ</th><th>意見論述の TOPIC</th><th style="width:11%">実施日</th><th style="width:11%">LINE 送信</th></tr>{tr}</table>
<div class="box tip"><div class="bh">使い方（くわしくは ① の「6 問題演習の進め方」）</div><ol>
<li>時間を計って書く（Set 1 は時間無制限・辞書OK → Set 2・3 は 要約20分／意見論述25分 → Set 4 から本番ペース 15分／20分）</li>
<li>語数を数えて、① の「8 セルフチェックリスト」で確認する</li>
<li>③ の解答例と比べ、自分の答案を<b>何も見ずに書き直す</b></li>
<li>書き直した答案を写真に撮って LINE で送る → 添削して返します</li></ol></div>
<div class="box"><div class="bh">解答欄について</div>手書きだと1行に10語前後が目安です。要約は6〜7行、意見論述は12〜15行ほどで語数の範囲に入ります
（字の大きさで変わるので、必ず語数を数えること）。解答欄の右端の小さな数字は行数です。</div>
<p class="foot-note">{NOTE}</p>"""]
    for d in sets:
        h.append('<div class="pb"></div>' + summary_problem(f'Set {d["no"]}', d["summary"], d["no"]))
        h.append('<div class="pb"></div>' + essay_problem(f'Set {d["no"]}', d["essay"], d["no"]))
    return "\n".join(h)


# ------------------------------------------------------------------ ③ 解答例と解説
def book_kaitou(ex, sets):
    h = [f"""
<div class="cover-top"><div class="kicker">EIKEN GRADE PRE-1 ／ WRITING</div>
<div class="title">英検準1級<br>ライティング対策プリント</div>
<div class="vol">③ 解答例と解説</div>
<div class="lead">必ず自分で書き終えてから開くこと。解答例は「正解」ではなく「一つの書き方」です。<br>
内容・構成がそろっていれば、表現が違っていても点はとれます。</div></div>
<div class="brand">{BRAND}</div>
<div class="box tip"><div class="bh">解説の読み方</div><ul>
<li><b>要約</b>：（1）段落ごとの要点 → 自分の答案に3つとも入っているか ／（2）言い換え表 → 同じ箇所を自分ならどう言い換えるか ／（3）削った情報 → 自分が書いてしまっていないか</li>
<li><b>意見論述</b>：（1）段落ごとの語数と役割を自分の答案と比べる ／（2）黄色の「使える表現」を表現ストックノートへ ／（3）「逆の立場で書くなら」は第8〜9週の演習で使う</li>
<li>解答例は、黄色の部分（要約＝言い換え／意見論述＝使える表現）を中心に<b>音読</b>すると、自分の表現として使えるようになります</li></ul></div>
<p class="foot-note">{NOTE}</p>"""]
    for d in sets:
        s, e = d["summary"], d["essay"]
        h.append(f"""<div class="pb"></div>
<div class="qband"><span class="set">Set {d["no"]}</span><span class="kind">大問4　要約　解答例と解説</span><span class="lim">{esc(s["theme_ja"])}</span></div>
{model_box("解答例", s["model"], [p["dst"] for p in s["paraphrases"]])}
<h4 class="mini">段落の役割と要点（{esc(s["type_ja"])}）</h4>{roles_table(s)}
<h4 class="mini">言い換え（解答例の黄色の部分）</h4>{paraphrase_table(s)}
<h4 class="mini">削った情報</h4>{omitted_list(s)}
<div class="box warn"><div class="bh">ワンポイント</div>{esc(s["note_ja"])}</div>""")
        h.append(f"""<div class="pb"></div>
<div class="qband"><span class="set">Set {d["no"]}</span><span class="kind">大問5　意見論述　解答例と解説</span></div>
<div class="small"><b>TOPIC</b>　<span class="en">{esc(e["topic"])}</span>　／　<b>POINTS</b>　<span class="en">{esc(" / ".join(e["points"]))}</span></div>
{essay_map(e)}
<h4 class="mini">使える表現（解答例の黄色の部分）</h4>{expressions_table(e)}
<div class="box warn"><div class="bh">ワンポイント</div>{esc(e["note_ja"])}</div>
{opposite_box(e)}""")
    return "\n".join(h)


# ------------------------------------------------------------------ 出力
def find_chrome():
    cands = [os.environ.get("CHROME", ""),
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    cands += sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"), reverse=True)
    cands += [shutil.which(x) or "" for x in ("google-chrome", "chromium", "chromium-browser")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome / Chromium が見つからない (env CHROME で指定できる)")


def doc(title, body, foot, body_class=""):
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    foot_css = ('@page { @bottom-left { content: "%s"; font: 7.4pt "Noto Sans JP", "Hiragino Kaku Gothic ProN", sans-serif;'
                ' color: #94a3b8; } }' % foot.replace('"', "'"))
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f'<style>{css}\n{foot_css}</style></head><body class="{body_class}">{body}</body></html>')


def render(key, title, body, body_class=""):
    os.makedirs(OUT, exist_ok=True)
    out_pdf = os.path.join(OUT, BOOKS[key])
    tmp = os.path.join(HERE, f"_{key}.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(doc(title, body, f"{title}　｜　{BRAND}", body_class))
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={out_pdf}", "file://" + tmp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.environ.get("KEEP_HTML"):
        os.remove(tmp)
    print(f"WROTE {out_pdf}")
    return out_pdf


def main():
    ex, sets = load()
    render("guide", f"{SERIES} ① コツと進め方", book_guide(ex, sets))
    render("mondai", f"{SERIES} ② 問題6セット", book_mondai(ex, sets))
    render("kaitou", f"{SERIES} ③ 解答例と解説", book_kaitou(ex, sets), "compact")


if __name__ == "__main__":
    main()
