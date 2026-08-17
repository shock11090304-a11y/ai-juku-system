# -*- coding: utf-8 -*-
"""英検準1級 オリジナル模擬試験 (一次・筆記) ビルダー

    python3 scripts/eiken_junichi/mogi/build.py            # 全回
    python3 scripts/eiken_junichi/mogi/build.py no02       # 回を絞る

単一ソース data_no*.json → 問題編 / 解答解説編 の HTML を生成する。
HTML → Chrome --headless --print-to-pdf で A4 PDF 化 (make_pdf.py)。

構成 (2024年度以降の新形式に準拠):
    大問1 短文の語句空所補充  (1)〜(18)
    大問2 長文の語句空所補充  (19)〜(24)   2パッセージ × 3空所
    大問3 長文の内容一致選択  (25)〜(31)   2パッセージ (4問 + 3問)
    大問4 English Summary     60〜70語
    大問5 English Composition 意見論述 (TOPIC + POINTS)

★ この JSON が**唯一の正典**。問題編と解説編は同じデータから作るので、
  「問題の選択肢と解説の選択肢が違う」ずれは構造的に起きない。
★ 相互チェック (CLAUDE.md 2026-08-16): ① check.py が正解キー・空所整合・
  正解位置分布・引用の実在を機械検査 ② 目隠し二重解答 (make_blind.py で
  答えを伏せた版を作り、独立に解かせて突き合わせ) ③ 人手で正解の一意性を再読。
"""
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

BRAND = "トリリオンAI塾"
NOTE = "本書は公益財団法人 日本英語検定協会とは無関係の、学習用オリジナル問題です。"

