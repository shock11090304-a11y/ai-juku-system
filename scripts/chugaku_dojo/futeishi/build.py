# -*- coding: utf-8 -*-
"""items.py → exam_questions 行 (question_data JSON) を組み立てて gate をかける。

正解 index は part 通しの round-robin (0,1,2,3) で均等化 = 位置で当てられないようにする。
解説は正解「テキスト」参照なので選択肢を入れ替えても壊れない。

出力:
  build/rows.json        … exam_questions へ入れる行 (5小問/大問)
  build/flat.json        … 全小問フラット (検証用・正解つき)
  build/blind.json       … 全小問フラット (answer/explanation 抜き = 盲ソルバー用)
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from items import ITEMS, UNIT  # noqa: E402

CHUNK = 5  # 既存 chugaku プールに合わせる (5小問/大問)
MODEL = "chugaku-koukou-futeishi-v1"      # ★rollback キー
SOURCE = "chugaku_koukou_futeishi_v1"     # ★rollback キー(question_data 内)

OUT = os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)


def _positions():
    """正解 index を 6/6/6/6 に均等配分しつつ、並び順に規則性を作らない。

    ★ 以前は pos = i % 4 にしていたが、これだと保存順の正解列が 0,1,2,3,0,1,2,3… の
      完全周期になり「英文を読まずに位置の周期だけで全問正解できる」状態になっていた
      (G10 の分布チェックは [6,6,6,6] なので素通りする)。stem の md5 で並べ替えてから
      順に 0,1,2,3 を振ることで、均等配分のまま決定的(再実行で同じ)かつ無規則にする。
    """
    ranked = sorted(range(len(ITEMS)),
                    key=lambda i: hashlib.md5(ITEMS[i]["stem"].encode("utf-8")).hexdigest())
    pos = [0] * len(ITEMS)
    for rank, i in enumerate(ranked):
        pos[i] = rank % 4
    return pos


def build_flat():
    flat = []
    positions = _positions()
    for i, it in enumerate(ITEMS):
        pos = positions[i]
        choices = list(it["distractors"])
        choices.insert(pos, it["correct"])
        assert choices[pos] == it["correct"]
        flat.append({
            "id": f"q{i + 1}",
            "type": "multiple_choice",
            "stem": it["stem"],
            "choices": choices,
            "answer": str(pos),          # ★文字列 index (既存プール規約)
            "unit": UNIT,
            # 正解テキストが「。」「.」で終わるとき(日本語選択肢や英文まるごとの肢)は
            # 直後の「。」を重ねない。G5 の接頭辞チェックも同じ関数を使う。
            "explanation": _expl_head(it["correct"]) + it["expl"],
            "_usage": it["usage"],
            "_correct_text": it["correct"],
        })
    return flat


# ───────────────────────── gates ─────────────────────────
# 位置語 = 選択肢を入れ替えると嘘になる表現。カタカナ語の中の「ア/イ/ウ/エ」を誤検出しないよう、
# 「(ア)」「「ア」」のように選択肢ラベルとして使われた形だけを拾う。
POSITIONAL = re.compile(
    # 「後ろから説明する」等は文法用語なので位置語ではない → 選択肢ラベル形と「N番目」だけを拾う。
    r"[（(「][アイウエ][）)」]|[①②③④]|[（(「][ABCD][）)」]|[0-9０-９一二三四]番目"
)


def _expl_head(correct):
    """解説の定型接頭辞。正解テキストの末尾が句点/ピリオドなら「。」を重ねない。"""
    tail = "" if str(correct).rstrip().endswith(("。", ".", "?", "！", "!")) else "。"
    return f"【単元】{UNIT}。正解は「{correct}」{tail}"


def _sig(q):
    """設問の同一判定キー。★insert.py / post_check.py と同じ規則にすること。
    ここだけ生 stem で見ていると、空白違いの重複を gate が見逃したまま insert 側が
    弾いて「本番に一部しか入らない」事故になる (実際に 25/30 問しか入らなかった)。"""
    return (" ".join(str(q.get("stem", "")).split()),
            tuple(sorted(str(c) for c in (q.get("choices") or []))))


def _wrap(flat):
    """DB に入る行(大問)の外側も含めて検査するため、rows と同じ形に包んだものを返す。"""
    return [{"passage": "", "subject": "英語", "univ_simulated": "公立高校入試(標準)",
             "year_simulated": None, "source": SOURCE, "format_type": UNIT,
             "questions": flat[i:i + CHUNK]} for i in range(0, len(flat), CHUNK)]


def gates(flat):
    errs = []
    # 1. 小問数・id 一意
    if len(flat) != len(ITEMS):
        errs.append(f"[G1] 小問数が items.py と不一致: {len(flat)}")
    if len({q["id"] for q in flat}) != len(flat):
        errs.append("[G1] id 重複")
    # 2. 設問の一意性は (stem, choices) の組で見る。「次の中から、英文として正しいものを
    #    選びなさい。」のように指示文だけが stem になる形式は、選択肢が違えば別問題として正当
    #    (逆に stem 単独で一意を強制すると、同じ形式なのに設問文を無理に言い換える羽目になる)。
    sigs = [_sig(q) for q in flat]
    if len(set(sigs)) != len(sigs):
        errs.append("[G2] 設問(stem+選択肢)の重複")
    for q in flat:
        # 3. 選択肢は4つ・重複なし・空なし
        ch = q["choices"]
        if len(ch) != 4:
            errs.append(f"[G3] {q['id']} 選択肢が4つでない")
        if len({c.strip().lower() for c in ch}) != 4:
            errs.append(f"[G3] {q['id']} 選択肢に重複(大小/空白無視)")
        if any(not c.strip() for c in ch):
            errs.append(f"[G3] {q['id']} 空の選択肢")
        # 4. answer は文字列 index で範囲内、指す先が正解テキスト
        a = q["answer"]
        if not isinstance(a, str) or not a.isdigit() or not (0 <= int(a) < len(ch)):
            errs.append(f"[G4] {q['id']} answer が文字列indexでない: {a!r}")
        elif ch[int(a)] != q["_correct_text"]:
            errs.append(f"[G4] {q['id']} answer index が正解テキストを指していない")
        # 5. 解説は 【単元】UNIT。正解は「正解テキスト」。で始まる
        head = _expl_head(q["_correct_text"])
        if not q["explanation"].startswith(head):
            errs.append(f"[G5] {q['id']} 解説の接頭辞が規約外")
        # 6. unit タグ
        if q["unit"] != UNIT:
            errs.append(f"[G6] {q['id']} unit タグが違う")
        # 7. 位置語(ア/A/①/N番目)の禁止 — 選択肢入替で嘘になるため
        for field in ("stem", "explanation"):
            if POSITIONAL.search(q[field]):
                errs.append(f"[G7] {q['id']} {field} に位置語")
        # 8. 空所補充なら stem に空欄 ( ) が要る。選択肢が「文まるごと」の問題(用法の識別・意味の
        #    理解・正しい英文選択)は空欄を持たないので、選択肢の形で判定する(設問文の文言に依存しない)。
        sentence_choices = any(c.rstrip().endswith((".", "。", "?", "？")) for c in ch)
        if not sentence_choices and "( )" not in q["stem"]:
            errs.append(f"[G8] {q['id']} stem に空欄 ( ) が無い")
        # 9. 解説内に不正解の選択肢テキストを「正解は」として書いていないか(単純衝突検出)
        if q["explanation"].count("正解は「") != 1:
            errs.append(f"[G9] {q['id']} 解説に「正解は「」が複数/ゼロ")
    # 10. 正解位置の分布 (問題数が4の倍数でなくてもよいよう max-min<=1 で判定)
    dist = [0, 0, 0, 0]
    for q in flat:
        dist[int(q["answer"])] += 1
    if max(dist) - min(dist) > 1:
        errs.append(f"[G10] 正解位置が不均等: {dist}")
    # 11. 「いちばん長い選択肢を選ぶ」だけで当たる tell の検出 (= 単独最長)
    longest = sum(1 for q in flat
                  if len(q["choices"][int(q["answer"])]) > max(
                      len(c) for i, c in enumerate(q["choices"]) if i != int(q["answer"])))
    if longest > len(flat) * 0.6:
        errs.append(f"[G11] 正解肢が単独最長のものが多すぎ({longest}/{len(flat)}) = 長さで当てられる")
    # 12. unitExact 衝突: 既存 '不定詞・動名詞' と相互に接頭辞にならないこと
    other = "不定詞・動名詞"
    if other.startswith(UNIT) or UNIT.startswith(other):
        errs.append(f"[G12] unit '{UNIT}' が既存 '{other}' と startsWith 衝突")
    # 16. ★他単元の topic 文字列を payload に含めない。bank は question_data 全体を
    #     LIKE '%<topic>%' で引くので、解説にうっかり「過去形」等を書くとその単元の
    #     取得枠にこの行が混ざる (unitExact が落とすので実害は出にくいが、非agg経路や
    #     unitExact 無しのカードをその part に足した瞬間に露出する)。
    OTHER_TOPICS = ["be動詞・一般動詞", "時制", "過去形", "未来形", "助動詞", "名詞・代名詞・冠詞",
                    "比較", "不定詞・動名詞", "分詞", "受動態", "現在完了", "関係代名詞",
                    "接続詞・前置詞", "会話表現", "長文読解"]
    payload = json.dumps(flat, ensure_ascii=False) + json.dumps(_wrap(flat), ensure_ascii=False)
    for t in OTHER_TOPICS:
        if t in payload:
            errs.append(f"[G16] 他単元の topic 文字列『{t}』が payload に含まれる (bank の LIKE に引っかかる)")
    # 13. 「答えはいつも to +原形」の形 tell の検出 (文法を知らなくても形だけで当たる)
    to_ans = sum(1 for q in flat if re.match(r"^[Tt]o [a-z]+$", q["_correct_text"]))
    if to_ans > len(flat) * 0.6:
        errs.append(f"[G13] 正解が「to +原形」の問題が多すぎ({to_ans}/{len(flat)}) = 形だけで当てられる")
    # 15. ★正解位置の「周期」tell: 分布が均等でも 0,1,2,3,0,1,2,3… だと位置だけで全問当たる。
    seq = [int(q["answer"]) for q in flat]
    step1 = sum(1 for i in range(1, len(seq)) if seq[i] == (seq[i - 1] + 1) % 4)
    if seq == [i % 4 for i in range(len(seq))]:
        errs.append("[G15] 正解位置が完全周期(0,1,2,3の繰り返し) = 位置だけで全問当てられる")
    elif step1 > (len(seq) - 1) * 0.5:
        errs.append(f"[G15] 正解位置が規則的すぎ(+1 遷移 {step1}/{len(seq) - 1})")
    # 14. 正解肢が単独最短の tell (逆方向)
    shortest = sum(1 for q in flat
                   if len(q["choices"][int(q["answer"])]) < min(
                       len(c) for i, c in enumerate(q["choices"]) if i != int(q["answer"])))
    if shortest > len(flat) * 0.6:
        errs.append(f"[G14] 正解肢が単独最短のものが多すぎ: {shortest}/{len(flat)}")
    return errs, dist, longest, to_ans, shortest


def main():
    flat = build_flat()
    errs, dist, longest, to_ans, shortest = gates(flat)
    # 行 (大問) に束ねる
    rows = []
    for i in range(0, len(flat), CHUNK):
        qs = []
        for q in flat[i:i + CHUNK]:
            qs.append({k: v for k, v in q.items() if not k.startswith("_")})
        rows.append({
            "passage": "",
            "subject": "英語",
            "univ_simulated": "公立高校入試(標準)",
            "year_simulated": None,
            "source": SOURCE,
            "format_type": UNIT,
            "questions": qs,
        })
    print(f"小問 {len(flat)} / 大問 {len(rows)} (CHUNK={CHUNK})")
    print(f"正解位置分布: {dist} (max-min<=1 ならOK)")
    print(f"tell 検査: 単独最長 {longest} / 単独最短 {shortest} / 正解が「to+原形」 {to_ans} (各 上限 {int(len(flat)*0.6)}件)")
    from collections import Counter
    print("用法内訳:", dict(Counter(q["_usage"] for q in flat)))
    if errs:
        # ★gate NG のときは build/ を書き換えない。書いてしまうと `build.py; insert.py --commit`
        #   と繋いだときに、落ちたはずの rows.json がそのまま本番へ入りうる。
        print("\n❌ GATE FAILED (build/ は更新していません)")
        for e in errs:
            print(" ", e)
        sys.exit(1)

    with open(os.path.join(OUT, "rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "flat.json"), "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=1)
    blind = [{"id": q["id"], "stem": q["stem"], "choices": q["choices"]} for q in flat]
    with open(os.path.join(OUT, "blind.json"), "w", encoding="utf-8") as f:
        json.dump(blind, f, ensure_ascii=False, indent=1)
    print("\n✅ 全 gate PASS → build/ を更新しました")


if __name__ == "__main__":
    main()
