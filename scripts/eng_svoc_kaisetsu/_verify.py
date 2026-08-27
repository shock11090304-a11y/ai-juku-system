# -*- coding: utf-8 -*-
"""照合の実体。check.py と build.py の両方がこれを呼ぶ（判定を二重に書かない）。"""
import os, re, sys, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import core


def restored_text(para):
    """1 段落分の解析 DSL から英文を復元して連結する。"""
    return " ".join(core.plain_text(core.parse(s["dsl"])) for s in para["sents"])


def check_passage(mod, errs):
    """本文（RAW＋FILLS）と解析 DSL の全文照合。段落単位で突き合わせる。"""
    name = mod.META["key"]
    if len(mod.RAW) != len(mod.PARAS):
        errs.append(f"[{name}] 段落数が合わない: RAW {len(mod.RAW)} / PARAS {len(mod.PARAS)}")
        return
    filled = core.apply_fills(mod.RAW, mod.FILLS)
    for i, (raw, para) in enumerate(zip(filled, mod.PARAS), 1):
        want = core.cmp_norm(raw)
        got = core.cmp_norm(restored_text(para))
        if want != got:
            errs.append(f"[{name}] 第{i}段落: 解析 DSL から復元した英文が本文と一致しない\n"
                        + _diff(want, got))


def _diff(want, got):
    w, g = want.split(), got.split()
    out = []
    for line in difflib.unified_diff(w, g, "本文", "復元", lineterm="", n=2):
        if line.startswith(("---", "+++", "@@")):
            continue
        out.append("      " + line)
        if len(out) > 24:
            out.append("      …")
            break
    return "\n".join(out)


def check_labels(mod, errs):
    """ラベルの整合。V が 1 つも無い解析、未知ラベル、空チャンクを弾く。"""
    name = mod.META["key"]
    for para in mod.PARAS:
        for j, s in enumerate(para["sents"], 1):
            where = f"[{name}] 第{para['no']}段落 第{j}文"
            try:
                node = core.parse(s["dsl"])
            except ValueError as e:
                errs.append(f"{where}: DSL 構文エラー: {e}")
                continue
            labels = [n.label for n in core.iter_nodes(node) if n.label]
            has_v = any(l.startswith("V") or l == "助" for l in labels)
            if not has_v and not s.get("frag"):
                errs.append(f"{where}: V も 助 も無い（frag 指定も無い）")
            if has_v and s.get("frag") and not any(
                    n.label in ("V", "助") for n in core.iter_nodes(node)):
                pass
            if not s.get("ja", "").strip():
                errs.append(f"{where}: 和訳が空")
            if not s.get("pat", "").strip():
                errs.append(f"{where}: 文型の表示が空")


core.iter_nodes = core.hb.iter_nodes


