#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The Rules 式 長文教材の全冊を検査する (相互チェック ②層)。

    python3 scripts/eng_therules/check_therules.py

引数なし = **eng_therules/*/content.py の全冊** (CLAUDE.md「引数なしの既定は刷るもの全部」)。
run_all_gates.py が check* として自動で拾う。何を見たかを必ず印字する。

見るもの (どれも「紙に出てから気づく」と手遅れになるもの):
  ・PASSAGE_HTML と PASSAGE_PLAIN の一致 — 語数表示と全訳・SVOC の土台がずれていないか
    (空所は正解語で埋める規約なので、空所の語だけは差分を許す)
  ・★解説・設問・SVOC が引用する英文が**本文に実在する**か (CLAUDE.md「引用は本文に実在させる」)
  ・配点の合計が META['full'] と一致するか (問題編と解答編の両方)
  ・解答表・記述解答が**全設問を漏れなく**カバーしているか (問N の抜け)
  ・下線部 <u>…<sup>(n)</sup> の番号が連番で、設問から参照されているか
  ・SVOC_LOGIC のキー (段, 文) が実データの文数の範囲に収まっているか
    (ずれると「別の文にチップが付く」= 誰も気づかないまま刷られる)
  ・★EVIDENCE (設問別・根拠箇所) / GRAMMAR (文法アプローチ) を持つ冊は:
      - 引用した英文が本文に実在するか
      - 全設問に根拠が付いているか / 記号選択肢 (①②…) を一つ残らず論じているか
      - 根拠側の解答が ANSWERS_TABLE の解答と食い違っていないか
        (★解答表だけ直して根拠を直し忘れる、を止める)
    ※持たない冊は素通りではなく「根拠/文法セクション無し」と印字して数える。

★ rulehunt*/check.py と違い、こちらは**引数なしで全冊**を見る。新しい号を足したら
  ここに何もしなくても自動で検査対象になる。
