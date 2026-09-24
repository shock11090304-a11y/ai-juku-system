#!/usr/bin/env python3
"""🏅 英検 語彙ドリルのシード (seed-data/eiken_vocab_pool_v1.json) を作る (2026-09-24)。

入力 (★リポジトリ外の教材。無い環境ではその部分を飛ばさず落ちる = 黙って欠けたシードを書かない):
  準1級 本番形式演習 第1弾/第2弾 大問1: ~/Desktop/📚 教材/英語/_生成元_英語教材_202609/data/eikenp1_mock{,2}/part1/S1..S6.json
  準1級 完全模試 全3回 大問1        : ~/Desktop/英検準1級_完全模試_リスニング除外_全3回_20260923/_制作ソース/pre1_set{1,2,3}_data.py の P1
  2級 対策問題集 Vol.1 大問1        : scripts/eiken_2kyu/data/part1_vocab.json (リポジトリ内・構造化)
  2級 対策問題集 Vol.2 大問1        : ~/Desktop/📚 教材/英語/04_英検/2級/英検2級_対策問題集_Vol2.pdf (生成元なし → PyMuPDF でテキスト抽出)
  2級 完全模試 全3回 大問1          : ~/Desktop/📚 教材/英語/04_英検/模擬試験/2級/英検2級_完全模試_リスニング除外_全3回_20260922/
                                       第N回/問題冊子 (本文・活用形の選択肢) + 採点・解説冊子 (正答・ポイント・和訳・意味)
出力: seed-data/eiken_vocab_pool_v1.json  {_meta, questions:[{subject:'eiken', unit, level:'standard', stem, choices, answer(0始まり), explanation, source}]}
検査: 空所ちょうど 1 つ・4 択相異・正解語 = choices[answer]・解説に正解語を含む・番号参照なし・stem 一意。1 件でも落ちたら書かない。
形式ゲート: scripts/check_eiken_vocab_seed.py (run_all_gates.py が拾う)。

★取り込む前の工程 (2026-09-24 に実施): 正解を伏せた独立ソルバー 3 名が全 401 問を解いて全問一致。指摘 3 件を
  OVERRIDES / DROP で反映して 400 問。生の解答ファイルは手元だけ (scripts/**/blind/ は .gitignore の方針で入れない)。
  残る記録はこの OVERRIDES / DROP と seed の _meta.blind_review。
  選択肢や本文を触ったら盲検をやり直すこと (英検準1級の本番形式演習で「ダミーを直したら 11 問に複数正解が再混入」した実測あり)。

実行:  python3 scripts/eiken_vocab/build_eiken_seed.py            # 既定の場所から読む
       EIKEN_P1_MOCK_DIR=... 等の環境変数で入力の場所を変えられる
"""
import collections
import glob
import importlib.util
import io
import json
import os
import re
import sys
import unicodedata

HOME = os.path.expanduser("~")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = os.environ.get("EIKEN_P1_MOCK_DIR", f"{HOME}/Desktop/📚 教材/英語/_生成元_英語教材_202609/data")
P1MOCK = os.environ.get("EIKEN_P1_ZENMOSHI_DIR", f"{HOME}/Desktop/英検準1級_完全模試_リスニング除外_全3回_20260923/_制作ソース")
WB1_JSON = os.path.join(REPO, "scripts", "eiken_2kyu", "data", "part1_vocab.json")
WB2_PDF = os.environ.get("EIKEN2_WB2_PDF", f"{HOME}/Desktop/📚 教材/英語/04_英検/2級/英検2級_対策問題集_Vol2.pdf")
MOCK2_DIR = os.environ.get("EIKEN2_MOCK_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/模擬試験/2級/英検2級_完全模試_リスニング除外_全3回_20260922")
OUT = os.path.join(REPO, "seed-data", "eiken_vocab_pool_v1.json")

CIRC = {"①": 0, "②": 1, "③": 2, "④": 3}
BLANK = "(   )"
U_2W, U_2P, U_P1W, U_P1P = "2級 単語", "2級 句動詞・熟語", "準1級 単語", "準1級 句動詞・熟語"
problems = []

