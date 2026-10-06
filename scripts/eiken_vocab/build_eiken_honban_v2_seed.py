#!/usr/bin/env python3
"""🏅 英検 本番形式演習 (2級 第1〜15回・準1級 第1〜11回) を単元ドリルのシード v2 にする (2026-10-06 塾長
「デスクトップに英検の 2 級と準 1 級の問題演習があるので AI アプリの科目別ドリルに追加して」)。

書き出すもの (v1 と同じ形・同じ単元名。CEO の補充ボタンが v1 と v2 を続けて送り、取込済みは server が dedup で飛ばす):
  seed-data/eiken_vocab_pool_v2.json    … 大問1 (語彙・熟語) → 「2級 単語」「2級 句動詞・熟語」「準1級 単語」「準1級 句動詞・熟語」
  seed-data/eiken_reading_pool_v2.json  … 大問2 (長文空所補充) / 大問3 (内容一致) → 「… 長文空所補充」「… 長文 内容一致」
  大問4 (要約)・大問5 (英作文) は 4 択でないので入れない。

出所 (全部この塾の書き下ろし・過去問なし。リポジトリの外 = Desktop 側。無ければ落ちる):
  2級   EIKEN2_HONBAN_DIR/英検2級_本番形式演習_*_2026100?/_制作資料/{part1,reading}.json
        part1.items[n=1..17]: options・answer (1 始まり)・explanation・option_notes (選択肢ごと・語で始まる)・review・translation
          n=1..10 → 単語、n=11..17 → 句動詞・熟語 (答えが熟語。2026-10-06 に全 15 回で確認)
        reading.cloze[2] (2A/2B・paragraphs に (18) 形式の空所・items の stem は空)、reading.reading[2] (3A = Eメール・3B = 記事)
          items: options・answer (1 始まり)・explanation・evidence・option_notes (選択肢ごと)・review
  準1級 EIKEN_P1_HONBAN_DIR/英検準1級_本番形式演習_第N回_*/_制作資料/content.py (runpy で読む。回によって item() の引数が違うが、
        読み終えた後の P1 / P2_QUESTIONS / P3_QUESTIONS / READING_NOTES の形は全 9 回で同じ)
          P1[18]: options・answer (1 始まり)・point・meanings (選択肢ごと)・exclusions (選択肢ごと・正答は「正答。…」)・translation
            n=1..14 → 単語、n=15..18 → 句動詞・熟語
          P2A/P2B (空所 ( 19 )…)・P3A/P3B と *_TITLE / *_JP。P2_QUESTIONS {19..24: (options, answer)}、
          P3_QUESTIONS {25..31: (question, options, answer)}、READING_NOTES {19..31: options_jp・evidence・reason・wrong["2：…"]・review}
        _確認資料/最終検査.json の status が P1_PASS_STATUSES (PASS_FINAL / PASS_FINAL_INDEPENDENT_DELIVERY_CHECK = 別担当の配布前検査まで済んだ回)
        の回だけ使う (作業中の回を拾わない。知らない PASS* は止める)。

★印刷物との照合: 各回の「問題冊子.pdf」の文字列を前から順に読み、全設問の stem と選択肢がデータと同じ順に並んでいるかを確かめる
  (データを直した後に刷り直していない・刷るときに選択肢を並べ替えた、を拾う)。1 か所でもずれたら書き出さない。
★盲検: --blind DIR で答え・解説・全訳を伏せたファイルを書く。3 名が全員一致した問題だけを採る ([[exam-material-review-rule]])。
  盲検の結果で直す/落とすものは下の DROP_VOCAB / DROP_PASSAGE / DROP_Q に理由つきで書く。生の解答はコミットしない。

使い方:
  python3 scripts/eiken_vocab/build_eiken_honban_v2_seed.py
  python3 scripts/eiken_vocab/build_eiken_honban_v2_seed.py --blind /tmp/eiken_v2_blind
"""
import argparse
import collections
import glob
import hashlib
import importlib.util
import json
import os
import re
import runpy
import sys
from datetime import date

