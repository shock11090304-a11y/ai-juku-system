#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cards_ja.json → 二次面接モード(s_interview)用ペイロード。
1カード=1行に「ナレーション + No.1〜No.4」を通しで格納。frontend の面接runnerが
phase/prep_sec/answer_sec/examiner_say を読んで逐次進行(面接官TTS・タイマー・録音)する。
"""
import json, os, re, base64

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cards_ja.json")
OUT = os.path.join(HERE, "interview_payload.json")
FIGDIR = os.path.join(HERE, "figures")
MODEL = "claude-max-eiken-interview-gp1-20260723"
GRADE = "gp1"

# topic_en → 4コマイラスト画像ファイル(gpt-image-1生成→1280px JPEG最適化・gen_figure.py)。
TOPIC_TO_SLUG = {
    "Technology in Schools": "edtech",
    "Telework and Flexible Working": "telework",
    "Community Support for the Elderly": "aging",
    "Reducing Plastic Waste": "plastic",
}

def figure_data_uri(topic_en):
    """topic の4コマ画像を data:image/jpeg;base64,… にして返す(無ければ空文字)。
    事前生成した画像を payload に直接埋め込む=取込時も生徒fetch時もOpenAI課金ゼロ(一度きり)。"""
    slug = TOPIC_TO_SLUG.get(topic_en)
    if not slug:
        return ""
    p = os.path.join(FIGDIR, slug + ".jpg")
    if not os.path.exists(p):
        return ""
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
    return "data:image/jpeg;base64," + b64

def clean(s):
    # リテラルのエスケープ列を実文字へ (\n→改行・\"→"・\'→')。build_payload.py と同一方針。
    return (s or "").replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'")

cards = json.load(open(SRC, encoding="utf-8"))
assert len(cards) == 4, f"カード{len(cards)}枚 != 4"

def storyboard(frames):
    return "🖼 4コマイラスト（各コマの場面を英語で描写しながら、ひとつの物語として語る）\n\n" + "\n\n".join(clean(f) for f in frames)

rows = []
for c in cards:
    topic_ja = c["topic_ja"]
    qs = [
        {"id": "q1", "type": "speaking", "phase": "narration", "label": "ナレーション",
         "prep_sec": 60, "answer_sec": 120,
         "examiner_say": clean(c["narration_prompt"]),
         "stem": "4コマのストーリーを英語で語ってください（指定の第1文で始め、過去形と接続語で・約2分）。",
         "answer": clean(c["narration_model"]), "explanation": clean(c["narration_tips"])},
        {"id": "q2", "type": "speaking", "phase": "q1", "label": "No.1",
         "prep_sec": 0, "answer_sec": 60,
         "examiner_say": clean(c["q1_stem"]), "stem": clean(c["q1_stem"]),
         "answer": clean(c["q1_model"]), "explanation": clean(c["q1_tips"])},
        {"id": "q3", "type": "speaking", "phase": "q2", "label": "No.2",
         "prep_sec": 0, "answer_sec": 60,
         "examiner_say": clean(c["q2_stem"]), "stem": clean(c["q2_stem"]),
         "answer": clean(c["q2_model"]), "explanation": clean(c["q2_tips"])},
        {"id": "q4", "type": "speaking", "phase": "q3", "label": "No.3",
         "prep_sec": 0, "answer_sec": 60,
         "examiner_say": clean(c["q3_stem"]), "stem": clean(c["q3_stem"]),
         "answer": clean(c["q3_model"]), "explanation": clean(c["q3_tips"])},
        {"id": "q5", "type": "speaking", "phase": "q4", "label": "No.4",
         "prep_sec": 0, "answer_sec": 60,
         "examiner_say": clean(c["q4_stem"]), "stem": clean(c["q4_stem"]),
         "answer": clean(c["q4_model"]), "explanation": clean(c["q4_tips"])},
    ]
    fig = figure_data_uri(c.get("topic_en", ""))
    assert fig, f"画像が見つからない: topic_en={c.get('topic_en')} (figures/ に jpg を配置)"
    rows.append({
        "exam_id": "eiken", "part_key": "s_interview", "eiken_grade": GRADE, "model": MODEL,
        "question_data": {
            "passage": storyboard(c["frames"]),
            "audio_script": "",
            "prompt": f"二次面接シミュレーション（テーマ: {topic_ja}）。面接官の指示に従って、ナレーション→No.1〜No.4の順に英語で答えます。",
            "topic_ja": topic_ja,
            "figure_b64": fig,  # 4コマイラスト(data URI・面接runnerがナレーション/No.1で表示)
            "questions": qs,
        },
    })

json.dump({"questions": rows, "skip_full": True}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 検証: 文字列値そのものにリテラル[バックスラッシュ+引用符]が無いこと
#   (json.dumps は正規の引用符も \" にエスケープするので、シリアライズ後ではなく値で検査する)
def scan(o):
    if isinstance(o, str):
        return (chr(92) + chr(34)) in o or (chr(92) + 'n') in o  # リテラル \" / \n の残存検出
    if isinstance(o, dict):
        return any(scan(v) for v in o.values())
    if isinstance(o, list):
        return any(scan(v) for v in o)
    return False
for r in rows:
    qd = r["question_data"]
    assert len(qd["questions"]) == 5, "設問5でない"
    for q in qd["questions"]:
        assert q["stem"] and q["answer"] and q["examiner_say"], "空フィールド"
    assert not scan(qd), "リテラル[バックスラッシュ+引用符]残存"
print(f"✅ {len(rows)} 行(s_interview・各5設問=計{sum(len(r['question_data']['questions']) for r in rows)}) → {OUT}")