# ── ブラインド 3 名 (2026-09-24) の指摘の反映 ──
OVERRIDES = {
    # 準1級 完全模試 第2回 (18): 文は過去形・主語は複数なのに正解語が 3 単現 → 過去形に (他の 3 択は過去形)
    "eikenp1-mock-202609-r2-18": {"choices": ["fell short of", "made up for", "looked past", "faced up to"],
                                  "explanation_replace": [("正解は faces up to", "正解は faced up to")]},
    # 準1級 完全模試 第2回 (15): 4 択が現在形なのに後半が過去形 → 4 択を過去形に。後半の backed が正解のヒントになるので voted for に
    "eikenp1-mock-202609-r2-15": {"choices": ["backed up", "played down", "ruled out", "went against"],
                                  "stem_replace": [("several lawmakers then backed the proposal", "several lawmakers then voted for the proposal")],
                                  "explanation_replace": [("正解は backs up", "正解は backed up")]},
    # 2級 対策問題集 Vol.2: PDF テキストで英単語が密着した箇所
    "eiken2-workbook-vol2-7": {"explanation_replace": [("beadmitted", "be admitted")]},
    "eiken2-workbook-vol2-21": {"explanation_replace": [("availableonline", "available online")]},
    # 2級 対策問題集 Vol.2 (22): 別冊への参照「(Vol.1 第40問)」はドリルでは意味がない
    "eiken2-workbook-vol2-22": {"explanation_replace": [("(Vol.1 第40問)", "")]},
}
DROP = {
    # 2級 対策問題集 Vol.1 (39): keep in touch が正解だが「catch up with … by email」も口語では通る (3 名とも指摘) → 外す
    "eiken2-workbook-vol1-39",
}


def norm_space(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def clean_stem(s):
    s = norm_space(s)
    s = re.sub(r"\(\s*\)|_{3,}", BLANK, s)      # "( )" / "(  )" / "_______" → 統一
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)        # 空所の直後の句読点の前の空白を詰める
    return s


_JA = "ぁ-んァ-ヶ一-龥々〆ヵヶ"


def tidy_ja(s):
    """PDF の行折り返しで日本語の途中に入った空白を消す (「遠すぎ たからだ」→「遠すぎたからだ」)。英語まわりは触らない。"""
    s = norm_space(s)
    # 日本語の文字 (と読点) の直後の空白だけを消す。「。」「:」の後の空白はラベルの区切りなので残す
    return re.sub(rf"(?<=[{_JA}、])\s+(?=[{_JA}])", "", s)


def pdf_text(path):
    import fitz  # PyMuPDF
    d = fitz.open(path)
    return "".join(f"\n<<<PAGE {i + 1}>>>\n" + p.get_text() for i, p in enumerate(d))


# ───────── 準1級 本番形式演習 (構造化) ─────────
def load_p1():
    out = []
    for vol, tag in (("eikenp1_mock", "eikenp1-mock-vol1"), ("eikenp1_mock2", "eikenp1-mock-vol2")):
        files = sorted(glob.glob(f"{GEN}/{vol}/part1/S*.json"), key=lambda p: int(re.search(r"S(\d+)", p).group(1)))
        if len(files) != 6:
            problems.append(f"{tag}: part1 の S*.json が 6 本でない ({len(files)}) at {GEN}/{vol}/part1"); continue
        for f in files:
            setno = int(re.search(r"S(\d+)", f).group(1))
            for q in json.load(open(f, encoding="utf-8")):
                unit = U_P1P if q.get("pos") == "句動詞" else U_P1W
                wrong = [re.sub(r'"([A-Za-z][A-Za-z \'\-]*)"', r"\1", w) for w in q.get("why_wrong", []) if w]
                expl = (f"正解は {q['target']}（{q.get('pos','')}：{q.get('meaning_ja','')}）。{q['why']}"
                        + (" 誤答: " + " ／ ".join(wrong) if wrong else "")
                        + (f" 訳: {q['translation']}" if q.get("translation") else ""))
                out.append({"subject": "eiken", "unit": unit, "level": "standard",
                            "stem": clean_stem(q["stem"]), "choices": [norm_space(c) for c in q["choices"]],
                            "answer": int(q["answer"]), "explanation": tidy_ja(expl),
                            "source": f"{tag}-S{setno}-{q['no']}"})
    return out