"""
import glob
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_content(path):
    """content.py を **ソースから直接** 読み込む。

    ★ importlib の exec_module は __pycache__ の .pyc を使うことがある。
      .pyc は (mtime, size) でしか検証されないので、書き戻し等で両方が一致すると
      **古いバイトコードのまま検査が通る**。それでは「刷るファイル」ではなく
      「昔のファイル」を検査したことになる (2026-08-24 に実際に踏んだ)。
      ここは必ず .py のテキストを compile して、紙になる中身そのものを見る。
    """
    name = "therules_" + re.sub(r"\W", "_", os.path.relpath(path, HERE))
    with open(path, encoding="utf-8") as f:
        source = f.read()
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    exec(compile(source, path, "exec"), mod.__dict__)
    return mod


ENTITIES = {"&mdash;": "-", "&ndash;": "-", "&nbsp;": " ", "&lt;": "<", "&gt;": ">",
            "&amp;": "&", "&quot;": '"', "&ldquo;": '"', "&rdquo;": '"',
            "&lsquo;": "'", "&rsquo;": "'", "&hellip;": "…"}

# SVOC が**補って**書く省略語。本文には無いので照合前に外す
#   例: the medicines &lt;(that) we swallow&gt; / the year &lt;(when) a treaty was signed&gt;
SUPPLIED = re.compile(r"\((that|which|who|whom|whose|when|where|why|do|does|did|to|be)\)",
                      re.I)


def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    for k, v in ENTITIES.items():
        s = s.replace(k, v)
    return s


def norm(s):
    """照合用: タグ・実体参照・補った省略語・記号・空白の揺れを吸収する。"""
    s = strip_tags(s)
    s = SUPPLIED.sub(" ", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[–—]", "-", s)
    s = re.sub(r"[^A-Za-z0-9']+", " ", s)
    return " ".join(s.split()).lower()


def fragments(s):
    """引用を「…」で分割する。省略記号入りの引用は断片ごとに本文照合する。"""
    return [f for f in re.split(r"…+|\.\.\.+", strip_tags(s)) if f.strip()]


# 引用として拾う英文 (2 語以上の連なり) を解説文から抜き出す
QUOTE_RE = re.compile(r"(?:<span class='en'>|<span class=\"en\">)([^<]+)</span>")



MARU = "①②③④⑤⑥⑦⑧⑨"


def _ans_key(s):
    """解答文字列の表記ゆれ (全角空白・／・スペース) を吸収して比較用に潰す。"""
    return re.sub(r"[\s\u3000／/]+", "", strip_tags(s or ""))


def check_evidence_grammar(mod, label, bad, passage, q_nos):
    """EVIDENCE / GRAMMAR (任意セクション) を検査し、(根拠数, 文法数) を返す。

    どちらも「引用が本文に実在する」ことが生命線。持たない冊は (None, None)。
    """
    n_ev = n_gr = None

    ev = getattr(mod, "EVIDENCE", None)
    if ev is not None:
        n_ev = 0
        table_ans = {r["no"]: r["ans"] for r in mod.ANSWERS_TABLE}
        q_by_no = {q["no"]: q for q in mod.QUESTIONS}
        covered = {e["no"] for e in ev}
        for no in q_nos:
            if no not in covered:
                bad.append(f"{label}: 根拠箇所(EVIDENCE) に {no} が無い")
        for e in ev:
            if e["no"] not in q_nos:
                bad.append(f"{label}: EVIDENCE の {e['no']} に対応する設問が無い")
            if not e.get("items"):
                bad.append(f"{label}: EVIDENCE {e['no']} の根拠が空")
            # 解答表と食い違っていないか
            if e["no"] in table_ans and _ans_key(e.get("ans")) != _ans_key(table_ans[e["no"]]):
                bad.append(f"{label}: EVIDENCE {e['no']} の解答が解答表と食い違う "
                           f"(根拠「{strip_tags(e.get('ans'))}」/ 解答表「{strip_tags(table_ans[e['no']])}」)")
            for it in e.get("items") or []:
                for k in ("para", "where", "en", "ja", "why"):
                    if not it.get(k):
                        bad.append(f"{label}: EVIDENCE {e['no']} に {k} が無い項目がある")
                if it.get("mark") not in (None, "○", "×"):
                    bad.append(f"{label}: EVIDENCE {e['no']} の mark が ○/× でない 「{it.get('mark')}」")
                nq = norm(it.get("en", ""))
                if len(nq.split()) < 3:
                    bad.append(f"{label}: EVIDENCE {e['no']} の引用が短すぎる 「{strip_tags(it.get('en',''))[:40]}」")
                elif nq not in passage:
                    bad.append(f"{label} EVIDENCE {e['no']}: 引用が本文に無い "
                               f"「{strip_tags(it['en'])[:60]}」")
                n_ev += 1
            # 記号選択肢 (①②… で始まる) は一つ残らず論じること
            q = q_by_no.get(e["no"])
            if q:
                marks = [c.strip()[0] for c in (q.get("choices") or [])
                         if c.strip() and c.strip()[0] in MARU]
                where_all = " ".join((it.get("where") or "") for it in e.get("items") or [])
                for m in marks:
                    if m not in where_all:
                        bad.append(f"{label}: EVIDENCE {e['no']} が選択肢 {m} に触れていない")

    gr = getattr(mod, "GRAMMAR", None)
    if gr is not None:
        n_gr = 0
        seen_ids = set()
        for g in gr:
            for k in ("id", "title", "star", "use", "point", "ex", "how", "trap"):
                if not g.get(k):
                    bad.append(f"{label}: GRAMMAR {g.get('id','?')} に {k} が無い")
            if g.get("id") in seen_ids:
                bad.append(f"{label}: GRAMMAR の id が重複 {g.get('id')}")
            seen_ids.add(g.get("id"))
            for pair in g.get("ex") or []:
                if len(pair) != 2:
                    bad.append(f"{label}: GRAMMAR {g.get('id')} の ex は (英, 訳) の2つ組で書く")
                    continue
                en, ja = pair
                if not ja:
                    bad.append(f"{label}: GRAMMAR {g.get('id')} の例文に訳が無い")
                ne = norm(en)
                if len(ne.split()) < 3:
                    bad.append(f"{label}: GRAMMAR {g.get('id')} の例文が短すぎる 「{strip_tags(en)[:40]}」")
                elif ne not in passage:
                    bad.append(f"{label} GRAMMAR {g.get('id')}: 例文が本文に無い 「{strip_tags(en)[:60]}」")
                n_gr += 1
        steps = getattr(mod, "GRAMMAR_STEPS", None)
        if not steps:
            bad.append(f"{label}: GRAMMAR があるのに GRAMMAR_STEPS (解法手順) が無い")
        else:
            for s in steps:
                if len(s) != 3:
                    bad.append(f"{label}: GRAMMAR_STEPS の項目は (番号, 見出し, 本文) の3つ組 {s[:1]}")
    return n_ev, n_gr


def check_book(mod, label, bad):
    meta = mod.META
    # --- 1. PASSAGE_HTML ⇔ PASSAGE_PLAIN --------------------------------
    html_words = norm(" ".join(b for _n, b in mod.PASSAGE_HTML)).split()
    plain_words = norm(mod.PASSAGE_PLAIN).split()
    # 空所 (【 A 】【 B 】) は PLAIN では正解語で埋める規約 → 語数の差は空所数まで許す
    n_blank = sum(b.count('class="blank"') for _n, b in mod.PASSAGE_HTML)
    if abs(len(html_words) - len(plain_words)) > n_blank + 2:
        bad.append(f"{label}: PASSAGE_HTML と PASSAGE_PLAIN の語数が食い違う "
                   f"(HTML {len(html_words)} / PLAIN {len(plain_words)} / 空所 {n_blank})")

    passage = norm(mod.PASSAGE_PLAIN)

    # --- 2. 引用した英文が本文に実在するか -------------------------------
    def check_quotes(text, where):
        for q in QUOTE_RE.findall(text):
            for frag in fragments(q):
                nq = norm(frag)
                if len(nq.split()) >= 3 and nq not in passage:
                    bad.append(f"{label} {where}: 引用が本文に無い 「{frag.strip()[:60]}」")

    for q in mod.QUESTIONS:
        check_quotes(q["stem"], q["no"])
        for c in q.get("choices") or []:
            check_quotes(c, q["no"])
    for r in mod.ANSWERS_TABLE:
        check_quotes(r["exp"], r["no"] + " 解説")
    for w in mod.ANSWERS_WRITTEN:
        check_quotes(w.get("points", ""), w["no"] + " 採点要素")

    # --- 3. SVOC の英文が本文に実在するか --------------------------------
    for p_idx, para in enumerate(mod.SVOC, 1):
        for s_idx, sent in enumerate(para["sentences"], 1):
            for tag, en, _ja in sent["chunks"]:
                ne = norm(en)
                if len(ne.split()) >= 4 and ne not in passage:
                    bad.append(f"{label} SVOC 第{p_idx}段 第{s_idx}文: "
                               f"本文に無い英文 「{strip_tags(en)[:60]}」")

    # --- 4. 配点の合計 = 満点 -------------------------------------------
    def pts_of(s):
        m = re.search(r"(\d+)\s*点", s or "")
        return int(m.group(1)) if m else 0

    total = 0
    for q in mod.QUESTIONS:
        p = pts_of(q["pts"])
        if "各" in q["pts"]:
            n = len(q.get("choices") or [])
            if "三つ" in q["stem"]:
                n = 3
            total += p * max(n, 1)
        else:
            total += p
    if total != meta["full"]:
        bad.append(f"{label}: 配点の合計が満点と合わない (合計 {total} / 満点 {meta['full']})")

    # --- 5. 全設問が解答編でカバーされているか ---------------------------
    q_nos = [q["no"] for q in mod.QUESTIONS]
    covered = {r["no"] for r in mod.ANSWERS_TABLE} | {w["no"] for w in mod.ANSWERS_WRITTEN}
    for no in q_nos:
        if no not in covered:
            bad.append(f"{label}: {no} の解答が解答編に無い")
    for no in covered:
        if no not in q_nos:
            bad.append(f"{label}: 解答編の {no} に対応する設問が無い")

    # --- 6. 下線部の番号 -------------------------------------------------
    sups = [int(m) for _n, b in mod.PASSAGE_HTML
            for m in re.findall(r"<sup>\((\d+)\)</sup>", b)]
    if sups != sorted(sups) or sups != list(range(1, len(sups) + 1)):
        bad.append(f"{label}: 下線部の番号が連番でない {sups}")
    body = " ".join(q["stem"] for q in mod.QUESTIONS)
    for n in sups:
        if f"({n})" not in body:
            bad.append(f"{label}: 下線部({n}) を参照する設問が無い")

    # --- 7. SVOC_LOGIC のキーが実データの範囲に収まっているか -------------
    logic = getattr(mod, "SVOC_LOGIC", {})
    for (p_idx, s_idx) in logic:
        if not (1 <= p_idx <= len(mod.SVOC)):
            bad.append(f"{label}: SVOC_LOGIC の段番号 {p_idx} が範囲外 (全{len(mod.SVOC)}段)")
        elif not (1 <= s_idx <= len(mod.SVOC[p_idx - 1]["sentences"])):
            bad.append(f"{label}: SVOC_LOGIC ({p_idx}, {s_idx}) が範囲外 "
                       f"(第{p_idx}段は {len(mod.SVOC[p_idx - 1]['sentences'])} 文)")

    # --- 8. 全訳・図解・ルールの体裁 --------------------------------------
    if len(mod.TRANSLATION) != len(mod.PASSAGE_HTML):
        bad.append(f"{label}: 全訳の段落数が本文と違う "
                   f"(全訳 {len(mod.TRANSLATION)} / 本文 {len(mod.PASSAGE_HTML)})")
    if len(mod.SVOC) != len(mod.PASSAGE_HTML):
        bad.append(f"{label}: SVOC の段落数が本文と違う "
                   f"(SVOC {len(mod.SVOC)} / 本文 {len(mod.PASSAGE_HTML)})")
    if not mod.VOCAB:
        bad.append(f"{label}: 重要語彙が空")
    for cat, items in mod.RULES.items():
        for r in items:
            if len(r) != 4:
                bad.append(f"{label}: RULES[{cat}] の項目の形が違う {r[:1]}")

    # --- 9. 設問別・根拠箇所 / 文法アプローチ (任意セクション) ---------
    q_nos_all = [q["no"] for q in mod.QUESTIONS]
    n_ev, n_gr = check_evidence_grammar(mod, label, bad, passage, q_nos_all)
    return len(mod.QUESTIONS), n_ev, n_gr


def main():
    paths = sorted(glob.glob(os.path.join(HERE, "*", "content.py")))
    paths += sorted(glob.glob(os.path.join(HERE, "content_no*.py")))
    if not paths:
        print("NG: 検査対象の content.py が 1 つも無い")
        return 1
    bad, n_books, n_qs = [], 0, 0
    n_ev_books = n_gr_books = 0
    for path in paths:
        label = os.path.relpath(path, HERE)
        try:
            mod = load_content(path)
        except Exception as e:
            bad.append(f"{label}: content.py を読めない ({e})")
            continue
        if not (hasattr(mod, "META") and hasattr(mod, "PASSAGE_HTML")
                and hasattr(mod, "QUESTIONS")):
            print(f"[SKIP] {label} (The Rules 式の content でない)")
            continue
        n_books += 1
        before = len(bad)
        nq, n_ev, n_gr = check_book(mod, label, bad)
        n_qs += nq
        # 何を見たかを必ず印字する (CLAUDE.md)。任意セクションは有無まで出す。
        extra = (f" / 根拠{n_ev}箇所" if n_ev is not None else " / 根拠セクション無し")
        extra += (f" / 文法例{n_gr}文" if n_gr is not None else " / 文法セクション無し")
        if n_ev is not None:
            n_ev_books += 1
        if n_gr is not None:
            n_gr_books += 1
        if len(bad) == before:
            print(f"[OK] {label} (No.{mod.META['no']} {mod.META['level']} / "
                  f"{len(mod.QUESTIONS)}問{extra})")
        else:
            print(f"[..] {label} に指摘あり (下に一覧)")
    if bad:
        for x in bad:
            print(f"NG: {x}")
        print(f"違反 {len(bad)} 件")
        return 1
    print(f"=== ALL PASS (冊子 {n_books} / 設問 {n_qs} / 根拠箇所つき {n_ev_books}冊 ・ 文法アプローチつき {n_gr_books}冊) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