CSS = """
* { box-sizing: border-box; }
@page { size: A4; margin: 15mm 14mm 16mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
  color:#151515; font-size:10pt; line-height:1.72; margin:0; }
.en { font-family: Georgia,"Times New Roman",serif; }
.band { background:linear-gradient(90deg,#0b1f4b,#1d4ed8); color:#fff; padding:10px 14px;
  border-radius:8px; display:flex; justify-content:space-between; align-items:center; }
.band .l { font-size:15pt; font-weight:700; }
.band .l small { font-size:9.5pt; font-weight:600; opacity:.92; margin-left:8px; }
.band .r { text-align:right; font-size:9pt; line-height:1.45; }
.band .r b { font-size:12.5pt; }
.subline { margin:7px 2px 3px; font-size:9pt; color:#475569; }
.metarow { display:flex; gap:9px; margin:9px 0 8px; font-size:9.5pt; }
.metarow .cell { border:1px solid #cbd5e1; border-radius:6px; padding:4px 10px; flex:1; }
.metarow .cell.score { flex:0 0 128px; text-align:center; }
.note { font-size:8.6pt; color:#64748b; margin:2px 2px 8px; }

/* 大問見出し — 帯の中に指示文まで入れる (対策問題集 build.py と同じ設計) */
.partttl { background:#0b1f4b; color:#fff; border-radius:6px; padding:6px 14px;
  margin:15px 0 9px; page-break-after:avoid; }
.partttl .t { font-size:13pt; font-weight:700; letter-spacing:.02em; }
.partttl .t small { font-weight:600; font-size:9pt; opacity:.85; margin-left:9px; }
.partttl .i { display:block; font-weight:400; font-size:8.9pt; opacity:.93; margin-top:3px;
  line-height:1.5; }

/* 設問 — 番号は濃紺のバッジ。設問文は幅いっぱいに置く (折り返しの段差を作らない) */
.item { margin:0 0 11px; page-break-inside:avoid; }
.item .no { display:inline-block; background:#0b1f4b; color:#fff; border-radius:4px;
  min-width:22px; text-align:center; padding:1px 6px; font-size:9pt; font-weight:700;
  margin-bottom:3px; }
.item .stem { font-size:10.2pt; line-height:1.75; }
.ch { display:flex; flex-wrap:wrap; gap:2px 20px; margin-top:3px; }
.ch span { font-size:10pt; }
.ch.v { flex-direction:column; gap:2px; }
.ch.v span { margin-left:12px; }
.ch .cn { font-weight:700; margin-right:3px; }

.instr { font-size:9.3pt; background:#f1f5f9; border-left:4px solid #0b1f4b;
  padding:6px 11px; border-radius:4px; margin:0 0 9px; color:#334155;
  page-break-after:avoid; }

/* 空所 — 枠で囲まず下線にする (本番の見え方に近い) */
.fill { display:inline-block; min-width:74px; border-bottom:1.4px solid #0f172a;
  margin:0 3px; vertical-align:baseline; }
.cloze { font-weight:700; color:#0b1f4b; white-space:nowrap; }

/* 長文 */
.ptitle { font-size:11.5pt; font-weight:700; color:#0f172a; margin:12px 0 5px;
  border-bottom:2px solid #0b1f4b; padding-bottom:3px; page-break-after:avoid; }
.ptitle .pwc { float:right; font-size:8.4pt; color:#94a3b8; font-weight:600; padding-top:4px; }
.psg { margin:5px 0 10px; }
.psg .en { text-align:justify; line-height:1.8; font-size:10.1pt; }
.psg .en p { margin:0 0 6px; }
.wbox { border:1px solid #cbd5e1; border-radius:7px; padding:9px 12px; margin:6px 0; }
.wbox ul { margin:4px 0 6px 18px; padding:0; font-size:9.4pt; }
.lines { border:1px solid #cbd5e1; border-radius:6px; height:118px; margin-top:5px;
  background:repeating-linear-gradient(#fff 0 25px,#e2e8f0 25px 26px); }
.lines.tall { height:210px; }
.sect { margin-top:15px; }
.sect h3 { font-size:11.5pt; margin:0 0 6px; border-left:5px solid #1d4ed8; padding-left:8px; }
table.ans { width:100%; border-collapse:collapse; font-size:9.2pt; }
table.ans th, table.ans td { border:1px solid #cbd5e1; padding:3px 6px; vertical-align:top; }
table.ans th { background:#eff6ff; }
table.ans td.c { text-align:center; font-weight:700; width:34px; }
table.ans tr { page-break-inside:avoid; }
.exp { margin:0 0 10px; page-break-inside:avoid; }
.exp .h { font-weight:700; font-size:10pt; background:#f1f5f9; border-radius:4px;
  padding:2px 8px; display:inline-block; }
.exp .h .ok { color:#047857; margin-left:8px; }
.exp .w { font-family:Georgia,serif; font-weight:700; }
.exp .ja { margin:3px 0 0; }
.exp .dis { font-size:9.2pt; color:#475569; margin-top:2px; }
.model { border:1px solid #93c5fd; background:#eff6ff; border-radius:7px; padding:8px 11px;
  margin:5px 0; font-size:9.6pt; }
.model .en { line-height:1.85; }
.foot { text-align:center; color:#64748b; font-size:8.2pt; margin-top:10px; padding-top:4px;
  border-top:1px solid #e2e8f0; page-break-inside:avoid; }
.pb { page-break-after:always; }
"""


def esc(s):
    return html.escape(str(s), quote=False)


def doc(title, inner):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body>{inner}</body></html>')


def band(d, kind):
    m = d["meta"]
    return (f'<div class="band"><div class="l">実用英語技能検定 準1級 '
            f'<small>一次試験・筆記 オリジナル模擬試験</small></div>'
            f'<div class="r">{esc(m["level_note"])}<br><b>第{esc(m["no"])}回</b></div></div>'
            f'<div class="subline">Grade Pre-1 Practice Test '
            f'&nbsp;/&nbsp; {esc(m["sections"])} &nbsp;/&nbsp; 目標 {esc(m["minutes"])}分 '
            f'&nbsp;/&nbsp; {esc(kind)}</div>')


def foot(d, kind):
    return (f'<div class="foot">{BRAND} ／ 英検準1級 オリジナル模擬試験 '
            f'第{esc(d["meta"]["no"])}回 ・ {esc(kind)}<br>{esc(NOTE)}</div>')