HOME = os.path.expanduser("~")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
E2_DIR = os.environ.get("EIKEN2_HONBAN_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/2級")
P1_DIR = os.environ.get("EIKEN_P1_HONBAN_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/準1級")
OUT_VOCAB = os.path.join(REPO, "seed-data", "eiken_vocab_pool_v2.json")
OUT_READING = os.path.join(REPO, "seed-data", "eiken_reading_pool_v2.json")
V1_VOCAB = os.path.join(REPO, "seed-data", "eiken_vocab_pool_v1.json")
V1_READING = os.path.join(REPO, "seed-data", "eiken_reading_pool_v1.json")

_spec = importlib.util.spec_from_file_location("eiken_reading_v1", os.path.join(os.path.dirname(__file__), "build_eiken_reading_seed.py"))
R1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R1)
norm_space, renumber_markers, renum_text, mask_email, circled, stem_cloze = (
    R1.norm_space, R1.renumber_markers, R1.renum_text, R1.mask_email, R1.circled, R1.stem_cloze)

BLANK = "(   )"
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
U2W, U2P, UPW, UPP = "2級 単語", "2級 句動詞・熟語", "準1級 単語", "準1級 句動詞・熟語"
U2C, U2R, UPC, UPR = "2級 長文空所補充", "2級 長文 内容一致", "準1級 長文空所補充", "準1級 長文 内容一致"
VOCAB_UNITS = (U2W, U2P, UPW, UPP)
READING_UNITS = (U2C, U2R, UPC, UPR)
_JA = "ぁ-んァ-ヶ一-龥"

# ── 盲検の結果を反映する場所 (キーは source / pid。理由は必ずコメントに) ─────────────────
DROP_VOCAB = {}          # {source: 理由}
DROP_PASSAGE = {}        # {pid: 理由}
# {pid: {設問番号(1始まり), ...}}  空所補充は空所を正解で埋めて付け直す
#   2026-10-06 盲検 (3 名・語彙 417 問 + 長文 96 本 327 問): 語彙 417 問・長文 326 問が全員一致 = 正解表どおり・指摘なし。
#   準1級 第5回 P2A 空所 1 (正解 justify an earlier expense) は 3 名とも「recover the ticket price も成立する」と指摘
#   (Going can seem to ( 1 ), even though the money is gone … は「お金を取り戻せる気がする」錯覚としても読める) → 全員一致だけ採用の原則で落とす。
DROP_Q = {"eikenp1-honban-r5:P2A": {1}}

# 準1級で使う回の最終検査の status (名前を決め打ち。2026-10-06 に別担当の配布前検査を経た回が _INDEPENDENT_DELIVERY_CHECK になった)
P1_PASS_STATUSES = {"PASS_FINAL", "PASS_FINAL_INDEPENDENT_DELIVERY_CHECK"}

# 本番に入った後で問題文が変わった問題 = 旧版の行を止める (CEO の 🏅 語彙ボタンが同期 /api/admin/grammar/sync で active=0 にする)。
#   止めるのは (source, 旧い問題文) の組だけ = 直した新版 (同じ source・新しい問題文) は止まらない。
#   2026-10-06: 作者の配布前の独立検査 (最終検査.json の correction) で直った分。正解の番号は変わっていない。
#     第7回 Q18「100枚から10枚へ減らす文脈にし、紛らわしい誤答を交換」(hold on to → do away with・問題文も変更)
#   ※第8回 Q7「別解になりうる誤答を交換」は問題文が同じなので止めずに同期で選択肢と解説をその場で直す (正解の文と位置は同じ)
RETIRED_VOCAB = [
    {"source": "eikenp1-honban-r7-18", "stem": "To reduce paper use while still providing a few copies for those who needed them, the office decided to (   ) printed handouts and send most documents electronically."},
]

# 2級 第1回の 3A だけ、出所に書き出し・結びの訳が無い (他の 14 回にはある) → ここで補う
EMAIL_JA_FILL = {"eiken2-honban-r1:3A": {"salutation_translation": "ボランティアの皆さま",
                                         "closing_translation": "よろしくお願いいたします。\nエミリー・ウォード"}}

problems = []


