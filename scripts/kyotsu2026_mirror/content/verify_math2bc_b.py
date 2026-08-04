# -*- coding: utf-8 -*-
"""verify_math2bc_b.py — math2bc_b.py の全マークスロットを独立に導出して assert する。

方針: 問題モジュールの答え (ANS_SECTIONS の slots) は「主張」であり，本スクリプトは
それを一切参照せずに sympy / 全数列挙 / 図カタログの条件判定で真の値を求め，
最後に一致を確認する。実行して "ALL VERIFY PASS" が出れば全 pass。
"""
import importlib.util, os
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("mod", os.path.join(HERE, "math2bc_b.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
CLAIM = {s["section"]: s["slots"] for s in mod.ANS_SECTIONS}

CIRC = "⓪①②③④⑤⑥⑦⑧⑨"  # ⓪①..⑨
def circ(i): return CIRC[i]

fails = []
def check(sec, key, expected, note=""):
    got = CLAIM[sec].get(key)
    ok = (got == expected)
    print(f"[{'OK ' if ok else 'NG '}] Q{sec} {key}: derived={expected!r} claim={got!r}  {note}")
    if not ok:
        fails.append((sec, key, expected, got))


# =====================================================================
#  Q3: differentiation / integration
# =====================================================================
x, k = sp.symbols("x k", real=True)
f = sp.Rational(5, 3) * x**3 - 10 * x**2 + 15 * x + k
fp = sp.diff(f, x)
print("f =", f)
print("f' =", sp.expand(fp), "=", sp.factor(fp))

# --- (1)(i) A: f'(x) from 6 choices ---
grpA = [
    sp.Rational(5, 3) * x**2 - 10 * x + 15 + k,
    sp.Rational(5, 3) * x**2 - 10 * x + 15,
    5 * x**2 - 20 * x + 15,
    5 * x**2 - 20 * x + 15 + k,
    sp.Rational(5, 12) * x**4 - sp.Rational(10, 3) * x**3 + sp.Rational(15, 2) * x**2 + k * x,
    sp.Rational(5, 3) * x**4 - 10 * x**3 + 15 * x**2 + k * x,
]
iA = [i for i, e in enumerate(grpA) if sp.simplify(e - fp) == 0]
assert len(iA) == 1, ("A not unique", iA)
check(3, "ア", circ(iA[0]), "f'(x)")

# --- extrema ---
crit = sorted(sp.solve(fp, x))
assert crit == [1, 3]
xmax = [c for c in crit if sp.diff(f, x, 2).subs(x, c) < 0][0]
xmin = [c for c in crit if sp.diff(f, x, 2).subs(x, c) > 0][0]
assert xmax == 1 and xmin == 3
check(3, "イ", str(int(xmax)), "x of max")
check(3, "エ", str(int(xmin)), "x of min")
vmax = sp.simplify(f.subs(x, xmax)); vmin = sp.simplify(f.subs(x, xmin))
print("max val =", vmax, " min val =", vmin)
grpUO = [sp.Integer(0), sp.Integer(1), sp.Integer(2), sp.Rational(5, 3), sp.Rational(20, 3),
         k, -sp.Rational(20, 3) + k, -sp.Rational(5, 3) + k, sp.Rational(5, 3) + k, sp.Rational(20, 3) + k]
iU = [i for i, e in enumerate(grpUO) if sp.simplify(e - vmax) == 0]
iO = [i for i, e in enumerate(grpUO) if sp.simplify(e - vmin) == 0]
assert len(iU) == 1 and len(iO) == 1
check(3, "ウ", circ(iU[0]), "max val 20/3+k")
check(3, "オ", circ(iO[0]), "min val k")

# --- (ii) figure selection Ka, Ki from catalog coefficients ---
def fig6_props(coef):
    a, b, c, d = coef
    xx = sp.symbols("xx", real=True)
    g = a * xx**3 + b * xx**2 + c * xx + d
    gc = sp.solve(sp.diff(g, xx), xx)
    vals = sorted(float(g.subs(xx, r)) for r in gc) if gc else []
    pos = a > 0
    if not vals:
        return dict(pos=pos, kind="mono")
    vmn, vmx = vals[0], vals[-1]
    TOL = 1e-6
    if abs(vmn) < TOL:
        kind = "min_touch"
    elif abs(vmx) < TOL:
        kind = "max_touch"
    elif vmn > 0:
        kind = "both_above"
    else:
        kind = "other"
    return dict(pos=pos, kind=kind)

props6 = [fig6_props(c) for c in mod._FIG6_COEF]
for i, p in enumerate(props6):
    print(f"  fig6 {circ(i)}: {p}")
cand_k0 = [i for i, p in enumerate(props6) if p["pos"] and p["kind"] == "min_touch"]
cand_kp = [i for i, p in enumerate(props6) if p["pos"] and p["kind"] == "both_above"]
assert len(cand_k0) == 1, ("k=0 fig not unique", cand_k0)
assert len(cand_kp) == 1, ("k>0 fig not unique", cand_kp)
check(3, "カ", circ(cand_k0[0]), "k=0 min touches axis")
check(3, "キ", circ(cand_kp[0]), "k>0 both above")

# --- (iii) Ku,Ke: range -20/3 < k < 0 ---
alpha = min(crit)
lo = sp.solve(sp.Eq(f.subs(x, alpha), 0), k)[0]
hi = sp.solve(sp.Eq(f.subs(x, 0), 0), k)[0]
print("range:", lo, "< k <", hi)
grpKK = [sp.Integer(0), sp.Rational(5, 3), sp.Rational(10, 3), sp.Rational(20, 3), sp.Rational(5, 2),
         -sp.Rational(5, 3), -sp.Rational(10, 3), -sp.Rational(20, 3), -sp.Rational(5, 2), -sp.Rational(25, 3)]
iKlo = [i for i, e in enumerate(grpKK) if e == lo]
iKhi = [i for i, e in enumerate(grpKK) if e == hi]
assert len(iKlo) == 1 and len(iKhi) == 1
check(3, "ク", circ(iKlo[0]), "lower -20/3")
check(3, "ケ", circ(iKhi[0]), "upper 0")

# --- Ko: area-equal condition = int_0^alpha f dx = 0 (index1) ---
kv = sp.solve(sp.integrate(f, (x, 0, alpha)), k)[0]
fk = f.subs(k, kv)
nr = [complex(r).real for r in sp.nroots(sp.Poly(fk, x)) if abs(complex(r).imag) < 1e-9]
beta = [r for r in nr if 0 < r < float(alpha)]
assert len(beta) == 1, ("beta not unique", beta, nr)
beta = beta[0]
S1 = -float(sp.integrate(fk, (x, 0, beta)))
S2 = float(sp.integrate(fk, (x, beta, alpha)))
print(f"beta~{beta:.5f}  S1~{S1:.6f}  S2~{S2:.6f}")
assert abs(S1 - S2) < 1e-6, "S1!=S2 at int_0^alpha=0"
check(3, "コ", circ(1), "int_0^alpha f=0")

# --- SaShiSu / SeSo : k = -55/12 ---
print("k =", sp.nsimplify(kv))
num, den = sp.fraction(sp.nsimplify(kv))
num = int(num); den = int(den)
assert num == -55 and den == 12
check(3, "サ", "−"); check(3, "シ", str(abs(num) // 10)); check(3, "ス", str(abs(num) % 10))
check(3, "セ", str(den // 10)); check(3, "ソ", str(den % 10))

# --- (2) 8-figure condition filtering ---
def cond_a(coef):
    a, b, c, d = coef
    xx = sp.symbols("xx", real=True)
    g = a * xx**3 + b * xx**2 + c * xx + d
    return (g.subs(xx, 0) == 0) and (sp.diff(g, xx).subs(xx, 0) > 0)
def cond_b(coef):
    a, b, c, d = coef
    xx = sp.symbols("xx", real=True)
    gp = sp.expand(sp.diff(a * xx**3 + b * xx**2 + c * xx + d, xx))
    return sp.Poly(gp, xx).coeff_monomial(xx) == 0
def cond_c(coef):
    a, b, c, d = coef
    return a > 0

sa = [i for i, c in enumerate(mod._FIG8_COEF) if cond_a(c)]
sb = [i for i in sa if cond_b(mod._FIG8_COEF[i])]
sc = [i for i in sb if cond_c(mod._FIG8_COEF[i])]
print("(a):", [circ(i) for i in sa], " (a)&(b):", [circ(i) for i in sb], " (a)&(b)&(c):", [circ(i) for i in sc])
assert len(sa) == 3 and len(sb) == 2 and len(sc) == 1
assert set(sc) <= set(sb) <= set(sa)
set_tachitsu = set(circ(i) for i in sa)
set_teto = set(circ(i) for i in sb)
claim_tachitsu = set(CLAIM[3][key] for key in ["タ", "チ", "ツ"])
claim_teto = set(CLAIM[3][key] for key in ["テ", "ト"])
print("TaChiTsu claim:", claim_tachitsu, " derived:", set_tachitsu)
print("TeTo claim:", claim_teto, " derived:", set_teto)
if claim_tachitsu != set_tachitsu:
    fails.append((3, "TaChiTsu", set_tachitsu, claim_tachitsu))
else:
    print("[OK ] Q3 TaChiTsu(unordered set) match")
if claim_teto != set_teto:
    fails.append((3, "TeTo", set_teto, claim_teto))
else:
    print("[OK ] Q3 TeTo(unordered set) match")
check(3, "ナ", circ(sc[0]), "(a)(b)(c) unique")


# =====================================================================
#  Q4: sequences (difference sequence)
# =====================================================================
n = sp.symbols("n", integer=True, positive=True)

def bfun(m): return 6 * m - 3
a1 = 4
b1 = bfun(1); a2 = a1 + b1; b2 = bfun(2); a3 = a2 + b2
print("b1,a2,b2,a3 =", b1, a2, b2, a3)
assert (b1, a2, b2, a3) == (3, 7, 9, 16)
check(4, "ア", str(b1)); check(4, "イ", str(a2)); check(4, "ウ", str(b2))
check(4, "エ", str(a3 // 10)); check(4, "オ", str(a3 % 10))

kk = sp.symbols("kk", integer=True, positive=True)
grpKA = [n - 1, n, n + 1, n + 2]
def true_a(N):
    a = a1
    for j in range(1, N):
        a += bfun(j)
    return a
good_up = []
for idx, U in enumerate(grpKA):
    anU = a1 + sp.summation(6 * kk - 3, (kk, 1, U))
    if all(int(anU.subs(n, N)) == true_a(N) for N in range(2, 9)):
        good_up.append(idx)
print("valid sum-upper-limit candidates:", [circ(i) for i in good_up])
assert good_up == [0], good_up
check(4, "カ", circ(0), "upper n-1")

an = sp.expand(a1 + sp.summation(6 * kk - 3, (kk, 1, n - 1)))
print("a_n =", an)
for N in range(1, 9):
    assert int(an.subs(n, N)) == true_a(N), (N, an.subs(n, N), true_a(N))
coeffs = sp.Poly(an, n).all_coeffs()
assert coeffs == [3, -6, 7]
check(4, "キ", str(coeffs[0]))
check(4, "ク", str(-coeffs[1]))
check(4, "ケ", str(coeffs[2]))

# --- (2) Ko,Sa ---
p, q = sp.symbols("p q")
cn = lambda m: (p * m + q) * 2**m
diff = sp.expand(cn(n + 1) - cn(n))
coeff = sp.expand(sp.powsimp(diff / 2**n, force=True))
print("c_{n+1}-c_n / 2^n =", sp.collect(coeff, n))
poly = sp.Poly(sp.collect(coeff, n), n)
c_n = poly.coeff_monomial(n)
c_const = poly.coeff_monomial(1)
print("n coeff =", c_n, " const =", c_const)
grpKS = [p, q, 2 * p, 2 * q, p + q, 2 * p + q, p + 2 * q, 2 * (p + q)]
iKo = [i for i, e in enumerate(grpKS) if sp.simplify(e - c_n) == 0]
iSa = [i for i, e in enumerate(grpKS) if sp.simplify(e - c_const) == 0]
assert len(iKo) == 1 and len(iSa) == 1
check(4, "コ", circ(iKo[0]), "p")
check(4, "サ", circ(iSa[0]), "2p+q")

sol = sp.solve([sp.Eq(c_n, 3), sp.Eq(c_const, -1)], [p, q], dict=True)[0]
pv, qv = sol[p], sol[q]
print("p =", pv, " q =", qv)
assert pv == 3 and qv == -7
check(4, "シ", str(int(pv)))
check(4, "ス", "−"); check(4, "セ", str(abs(int(qv))))

c = lambda m: (pv * m + qv) * 2**m
Sn = sp.simplify(c(n + 1) - c(1))
print("sum d_k =", sp.expand(Sn))
def true_sum2(N): return sum((3 * m - 1) * 2**m for m in range(1, N + 1))
for N in range(1, 9):
    assert int(Sn.subs(n, N)) == true_sum2(N), (N, Sn.subs(n, N), true_sum2(N))
so_coeff = sp.expand(pv * (n + 1) + qv)
print("coeff of 2^{n+1} =", so_coeff)
grpSO = [3 * n - 2, 3 * n - 4, 2 * n - 3, 2 * n - 1, n - 1, n + 1]
iSo = [i for i, e in enumerate(grpSO) if sp.simplify(e - so_coeff) == 0]
assert len(iSo) == 1
check(4, "ソ", circ(iSo[0]), "3n-4")
c1 = c(1); ta = -c1
print("c_1 =", c1, " Ta =", ta)
assert ta == 8
check(4, "タ", str(int(ta)))

# --- (3) Chi,Tsu ---
r, s, t = sp.symbols("r s t")
cq = lambda m: (r * m**2 + s * m + t) * 2**m
diffq = sp.expand(sp.powsimp((cq(n + 1) - cq(n)) / 2**n, force=True))
pq = sp.Poly(sp.collect(diffq, n), n)
solq = sp.solve([sp.Eq(pq.coeff_monomial(n**2), 1),
                 sp.Eq(pq.coeff_monomial(n), -2),
                 sp.Eq(pq.coeff_monomial(1), -2)], [r, s, t], dict=True)[0]
rv, sv, tv = solq[r], solq[s], solq[t]
print("r,s,t =", rv, sv, tv)
assert (rv, sv, tv) == (1, -6, 8)
cqv = lambda m: (rv * m**2 + sv * m + tv) * 2**m
Snq = sp.simplify(cqv(n + 1) - cqv(1))
print("sum d_k =", sp.expand(Snq))
def true_sum3(N): return sum((m**2 - 2 * m - 2) * 2**m for m in range(1, N + 1))
for N in range(1, 9):
    assert int(Snq.subs(n, N)) == true_sum3(N), (N, Snq.subs(n, N), true_sum3(N))
chi_coeff = sp.expand(rv * (n + 1)**2 + sv * (n + 1) + tv)
print("coeff of 2^{n+1} =", chi_coeff)
grpCHI = [3 * n - 3, 3 * n + 3, 2 * n - 3, 2 * n + 3,
          n**2 - 4 * n + 3, n**2 - 6 * n + 8, n**2 + 2 * n - 2, n**2 - 2 * n - 2,
          n**2 + 4 * n + 1, n**2 - 4 * n - 1]
iChi = [i for i, e in enumerate(grpCHI) if sp.simplify(e - chi_coeff) == 0]
assert len(iChi) == 1
check(4, "チ", circ(iChi[0]), "n^2-4n+3")
c1q = cqv(1)
# sum = (chi)*2^{n+1} - c1q  (printed as  ... - [Tsu]), so Tsu = c1q
tsu = c1q
print("c_1(quad) =", c1q, " Tsu =", tsu)
assert tsu == 6
check(4, "ツ", str(int(tsu)))


# =====================================================================
#  distribution check (selection slots): no 3-in-a-row
# =====================================================================
sel_order_3 = ["ア", "ウ", "オ", "カ", "キ", "ク", "ケ", "コ",
               "タ", "チ", "ツ", "テ", "ト", "ナ"]
sel_order_4 = ["カ", "コ", "サ", "ソ", "チ"]
seq = [CLAIM[3][k_] for k_ in sel_order_3] + [CLAIM[4][k_] for k_ in sel_order_4]
print("selection slot sequence:", seq)
run = max_run = 1
for i in range(1, len(seq)):
    run = run + 1 if seq[i] == seq[i - 1] else 1
    max_run = max(max_run, run)
print("max run:", max_run)
assert max_run < 3, "3-in-a-row selection detected"
from collections import Counter
print("distribution:", dict(Counter(seq)))


# =====================================================================
if fails:
    print("\n=== FAIL ===")
    for f_ in fails:
        print(f_)
    raise SystemExit(1)
print("\nALL VERIFY PASS")