def circled(i):
    """選択肢の番号。① 〜 ④ (U+2460〜) を使う。

    ★ 丸数字は JIS X 0208 にあり、刷るフォント (Hiragino / Yu Gothic) に必ず在るので
      豆腐にならない。対策問題集 build.py も同じ字を使って刷れている。
    """
    return "①②③④"[i]


def part_head(n, title, en, instr):
    """大問の見出し帯。指示文まで帯の中に入れる。"""
    return (f'<div class="partttl"><div class="t">大問{n}　{esc(title)}'
            f'<small>{esc(en)}</small>'
            f'<span class="i">{esc(instr)}</span></div></div>')


def choices_inline(choices, vertical=False):
    cls = "ch v" if vertical else "ch"
    body = "".join(f'<span class="en"><span class="cn">{circled(k)}</span>{esc(c)}</span>'
                   for k, c in enumerate(choices))
    return f'<div class="{cls}">{body}</div>'


def stem_with_fill(sentence):
    """本文中の ( ) を下線の空所にする。枠で囲まない。

    ★ ここを変えると**刷り上がり PDF の文字列が変わる**。掲載ページを実測している
      make_bundle.py の probe は、この関数と同じ規則 (BLANK_RE を消す) で作ること。
    """
    return BLANK_RE.sub('<span class="fill">&nbsp;</span>', esc(sentence))


# ============================ 問題編 ============================
def build_mondai(d):
    m = d["meta"]
    h = band(d, "問題編")
    h += (f'<div class="metarow"><div class="cell">氏名</div>'
          f'<div class="cell">日付　　　　／</div>'
          f'<div class="cell score">得点　　　／ {m["full"]}</div></div>')
    h += f'<div class="note">{esc(NOTE)}　{esc(m["instruction"])}</div>'

    # --- 大問1 ---
    h += part_head(1, "短文の語句空所補充", "Vocabulary & Phrasal Verbs",   # esc() が通すので生の &
                   "次の各文の空所に入れるのに最も適切なものを ①〜④ から一つ選びなさい。")
    for i, it in enumerate(d["part1"], 1):
        h += (f'<div class="item"><span class="no">{i}</span>'
              f'<div class="stem en">{stem_with_fill(it["sentence"])}</div>'
              f'{choices_inline(it["choices"])}</div>')

    # --- 大問2 ---
    h += '<div class="pb"></div>'
    h += part_head(2, "長文の語句空所補充", "Gap-fill in Context",
                   "次の英文を読み、その文意にそって空所に入れるのに最も適切なものを "
                   "①〜④ から一つ選びなさい。")
    n = 19
    for ps in d["part2"]:
        wc = len(" ".join(ps["text"]).split())
        h += (f'<div class="ptitle en">{esc(ps["title"])}'
              f'<span class="pwc">約{int(round(wc / 10.0) * 10)} words</span></div>')
        h += f'<div class="psg"><div class="en">{render_gap_text(ps["text"], n)}</div></div>'
        for b in ps["blanks"]:
            h += (f'<div class="item"><span class="no">{n}</span>'
                  f'{choices_inline(b["choices"])}</div>')
            n += 1

    # --- 大問3 ---
    h += '<div class="pb"></div>'
    h += part_head(3, "長文の内容一致選択", "Reading Comprehension",
                   "次の英文の内容に関して、質問に対して最も適切なもの、または英文の内容と"
                   "一致するものを ①〜④ から一つ選びなさい。")
    for ps in d["part3"]:
        wc = len(" ".join(ps["paras"]).split())
        h += (f'<div class="ptitle en">{esc(ps["title"])}'
              f'<span class="pwc">約{int(round(wc / 10.0) * 10)} words</span></div>')
        h += ('<div class="psg"><div class="en">'
              + "".join(f"<p>{esc(p)}</p>" for p in ps["paras"]) + '</div></div>')
        for q in ps["questions"]:
            h += (f'<div class="item"><span class="no">{n}</span>'
                  f'<div class="stem en">{esc(q["q"])}</div>'
                  f'{choices_inline(q["choices"], vertical=True)}</div>')
            n += 1

    # --- 大問4 要約 ---
    h += '<div class="pb"></div>'
    w = d["part4"]
    h += ('<div class="partttl"><div class="t">大問4　English Summary（要約）'
          '<small>60〜70 words</small></div></div>')
    h += ('<div class="instr">● 以下の英文を読み、その内容を <b>60語〜70語</b> の英語で要約しなさい。'
          '<br>● できる限り自分自身の言葉で書くこと。</div>')
    h += f'<div class="psg"><div class="en">'
    h += "".join(f"<p>{esc(p)}</p>" for p in w["summary"]["paras"])
    h += '</div></div><div class="lines tall"></div>'

    # --- 大問5 意見論述 ---
    h += '<div class="pb"></div>'
    e = w["essay"]
    h += ('<div class="partttl"><div class="t">大問5　English Composition（意見論述）'
          '<small>120〜150 words</small></div></div>')
    h += ('<div class="instr">● 以下の TOPIC について、あなたの意見とその理由を述べる英文を書きなさい。'
          '<br>● POINTS から <b>2つ</b> を選び、それぞれについて理由を述べること。'
          '<br>● 語数の目安は <b>120語〜150語</b>。</div>')
    h += (f'<div class="wbox"><b>TOPIC</b><div class="en">{esc(e["topic"])}</div>'
          f'<b>POINTS</b><ul class="en">')
    h += "".join(f"<li>{esc(p)}</li>" for p in e["points"])
    h += '</ul></div><div class="lines tall"></div><div class="lines tall"></div>'

    h += foot(d, "問題編")
    return doc(f'英検準1級 模擬試験 第{m["no"]}回 問題編', h)