def rno(path):
    m = re.search(r"第(\d+)回", os.path.basename(str(path).rstrip("/")))   # 親フォルダ「01_本番形式演習_第1〜11回」を拾わない
    return int(m.group(1)) if m else 1


def round_dirs(base, pattern):
    """回フォルダ (base の直下か 1 段下)。2026-10-06 のデスクトップ整理で各回が「01_本番形式演習_第1〜N回」の中に入ったので、
    直下だけ探すと 1 回も見つからない。同じ回のフォルダが 2 つあれば (コピーの置き忘れ) どちらを使うか決められないので止める。"""
    ds = sorted({d for d in glob.glob(f"{base}/{pattern}") + glob.glob(f"{base}/*/{pattern}") if os.path.isdir(d)}, key=rno)
    by = collections.defaultdict(list)
    for d in ds:
        by[rno(d)].append(d)
    for r, v in by.items():
        if len(v) > 1:
            problems.append(f"同じ回のフォルダが {len(v)} つある (第{r}回): {v}")
    return ds


def clean_stem(s):
    s = norm_space(str(s).replace("\n", " "))
    s = re.sub(r"\(BLANK\)|\(\s*\)|_{3,}", BLANK, s)
    return s


def pdf_norm(path):
    import fitz
    with fitz.open(path) as d:
        t = "".join(p.get_text() for p in d)
    return re.sub(r"[^a-z0-9]", "", t.lower())


def key_of(s):
    return re.sub(r"[^a-z0-9]", "", str(s).replace("(BLANK)", " ").lower())


def check_booklet(pdf, seq, tag):
    """seq = [(n, stem or '', [options])] を問題冊子の文字列に前から順に当てる。"""
    if not os.path.exists(pdf):
        problems.append(f"{tag}: 問題冊子が無い {pdf}")
        return
    txt = pdf_norm(pdf)
    cur = 0
    for n, stem, opts in seq:
        if stem:
            k = key_of(re.sub(r"\(\s*\)|\(BLANK\)", " ", stem))[:60]
            i = txt.find(k, cur)
            if i < 0:
                problems.append(f"{tag} 問{n}: 問題冊子に stem が見つからない: {stem[:50]}")
                continue
            cur = i + len(k)
        for o in opts:
            k = key_of(o)
            i = txt.find(k, cur)
            if i < 0:
                problems.append(f"{tag} 問{n}: 問題冊子に選択肢が順に並んでいない: {o!r}")
                break
            cur = i + len(k)


def expl_vocab(aw, head, notes, review=None, translation=None):
    s = f"正解は {aw}。{norm_space(head)}"
    if review:
        s += f" {norm_space(review)}"
    if notes:
        s += " 誤答: " + " ／ ".join(norm_space(x) for x in notes if norm_space(x))
    if translation:
        s += f" 訳: {norm_space(str(translation).replace(chr(10), ' '))}"
    return s


def fmt_reading(choices, ans0, main, wrongs, evidence=None, review=None, jp=None):
    """v1 と同じ形: 正解 → 解説 → 【根拠】 → 【他の選択肢】 (+ 【復習】)。jp があれば選択肢の後に訳を付ける。"""
    def lab(i):
        return f"{circled(i)} {choices[i]}" + (f"（{norm_space(jp[i])}）" if jp and i < len(jp) and norm_space(jp[i]) else "")
    lines = [f"正解 {lab(ans0)}"]
    if norm_space(main):
        lines.append(norm_space(main))
    if evidence:
        lines.append(f"【根拠】{norm_space(evidence)}")
    lines.append("【他の選択肢】")
    for i in range(len(choices)):
        if i == ans0:
            continue
        r = norm_space(wrongs.get(i, ""))
        lines.append(lab(i) + (f" … {r}" if r else ""))
    if review:
        lines.append(f"【復習】{norm_space(review)}")
    return "\n".join(lines)


def passage(unit, title, body, body_ja, source, questions, pid):
    return {"pid": pid, "unit": unit, "level": "standard", "title": norm_space(title) or None,
            "body": mask_email(body.strip()), "body_ja": mask_email((body_ja or "").strip()) or None,
            "source": source[:60], "questions": questions}


