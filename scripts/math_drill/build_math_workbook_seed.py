#!/usr/bin/env python3
"""📐 高校数学ドリル 第2弾: 塾の問題集 8 冊 (基礎徹底 数I・数II・数A・数III系 / 問題演習テキスト IA・IIB・IA第2集・IIB第2集) を
4 択の単元ドリルのシード seed-data/math_drill_workbook_v1.json にする (2026-10-06 塾長「1→2でやって」の ②)。

素材: scripts/math_workbook/content_*.py (問題・答え・解説・答えの値 av) を extract_workbook_items.py で取り出す
  (診断用の 2 冊・証明・図が要る問題は入れない。理由は extract の docstring)。
選択肢: 元は記述式なので、誤答 3 つを書き足した data/workbook_choices.json (id と元の問題文のハッシュで結ぶ) を使う。
  誤答は典型的な誤り (符号・係数の落とし・公式の取り違え・境界) から作り、複数の値の答えは 2×2、数値は正解の順位を散らす。
検査 (ここで落ちたら書き出さない):
  - 問題文と答えのハッシュが元と一致 (stem_hash / answer_hash。元の問題や答えが変わったら選択肢を作り直す)
  - sympy: 正解の選択肢の値 == 元の答えの値 av (av があるとき)、誤答の値 != av、4 つの値が互いに違う
    (直線・円の式は定数倍、1 変数の不等式は解の集合で比べる。av があるのに照合できないものは AV_SHAPE_CHECKED に理由つきで足す)
  - 形式 (4 つ相異・$ を使わない・\\( \\) の数・図への言及なし) は scripts/check_math_drill_seed.py と同じ観点
解説: 元の解説 + 【よくある誤り】(誤答ごとに「どの誤りでその値になるか」)。表示位置は単元ごとに巡回で散らす。
★盲検 3 名の全員一致だけを採る。直すものは下の DROP / OVERRIDES に理由つきで書く (生の解答はコミットしない)。
★本番に入った後で外した問題は _meta.retired_sources に載せる (CEO の補充ボタンが同期 API で active=0 にする)。
★直したら builder を回してシードもコミットする (scripts/math_drill/check_workbook_seed_fresh.py が組み直しと突き合わせる)。
使い方:
  python3 scripts/math_drill/build_math_workbook_seed.py            # seed-data/math_drill_workbook_v1.json
  python3 scripts/math_drill/build_math_workbook_seed.py --blind DIR  # 盲検用 (答え・解説なし) と正解表
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CHOICES = os.path.join(HERE, "data", "workbook_choices.json")
OUT = os.path.join(REPO, "seed-data", "math_drill_workbook_v1.json")
LEVELS = {"basic", "standard", "advanced"}

# 元の答えの値 av の形が選択肢の値と違うので sympy で照合できないもの (解の組を list・不等式を境界値・n進法を文字列・
#   素因数分解を dict・不定方程式を係数の組で持っている)。2026-10-06 に 28 問とも正解の選択肢が公式の答えと同じ文であることを目で確認した。
AV_SHAPE_CHECKED = set("""kI:2:4 kI:2:5 kI:2:6 kI:2:7 kI:5:1 kI:5:2 kI:5:5 kI:5:6 kI:5:7 kII:1:7 kII:2:8 kII:3:4 kII:3:8
    kA:1:8 kA:3:6 kA:5:7 kA:6:1 kA:7:4 kA:7:6 kA:7:7 kA:8:1 kA:8:2 kA:8:3 kA:9:3 kA:9:4 kA:9:5 kIII:4:3 kIII:4:5""".split())
# 答えが文・語なので値で比べられないもの (av は反例の値や語)。2026-10-06 に正解の選択肢が公式の答えと同じことを目で確認した:
#   kI:3:4 逆「x²=4 ⇒ x=2」は偽 (反例 −2) / kA:4:5 7+3=10 で外接 / kA:4:6 6−2=4 で内接
AV_SHAPE_CHECKED |= {"kI:3:4", "kA:4:5", "kA:4:6"}
# 2 冊に同じ問題がある組 (2026-10-06 コミット前レビュー。言い回しだけ違う 23 組)。問題演習テキスト側を外す
#   原則 問題演習テキスト側を外す (kIII:1:3 だけは中身が数学II の計算なので、基礎徹底側を外して 数学II 複素数と方程式 の iib:2:1 を残す)。
#   ★45f53ec で本番に入った分は _meta.retired_sources に載せ、CEO の補充ボタンが同期で active=0 にする (生徒に出さない)
SAME_AS = {   # {外す id: 残す id}
    "iib:4:1": "kII:1:1",
    "iib2:4:1": "kII:1:2",
    "iib2:4:3": "kII:1:4",
    "iib:4:6": "kII:2:3",
    "iib:4:8": "kII:2:5",
    "iib:4:12": "kII:2:8",
    "iib:5:1": "kII:3:2",
    "iib:5:10": "kII:3:7",
    "iib:5:4": "kII:4:1",
    "iib:5:8": "kII:4:7",
    "iib:6:5": "kII:5:6",
    "iib:7:7": "kII:6:7",
    "iib:7:8": "kII:6:8",
    "ia:1:2": "kI:1:1",
    "ia:1:1": "kI:1:2",
    "ia:3:7": "kI:5:1",
    "ia:3:13": "kI:5:7",
    "ia:4:6": "kI:7:3",
    "ia:4:9": "kI:7:6",
    "ia:8:2": "kA:1:4",
    "iib:10:10": "kIII:4:3",
    "kIII:1:3": "iib:2:1",
    "ia:7:11": "kIII:3:1",
    "ia:9:6": "kA:7:4",     # 2 回目のレビューで見つかった (k と t の違いだけ)
}
DROP = {i: f"{k} と同じ問題 (言い回しだけ違う)" for i, k in SAME_AS.items()}   # {id: 理由}
DROP["iib:6:6"] = "kII:5:7 (極大値) と kII:5:8 (極小値) を 1 問にしたもの (同じ関数 y=x³−3x)"
OVERRIDES = {}   # {id: {"stem": ..., "choices": [...], "answer_index": n, "sympy": [...], "notes": [...]}}
# ↑ 2026-10-06 の盲検・照合で直した問題文・選択肢・注記は data/workbook_choices.json の行を直接直し、"fix" に理由を書いた (27 問)。

# 単元の付け替え (問題集の章立てと新課程・入試道場の単元がずれるもの。2026-10-06 照合レビュー)
_CUBIC = "3 次の展開・因数分解・対称式は新課程 (2022〜) では数学II 式と証明"
_COORD = "座標で重心・外心・垂心を求めるのは数学II 図形と方程式 (同じ型の iib2:3:3 もそこ)"
_REMAINDER = "剰余の定理は新課程の教科書では数学II「複素数と方程式」の章 (同じ型の iib:2:11 もそこ)"
_SETCOUNT = "集合の要素の個数 (n(A∪B) の公式) は新課程では数学A 場合の数と確率"
UNIT_FIX = {
    "ia:1:17": ("数学II 式と証明", _CUBIC), "ia2:1:1": ("数学II 式と証明", _CUBIC), "ia2:1:2": ("数学II 式と証明", _CUBIC),
    "ia2:1:4": ("数学II 式と証明", _CUBIC), "ia2:1:11": ("数学II 式と証明", _CUBIC),
    "kA:1:8": ("数学II 図形と方程式", _COORD), "ia2:8:1": ("数学II 図形と方程式", _COORD),
    "ia2:8:10": ("数学II 図形と方程式", _COORD), "ia2:8:11": ("数学II 図形と方程式", _COORD),
    "ia:2:1": ("基礎数学 整数", "約数の個数で、集合も命題も使わない (問題集では集合と命題の章にある)"),
    "iib:9:11": ("数学II 図形と方程式", _COORD),
    "kIII:1:4": ("数学II 複素数と方程式", "複素数の四則計算は数学II (数学C 複素数平面 は図形との対応から)"),
    # 2 回目のレビュー: 剰余の定理は新課程の教科書で「複素数と方程式」(高次方程式) の章。集合の要素の個数 (包除) は数学A 場合の数と確率
    #   (期待値は新課程で数学A に戻ったので 基礎数学 確率 のまま。確率変数 E(X) の記法の kIII:3:1 は数学B)
    "iib:1:6": ("数学II 複素数と方程式", _REMAINDER), "iib2:1:7": ("数学II 複素数と方程式", _REMAINDER),
    "kI:3:3": ("基礎数学 確率", _SETCOUNT), "ia:2:2": ("基礎数学 確率", _SETCOUNT), "ia:2:3": ("基礎数学 確率", _SETCOUNT),
    "ia2:2:3": ("基礎数学 確率", _SETCOUNT), "ia2:2:6": ("基礎数学 確率", _SETCOUNT),
}
# 解説の書き換え (old → new。old が無ければ止める)。選択肢に (ア)〜(エ) は無く並びも変わるので記号で指さない・前後の問を指さない
EXPL_FIX = {
    "kA:2:1": [("(イ)は内心、(ウ)は重心、(エ)は垂心。", "3つの内角の二等分線の交点は内心、3本の中線の交点は重心、3本の垂線の交点は垂心。")],
    "kA:3:9": [("(ア)はとなり合う角なので不適。", "\\(\\angle A+\\angle B=180^\\circ\\) はとなり合う角の和なので不適。")],
    "kA:8:4": [("次の問と見比べること。", "")],
    "kIII:3:3": [("分散はちがう（下の問）。", "分散は \\(V(aX+b)=a^2V(X)\\) となり、ここがちがう。")],
    "iib:10:2": [("\\(E(X^2)=", "\\(E(X)=1\\cdot\\dfrac{1}{2}+2\\cdot\\dfrac{1}{3}+3\\cdot\\dfrac{1}{6}=\\dfrac{5}{3}\\)。\\(E(X^2)=")],
    "kA:2:9": [("三角形の五心は", "各頂点を通り対辺（またはその延長）と直交する直線は、頂点から対辺に下ろした垂線。3本の垂線の交点を垂心という。三角形の五心は")],
    # 数学II 図形と方程式 に移したので、ベクトル (数学C) を使わず傾きで解く
    "ia2:8:11": [("\\(\\overrightarrow{BC}=(-3,\\ 3)\\) に垂直で \\(A\\) を通るから \\(-3x+3y=0\\)、すなわち \\(y=x\\)。",
                  "直線 \\(BC\\) の傾きは \\(\\dfrac{3-0}{1-4}=-1\\) だから、これに垂直な直線の傾きは \\(1\\)。\\(A\\) を通るから \\(y=x\\)。"),
                 ("\\(\\overrightarrow{AC}=(1,\\ 3)\\) に垂直で \\(B(4,0)\\) を通るから \\(1\\cdot(x-4)+3\\cdot y=0\\)、すなわち \\(x+3y=4\\)。",
                  "直線 \\(CA\\) の傾きは \\(\\dfrac{3-0}{1-0}=3\\) だから、これに垂直な直線の傾きは \\(-\\dfrac{1}{3}\\)。\\(B(4,\\ 0)\\) を通るから \\(y=-\\dfrac{1}{3}(x-4)\\)、すなわち \\(x+3y=4\\)。")],
    "ia2:8:5": [("接線と弦 \\(AB\\) のなす角は", "\\(\\angle SAB\\) は"), ("接線と弦 \\(AC\\) のなす角は", "\\(\\angle TAC\\) は"),
                ("接点 \\(A\\) を通る接線は一直線だから、接線上で", "\\(S,\\ A,\\ T\\) は一直線上にあるから")],
}

problems = []
_spec = importlib.util.spec_from_file_location("extract_workbook_items", os.path.join(HERE, "extract_workbook_items.py"))
EX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EX)


# ───────── sympy で値を比べる ─────────
def sym_env():
    import sympy as sp
    names = "x y z a b c d k m n p q r s t theta alpha beta"
    env = {k: getattr(sp, k) for k in ("sqrt", "pi", "Rational", "I", "oo", "E", "log", "sin", "cos", "tan", "exp", "Abs",
                                       "Interval", "Union", "FiniteSet", "Tuple", "S", "Integer", "Float", "binomial", "factorial",
                                       "asin", "acos", "atan", "EmptySet", "Eq", "Matrix")}
    for nm in names.split():
        env[nm] = sp.Symbol(nm, real=True)
    return sp, env


def to_sym(expr, sp, env):
    if expr is None or str(expr).strip() == "":
        return None
    try:
        v = eval(str(expr), {"__builtins__": {}}, env)
    except Exception:
        try:
            v = sp.sympify(str(expr), locals=env)
        except Exception:
            return "ERR"
    if isinstance(v, set):
        v = sp.FiniteSet(*v)
    elif isinstance(v, (tuple, list)):
        v = sp.Tuple(*v)
    elif isinstance(v, (int, float)):
        v = sp.nsimplify(v) if isinstance(v, float) else sp.Integer(v)
    return v


def _rel_same(u, v, sp):
    """等式・不等式どうしが同じ条件か。等式は (左辺−右辺) が定数倍で一致すれば同じ (y=2x+1 と 2x−y+1=0)。
    1 変数の不等式は実数の解の集合で比べる。比べられなければ None。"""
    if isinstance(u, sp.Equality) and isinstance(v, sp.Equality):
        du, dv = sp.expand(u.lhs - u.rhs), sp.expand(v.lhs - v.rhs)
        if du == 0 or dv == 0:
            return du == dv
        ratio = sp.simplify(du / dv)
        return bool(ratio.is_number and ratio != 0)
    if isinstance(u, sp.core.relational.Relational) and isinstance(v, sp.core.relational.Relational):
        syms = (u.free_symbols | v.free_symbols)
        if len(syms) == 1:
            x = next(iter(syms))
            return sp.solveset(u, x, sp.S.Reals) == sp.solveset(v, x, sp.S.Reals)
    return None


def same(u, v, sp):
    try:
        if u == v:
            return True
        r = _rel_same(u, v, sp)
        if r is not None:
            return r
        if isinstance(u, sp.Tuple) and isinstance(v, sp.Tuple):
            return len(u) == len(v) and all(same(a, b, sp) for a, b in zip(u, v))
        if isinstance(u, sp.Expr) and isinstance(v, sp.Expr):
            d = sp.simplify(sp.expand(u - v))
            if d == 0:
                return True
            if not d.free_symbols:
                return abs(complex(sp.N(d))) < 1e-9
            return False
        if isinstance(u, sp.Set) and isinstance(v, sp.Set):
            return sp.simplify(u.symmetric_difference(v)) == sp.EmptySet
    except Exception:
        return False
    return False


# ───────── 組み立て ─────────
def build():
    ex = EX.extract()   # ファイルを書かない・抽出の問題 (章の対応漏れ・$ の数・図への言及) もここに積む
    problems.extend(f"抽出: {p_}" for p_ in ex["problems"])
    items = ex["items"]
    authored = json.load(open(CHOICES, encoding="utf-8"))
    sp, env = sym_env()
    qs = []
    for it in items:
        a = authored.get(it["id"])
        if a is None:
            problems.append(f"{it['id']}: 選択肢が無い (data/workbook_choices.json)"); continue
        if a.get("stem_hash") != it["stem_hash"]:
            problems.append(f"{it['id']}: 元の問題文が変わった (stem_hash) → 選択肢を作り直す"); continue
        if a.get("answer_hash") != it["answer_hash"]:
            # 解説は問題集から、正解の選択肢は workbook_choices.json から来るので、答えだけ直すと両者が食い違う
            problems.append(f"{it['id']}: 元の答えが変わった (answer_hash) → 正解の選択肢と誤答を作り直す"); continue
        if a.get("drop") or it["id"] in DROP:
            continue
        a = {**a, **OVERRIDES.get(it["id"], {})}
        ch, ai, sy, notes = list(a["choices"]), int(a["answer_index"]), list(a.get("sympy") or ["", "", "", ""]), list(a.get("notes") or ["", "", "", ""])
        src = f"mathwb-{it['id']}"
        if len(ch) != 4 or len(set(c.strip() for c in ch)) != 4 or not (0 <= ai <= 3):
            problems.append(f"{src}: 選択肢 {ch} / answer {ai}"); continue
        # sympy の照合 (照合できないまま黙って通さない: 式が 4 つ無い・av があるのに比べられないのは止める)
        if len(sy) != 4:
            problems.append(f"{src}: sympy の式が 4 つでない {sy}"); continue
        vals = [to_sym(e, sp, env) for e in sy]
        if any(v == "ERR" for v in vals):
            problems.append(f"{src}: sympy の式が読めない {sy}")
        else:
            av = to_sym(it["av"], sp, env) if (it.get("av") and it["id"] not in AV_SHAPE_CHECKED) else None
            if it.get("av") and it["id"] not in AV_SHAPE_CHECKED and (av == "ERR" or vals[ai] is None):
                problems.append(f"{src}: 元の答えの値 av があるのに正解と照合できない (sympy を書くか AV_SHAPE_CHECKED に理由つきで足す)")
            if av not in (None, "ERR") and vals[ai] is not None and not same(vals[ai], av, sp):
                problems.append(f"{src}: 正解の値 {sy[ai]} が元の答え {it['av']} と違う")
            for i in range(4):
                for j in range(i + 1, 4):
                    if vals[i] is not None and vals[j] is not None and same(vals[i], vals[j], sp):
                        problems.append(f"{src}: 選択肢 {ch[i]!r} と {ch[j]!r} が同じ値")
            if av not in (None, "ERR"):
                for i, v in enumerate(vals):
                    if i != ai and v is not None and same(v, av, sp):
                        problems.append(f"{src}: 誤答 {ch[i]!r} が正解と同じ値")
        expl = it["explanation"]
        for old, new in EXPL_FIX.get(it["id"], []):
            if old not in expl:
                problems.append(f"{src}: EXPL_FIX の {old!r} が解説に無い")
            expl = expl.replace(old, new)
        stem = a["stem"]
        # 作図の手順などの「①②③」は、ドリルでは選択肢の番号と紛れるので (1)(2)(3) にする
        circ = {c: f"({n})" for n, c in enumerate("①②③④⑤⑥⑦⑧⑨", 1)}
        stem = "".join(circ.get(c, c) for c in stem)
        expl = "".join(circ.get(c, c) for c in expl)
        wrong = [f"{ch[i]}：{notes[i]}" for i in range(4) if i != ai and str(notes[i]).strip()]
        if wrong:
            expl += "\n【よくある誤り】" + " ／ ".join(wrong)
        qs.append({"subject": "math", "unit": UNIT_FIX.get(it["id"], (it["unit"],))[0], "level": it["level"] if it["level"] in LEVELS else "standard",
                   "stem": stem, "choices": ch, "answer": ai, "explanation": expl, "source": src})
    ids = {it["id"] for it in items}
    for i in sorted((set(UNIT_FIX) | set(EXPL_FIX)) - ids):
        problems.append(f"{i}: UNIT_FIX / EXPL_FIX の id が問題集に無い")
    # 表示位置を単元ごとに 4 位置へ順に配る (巡回なので並びの順は保つ)
    counter = collections.Counter()
    for q in sorted(qs, key=lambda x: (x["unit"], x["source"])):
        t = counter[q["unit"]] % 4
        counter[q["unit"]] += 1
        r = (t - q["answer"]) % 4
        q["choices"] = [q["choices"][(i - r) % 4] for i in range(4)]
        q["answer"] = t
    return qs


def validate(qs):
    seen = {}
    for q in qs:
        src = q["source"]
        for part, t in [("stem", q["stem"]), ("explanation", q["explanation"])] + [(f"c{i}", c) for i, c in enumerate(q["choices"])]:
            if "$" in t:
                problems.append(f"{src}: {part} に $")
            if t.count("\\(") != t.count("\\)"):
                problems.append(f"{src}: {part} の \\( \\) の数が合わない")
        if EX.FIGURE_REF.search(q["stem"]):
            problems.append(f"{src}: stem に図への言及")
        k = q["stem"].strip()
        if k in seen:
            problems.append(f"{src}: stem が {seen[k]} と重複")
        seen[k] = src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    qs = build()
    validate(qs)
    by = collections.Counter(q["unit"] for q in qs)
    print("問題数:", len(qs))
    for u, n in sorted(by.items()):
        print(f"  {u}: {n}")
    if problems:
        print(f"\n❌ 検査 NG {len(problems)} 件 (書き出しません):")
        for p in problems[:120]:
            print("  -", p)
        sys.exit(1)
    if a.blind:
        os.makedirs(a.blind, exist_ok=True)
        blind = [{"id": "W-" + hashlib.sha1((q["stem"] + "|".join(q["choices"])).encode()).hexdigest()[:10], "unit": q["unit"],
                  "stem": q["stem"], "choices": q["choices"]} for q in qs]
        assert len({b["id"] for b in blind}) == len(blind)
        key = {b["id"]: {"answer": q["choices"][q["answer"]], "source": q["source"]} for b, q in zip(blind, qs)}
        json.dump(blind, open(os.path.join(a.blind, "blind_math_wb.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(key, open(os.path.join(a.blind, "key_math_wb.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"盲検用: {a.blind} ({len(blind)} 問)")
        return
    meta = {"name": "math_drill_workbook_v1", "created": CREATED, "subject": "math", "units": dict(sorted(by.items())),
            # 45f53ec で本番に入ったあと外した問題の source。CEO の補充ボタンが同期 (/api/admin/grammar/sync) で active=0 にする
            "retired_sources": retired_sources(),
            "sources": ["scripts/math_workbook/content_kisoI・kisoII・kisoA・kisoIII (基礎徹底問題集 4 冊)",
                        "scripts/math_workbook/content_ia・iib・ia_v2・iib_v2 (問題演習テキスト IA・IIB・第2集)"],
            "blind_review": BLIND_NOTE,
            "note": "全部この塾のオリジナル。記述式の問題に典型的な誤りの誤答 3 つを足した 4 択。数式は \\( \\) の LaTeX。単元名は入試道場の topic と同じ (数学II 複素数と方程式 だけは道場に無い)。level は元の 基礎/標準/発展。"}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": meta, "questions": qs}, ensure_ascii=False, indent=1) + "\n")
    print("✅", a.out, len(qs), "問")


def retired_sources():
    return sorted(f"mathwb-{i}" for i in DROP)


CREATED = "2026-10-06"   # 作り直しても変えない (鮮度ゲートが組み直した結果とシードを突き合わせる)
BLIND_NOTE = ("盲検 (2026-10-06): 3 名 × 675 問で全員一致・元の問題集との照合 10 名・コミット前レビュー 2 回。直した問題は workbook_choices.json の fix。"
              "問題文・選択肢を変えた 24 問は盲検をやり直して全員一致。誤答の注記 1,935 件は書き手と別の確かめ役で総点検。2 冊の重複など 25 問は外した (retired_sources)")

if __name__ == "__main__":
    main()
