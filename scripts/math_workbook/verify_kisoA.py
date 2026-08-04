#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数学の基礎徹底問題集の機械ゲート（build_kiso.py より先に実行する）。

  python3 verify_kisoA.py                 # 数A（既定）
  python3 verify_kisoA.py content_kisoI   # 数I
  python3 verify_kisoA.py content_kisoII  # 数II

  A. sympy 検算 …… 各問の chk() を実行し、答えを独立再計算して一致を確認
  B. 汎用ゲート …… scripts/_workbook_gates.py（解答漏洩・文字監査など）
  C. 数学固有 ……
     ・chk が None（手検証）の問題を一覧化し、割合が高すぎないか
     ・stem の重複（同じ問題を2回載せていないか）
     ・LaTeX の $ の対応が取れているか（奇数個＝崩れる）／日本語が $...$ の中に入っていないか
     ・answer に出てくる数値が chk で再計算した値と結びついているか（answerの空文字検出）
     ・level の値が想定内か／group が空でないか
     ・★選択肢問題(ア)(イ)…の正解位置の偏り
"""
import os
import re
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # scripts/
sys.path.insert(0, HERE)

import importlib                           # noqa: E402

from _workbook_gates import Gate            # noqa: E402

# ★引数なしのときは kisoA 系の**全冊**を検査する。以前は content_kisoA だけで、
#   同じ規約で書かれた kisoI / kisoII / kisoIII が対象外だった
#   （run_all_gates.py は引数を渡さないので、CI は1冊しか見ていなかった）。
#   content_kiso / content_kiso2 は av を持たない別規約なので **verify.py 側**が見る
#   （どちらの検査にも属さない本を作らないこと）。
DEFAULT_MODS = ["content_kisoA", "content_kisoI", "content_kisoII", "content_kisoIII"]

# ★親（引数なし）では content を import しない。ここで読むと、1冊目が壊れているだけで
#   親が即クラッシュして**残り3冊が1冊も走らない**。子プロセスに1冊ずつ任せる。
MOD = sys.argv[1] if len(sys.argv) > 1 else None
C = importlib.import_module(MOD) if MOD else None

g = Gate()
ALL = ([(p["area"], u, q) for p in C.PARTS for u in p["units"] for q in u["problems"]]
       if C else [])
LEVELS = {"basic", "standard", "advanced"}
# 日本語がこの中にあると KaTeX が崩れる
JP = re.compile(r"[ぁ-んァ-ヶ一-龥]")


# ---------------------------------------------------------------- A. sympy 検算
def check_sympy():
    """★chk は「答えの値 av」を受け取って照合する形にしてある。
    以前は chk がリテラルどうしを比べるだけで answer を一切見ておらず、
    answer を誤りに書き換えても全問パスした（変異テストで実証済み）。
    いまは av を経由するので、answer↔av↔chk の3者が連動する。"""
    ok = fail = manual = 0
    fails, manuals = [], []
    for area, u, q in ALL:
        tag = f'{u["name"]}／{q["stem"][:24]}…'
        chk = q.get("chk")
        if chk is None:
            manual += 1
            manuals.append(tag)
            continue
        if "av" not in q and not q.get("proof"):
            fail += 1
            fails.append(f'{tag}  chk はあるが av（答えの値）が無い＝answerと連動していない')
            continue
        try:
            r = chk(q["av"]) if "av" in q else chk()
        except Exception:
            fail += 1
            fails.append(f'{tag}  例外: {traceback.format_exc(limit=1).splitlines()[-1]}')
            continue
        if r is True or r == 1:
            ok += 1
        else:
            fail += 1
            fails.append(f'{tag}  chk(av) が True を返さない: {r!r}')
    for f in fails:
        g._fail(f"[sympy検算] {f}")
    total = len(ALL)
    g._ok(f"[sympy検算] 全{total}問中 {ok}問を独立再計算して一致 ／ 手検証{manual}問 ／ 失敗{fail}問")
    if manual > total * 0.25:
        g._fail(f"[sympy検算] 手検証の問題が{manual}/{total}問＝{manual/total:.0%}と多すぎる"
                "（式で書ける問題はchkを付けること）")
    for m in manuals:
        g._warn(f"[手検証] chk無し（人間が確認する必要あり）: {m}")


# ---------------------------------------------------------------- C. 数学固有
def check_answer_matches_av():
    """★印刷される answer と、検算に使う av がズレていないか。
    ここが無いと「chk は通るのに冊子には別の数字が印刷されている」事故が起きる。
      ・answer が「A:B」型 → av は R(A,B) と順序込みで一致すること（2:3 と 3:2 を区別）
      ・それ以外 → av に現れる整数がすべて answer の中に出てくること
    """
    import sympy as _sp
    bad, checked = [], 0
    for area, u, q in ALL:
        if "av" not in q:
            continue   # 証明問題(proof=True)は「答えの値」を持たないので対象外
        checked += 1
        ans, av = q["answer"], q["av"]
        ratios = re.findall(r"(\d+)\s*:\s*(\d+)", ans)
        if ratios:
            a, b = ratios[-1]
            if not _eq_safe(av, _sp.Rational(int(a), int(b))):
                bad.append(f'{u["name"]}／answer「{ans}」の比 {a}:{b} と av={av} が不一致')
            continue
        if isinstance(av, str):          # 「外接する」「400」など、答えの語そのもの
            if av not in ans:
                bad.append(f'{u["name"]}／av「{av}」が answer「{ans}」に無い')
            continue
        if isinstance(av, dict):
            # 素因数分解 {2:3, 3:2, 5:1}。指数1は $5$ のように省略して印刷するので除く
            need = set(av) | {e for e in av.values() if e > 1}
            miss = [n for n in need if str(n) not in ans]
            if miss:
                bad.append(f'{u["name"]}／av={av} の {miss} が answer「{ans}」に無い')
            continue
        # ★記号(√・文字式)を含むかの判定を、リスト分岐より【先】に行う。
        #   後ろに置くと [3/4-sqrt(17)/4, ...] のようなリストが数字照合に回って誤検出する。
        if _has_symbolic(av):
            if not _latex_matches(ans, av):
                bad.append(f'{u["name"]}／av={av} と answer「{ans}」が数式として一致しない')
            continue
        if isinstance(av, (list, tuple)):
            # 余りの分類 [0,1,2] のように、0 は「$3k$」と書かれ数字が出ない
            miss = [n for n in av if n not in (0,) and str(n) not in ans]
            if miss:
                bad.append(f'{u["name"]}／av={av} の {miss} が answer「{ans}」に無い')
            continue
        # ★√ や文字式を含む av は「数字が answer に出るか」では判定できない
        #   （sqrt(3)+sqrt(5) の内部表現に 8/2/15 等の数が現れて誤検出する）。
        #   answer の LaTeX から数式を取り出して sympy で同値判定する。
        try:
            av_txt = str(_sp.nsimplify(av))
        except Exception:
            av_txt = str(av)
        nums = {abs(int(n)) for n in re.findall(r"-?\d+", av_txt)}
        digits_in_ans = set(re.findall(r"\d+", ans))
        missing = [n for n in nums if str(n) not in ans and str(n) not in digits_in_ans]
        if missing:
            bad.append(f'{u["name"]}／av={av} の数 {missing} が answer「{ans}」に無い')
    for b in bad:
        g._fail(f"[答えとav] {b}")
    if not bad:
        g._ok(f"[答えとav] {checked}問 印刷される答えと検算値が一致 OK")


def _has_symbolic(av):
    """av に √ や文字式が含まれるか（含むなら「数字が出るか」では照合できない）。"""
    import sympy as _sp
    for v in (av if isinstance(av, (list, tuple)) else [av]):
        try:
            e = _sp.sympify(v)
        except Exception:
            return True
        if e.free_symbols or not e.is_Rational:
            return True
    return False


def _tokens_from_av(av):
    """av から「整数の集合」と「使われている関数名」を取り出す。"""
    import sympy as _sp
    ints, funcs = set(), set()
    for v in (av if isinstance(av, (list, tuple)) else [av]):
        e = _sp.sympify(v)
        txt = _sp.srepr(e)
        # srepr は符号を Mul(Integer(-1), ...) で表すので、1 は答えに現れない内部表現。
        # 0 も同様に構造由来のことがあるため除外する。
        ints |= {abs(int(n)) for n in re.findall(r"Integer\((-?\d+)\)", txt)
                 if abs(int(n)) > 1}
        for f in ("sqrt", "Pow(Integer(2), Rational(1, 2))", "pi", "sin", "cos", "tan"):
            if f in txt.lower():
                funcs.add(f.split("(")[0])
        if "Rational(1, 2))" in txt:
            funcs.add("sqrt")
    return ints, funcs


def _tokens_from_answer(ans):
    """answer の LaTeX から「整数の集合」と「関数名」を取り出す。"""
    ints = {abs(int(n)) for n in re.findall(r"-?\d+", ans) if abs(int(n)) > 1}
    funcs = set()
    if "sqrt" in ans:
        funcs.add("sqrt")
    for f in ("pi", "sin", "cos", "tan"):
        if "\\" + f in ans:
            funcs.add(f)
    return ints, funcs


def _latex_matches(ans, av):
    """★√や文字式を含む答えは、LaTeXを厳密にパースするより
    「答えに現れる整数の集合」と「関数（sqrt/pi/sin…）の有無」で照合するほうが頑健。
    数字を1つでも書き換えれば集合が変わるので、誤植は捕まる。"""
    ai, af = _tokens_from_av(av)
    bi, bf = _tokens_from_answer(ans)
    # av の整数がすべて answer に出ていること（answer 側の余分な数＝係数表記等は許す）
    if not ai <= bi:
        return False
    if "sqrt" in af and "sqrt" not in bf:
        return False
    return True


def _eq_safe(a, b):
    import sympy as _sp
    try:
        return _sp.simplify(_sp.nsimplify(a) - _sp.nsimplify(b)) == 0
    except Exception:
        return False


def _points_texts():
    """「この単元のキモ」(POINTS) の本文。★ゲートが問題(ALL)しか見ておらず、
    POINTS の数式内に日本語が入っていても素通りしていた（実際に3件すり抜けた）。"""
    import importlib
    name = MOD.replace("content_", "explanations_")
    try:
        E = importlib.import_module(name)
    except ModuleNotFoundError:
        return []
    return [(f"POINTS[{k}]", v) for k, v in getattr(E, "POINTS", {}).items()]


def check_figure_leak():
    """★図の中に「答えそのもの」が書かれていないか。
    数Aの2円の図（d=r₁+r₂ と明記）でやらかし、数Iの二次不等式・箱ひげ図・暗記三角形で
    再発させた。図は形と位置関係を示すもので、読めば答えが出る数値は問題編に置かない。
    判定: 図中の文字列が answer / av の数値と一致したら FAIL。"""
    import importlib
    name = MOD.replace("content_", "figs_")
    try:
        figs = importlib.import_module(name)
    except ModuleNotFoundError:
        g._ok("[図の漏洩] 図モジュールなし（対象外）")
        return
    figs.attach(C.PARTS)
    bad, n = [], 0
    for area, u, q in ALL:
        svg = q.get("figure")
        if not svg:
            continue
        n += 1
        texts = {t.strip() for t in re.findall(r">([^<>]+)</text>", svg)}
        nums = {t for t in texts if re.fullmatch(r"-?\d+(\.\d+)?", t)}
        ans_nums = set(re.findall(r"-?\d+", q.get("answer", "")))
        hit = {t for t in nums if t.lstrip("-") in ans_nums or t in ans_nums}
        if hit:
            bad.append(f'{u["name"]}／図に {sorted(hit)} ＝ answer「{q["answer"][:22]}」の数値')
    for b_ in bad:
        g._fail(f"[図の漏洩] {b_}")
    if not bad:
        g._ok(f"[図の漏洩] 図{n}枚 answer の数値が図に書かれていない OK")


def check_latex():
    bad_dollar, bad_jp, empty = [], [], []
    for where, s in _points_texts():
        if s.count("$") % 2 != 0:
            bad_dollar.append(f'{where}／$が{s.count("$")}個（奇数）')
        for m in re.findall(r"\$(.+?)\$", s):
            if JP.search(m):
                bad_jp.append(f'{where}／「{m[:20]}」')
    for area, u, q in ALL:
        for field in ("stem", "answer", "explanation"):
            s = q.get(field, "")
            if field in ("stem", "answer") and not s.strip():
                empty.append(f'{u["name"]}／{field}が空')
            if s.count("$") % 2 != 0:
                bad_dollar.append(f'{u["name"]}／{field}／$が{s.count("$")}個（奇数）')
            # $...$ の中身に日本語が入っていないか
            for m in re.findall(r"\$(.+?)\$", s):
                if JP.search(m):
                    bad_jp.append(f'{u["name"]}／{field}／「{m[:20]}」')
    for b in bad_dollar:
        g._fail(f"[LaTeX] $ の対応が取れていない: {b}")
    for b in bad_jp:
        g._fail(f"[LaTeX] $...$ の中に日本語が入っている（KaTeXが崩れる）: {b}")
    for b in empty:
        g._fail(f"[内容] {b}")
    if not (bad_dollar or bad_jp or empty):
        g._ok(f"[LaTeX] 全{len(ALL)}問＋POINTS{len(_points_texts())}件 $の対応OK／数式内に日本語なし")


def check_dup_and_meta():
    seen = {}
    dups = []
    for area, u, q in ALL:
        s = re.sub(r"\s+", "", q["stem"])
        if s in seen:
            dups.append(f'{u["name"]} ≒ {seen[s]}')
        seen[s] = u["name"]
        if q.get("level") not in LEVELS:
            g._fail(f'[メタ] level が想定外: {q.get("level")!r}（{u["name"]}）')
        if not q.get("group"):
            g._fail(f'[メタ] group が空（{u["name"]}）')
        if not q.get("explanation", "").strip():
            g._fail(f'[メタ] explanation が空（{u["name"]}／{q["stem"][:20]}）')
    if dups:
        g._fail("[重複] 同じ問題が複数ある: " + "／".join(dups))
    else:
        g._ok(f"[重複] 全{len(ALL)}問 stem の重複なし／level・group・explanation すべて埋まっている")


def check_choice_bias():
    """(ア)(イ)(ウ)(エ) 型の選択肢問題で、正解が特定の記号に偏っていないか。"""
    from collections import Counter
    KANA = "アイウエオ"
    pos = Counter()
    n = 0
    for area, u, q in ALL:
        if not re.search(r"\(ア\)", q["stem"]):
            continue
        n += 1
        hit = re.findall(r"\((ア|イ|ウ|エ|オ)\)", q.get("answer", ""))
        for h in set(hit):
            pos[h] += 1
    if n < 4:
        g._ok(f"[選択肢] 記号選択{n}問＝判定に必要な4問未満のためスキップ")
        return
    top = max(pos.values()) if pos else 0
    dist = "／".join(f"{k}:{pos.get(k,0)}" for k in KANA[:4])
    if top > n * 0.5:
        g._fail(f"[選択肢] 記号選択{n}問で正解が偏っている: {dist}")
    else:
        g._ok(f"[選択肢] 記号選択{n}問 正解分布 {dist} OK")


def check_balance():
    from collections import Counter
    lv = Counter(q["level"] for _, _, q in ALL)
    per_part = {p["area"]: sum(len(u["problems"]) for u in p["units"]) for p in C.PARTS}
    g._ok(f"[構成] 編ごとの問題数 {per_part}")
    g._ok(f"[構成] 難易度 基礎{lv['basic']}／標準{lv['standard']}／発展{lv['advanced']}")
    if lv["basic"] < len(ALL) * 0.3:
        g._fail(f"[構成] 基礎徹底をうたうのに basic が{lv['basic']}/{len(ALL)}問しかない")
    for p in C.PARTS:
        for u in p["units"]:
            if len(u["problems"]) < 6:
                g._warn(f'[構成] 単元「{u["name"]}」が{len(u["problems"])}問と少ない')


# ---------------------------------------------------------------- 実行
def main():
    print(f"=== 基礎徹底問題集 機械ゲート（{MOD}）===")
    print("[A] sympy による独立再計算")
    check_sympy()
    print("[B] 汎用ゲート")
    g.glyphs([[{k: v for k, v in q.items() if k != "chk"} for _, _, q in ALL],
              [{"area": p["area"], "sub": p["sub"]} for p in C.PARTS]])
    print("[C] 数学固有")
    check_answer_matches_av()
    check_figure_leak()
    check_latex()
    check_dup_and_meta()
    check_choice_bias()
    check_balance()
    g.report()


if __name__ == "__main__":
    if MOD:
        main()                       # 指定された1冊だけ
    else:
        # ★1プロセスで2冊読むと content_* が sys.modules に残って**2冊目が1冊目を掴む**
        #   （この問題集群で実際に踏んだ罠）。1冊1プロセスで回す。
        import subprocess
        rc, ok = 0, 0
        for m in DEFAULT_MODS:
            print(f"\n########## {m} ##########", flush=True)   # ★パイプでも順序が崩れないように
            code = subprocess.run([sys.executable, __file__, m]).returncode
            rc |= code
            ok += (code == 0)
        # ★「検査した本 4 冊」と固定で出すと、import できずに落ちた本があっても 4 冊と嘘をつく。
        #   実際に通った数を出す（verify.py と同じ形にそろえる）。
        print(f"\n########## 検査した本 {ok}/{len(DEFAULT_MODS)} 冊 ##########")
        if ok == 0:
            print("  × 1冊も検査できていない")
            sys.exit(1)
        sys.exit(rc)
