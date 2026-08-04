# -*- coding: utf-8 -*-
"""再チェック(9次元Workflow)の confirmed 指摘＋レベル改善を data に適用する。
- 大問1: 易しすぎる句動詞正解 v31/v32/v39 を準1級相当へ差し替え(正解indexは据置=分布維持)
- 大問1: v01/v34 の why_others_wrong を「目的語に取れない」→「意味が逆・不適」へ修正(confirmed nit)
- 大問3: p3_2(ビーバー) Q1/Q3 の正解肢を本文引き写し→言い換えへ(易化解消)
"""
import json, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ---- 大問1: 差し替え(完全置換) ----
REPLACE = {
    "v31": {
        "id": "v31",
        "sentence": "The negotiators worked late into the night, determined to _______ the last few differences that stood in the way of a final peace agreement.",
        "choices": ["call off", "hand down", "iron out", "give away"],
        "answer": 2,
        "target_word": "iron out",
        "gloss_ja": "(意見の相違・問題を)解決する、円満に片づける",
        "distractors_ja": {"call off": "中止する", "hand down": "(判決・伝統を)申し渡す・伝える", "give away": "ただで譲る・(秘密を)漏らす"},
        "why_correct": "合意を妨げる『残りの相違点を解決する』が文脈に最適。iron out は differences / problems と結びつく定番の句動詞。",
        "why_others_wrong": {"call off": "『中止する』では交渉をまとめようとする文脈と逆になり不適", "hand down": "『申し渡す・伝える』の意で、相違点を解決する文脈にならない", "give away": "『譲る・漏らす』では合意に向けて相違を解消する文脈に合わない"},
        "level": "句動詞",
    },
    "v32": {
        "id": "v32",
        "sentence": "The initial screening test is designed to _______ applicants who lack the basic qualifications, leaving only the strongest candidates for the final interview.",
        "choices": ["weed out", "take after", "hold up", "put up"],
        "answer": 0,
        "target_word": "weed out",
        "gloss_ja": "(不要・不適格なものを)ふるい落とす、除く",
        "distractors_ja": {"take after": "(親などに)似ている", "hold up": "遅らせる・持ちこたえる・強盗する", "put up": "建てる・掲げる・泊める"},
        "why_correct": "資格を欠く応募者を『ふるい落とす』が文脈に最適。weed out は不適格者・欠陥を取り除く意味の定番。",
        "why_others_wrong": {"take after": "『似ている』の意で、応募者を選別する文脈に合わない", "hold up": "『遅らせる・持ちこたえる』の意になり、選別して残す文脈と噛み合わない", "put up": "『建てる・掲げる』の意で、不適格者を除く文脈に合わない"},
        "level": "句動詞",
    },
    "v39": {
        "id": "v39",
        "sentence": "Prices have risen so sharply this year that many families on fixed incomes can no longer _______ the soaring cost of everyday necessities.",
        "choices": ["do without", "keep abreast of", "contend with", "give rise to"],
        "answer": 2,
        "target_word": "contend with",
        "gloss_ja": "(困難・問題に)対処する、立ち向かう",
        "distractors_ja": {"do without": "〜なしで済ませる", "keep abreast of": "(情報・進展に)遅れずについていく", "give rise to": "引き起こす"},
        "why_correct": "固定収入の家庭が高騰する生活費に『対処しきれない』が文脈に最適。contend with は困難な状況に立ち向かう意味。",
        "why_others_wrong": {"do without": "『〜なしで済ます』では生活必需品を諦める意味になり文脈と合わない", "keep abreast of": "『(情報に)遅れずついていく』は最新情報に使う語で、費用への対処には不適", "give rise to": "『引き起こす』では家庭が費用を生じさせる意味になり主語と不整合"},
        "level": "句動詞",
    },
}

# ---- 大問1: why_others_wrong の文言のみ修正(confirmed nit) ----
PATCH_WOW = {
    "v01": {"aggravate": "『悪化させる』は支援内容と矛盾", "provoke": "『挑発する・引き起こす』方向の語で、苦しみを和らげる alleviate とは意味が逆になり不適", "intensify": "『激化させる』は支援の目的と正反対"},
    "v34": {"got away with": "『(罰などを)まぬがれる』の意で、病気に『かかる』文脈に合わない", "made up for": "『埋め合わせる』は病気にかかる文脈に合わない", "caught up with": "『追いつく』では病気を『発症する』意味にならない"},
}

p1 = json.load(open(os.path.join(D, "part1_vocab.json"), encoding="utf-8"))
for it in p1["items"]:
    iid = it["id"]
    if iid in REPLACE:
        it.clear(); it.update(REPLACE[iid])
    elif iid in PATCH_WOW:
        it["why_others_wrong"] = PATCH_WOW[iid]
json.dump(p1, open(os.path.join(D, "part1_vocab.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- 大問3: p3_2 Q1/Q3 の正解肢を言い換えへ(本文引き写し解消) ----
p3 = json.load(open(os.path.join(D, "part3_reading.json"), encoding="utf-8"))
for ps in p3["passages"]:
    if ps["id"] == "p3_2":
        q1 = ps["questions"][0]
        q1["choices"][q1["answer"]] = "People viewed them as harmful creatures responsible for wrecking woodland and submerging usable farmland."
        q3 = ps["questions"][2]
        q3["choices"][q3["answer"]] = "They help purify water by catching mud and contaminants before it flows downstream."
json.dump(p3, open(os.path.join(D, "part3_reading.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("applied: v31/v32/v39 差し替え, v01/v34 文言修正, p3_2 Q1/Q3 言い換え")
