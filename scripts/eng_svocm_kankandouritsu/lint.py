# -*- coding: utf-8 -*-
"""分解 DSL の契約チェッカ（CLI ＋ ライブラリ）。

    python3 lint.py items.json        # 全件を検査して人が読める形で出す
    python3 lint.py items.json --json # 機械可読（executor / エディタ用）

★check.py はこのファイルの `validate_item()` を import して使う。
  「原稿を書くときに通す検査」と「ビルド前のゲート」を別々に書くと必ず片方だけ緩くなるので、
  契約は**この 1 ファイルにしか書かない**。

items.json の 1 件:
    {"id": "A1",                  # 表示用。任意
     "mode": "drill" | "kaishaku",# drill=第1部（①②③に切り出す）/ kaishaku=第3部（精密分解）
     "dsl":  "{S:...} {V:...} .",
     "en":   "...",               # DSL から復元される英文と 1 文字も違わないこと
     "pat":  "第5文型（SVOC）",
     "notes": ["...", "..."],     # 任意（あれば HTML 健全性を見る）
     "ja":   "..."}               # 任意
"""
import json
import re
import sys

from layout import (
    DRILL_LABELS, PATTERN_CORE, SYN_VOCAB, infer_pattern, normalize, parse, plain_text,
    top_segments,
)

# ------------------------------------------------------------------ 表記規約
# ★この教材は「記号を指させるか」で採点する。だから**同じ構文が2通りに書けてはいけない**。
#   規約を散文で書いても次の原稿で必ず揺れるので、機械で守らせる（凡例と 1 対 1 で対応）。
#
#   規約1 助動詞・完了の have・受動の be は V と同じマスに入れる。
#         副詞や S が割り込んだときだけ {助:} を独立させる。
#   規約2 ダッシュの数 ＝ 囲みの深さ（S V O C M O1 O2）。深さ3以上は 2 本で頭打ち。
#         接・同格・挿入・強調・真S・真O・助 にはダッシュを付けない。
#   規約3 括弧の種類とラベルの働きを一致させる。
#         ( ) 副詞 → M / 挿入      [ ] 名詞 → S O C O1 O2 真S 真O 同格 強調      < > 形容詞 → M
#   規約4 < > の中で分詞が後置修飾するときは、分詞に {V':} を付ける（素の語で置かない）。
#   規約5 < > の中の that は関係詞（{S':that} / {O':that}）。同格の that 節は [同格: {接:that} … ]。
#   規約6 名詞のマス（S O O1 O2）に of 句を抱え込まない。核だけをマスにし、of 句は外へ出す。
#         形容詞・動詞が要求する前置詞（be capable of / take advantage of）はマスに残してよい
#         ので、この検査は名詞のマスだけを見る。
NO_DASH = {"接", "助", "真S", "真O", "同格", "挿入", "強調"}
BRACKET_LABELS = {
    "(": {"M", "挿入", ""},
    "[": {"S", "O", "C", "O1", "O2", "真S", "真O", "同格", "強調"},
    "<": {"M", ""},
}
BRACKET_JA = {"(": "( ) 副詞のカタマリ", "[": "[ ] 名詞のカタマリ", "<": "&lt; &gt; 形容詞のカタマリ"}
MAX_DASH = 2
PARTICIPLE = re.compile(r"^[A-Za-z]+(?:ed|ing)$")
# 規約15: to の次がこれらなら前置詞の to（不定詞ではない）
DETERMINER = {"the", "a", "an", "this", "that", "these", "those", "his", "her", "their",
              "its", "our", "my", "your", "some", "any", "all", "most", "many", "much",
              "several", "each", "every", "one", "two", "three", "both", "other", "another",
              "such", "no", "him", "them", "us", "me", "you", "it", "which", "whom", "what"}
