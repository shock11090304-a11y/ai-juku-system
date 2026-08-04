#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""難関国公立大 英文法 実戦問題集 — 機械ゲート。

  python3 scripts/eng_kokkoritsu_nankan/check.py

★存在理由: 盲ソルバー（AI が実際に解いて鍵と照合する層）は「鍵が正しいか」しか測らない。
  「トークンと解答がそもそも一致していない」「答えが問題編に印字されている」「配点が合わない」
  「誤りの位置が偏っている」は、AI に探させる前に Python で確定的に潰せる。
  ここが FAIL のうちは build.py を走らせない（build.py が先頭でこのゲートを呼ぶ）。
"""
import os
import re
import sys
import difflib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
# ★機械（ゲート・組版・盲検証）は共有し、中身だけ差し替える。
#   WORKBOOK_DIR=<別冊のディレクトリ> を付けて実行すると、そちらの content.py を読む。
BOOK_DIR = os.path.abspath(os.environ.get("WORKBOOK_DIR") or HERE)
sys.path.insert(0, BOOK_DIR)
sys.path.insert(0, os.path.dirname(HERE))

from _workbook_gates import Gate                      # noqa: E402
from content import (BOOK, all_items, question_text, frame_text,  # noqa: E402
                     Q_FIELDS, ELEMENT_KINDS)

# ★英語専用の判定（与えられた語の語幹照合・英単語数の下限・機能語の除外）は
#   日本語教材では意味をなさない。content.py の lang で切り替える。
JA = BOOK.get("lang") == "ja"

# 問題編の見出し・指示文に書いてはいけない語（書いた瞬間に何の文法かが割れる＝解答漏洩）
FORBIDDEN_IN_QUESTION = [
    "仮定法", "関係代名詞", "関係副詞", "分詞構文", "倒置", "強調構文", "比較級", "最上級",
    "動名詞", "不定詞", "過去完了", "現在完了", "使役", "受動態", "同格", "連鎖関係詞",
    "無生物主語", "部分否定", "譲歩",
]
REQUIRED = {
    "mc":      ("stem", "choices", "ans", "exp", "point"),
    "error":   ("stem", "parts", "ans", "fix", "exp", "point"),
    "order":   ("ja", "frame", "tokens", "ans", "exp", "point"),
    "fill":    ("stem", "ans", "exp", "point"),
    "ident":   ("stem", "ans", "exp", "point"),   # 傍線部を文法的に説明する（空所なし）
    "rewrite": ("src", "inst", "ans", "exp", "point"),
    "jtrans":  ("context", "src", "model", "alts", "elements", "exp", "point"),
    "trans":   ("ja", "model", "alts", "elements", "exp"),
}
WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
CJK = re.compile(r"[぀-ヿ一-龥]")
# 内容語を1つも含まない3語（would not have など）は、たまたま重なるだけで漏洩ではない
STOP = set("""a an the of to in on at for with by from as that this these those is are was
were be been being has have had do does did will would can could may might should not no
and or but it he she they we you i his her their our my your its than so if when what which
who whom whose there here one all any some more most much many very too then""".split())
# 語幹の前方一致では拾えない不規則変化（空所補充の「与えられた語」照合用）
IRREGULAR = {
    "have": ("had", "has"), "do": ("did", "does"), "be": ("was", "were", "been", "is", "are"),
    "see": ("saw", "seen"), "go": ("went", "gone"), "think": ("thought",),
    "know": ("knew", "known"), "take": ("took", "taken"), "say": ("said",),
    "tell": ("told",), "make": ("made",), "hear": ("heard",), "feel": ("felt",),
    "break": ("broke", "broken"), "write": ("wrote", "written"),
    "leave": ("left",), "buy": ("bought",), "teach": ("taught",),
}


def words(s):
    """英文をトークン列へ。句読点は落とし、小文字化する。"""
    return [w.lower().strip(",.;:!?\"'") for w in str(s).split() if w.strip(",.;:!?\"'")]


def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def main():
    g = Gate()
    qtext = question_text()
    qnorm = norm(qtext)
    items = list(all_items())
    print(f"■ {BOOK['title']}／{len(BOOK['parts'])}部・{len(items)}問\n")

    # ---------------------------------------------------------- G1 構造
    bad = []
    for _p, s, it, where in items:
        for f in REQUIRED[s["kind"]]:
            v = it.get(f)
            if v in (None, "", [], {}):
                bad.append(f'{where} に {f} がない')
    g._fail(f"[構造] 必須フィールド欠落 {len(bad)}件: " + "／".join(bad[:6])) if bad else \
        g._ok(f"[構造] {len(items)}問 必須フィールド完備 OK")

    # ---------------------------------------------------------- G2 配点
    bad = []
    for p in BOOK["parts"]:
        tot = sum(len(s["items"]) * s["pt"] for s in p["sections"])
        n = sum(len(s["items"]) for s in p["sections"])
        if tot != p["total"]:
            bad.append(f'第{p["no"]}部 実配点{tot} ≠ 表示{p["total"]}')
        else:
            g._ok(f'[配点] 第{p["no"]}部 {n}問 = {tot}点 OK')
    if bad:
        g._fail("[配点] 小問配点の合計が満点と一致しない（生徒が自己採点できない）: "
                + "／".join(bad))

    # ------------------------------------------------------------ G2b 四択
    mcs = [{"where": w, "choices": it["choices"], "ans": it["ans"], "exp": it.get("exp", "")}
           for _p, s, it, w in items if s["kind"] == "mc"]
    if mcs:
        bad = [m["where"] for m in mcs
               if not 0 <= m["ans"] < len(m["choices"]) or len(m["choices"]) != 4]
        if bad:
            g._fail("[四択] 選択肢が4つでない／正解indexが範囲外: " + "／".join(bad))
        else:
            g._ok(f"[四択] {len(mcs)}問 選択肢4つ・正解index正常 OK")
        # 共通ゲート（社会・理科の問題集と同じ実装を流用）
        g.choice_position([{"where": m["where"], "choices": m["choices"], "ans": m["ans"]}
                           for m in mcs], ratio=0.35)
        # ★共通ゲートの longest_tell は同点も「最長」と数える。四択の選択肢は
        #   機能語1語どうしで長さが並ぶことが多く、同点は tell にならないので
        #   「単独で最長」に絞って判定する（誤り指摘の下線部と同じ考え方）。
        mc_long = [m["where"] for m in mcs
                   if len(m["choices"][m["ans"]]) == max(len(c) for c in m["choices"])
                   and [len(c) for c in m["choices"]].count(
                       max(len(c) for c in m["choices"])) == 1]
        if len(mc_long) > len(mcs) * 0.35:
            g._fail(f"[テル] 正解肢が単独で最長の四択が {len(mc_long)}/{len(mcs)}問"
                    f"（偶然なら25%）。長さだけで当てられる: " + "／".join(mc_long[:8]))
        else:
            g._ok(f"[テル] 正解肢が単独最長の四択は {len(mc_long)}/{len(mcs)}問"
                  f"（期待値{len(mcs)*0.25:.0f}）OK")
        g.exp_choice_refs(mcs)
        dup = [m["where"] for m in mcs
               if len({norm(x) for x in m["choices"]}) != len(m["choices"])]
        if dup:
            g._fail("[四択] 同じ選択肢が重複している: " + "／".join(dup))
        else:
            g._ok(f"[四択] {len(mcs)}問 選択肢の重複なし OK")

    # ------------------------------------------------- G3/G4 誤り指摘
    errs = [(w, it) for _p, s, it, w in items if s["kind"] == "error"]
    bad, pos = [], Counter()
    for where, it in errs:
        marks = re.findall(r"\{([abcd])\}", it["stem"])
        if sorted(marks) != ["a", "b", "c", "d"]:
            bad.append(f"{where} 下線部マーカーが {marks}")
        if len(it["parts"]) != 4:
            bad.append(f'{where} parts が {len(it["parts"])}個')
        if not 0 <= it["ans"] < 4:
            bad.append(f'{where} ans={it["ans"]} が範囲外')
            continue
        pos[it["ans"]] += 1
        # fix の矢印の左側（直す前の形）は、誤っている下線部の中に実在していなければならない。
        # ★下線部が長いとき fix は中の1語だけを書くのが自然なので、前方一致ではなく包含で見る。
        wrong = norm(it["parts"][it["ans"]])
        before = norm(re.split(r"[→>]", it["fix"])[0])
        if not before or before not in wrong:
            bad.append(f'{where} fix「{it["fix"][:26]}」が誤答部「{wrong[:22]}」の中に無い')
    if bad:
        g._fail(f"[誤り指摘] {len(bad)}件: " + "／".join(bad[:6]))
    else:
        g._ok(f"[誤り指摘] {len(errs)}問 マーカー/parts/fix対応 OK")
    dist = "／".join(f"({c}){pos.get(i,0)}問" for i, c in enumerate("abcd"))
    if errs and max(pos.values()) > len(errs) * 0.4:
        g._fail(f"[誤り指摘] 誤りの位置が偏っている（読まずに当てられる）: {dist}")
    else:
        g._ok(f"[誤り指摘] 誤り位置の分布 {dist} OK")

    # ★下線部の「長さ」も位置と同じ tell になる。正解だけ主語ごと囲うと、英文を読まずに
    #   「いちばん長い下線部」を選ぶだけで当たってしまう（初版は26問中12問＝46%だった）。
    long_hit, gap = [], []
    for where, it in errs:
        L = [len(x.split()) for x in it["parts"]]
        if L[it["ans"]] == max(L) and L.count(max(L)) == 1:
            long_hit.append(where)
            if L[it["ans"]] - sorted(L)[-2] >= 3:
                gap.append(f"{where}{L}")
    if errs and len(long_hit) > len(errs) * 0.35:
        g._fail(f"[誤り指摘] 正解の下線部が単独で最長の問が {len(long_hit)}/{len(errs)}問"
                f"（偶然なら25%）。長さだけで当てられる: " + "／".join(long_hit[:8]))
    elif gap:
        g._fail(f"[誤り指摘] 正解の下線部が2番目より3語以上長い問がある（露骨なtell）: "
                + "／".join(gap))
    else:
        g._ok(f"[誤り指摘] 正解が単独最長なのは {len(long_hit)}/{len(errs)}問"
              f"（期待値{len(errs)*0.25:.0f}問）OK")

    # ★訂正後の全文を機械で組み立てて、fix の適用先が本文に実在するかを確かめる。
    #   これを見ていなかったため「is because → is that」を当てると
    #   "is that that it can accommodate" になる壊れた設問が出荷寸前まで残った。
    bad = []
    for where, it in errs:
        full = it["stem"]
        for j, c in enumerate("abcd"):
            full = full.replace("{%s}" % c, it["parts"][j])
        before = re.split(r"[→>]", it["fix"])[0].strip()
        after = re.sub(r"（.*?）", "", re.split(r"[→>]", it["fix"])[1]).strip()
        if before not in full:
            bad.append(f"{where} fix の「{before}」が本文に無い")
            continue
        fixed = full.replace(before, after, 1)
        for dup in (" that that ", " to to ", " the the ", " is is ", " of of "):
            if dup in " " + fixed + " ":
                bad.append(f'{where} 訂正後に「{dup.strip()}」の重複が残る: '
                           f"…{fixed[max(0,fixed.find(dup)-30):fixed.find(dup)+30]}…")
    if bad:
        g._fail(f"[誤り指摘] 訂正後の英文が壊れている {len(bad)}件: " + "／".join(bad))
    else:
        g._ok(f"[誤り指摘] {len(errs)}問 訂正後の全文に語の重複なし OK")

    # ---------------------------------------------------- G5/G6 語句整序
    orders = [(w, it) for _p, s, it, w in items if s["kind"] == "order"]
    bad_set, bad_frame, leak_order = [], [], []
    for where, it in orders:
        tk, an = sorted(w.lower() for w in it["tokens"]), sorted(words(it["ans"]))
        if tk != an:
            only_t = list((Counter(tk) - Counter(an)).elements())
            only_a = list((Counter(an) - Counter(tk)).elements())
            bad_set.append(f'{where} トークンのみ{only_t}／解答のみ{only_a}')
        if it["frame"].count("[") != 1 or it["frame"].count("]") != 1:
            bad_frame.append(f"{where} frame の [ ] が1組でない")
        if [w.lower() for w in it["tokens"]] == words(it["ans"]):
            leak_order.append(where)
    if bad_set:
        g._fail(f"[整序] トークンと解答の語が一致しない（並べ替えても解答にならない）"
                f" {len(bad_set)}件: " + "／".join(bad_set))
    else:
        g._ok(f"[整序] {len(orders)}問 トークン集合＝解答の語 完全一致 OK")
    if bad_frame:
        g._fail("[整序] " + "／".join(bad_frame))
    if leak_order:
        g._fail("[整序] トークンが解答の語順のまま並んでいる（並べ替え不要で解ける）: "
                + "／".join(leak_order))
    else:
        g._ok(f"[整序] {len(orders)}問 トークンは解答と別の順序 OK")

    # ------------------------------------------------------- G7 空所補充
    fills = [(w, it) for _p, s, it, w in items if s["kind"] == "fill"]
    bad = []
    for where, it in fills:
        if "(" not in it["stem"]:
            bad.append(f"{where} stem に空所がない")
        h = it.get("hint")
        if h and not norm(it["ans"]).startswith(h.lower()):
            bad.append(f'{where} 頭文字ヒント({h})と解答「{it["ans"]}」が不一致')
        givens = [w for w in re.split(r"[,\s]+", it.get("given", "")) if w]
        # ★与えられた語の数と解答の語数が合わないと、示されていない語（had / did など）を
        #   生徒に勝手に補わせることになる。指示文の範囲を超えた出題になるので FAIL。
        if givens and len(givens) != len(str(it["ans"]).split()):
            bad.append(f'{where} 与えられた語{len(givens)}語に対し解答「{it["ans"]}」は'
                       f'{len(str(it["ans"]).split())}語（示されていない語を補わせている）')
        for gw in ([] if JA else givens):
            gw = gw.lower()
            # ★語幹の前方一致だけだと不規則変化（have→had, do→did）を誤検出する。
            forms = {gw[:3]} | set(IRREGULAR.get(gw, ()))
            if not any(fm in norm(it["ans"]) for fm in forms):
                bad.append(f'{where} 与えられた語「{gw}」が解答「{it["ans"]}」に反映されていない')
    if bad:
        g._fail(f"[空所補充] {len(bad)}件: " + "／".join(bad[:6]))
    else:
        g._ok(f"[空所補充] {len(fills)}問 空所/ヒント/与えられた語 整合 OK")

    # ------------------------------------------------------- G8 書き換え
    rws = [(w, it) for _p, s, it, w in items if s["kind"] == "rewrite"]
    bad = []
    for where, it in rws:
        m = re.search(r"([A-Za-z][A-Za-z' ]*?)\s*(?:を書き出し|で始め|を主語)", it["inst"])
        if m and not norm(it["ans"]).startswith(norm(m.group(1))):
            bad.append(f'{where} 指示「{m.group(1).strip()}」で始まっていない：{it["ans"][:34]}')
        if norm(it["ans"]) == norm(it["src"]):
            bad.append(f"{where} 書き換え前後が同一文")
    if bad:
        g._fail(f"[書き換え] {len(bad)}件: " + "／".join(bad))
    else:
        g._ok(f"[書き換え] {len(rws)}問 指示どおりの書き出し OK")

    # ------------------------------------------------------- G9 和文英訳
    trs = [(w, s, it) for _p, s, it, w in items if s["kind"] in ELEMENT_KINDS]
    bad = []
    for where, s, it in trs:
        tot = sum(e[1] for e in it["elements"])
        if tot != s["pt"]:
            bad.append(f'{where} 採点要素の合計{tot}点 ≠ 配点{s["pt"]}点')
        # 和文英訳の模範解答は英語、英文和訳の模範解答は日本語。取り違えを機械で弾く。
        cjk = len(CJK.findall(it["model"]))
        if s["kind"] == "trans" and not JA and (len(WORD.findall(it["model"])) < 6 or cjk):
            bad.append(f"{where} model が英文になっていない")
        if s["kind"] == "jtrans":
            if cjk < 20:
                bad.append(f"{where} model が訳文になっていない（漢字かな{cjk}字）")
            src_len = len(CJK.findall(it["src"])) if JA else len(WORD.findall(it["src"]))
            if src_len < 12:
                bad.append(f"{where} 訳す部分が短すぎる（{src_len}）")
        if not it.get("alts"):
            bad.append(f"{where} 別解(alts)がない")
    if bad:
        g._fail(f"[記述採点] {len(bad)}件: " + "／".join(bad))
    else:
        g._ok(f"[記述採点] 和訳・英訳{len(trs)}問 採点要素の合計＝配点／別解あり OK")

    # ------------------------------------------- G10/G11 解答の自己漏洩
    leaks, warns = [], []
    for _p, s, it, where in items:
        ans = it.get("model") if s["kind"] in ELEMENT_KINDS else it.get("ans")
        if s["kind"] == "error" or not isinstance(ans, str):
            continue
        # ★自分自身の設問文は走査対象から外す。書き換え問題の解答が元の文と語を共有するのは
        #   当たり前で、そこを数えると本物の漏洩（他の問題への露出）が warning に埋もれる。
        hay = norm(question_text(exclude=it))
        ws = words(ans)
        if len(ws) >= 3 and norm(ans) in hay:
            leaks.append(f'{where}「{ans[:40]}」')
        elif len(ws) >= 6:                       # 5語連続の一致は要目視
            for i in range(len(ws) - 4):
                if " ".join(ws[i:i + 5]) in hay:
                    warns.append(f'{where}「{" ".join(ws[i:i+5])}」')
                    break
    if leaks:
        g._fail(f"[解答漏洩] 解答そのものが問題編に印字されている {len(leaks)}件: "
                + "／".join(leaks))
    else:
        g._ok(f"[解答漏洩] {len(items)}問 解答文字列は問題編に出現しない OK")
    for w in warns:
        g._warn(f"[解答漏洩] 5語連続一致（目視で確認）: {w}")

    jbad = [w for _p, s, it, w in items if s["kind"] == "jtrans"
            and norm(it["model"])[:24] in qnorm]
    if jbad:
        g._fail(f"[解答漏洩] 英文和訳の模範訳が問題編に印字されている: " + "／".join(jbad))
    else:
        g._ok(f"[解答漏洩] 英文和訳{sum(1 for _p,s,_i,_w in items if s['kind']=='jtrans')}問 "
              "模範訳は問題編に出現しない OK")

    hit = [f for f in ("exp", "point", "fix", "model", "elements", "alts", "accept")
           if f in Q_FIELDS]
    if hit:
        g._fail(f"[漏洩構造] 解説系フィールドが問題編に印字される設定になっている: {hit}")
    else:
        g._ok("[漏洩構造] 問題編に出るのは設問フィールドのみ OK")

    # ★走査するのは表紙・前書き・部扉・大問見出し・大問の指示文だけ。
    #   小問の指示（「分詞構文で始めて」等）は本番の設問文そのものなので対象外。
    if JA:
        # ★FORBIDDEN_IN_QUESTION は英文法の単元名リストなので日本語教材には使えない。
        #   単元別の冊子では「使役」「同格」は部扉に出るのが正しい（その部の主題そのもの）。
        #   代わりに、より的確な漏洩を見る＝大問の見出し・指示文が、その大問の答えを
        #   そのまま印字していないか。指示文の「(例: 〜)」に本物の答えを書く事故が実際に出た。
        bad = []
        for p in BOOK["parts"]:
            for s in p["sections"]:
                head = f'{s["title"]}／{s["inst"]}'
                for i, it in enumerate(s["items"], 1):
                    a = norm(it.get("ans", ""))
                    if len(a) >= 4 and a in norm(head):
                        bad.append(f'第{p["no"]}部 大問{s["no"]}-{i} の答え「{it["ans"]}」')
        if bad:
            g._fail(f"[漏洩構造] 大問の見出し・指示文が、その大問の答えを印字している "
                    f"{len(bad)}件: " + "／".join(bad[:6]))
        else:
            g._ok("[漏洩構造] 大問の見出し・指示文に答えの記載なし OK")
    else:
        bad = [w for w in FORBIDDEN_IN_QUESTION if w in frame_text()]
        if bad:
            g._fail(f"[漏洩構造] 部扉・大問見出しに文法項目名が出ている（何の文法かが割れる）: {bad}")
        else:
            g._ok("[漏洩構造] 部扉・大問見出しに文法項目名の記載なし OK")

    # --------------------------------------------------------- G12 重複
    # ★鍵は「設問文」だけでは足りない。誤り指摘のように stem が {a}〜{d} の並びだけの
    #   出題形式では、別の設問どうしが同じ鍵になって偽の重複が出る。逆に「次の中から
    #   正しいものを選べ」のような指示文だけが stem になる形式では、本物の別問題が
    #   同一とみなされて投入時に落ちる事故が実際に起きた。鍵は必ず
    #   （設問文 ＋ 生徒が実際に目にする選択肢・下線部・語群）で作ること。
    seen, dup = {}, []
    for _p, s, it, where in items:
        opts = it.get("choices") or it.get("parts") or it.get("tokens") or []
        key = norm(it.get("stem") or it.get("ja") or it.get("src")) + \
            "|" + norm(" ".join(str(x) for x in opts))
        if key in seen:
            dup.append(f"{where} ＝ {seen[key]}")
        seen[key] = where
    if dup:
        g._fail(f"[重複] 同じ設問が2度出ている: " + "／".join(dup))
    else:
        g._ok(f"[重複] {len(seen)}問 設問文の重複なし OK")

    # ----------------------------------------------------- G13 解説の実質
    thin = [w for _p, s, it, w in items if len(str(it.get("exp", ""))) < 40]
    if thin:
        g._fail(f"[解説] 40字未満の解説 {len(thin)}件: " + "／".join(thin[:6]))
    else:
        g._ok(f"[解説] {len(items)}問 すべて40字以上 OK")



    # ------------------------------- G17 「答えの形」が他の設問の問題文に活字で出ている
    # ★G10（解答文字列の完全一致）と G15（学習項目の類似）の隙間に落ちる型を捕まえる。
    #   例: 大問3の答えが much で、別の大問の問題文に not so much a scholar as と印字されている。
    #   答えを埋めた完成形から3語のかたまりを取り、他の設問の印字テキストに出ていないか走査する。
    def _grams(text, n=3):
        if JA:
            # 日本語は語の区切りがないので文字 n-gram（6字）で見る。
            t = re.sub(r"[\s　（）\(\)＿]", "", str(text))
            return {t[i:i + 6] for i in range(len(t) - 5)}
        w = words(text)
        return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

    printed = []          # (where, その設問が問題編に印字するテキスト)
    filled = []           # (where, 答えを埋めた完成形)
    for _p, s_, it, where in items:
        printed.append((where, " ".join(
            " ".join(str(x) for x in v) if isinstance(v, list) else str(v)
            for f in Q_FIELDS if (v := it.get(f)))))
        if s_["kind"] == "mc":
            filled.append((where, re.sub(r"[（(]\s*[）)]", f' {it["choices"][it["ans"]]} ',
                                         it["stem"]) if JA else
                           re.sub(r"\(\s*\)", f' {it["choices"][it["ans"]]} ', it["stem"])))
        elif s_["kind"] == "fill":
            filled.append((where, re.sub(r"[（(]\s*[A-Za-z]?\s*[）)]", f' {it["ans"]} ',
                                         it["stem"])))
        elif s_["kind"] == "order":
            filled.append((where, re.sub(r"\[\s*\]", f' {it["ans"]} ', it["frame"])))
        elif s_["kind"] == "error":
            full = it["stem"]
            for j, c in enumerate("abcd"):
                full = full.replace("{%s}" % c, it["parts"][j])
            after = re.sub(r"（.*?）", "", re.split(r"[→>]", it["fix"])[1]).strip()
            filled.append((where, full.replace(
                re.split(r"[→>]", it["fix"])[0].strip(), after, 1)))

    hits = []
    for where, full in filled:
        # 答えを含む3語のかたまりだけを見る（設問文の共通句で誤検出しないため）
        _it, _k = next((it, s_["kind"]) for _p, s_, it, w in items if w == where)
        _ansstr = _it["choices"][_it["ans"]] if _k == "mc" else _it["ans"]
        if JA:
            # 答えの文字列を含む 6字のかたまりだけを見る
            grams = {g for g in _grams(full) if any(ch in g for ch in _ansstr[:4])}
        else:
            answ = set(words(_ansstr)) - STOP
            grams = {g for g in _grams(full)
                     if (answ & set(g.split())) and (set(g.split()) - STOP)}
        for w2, txt in printed:
            if w2 == where:
                continue
            for gram in grams & _grams(txt):     # ★変数名を g にすると Gate を潰す
                hits.append(f'{where}の答え「{gram}」が {w2} の問題文に印字')
                break
    if hits:
        g._fail(f"[解答漏洩] 答えを埋めた形が他の設問の問題文に印字されている {len(hits)}件"
                "（ページをめくれば答えが読める）: " + "／".join(hits[:10]))
    else:
        g._ok(f"[解答漏洩] {len(filled)}問 答えの形は他の設問の問題文に出現しない OK")

    # ------------- G18 四択の選択肢が、同一部内の記述問題の答えを印字していないか
    # ★単一項目（助動詞だけ等）の演習書に固有の穴。同じ項目を四択と記述の両方で問うのは
    #   設計として正しいが、四択の選択肢に記述の答えがそのまま並んでいると、
    #   四択を見た生徒は記述を考えずに書き写せる。
    def _key(x):
        return re.sub(r"[\s　「」『』（）\(\)・の]", "", str(x))

    writ = [(p["no"], w, it["ans"]) for p, s_, it, w in items
            if s_["kind"] in ("fill", "ident") and isinstance(it.get("ans"), str)]
    hits = []
    for p, s_, it, w in items:
        if s_["kind"] != "mc":
            continue
        cks = {_key(x) for x in it["choices"] if len(_key(x)) >= 5}
        for pn, w2, a in writ:
            if pn == p["no"] and _key(a) in cks:
                hits.append(f"{w} の選択肢が {w2} の答え「{a}」を印字")
    if hits:
        g._fail(f"[解答漏洩] 四択の選択肢が同じ部の記述問題の答えを印字している {len(hits)}件: "
                + "／".join(hits[:8]))
    else:
        g._ok("[解答漏洩] 四択の選択肢が同一部内の記述の答えを印字していない OK")

    # ------------------------------------- G15 設問どうしが互いの答えを教え合う
    # ★これが最大の穴だった。解答文字列の一致だけを見ていたので、
    #   「大問2の問題文が The 比較級 の形を印字 → 大問3の答えが the」のように
    #   **同じ文法項目が、一方では問題文に印字され、他方では答えになっている**組を
    #   まったく検出できなかった（冊子レビューで5組見つかった）。
    #   ▶ポイント（その問題で学ぶこと）の類似度で機械的に捕まえる。
    pts = [(w, p["no"], str(it.get("point", "")) or str(it.get("exp", ""))[:40])
           for p, _s, it, w in items]
    same_part, cross_part = [], []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            (wa, pa, ta), (wb, pb, tb) = pts[i], pts[j]
            if not ta or not tb:
                continue
            r = difflib.SequenceMatcher(None, ta, tb).ratio()
            if r < 0.62:
                continue
            (same_part if pa == pb else cross_part).append(f"{wa}⇔{wb}({r:.2f})")
    if same_part and not JA:
        g._fail(f"[出題の重複] 同じ部の中で同じ文法項目を2度問うている {len(same_part)}組"
                "（先の大問の問題文が後の答えになる）: " + "／".join(same_part))
    elif same_part:
        # 単一項目の演習書では「接続→意味→識別」と角度を変えた再出題が設計。
        # 実害（答えの印字）は G18 が直接測るので、ここは目視用の WARN に留める。
        g._ok(f"[出題の重複] 同一部内の再出題 {len(same_part)}組（単一項目の演習書なので設計どおり。"
              "答えの印字は G18 で判定）")
        for x in same_part[:6]:
            g._warn(f"[出題の重複] 同一部内の再出題（角度が違うか目視）: {x}")
    else:
        g._ok(f"[出題の重複] 同一部内で学習項目の重複なし OK（部をまたぐ再出題 {len(cross_part)}組）")
    for x in cross_part:
        g._warn(f"[出題の重複] 部をまたぐ再出題（難易度が逆転していないか目視）: {x}")

    # --------------------------------- G16 前書きの採点規定と実配点が一致するか
    stated = {"jtrans": 2, "trans": 1}   # 前書きに「1要素につき何点」と書いた値
    bad = []
    for _p, s_, it, where in items:
        if s_["kind"] not in ELEMENT_KINDS:
            continue
        per = {e[1] for e in it["elements"]}
        if per != {stated[s_["kind"]]}:
            bad.append(f'{where} 要素1つ{sorted(per)}点（前書きは{stated[s_["kind"]]}点）')
    if bad:
        g._fail("[採点規定] 前書きの「ポイント1つにつき何点」と実際の配点が食い違う"
                "（そのとおり採点すると満点にならない）: " + "／".join(bad[:6]))
    else:
        g._ok("[採点規定] 前書きの配点規定と各問の採点要素が一致 OK")

    # ------------------------- G19 誤り指摘の下線部が stem にも書かれている（二重印字）
    # ★{a}〜{d} は「ここに下線部を差し込む」印。印のあとに下線部の文字列も書くと、
    #   組版が「(a)Did Kaito and AiriDid Kaito and Airi」と二度刷る。
    #   PDF は正常に生成され、配点も解答も合っているので、機械ゲートも盲ソルバーも
    #   素通りした（盲ソルバーはデータを読むので二重印字を見ない）。冊子レビューで発覚。
    # ★「parts[j] が stem のどこかにある」で判定すると、下線部が is / to のような
    #   1〜2語のときに本文の同じ語へ誤爆する（姉妹編で実際に2件出た）。
    #   組版が二重に刷るのは「印の直後に同じ文字列が続く」ときだけなので、そこだけを見る。
    bad = []
    for where, it in errs:
        for j, c in enumerate("abcd"):
            if j >= len(it["parts"]):
                continue
            k = it["stem"].find("{%s}" % c)
            if k < 0:
                continue
            if it["stem"][k + 3:].lstrip().startswith(it["parts"][j]):
                bad.append(f'{where}({c})「{it["parts"][j][:24]}」')
    if bad:
        g._fail(f"[誤り指摘] 下線部の文字列が stem にも書かれている {len(bad)}件"
                "（組版が同じ英文を二度刷り、読めない設問になる）: " + "／".join(bad[:6]))
    else:
        g._ok(f"[誤り指摘] {len(errs)}問 stem は下線部を二重に持たない OK")

    # ------------------------------- G20 四択の正解位置が「大問ごとに」偏っていないか
    # ★冊子全体の分布が均等でも、大問の中では1番に固まっていることがある。
    #   生徒が解くのは大問単位なので、偏りは大問ごとに見ないと意味がない。
    bad = []
    for p in BOOK["parts"]:
        for s in p["sections"]:
            if s["kind"] != "mc" or len(s["items"]) < 4:
                continue
            pos = Counter(it["ans"] for it in s["items"])
            n = len(s["items"])
            if max(pos.values()) > n * 0.45:
                bad.append(f'第{p["no"]}部 大問{s["no"]} '
                           + "／".join(f"{k+1}番:{pos.get(k,0)}" for k in range(4)))
    if bad:
        g._fail("[正解位置] 大問の中で正解の番号が偏っている（読まずに当てられる）: "
                + "／".join(bad))
    else:
        g._ok("[正解位置] 四択のある全大問で、大問内の正解番号の偏りなし OK")

    # --------------------------------------------------------- G14 グリフ
    g.glyphs(BOOK)

    return g.report()


if __name__ == "__main__":
    main()