def check_questions(mod, errs):
    """設問解説の検査。CLAUDE.md の 4 セクション必須 ＋ 引用の実在 ＋ 解答の相互照合。"""
    name = mod.META["key"]
    qs = getattr(mod, "QUESTIONS", None)
    if not qs:
        return
    body = core.cmp_norm(" ".join(core.apply_fills(mod.RAW, mod.FILLS)))
    seen = set()
    for q in qs:
        w = f"[{name}] 設問{q['no']}"
        if q["no"] in seen:
            errs.append(f"{w}: 設問番号が重複")
        seen.add(q["no"])
        # --- 4 セクション（🎯 コアイメージ / 🔬 文構造分析 / 📍 本文の根拠 / ❌ 誤答NG）
        for key, ja in (("core", "🎯 コアイメージ"), ("struct", "🔬 文構造分析"),
                        ("evidence", "📍 本文の根拠"), ("ng", "❌ 誤答 NG 理由")):
            if not q.get(key):
                errs.append(f"{w}: 「{ja}」が空（4 セクション必須）")
        if not q.get("ans", "").strip():
            errs.append(f"{w}: 解答が空")
        # --- 引用した英文が本文に実在するか（全数照合）
        for quote, _note in q.get("evidence", []):
            if core.cmp_norm(quote) not in body:
                errs.append(f"{w}: 📍本文の根拠 の引用が本文に無い → {quote!r}")

    # --- 解答の相互照合: 本文に入れた語（FILLS）と解説の主張する記号が一致するか
    opts = getattr(mod, "OPTIONS", {})
    for marker, (qno, letter) in getattr(mod, "ANSWER_MAP", {}).items():
        want = opts.get(qno, {}).get(letter)
        if want is None:
            errs.append(f"[{name}] {marker}: 選択肢 {qno} {letter}) が OPTIONS に無い")
            continue
        got = mod.FILLS.get(marker)
        if core.cmp_norm(got or "") != core.cmp_norm(want):
            errs.append(f"[{name}] {marker}: 本文に入れた語と解説の記号が食い違う "
                        f"（本文 {got!r} / {qno} {letter}) は {want!r}）")
        q = next((x for x in mod.QUESTIONS if x["no"] == qno), None)
        if q and letter not in q["ans"]:
            errs.append(f"[{name}] {marker}: 解答欄に記号 {letter}) が書かれていない → {q['ans']!r}")

    # --- 重複不可の設問で記号が重複していないか
    b_letters = [l for m, (qq, l) in getattr(mod, "ANSWER_MAP", {}).items() if qq == "(B)"]
    if len(b_letters) != len(set(b_letters)):
        errs.append(f"[{name}] (B): 同じ記号を複数回使っている → {sorted(b_letters)}")

    # --- 単独選択問題（本文の空所ではないもの）の記号が解答欄に書かれているか
    for qno, letter in getattr(mod, "STANDALONE_ANSWER", {}).items():
        q = next((x for x in mod.QUESTIONS if x["no"] == qno), None)
        if not q:
            errs.append(f"[{name}] {qno}: 設問が見つからない")
        elif letter not in q["ans"]:
            errs.append(f"[{name}] {qno}: 解答欄に記号 {letter}) が無い → {q['ans']!r}")
        elif qno in opts and opts[qno][letter] not in q["ans"]:
            errs.append(f"[{name}] {qno}: 解答欄の本文が選択肢 {letter}) と違う")

    # --- (F) 語句整序: 与えられた語をすべて 1 回ずつ使い、コンマがちょうど 1 つか
    fw = getattr(mod, "F_WORDS", None)
    if fw:
        got = mod.FILLS.get("(F)", "")
        used = [t.strip(",") for t in got.split()]
        if sorted(used) != sorted(fw):
            errs.append(f"[{name}] (F): 与えられた語と使った語が一致しない\n"
                        f"      与: {sorted(fw)}\n      使: {sorted(used)}")
        if got.count(",") != 1:
            errs.append(f"[{name}] (F): コンマがちょうど 1 つでない（{got.count(',')} 個）")
        qf = next((x for x in mod.QUESTIONS if x["no"] == "(F)"), None)
        if qf and core.cmp_norm(qf["ans"]) != core.cmp_norm(got):
            errs.append(f"[{name}] (F): 解答欄と本文に入れた語句が違う\n"
                        f"      解答欄: {qf['ans']!r}\n      本文  : {got!r}")


def check_underline(mod, errs):
    """表示用の下線部が本文に実在するか。ここがずれると解説の指し示す場所が狂う。"""
    name = mod.META["key"]
    body = core.cmp_norm(" ".join(core.apply_fills(mod.RAW, mod.FILLS)))
    for label, anchor, target in getattr(mod, "UNDERLINE", []):
        n = body.count(core.cmp_norm(anchor))
        if n == 0:
            errs.append(f"[{name}] 下線部({label}) のアンカーが本文に無い → {anchor!r}")
        elif n > 1:
            errs.append(f"[{name}] 下線部({label}) のアンカーが本文に {n} 箇所ある"
                        f"（どれに下線が付くか決まらない）→ {anchor!r}")
        if core.cmp_norm(target) not in core.cmp_norm(anchor):
            errs.append(f"[{name}] 下線部({label}) の下線部分がアンカーの中に無い → {target!r}")