# 規約17: 英綴り -> 米綴り
BRITISH = {
    "colour": "color", "colours": "colors", "coloured": "colored",
    "metre": "meter", "metres": "meters", "centre": "center", "centres": "centers",
    "harbour": "harbor", "harbours": "harbors", "neighbour": "neighbor",
    "neighbours": "neighbors", "behaviour": "behavior", "favourite": "favorite",
    "labour": "labor", "labelled": "labeled", "travelled": "traveled",
    "cancelled": "canceled", "practise": "practice", "practised": "practiced",
    "organisation": "organization", "organisations": "organizations",
    "realise": "realize", "realised": "realized", "recognise": "recognize",
    "theatre": "theater", "theatres": "theaters", "programme": "programme",
    "defence": "defense", "offence": "offense", "grey": "gray", "analyse": "analyze",
}
# 規約11: V のマスの先頭に立てる助動詞・完了・受動の be
AUX_HEAD = {"be", "am", "is", "are", "was", "were", "been", "being", "has", "have", "had",
            "can", "could", "will", "would", "shall", "should", "may", "might", "must",
            "do", "does", "did"}
# ★not / never は V と同じマスに入れてよい（否定は動詞の一部として扱う）。
NEG_OK = {"not", "never", "n't"}
ADV_IN_V = {"also", "always", "still", "often", "already", "long", "just", "soon",
            "recently", "hardly", "seldom", "rarely", "ever", "then", "even", "only"}
# 規約13: 原形不定詞を C に取る動詞（この V があるのに C が 2 語以上の平マスなら分解漏れ）
BARE_INF_V = {"make", "makes", "made", "let", "lets", "have", "has", "had", "help", "helps",
              "helped", "see", "sees", "saw", "hear", "hears", "heard", "watch", "watches",
              "watched", "feel", "feels", "felt", "notice", "notices", "noticed"}
# ★C が形容詞句のときに「原形不定詞の分解漏れ」と誤検出しないための除外。
#   make O C は C に形容詞も原形も取るので、V だけでは決められない（実測で
#   {C:extremely difficult} {C:impossible to explain} {C:more important than ever} を落とした）。
ADJ_HEAD = {"more", "less", "most", "least", "very", "too", "so", "quite", "rather", "much",
            "far", "even", "as", "no", "a", "an", "the", "one", "two", "his", "her", "their",
            "its", "our", "my", "your", "part", "unable", "able", "aware", "free", "full",
            "open", "safe", "clear", "worth", "sure", "ready", "silent", "alive", "alone"}
ADJ_SUFFIX = ("ly", "ble", "ous", "ive", "al", "ful", "less", "ent", "ant", "ic", "ary",
              "ed", "ing", "y", "er", "est")

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

# 解説文で許可する HTML タグ。これ以外の生 '<' は Chrome が語ごと飲み込む。
TAG_OK = re.compile(r'</?(?:b|u|i|br|span(?:\s+class="[a-z0-9 _-]+")?)\s*/?>')
ENT_OK = re.compile(r"&(?:lt|gt|amp|nbsp|quot|#\d+);")
PAT_NAME = re.compile(r"第[1-5]文型")


# ★実体参照で書かれた強調タグ。&lt;b&gt; と書くと、紙には <b> という**文字**が出る。
#   markup_errors は &lt; を「正しいエスケープ」として通すので、これは別に見ないと素通りする。
ESCAPED_TAG = re.compile(r"&lt;/?(?:b|u|i|br|span)&gt;")


def markup_errors(s):
    """生タグ・未エスケープの & ・タグの開閉不一致・エスケープしすぎた強調タグを列挙する。"""
    out = []
    for m in ESCAPED_TAG.finditer(s):
        out.append(f"強調タグをエスケープしている（紙にタグが文字で出る）: {m.group(0)}"
                   "　強調は生の <b>…</b> で書く")
    for m in re.finditer(r"<", s):
        if not TAG_OK.match(s, m.start()):
            out.append(f"未エスケープの '<'（&lt; と書く）: …{s[m.start():m.start() + 30]}…")
    for m in re.finditer(r"&", s):
        if not ENT_OK.match(s, m.start()):
            out.append(f"未エスケープの '&': …{s[m.start():m.start() + 22]}…")
    opens = sorted(re.findall(r"<(b|u|i|span)\b", s))
    closes = sorted(re.findall(r"</(b|u|i|span)>", s))
    if opens != closes:
        out.append(f"タグの開閉が不一致: open={opens} close={closes}")
    return out


def _want_dash(d):
    return min(d, MAX_DASH)


