#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英検準1級 二次(面接)カード(cards_ja.json)→ exam_questions import ペイロード生成。
本物の準1級二次形式: s_read=4コマナレーション / s_q1=No.1(イラスト質問) / s_qa=No.2-4(意見)。
生成: 2026-07-23。単一ソース。import は import_prod.py (railway run -s ai-juku-api) で。
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cards_ja.json")
ORIG = os.path.join(HERE, "cards.json")
OUT = os.path.join(HERE, "payload.json")
MODEL = "claude-max-eiken-nijikai-gp1-20260723"
GRADE = "gp1"

cards = json.load(open(SRC, encoding="utf-8"))
orig = json.load(open(ORIG, encoding="utf-8"))

def clean(s):
    """表示ノイズ除去: 生成物に紛れたリテラル `\\"`(バックスラッシュ+引用符)→ `"`。
    正規の日本語/英語本文にバックスラッシュ+引用符は出ないため安全。"""
    return (s or "").replace('\\"', '"').replace("\\'", "'")

# --- 独立検証: frames以外は元と同一 / framesは全て日本語・4要素 ---
def has_ja(s): return bool(re.search(r"[ぁ-んァ-ヶ一-龥]", s or ""))
assert len(cards) == 4, f"カード枚数 {len(cards)} != 4"
by_topic_orig = {c["topic_en"]: c for c in orig}
NONFRAME = [k for k in cards[0].keys() if k != "frames"]
for c in cards:
    o = by_topic_orig[c["topic_en"]]
    assert len(c["frames"]) == 4, f"{c['topic_en']}: frames != 4"
    assert all(has_ja(f) for f in c["frames"]), f"{c['topic_en']}: 日本語でないframeあり"
    for k in NONFRAME:
        assert c.get(k) == o.get(k), f"{c['topic_en']}: フィールド {k} が元と不一致"
print("✅ 検証OK: 全4枚 frames=日本語4コマ / frames以外は元と完全一致")

def storyboard(frames):
    return "🖼 4コマイラスト（各コマの場面を英語で描写しながら、ひとつの物語として語る）\n\n" + "\n\n".join(clean(f) for f in frames)

rows = []
for c in cards:
    sb = storyboard(c["frames"])
    topic_ja = c["topic_ja"]
    # ① ナレーション (s_read)
    rows.append({
        "exam_id": "eiken", "part_key": "s_read", "eiken_grade": GRADE, "model": MODEL,
        "question_data": {
            "passage": sb, "audio_script": "", "prompt": clean(c["narration_prompt"]),
            "questions": [{
                "id": "q1", "type": "speaking",
                "stem": "上の4コマのストーリーを英語で語ってください（指定の第1文で始め、約2分・過去形と接続語を使う）。",
                "choices": [], "answer": clean(c["narration_model"]),
                "explanation": clean(c["narration_tips"]), "unit": f"二次-ナレーション（{topic_ja}）",
            }],
        },
    })
    # ② No.1 (s_q1) — 4コマ目の人物視点。文脈のため storyboard も付す
    rows.append({
        "exam_id": "eiken", "part_key": "s_q1", "eiken_grade": GRADE, "model": MODEL,
        "question_data": {
            "passage": sb, "audio_script": "",
            "prompt": "4コマ目の人物になったつもりで、面接官の質問に英語で答えてください。",
            "questions": [{
                "id": "q1", "type": "speaking", "stem": clean(c["q1_stem"]), "choices": [],
                "answer": clean(c["q1_model"]), "explanation": clean(c["q1_tips"]), "unit": f"二次-No.1（{topic_ja}）",
            }],
        },
    })
    # ③ No.2-4 (s_qa) — 意見。No.2/3=トピック関連, No.4=一般社会問題
    rows.append({
        "exam_id": "eiken", "part_key": "s_qa", "eiken_grade": GRADE, "model": MODEL,
        "question_data": {
            "passage": "", "audio_script": "",
            "prompt": f"テーマ「{topic_ja}」に関する質問です。面接官の質問に即興で答えてください（各: 立場を先に述べ、理由を2つ）。",
            "questions": [
                {"id": "q1", "type": "speaking", "stem": clean(c["q2_stem"]), "choices": [],
                 "answer": clean(c["q2_model"]), "explanation": clean(c["q2_tips"]), "unit": f"二次-No.2（{topic_ja}）"},
                {"id": "q2", "type": "speaking", "stem": clean(c["q3_stem"]), "choices": [],
                 "answer": clean(c["q3_model"]), "explanation": clean(c["q3_tips"]), "unit": f"二次-No.3（{topic_ja}）"},
                {"id": "q3", "type": "speaking", "stem": clean(c["q4_stem"]), "choices": [],
                 "answer": clean(c["q4_model"]), "explanation": clean(c["q4_tips"]), "unit": f"二次-No.4（一般社会・{topic_ja}）"},
            ],
        },
    })

json.dump({"questions": rows, "skip_full": True}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- サマリ ---
from collections import Counter
cnt = Counter((r["exam_id"], r["part_key"], r["eiken_grade"]) for r in rows)
print(f"\n✅ {len(rows)} 行 → {OUT}")
for k, v in sorted(cnt.items()):
    print(f"   {k[0]}/{k[1]}/{k[2]}: {v} 行")
nq = sum(len(r["question_data"]["questions"]) for r in rows)
print(f"   総設問数(小問): {nq}")
