#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""夏の勉強合宿(8/5〜8/8)の学習計画表を PDF 化する。

  python3 build_plan.py

合宿で配られる紙の〈学習計画表①②〉の時限割(初日は4限50分から、2〜3日目は1〜9限、
最終日は1〜3限)にそのまま書き写せる形で組む。
"""
import os, sys, subprocess, datetime
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
MATH = os.path.abspath(os.path.join(HERE, "..", "math_workbook"))
sys.path.insert(0, MATH)
import build_html as B          # noqa: E402  CHROME / stamp_pdf / esc

OUT = os.path.join(HERE, "gasshuku_gakushu_keikaku.pdf")
# ★宛名はコードに書かない（PUBLIC リポジトリ）。刷るときだけ環境変数で渡す:
#   STUDENT_NAME="姓 名" python3 build_plan.py    空なら宛名なしの汎用版。
STUDENT = os.environ.get("STUDENT_NAME", "")
BOOK = "夏の勉強合宿 学習計画"

# (時限, 分, 教科, 内容[紙に書き写す], ねらい[書かなくてよい])
DAYS = [
    {
        "date": "8月5日(水)", "label": "初日", "total": 410,
        "goal": "化学の第1編（気体と液体）を1周し、×はその日のうちに解き直す",
        "note": "移動の疲れがあるので、暗記もの→計算ものの順に立ち上げる。初日から数学を2コマ入れて"
                "「合宿はここまでやる」という基準を体に入れてしまう。",
        "rows": [
            ("4", 50, "国語", "古文単語 1〜100（赤シートで2周）＋今日の目標を書く",
             "移動直後は頭が重い。手を動かすだけで進む暗記から入る"),
            ("5", 90, "化学", "総復習 C01・C02・C03（気体と液体 18問）",
             "状態方程式は理論化学すべての土台。ここを最初に固める"),
            ("6", 90, "数学", "第2集 13→15→16（18問）",
             "13で「数えて割る」を固めてから15に入ると、15が新しい公式ではなく数え直しに見える"),
            ("7", 45, "化学", "第1編の×だけ解き直し（解説をノートに写す）",
             "6限に数学をはさんだので、思い出す負荷がかかって定着する"),
            ("8", 45, "英語", "長文 第1問 The Paradox of Choice の語彙先読み＋通読1回",
             "明日の本番前の下ごしらえ。設問はまだ解かない"),
            ("9", 90, "数学", "第2集 14 独立試行と反復試行（12問）＋6限の×を解き直し",
             "確率をもう1コマ続けて、確率は初日のうちに一区切りつける"),
        ],
    },
    {
        "date": "8月6日(木)", "label": "2日目", "total": 675,
        "goal": "漸化式を、単元名を見なくても「どの型か」当てられるようにする",
        "note": "合宿でいちばん時間が取れる日。漸化式は「どの型か」を当てられるかが勝負なので、"
                "型の見分け→帰納法→特性方程式→階差→SnとAn の順で一気に通す。",
        "rows": [
            ("1", 45, "国語", "古文単語 1〜100 再テスト＋101〜200 インプット",
             "前日やった100語を先にテスト。思い出せない語だけ印をつける"),
            ("2", 90, "化学", "総復習 C04・C05・C06（状態変化・溶解度・希薄溶液 18問）",
             "溶解度と凝固点降下は計算の型が決まっている。朝いちの計算枠に置く"),
            ("3", 90, "数学", "第2集 17→21→18（16問）",
             "★21は3問しかない。18より前に置いて「型を覚える1枚」として独立させる"),
            ("4", 90, "英語", "長文 第1問（時間を計って設問→答え合わせ→構文解説→音読3回）",
             "昨日下読みしてあるので、今日は本番の速さで解ける"),
            ("5", 90, "化学", "総復習 C07・C08・C09（反応エンタルピー・ヘスの法則 18問）",
             "ΔH は符号（発熱＝マイナス）だけ間違える人が多い。まとめて1コマで慣れる"),
            ("6", 90, "数学", "第2集 19 階差型→20 SnとAn（11問）＋3限の×を再テスト",
             "合言葉は 階差＝「上端は n−1」、SnとAn＝「n=1 だけ別扱い」"),
            ("7", 45, "化学", "第2編・第3編の×だけ解き直し",
             "その日のうちに×を0にして寝る。翌日に持ち越さない"),
            ("8", 45, "英語", "英作文 基本例文30（和文英訳・声に出して書く）",
             "長文の後に書く側へ回すと、読んだ表現がそのまま使える"),
            ("9", 90, "数学", "数学II 式と証明（剰余の定理・因数定理・部分分数分解）",
             "持参の問題集。★ここが唯一の予備枠——×が溜まっていたら、この90分を回収に充てる"),
        ],
    },
    {
        "date": "8月7日(金)", "label": "3日目", "total": 675,
        "goal": "化学平衡の計算を、変化量表（最初／変化／平衡）を書いて最後まで出しきる",
        "note": "疲れが出る3日目。ベクトルは頭が動く中盤に置き、計算中心のΣ・等差等比を最終コマに回した。"
                "いちばん大事なものを、いちばん疲れた枠に置かないための入れ替え。",
        "rows": [
            ("1", 45, "国語", "古文単語 101〜200 再テスト＋201〜300 インプット",
             "3日で300語。テスト→新規の順は崩さない"),
            ("2", 90, "化学", "総復習 C10・C11・C12（反応の速さとしくみ 18問）",
             "反応速度式の次数は、実験データの表から決める型を体で覚える"),
            ("3", 90, "数学", "第2集 22 漸化式の総仕上げ（6問）＋前日の×を再テスト",
             "★単元名が解法を教えてくれない本番形式。漸化式はここが本当の総仕上げ"),
            ("4", 90, "英語", "長文 第2問 Language and the Construction of Reality",
             "第1問と同じ手順（解く→答え合わせ→構文→音読3回）で回す"),
            ("5", 90, "化学", "総復習 C13・C14・C15（化学平衡・ルシャトリエ・電離平衡 18問）",
             "理論化学の山場。変化量表を必ず書いてから式を立てる"),
            ("6", 90, "数学", "第2集 25→26→27 ベクトルの総仕上げ（21問）",
             "★「もう大丈夫」と思っている所ほど穴が残る。ベクトルはここでまとめて確認する"),
            ("7", 45, "化学", "第4編・第5編の×だけ解き直し",
             "平衡の×は必ずその日に潰す。翌日は電池で頭を使う"),
            ("8", 45, "英語", "自由英作文の型（意見＋理由2つ＋結論／60〜80語を1本）",
             "型を1つ持っておくと本番で手が止まらない"),
            ("9", 90, "数学", "第2集 23 Σの計算→24 等差・等比の和（20問）",
             "自分から「もう一度やりたい」と言っていた分野。計算中心なので最終コマ向き"),
        ],
    },
    {
        "date": "8月8日(土)", "label": "最終日", "total": 225,
        "goal": "合宿で×だった問題を、何も見ずに解けるところまで戻す",
        "note": "残り3コマ。新しいことは1コマだけにして、あとは全部「×の回収」に使う。"
                "ここで回収しきれなかった問題が、下山後にやることの中身になる。",
        "rows": [
            ("1", 45, "国語", "古文単語 1〜300 総再テスト（×だけ書き出す）",
             "書き出した×が、そのまま帰ってからの単語リストになる"),
            ("2", 90, "化学", "総復習 C16・C17・C18（電池と電気分解 18問）",
             "電気分解は計算が決まっている。最後に持ってきても得点になる分野"),
            ("3", 90, "総仕上げ", "化学 第6編の× → 数学 第2集で2回×だった問題 → 英語 第1・2問の音読",
             "教科をまたいで×だけを拾う。最後の音読は「やりきった」で終わるため"),
        ],
    },
]

SUBJ_MIN = {}
for d in DAYS:
    for _, m, s, _, _ in d["rows"]:
        SUBJ_MIN[s] = SUBJ_MIN.get(s, 0) + m

MOCHIMONO = [
    "数列・確率・ベクトル 基礎徹底問題集［第2集］弱点集中トレーニング（＋自己採点シート）",
    "化学［理論］総復習トレーニング（＋自己採点シート）　※今回の合宿用",
    "英語長文読解 難関国公立大学対策テキスト",
    "数学II の問題集（式と証明のところ）",
    "古文単語帳（学校のもの）",
    "赤シート・付箋・ノート（解説を写す用）・時計",
]

AFTER = [
    ("8月11日(月)", "合宿で×だった問題だけを通しで解き直す（化学 → 数学の順・60分）"),
    ("8月18日(月)", "2回とも×だった問題だけをもう一度（30分）。2回連続で○になったらクリア"),
    ("提出", "自己採点シート2枚（数学第2集・化学）の写真を送る。×と△の番号が読めるように撮る"),
]

CSS = """
@page { size: A4; margin: 14mm 13mm 12mm 13mm; }
* { box-sizing: border-box; }
body { font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif; color:#1a1a1a;
       font-size:9.4pt; line-height:1.6; margin:0; }