# ───────── 準1級 完全模試 全3回 (制作ソース pre1_set{1,2,3}_data.py の P1) ─────────
def _format_notes(notes, opts, ai):
    """option_notes → 「語 = 意味 ／ …」の形。番号 (位置) は書かない。"""
    if isinstance(notes, dict):
        # {1:'…', 2:'正答。…', …}: 正答の項は point と同文なので省き、値だけ並べる (値は語を名指ししている)
        vals = []
        for k, v in sorted(notes.items(), key=lambda kv: int(kv[0])):
            if int(k) - 1 == ai:
                continue
            vals.append(norm_space(v))
        return " ／ ".join(v for v in vals if v)
    s = norm_space(notes)
    # 「adverse 有害な / abundant 豊富な / …。説明」 → 「adverse = 有害な ／ abundant = 豊富な ／ …。説明」
    head, sep, tail = s.partition("。")
    parts = [p.strip() for p in head.split(" / ")]
    if len(parts) == 4:
        conv = []
        for p in parts:
            m = re.match(r"^([A-Za-z][A-Za-z '\-]*?)\s+([^A-Za-z\s].*)$", p)   # 英語部分は句動詞 (call off) をまるごと取る
            if not m:
                conv = None; break
            conv.append(f"{m.group(1)} = {m.group(2)}")
        if conv:
            s = " ／ ".join(conv) + (sep + tail if sep else "")
    # 説明文に残った裸の選択肢番号 (「…2のみ適切」) は語に置き換える (生徒は番号を見ない)
    s = re.sub(rf"(?<=[{_JA}])([1-4])(?=のみ|だけ|が(?:文意|適切|自然|正解)|[。、]|\s|$)", lambda m: f" {opts[int(m.group(1)) - 1]} ", s)
    s = re.sub(r"\s+([。、])", r"\1", norm_space(s))
    return s


def load_p1_mock():
    out = []
    for r in (1, 2, 3):
        path = f"{P1MOCK}/pre1_set{r}_data.py"
        if not os.path.exists(path):
            problems.append(f"eikenp1-mock-202609-r{r}: {path} が無い"); continue
        spec = importlib.util.spec_from_file_location(f"pre1_set{r}_data", path)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        for q in m.P1:
            opts = [norm_space(o) for o in q["options"]]
            ai = int(q["answer"]) - 1                      # データは 1 始まり (answer=2 → options[1])
            if not (0 <= ai <= 3):
                problems.append(f"eikenp1-mock-202609-r{r}-{q['n']}: answer 範囲外 {q['answer']}"); continue
            aw = opts[ai]
            stem_word = re.sub(r"(ed|ing|es|s|d)$", "", aw.split(" ")[0].lower())[:4]
            if stem_word and stem_word not in (q.get("point") or "").lower():
                problems.append(f"eikenp1-mock-202609-r{r}-{q['n']}: point に正解語 {aw!r} の語幹が無い → 1始まり/0始まりを確認")
            unit = U_P1P if any(" " in o for o in opts) else U_P1W
            expl = (f"正解は {aw}。{q.get('point','')} 選択肢の意味: {_format_notes(q.get('option_notes', ''), opts, ai)}"
                    + (f" 訳: {q['translation']}" if q.get("translation") else ""))
            out.append({"subject": "eiken", "unit": unit, "level": "standard", "stem": clean_stem(q["stem"]),
                        "choices": opts, "answer": ai, "explanation": tidy_ja(expl),
                        "source": f"eikenp1-mock-202609-r{r}-{q['n']}"})
    return out


