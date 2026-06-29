#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲ソルバー(units_verify/<slug>__<P>.json)の解答と保存正解(units/<slug>.json)を
決定的に厳密照合し、疑義のある問題を flagged.json に抽出する。

LLMは「解く」だけ。照合・フラグ判定はここ(Python)で行う=ミスの混入を防ぐ。

フラグ条件(いずれか):
  key-mismatch : いずれかのソルバーが保存正解と食い違う
  verifiers-split: ソルバー同士で割れている
  multiple-valid : いずれかが「2つ目の正解あり」と判定
  grammatical    : いずれかが「英文が不自然/誤り」と判定
  off-unit       : いずれかが「単元不一致」と判定
  missing        : 3人ぶんの解答が揃っていない
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "units")
VER = os.path.join(HERE, "units_verify")
PERSONAS = ["A", "B", "C"]

def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[.,?!;:\"'()\[\]]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def norm_loose(s):
    # 括弧内(任意要素 (by him) 等)を除去してから正規化
    s = re.sub(r"\([^)]*\)", " ", s or "")
    return norm(s)

def load_verifiers(slug):
    out = {}
    for p in PERSONAS:
        path = os.path.join(VER, f"{slug}__{p}.json")
        if not os.path.exists(path):
            out[p] = None
            continue
        try:
            d = json.load(open(path, encoding="utf-8"))
            by_no = {}
            for v in d.get("verdicts", []):
                by_no[v["no"]] = v
            out[p] = by_no
        except Exception as e:
            out[p] = {"_error": str(e)}
    return out

def main():
    slugs = sys.argv[1:] or None
    files = sorted(f[:-5] for f in os.listdir(SRC) if f.endswith(".json"))
    if slugs:
        files = [s for s in files if s in slugs]

    flagged = []
    reason_counts = {}
    bad_files = []
    per_unit = {}

    for slug in files:
        d = json.load(open(os.path.join(SRC, f"{slug}.json"), encoding="utf-8"))
        unit = d["unit"]
        vmaps = load_verifiers(slug)
        # ファイル健全性
        for p in PERSONAS:
            vm = vmaps[p]
            if vm is None:
                bad_files.append(f"{slug}__{p}: MISSING")
            elif "_error" in vm:
                bad_files.append(f"{slug}__{p}: PARSE {vm['_error']}")
            elif len(vm) != len(d["questions"]):
                bad_files.append(f"{slug}__{p}: {len(vm)}/{len(d['questions'])} verdicts")
        n_flag = 0
        for q in d["questions"]:
            no = q["no"]; t = q["type"]
            reasons = []
            solver_disp = {}
            concerns = []
            present = 0
            mc_idxs = []
            sents = []
            for p in PERSONAS:
                vm = vmaps[p]
                v = (vm or {}).get(no) if isinstance(vm, dict) and "_error" not in (vm or {}) else None
                if not v:
                    continue
                present += 1
                if v.get("multiple_valid"):
                    concerns.append(f"{p}:multi:{v.get('multiple_valid_note','')[:60]}")
                if v.get("grammatical_issue"):
                    concerns.append(f"{p}:gram:{v.get('note','')[:60]}")
                if v.get("off_unit"):
                    concerns.append(f"{p}:offunit:{v.get('note','')[:60]}")
                if t == "mc":
                    mc_idxs.append(v.get("mc_index"))
                    solver_disp[p] = f"idx={v.get('mc_index')}"
                else:
                    sents.append(v.get("produced_sentence", ""))
                    solver_disp[p] = v.get("produced_sentence", "")

            if present < len(PERSONAS):
                reasons.append("missing")

            if t == "mc":
                ai = q.get("answer_index")
                if any(ix != ai for ix in mc_idxs):
                    reasons.append("key-mismatch")
                if len(set(mc_idxs)) > 1:
                    reasons.append("verifiers-split")
                key_disp = f"idx={ai}:{q.get('answer_text','')}"
            else:
                keyn = norm(q.get("answer_text", ""))
                keyl = norm_loose(q.get("answer_text", ""))
                def matches(s):
                    return norm(s) == keyn or norm_loose(s) == keyl
                if any(not matches(s) for s in sents):
                    reasons.append("key-mismatch")
                if len({norm_loose(s) for s in sents}) > 1:
                    reasons.append("verifiers-split")
                key_disp = q.get("answer_text", "")

            if concerns:
                if any("multi" in c for c in concerns): reasons.append("multiple-valid")
                if any("gram" in c for c in concerns): reasons.append("grammatical")
                if any("offunit" in c for c in concerns): reasons.append("off-unit")

            if reasons:
                reasons = sorted(set(reasons))
                n_flag += 1
                for r in reasons:
                    reason_counts[r] = reason_counts.get(r, 0) + 1
                flagged.append({
                    "slug": slug, "unit": unit, "no": no, "type": t,
                    "reasons": reasons,
                    "key_answer": key_disp,
                    "solvers": solver_disp,
                    "concerns": concerns,
                })
        per_unit[slug] = n_flag

    flagged.sort(key=lambda x: (x["slug"], x["no"]))
    json.dump(flagged, open(os.path.join(HERE, "flagged.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("=== reconcile ===")
    print("units:", len(files), "| flagged questions:", len(flagged))
    print("reason breakdown:", reason_counts)
    print("per-unit flags:", {k: v for k, v in per_unit.items() if v})
    if bad_files:
        print("!! BAD/INCOMPLETE verify files:")
        for b in bad_files:
            print("  ", b)
    # 重要: key-mismatch を強調表示(最優先)
    km = [f for f in flagged if "key-mismatch" in f["reasons"]]
    print(f"\n*** key-mismatch (要精査) : {len(km)} ***")
    for f in km:
        print(f"  {f['slug']} #{f['no']} [{f['type']}] key={f['key_answer']!r} solvers={f['solvers']}")

if __name__ == "__main__":
    main()
