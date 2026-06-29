#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共通テスト問題プールの品質是正 (監査A2/A3/A4/A5)。本番DBを read→fix→(APPLY時のみ)write。
  APPLY=1 で実書込。既定は DRY-RUN (件数と例のみ)。
  railway run -s Postgres python3 scripts/math_exam_drill/fix_pool_quality.py
"""
import os, json, re, psycopg
from collections import Counter

APPLY = os.environ.get("APPLY") == "1"
conn = psycopg.connect(os.environ["DATABASE_PUBLIC_URL"]); conn.autocommit = True
c = conn.cursor()

def load(qd): return qd if isinstance(qd, (dict, list)) else json.loads(qd)
def dump(d): return json.dumps(d, ensure_ascii=False)

def upd(rid, d):
    if APPLY:
        c.execute("UPDATE exam_questions SET question_data=%s WHERE id=%s", (dump(d), rid))

# ---------- A5a: \text{...} 内の中点 ·(U+00B7) / ・(U+30FB) を }\cdot\text{ に ----------
TEXT = re.compile(r'\\text\{([^{}]*)\}')
def fix_textdot(s):
    if not isinstance(s, str) or ('·' not in s and '・' not in s): return s, False
    changed = [False]
    def repl(m):
        inner = m.group(1)
        if '·' in inner or '・' in inner:
            changed[0] = True
            inner = inner.replace('·', '}\\cdot\\text{').replace('・', '}\\cdot\\text{')
        return '\\text{' + inner + '}'
    return TEXT.sub(repl, s), changed[0]
def walk_textdot(o):
    if isinstance(o, dict):
        ch=False
        for k,v in o.items():
            o[k],c2=walk_textdot(v); ch=ch or c2
        return o,ch
    if isinstance(o, list):
        ch=False
        for i,v in enumerate(o):
            o[i],c2=walk_textdot(v); ch=ch or c2
        return o,ch
    s,c2=fix_textdot(o); return s,c2

# ---------- A4: 単一 $...$ → \(...\) (＄＄ display は保護)。理系記述partのみ ----------
A4_PARTS = ["math_q1","math_q2","math_q3","phys_q1","phys_q2","phys_q3","chem_q1","chem_q2","chem_q3","bio_q1"]
SENT = ""
SINGLE = re.compile(r'\$([^$]+?)\$')
def fix_dollar(s):
    if not isinstance(s, str) or '$' not in s: return s, False
    prot = s.replace('$$', '\x00DISPLAYMATH\x00')
    new = SINGLE.sub(lambda m: '\\(' + m.group(1) + '\\)', prot)
    new = new.replace('\x00DISPLAYMATH\x00', '$$')
    return new, (new != s)
def walk_dollar(o):
    if isinstance(o, dict):
        ch=False
        for k,v in o.items(): o[k],c2=walk_dollar(v); ch=ch or c2
        return o,ch
    if isinstance(o, list):
        ch=False
        for i,v in enumerate(o): o[i],c2=walk_dollar(v); ch=ch or c2
        return o,ch
    s,c2=fix_dollar(o); return s,c2

def run():
    # ===== A2: id442 第3小問 重複 unanimous(idx1) → unilateral =====
    print("=== A2: id442 ===")
    c.execute("SELECT question_data FROM exam_questions WHERE id=442")
    row=c.fetchone()
    if row:
        d=load(row[0]); qs=d.get("questions") or []
        for qi,qq in enumerate(qs):
            ch=qq.get("choices") or []
            if ch and len(ch)!=len(set(ch)):
                print(f"  q{qi+1} before: {ch} ans={qq.get('answer')}")
                # 重複している非正解側を別語に。idx1 'unanimous' → 'unilateral'
                seen={}
                for i,x in enumerate(ch):
                    if x in seen and i!=qq.get("answer"):
                        ch[i] = "unilateral" if x=="unanimous" else (x+"_alt")
                    seen[x]=i
                print(f"  q{qi+1} after : {ch}")
        upd(442, d)

    # ===== A5a: text-dot 全part =====
    print("=== A5a: \\text{} 内中点 ===")
    c.execute(r"SELECT id, question_data FROM exam_questions WHERE question_data::text ~ '\\\\text\{[^}]*(·|・)[^}]*\}'")
    rows=c.fetchall(); n=0
    for rid,qd in rows:
        d=load(qd); d2,ch=walk_textdot(d)
        if ch: n+=1; upd(rid,d2)
    print(f"  fixed rows: {n}")

    # ===== A5b: 検証済プール重複 削除 (18913/18915/18917) =====
    print("=== A5b: verified dup 削除 ===")
    for keep,dele in [(18912,18913),(18914,18915),(18916,18917)]:
        c.execute("SELECT question_data FROM exam_questions WHERE id=%s",(keep,)); a=c.fetchone()
        c.execute("SELECT question_data FROM exam_questions WHERE id=%s",(dele,)); b=c.fetchone()
        if not a or not b: print(f"  {keep}/{dele}: 不在 skip"); continue
        same = dump(load(a[0]))==dump(load(b[0]))
        c.execute("SELECT count(*) FROM question_attempts WHERE exam_question_id=%s",(dele,)); att=c.fetchone()[0]
        print(f"  keep={keep} del={dele} content同一={same} del側attempts={att}")
        if same and att==0 and APPLY:
            c.execute("DELETE FROM exam_questions WHERE id=%s",(dele,))

    # ===== A4: single-$ 正規化 =====
    print("=== A4: single-$ → \\(\\) (理系記述part) ===")
    for pk in A4_PARTS:
        c.execute("SELECT id, question_data FROM exam_questions WHERE part_key=%s AND question_data::text LIKE '%%$%%'",(pk,))
        rows=c.fetchall(); n=0
        for rid,qd in rows:
            d=load(qd); d2,ch=walk_dollar(d)
            if ch: n+=1; upd(rid,d2)
        if rows: print(f"  {pk}: $行={len(rows)} 変換={n}")

    # ===== A3: 正解位置 均等化 (位置参照0の安全part) =====
    # ★A3対象は「解説が選択肢を位置で名指ししない」part に限定。
    #   rinri(118件)/phys_q2(18件) は「選択肢 0 は…」と0始まり位置参照→シャッフルで解説破壊するため除外。
    #   gendai_unit は位置名指し0件(現代文は本文内容を参照)で安全。
    print("=== A3: 正解位置均等化 (gendai_unit のみ・位置参照0) ===")
    SAFE=[("daigaku","gendai_unit")]
    for pe,pk in SAFE:
        c.execute("SELECT id, question_data FROM exam_questions WHERE exam_id=%s AND part_key=%s ORDER BY id",(pe,pk))
        rows=c.fetchall()
        # 平坦化: (rid, d, qindex) で4択intのみ対象
        slots=[]
        for rid,qd in rows:
            d=load(qd)
            for qi,qq in enumerate(d.get("questions") or [d]):
                ch=qq.get("choices")
                a=qq.get("answer")
                ai=a if isinstance(a,int) else (int(a) if isinstance(a,str) and a.isdigit() else None)
                if isinstance(ch,list) and len(ch)==4 and ai is not None and 0<=ai<4:
                    slots.append((rid,d,qq,ai))
        before=Counter(s[3] for s in slots)
        # round-robin 目標位置
        for k,(rid,d,qq,ai) in enumerate(slots):
            tgt=k%4
            if tgt!=ai:
                ch=qq["choices"]; correct=ch[ai]
                rest=[ch[j] for j in range(4) if j!=ai]
                newch=[None]*4; newch[tgt]=correct; j=0
                for i in range(4):
                    if i!=tgt: newch[i]=rest[j]; j+=1
                qq["choices"]=newch
                qq["answer"]=tgt if isinstance(qq.get("answer"),int) else str(tgt)
        after=Counter(qq["answer"] if isinstance(qq["answer"],int) else int(qq["answer"]) for _,_,qq,_ in slots)
        print(f"  {pe}/{pk}: n={len(slots)} before={dict(sorted(before.items()))} after={dict(sorted(after.items()))}")
        if APPLY:
            seen_rows={}
            for rid,d,_,_ in slots: seen_rows[rid]=d   # 1行=1 d オブジェクト(in-place変異済)
            for rid,d in seen_rows.items(): upd(rid,d)

    print("\nMODE:", "APPLY(書込済)" if APPLY else "DRY-RUN(未書込)")

run()
conn.close()
