#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
過去問 SVOCM 構造解析プリント — 全ゲート

  python3 scripts/eng_svoc_kaisetsu/check.py            # 刷るもの全部（既定）
  python3 scripts/eng_svoc_kaisetsu/check.py keio2018   # 絞る

★引数なしの既定は「刷るもの全部」。何を検査したかを必ず印字する（CLAUDE.md 2026-08-04）。

見るもの:
  ① 本文（RAW＋FILLS）と解析 DSL の全文照合 — 語を 1 つでも落としたら落ちる
  ② ラベル整合（V の欠落・DSL 構文エラー・和訳や文型の書き忘れ）
  ③ 設問解説の 4 セクション（🎯🔬📍❌）が揃っているか
  ④ 「📍本文の根拠」で引用した英文が本文に実在するか（全数照合）
  ⑤ 本文に入れた語（FILLS）と解説が主張する記号の相互照合・記号の重複
  ⑥ (F) 語句整序が与えられた語をすべて 1 回ずつ使い、コンマが 1 つか
  ⑦ ゲート自体が効いているかの自己検査（変異を入れて落ちることを確かめる）
"""
import os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _verify

ALL = ["keio2018", "todai2018"]


def load(key):
    import importlib
    return importlib.import_module({"keio2018": "content_keio2018",
                                    "todai2018": "content_todai2018"}[key])


def run(mod):
    errs = []
    _verify.check_passage(mod, errs)
    _verify.check_labels(mod, errs)
    _verify.check_questions(mod, errs)
    _verify.check_underline(mod, errs)
    return errs


class _Snap:
    """モジュールは deepcopy できないので、検査が見る属性だけを複製した器を作る。"""
    _KEYS = ("META", "RAW", "FILLS", "PARAS", "QUESTIONS",
             "OPTIONS", "ANSWER_MAP", "STANDALONE_ANSWER", "F_WORDS", "UNDERLINE")

    def __init__(self, mod):
        for k in self._KEYS:
            if hasattr(mod, k):
                setattr(self, k, copy.deepcopy(getattr(mod, k)))


def selftest():
    """★ゲートが本当に効いているかを変異で確かめる。全部『落ちる』のが正解。"""
    import content_todai2018 as T
    cases = []

    # 変異1: 解析 DSL から語を 1 つ落とす
    m = _Snap(T)
    m.PARAS[0]["sents"][2]["dsl"] = m.PARAS[0]["sents"][2]["dsl"].replace("{M:too slowly and carefully}", "")
    cases.append(("解析から語を落とす", m))

    # 変異2: 解析の語を別語に差し替える（言い換えてしまう事故）
    m = _Snap(T)
    m.PARAS[1]["sents"][4]["dsl"] = m.PARAS[1]["sents"][4]["dsl"].replace("{V:left}", "{V:kept}")
    cases.append(("解析の語を言い換える", m))

    # 変異3: 本文に無い英文を「本文の根拠」に引用する
    m = _Snap(T)
    m.QUESTIONS[0]["evidence"] = [("she told him she was deaf", "捏造した引用")]
    cases.append(("存在しない英文を引用", m))

    # 変異4: 解説の記号と本文に入れた語を食い違わせる
    m = _Snap(T)
    m.FILLS["(C)"] = "seemed"
    cases.append(("本文と解説の解答が食い違う", m))

    # 変異5: 4 セクションのうち 1 つを空にする
    m = _Snap(T)
    m.QUESTIONS[2]["struct"] = []
    cases.append(("🔬文構造分析 を欠落させる", m))

    # 変異6: (B) で同じ記号を 2 回使う
    m = _Snap(T)
    m.ANSWER_MAP["(B30)"] = ("(B)", "e")
    cases.append(("(B) で記号を重複させる", m))

    # 変異7: (F) で語を 1 つ落とす
    m = _Snap(T)
    m.FILLS["(F)"] = "know something about the buildings, the ones I photograph"
    cases.append(("(F) で語を 1 つ落とす", m))

    # 変異8: 下線部を本文に無い文字列にする
    m = _Snap(T)
    m.UNDERLINE = [("A", "It would be unlike her mother to mention it.",
                    "It would be unlike her mother to mention it.")]
    cases.append(("下線部が本文に無い", m))

    # 変異9: 下線部のアンカーを本文で一意でない文字列にする
    #        （2026-08-27 に実際に起きた事故：「will」で 3 箇所に当たっていた）
    m = _Snap(T)
    m.UNDERLINE = [("A", "her mother", "her mother")]
    cases.append(("下線部のアンカーが一意でない", m))

    # 変異10: 和訳を空にする
    m = _Snap(T)
    m.PARAS[0]["sents"][0]["ja"] = ""
    cases.append(("和訳を空にする", m))

    bad = []
    for label, mm in cases:
        try:
            errs = run(mm)
        except Exception as e:
            errs = [str(e)]
        if not errs:
            bad.append(label)
    return bad


def main():
    want = sys.argv[1:] or ALL
    unknown = [k for k in want if k not in ALL]
    if unknown:
        print(f"✗ 知らない対象: {unknown}  （選べるのは {ALL}）")
        return 1

    print("=" * 68)
    print("過去問 SVOCM 構造解析プリント — ゲート")
    print(f"検査対象: {', '.join(want)}" + ("  ← 既定（刷るもの全部）" if len(sys.argv) == 1 else ""))
    print("=" * 68)

    total = 0
    for key in want:
        mod = load(key)
        n_s = sum(len(p["sents"]) for p in mod.PARAS)
        n_q = len(getattr(mod, "QUESTIONS", []))
        n_e = sum(len(q.get("evidence", [])) for q in getattr(mod, "QUESTIONS", []))
        errs = run(mod)
        head = f"[{key}] {mod.META['school']} {mod.META['year']} {mod.META['qno']}"
        print(f"\n{head}")
        print(f"  段落 {len(mod.PARAS)} / 解析文 {n_s} / 設問 {n_q} / 引用照合 {n_e} 件")
        if errs:
            for e in errs:
                print(f"  ✗ VIOLATION: {e}")
            total += len(errs)
        else:
            print("  ✓ 本文照合・ラベル・4 セクション・引用実在・解答相互照合 すべて PASS")

    print("\n" + "-" * 68)
    print("自己検査（ゲートが効いているか・変異を入れて落ちることを確かめる）")
    survived = selftest()
    if survived:
        for s in survived:
            print(f"  ✗ VIOLATION: 変異『{s}』を入れてもゲートが通ってしまった（検査が無力）")
        total += len(survived)
    else:
        print("  ✓ 変異 10 種すべてでゲートが落ちた（検査は生きている）")

    print("=" * 68)
    if total:
        print(f"✗ {total} 件の違反。修正するまで納品しないこと。")
        return 1
    print("✓ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