def notation_errors(root):
    """表記規約（1〜6）を機械で守らせる。"""
    out = []

    def check_label(lbl, d, what):
        base = lbl.replace("'", "")
        if not lbl or base in NO_DASH:
            if "'" in lbl:
                out.append(f"規約2: {lbl} にダッシュは付けない（{what}）")
            return
        want = _want_dash(d)
        got = lbl.count("'")
        if got != want:
            out.append(f"規約2: ラベル {lbl} のダッシュが {got} 本（深さ {d} なので {want} 本）: {what}")

    def walk(nd, d):
        kids = nd.kids
        for i, k in enumerate(kids):
            if k.kind == "plain":
                continue
            what = k.text if k.kind == "chunk" else plain_text(k)[:34]
            check_label(k.label, d, what)
            if k.kind == "chunk":
                # 規約1: {助:…} の直後が V なら 1 マスにまとめる
                if k.label.replace("'", "") == "助":
                    nxt = kids[i + 1] if i + 1 < len(kids) else None
                    if nxt and nxt.kind == "chunk" and nxt.label.replace("'", "") == "V":
                        out.append(f"規約1: 助動詞と動詞が隣り合っている。1 マスにまとめる: "
                                   f"{{{k.label}:{k.text}}} {{{nxt.label}:{nxt.text}}}")
                # 規約6: 名詞のマスに of 句を抱え込まない
                if k.label.replace("'", "") in ("S", "O", "O1", "O2") and " of " in f" {k.text} ":
                    out.append(f"規約6: 名詞のマスが of 句を抱えている: {{{k.label}:{k.text}}}"
                               "（核だけをマスにし、of 句は外に出す）")
                toks = k.text.split()
                low = [t.lower().strip(",.;:") for t in toks]
                if k.label.replace("'", "") == "V":
                    # 規約11: V のマスに副詞を巻き込まない（not / never は可）
                    if len(low) >= 3 and low[0] in AUX_HEAD:
                        for t in low[1:-1]:
                            if t in NEG_OK:
                                continue
                            if t.endswith("ly") or t in ADV_IN_V:
                                out.append(f"規約11: V のマスに副詞 {t!r} が入っている: "
                                           f"{{{k.label}:{k.text}}}"
                                           "（助動詞を {助:} で分け、副詞は M にする）")
                                break
                    # 規約12: 準助動詞を V のマスに入れない。
                    # ★先頭の to は不定詞そのもの（{V':to rethink}）なので正しい形。
                    #   2 語目以降に to が来る形（tend to report / have to be）だけを落とす。
                    if "to" in low[1:]:
                        out.append(f"規約12: V のマスに準助動詞の to が入っている: "
                                   f"{{{k.label}:{k.text}}}"
                                   "（tend / have を V にし、to 不定詞は別のマスにする）")
                # 規約13: C が節相当なら [ C: ] で囲む
                if k.label.replace("'", "") == "C" and len(low) >= 2:
                    # ★have / has / had は使役動詞にも完了の助動詞にもなる。
                    #   1 語だけのときに限って使役と見る（{V:has become} を使役と数えると
                    #   {C:its small garden} を「分解漏れ」と誤って落とす。実測で踏んだ）。
                    sib_v = []
                    for c in nd.kids:
                        if c.kind != "chunk" or c.label.replace("'", "") != "V":
                            continue
                        w = c.text.lower().split()
                        if len(w) > 1 and w[0] in ("have", "has", "had"):
                            continue
                        sib_v += w
                    if low[0] == "to":
                        out.append(f"規約13: to 不定詞の C を平マスにしている: {{{k.label}:{k.text}}}"
                                   "（[ C: {V':to …} … ] と囲んで分解する）")
                    elif (any(w in BARE_INF_V for w in sib_v)
                          and low[0] not in ADJ_HEAD
                          and not low[0].endswith(ADJ_SUFFIX)):
                        out.append(f"規約13: 原形不定詞の C を平マスにしている疑い: "
                                   f"{{{k.label}:{k.text}}}"
                                   "（[ C: {V':…} … ] と囲んで分解する）")
                continue
            # 規約3: 括弧の種類とラベルの働き
            allowed = BRACKET_LABELS[k.text]
            if k.label.replace("'", "") not in allowed:
                out.append(f"規約3: {BRACKET_JA[k.text]} に {k.label!r} は付けられない"
                           f"（使えるのは {sorted(x for x in allowed if x)}）: {what}")
            if k.text in "<(" and k.kids:
                head = k.kids[0]
                if head.kind == "plain":
                    w = head.text.split()[0]
                    # 規約4 / 規約14: 分詞は素の語で置かない（後置修飾も分詞構文も）
                    words = head.text.split()
                    if PARTICIPLE.match(w):
                        num = "規約4" if k.text == "<" else "規約14"
                        out.append(f"{num}: 分詞 {w!r} が素の語のまま。"
                                   f"{{V{chr(39) * _want_dash(d + 1)}:{w}}} と示す: {what}")
                    elif (w.lower() == "to" and len(words) > 1
                          and words[1].lower() not in DETERMINER
                          and not words[1][:1].isupper()):
                        out.append(f"規約15: to 不定詞が素の語のまま。"
                                   f"{{V{chr(39) * _want_dash(d + 1)}:to {words[1]}}} と示して"
                                   f"中まで分解する: {what}")
            if k.text == "<" and k.kids:
                # 規約5: < > の中の that は関係詞
                for c in k.kids:
                    if c.kind == "chunk" and c.label == "接" and c.text.lower() == "that":
                        out.append("規約5: 形容詞のカタマリの中の that を {接:that} と書いている。"
                                   "関係詞なら {S':that} / {O':that}、同格なら [同格: …] にする: "
                                   f"{what}")
            # 規約18: カタマリの中の「名詞 + of 句」は割って外に出す（うしろに修飾が続かないとき）
            for ci, c in enumerate(k.kids):
                if c.kind != "plain" or " of " not in f" {c.text} ":
                    continue
                if c.text.lower().startswith("of "):
                    continue      # このカタマリ自体が of 句＝すでに割れている
                if [x for x in k.kids[ci + 1:] if x.kind == "group"]:
                    continue      # うしろに修飾が続く。割ると規約16 と衝突する
                out.append("規約18: カタマリの中の of 句が割られていない: "
                           f"{k.text}{k.label}: {c.text}"
                           "（of 以下を &lt; M: &gt; で外に出す）")
            # 規約16: 同じ深さに < > を 2 つ並べない（かかり先が図から読めなくなる）
            nxt = kids[i + 1] if i + 1 < len(kids) else None
            if (k.text == "<" and nxt is not None and nxt.kind == "group"
                    and nxt.text == "<"):
                out.append("規約16: 同じ深さに &lt; &gt; が 2 つ並んでいる。"
                           "2 つ目が 1 つ目の中の名詞にかかるなら入れ子にする: "
                           f"{what} / {plain_text(nxt)[:28]}")
            walk(k, d + 1)

    walk(root, 0)
    return out


