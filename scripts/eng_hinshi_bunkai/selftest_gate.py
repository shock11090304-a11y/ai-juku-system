# -*- coding: utf-8 -*-
"""check.py のゲートが「本当に落とせるか」を、故意の欠陥を注入して確かめる。

過去に素通りした 6 種（下線部の番号ずれ / 訳のドリフト / 語注の取り違え /
生タグ混入 / 問2 と問3 の重複 / pat と文型ラベルの不一致）と、
parse() の無限ループを再現し、いずれも検出・例外になることを確認する。
"""
import copy, importlib, signal, sys
import content as C
import check as K


def run_check():
    """check.main() を走らせ、(exit_code, ERR一覧) を返す。"""
    K.ERR.clear()
    K.WARN.clear()
    out = 0
    try:
        K.main()
    except SystemExit as e:
        out = e.code or 0
    return out, list(K.ERR)


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


@case("下線部の番号ずれ（問2 が別の文を引用）")
def _(P):
    P[0]["mcq"][0]["q"] = P[0]["mcq"][0]["q"].replace("下線部 (1)", "下線部 (5)")


@case("訳のドリフト（sents.ja と全訳の不一致）")
def _(P):
    P[0]["sents"][0]["ja"] = P[0]["sents"][0]["ja"].replace("空いている", "あいている")


@case("語注の取り違え（他の長文の語を混入）")
def _(P):
    P[0]["vocab"] = P[0]["vocab"] + [("yogurt", "名 ヨーグルト")]


@case("生タグ混入（< を書いて語が消える）")
def _(P):
    P[0]["sents"][0]["notes"][0] = "<of the park> は size にかかる。"


@case("問2 と問3 の重複（採点ポイントの先出し）")
def _(P):
    P[0]["trans"][0]["n"] = 1          # 長文1 の問2 は下線部 (1) を扱っている


@case("pat と文型ラベルの不一致（第3文型なのに O が無い）")
def _(P):
    P[0]["sents"][1]["pat"] = "第3文型（SVO）"   # 実際は第1文型（SV）


@case("4択の正解位置の偏り")
def _(P):
    for q in P[0]["mcq"]:
        q["ans"] = 0


def main():
    base = copy.deepcopy(C.PASSAGES)

    code, errs = run_check()
    if code or errs:
        print("!! ベースラインが既に NG。先に本体を直すこと。")
        for e in errs:
            print("  ", e)
        sys.exit(1)
    print("baseline: ALL CHECKS PASSED\n")

    ng = 0
    for name, mutate in CASES:
        C.PASSAGES[:] = copy.deepcopy(base)
        K.PASSAGES = C.PASSAGES
        mutate(C.PASSAGES)
        code, errs = run_check()
        caught = bool(code) and bool(errs)
        print(f"[{'検出' if caught else '素通り'}] {name}")
        if caught:
            print(f"         → {errs[0][:110]}")
        else:
            ng += 1
    C.PASSAGES[:] = base
    K.PASSAGES = C.PASSAGES

    # parse() の孤立 '}' がハングせず ValueError になること
    from core import parse

    def on_alarm(*_):
        raise TimeoutError("parse がハングした")
    signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(3)
    try:
        parse("{S:A} {V:b} } {O:c} .")
        print("[素通り] 孤立した '}' が例外にならない")
        ng += 1
    except TimeoutError:
        print("[素通り] 孤立した '}' で parse が無限ループ")
        ng += 1
    except ValueError:
        print("[検出] 孤立した '}' → ValueError")
    finally:
        signal.alarm(0)

    print(f"\n素通り {ng} 件 / 全 {len(CASES) + 1} ケース")
    sys.exit(1 if ng else 0)


if __name__ == "__main__":
    main()
