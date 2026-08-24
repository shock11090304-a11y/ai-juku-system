#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_therules.py の「根拠箇所・文法アプローチ」検査が**本当に効いているか**を確かめる。

    python3 scripts/eng_therules/check_evidence_guards.py

なぜ要るか (CLAUDE.md):
  「ゲート自体が壊れた (CRASH) / 書いたのに誰も呼んでいない (DEAD) / exit 0 なのに違反を
   印字している (INCONSISTENT)」——どれも「通った」ではなく「検査していない」。
  `if` を 1 つ消すだけでガードは無言で死ぬ。そこで**わざと壊したデータ**を食わせ、
  1 件ずつ「ちゃんと落ちること」を確認する (class_recordings/check_assign_logic.py と同じ考え方)。

やり方:
  実ファイルは書き換えない。s01 の正しいデータを読み、**メモリ上でだけ**変異させて
  check_therules.check_evidence_grammar() を直接呼ぶ。CI でも安全に回る。
"""
import copy
import importlib.util
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    with open(path, encoding="utf-8") as f:
        exec(compile(f.read(), path, "exec"), mod.__dict__)
    return mod


CHK = _load(os.path.join(HERE, "check_therules.py"), "therules_check")


def _mod_with(content, **over):
    """content の必要属性だけ持つ偽モジュールを作る (変異を載せる器)。"""
    ns = types.SimpleNamespace(
        META=content.META,
        QUESTIONS=copy.deepcopy(content.QUESTIONS),
        ANSWERS_TABLE=copy.deepcopy(content.ANSWERS_TABLE),
        EVIDENCE=copy.deepcopy(content.EVIDENCE),
        GRAMMAR=copy.deepcopy(content.GRAMMAR),
        GRAMMAR_STEPS=copy.deepcopy(content.GRAMMAR_STEPS),
    )
    for k, v in over.items():
        setattr(ns, k, v)
    return ns


# ---- 変異 (どれも「刷る前に気づきたい」実際の事故) -------------------------
def m_quote_fake(m):
    """引用の英文を1語だけ書き換える = 本文に無い英文を根拠として示す。"""
    m.EVIDENCE[3]["items"][0]["en"] = m.EVIDENCE[3]["items"][0]["en"].replace(
        "a sign of idleness", "a sign of laziness")


def m_choice_untouched(m):
    """選択肢の1つを論じ忘れる (誤答の理由が抜けた解説)。"""
    for it in m.EVIDENCE[6]["items"]:
        it["where"] = it["where"].replace("④", "")


def m_answer_drift(m):
    """解答表だけ直して根拠を直し忘れる (逆でも同じ)。"""
    m.EVIDENCE[5]["ans"] = "①"


def m_missing_question(m):
    """設問1つぶん根拠が無い。"""
    m.EVIDENCE = [e for e in m.EVIDENCE if e["no"] != "問3"]


def m_empty_items(m):
    """根拠が空の設問。"""
    m.EVIDENCE[0]["items"] = []


def m_missing_field(m):
    """訳や判断の欠落 (引用だけ貼って解説が無い)。"""
    m.EVIDENCE[2]["items"][0]["why"] = ""


def m_bad_mark(m):
    """○× 以外の記号 (表示が崩れる)。"""
    m.EVIDENCE[6]["items"][0]["mark"] = "▲"


def m_grammar_fake_ex(m):
    """文法の例文を本文に無い英文に差し替える (作文した例文を本文だと偽る)。"""
    m.GRAMMAR[7]["ex"][0] = ("bows to no master at all", "いかなる主人にも屈しない")


def m_grammar_missing_field(m):
    """誤読しやすい点 (trap) の欠落。"""
    m.GRAMMAR[0]["trap"] = ""


def m_grammar_dup_id(m):
    """id の重複 (相互参照が壊れる)。"""
    m.GRAMMAR[1]["id"] = m.GRAMMAR[0]["id"]


def m_no_steps(m):
    """解法手順を消す。"""
    m.GRAMMAR_STEPS = []


def m_bad_step_shape(m):
    """手順の形が違う。"""
    m.GRAMMAR_STEPS = [("STEP 1", "見出しだけ")]


def m_grammar_no_ja(m):
    """例文の訳が無い。"""
    m.GRAMMAR[2]["ex"][0] = (m.GRAMMAR[2]["ex"][0][0], "")


MUTATIONS = [
    ("引用が本文に無い英文になっている", m_quote_fake),
    ("選択肢を1つ論じ忘れている", m_choice_untouched),
    ("根拠側の解答が解答表と食い違う", m_answer_drift),
    ("設問1つぶん根拠が無い", m_missing_question),
    ("根拠が空の設問がある", m_empty_items),
    ("根拠の判断(why)が空", m_missing_field),
    ("○×以外の記号が入っている", m_bad_mark),
    ("文法の例文が本文に無い", m_grammar_fake_ex),
    ("文法の誤読ポイント(trap)が空", m_grammar_missing_field),
    ("文法の id が重複している", m_grammar_dup_id),
    ("解法手順(GRAMMAR_STEPS)が無い", m_no_steps),
    ("解法手順の形が違う", m_bad_step_shape),
    ("文法の例文に訳が無い", m_grammar_no_ja),
]


def run_for(path, label, fails):
    content = _load(path, "therules_guard_" + label.replace("/", "_"))
    if not hasattr(content, "EVIDENCE") and not hasattr(content, "GRAMMAR"):
        return 0
    passage = CHK.norm(content.PASSAGE_PLAIN)
    q_nos = [q["no"] for q in content.QUESTIONS]

    # 0) 手を加えていない正しいデータは必ず 0 件 (誤検知しないこと)
    bad = []
    CHK.check_evidence_grammar(_mod_with(content), label, bad, passage, q_nos)
    if bad:
        fails.append(f"{label}: 正しいデータなのに違反が出た (誤検知) → {bad[0]}")
        print(f"  ✗ {label}: 正しいデータで違反 {len(bad)} 件")
    else:
        print(f"  ✓ {label}: 正しいデータは違反 0 件")

    # 1) 変異を1つずつ入れて、必ず捕まることを確かめる
    n = 0
    for name, mutate in MUTATIONS:
        m = _mod_with(content)
        mutate(m)
        bad = []
        CHK.check_evidence_grammar(m, label, bad, passage, q_nos)
        if bad:
            print(f"  ✓ 検知: {name}")
        else:
            fails.append(f"{label}: 変異「{name}」を見逃した (ガードが死んでいる)")
            print(f"  ✗ ★見逃し: {name}")
        n += 1
    return n


def main():
    import glob
    paths = sorted(glob.glob(os.path.join(HERE, "*", "content.py")))
    paths += sorted(glob.glob(os.path.join(HERE, "content_no*.py")))
    fails, n_books, n_mut = [], 0, 0
    for path in paths:
        label = os.path.relpath(path, HERE)
        content = _load(path, "probe_" + label.replace("/", "_").replace(".", "_"))
        if not (hasattr(content, "EVIDENCE") or hasattr(content, "GRAMMAR")):
            continue
        print(f"[{label}] 根拠箇所・文法アプローチのガードを変異で検査")
        n_books += 1
        n_mut += run_for(path, label, fails)

    if n_books == 0:
        # 検査対象ゼロで緑を出さない (DEAD 判定)
        print("NG: EVIDENCE/GRAMMAR を持つ冊が 1 つも無い。"
              "セクションを消したなら、このゲートも一緒に畳むこと。")
        return 1
    if fails:
        for f in fails:
            print(f"NG: {f}")
        print(f"違反 {len(fails)} 件")
        return 1
    print(f"=== ALL PASS (冊子 {n_books} / 変異 {n_mut} 種をすべて検知) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