.head { border-bottom:2.4px solid #1f3a5f; padding-bottom:7px; margin-bottom:12px; }
.head h1 { color:#1f3a5f; font-size:19pt; margin:0; letter-spacing:1px; }
.head .sub { color:#444; font-size:10.5pt; margin-top:3px; }
.head .who { float:right; color:#1f3a5f; font-size:11pt; margin-top:-30px;
             border-bottom:1.4px solid #c8a24e; padding:0 12px 3px; }
.lead { background:#f4f6f9; border-left:3px solid #c8a24e; padding:7px 11px; margin-bottom:9px;
        font-size:8.9pt; line-height:1.5; color:#333; }
.lead b { color:#1f3a5f; }
h2.day { color:#fff; background:#1f3a5f; font-size:12pt; margin:14px 0 0; padding:5px 10px; }
h2.day .lab { font-size:9.5pt; opacity:.85; margin-left:10px; }
h2.day .tot { float:right; font-size:9.5pt; opacity:.85; font-weight:normal; }
.goal { border:1.1px solid #1f3a5f; border-top:none; padding:5px 10px; font-size:9.4pt; }
.goal b { color:#1f3a5f; }
.why { color:#555; font-size:8.4pt; line-height:1.5; padding:3px 10px 5px;
       border:1.1px solid #1f3a5f; border-top:none; background:#fbfcfd; }
table { border-collapse:collapse; width:100%; margin-top:5px; }
th { background:#e8edf3; color:#1f3a5f; font-size:8.6pt; font-weight:normal;
     border:0.6px solid #9fb0c3; padding:3px 5px; }
td { border:0.6px solid #9fb0c3; padding:3px 6px; vertical-align:top; }
td.k { text-align:center; font-weight:bold; color:#1f3a5f; white-space:nowrap; width:13mm; }
td.k small { display:block; font-weight:normal; color:#8a8a8a; font-size:7.6pt; }
td.s { text-align:center; white-space:nowrap; width:16mm; font-weight:bold; }
td.c { width:74mm; }
td.n { color:#555; font-size:8.5pt; }
.s-数学 { color:#1f3a5f; } .s-化学 { color:#2d7a4f; } .s-英語 { color:#a03030; }
.s-国語 { color:#7a5aa0; } .s-総仕上げ { color:#b06a1f; }
/* 1日分(帯+目標+ねらい+時限表)が途中で改ページされると、紙の計画表に写すとき
   ページをめくりながらになって使いものにならない。日ごとに塊で改ページする。 */
.dayblock { break-inside:avoid; page-break-inside:avoid; }
.two { display:flex; gap:10px; margin-top:12px; break-inside:avoid; page-break-inside:avoid; }
.box { flex:1; border:1.1px solid #1f3a5f; padding:6px 10px; }
.box h3 { color:#1f3a5f; font-size:10pt; margin:0 0 4px; }
.box ul { margin:0; padding-left:15px; }
.box li { margin-bottom:1px; font-size:8.5pt; line-height:1.45; }
.after td { font-size:8.5pt; padding:2.5px 5px; }
.after td.d { white-space:nowrap; font-weight:bold; color:#1f3a5f; width:26mm; }
.tally { margin-top:10px; font-size:9pt; color:#333; }
.tally span { display:inline-block; border:1px solid #9fb0c3; border-radius:3px;
              padding:2px 9px; margin-right:6px; background:#f7f9fb; }
.tally b { color:#1f3a5f; }
.pb { page-break-before:always; }
.foot { margin-top:12px; color:#8a8a8a; font-size:8pt; }
"""


def rows_html(d):
    tr = []
    for k, m, s, c, n in d["rows"]:
        tr.append(f'<tr><td class="k">{k}限<small>{m}分</small></td>'
                  f'<td class="s s-{s}">{B.esc(s)}</td>'
                  f'<td class="c">{B.esc(c)}</td>'
                  f'<td class="n">{B.esc(n)}</td></tr>')
    return "".join(tr)


def day_html(d):
    return ('<div class="dayblock">'
            f'<h2 class="day">{d["date"]}　【{d["label"]}】'
            f'<span class="tot">この日の学習 {d["total"]}分 = {d["total"]//60}時間{d["total"]%60:02d}分</span></h2>'
            f'<div class="goal"><b>目標：</b>{B.esc(d["goal"])}</div>'
            f'<div class="why">{B.esc(d["note"])}</div>'
            '<table><tr><th>時限</th><th>教科</th><th>内容（そのまま計画表に書き写す）</th>'
            '<th>ねらい（書かなくてよい）</th></tr>'
            f'{rows_html(d)}</table></div>')


def build():
    today = datetime.date.today().strftime("%Y年%m月%d日")
    total = sum(d["total"] for d in DAYS)
    tally = "".join(
        f'<span>{k}　<b>{v//60}時間{v%60:02d}分</b></span>'
        for k, v in sorted(SUBJ_MIN.items(), key=lambda kv: -kv[1]))
    mochi = "".join(f"<li>{B.esc(x)}</li>" for x in MOCHIMONO)
    after = "".join(f'<tr><td class="d">{B.esc(a)}</td><td>{B.esc(b)}</td></tr>' for a, b in AFTER)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<style>{CSS}</style></head><body>
<div class="head"><h1>夏の勉強合宿　学習計画</h1>
  <div class="sub">2026年8月5日(水)〜8日(土)　全27コマ・{total//60}時間{total%60:02d}分</div>
  <div class="who">{B.esc(STUDENT)} さん</div></div>

<div class="lead"><b>この計画の考え方</b><br>
合宿の{total//60}時間を、<b>数学＝第2集の104問を1冊やりきる</b>、<b>化学＝理論6分野を1周する</b>、
<b>英語＝長文2本を完全に仕上げる</b>、<b>古文単語＝300語を3回まわす</b>、の4本に絞りました。
科目を増やすより、<b>「合宿が終わったときに終わっているもの」を先に決める</b>ほうが計画は守れます。<br>
配置のルールは3つだけです。①<b>90分の枠には必ず「解く」ものを置く</b>（読むだけ・覚えるだけは45分枠へ）。
②<b>同じ教科を続けない</b>（間に別教科をはさむと、思い出す負荷がかかって記憶に残る）。
③<b>×はその日のうちに解き直す</b>（45分枠を毎日そのために空けてあります）。<br>★化学の90分×18問は1問5分でかなり速いペースです。<b>時間内に終わらなければ［発展］は飛ばして、×の解き直しを優先</b>してください。飛ばした問題は下山後に回します。</div>

<div class="tally">教科別の合計：{tally}</div>

<div class="two">
  <div class="box"><h3>持ち物（これだけあれば計画は回ります）</h3><ul>{mochi}</ul></div>
  <div class="box"><h3>「下山後の学習に対する決意」に書くこと</h3>
    <table class="after">{after}</table>
    <div style="margin-top:6px;color:#555;font-size:8.6pt;">
    合宿でやった問題は、<b>日をあけてもう一度</b>解かないと定着しません。
    上の2つの日付を先に決めて計画表の決意欄に書いておくと、帰ってからの迷いがなくなります。</div>
  </div>
</div>

{day_html(DAYS[0])}
{day_html(DAYS[1])}
{day_html(DAYS[2])}
{day_html(DAYS[3])}

<div class="foot">{today}　トリリオン AI塾　／　※「内容」欄をそのまま紙の〈学習計画表①②〉に書き写してください。
一番右の「ねらい」は書き写す必要はありません（なぜその順番なのかの説明です）。</div>
</body></html>"""


def main():
    html_path = os.path.join(HERE, "_build_plan.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build())
    subprocess.run([B.CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=15000", f"--print-to-pdf={OUT}",
                    "file://" + html_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    B.stamp_pdf(OUT, BOOK)
    d = fitz.open(OUT)
    total = sum(x["total"] for x in DAYS)
    print(f"WROTE {OUT} | pages: {d.page_count} | 総学習 {total}分 | 内訳 {SUBJ_MIN}")
    d.close()


if __name__ == "__main__":
    main()