def q(stem, choices, ans0, explanation, source):
    return {"stem": mask_email(norm_space(stem)), "choices": [mask_email(norm_space(c)) for c in choices], "answer": int(ans0),
            "explanation": mask_email(explanation.strip()), "source": source[:30]}


def paras_of(s):
    """content.py の本文 (段落は改行で区切る) → 段落のリスト。"""
    if isinstance(s, (list, tuple)):
        s = "\n".join(s)
    return [norm_space(x) for x in re.split(r"\n+", str(s)) if norm_space(x)]


# ───────────────────────── 2級 ─────────────────────────
def load_e2():
    vocab, passages = [], []
    dirs = [d for d in round_dirs(E2_DIR, "英検2級_本番形式演習_*") if re.search(r"_2026\d{4}$", d)]
    if len(dirs) != 15:
        problems.append(f"2級 本番形式演習が 15 回分でない ({len(dirs)}) at {E2_DIR}")
    for d in dirs:
        r = rno(d)
        tag = f"eiken2-honban-r{r}"
        src = f"{d}/_制作資料"
        p1 = json.load(open(f"{src}/part1.json", encoding="utf-8"))["items"]
        rd = json.load(open(f"{src}/reading.json", encoding="utf-8"))
        seq = []
        if [it["n"] for it in p1] != list(range(1, 18)):
            problems.append(f"{tag}: 大問1 の番号が 1〜17 でない")
        for it in p1:
            opts = [norm_space(o) for o in it["options"]]
            ai = int(it["answer"]) - 1
            aw = opts[ai]
            notes = [x for i, x in enumerate(it.get("option_notes") or []) if i != ai]
            if len(it.get("option_notes") or []) != 4:
                problems.append(f"{tag}-{it['n']}: option_notes が 4 つでない")
            elif not norm_space(it["option_notes"][ai]).lower().startswith(aw.lower()[:4]):
                problems.append(f"{tag}-{it['n']}: 正解の option_notes が正解語で始まらない → 添字を確認 ({aw} / {it['option_notes'][ai][:20]})")
            unit = U2W if it["n"] <= 10 else U2P
            vocab.append({"subject": "eiken", "unit": unit, "level": "standard", "stem": clean_stem(it["stem"]),
                          "choices": opts, "answer": ai,
                          "explanation": expl_vocab(aw, it.get("explanation", ""), notes, it.get("review"), it.get("translation")),
                          "source": f"{tag}-{it['n']}"})
            seq.append((it["n"], it["stem"], opts))
        # 大問2 空所補充
        for c in rd["cloze"]:
            body = "\n\n".join(norm_space(p) for p in c["paragraphs"])
            body, mapping = renumber_markers(body)
            ja = c.get("translation") or ""
            body_ja = "\n\n".join(norm_space(x) for x in ja) if isinstance(ja, list) else norm_space(ja)
            nos = [it["n"] for it in c["items"]]
            if sorted(mapping) != nos:
                problems.append(f"{tag} {c['id']}: 本文の空所 {sorted(mapping)} と設問 {nos} が合わない")
            qs = []
            for it in c["items"]:
                opts = [norm_space(o) for o in it["options"]]
                ai = int(it["answer"]) - 1
                k = mapping.get(it["n"])
                wr = {i: renum_text(x, mapping) for i, x in enumerate(it.get("option_notes") or []) if i != ai}
                qs.append(q(stem_cloze(k), opts, ai, fmt_reading(opts, ai, renum_text(it.get("explanation", ""), mapping), wr,
                                                                   evidence=renum_text(it.get("evidence") or "", mapping), review=renum_text(it.get("review") or "", mapping)), tag))
                seq.append((it["n"], "", opts))
            passages.append(passage(U2C, c.get("title"), body, body_ja, f"{tag} 大問2[{c['id']}]", qs, f"{tag}:{c['id']}"))
        # 大問3 内容一致 (A = Eメール)
        for a in rd["reading"]:
            paras = [norm_space(p) for p in a["paragraphs"]]
            ja_list = a.get("translation") or []
            ja_paras = [norm_space(x) for x in ja_list] if isinstance(ja_list, list) else [norm_space(ja_list)]
            title = a.get("title")
            a = {**a, **{k: v for k, v in (EMAIL_JA_FILL.get(f"{tag}:{a['id']}") or {}).items() if not a.get(k)}}
            if a.get("headers"):
                hd = [(k, re.sub(r"\s*<[^>]*>", "", v).strip()) for k, v in a["headers"]]
                header = "\n".join(f"{k}: {v}" for k, v in hd)
                subj = dict(hd).get("Subject", "")
                title = f"Eメール（{subj}）" if subj else "Eメール"
                closing = a.get("closing") or []
                body = "\n\n".join([header] + ([norm_space(a["salutation"])] if a.get("salutation") else []) + paras
                                   + (["\n".join(norm_space(x) for x in closing)] if closing else []))
                ht = a.get("header_translations") or {}
                hj = []
                for k, v in hd:
                    jv = ht.get(k) or v
                    if k == "Date" and not ht.get(k):   # 第1回は見出しの訳が無い → 日付だけ「11月6日」に直す
                        dm = re.match(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})$", v)
                        if dm:
                            jv = f"{MONTHS.index(dm.group(1)) + 1}月{dm.group(2)}日"
                    hj.append({"From": "送信者", "To": "宛先", "Date": "日付", "Subject": "件名"}.get(k, k) + "：" + jv)
                body_ja = "\n\n".join(["\n".join(hj)] + ([norm_space(a["salutation_translation"])] if a.get("salutation_translation") else [])
                                      + ja_paras + ([str(a["closing_translation"]).strip()] if a.get("closing_translation") else []))
            else:
                body = "\n\n".join(paras)
                body_ja = "\n\n".join(ja_paras)
            qs = []
            for it in a["items"]:
                opts = [norm_space(o) for o in it["options"]]
                ai = int(it["answer"]) - 1
                wr = {i: x for i, x in enumerate(it.get("option_notes") or []) if i != ai}
                qs.append(q(it["stem"], opts, ai, fmt_reading(opts, ai, it.get("explanation", ""), wr,
                                                              evidence=it.get("evidence"), review=it.get("review")), tag))
                seq.append((it["n"], it["stem"], opts))
            passages.append(passage(U2R, title, body, body_ja, f"{tag} 大問3[{a['id']}]", qs, f"{tag}:{a['id']}"))
        pdfs = glob.glob(f"{d}/*問題冊子.pdf")
        check_booklet(pdfs[0] if pdfs else f"{d}/問題冊子.pdf", sorted(seq, key=lambda x: x[0]), tag)
    return vocab, passages


