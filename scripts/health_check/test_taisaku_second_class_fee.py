#!/usr/bin/env python3
"""志望大学・学部別 対策クラスの料金 (2026-11-19 塾長決定):
1クラス目 12,500円・2クラス目から1クラスにつき 6,000円。サーバ (api/register-subscribe.py) と courses.json の両方を確かめる。"""
import importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("rs", ROOT / "api/register-subscribe.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
ARC = ["archive-kankan", "archive-kyutei", "archive-ninki", "archive-chuken"]
ng = 0
def check(label, got, want):
    global ng
    ok = got == want
    print(("✅" if ok else "❌"), label, got, "" if ok else f"(期待 {want})")
    ng += 0 if ok else 1
for n, want in [(1, 12500), (2, 18500), (3, 24500), (4, 30500)]:
    check(f"対策クラス {n} つ", m._calculate_fee(ARC[:n], [])[0], want)
check("並べ方が逆でも同じ", m._calculate_fee(list(reversed(ARC[:2])), [])[0], 18500)
check("ほかのコースは割り引かない", m._calculate_fee(["gmarch", "soukei", "archive-chuken"], [])[0], 37500)
check("設備費は1回だけ", m._calculate_fee(ARC[:2], ["facility-1350"])[0], 19850)
cj = json.loads((ROOT / "payment/courses.json").read_text(encoding="utf-8"))
for c in cj["courses"]:
    if c["id"] in ARC:
        check(f"courses.json {c['id']} group/addPrice", (c.get("group"), c.get("addPrice")), ("taisaku", 6000))
        check(f"サーバ {c['id']} group/addPrice", (m.COURSES[c["id"]].get("group"), m.COURSES[c["id"]].get("addPrice")), ("taisaku", 6000))
print("✅ ALL PASS" if not ng else f"❌ {ng} 件 NG")
sys.exit(1 if ng else 0)