# ★ 空所の正典パターン。make_bundle.py が probe を作るときにもこれを import して使う
#   (別々に書くと、刷り上がりの文字列と probe がずれて掲載ページを見失う)。
BLANK_RE = re.compile(r"\(\s*\)")            # 大問1 の空所 "( )"
GAP_RE = re.compile(r"\(\s*(\d+)\s*\)")     # 大問2 の空所 "( 19 )"


def render_gap_text(text, start_no):
    """本文中の ( 19 ) を空所枠に描く。番号は JSON に書かれたものをそのまま使う。"""
    def rep(mo):
        return f'<span class="cloze">（&nbsp;{mo.group(1)}&nbsp;）</span>'
    return "".join(f"<p>{GAP_RE.sub(rep, esc(p))}</p>" for p in text)


# ============================ 解説編 ============================
def build_kaisetsu(d):
    m = d["meta"]
    h = band(d, "解答・解説編")
    h += ('<div style="text-align:center;font-weight:700;font-size:12pt;margin:8px 0 3px;">'
          '解答・解説編</div>'
          '<div style="text-align:center;font-size:9pt;color:#475569;margin-bottom:9px;">'
          '解答一覧 ／ 大問1 語彙の全解説 ／ 大問2 談話の根拠 ／ 大問3 段落要旨と選択肢処理 ／ '
          '要約・意見論述の解答例</div>')

    # --- 解答一覧 ---
    keys = answer_keys(d)
    h += '<div class="sect"><h3>解答一覧 <small>Answer Key</small></h3><table class="ans"><tr>'
    for no, a in keys:
        h += f'<th>({no})</th>'
    h += '</tr><tr>'
    for no, a in keys:
        h += f'<td class="c">{a}</td>'
    h += '</tr></table></div>'

    # --- 大問1 ---
    h += '<div class="sect"><h3>大問1 ｜ 短文の語句空所補充</h3>'
    for i, it in enumerate(d["part1"], 1):
        ans = it["answer"]
        h += (f'<div class="exp"><div class="h">({i}) '
              f'<span class="ok">正解 {ans + 1}　'
              f'<span class="w">{esc(it["choices"][ans])}</span></span></div>'
              f'<div class="ja"><b>{esc(it.get("pos", ""))}</b> {esc(it["gloss_ja"])}</div>'
              f'<div class="ja">和訳：{esc(it["trans_ja"])}</div>')
        if it.get("distractors_ja"):
            h += ('<div class="dis">他の選択肢：'
                  + " ／ ".join(f'<span class="w">{esc(k)}</span> {esc(v)}'
                                for k, v in it["distractors_ja"].items()) + '</div>')
        h += '</div>'
    h += '</div>'

    # --- 大問2 ---
    h += '<div class="sect"><h3>大問2 ｜ 長文の語句空所補充</h3>'
    for ps in d["part2"]:
        h += (f'<div class="exp"><div class="h en">{esc(ps["title"])}</div>'
              f'<div class="ja">{esc(ps["summary_ja"])}</div></div>')
        for b in ps["blanks"]:
            h += (f'<div class="exp"><div class="h">({b["no"]}) '
                  f'<span class="ok">正解 {b["answer"] + 1}　'
                  f'<span class="w">{esc(b["choices"][b["answer"]])}</span></span></div>'
                  f'<div class="ja">{esc(b["exp_ja"])}</div></div>')
    h += '</div>'

    # --- 大問3 ---
    h += '<div class="sect"><h3>大問3 ｜ 長文の内容一致選択</h3>'
    for ps in d["part3"]:
        h += (f'<div class="exp"><div class="h en">{esc(ps["title"])}</div>'
              f'<div class="ja">{esc(ps["summary_ja"])}</div></div>')
        for q in ps["questions"]:
            h += (f'<div class="exp"><div class="h">({q["no"]}) '
                  f'<span class="ok">正解 {q["answer"] + 1}</span></div>'
                  f'<div class="ja">設問：{esc(q["q_ja"])}</div>'
                  f'<div class="ja">{esc(q["exp_ja"])}</div></div>')
    h += '</div>'

    # --- 大問4・5 ---
    w = d["part4"]
    h += '<div class="sect"><h3>大問4 ｜ English Summary（要約）</h3>'
    h += f'<div class="exp"><div class="ja">{esc(w["summary"]["outline_ja"])}</div></div>'
    h += (f'<div class="model"><b>解答例（{w["summary"]["model_words"]} words）</b>'
          f'<div class="en">{esc(w["summary"]["model"])}</div></div>')
    h += f'<div class="exp"><div class="ja">{esc(w["summary"]["points_ja"])}</div></div></div>'

    e = w["essay"]
    h += '<div class="sect"><h3>大問5 ｜ English Composition（意見論述）</h3>'
    h += f'<div class="exp"><div class="ja">{esc(e["outline_ja"])}</div></div>'
    h += (f'<div class="model"><b>解答例（{e["model_words"]} words）</b>'
          f'<div class="en">{esc(e["model"])}</div></div>')
    h += f'<div class="exp"><div class="ja">{esc(e["points_ja"])}</div></div></div>'

    h += foot(d, "解答・解説編")
    return doc(f'英検準1級 模擬試験 第{m["no"]}回 解答解説編', h)


def answer_keys(d):
    """(通し番号, 正解番号) の一覧。問題編の番号付けと同じ規則で決定論的に作る。"""
    out = []
    n = 1
    for it in d["part1"]:
        out.append((n, it["answer"] + 1))
        n += 1
    for ps in d["part2"]:
        for b in ps["blanks"]:
            out.append((n, b["answer"] + 1))
            n += 1
    for ps in d["part3"]:
        for q in ps["questions"]:
            out.append((n, q["answer"] + 1))
            n += 1
    return out


def main():
    only = sys.argv[1:] or None
    files = sorted(glob.glob(os.path.join(HERE, "data_no*.json")))
    if only:
        files = [f for f in files if any(k in os.path.basename(f) for k in only)]
    if not files:
        print("✗ data_no*.json が見つかりません")
        return 1
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        tag = os.path.splitext(os.path.basename(f))[0].replace("data_", "")
        mo = build_mondai(d)
        ka = build_kaisetsu(d)
        for name, body in ((f"mondai_{tag}.html", mo), (f"kaisetsu_{tag}.html", ka)):
            with open(os.path.join(HERE, name), "w", encoding="utf-8") as fp:
                fp.write(body)
            print(f"[ok] {name} ({len(body) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