# ───────────────────────── 準1級 ─────────────────────────
def load_p1():
    vocab, passages = [], []
    dirs = round_dirs(P1_DIR, "英検準1級_本番形式演習_第*回_*")
    used = []
    for d in dirs:
        r = rno(d)
        tag = f"eikenp1-honban-r{r}"
        fin = f"{d}/_確認資料/最終検査.json"
        st = json.load(open(fin, encoding="utf-8")).get("status") if os.path.exists(fin) else None
        if st not in P1_PASS_STATUSES:   # 名前を決め打ちで許す (PASS_FINAL_PENDING のような作業中の印を黙って拾わない)
            if str(st or "").startswith("PASS"):
                problems.append(f"準1級 第{r}回: 最終検査の status {st!r} を知らない (使ってよい回なら P1_PASS_STATUSES に足す)")
            print(f"  (準1級 第{r}回は 最終検査 {st} → 使わない)")
            continue
        used.append(r)
        cwd = os.getcwd()
        try:
            os.chdir(f"{d}/_制作資料")
            g = runpy.run_path(f"{d}/_制作資料/content.py")
        finally:
            os.chdir(cwd)
        seq = []
        if [it["n"] for it in g["P1"]] != list(range(1, 19)):
            problems.append(f"{tag}: 大問1 の番号が 1〜18 でない")
        for it in g["P1"]:
            opts = [norm_space(o) for o in it["options"]]
            ai = int(it["answer"]) - 1
            aw = opts[ai]
            mean = it.get("meanings") or [""] * 4
            exc = it.get("exclusions") or [""] * 4
            if not str(exc[ai]).startswith("正答"):
                problems.append(f"{tag}-{it['n']}: 正解の exclusions が「正答」で始まらない → 添字を確認")
            notes = [f"{opts[i]}（{norm_space(mean[i])}）：{norm_space(exc[i])}" for i in range(4) if i != ai]
            head = f"（{norm_space(mean[ai])}）。{norm_space(it.get('point', ''))}"
            unit = UPW if it["n"] <= 14 else UPP
            vocab.append({"subject": "eiken", "unit": unit, "level": "standard", "stem": clean_stem(it["stem"]),
                          "choices": opts, "answer": ai,
                          "explanation": expl_vocab(aw, head, notes, None, it.get("translation")).replace(f"正解は {aw}。（", f"正解は {aw}（", 1),
                          "source": f"{tag}-{it['n']}"})
            seq.append((it["n"], it["stem"], opts))
        notes = g["READING_NOTES"]

        def wrongs_of(no, ai):
            out = {}
            for w in notes[no].get("wrong") or []:
                m = re.match(r"^\s*([1-4])\s*[：:]\s*(.*)$", str(w), re.S)
                if not m:
                    problems.append(f"{tag} 問{no}: wrong の先頭に番号が無い: {str(w)[:30]}")
                    continue
                i = int(m.group(1)) - 1
                if i == ai:
                    problems.append(f"{tag} 問{no}: wrong に正解の番号 {i + 1} がある → 添字を確認")
                out[i] = m.group(2)
            if sorted(out) != sorted(set(range(4)) - {ai}):
                problems.append(f"{tag} 問{no}: wrong の番号 {sorted(i + 1 for i in out)} が誤答 3 つと合わない (正解 {ai + 1})")
            return out
        for key, nos in (("P2A", (19, 20, 21)), ("P2B", (22, 23, 24))):
            body, mapping = renumber_markers("\n\n".join(paras_of(g[key])))
            body_ja = renum_text("\n\n".join(paras_of(g.get(key + "_JP") or "")), mapping)
            if sorted(mapping) != list(nos):
                problems.append(f"{tag} {key}: 本文の空所 {sorted(mapping)} が {nos} でない")
            qs = []
            for no in nos:
                opts, ans = g["P2_QUESTIONS"][no]
                opts = [norm_space(o) for o in opts]
                ai = int(ans) - 1
                nt = notes[no]
                qs.append(q(stem_cloze(mapping.get(no)), opts, ai,
                            fmt_reading(opts, ai, renum_text(nt.get("reason", ""), mapping), {i: renum_text(w, mapping) for i, w in wrongs_of(no, ai).items()},
                                        evidence=renum_text(nt.get("evidence") or "", mapping), review=renum_text(nt.get("review") or "", mapping), jp=nt.get("options_jp")), tag))
                seq.append((no, "", opts))
            passages.append(passage(UPC, g.get(key + "_TITLE"), body, body_ja, f"{tag} 大問2[{key[-1]}]", qs, f"{tag}:{key}"))
        for key, nos in (("P3A", (25, 26, 27)), ("P3B", (28, 29, 30, 31))):
            body = "\n\n".join(paras_of(g[key]))
            body_ja = "\n\n".join(paras_of(g.get(key + "_JP") or ""))
            qs = []
            for no in nos:
                qtext, opts, ans = g["P3_QUESTIONS"][no]
                opts = [norm_space(o) for o in opts]
                ai = int(ans) - 1
                nt = notes[no]
                qs.append(q(qtext, opts, ai, fmt_reading(opts, ai, nt.get("reason", ""), wrongs_of(no, ai),
                                                         evidence=nt.get("evidence"), review=nt.get("review"), jp=nt.get("options_jp")), tag))
                seq.append((no, qtext, opts))
            passages.append(passage(UPR, g.get(key + "_TITLE"), body, body_ja, f"{tag} 大問3[{key[-1]}]", qs, f"{tag}:{key}"))
        pdfs = glob.glob(f"{d}/*問題冊子.pdf")
        check_booklet(pdfs[0] if pdfs else f"{d}/問題冊子.pdf", sorted(seq, key=lambda x: x[0]), tag)
    return vocab, passages, used