# ───────── 2級 対策問題集 Vol.1 (リポジトリ内の構造化データ) ─────────
def load_wb1_json():
    d = json.load(open(WB1_JSON, encoding="utf-8"))
    items = (d.get("items") or d.get("questions")) if isinstance(d, dict) else d
    if not isinstance(items, list) or len(items) != 40:
        problems.append(f"eiken2-workbook-vol1: part1_vocab.json が 40 問でない"); return []
    out = []
    for q in items:
        n = int(re.sub(r"\D", "", q["id"]))
        ai = int(q["answer"])
        aw = q["choices"][ai]
        dist = q.get("distractors_ja") or {}
        wrong = q.get("why_others_wrong") or {}
        wrong_txt = " ／ ".join(f"{w}（{dist.get(w, '')}）＝ {wrong.get(w, '')}".replace("（）", "") for w in q["choices"] if w != aw)
        expl = f"正解は {aw}（{q.get('gloss_ja', '')}）。{q.get('why_correct', '')} 誤答: {wrong_txt}"
        unit = U_2P if (q.get("level") == "句動詞" or n >= 31) else U_2W
        out.append({"subject": "eiken", "unit": unit, "level": "standard", "stem": clean_stem(q["sentence"]),
                    "choices": [norm_space(c) for c in q["choices"]], "answer": ai, "explanation": tidy_ja(expl),
                    "source": f"eiken2-workbook-vol1-{n}", "_ans_word": q.get("target_word")})
    return out


# ───────── 2級 対策問題集 Vol.2 (PDF テキスト) ─────────
def parse_workbook(txt, tag):
    lines = txt.split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.startswith("大問1") and "空所補充" in l)
    i1 = next(i for i in range(i0 + 1, len(lines)) if lines[i].startswith("大問2"))
    blocks = {}; cur = None; buf = []

    def flush():
        if cur is not None:
            blocks[cur] = buf[:]
    for l in lines[i0 + 1:i1]:
        if re.fullmatch(r"\d{1,2}", l.strip()) and 1 <= int(l.strip()) <= 40 and (cur is None or int(l.strip()) == cur + 1):
            flush(); cur = int(l.strip()); buf = []
        elif cur is not None:
            buf.append(l)
    flush()
    qs = {}
    for no, bl in blocks.items():
        choice_lines = [l for l in bl if l.strip()[:1] in CIRC]
        first_choice = next((i for i, l in enumerate(bl) if l.strip()[:1] in CIRC), len(bl))
        body = [l for l in bl[:first_choice] if not l.startswith("<<<PAGE") and l.strip() not in ("問題編", "次の各文の空所に入れるのに最も適切なものを①〜④から一つ選びなさい。")]
        while body and body[-1].strip() == "":            # 末尾の空白行 (ページ境界の残り) は空所ではない
            body.pop()
        parts = []; blanks = 0; pending_gap = False
        for l in body:                                     # 空所 = 行末の空白 / 空白だけの行 (連続は 1 つ)
            if l.strip() == "":
                if not pending_gap:
                    parts.append(BLANK); blanks += 1; pending_gap = True
                continue
            if l != l.rstrip():
                parts.append(l.rstrip())
                if not pending_gap:
                    parts.append(BLANK); blanks += 1; pending_gap = True
                continue
            parts.append(l.strip()); pending_gap = False
        stem = clean_stem(" ".join(parts))
        if blanks == 0 and (stem.startswith(",") or stem[:1].islower()):   # 文頭の空所は PDF テキストで消える → 補う
            stem = BLANK + (" " if not stem.startswith(",") else "") + stem; blanks = 1
        choices = [norm_space(m.group(2)) for m in (re.match(r"^([①②③④])\s*(.+)$", cl.strip()) for cl in choice_lines) if m]
        qs[no] = {"stem": stem, "choices": choices}
    a0 = next(i for i, l in enumerate(lines) if l.startswith("大問1（語彙"))
    a1 = next(i for i in range(a0 + 1, len(lines)) if lines[i].startswith("大問2（"))
    nums = [int(l.strip()) for l in lines[a0 + 1:a1] if re.fullmatch(r"\d{1,2}", l.strip())]
    syms = [CIRC[l.strip()] for l in lines[a0 + 1:a1] if l.strip() in CIRC]
    if len(nums) != len(syms) or len(nums) != 40:
        problems.append(f"{tag}: 解答表の数が合わない nums={len(nums)} syms={len(syms)}")
    answers = dict(zip(nums, syms))
    e0 = next(i for i, l in enumerate(lines) if l.startswith("大問1") and "解説" in l)
    e1 = next(i for i in range(e0 + 1, len(lines)) if lines[i].startswith("大問2"))
    expl = {}; cur = None; buf = []
    for l in lines[e0 + 1:e1]:
        m = re.match(r"^(\d{1,2}) 正解 ([①②③④])\s*(.+)$", l.strip())
        if m:
            if cur is not None:
                expl[cur] = buf
            cur = int(m.group(1)); buf = [("HEAD", CIRC[m.group(2)], norm_space(m.group(3)))]
        elif cur is not None and not l.startswith("<<<PAGE") and l.strip() and "対策問題集" not in l and not re.fullmatch(r"\d+", l.strip()):
            buf.append(l.rstrip())
    if cur is not None:
        expl[cur] = buf
    out = []
    for no in range(1, 41):
        q = qs.get(no); e = expl.get(no)
        if not q or not e or no not in answers:
            problems.append(f"{tag} Q{no}: 問題/解説/解答のどれかが無い"); continue
        head = e[0]; ans_sym, ans_word = head[1], head[2]
        if answers[no] != ans_sym:
            problems.append(f"{tag} Q{no}: 解答表 {answers[no]} と解説 {ans_sym} が食い違う")
        body_lines = [l for l in e[1:] if l.strip() not in ("単語", "句動詞", "イディオム")]
        joined = []
        for l in body_lines:
            l = l.strip()
            if joined and not re.search(r"[。．.!?」』)）]$", joined[-1]) and not re.match(r"^(訳|語法|関連|イディオム|[A-Za-z][A-Za-z '\-]*[（(＝])", l):
                joined[-1] += l
            else:
                joined.append(l)
        keep = []
        for l in joined:
            if l.startswith("関連"):
                continue                                   # 関連語は長いので省く (語法・誤答の理由は残す)
            m2 = re.match(r"^(訳|語法|イディオム|単語|句動詞)(?![:：\s])(.+)$", l)   # PDF で密着したラベルに区切りを補う
            if m2:
                l = f"{m2.group(1)}: {m2.group(2)}"
            keep.append(l)
        text = tidy_ja("正解は " + ans_word + "。 " + " ".join(keep))
        out.append({"subject": "eiken", "unit": U_2P if no >= 31 else U_2W, "level": "standard",
                    "stem": q["stem"], "choices": q["choices"], "answer": ans_sym, "explanation": text,
                    "source": f"{tag}-{no}", "_ans_word": ans_word})
    return out


