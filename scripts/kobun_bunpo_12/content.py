# -*- coding: utf-8 -*-
"""古典文法 十二講 完全演習 — 単一ソース。

講義（スタディサプリ 高3 古文〈文法編〉全12講）の**単元の並びに1対1で対応**させた
演習プリント。1部＝1講。講義を見た直後にその部を解く使い方を想定している。
★講義テキストの例文・解説は一切複製していない（塾のオリジナル問題）。
  対応させているのは「各講が扱う文法項目とその順番」という事実だけ。

組版・機械ゲート・盲検証は英文法問題集と共有する（データだけがここにある）:
  WORKBOOK_DIR=scripts/kobun_bunpo_12 python3 scripts/eng_kokkoritsu_nankan/build.py

★設問データは data/L01.json 〜 L12.json（1講1ファイル）。
  Python に直書きしないのは、12講×13問を並列で書かせたときに構文エラーで全体が
  死ぬのを避けるため。JSON なら1ファイル壊れてもその講だけが落ちる。
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tables import TABLES, FLOWS  # noqa: E402

# 問題編に印字してよいフィールド（★ここに exp / point / ans / model を足さないこと。
# 足した瞬間に「答えが問題編に載る」＝知識ゼロで得点できる冊子になる）
Q_FIELDS = ("stem", "choices", "frame", "tokens", "ja", "src", "inst",
            "given", "hint", "context")


def _load_parts():
    """data/L*.json を講番号順に読み、満点を実データから計算して返す。"""
    parts = []
    for path in sorted(glob.glob(os.path.join(HERE, "data", "L*.json"))):
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        # ★満点は必ずデータから出す。手書きすると問数を変えたときに表紙だけ嘘になる
        p["total"] = sum(len(s["items"]) * s["pt"] for s in p["sections"])
        p["univ"] = f'スタディサプリ 高3 古文〈文法編〉 {p["ref"]} に対応'
        parts.append(p)
    if not parts:
        raise SystemExit(f"設問データが無い: {os.path.join(HERE, 'data')}/L*.json")
    return parts


BOOK = {
    "title": "古典文法 十二講 完全演習",
    "sub": "講義対応ドリル／用言・助動詞・助詞・敬語・識別",
    "series": "国語（古文）",
    "file": "古典文法_十二講_完全演習",
    "lang": "ja",
    "intro": [
        ("この冊子の使い方",
         "講義の全12講と、この冊子の第1部〜第12部が一対一で対応しています。"
         "第○講を見終わったら、その日のうちに第○部を解いてください。"
         "対応表は次のページにあります。"
         "まとめて後から解くより、見た直後に解くほうが定着します。"),
        ("講義との関係",
         "この冊子は塾が独自に作った演習問題です。"
         "講義テキストの例文や解説を写したものではありません。"
         "対応させているのは「各講がどの文法項目を扱うか」という順番だけなので、"
         "同じ範囲を別の問題で解き直すことになります。"
         "つまり講義の復習として使えます。"),
        ("進め方（基本の確認→解説→基本問題→応用問題）",
         "各部の扉に「この部の解き方」を三手順で示してあります。"
         "解く前にその三手順を声に出して確認し、"
         "一問ごとに手順のどこで答えが決まったかを言えるようにしてください。"
         "答え合わせのときは、解答解説編の解説（なぜそうなるか）と"
         "▶ポイント（次に使える形）の二つを読みます。"),
        ("解き方の約束",
         "①まず傍線部の直前の語の活用形を言う。②接続から候補を絞る。"
         "③主語・呼応の副詞・文脈で意味を決める。"
         "この三手順を、答えが分かっている問題でも省かないこと。"
         "手順を飛ばして当てた問題は、本番で外れます。"),
        ("採点のしかた",
         "四択・空所補充・文法的説明は、解答と一致していれば正解です"
         "（解答編に併記した別解も可）。"
         "現代語訳だけは模範解答と一字一句同じである必要はありません。"
         "解答編に示した「採点のポイント」を1つ満たすごとに2点を与えてください。"
         "ポイントは文法事項の意味を落としていないかを見るもので、"
         "模範解答と同じ言い回しである必要はありません。"),
        ("一覧表について",
         "活用表・接続表・助詞一覧・敬語一覧は、あえてこの問題編には載せていません。"
         "表が手元にあると、接続や活用を問う設問を表から写すだけで解けてしまい、"
         "覚えたかどうかが分からなくなるからです。"
         "表と覚え方（語呂合わせ）、識別のフローチャートは、"
         "解答解説編の巻頭に「基本の確認」としてまとめてあります。"
         "解き終わってから、答え合わせと一緒に確認してください。"),
    ],
    # ★解答解説編の巻頭に置く「基本の確認」。問題編には絶対に出さない。
    "tables": TABLES,
    "flows": FLOWS,
    "parts": _load_parts(),
}

KIND_LABEL = {
    "mc": "四択",
    "fill": "記述",
    "jtrans": "現代語訳",
    "trans": "古文で書く",
    "error": "誤り指摘",
    "order": "語順整序",
    "ident": "文法的説明",
    "rewrite": "書き換え",
}
# 採点要素で採る（唯一解が無い）出題形式
ELEMENT_KINDS = ("trans", "jtrans")


def all_items():
    """(part, section, item, 通し表示名) を順に返す。"""
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for i, it in enumerate(s["items"], start=1):
                where = f'第{p["no"]}部 大問{s["no"]}-{i}'
                yield p, s, it, where


def frame_text():
    """問題編のうち「設問そのもの以外」＝表紙・前書き・部扉・大問見出し・指示文。"""
    buf = [BOOK["title"], BOOK["sub"]]
    for h, b in BOOK["intro"]:
        buf += [h, b]
    for p in BOOK["parts"]:
        buf += [p["level"], p["univ"], p["aim"]] + list(p.get("steps", []))
        for s in p["sections"]:
            buf += [s["title"], s["inst"]]
    return "\n".join(buf)


def question_text(exclude=None):
    """問題編に印字される全テキスト（解答漏洩ゲートの走査対象）。"""
    buf = [frame_text()]
    for p in BOOK["parts"]:
        for s in p["sections"]:
            for it in s["items"]:
                if it is exclude:
                    continue
                for f in Q_FIELDS:
                    v = it.get(f)
                    if isinstance(v, list):
                        buf += [str(x) for x in v]
                    elif v:
                        buf.append(str(v))
    return "\n".join(buf)