def depth_errors(root):
    """後方互換のための別名（表記規約の検査本体は notation_errors）。"""
    return notation_errors(root)


def validate_item(it):
    """1 件を検査して (errors, info) を返す。errors が空なら合格。"""
    errs, info = [], {}
    mode = it.get("mode", "kaishaku")
    dsl = it.get("dsl", "")
    en = normalize(it.get("en", ""))
    pat = it.get("pat", "")

    try:
        root = parse(dsl)
    except ValueError as e:
        return [f"DSL パース失敗: {e}"], info

    recon = plain_text(root)
    info["recon"] = recon
    if recon != en:
        errs.append("復元英文が en と不一致\n"
                    f"     en   : {en}\n"
                    f"     復元 : {recon}")
    if recon[-1:] not in ".?!":
        errs.append(f"文末記号が無い: …{recon[-14:]!r}")
    for bad in "{}[]<>()@":
        if bad in en:
            errs.append(f"en に記号 {bad!r} が混ざっている（DSL をそのまま貼っていないか）")
            break
    errs += depth_errors(root)
    for w in re.findall(r"[A-Za-z]+", en):
        if w.lower() in BRITISH and BRITISH[w.lower()] != w.lower():
            errs.append(f"規約17: 英綴り {w!r} が混ざっている（{BRITISH[w.lower()]} に統一する）")

    segs = top_segments(root)
    info["segs"] = segs
    top_lbl = [lb for lb, _t, _u in segs]
    info["top_labels"] = top_lbl

    if not any(lb in ("V", "助") for lb in top_lbl):
        errs.append("主節の V（述語動詞）が無い")
    if not any(lb in ("S", "真S") for lb in top_lbl) and "命令文" not in pat:
        errs.append("主節の S が無い（命令文なら pat に「命令文」と書く）")
    for lb, txt, unlabeled in segs:
        if unlabeled:
            errs.append(f"トップレベルにラベルの無い語が残っている: {txt!r}"
                        "（接続詞なら {接:...}、修飾語なら (M: ...) で囲む）")
        elif mode == "drill" and not lb:
            # ★ラベルの無いカタマリ ( … ) は「地の文」ではないので上の検査に掛からない。
            #   第1部では解答欄が1つ空白のまま刷られる（答えの無い番号ができる）ので必ず止める。
            errs.append(f"ラベルの無いカタマリがトップレベルにある: {txt!r}"
                        "（第1部は (M: ...) のように働きを必ず付ける）")

    if mode == "drill":
        bad = [lb for lb in top_lbl if lb and lb not in DRILL_LABELS]
        if bad:
            errs.append(f"第1部の主節ラベルは {DRILL_LABELS} だけ。使えないラベル: {sorted(set(bad))}"
                        "（等位接続で2文をつなぐ形は第1部に出さない）")
        if not (3 <= len(segs) <= 7):
            errs.append(f"切り出しが {len(segs)} 個（3〜7 個にする）")
        if len(segs) != len(set(t for _l, t, _u in segs)):
            errs.append("同じ文字列の区切りが2つある（①②の見分けがつかない）")

    got = infer_pattern(top_lbl)
    info["inferred_pat"] = got
    named = PAT_NAME.findall(pat)
    if not named:
        if "命令文" not in pat:
            errs.append(f"pat に文型の記載が無い: {pat!r}")
    elif got is None:
        errs.append(f"主節ラベル {top_lbl} からは文型を決められない（pat は {named[0]}）")
    elif len(set(named)) == 1 and named[0] != got:
        errs.append(f"pat は {named[0]} だが、主節ラベル {top_lbl} は {got}"
                    f"（{PATTERN_CORE[got]}）")

    syn = it.get("syn")
    if syn is not None and syn not in SYN_VOCAB:
        near = [k for k in SYN_VOCAB if syn and (syn[:5] in k or k[:5] in syn)]
        errs.append(f"syn（構文カテゴリ）{syn!r} は語彙に無い。"
                    f"近いもの: {near[:6] or sorted(SYN_VOCAB)[:8]} "
                    "（一覧は layout.py の SYN_VOCAB）")
    for i, n in enumerate(it.get("notes") or []):
        for m in markup_errors(n):
            errs.append(f"notes[{i}]: {m}")
    if it.get("_require_notes") and len(it.get("notes") or []) < 2:
        errs.append("notes が 2 項目未満")
    if it.get("_require_ja") and not it.get("ja"):
        errs.append("ja（和訳）が空")
    return errs, info


def drill_line(segs):
    """判別問題として印字される 1 行（①②③…）を文字で再現する。"""
    return " ".join(f"{CIRCLED[i]}{t}" for i, (_l, t, _u) in enumerate(segs))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    items = json.load(open(argv[1], encoding="utf-8"))
    if isinstance(items, dict):
        items = [items]
    as_json = "--json" in argv
    report, ng = [], 0
    for i, it in enumerate(items, 1):
        errs, info = validate_item(it)
        ng += bool(errs)
        report.append({"id": it.get("id", f"#{i}"), "ok": not errs, "errors": errs,
                       "top_labels": info.get("top_labels"),
                       "inferred_pat": info.get("inferred_pat"),
                       "drill_line": drill_line(info["segs"]) if info.get("segs") else ""})
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for r in report:
            head = "OK  " if r["ok"] else "NG  "
            print(f"{head}{r['id']}  {r['inferred_pat'] or '-'}  {r['top_labels']}")
            if r["drill_line"]:
                print(f"      {r['drill_line']}")
            for e in r["errors"]:
                print(f"      - {e}")
        print(f"\n合計 {len(report)} 件 / NG {ng} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