# ───────── 2級 完全模試 全3回 (問題冊子 + 採点・解説冊子の PDF テキスト) ─────────
def parse_mock_booklet(txt):
    """問題冊子: '(N)' → 本文行 → '1' 語 '2' 語 '3' 語 '4' 語 (活用形のまま)。(18) 以降は大問2/3 なので 1〜17 だけ。"""
    junk = re.compile(r"^(Grade 2|•\s*\d+\s*•|オリジナル模試・非公式)$")
    lines = [l for l in txt.split("\n") if not l.startswith("<<<PAGE") and not junk.match(l.strip())]
    out = {}; cur = None; buf = []

    def flush():
        if cur is not None and 1 <= cur <= 17:
            out[cur] = buf[:]
    for l in lines:
        m = re.fullmatch(r"\((\d{1,2})\)", l.strip())
        if m:
            flush(); cur = int(m.group(1)); buf = []
        elif cur is not None:
            buf.append(l.strip())
    flush()
    res = {}
    for no, bl in out.items():
        stem_lines = []; choices = []; i = 0
        while i < len(bl):
            if bl[i] in ("1", "2", "3", "4") and i + 1 < len(bl) and len(choices) == int(bl[i]) - 1:
                choices.append(norm_space(bl[i + 1])); i += 2; continue
            if not choices and bl[i]:
                stem_lines.append(bl[i])
            i += 1
        res[no] = {"stem": clean_stem(" ".join(stem_lines)), "choices": choices}
    return res


