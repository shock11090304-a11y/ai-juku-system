# -*- coding: utf-8 -*-
"""draft_*.json（第11〜20回の原稿）を content.py に追記する。

★原稿を信用せず、ここで契約を検査してから入れる:
  - plan_11_20.json の語と**完全一致**（追加・削除・綴り違いを許さない）
  - 20語ちょうど / 誤答3つ / 必須フィールドが空でない
  - 誤答が正解と同一、誤答どうしが同一 でない
契約に落ちたら1文字も書かずに終了する（半端に入ると原因が追えなくなる）。
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS = ["draft_11_12.json", "draft_13_14.json", "draft_15_16.json",
          "draft_17_18.json", "draft_19_20.json"]
FIELDS = ("word", "pos", "gloss", "distractors", "usage_en", "usage_ja", "note")


def die(msg):
    print("[merge] NG %s" % msg)
    sys.exit(1)


def load():
    plan = json.load(io.open(os.path.join(HERE, "plan_11_20.json"), encoding="utf-8"))
    out = {}
    for fn in DRAFTS:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            die("%s が無い（担当が未完了）" % fn)
        out.update(json.load(io.open(p, encoding="utf-8")))
    return plan, out


def check(plan, drafts):
    for no in map(str, range(11, 21)):
        if no not in drafts:
            die("第%s回の原稿が無い" % no)
        items = drafts[no]
        want = plan[no]["words"] + plan[no]["idioms"]
        if len(items) != 20:
            die("第%s回が%d語（20語であること）" % (no, len(items)))
        got = [it.get("word", "") for it in items]
        if got != want:
            miss = [w for w in want if w not in got]
            extra = [w for w in got if w not in want]
            die("第%s回の語が割り当てと違う 不足=%s 余分=%s 順序違い=%s"
                % (no, miss, extra, got != want and not miss and not extra))
        for it in items:
            for f in FIELDS:
                if not it.get(f):
                    die("第%s回 %s: %s が空" % (no, it.get("word"), f))
            d = it["distractors"]
            if len(d) != 3:
                die("第%s回 %s: 誤答が%d個" % (no, it["word"], len(d)))
            if len(set(d)) != 3:
                die("第%s回 %s: 誤答どうしが同一 %s" % (no, it["word"], d))
            brief = it["gloss"].split("、")[0].split("／")[0]
            if brief in d or it["gloss"] in d:
                die("第%s回 %s: 誤答が正解と同一" % (no, it["word"]))
            # ★`not in "動名形副熟"` は部分文字列判定になり、pos="動名" が素通りする
            if it["pos"] not in ("動", "名", "形", "副", "熟"):
                die("第%s回 %s: pos が不正 %r" % (no, it["word"], it["pos"]))
    print("[merge] 契約OK  第11〜20回 200語")


def q(s):
    # ★ダブルクォートだけ弾いても足りない。改行が入ると契約を通ったまま content.py が
    #   SyntaxError になり、バックスラッシュは**例外も出さずに**改行や制御文字へ化ける（無言のデータ破損）。
    bad = [name for ch, name in (('"', "ダブルクォート"), ("\\", "バックスラッシュ"),
                                 ("\n", "改行"), ("\r", "復帰"), ("\t", "タブ")) if ch in s]
    if bad:
        die("原稿に %s が混入: %r" % ("・".join(bad), s))
    return '"%s"' % s


def render(plan, drafts):
    buf = []
    for no in map(str, range(11, 21)):
        buf.append("    # ============================== 第%s回 ==============================" % no)
        # title も q() を通す（ここだけ素通りで、タブなどが content.py に混入しうる）
        buf.append('    {"no": %s, "title": %s, "items": [' % (no, q(plan[no]["title"])))
        for it in drafts[no]:
            buf.append("        (%s, %s, %s," % (q(it["word"]), q(it["pos"]), q(it["gloss"])))
            buf.append("         (%s, %s, %s)," % tuple(q(x) for x in it["distractors"]))
            buf.append("         %s, %s," % (q(it["usage_en"]), q(it["usage_ja"])))
            buf.append("         %s)," % q(it["note"]))
        buf.append("    ]},")
    return "\n".join(buf)


def main():
    plan, drafts = load()
    check(plan, drafts)
    p = os.path.join(HERE, "content.py")
    src = io.open(p, encoding="utf-8").read()
    if '"no": 11,' in src:
        die("content.py に既に第11回がある（二重追記を防ぐため中止）")
    m = re.search(r"\n\]\s*$", src)
    if not m:
        die("content.py の末尾 ] が見つからない")
    new = src[:m.start()] + "\n" + render(plan, drafts) + "\n]\n"
    # ★書く前に Python として読めることを確かめる。q() をすり抜ける文字が今後出ても、
    #   壊れた content.py を残さない（docstring の「1文字も書かずに終了する」を実装で保証する）。
    try:
        compile(new, p, "exec")
    except SyntaxError as e:
        die("追記すると content.py が壊れる（%s 行%s）ので中止した" % (e.msg, e.lineno))
    io.open(p, "w", encoding="utf-8").write(new)
    print("[merge] content.py に第11〜20回を追記した")


if __name__ == "__main__":
    main()