# ───────────────────────── 検査 ─────────────────────────
def drop_questions(p, qnos):
    R1.drop_questions(p, qnos)


def validate_vocab(qs, v1_stems):
    seen = {}
    for x in qs:
        src = x["source"]
        if x["stem"].count(BLANK) != 1:
            problems.append(f"{src}: 空所が {x['stem'].count(BLANK)} 個: {x['stem'][:80]}")
        if len(x["choices"]) != 4 or len(set(c.lower() for c in x["choices"])) != 4 or any(not c for c in x["choices"]):
            problems.append(f"{src}: 選択肢が 4 つ相異でない {x['choices']}")
        if not (0 <= x["answer"] <= 3):
            problems.append(f"{src}: answer 範囲外")
        elif x["choices"][x["answer"]].lower() not in x["explanation"].lower():
            problems.append(f"{src}: 解説に正解語が無い")
        if re.search(rf"[①②③④]|選択肢\s*[1-4１-４]|\{{\s*[1-4]\s*:|(?<=[{_JA}])[1-4](?=のみ|だけ|が(?:文意|適切|自然|正解)|[。、]|\s|$)", x["explanation"]):
            problems.append(f"{src}: 解説に番号参照: {re.search(r'.{0,12}(?:[①②③④]|選択肢|[1-4](?=のみ|だけ)).{0,12}', x['explanation'])}")
        k = x["stem"].lower()
        if k in seen:
            problems.append(f"{src}: stem が {seen[k]} と重複")
        if k in v1_stems:
            problems.append(f"{src}: stem が v1 シードと重複")
        seen[k] = src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", default=None)
    a = ap.parse_args()
    v2, p2 = load_e2()
    vp, pp, used = load_p1()
    vocab = [x for x in v2 + vp if x["source"] not in DROP_VOCAB]
    passages = []
    for p in p2 + pp:
        if p["pid"] in DROP_PASSAGE:
            continue
        if p["pid"] in DROP_Q:
            drop_questions(p, DROP_Q[p["pid"]])
        passages.append(p)
    v1_stems = {x["stem"].strip().lower() for x in json.load(open(V1_VOCAB, encoding="utf-8"))["questions"]}
    validate_vocab(vocab, v1_stems)
    R1.problems.clear()
    R1.validate(passages)
    problems.extend(R1.problems)
    v1_hash = {hashlib.sha256(re.sub(r"\s+", " ", p["body"]).lower().encode()).hexdigest()[:16]
               for p in json.load(open(V1_READING, encoding="utf-8"))["passages"]}
    for p in passages:
        if hashlib.sha256(re.sub(r"\s+", " ", p["body"]).lower().encode()).hexdigest()[:16] in v1_hash:
            problems.append(f"{p['pid']}: 本文が v1 シードと重複")
    vu = collections.Counter(x["unit"] for x in vocab)
    pos = collections.defaultdict(collections.Counter)
    for x in vocab:
        pos[x["unit"]][x["answer"]] += 1
    ru = {u: [0, 0] for u in READING_UNITS}
    rpos = collections.defaultdict(collections.Counter)
    for p in passages:
        ru[p["unit"]][0] += 1
        ru[p["unit"]][1] += len(p["questions"])
        for qq in p["questions"]:
            rpos[p["unit"]][qq["answer"]] += 1
    print("語彙:", len(vocab), dict(vu))
    for u in VOCAB_UNITS:
        print("  正解位置", u, dict(sorted(pos[u].items())))
    print("長文:", {u: f"本文{n}本/設問{m}問" for u, (n, m) in ru.items()})
    for u in READING_UNITS:
        print("  正解位置", u, dict(sorted(rpos[u].items())))
    print("準1級で使った回:", used)
    if problems:
        print(f"\n❌ 検査 NG {len(problems)} 件 (書き出しません):")
        for x in problems[:120]:
            print("  -", x)
        sys.exit(1)
    if a.blind:
        os.makedirs(a.blind, exist_ok=True)
        bv = [{"stem": x["stem"], "choices": x["choices"]} for x in vocab]
        json.dump(bv, open(os.path.join(a.blind, "blind_vocab.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump({x["stem"]: x["choices"][x["answer"]] for x in vocab},
                  open(os.path.join(a.blind, "key_vocab.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        br, kr = [], {}
        for i, p in enumerate(passages, 1):
            pid = f"P{i:03d}"
            br.append({"pid": pid, "unit": p["unit"], "title": p["title"], "body": p["body"],
                       "questions": [{"qid": f"{pid}-{j}", "stem": qq["stem"], "choices": qq["choices"]} for j, qq in enumerate(p["questions"], 1)]})
            for j, qq in enumerate(p["questions"], 1):
                kr[f"{pid}-{j}"] = {"src": p["pid"], "answer": qq["choices"][qq["answer"]]}
        json.dump(br, open(os.path.join(a.blind, "blind_reading.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(kr, open(os.path.join(a.blind, "key_reading.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n盲検用: {a.blind}/ (語彙 {len(bv)} 問・長文 {len(br)} 本)")
        return
    today = date.today().isoformat()
    meta = {"name": "eiken_vocab_pool_v2", "created": today, "subject": "eiken", "units": {u: vu.get(u, 0) for u in VOCAB_UNITS},
            "sources": ["2級: 本番形式演習 第1〜15回 大問1 (Desktop/📚 教材/英語/04_英検/2級/01_本番形式演習_第1〜15回/英検2級_本番形式演習_*/_制作資料/part1.json)",
                        f"準1級: 本番形式演習 第{used[0]}〜{used[-1]}回 大問1 (Desktop/📚 教材/英語/04_英検/準1級/01_本番形式演習_第1〜N回/英検準1級_本番形式演習_第N回_*/_制作資料/content.py の P1)"],
            "blind_review": BLIND_NOTE,
            "retired_sources": [{"source": x["source"], "stem": x["stem"]} for x in RETIRED_VOCAB],
            "note": "全部トリリオンAI塾の書き下ろし (過去問なし)。v1 と同じ単元名・形式。解説は値で書く (①や『選択肢2』を書かない)。level は全問 standard。"}
    os.makedirs(os.path.dirname(OUT_VOCAB), exist_ok=True)
    with open(OUT_VOCAB, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": meta, "questions": vocab}, ensure_ascii=False, indent=1) + "\n")
    out = {"subject": "eiken", "version": "v2", "generated": today,
           "note": f"英検 長文ドリル v2 (大問2 長文空所補充 / 大問3 内容一致)。出所は 本番形式演習 2級 第1〜15回・準1級 第{used[0]}〜{used[-1]}回。"
                   "全部この塾の書き下ろし。空所は ( 1 ) ( 2 ) … に正規化済み。" + BLIND_NOTE,
           "units": {u: {"passages": ru[u][0], "questions": ru[u][1]} for u in READING_UNITS},
           "passages": [{k: v for k, v in p.items() if k != "pid"} for p in passages]}
    with open(OUT_READING, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"✅ {OUT_VOCAB}: {len(vocab)} 問")
    print(f"✅ {OUT_READING}: 本文 {len(passages)} 本 / 設問 {sum(len(p['questions']) for p in passages)} 問")


BLIND_NOTE = ("盲検 (2026-10-06): 正解を伏せた独立ソルバー 3 名が 語彙 417 問・長文 327 問を解き、語彙は全問・長文は 326 問が全員一致"
              "(正解表どおり・指摘なし)。残る 1 問 (準1級 第5回 大問2[A] 空所 1) は 3 名とも別解ありと指摘 → DROP_Q で落とした。"
              "追加 (同日): 準1級 第10・11回 (語彙 36 問・長文 本文 8 本 26 問) と、作者の配布前検査で直った 第7回 語彙18・第8回 語彙7 を"
              "同じく 3 名で盲検 → 語彙 38 問・長文 26 問とも全員一致・指摘なし。生の解答はコミットしない。")

if __name__ == "__main__":
    main()
