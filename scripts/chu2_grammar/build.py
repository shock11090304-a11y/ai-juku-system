# -*- coding: utf-8 -*-
"""中2英文法ドリル(過去形/未来形/助動詞 各15) 作問 → 検証補助 → import JSON 生成。

- 作問は中2レベル・自己完結(stemに文全体+空所___)・単一正解。
- 解説は「値参照」のみ(位置トークン ①②/N番目/答え:N を書かない)= ラウンドロビン位置シャッフルで陳腐化しない。
- unit は GRAMMAR_UNITS 準拠: 過去形/未来形 → 「時制」, 助動詞 → 「助動詞」。
  グループ(過去形/未来形/助動詞)は group フィールドで保持し、宿題ドリル分離に使う。
出力:
  seed-data/chu2_grammar_v1.json      … import 用(unit/level/stem/choices/answer(0始index)/explanation/source/subject)
  scripts/chu2_grammar/blind_view.json … 盲ソルバー用(stem+choices のみ・キー無し)
"""
import json, os, re

SOURCE = "chu2grammar-20260709"   # <=30字。rollback: DELETE FROM grammar_questions WHERE source=...
SUBJECT = "english"
LEVEL = "basic"                    # 中2レベル

# 各問: (group, stem, [choices...(自然順)], answer_text, explanation)
# answer_text は choices のどれかと完全一致。builder が位置を round-robin 再配置する。
Q = [
# ================= 過去形 (unit=時制) 15問 =================
("past", "I ___ soccer with my friends yesterday.",
 ["play", "played", "playing", "plays"], "played",
 "yesterday(昨日)があるので過去の文。play は規則変化で過去形「played」になる。"),
("past", "She ___ to the library last Sunday.",
 ["go", "goes", "went", "going"], "went",
 "last Sunday(先週の日曜)で過去の文。go の過去形は不規則で「went」。"),
("past", "We ___ a movie last night.",
 ["watch", "watched", "watches", "watching"], "watched",
 "last night(昨夜)で過去の文。watch の過去形は規則変化で「watched」。"),
("past", "He ___ up at six this morning.",
 ["get", "got", "gets", "getting"], "got",
 "this morning の出来事で過去の文。get の過去形は不規則で「got」。"),
("past", "My father ___ very busy last week.",
 ["is", "was", "were", "are"], "was",
 "主語 My father は3人称単数で、last week(先週)なので be 動詞の過去形は「was」。"),
("past", "They ___ in Osaka three years ago.",
 ["live", "lived", "lives", "living"], "lived",
 "three years ago(3年前)で過去の文。live は e で終わるので d だけ足して「lived」。"),
("past", "I ___ my homework after dinner last night.",
 ["do", "did", "does", "done"], "did",
 "last night(昨夜)があるので過去の文。do の過去形は不規則で「did」。"),
("past", "___ you enjoy the concert last night?",
 ["Do", "Did", "Are", "Were"], "Did",
 "一般動詞 enjoy の過去の疑問文。last night があるので文頭は「Did」。"),
("past", "We ___ not have school yesterday.",
 ["did", "do", "were", "was"], "did",
 "一般動詞 have の過去の否定文は did not(didn't) を使う。空所には「did」。"),
("past", "She ___ a beautiful picture in art class yesterday.",
 ["draw", "drew", "drawn", "draws"], "drew",
 "yesterday(昨日)があるので過去の文。draw の過去形は不規則で「drew」。"),
("past", "The students ___ very tired after the game.",
 ["was", "were", "are", "is"], "were",
 "主語 The students は複数なので、過去の be 動詞は「were」。"),
("past", "I ___ my grandmother last weekend.",
 ["visit", "visited", "visits", "visiting"], "visited",
 "last weekend(先週末)で過去の文。visit の過去形は規則変化で「visited」。"),
("past", "He ___ lunch at that restaurant.",
 ["eat", "ate", "eaten", "eats"], "ate",
 "過去の動作。eat の過去形は不規則で「ate」。"),
("past", "We ___ a lot of pictures on the trip.",
 ["take", "took", "taken", "takes"], "took",
 "旅行での過去の動作。take の過去形は不規則で「took」。"),
("past", "It ___ rainy last Monday.",
 ["is", "was", "were", "did"], "was",
 "主語 It は3人称単数で、last Monday なので過去の be 動詞「was」。"),

# ================= 未来形 (unit=時制) 15問 =================
("future", "I ___ visit my uncle next Sunday.",
 ["will", "am", "do", "was"], "will",
 "next Sunday(次の日曜)で未来の文。will の後は動詞の原形。空所には「will」。"),
("future", "It ___ be sunny tomorrow.",
 ["will", "is", "was", "does"], "will",
 "tomorrow(明日)の予想で未来の文。「will be 〜」で『〜だろう』。空所には「will」。"),
("future", "She is going to ___ tennis this afternoon.",
 ["play", "plays", "played", "playing"], "play",
 "be going to の後は動詞の原形。空所には原形の「play」。"),
("future", "We ___ going to have a party next week.",
 ["are", "will", "do", "is"], "are",
 "主語 We に合う be 動詞は「are」。be going to で未来を表す。"),
("future", "___ you help me tomorrow?",
 ["Will", "Do", "Are", "Did"], "Will",
 "tomorrow がある未来の依頼・疑問文。文頭は「Will」。"),
("future", "He ___ be twelve years old next month.",
 ["will", "is", "was", "are"], "will",
 "next month(来月)で未来の文。「will be 〜」で年齢の予定。空所には「will」。"),
("future", "I'm going ___ study English hard.",
 ["to", "for", "at", "in"], "to",
 "be going to + 動詞の原形 で未来を表す。空所には「to」。"),
("future", "They will ___ to Okinawa next summer.",
 ["go", "going", "went", "goes"], "go",
 "助動詞 will の後は動詞の原形。空所には原形の「go」。"),
("future", "My brother ___ going to buy a new bike.",
 ["is", "are", "will", "does"], "is",
 "主語 My brother は3人称単数なので be 動詞は「is」。be going to で未来。"),
("future", "___ it be cold tomorrow? — No, it won't.",
 ["Will", "Is", "Does", "Did"], "Will",
 "答えが No, it won't. なので疑問文は Will を使う未来の文。文頭は「Will」。"),
("future", "What ___ you do next weekend?",
 ["will", "do", "are", "did"], "will",
 "next weekend(次の週末)で未来の疑問文。「What will you do?」空所には「will」。"),
("future", "The train ___ arrive at ten.",
 ["will", "is", "was", "has"], "will",
 "これからの予定を表す未来の文。「will arrive」。空所には「will」。"),
("future", "Are you going ___ join the soccer team?",
 ["to", "for", "with", "in"], "to",
 "be going to + 動詞の原形 の疑問文。空所には「to」。"),
("future", "We ___ meet in front of the station tomorrow.",
 ["will", "are", "do", "were"], "will",
 "tomorrow がある未来の文。「will meet」。空所には「will」。"),
("future", "She won't ___ late for school.",
 ["be", "is", "was", "being"], "be",
 "won't(will not)の後は動詞の原形。be 動詞の原形は「be」。"),

# ================= 助動詞 (unit=助動詞) 15問 =================
("aux", "___ you play the guitar? — Yes, I can.",
 ["Can", "Do", "Must", "Are"], "Can",
 "答えが Yes, I can. なので疑問文も Can を使う。『〜できますか』。文頭は「Can」。"),
("aux", "I have ___ get up early every day.",
 ["to", "can", "will", "must"], "to",
 "have to + 動詞の原形 で『〜しなければならない』。have の後に続くのは「to」。"),
("aux", "Ken can ___ English very well.",
 ["speak", "speaks", "spoke", "speaking"], "speak",
 "助動詞 can の後は動詞の原形。空所には原形の「speak」。"),
("aux", "___ I use your pen? — Sure, go ahead.",
 ["May", "Do", "Am", "Was"], "May",
 "『〜してもいいですか』と許可を求める文。答えが Sure なので文頭は「May」。"),
("aux", "It's cold. You ___ close the window.",
 ["should", "are", "is", "being"], "should",
 "『〜したほうがよい』と助言する文。助動詞 should の後は動詞の原形。空所には「should」。"),
("aux", "Students must ___ the school rules.",
 ["follow", "follows", "followed", "following"], "follow",
 "助動詞 must の後は動詞の原形。空所には原形の「follow」。"),
("aux", "___ I carry your bag? — Oh, thank you.",
 ["Shall", "Do", "Am", "Did"], "Shall",
 "『(私が)〜しましょうか』と申し出る文。答えが thank you なので文頭は「Shall」。"),
("aux", "She ___ swim well when she was five.",
 ["could", "can", "must", "should"], "could",
 "when she was five(5歳のとき)で過去の能力。can の過去形「could」を使う。"),
("aux", "You look sleepy. You ___ go to bed early.",
 ["should", "are", "do", "being"], "should",
 "『〜したほうがよい』と助言する文。助動詞 should の後は動詞の原形。空所には「should」。"),
("aux", "My sister can ___ a bike.",
 ["ride", "rides", "rode", "riding"], "ride",
 "助動詞 can の後は動詞の原形。空所には原形の「ride」。"),
("aux", "We ___ to wear a uniform at our school.",
 ["have", "must", "can", "should"], "have",
 "have to + 動詞の原形 で『〜しなければならない』。to が続くのは「have」だけ。"),
("aux", "___ you close the door, please? — Sure.",
 ["Can", "Do", "Are", "Was"], "Can",
 "『〜してくれますか』と依頼する文。please があり答えが Sure。文頭は「Can」。"),
("aux", "You ___ not run in the hospital.",
 ["must", "are", "is", "being"], "must",
 "must not で『〜してはいけない』という強い禁止を表す。空所には「must」。"),
("aux", "He must ___ tired after the long trip.",
 ["be", "is", "was", "being"], "be",
 "助動詞 must の後は動詞の原形。be 動詞の原形は「be」。「must be tired」で『疲れているにちがいない』。"),
("aux", "___ I have some water? — Of course.",
 ["Can", "Do", "Am", "Was"], "Can",
 "『〜してもいいですか』と求める文。答えが Of course なので文頭は「Can」。"),
]