def parse_mock(txt, tag, booklet):
    lines = txt.split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.startswith("大問1 短文の語句空所補充"))
    i1 = next(i for i in range(i0 + 1, len(lines)) if lines[i].startswith("大問2"))
    seg = [l for l in lines[i0 + 1:i1] if not l.startswith("<<<PAGE") and "採点・解説冊子" not in l and l.strip() != "オリジナル模試・非公式" and not re.fullmatch(r"\d+", l.strip())]
    blocks = []; cur = None
    for l in seg:
        m = re.match(r"^\((\d{1,2})\) 正答 (\d) (.+)$", l.strip())
        if m:
            cur = {"no": int(m.group(1)), "ans": int(m.group(2)) - 1, "word": norm_space(m.group(3)), "lines": []}
            blocks.append(cur)
        elif cur is not None and l.strip():
            cur["lines"].append(l.strip())
    out = []
    for b in blocks:
        ja = []; point = []; choice_line = []; mode = "stem"; stem_lines = []
        for l in b["lines"]:
            if l.startswith("和訳："):
                mode = "ja"; ja.append(l[len("和訳："):]); continue
            if l.startswith("ポイント："):
                mode = "point"; point.append(l[len("ポイント："):]); continue
            if l.startswith("選択肢："):
                mode = "choice"; choice_line.append(l[len("選択肢："):]); continue
            {"stem": stem_lines, "ja": ja, "point": point, "choice": choice_line}[mode].append(l)
        cl = norm_space(" ".join(choice_line))
        base_words = []; meanings = []
        for p in [p.strip() for p in cl.split(" / ")]:
            m = re.match(r"^([A-Za-z][A-Za-z '\-]*?)\s+([^A-Za-z].*)$", p)
            if not m:
                problems.append(f"{tag} ({b['no']}): 選択肢の分解に失敗: {p!r}"); base_words.append(p); meanings.append(""); continue
            base_words.append(norm_space(m.group(1))); meanings.append(norm_space(m.group(2)))
        bk = booklet.get(b["no"])
        if not bk or len(bk["choices"]) != 4:
            problems.append(f"{tag} ({b['no']}): 問題冊子に選択肢が無い/4 つでない {bk}"); continue
        choices = bk["choices"]                                   # 活用形のまま (解説冊子の意味行は原形)
        stem = bk["stem"] or clean_stem(" ".join(stem_lines))
        if len(base_words) != 4:
            problems.append(f"{tag} ({b['no']}): 意味が 4 つでない {base_words}")
        for c, bw in zip(choices, base_words):
            if c.lower()[:1] != bw.lower()[:1]:
                print(f"  ⚠ {tag} ({b['no']}): 選択肢 {c!r} と意味行 {bw!r} の対応を目で確認")
        unit = U_2P if any(" " in c for c in choices) else U_2W
        mean = " ／ ".join((f"{c}（{bw}）= {mn}" if bw.lower() != c.lower() else f"{c} = {mn}") for c, bw, mn in zip(choices, base_words, meanings))
        expl = ("正解は " + b["word"] + "。 " + tidy_ja(" ".join(point)) + " 訳: " + tidy_ja(" ".join(ja)) + " 選択肢の意味: " + mean)
        out.append({"subject": "eiken", "unit": unit, "level": "standard", "stem": stem, "choices": choices,
                    "answer": b["ans"], "explanation": norm_space(expl), "source": f"{tag}-{b['no']}", "_ans_word": b["word"]})
    return out


def apply_overrides(qs):
    out = []
    for q in qs:
        if q["source"] in DROP:
            continue
        ov = OVERRIDES.get(q["source"])
        if ov:
            if "choices" in ov:
                assert len(ov["choices"]) == 4
                q["choices"] = ov["choices"]
                q.pop("_ans_word", None)
            for a, b in ov.get("stem_replace", []):
                assert a in q["stem"], (q["source"], a)
                q["stem"] = q["stem"].replace(a, b)
            for a, b in ov.get("explanation_replace", []):
                assert a in q["explanation"], (q["source"], a)
                q["explanation"] = q["explanation"].replace(a, b)
        out.append(q)
    return out


