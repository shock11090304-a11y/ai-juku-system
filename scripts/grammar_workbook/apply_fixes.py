#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""審査エージェントの結論(units_fixes/<slug>__<no>.json)を、盲再確認
(units_fixes/<slug>__<no>__check.json)で裏取りしてから units/<slug>.json に適用する。

- action=unchanged       : 変更なし(誤検出=正しかった)
- action=fix_key/rewrite : 構造検証OK かつ 盲チェッカーが一致 のときだけ適用
- それ以外               : UNRESOLVED として保留(手動確認)

LLMは「審査・解答」だけ。確認(一致判定)と適用はここ(Python)で決定的に行う。
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "units")
FIX = os.path.join(HERE, "units_fixes")

def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[.,?!;:\"'()\[\]]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def norm_loose(s):
    s = re.sub(r"\([^)]*\)", " ", s or "")
    return norm(s)

def expand(s):
    """短縮形を展開してから正規化(can't/cannot, don't 等の表記差を吸収)。"""
    s = (s or "").lower()
    s = s.replace("can't", "can not").replace("won't", "will not").replace("shan't", "shall not")
    s = s.replace("cannot", "can not")
    s = re.sub(r"n't\b", " not", s)
    s = re.sub(r"'re\b", " are", s)
    s = re.sub(r"'ve\b", " have", s)
    s = re.sub(r"'ll\b", " will", s)
    s = re.sub(r"'m\b", " am", s)
    return norm(s)

def ascii_ok(s):
    """英語フィールドは半角ASCII印字可能文字のみ許容(スマートクオート/全角空白/絵文字/ダッシュ/省略記号は不可)。"""
    for ch in (s or ""):
        o = ord(ch)
        if ch in "\n\t":
            continue
        if not (0x20 <= o <= 0x7E):
            return False
    return True

def validate_cq(cq):
    """corrected_question の構造検証。問題があれば理由リストを返す。"""
    errs = []
    t = cq.get("type")
    # 英語フィールドのみASCII検査(instruction/prompt_ja/explanation/point は日本語)
    for fld in ("stem", "answer_text", "original"):
        v = cq.get(fld)
        if isinstance(v, str) and not ascii_ok(v):
            errs.append(f"non-ascii in {fld}")
    for ch in (cq.get("choices") or []):
        if not ascii_ok(ch):
            errs.append("non-ascii in choices")
    if t == "mc":
        ch = cq.get("choices") or []
        ai = cq.get("answer_index")
        if len(ch) != 4: errs.append(f"choices={len(ch)}")
        if len(set(ch)) != len(ch): errs.append("dup choices")
        if not isinstance(ai, int) or not (0 <= ai < len(ch)): errs.append(f"answer_index={ai}")
        elif ch[ai] != cq.get("answer_text"): errs.append("answer_text!=choices[ai]")
        if "( )" not in (cq.get("stem") or "") and "()" not in (cq.get("stem") or ""):
            errs.append("no '( )' in stem")
    elif t == "order":
        toks = cq.get("tokens") or []
        ans = cq.get("answer_text") or ""
        tw = sorted(norm(" ".join(toks)).split())
        aw = sorted(norm(ans).split())
        if tw != aw:
            errs.append(f"tokens words != answer words ({tw} vs {aw})")
        if not ans or ans[0].islower(): errs.append("answer not capitalized")
        if ans and ans[-1] not in ".?!": errs.append("answer not terminated")
    elif t == "rewrite":
        for fld in ("original", "instruction", "answer_text"):
            if not (cq.get(fld) or "").strip(): errs.append(f"empty {fld}")
    else:
        errs.append(f"bad type {t}")
    if not (cq.get("explanation") or "").strip(): errs.append("no explanation")
    if not (cq.get("point") or "").strip(): errs.append("no point")
    return errs

def check_confirms(cq, chk):
    """盲チェッカーの独立解が修正後の正解と一致するか。
    mc/order は一意性も必須(選択肢・語順は一意でなければならない)。
    rewrite は『独立解が正解と一致』すれば可(短縮形/任意要素の表記差は吸収。
    書き換えに唯一文字列まで求めると過剰)。"""
    if not chk:
        return False, "no checker file"
    t = cq.get("type")
    if t == "mc":
        if not chk.get("is_unique", False):
            return False, "checker is_unique=false"
        if chk.get("mc_index") == cq.get("answer_index"):
            return True, "ok"
        return False, f"checker idx={chk.get('mc_index')} != {cq.get('answer_index')}"
    elif t == "order":
        if not chk.get("is_unique", False):
            return False, "checker is_unique=false (順序が一意でない)"
        ps = chk.get("produced_sentence", "")
        if norm(ps) == norm(cq.get("answer_text", "")):
            return True, "ok"
        return False, f"checker sentence != answer ({ps!r} vs {cq.get('answer_text')!r})"
    else:  # rewrite
        ps = chk.get("produced_sentence", "")
        key = cq.get("answer_text", "")
        if (norm(ps) == norm(key) or norm_loose(ps) == norm_loose(key)
                or expand(ps) == expand(key) or expand(norm_loose(ps)) == expand(norm_loose(key))):
            return True, "ok(independent solver reproduced the key)"
        return False, f"checker sentence != answer ({ps!r} vs {key!r})"

def main():
    apply = "--apply" in sys.argv
    fix_files = sorted(f for f in os.listdir(FIX) if f.endswith(".json") and "__check" not in f)
    applied, unchanged, unresolved = [], [], []
    units_cache = {}

    for ff in fix_files:
        d = json.load(open(os.path.join(FIX, ff), encoding="utf-8"))
        slug, no = d["slug"], d["no"]
        action = d.get("action")
        tag = f"{slug}#{no}"
        if action == "unchanged":
            unchanged.append((tag, d.get("reason", "")[:80]))
            continue
        cq = d.get("corrected_question")
        if not cq:
            unresolved.append((tag, f"action={action} but no corrected_question"))
            continue
        errs = validate_cq(cq)
        if errs:
            unresolved.append((tag, "INVALID cq: " + "; ".join(errs)))
            continue
        chk_path = os.path.join(FIX, f"{slug}__{no}__check.json")
        chk = json.load(open(chk_path, encoding="utf-8")) if os.path.exists(chk_path) else None
        ok, why = check_confirms(cq, chk)
        if not ok:
            unresolved.append((tag, f"NOT CONFIRMED: {why} | action={action} reason={d.get('reason','')[:60]}"))
            continue
        # 適用準備
        if slug not in units_cache:
            units_cache[slug] = json.load(open(os.path.join(SRC, f"{slug}.json"), encoding="utf-8"))
        ud = units_cache[slug]
        found = False
        for i, q in enumerate(ud["questions"]):
            if q["no"] == no:
                cq["no"] = no  # 念のためno固定
                ud["questions"][i] = cq
                found = True
                break
        if not found:
            unresolved.append((tag, "no not found in unit file"))
            continue
        applied.append((tag, action, d.get("reason", "")[:80]))

    if apply:
        for slug, ud in units_cache.items():
            json.dump(ud, open(os.path.join(SRC, f"{slug}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)

    print("=== apply_fixes", "(APPLIED)" if apply else "(DRY-RUN)", "===")
    print(f"applied: {len(applied)} | unchanged: {len(unchanged)} | unresolved: {len(unresolved)}")
    print("\n-- APPLIED --")
    for tag, act, why in applied:
        print(f"  {tag} [{act}] {why}")
    print("\n-- UNCHANGED (誤検出=元から正しい) --")
    for tag, why in unchanged:
        print(f"  {tag} {why}")
    print("\n-- UNRESOLVED (要手動確認) --")
    for tag, why in unresolved:
        print(f"  {tag} {why}")

if __name__ == "__main__":
    main()