POS_TOKENS = re.compile(r"[①②③④⑤]|[0-9]\s*番目|答え\s*[:：]\s*[0-9]|選択肢\s*[0-9]|正解\s*[:：]\s*[0-9]")

def main():
    assert len(Q) == 45, f"問題数が45ではない: {len(Q)}"
    groups = {}
    for g, *_ in Q:
        groups[g] = groups.get(g, 0) + 1
    assert groups == {"past": 15, "future": 15, "aux": 15}, groups

    out, blind = [], []
    pos_counter = {"past": 0, "future": 0, "aux": 0}
    unit_map = {"past": "時制", "future": "時制", "aux": "助動詞"}
    for i, (g, stem, choices, ans_text, expl) in enumerate(Q):
        # 健全性チェック
        assert "___" in stem, f"stemに空所(___)が無い: {stem}"
        assert len(choices) == 4, f"選択肢が4つでない: {stem}"
        assert len(set(choices)) == 4, f"選択肢に重複: {stem} {choices}"
        assert ans_text in choices, f"answer_text が choices に無い: {stem} / {ans_text}"
        assert not POS_TOKENS.search(expl), f"解説に位置トークン: {stem} / {expl}"
        # round-robin: グループ内で 0,1,2,3 を順に正解位置へ
        target = pos_counter[g] % 4
        pos_counter[g] += 1
        distractors = [c for c in choices if c != ans_text]  # 元の相対順を保持
        new_choices = []
        di = 0
        for pos in range(4):
            if pos == target:
                new_choices.append(ans_text)
            else:
                new_choices.append(distractors[di]); di += 1
        ans_idx = new_choices.index(ans_text)
        assert new_choices[ans_idx] == ans_text and ans_idx == target
        out.append({
            "group": g,
            "unit": unit_map[g],
            "level": LEVEL,
            "stem": stem,
            "choices": new_choices,
            "answer": ans_idx,               # 0始まりindex
            "explanation": expl,
            "source": SOURCE,
            "subject": SUBJECT,
        })
        blind.append({"n": i, "group": g, "stem": stem, "choices": new_choices})

    base = os.path.dirname(os.path.abspath(__file__))
    seed_dir = os.path.join(base, "..", "..", "seed-data")
    os.makedirs(seed_dir, exist_ok=True)
    with open(os.path.join(seed_dir, "chu2_grammar_v1.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(base, "blind_view.json"), "w", encoding="utf-8") as f:
        json.dump(blind, f, ensure_ascii=False, indent=2)

    # 位置分布レポート
    dist = {0: 0, 1: 0, 2: 0, 3: 0}
    for o in out:
        dist[o["answer"]] += 1
    print("生成 45 問 OK")
    print("正解位置分布:", dist)
    for g in ("past", "future", "aux"):
        gd = {0: 0, 1: 0, 2: 0, 3: 0}
        for o in out:
            if o["group"] == g:
                gd[o["answer"]] += 1
        print(f"  {g}: {gd}")

if __name__ == "__main__":
    main()