def main():
    qs = load_p1()
    qs += load_p1_mock()
    qs += load_wb1_json()
    if os.path.exists(WB2_PDF):
        qs += parse_workbook(pdf_text(WB2_PDF), "eiken2-workbook-vol2")
    else:
        problems.append(f"Vol.2 の PDF が無い: {WB2_PDF}")
    for r, sub in ((1, "第1回_修正版"), (2, "第2回"), (3, "第3回")):
        qp = f"{MOCK2_DIR}/{sub}/英検2級_完全模試_第{r}回_問題冊子（リスニング除外）.pdf"
        ap = f"{MOCK2_DIR}/{sub}/英検2級_完全模試_第{r}回_採点・解説冊子（リスニング除外）.pdf"
        if not (os.path.exists(qp) and os.path.exists(ap)):
            problems.append(f"2級 完全模試 第{r}回の PDF が無い: {qp}"); continue
        qs += parse_mock(pdf_text(ap), f"eiken2-mock-202609-r{r}", parse_mock_booklet(pdf_text(qp)))
    qs = apply_overrides(qs)
    # ── 検査 (形式ゲート scripts/check_eiken_vocab_seed.py と同じ観点 + 出所ごとの正解語照合) ──
    seen = {}
    for q in qs:
        src = q["source"]
        if q["stem"].count(BLANK) != 1:
            problems.append(f"{src}: 空所が {q['stem'].count(BLANK)} 個: {q['stem'][:90]}")
        if len(q["choices"]) != 4 or len(set(c.lower() for c in q["choices"])) != 4:
            problems.append(f"{src}: 選択肢が 4 つ相異でない {q['choices']}")
        if not (0 <= q["answer"] <= 3):
            problems.append(f"{src}: answer 範囲外 {q['answer']}")
        aw = q.get("_ans_word")
        if aw and q["choices"] and 0 <= q["answer"] <= 3 and q["choices"][q["answer"]].lower() != aw.lower():
            problems.append(f"{src}: 正解語 {aw!r} が choices[answer]={q['choices'][q['answer']]!r} と違う")
        if q["choices"] and 0 <= q["answer"] <= 3 and q["choices"][q["answer"]].lower() not in q["explanation"].lower():
            problems.append(f"{src}: 解説に正解語が無い")
        if re.search(rf"[①②③④]|選択肢\s*[1-4１-４]|\{{\s*[1-4]\s*:|(?<=[{_JA}])[1-4](?=のみ|だけ|が(?:文意|適切|自然|正解)|[。、]|\s|$)", q["explanation"]):
            problems.append(f"{src}: 解説に番号参照がある")
        if len(q["explanation"]) < 20:
            problems.append(f"{src}: 解説が短すぎる")
        key = q["stem"].lower()
        if key in seen:
            problems.append(f"{src}: stem が {seen[key]} と重複")
        seen[key] = src
    for q in qs:
        q.pop("_ans_word", None)
    by_unit = collections.Counter(q["unit"] for q in qs)
    pos = collections.defaultdict(collections.Counter)
    for q in qs:
        pos[q["unit"]][q["answer"]] += 1
    print("問題数:", len(qs), dict(by_unit))
    for u, cnt in pos.items():
        print("  正解位置", u, dict(sorted(cnt.items())))
    if problems:
        print(f"\n❌ 検査 NG {len(problems)} 件 (書き出しません):")
        for p in problems[:80]:
            print("  -", p)
        sys.exit(1)
    meta = {"name": "eiken_vocab_pool_v1", "created": "2026-09-24", "subject": "eiken", "units": dict(by_unit),
            "sources": ["準1級: 大問1-4 本番形式演習 第1弾/第2弾 大問1 (Desktop/📚 教材/英語/_生成元_英語教材_202609/data/eikenp1_mock, eikenp1_mock2)",
                        "準1級: 完全模試 リスニング除外 全3回 大問1 (Desktop/英検準1級_完全模試_…_20260923/_制作ソース pre1_set*_data.py の P1)",
                        "2級: 対策問題集 Vol.1 大問1 (scripts/eiken_2kyu/data/part1_vocab.json)",
                        "2級: 対策問題集 Vol.2 大問1 (PDF から抽出)", "2級: 完全模試 リスニング除外 全3回 大問1 (問題冊子 + 採点・解説冊子の PDF から抽出)"],
            "blind_review": "2026-09-24: 正解を伏せた独立ソルバー 3 名が全 401 問を解いて全問一致。指摘 3 件 (活用・時制・第 2 の正解の余地) を builder の OVERRIDES/DROP で反映 → 400 問 (生の解答は手元のみ・リポジトリには入れない)",
            "note": "全部トリリオンAI塾の書き下ろし (過去問なし)。解説は値で書く (①や『選択肢2』を書かない)。level は全問 standard (級は unit 名で分ける)。"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps({"_meta": meta, "questions": qs}, ensure_ascii=False, indent=1) + "\n")
    print("✅ 書き出し:", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
