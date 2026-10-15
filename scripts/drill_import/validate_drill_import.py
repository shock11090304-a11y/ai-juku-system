#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📖🧪 科目別ドリルの取込ファイル (英語長文 english_long / 習熟度テスト proficiency_test) の検査スクリプト。

正本の仕様は docs/drill-import-spec.md (取込仕様書 v1・形式 "trillion-drill-import/v1")。仕様書 11 章のエラー・警告をこの 1 本で出す。

    python3 -I validate_drill_import.py <drill.json|test.json>                 # 検査 (エラー 0 なら exit 0・警告だけなら 0)
    python3 -I validate_drill_import.py --json <ファイル>                       # 機械向けの出力 (JSON)
    python3 -I validate_drill_import.py --make-blind <出力フォルダ> <ファイル>   # 盲検のシートと解答用紙のひな形を書く
    python3 -I validate_drill_import.py                                         # 引数なし = 自己検査 (隣に fixtures/ があるとき)

★単体で動く (2026-10-15 塾長決定): Python 3.9 の標準ライブラリだけを使い、どのフォルダからでも `python3 -I` で動く
  (塾長の Mac の /usr/bin/python3 は 3.9.6。match 文・X | Y の型注釈・3.10 以降の関数は使わない)。
  サーバ (server/main.py) の単元表などは下の SERVER_TABLES に写して持つ。サーバの表を変えたらここも同じに直す
  (ずれると CI の scripts/health_check/test_drill_import_parity.py が落ちる)。直したら塾長のデスクトップの写し
  (~/Desktop/📝 模試・演習/習熟度テスト/_tools/) にも置き直す。
★書き込むのは --make-blind の出力先 (git リポジトリと seed-data の中は拒否) と、自己検査の一時フォルダ (tempfile) だけ。
  リポジトリには何も書かない (scripts/run_all_gates.py が実測で見張っている)。通信はしない。

終了コード: 0 = エラー 0 件 / 1 = エラーあり・自己検査の食い違い / 2 = 使い方の誤り・読めないファイル
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL_VERSION = "validate_drill_import/v1"
DOC_FORMAT = "trillion-drill-import/v1"
ANSWERS_FORMAT = "trillion-blind-answers/v1"
SHEET_FORMAT = "trillion-blind-sheet/v1"
KIND_LABEL = {"english_long": "英語長文", "proficiency_test": "習熟度テスト"}
CIRCLED = "①②③④⑤⑥⑦⑧"

# ---------------------------------------------------------------------------
# サーバの表の写し (server/main.py の同名の定数と同じでなければならない)。
# ★scripts/health_check/test_drill_import_parity.py が server/main.py を構文木で読んで突き合わせる。
#   サーバ側で単元を足した・名前を変えたときは、ここも同じ commit で直す (CI が落ちて知らせる)。
# ---------------------------------------------------------------------------
SERVER_TABLES = {
    "GRAMMAR_UNITS": [
        "時制", "助動詞", "受動態", "不定詞", "動名詞", "分詞", "分詞構文",
        "関係詞", "仮定法", "比較", "接続詞", "前置詞", "疑問詞・間接疑問",
        "否定・倒置", "強調・省略", "冠詞", "名詞・代名詞", "形容詞・副詞",
        "話法", "語法・イディオム",
    ],
    "_GRAMMAR_SUBJECT_UNIT_ORDER": {
        "chugaku": ["be動詞・一般動詞", "時制", "助動詞", "名詞・代名詞・冠詞", "比較", "不定詞・動名詞",
                    "分詞", "受動態", "現在完了", "関係代名詞", "接続詞・前置詞", "会話表現"],
        "chugaku_math": ["正負の数", "式の計算", "一次方程式", "連立方程式", "平方根", "二次方程式",
                         "比例・反比例", "一次関数", "二乗に比例", "合同と証明", "相似", "円周角",
                         "三平方の定理", "確率", "データの活用"],
        "chugaku_rika": ["光と音", "力と圧力", "電流と回路", "電流と磁界", "運動とエネルギー", "物質と状態変化",
                         "化学変化と原子", "イオンと酸", "植物", "動物と人体", "生殖と遺伝", "大地の変化", "天気", "天体"],
        "chugaku_shakai": ["世界地理", "日本地理", "歴史 古代", "歴史 中世", "歴史 近世", "歴史 近代", "歴史 現代",
                           "公民 政治", "公民 経済", "公民 国際", "資料読み取り"],
        "chugaku_kokugo": ["漢字", "語句", "文法", "敬語", "古文", "詩歌"],
        "eiken": ["2級 単語", "2級 句動詞・熟語", "準1級 単語", "準1級 句動詞・熟語",
                  "2級 長文空所補充", "2級 長文 内容一致", "準1級 長文空所補充", "準1級 長文 内容一致"],
        "english_long": ["長文 Lv.1", "長文 Lv.2", "国公立 長文"],
    },
    "_GRAMMAR_CANON_SUBJECTS": sorted([
        "english", "math", "physics", "chemistry", "biology", "earth", "japanese", "social",
        "chugaku", "eiken", "chugaku_math", "chugaku_rika", "chugaku_shakai", "chugaku_kokugo",
        "english_long", "proficiency_test"]),
    "_PASSAGE_ONLY_SUBJECTS": ["english_long", "proficiency_test"],
    "_GRAMMAR_REVIEW_PROTOCOL": "trillion-blind/v1",
    "_PTEST_SUBJECT": "proficiency_test",
    "_PTEST_MAX_SECTIONS": 12,
    "_PTEST_MAX_QUESTIONS": 60,
    "_PTEST_UNIT_RE": r"^(高校|中学)(英語|数学|国語|理科|社会) (\S{1,10}) 第([1-9][0-9]?)回(?:改([1-9]))?$",
}

REVIEW_PROTOCOL = SERVER_TABLES["_GRAMMAR_REVIEW_PROTOCOL"]
PTEST_SUBJECT = SERVER_TABLES["_PTEST_SUBJECT"]
PTEST_UNIT_RE = re.compile(SERVER_TABLES["_PTEST_UNIT_RE"])
PTEST_MAX_SECTIONS = SERVER_TABLES["_PTEST_MAX_SECTIONS"]
PTEST_MAX_QUESTIONS = SERVER_TABLES["_PTEST_MAX_QUESTIONS"]
ENGLONG_UNITS = list(SERVER_TABLES["_GRAMMAR_SUBJECT_UNIT_ORDER"]["english_long"])
# skill に書ける単元 (サーバの _ptest_meta_from_payload と同じ: english は GRAMMAR_UNITS・ほかは単元の並びが決まっている科目)
SKILL_UNITS = {"english": list(SERVER_TABLES["GRAMMAR_UNITS"])}
SKILL_UNITS.update({k: list(v) for k, v in SERVER_TABLES["_GRAMMAR_SUBJECT_UNIT_ORDER"].items()})
# 単元名が決まっていない科目 (高校の math・japanese・social など): skill に書くと警告して外す (仕様書 10 章)
SKILL_NO_UNIT_SUBJECTS = sorted(set(SERVER_TABLES["_GRAMMAR_CANON_SUBJECTS"]) - set(SKILL_UNITS) - {PTEST_SUBJECT})

# 英語長文の目安 (仕様書 3 章): 単元 -> (語数の下限, 上限, 設問数の下限, 上限)。外れたら警告
ENGLONG_GUIDE = {"長文 Lv.1": (300, 550, 4, 5), "長文 Lv.2": (500, 800, 5, 6), "国公立 長文": (600, 1000, 5, 6)}
ENGLONG_MAX_WORDS = 1500
ENGLONG_Q_RANGE = (3, 6)
ENGLONG_MAX_PASSAGES = 20
ENGLONG_TITLE_MAX = 60
ENGLONG_TYPES = ("内容一致", "内容不一致", "空所補充", "下線部の意味", "指示語", "段落の要旨", "主題・タイトル", "推論", "文挿入")
PTEST_TARGETS = {"kosei": "高校", "chugaku": "中学"}
PTEST_SUBJECT_JA = ("英語", "数学", "国語", "理科", "社会")
PTEST_SECTION_Q_MAX = 15
PTEST_TITLE_MAX = 40
PTEST_CHOICES = (2, 8)

# 0 始まりと 1 始まりの取り違えを防ぐため、番号の欄は correct_choice_no だけ (仕様書 1-2)
FORBIDDEN_KEYS = ("answer", "answers", "key", "good", "correct", "accepted_pairs", "linked_choices", "marks", "points", "multi")
FIGURE_KEYS = ("figure", "figures", "figure_svg", "image", "images", "img", "svg", "diagram", "picture", "photo")
REVIEW_ERRORS = ("E_REVIEW_MISSING", "E_BLIND_MISMATCH", "E_BLIND_STALE", "E_BLIND_OFFSET")

_CTRL_RE = re.compile("[\x00-\x09\x0b-\x1f\x7f\u200b-\u200f\u2028\u2029\u2060\ufeff]")
_HTML_RE = re.compile(r"<\s*/?\s*[A-Za-z][A-Za-z0-9-]*(?:\s[^<>\n]*)?/?\s*>")
_MD_RE = re.compile(r"\*\*[^*\n]+\*\*|!\[[^\]\n]*\]\(|\[[^\]\n]+\]\((?:https?:|/)")
_URL_RE = re.compile(r"https?://|\bwww\.[A-Za-z0-9-]+\.", re.I)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")
_KATEX_RE = re.compile(r"\$|\\\(|\\\[")
_BLANK_RE = re.compile(r"\(\s*(\d{1,2})\s*\)")            # アプリが黄色くする空所 (class.html の gdPassageHtml と同じ形)
_STEM_BLANK_RE = re.compile(r"^\s*\(\s*(\d{1,2})\s*\)")
_MULTI_RE = re.compile(
    r"[2２二]\s*つ(?:を)?\s*選|[2２二]\s*つ以上|すべて選|全て選|全部選|複数(?:を)?選|あてはまるものを(?:すべて|全て)|当てはまるものを(?:すべて|全て)"
    r"|\b(?:choose|select|pick|mark)\s+(?:two|three|all|both)\b|\ball\s+that\s+apply\b|\b(?:two|2)\s+(?:correct\s+)?answers\b",
    re.I)
_COND_RE = re.compile(
    r"を選んだ場合|を選ぶ場合|選んだ答え|で選んだ(?:もの|選択肢|番号)|前問の答え|前の問いの答え|前の問題の答え|前問で選|前の問(?:い|題)で選"
    r"|解答番号\s*[0-9０-９]+\s*(?:で|に)|対応する正答|答えによって|\bif you (?:chose|choose|selected|picked)\b"
    r"|\byour answer to (?:the )?(?:previous|question)\b",
    re.I)
# ★日本語は「図書館」「地図を見ながら歩いた」「棚の上の写真立て」のような普通の文に当たりやすいので、図を指す言い方だけにする
#   (解説・全訳は見ない。図を使う問題なら本文か問題文に出る)
_FIG_JA_RE = re.compile(
    r"(?:下|上|次|左|右|以下|前ページ|次ページ)の(?:図|グラフ|イラスト|画像|チャート)"
    r"|(?<![地意企合版])図\s*[0-9０-９ⅠⅡⅢⅣⅤ]"
    r"|(?:グラフ|写真|地図|イラスト|画像|挿絵)\s*[0-9０-９ⅠⅡⅢⅣⅤA-DＡ-Ｄ](?![A-Za-z])"
    r"|(?:図|グラフ|写真|地図|イラスト|画像)(?:から|を参照して|を見て(?:答え|選))")
_FIG_NOUN = r"(?:graphs?|charts?|figures?|diagrams?|pictures?|photos?|photographs?|maps?|illustrations?|images?)"
_FIG_EN_RE = re.compile(
    r"\b" + _FIG_NOUN + r"\s+(?:below|above)\b"
    r"|\b(?:the|this|these|following)\s+" + _FIG_NOUN + r"\b[^.?!\n]{0,30}\b(?:below|above)\b"
    r"|\b(?:shown|illustrated|presented)\s+(?:in|on)\s+the\s+" + _FIG_NOUN + r"\b"
    r"|\b(?:look at|see|refer to)\s+the\s+" + _FIG_NOUN + r"\b"
    r"|\b(?:fig\.|figure)\s*\d",
    re.I)
_AMBIG_RE = re.compile(r"別解|正解が\s*[2２二]|複数|あいまい|曖昧|ambiguous|two answers|two correct", re.I)
_SECTION_HEAD_RE = re.compile(r"^\s*第\s*[0-9０-９一二三四五六七八九十]+\s*問")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_EN_WORD_RE = re.compile(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*")
_JA_TOKEN_RE = re.compile(r"[一-龥々]{2,}|[ァ-ヶー]{3,}")
_STOP_EN = set("""
about above according across after again against also among another answer answers because been before being below best between
both cannot could does doing down during each either following from further have having here into itself just least less more
most much must neither only other others over passage paragraph question questions same should since some statement statements
such than that their them then there these they this those through true false under until upon very what when where which while
whom whose will with without would your word words phrase sentence sentences text writer author article choose select mean means
meaning closest best describes stated mentioned
""".split())
_STOP_JA = {"本文", "内容", "筆者", "選択", "選択肢", "適切", "適当", "最", "次", "下線部", "段落", "空所", "設問", "問題", "文章", "説明",
            "主題", "理由", "意味", "合致", "一致", "不一致", "記述", "部分", "表現", "以下", "英文", "日本語", "正", "誤", "組合", "組み合わせ"}


def nfc(s):
    return unicodedata.normalize("NFC", s)


def norm_ws(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def squash(s):
    return re.sub(r"\s+", "", str(s))


def item_hash(body, stem, choices):
    """盲検の答えをその版の問題に結びつける値 (仕様書 6 章)。本文・問題文・選択肢のどれかを直すと変わる (解説・訳・skill では変わらない)。
    ★式を変えると、記録済みの盲検が全部 E_BLIND_STALE になる。自己検査が既知の値で固定している。"""
    data = json.dumps([nfc(body), nfc(stem), [nfc(c) for c in choices]], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def ptest_unit_name(doc):
    """習熟度テストの単元名「<高校|中学><科目> <series_ja> 第<round>回(改<revision>)」(仕様書 4 章・サーバの _PTEST_UNIT_RE)。組み立てられなければ ''。"""
    t = PTEST_TARGETS.get(doc.get("target")) if isinstance(doc.get("target"), str) else None
    sj, se, rd = doc.get("subject_ja"), doc.get("series_ja"), doc.get("round")
    rev = doc.get("revision", 0)
    if rev is None:
        rev = 0
    if not t or not isinstance(sj, str) or not isinstance(se, str) or not _is_int(rd) or not _is_int(rev):
        return ""
    return f"{t}{sj} {se} 第{rd}回" + (f"改{rev}" if rev else "")


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def location_problem(path):
    """ファイル (または出力先) が置いてはいけない場所なら理由、よければ ''。git リポジトリ (祖先のどこかに .git) と seed-data の中は不可
    (仕様書 1-10: 公開リポジトリに入るとテストの答えが漏れる)。まだ無い出力先でも、親をたどって判定する。"""
    real = os.path.realpath(os.path.abspath(path))
    if "/seed-data/" in real.replace(os.sep, "/") + "/":
        return "seed-data の中"
    d = real
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return f"git リポジトリ ({d}) の中"
        parent = os.path.dirname(d)
        if parent == d:
            return ""
        d = parent


class Report:
    def __init__(self, path):
        self.path = path
        self.doc = None
        self.kind = ""
        self.doc_id = ""
        self.units = []
        self.errors = []      # (code, where, message)
        self.warnings = []
        self.item_hashes = {}  # qid -> item_hash
        self.file_sha256 = ""
        self.n_groups = 0
        self.n_questions = 0
        self.review_status = "未確認"

    def err(self, code, where, msg):
        self.errors.append((code, where, msg))

    def warn(self, code, where, msg):
        self.warnings.append((code, where, msg))

    def error_codes(self):
        return sorted({c for c, _, _ in self.errors})

    def warning_codes(self):
        return sorted({c for c, _, _ in self.warnings})

    def to_json(self):
        return {"tool": TOOL_VERSION, "file": self.path, "ok": not self.errors, "kind": self.kind, "id": self.doc_id,
                "units": self.units, "groups": self.n_groups, "questions": self.n_questions, "file_sha256": self.file_sha256,
                "review": self.review_status, "item_hashes": self.item_hashes,
                "errors": [{"code": c, "where": w, "message": m} for c, w, m in self.errors],
                "warnings": [{"code": c, "where": w, "message": m} for c, w, m in self.warnings]}


def _dup_key_hook(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"同じ名前の欄「{k}」が 2 回あります (後の値で黙って上書きされるので不可)")
        seen[k] = v
    return seen


def read_json(path):
    """(生のバイト列, 中身) を返す。UTF-8 でない・BOM つき・JSON でない・同じ欄が 2 回、は ValueError。"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("先頭に BOM があります (BOM なしの UTF-8 で保存してください)")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"UTF-8 で読めません ({e})")
    try:
        return raw, json.loads(text, object_pairs_hook=_dup_key_hook)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON として読めません ({e.msg}・{e.lineno} 行 {e.colno} 文字目)")


# ---------------------------------------------------------------------------
# 全体の決まり (仕様書 1 章): 文字・禁止欄・HTML・メール
# ---------------------------------------------------------------------------
def _walk(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.append(("key", f"{path}.{k}" if path else str(k), k))
            _walk(v, f"{path}.{k}" if path else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _walk(v, f"{path}[{i}]", out)
    elif isinstance(obj, str):
        out.append(("str", path, obj))


def _check_hygiene(r, doc):
    nodes = []
    _walk(doc, "", nodes)
    for typ, path, val in nodes:
        top = path.split(".")[0].split("[")[0]
        if typ == "key":
            if val in FORBIDDEN_KEYS:
                r.err("E_INDEX_FIELD", path, f"欄「{val}」は書けません。正解は correct_choice_no (1 始まり) だけで書く (0 始まりとの取り違え防止)")
            elif val in FIGURE_KEYS:
                r.err("E_FIGURE", path, f"欄「{val}」(図・画像) は使えません。アプリで出せるのは文字だけ")
            if not isinstance(val, str) or nfc(val) != val or _CTRL_RE.search(val):
                r.err("E_FORMAT", path, "欄の名前に NFC でない文字・制御文字がある")
            continue
        if nfc(val) != val:
            r.err("E_FORMAT", path, "NFC でない文字がある (濁点の分離など)。NFC に正規化して保存する")
        m = _CTRL_RE.search(val)
        if m:
            r.err("E_FORMAT", path, f"タブ・制御文字・見えない文字 (U+{ord(m.group(0)):04X}) がある。改行は \\n だけ")
        if _EMAIL_RE.search(val):
            r.err("E_EMAIL", path, "メールアドレスの @ は全角 ＠ にする (公開リポジトリの個人情報検査のため)")
        if top in ("copyright", "_review", "_fixture", "_expect"):
            continue          # 出典の URL (fact_sources) と記録は対象外
        if _HTML_RE.search(val) or _MD_RE.search(val):
            r.err("E_HTML", path, "HTML のタグ・Markdown (**太字** や画像) は使えない")
        elif _URL_RE.search(val):
            r.err("E_HTML", path, "URL の埋め込みは使えない (出典は copyright.fact_sources に書く)")


def _check_copyright(r, doc):
    cp = doc.get("copyright")
    if not isinstance(cp, dict):
        r.err("E_FORMAT", "copyright", "copyright がありません ({\"original\": true, \"not_published_anywhere\": true, …})")
        return
    if cp.get("original") is not True:
        r.err("E_FORMAT", "copyright.original", "original: true (書き下ろし) が必要です (仕様書 1-8)")
    if cp.get("not_published_anywhere") is not True:
        r.err("E_FORMAT", "copyright.not_published_anywhere",
              "not_published_anywhere: true が必要です (note・PDF・配布物などで公開・販売していないこと)")
    if "no_past_exam_text" in cp and cp.get("no_past_exam_text") is not True:
        r.err("E_FORMAT", "copyright.no_past_exam_text", "no_past_exam_text は true だけ (過去問の文章は使えない)")
    fs = cp.get("fact_sources", [])
    if not isinstance(fs, list) or not all(isinstance(x, str) for x in fs):
        r.err("E_FORMAT", "copyright.fact_sources", "fact_sources は文字列 (資料名・URL) の配列")


# ---------------------------------------------------------------------------
# 本文 (仕様書 2 章)
# ---------------------------------------------------------------------------
def _check_text_figure(r, where, text):
    if not isinstance(text, str):
        return
    m = _FIG_JA_RE.search(text) or _FIG_EN_RE.search(text)
    if m:
        r.err("E_FIGURE", where, f"図・グラフ・写真への言及「{m.group(0)}」がある。数値が要るなら表 (［表］) にする")


def _check_conditional(r, where, text):
    if isinstance(text, str):
        m = _COND_RE.search(text)
        if m:
            r.err("E_CONDITIONAL", where, f"選んだ答えで正解が変わる・前の問いの答えを使う形「{m.group(0)}」は不可 (前の問いの正解を問題文に書けば可)")


def _check_tables(r, where, body):
    lines = body.split("\n")
    rows_in_table = set()
    probs = []
    for i, line in enumerate(lines):
        if line.strip() == "［表］":
            rows = []
            j = i + 1
            while j < len(lines) and "｜" in lines[j]:
                rows.append(lines[j])
                rows_in_table.add(j)
                j += 1
            if len(rows) < 2:
                probs.append("［表］の下に見出しの行と 1 行以上の中身が無い")
            else:
                cols = [len(x.split("｜")) for x in rows]
                if len(set(cols)) != 1:
                    probs.append(f"列の数がそろっていない (行ごとの列数 {cols})")
    for i, line in enumerate(lines):
        if "｜" in line and i not in rows_in_table:
            probs.append(f"［表］の外に ｜ の行がある「{line.strip()[:20]}」")
        if re.match(r"^\s*\|.*\|", line):
            probs.append("Markdown の表 (半角 |) は使えない。［表］と全角 ｜ で書く")
    if probs:
        r.err("E_TABLE", where, "・".join(probs))


def _check_blanks(r, where, body, stems):
    nums = [int(m.group(1)) for m in _BLANK_RE.finditer(body)]
    probs = []
    if nums != list(range(1, len(nums) + 1)):
        probs.append(f"本文の ( N ) が出てくる順に ( 1 ) ( 2 ) … と 1 回ずつになっていない (本文の並び {nums})")
    refs = set()
    for s in stems:
        if isinstance(s, str):
            m = _STEM_BLANK_RE.match(s)
            if m:
                refs.add(int(m.group(1)))
    unref = sorted(set(nums) - refs)
    if unref:
        probs.append(f"どの設問からも参照されない空所 {['( %d )' % n for n in unref]} がある (設問は「( k ) に入れるのに…」で始める・段落番号は [1])")
    dangling = sorted(refs - set(nums))
    if dangling:
        probs.append(f"設問の {['( %d )' % n for n in dangling]} が本文に無い")
    if probs:
        r.err("E_BLANKS", where, "・".join(probs))


def _check_underlines(r, where, body, stems):
    probs = []
    for s in stems:
        if not isinstance(s, str):
            continue
        for m in re.finditer(r"下線部\s*([A-Za-zＡ-Ｚａ-ｚ])?", s):
            if not m.group(1):
                probs.append("問題文の下線部は「下線部A」のように記号で呼ぶ")
                continue
            x = unicodedata.normalize("NFKC", m.group(1)).upper()
            if not re.search(r"[［\[]\s*" + re.escape(x) + r"\s*[：:]", body):
                probs.append(f"問題文の「下線部{x}」が本文に無い (本文には［{x}：…］と書く)")
    for m in re.finditer(r"［\s*([A-ZＡ-Ｚ])\s*[：:]", body):
        rest = body[m.end():]
        close, nxt = rest.find("］"), rest.find("［")
        if close < 0 or (0 <= nxt < close):
            probs.append(f"本文の［{m.group(1)}：… が］で閉じていない")
    if probs:
        r.err("E_UNDERLINE", where, "・".join(sorted(set(probs))))


def _english_words(text):
    return len(_EN_WORD_RE.findall(re.sub(r"\[\d+\]", " ", text)))


# ---------------------------------------------------------------------------
# 設問 (仕様書 1・3・4・5 章)
# ---------------------------------------------------------------------------
_NUMBERING_RES = (
    re.compile(r"^\s*[\(（]\s*(?:[A-Ha-hＡ-Ｈａ-ｈ]|[0-9０-９]{1,2}|[ア-ク]|[ⅰⅱⅲⅳⅠⅡⅢⅣ])\s*[\)）]"),
    re.compile(r"^\s*(?:[A-Ha-hＡ-Ｈ]|[0-9０-９]{1,2})\s*[\.．\)）:：、]\s"),
    re.compile(r"^\s*[ア-ク]\s*[\.．\)）:：、\s　]"),
)


def _numbered_choice(c):
    s = c.strip()
    labels = len(re.findall(r"[①-⑳]", s))
    if labels >= 2:
        return False          # 「③→①→④→②」「①と③」のような組み合わせ・順序の選択肢 (仕様書 7 章) は可
    if labels == 1 and re.match(r"^[①-⑳]", s):
        return True
    if any(rx.match(s) for rx in _NUMBERING_RES):
        return len(re.findall(r"[\(（]\s*[A-Ha-hＡ-Ｈ0-9０-９ア-ク]\s*[\)）]", s)) < 2
    return False


def _parse_explanation(text):
    lines = text.split("\n")
    sections = {}
    cur = None
    for line in lines[1:]:
        m = re.match(r"^\s*【([^】]{1,12})】(.*)$", line)
        if m:
            cur = m.group(1).strip()
            sections.setdefault(cur, [])
            rest = m.group(2).strip()
            if rest:
                sections[cur].append(rest)
            continue
        if cur is not None:
            sections[cur].append(line)
    return lines[0], sections


def _evidence_in_body(line, body_sq):
    cand = line.strip()
    if len(cand) >= 2 and cand[0] in "「『\"“'" and cand[-1] in "」』\"”'":
        cand = cand[1:-1].strip()
    variants = [cand, re.sub(r"^\[\d+\]\s*", "", cand), re.sub(r"^第\s*\d+\s*段落\s*[:：]?\s*", "", cand)]
    return any(v and squash(v) in body_sq for v in variants)


def _check_explanation(r, kind, where, expl, choices, cno, body):
    first, secs = _parse_explanation(expl)
    want = f"正解 {CIRCLED[cno - 1]} {choices[cno - 1]}"
    got = norm_ws(first)
    if got != norm_ws(want):
        hint = ""
        m = re.match(r"^正解\s*([①-⑧])\s*(.*)$", got)
        if m:
            n_got = CIRCLED.index(m.group(1)) + 1
            t_got = norm_ws(m.group(2))
            if t_got == norm_ws(choices[cno - 1]) and n_got != cno:
                hint = f" (番号 {m.group(1)} が correct_choice_no={cno} と違う = 番号ずれの疑い)"
            elif n_got == cno:
                hint = " (選択肢の文字列がそのままになっていない)"
            elif any(t_got == norm_ws(c) for c in choices):
                hint = " (別の選択肢の文字列 = 番号ずれの疑い)"
        r.err("E_EXPL_HEAD", where, f"解説の 1 行目は「{want}」にする{hint}")
    body_sq = squash(body)
    probs = []
    ev = [x for x in secs.get("根拠", []) if x.strip()]
    if kind == "english_long":
        if not ev:
            probs.append("【根拠】(本文の 1 文をそのまま) が無い")
        if not [x for x in secs.get("訳", []) if x.strip()]:
            probs.append("【訳】(根拠の和訳) が無い")
    else:
        if not ev and not [x for x in secs.get("解説", []) if x.strip()]:
            probs.append("【解説】(または【根拠】) が無い")
    for line in ev:
        if not _evidence_in_body(line, body_sq):
            probs.append(f"【根拠】「{line.strip()[:40]}」が本文と一致しない (要約しない・空白以外は 1 字も変えない)")
    if probs:
        r.err("E_EXPL_EVIDENCE", where, "・".join(probs))
    required = kind == "english_long" or len(choices) <= 6
    others = [x for x in secs.get("他の選択肢", []) if x.strip()]
    probs = []
    if "他の選択肢" not in secs or not others:
        if required:
            probs.append("【他の選択肢】(誤答 1 つにつき「① <選択肢そのまま> … 理由」の 1 行) が無い")
    else:
        seen = set()
        for line in others:
            s = norm_ws(line)
            m = re.match(r"^([①-⑧])\s*(.*)$", s)
            if not m:
                probs.append(f"行が ① などの番号で始まっていない「{s[:20]}」")
                continue
            k = CIRCLED.index(m.group(1)) + 1
            if k == cno:
                probs.append(f"正解の番号 {m.group(1)} が誤答の行にある (番号ずれの疑い)")
                continue
            if k > len(choices):
                probs.append(f"{m.group(1)} という選択肢は無い")
                continue
            c = norm_ws(choices[k - 1])
            rest = m.group(2)
            if not rest.startswith(c):
                probs.append(f"{m.group(1)} の文字列が選択肢 {m.group(1)}「{c[:20]}」と違う (番号ずれの疑い)")
                continue
            if not re.match(r"^(?:…|\.\.\.|：|:|—|–|-|→)+\s*\S", rest[len(c):].strip()):
                probs.append(f"{m.group(1)} の行に「… 誤りの理由」が無い")
            seen.add(k)
        if required:
            miss = [CIRCLED[k - 1] for k in range(1, len(choices) + 1) if k != cno and k not in seen]
            if miss:
                probs.append(f"誤答 {''.join(miss)} の行が無い")
    if probs:
        r.err("E_EXPL_OTHERS", where, "・".join(probs))


def _check_question(r, kind, where, q, body, group):
    """1 問ぶんの検査。戻り値 = 位置・盲検の照合に使う要約 (dict)。"""
    it = {"where": where, "qid": None, "group": group, "body": body, "stem": None, "choices": None, "correct": None,
          "explanation": None, "hash": None}
    if not isinstance(q, dict):
        r.err("E_FORMAT", where, "設問が object ではない")
        return it
    stem = q.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        r.err("E_FORMAT", where, "stem (問題文) が無い")
        stem = None
    it["stem"] = stem
    choices = q.get("choices")
    n_ok = (4, 4) if kind == "english_long" else PTEST_CHOICES
    if not isinstance(choices, list):
        r.err("E_CHOICES", where, "choices (選択肢) が文字列の配列ではない")
        choices = None
    else:
        probs = []
        if not (n_ok[0] <= len(choices) <= n_ok[1]):
            probs.append(f"選択肢は {n_ok[0]}" + (f"〜{n_ok[1]}" if n_ok[1] != n_ok[0] else "") + f" 個 (いま {len(choices)} 個)")
        if not all(isinstance(c, str) and c.strip() for c in choices):
            probs.append("空の選択肢・文字列でない選択肢がある")
        else:
            keys = [squash(unicodedata.normalize("NFKC", c)).casefold() for c in choices]
            if len(set(keys)) != len(keys):
                probs.append("重複した選択肢がある (大文字小文字・空白だけの違いも重複)")
            nb = [c for c in choices if _numbered_choice(c)]
            if nb:
                probs.append(f"選択肢の頭に番号・記号がある「{nb[0][:12]}」(アプリが ①②③… を付ける)")
            if "\n" in "".join(choices):
                probs.append("選択肢の中に改行がある")
        if probs:
            r.err("E_CHOICES", where, "・".join(probs))
            if not (n_ok[0] <= len(choices) <= n_ok[1]) or not all(isinstance(c, str) and c.strip() for c in choices):
                choices = None
    it["choices"] = choices
    cno = q.get("correct_choice_no", None)
    if "correct_choice_no" not in q:
        r.err("E_CORRECT_NO", where, "correct_choice_no (1 始まりの正解番号) が無い")
    elif isinstance(cno, list):
        r.err("E_CORRECT_NO", where, "correct_choice_no が配列 (正解は 1 つだけ。2 つ選ぶ問題は組み合わせの選択肢に作り直す)")
    elif not _is_int(cno):
        r.err("E_CORRECT_NO", where, f"correct_choice_no が整数ではない ({cno!r}。true / \"3\" は不可)")
    elif choices is not None and not (1 <= cno <= len(choices)):
        r.err("E_CORRECT_NO", where, f"correct_choice_no={cno} が範囲外 (1〜{len(choices)}・1 始まり)")
    elif choices is not None:
        it["correct"] = cno
    expl = q.get("explanation")
    if not isinstance(expl, str) or not expl.strip():
        r.err("E_EXPL_HEAD", where, "explanation (解説) が無い (全問必須)")
        expl = None
    it["explanation"] = expl
    for fld, val in (("stem", stem), ("explanation", expl)):
        if isinstance(val, str) and _KATEX_RE.search(val):
            r.err("E_KATEX", f"{where} {fld}", "$ \\( \\[ は数式として描画されて崩れる (金額は「20ドル」「＄20」と書く)")
    if choices and any(_KATEX_RE.search(c) for c in choices):
        r.err("E_KATEX", f"{where} choices", "選択肢に $ \\( \\[ がある (金額は「20ドル」「＄20」と書く)")
    if isinstance(stem, str):
        m = _MULTI_RE.search(stem)
        if m:
            r.err("E_MULTI_SELECT", where, f"「{m.group(0)}」のような 2 つ以上を選ぶ問題は不可 (正解が 1 つの組み合わせの選択肢にする)")
        _check_conditional(r, where, stem)
    _check_text_figure(r, f"{where} stem", stem)
    if choices:
        for c in choices:
            _check_text_figure(r, f"{where} choices", c)
    if expl and choices and it["correct"] is not None:
        _check_explanation(r, kind, where, expl, choices, it["correct"], body if isinstance(body, str) else "")
    if isinstance(body, str) and isinstance(stem, str) and choices:
        it["hash"] = item_hash(body, stem, choices)
    return it


# ---------------------------------------------------------------------------
# 英語長文 (仕様書 3 章)
# ---------------------------------------------------------------------------
def _check_english_long(r, doc):
    items = []
    set_id = doc.get("set_id")
    if not (isinstance(set_id, str) and re.fullmatch(r"[A-Z0-9]{2,8}", set_id)):
        r.err("E_ID", "set_id", "set_id は英大文字と数字で 2〜8 字 (例 L1S001)")
    r.doc_id = set_id if isinstance(set_id, str) else ""
    unit = doc.get("unit")
    if not isinstance(unit, str) or unit not in ENGLONG_UNITS:
        r.err("E_UNIT", "unit", f"unit「{unit}」は {' / '.join(ENGLONG_UNITS)} のどれか (1 文字でも違うと取り込まれない)")
    else:
        r.units = [unit]
    _check_copyright(r, doc)
    for k in ("created",):
        if k in doc and not (isinstance(doc[k], str) and _DATE_RE.match(doc[k])):
            r.err("E_FORMAT", k, f"{k} は YYYY-MM-DD")
    passages = doc.get("passages")
    if not isinstance(passages, list) or not passages:
        r.err("E_FORMAT", "passages", "passages (本文と設問) が無い")
        return items
    if len(passages) > ENGLONG_MAX_PASSAGES:
        r.err("E_SIZE", "passages", f"1 ファイルの本文は {ENGLONG_MAX_PASSAGES} 本まで (いま {len(passages)} 本)")
    seen_pid, seen_qid, bodies, qkeys = set(), set(), {}, {}
    guide = ENGLONG_GUIDE.get(unit) if isinstance(unit, str) else None
    for i, p in enumerate(passages, 1):
        where = f"本文{i}"
        if not isinstance(p, dict):
            r.err("E_FORMAT", where, "本文が object ではない")
            continue
        pid = p.get("pid")
        if not (isinstance(pid, str) and re.fullmatch(r"P\d{2}", pid)):
            r.err("E_ID", where, "pid は P01 の形")
            pid = None
        elif pid in seen_pid:
            r.err("E_ID", pid, f"pid {pid} が重複")
        else:
            seen_pid.add(pid)
            where = pid
        r.n_groups += 1
        title = p.get("title")
        if title is not None and not isinstance(title, str):
            r.err("E_FORMAT", f"{where} title", "title は文字列")
        elif isinstance(title, str) and len(title) > ENGLONG_TITLE_MAX:
            r.err("E_SIZE", f"{where} title", f"title は {ENGLONG_TITLE_MAX} 字以内")
        _check_text_figure(r, f"{where} title", title)
        body = p.get("body")
        if not isinstance(body, str) or not body.strip():
            r.err("E_FORMAT", f"{where} body", "body (本文) が無い")
            body = None
        bja = p.get("body_ja")
        if not isinstance(bja, str) or not bja.strip():
            r.err("E_FORMAT", f"{where} body_ja", "body_ja (全訳) が無い (英語長文は必須・生徒には解き終えた後だけ見える)")
        qs = p.get("questions")
        if not isinstance(qs, list):
            r.err("E_FORMAT", f"{where} questions", "questions が無い")
            qs = []
        if body is not None:
            words = _english_words(body)
            if words > ENGLONG_MAX_WORDS:
                r.err("E_SIZE", f"{where} body", f"本文は 1 本 {ENGLONG_MAX_WORDS} 語まで (いま {words} 語)")
            elif guide and not (guide[0] <= words <= guide[1]):
                r.warn("W_WORDS", f"{where} body", f"「{unit}」の本文の目安は {guide[0]}〜{guide[1]} 語 (いま {words} 語)")
            hk = norm_ws(body).lower()
            if hk in bodies:
                r.err("E_DUP", where, f"本文が {bodies[hk]} と同じ")
            bodies.setdefault(hk, where)
            _check_text_figure(r, f"{where} body", body)
            _check_conditional(r, f"{where} body", body)
            _check_tables(r, f"{where} body", body)
        if not (ENGLONG_Q_RANGE[0] <= len(qs) <= ENGLONG_Q_RANGE[1]):
            r.err("E_SIZE", f"{where} questions", f"設問は 1 本あたり {ENGLONG_Q_RANGE[0]}〜{ENGLONG_Q_RANGE[1]} 問 (いま {len(qs)} 問)")
        elif guide and not (guide[2] <= len(qs) <= guide[3]):
            r.warn("W_QUESTIONS", f"{where} questions", f"「{unit}」の設問数の目安は {guide[2]}〜{guide[3]} 問 (いま {len(qs)} 問)")
        stems = []
        for j, q in enumerate(qs, 1):
            qwhere = f"{where}-Q{j}"
            qid = q.get("qid") if isinstance(q, dict) else None
            if not (isinstance(qid, str) and re.fullmatch(r"P\d{2}-Q[1-9]", qid) and (pid is None or qid.startswith(pid + "-"))):
                r.err("E_ID", qwhere, f"qid は {pid or 'P01'}-Q1 の形 (本文の pid で始める)")
                qid = None
            elif qid in seen_qid:
                r.err("E_ID", qwhere, f"qid {qid} が重複")
                qid = None
            else:
                seen_qid.add(qid)
                qwhere = qid
            if isinstance(q, dict):
                t = q.get("type")
                t0 = re.sub(r"[（(].*[）)]\s*$", "", t).strip() if isinstance(t, str) else t
                if t0 not in ENGLONG_TYPES:
                    if isinstance(t, str) and re.search(r"[2２二]つ|複数|すべて|全て", t):
                        r.err("E_MULTI_SELECT", qwhere, f"type「{t}」は不可 (2 つ選ぶ問題は作れない)")
                    else:
                        r.err("E_FORMAT", qwhere, f"type「{t}」は {'／'.join(ENGLONG_TYPES)} のどれか (記述・和訳・要約・整序は不可)")
            it = _check_question(r, "english_long", qwhere, q, body, where)
            it["qid"] = qid
            items.append(it)
            stems.append(it["stem"])
            if it["stem"] and it["choices"]:
                k = (squash(it["stem"]).lower(), tuple(squash(c).lower() for c in it["choices"]))
                if k in qkeys:
                    r.err("E_DUP", qwhere, f"{qkeys[k]} と同じ問題 (問題文と選択肢が同じ)")
                qkeys.setdefault(k, qwhere)
        if body is not None:
            _check_blanks(r, where, body, stems)
            _check_underlines(r, where, body, stems)
    return items


# ---------------------------------------------------------------------------
# 習熟度テスト (仕様書 4 章)
# ---------------------------------------------------------------------------
def _check_skill(r, where, skill):
    if skill is None:
        return
    if not isinstance(skill, dict) or set(skill) - {"subject", "unit"}:
        r.err("E_SKILL", where, "skill は {\"subject\": …, \"unit\": …} か null")
        return
    s, u = skill.get("subject"), skill.get("unit")
    if not isinstance(s, str) or not isinstance(u, str):
        r.err("E_SKILL", where, "skill の subject と unit は文字列")
        return
    if s in SKILL_NO_UNIT_SUBJECTS:
        r.warn("W_SKILL", where, f"skill の科目 {s} は単元名が決まっていないので外して取り込む (仕様書 10 章)")
        return
    if s not in SKILL_UNITS:
        r.err("E_SKILL", where, f"skill の科目「{s}」は使えない ({' / '.join(sorted(SKILL_UNITS))} のどれか)")
        return
    if u not in SKILL_UNITS[s]:
        r.err("E_SKILL", where, f"skill の単元「{u}」は {s} の単元に無い (仕様書 10 章の一覧と完全に一致させる)")


def _check_ptest(r, doc):
    items = []
    test_id = doc.get("test_id")
    if not (isinstance(test_id, str) and re.fullmatch(r"[A-Z0-9]{3,10}", test_id)):
        r.err("E_ID", "test_id", "test_id は英大文字と数字で 3〜10 字 (例 HSENG01)")
    r.doc_id = test_id if isinstance(test_id, str) else ""
    probs = []
    if not isinstance(doc.get("target"), str) or doc.get("target") not in PTEST_TARGETS:
        probs.append("target は \"kosei\" か \"chugaku\"")
    if doc.get("subject_ja") not in PTEST_SUBJECT_JA:
        probs.append(f"subject_ja は {'・'.join(PTEST_SUBJECT_JA)} のどれか")
    se = doc.get("series_ja")
    if not (isinstance(se, str) and 1 <= len(se) <= 10 and not re.search(r"\s", se)):
        probs.append("series_ja は 10 字以内・空白なし")
    if not (_is_int(doc.get("round")) and 1 <= doc.get("round") <= 99):
        probs.append("round は 1〜99 の整数")
    rev = doc.get("revision", 0)
    if not (_is_int(rev) and 0 <= rev <= 9):
        probs.append("revision は 0〜9 の整数 (直した版は 1 = 「第N回改1」)")
    unit = ptest_unit_name(doc)
    if not probs and not PTEST_UNIT_RE.match(unit):
        probs.append(f"組み立てた単元名「{unit}」がサーバの形に合わない")
    if "unit" in doc and doc.get("unit") != unit:
        probs.append(f"unit は書かない (取込スクリプトが「{unit}」を作る)")
    if probs:
        r.err("E_UNIT", "単元", "・".join(probs))
    else:
        r.units = [unit]
    if not (isinstance(doc.get("subject"), str) and doc.get("subject").strip()):
        r.err("E_FORMAT", "subject", "subject (例 \"english\") が無い")
    title = doc.get("title")
    if not (isinstance(title, str) and title.strip() and len(title) <= 120):
        r.err("E_FORMAT", "title", "title (テストの名前・120 字以内) が無い")
    tl = doc.get("time_limit_min")
    if tl is not None and not (_is_int(tl) and 1 <= tl <= 600):
        r.err("E_FORMAT", "time_limit_min", "time_limit_min は分の整数か null")
    if "created" in doc and not (isinstance(doc["created"], str) and _DATE_RE.match(doc["created"])):
        r.err("E_FORMAT", "created", "created は YYYY-MM-DD")
    _check_copyright(r, doc)
    sections = doc.get("sections")
    if not isinstance(sections, list) or not sections:
        r.err("E_FORMAT", "sections", "sections (大問) が無い")
        return items
    if len(sections) > PTEST_MAX_SECTIONS:
        r.err("E_SIZE", "sections", f"大問は {PTEST_MAX_SECTIONS} 個まで (いま {len(sections)} 個)")
    total = sum(len(s.get("questions") or []) for s in sections if isinstance(s, dict) and isinstance(s.get("questions"), list))
    if total > PTEST_MAX_QUESTIONS:
        r.err("E_SIZE", "sections", f"1 回分は合計 {PTEST_MAX_QUESTIONS} 問まで (いま {total} 問)")
    bodies, qkeys, qn = {}, {}, 0
    id_probs = []
    for i, sec in enumerate(sections, 1):
        where = f"大問{i}"
        if not isinstance(sec, dict):
            r.err("E_FORMAT", where, "大問が object ではない")
            continue
        if sec.get("section_no") != i:
            id_probs.append(f"{where} の section_no が {sec.get('section_no')!r} (1 から並び順のとおりに)")
        r.n_groups += 1
        title = sec.get("title")
        if title is not None and not (isinstance(title, str) and len(title) <= PTEST_TITLE_MAX):
            r.err("E_SIZE", f"{where} title", f"大問の title は {PTEST_TITLE_MAX} 字以内の文字列")
        _check_text_figure(r, f"{where} title", title)
        body = sec.get("body")
        if not isinstance(body, str) or not body.strip():
            r.err("E_FORMAT", f"{where} body", "body が無い (読む文章の無い大問も指示文を書く)")
            body = None
        elif not _SECTION_HEAD_RE.match(body):
            r.err("E_FORMAT", f"{where} body", "大問の body は「第N問」で書き始める (同じ文の本文は重複として飛ばされるため)")
        bja = sec.get("body_ja")
        if bja is not None and not isinstance(bja, str):
            r.err("E_FORMAT", f"{where} body_ja", "body_ja は文字列か null")
        if body is not None:
            hk = norm_ws(body).lower()
            if hk in bodies:
                r.err("E_DUP", where, f"body が {bodies[hk]} と同じ (サーバが重複として飛ばし、設問が消える)")
            bodies.setdefault(hk, where)
            _check_text_figure(r, f"{where} body", body)
            _check_conditional(r, f"{where} body", body)
            _check_tables(r, f"{where} body", body)
        qs = sec.get("questions")
        if not isinstance(qs, list) or not (1 <= len(qs) <= PTEST_SECTION_Q_MAX):
            r.err("E_SIZE", f"{where} questions", f"1 つの大問に 1〜{PTEST_SECTION_Q_MAX} 問")
            qs = qs if isinstance(qs, list) else []
        stems = []
        for q in qs:
            qn += 1
            want = f"Q{qn:02d}"
            qid = q.get("qid") if isinstance(q, dict) else None
            qwhere = f"{where} {qid if isinstance(qid, str) else want}"
            if qid != want:
                id_probs.append(f"{qwhere} の qid は {want} (Q01 から出題順の通し番号・欠番なし)")
            it = _check_question(r, "proficiency_test", qwhere, q, body, where)
            it["qid"] = qid if isinstance(qid, str) else None
            items.append(it)
            stems.append(it["stem"])
            if isinstance(q, dict):
                _check_skill(r, qwhere, q.get("skill"))
            if it["stem"] and it["choices"]:
                k = (squash(it["stem"]).lower(), tuple(squash(c).lower() for c in it["choices"]))
                if k in qkeys:
                    r.err("E_DUP", qwhere, f"{qkeys[k]} と同じ問題 (問題文と選択肢が同じ)")
                qkeys.setdefault(k, qwhere)
        if body is not None:
            _check_blanks(r, where, body, stems)
            _check_underlines(r, where, body, stems)
    if id_probs:
        r.err("E_ID", "番号", "・".join(id_probs[:5]) + (f" ほか {len(id_probs) - 5} 件" if len(id_probs) > 5 else ""))
    qids = [it["qid"] for it in items if it["qid"]]
    if len(set(qids)) != len(qids):
        r.err("E_ID", "qid", "qid が重複している")
    return items


# ---------------------------------------------------------------------------
# 正解の位置・読まずに当たる (仕様書 3・4 章)
# ---------------------------------------------------------------------------
def _check_positions(r, kind, items):
    seq = [it for it in items if it["correct"] is not None and it["choices"] and (kind == "english_long" or len(it["choices"]) == 4)]
    probs = []
    n = len(seq)
    if n >= 3:
        counts = {}
        for it in seq:
            counts[it["correct"]] = counts.get(it["correct"], 0) + 1
        for k in sorted(counts):
            if counts[k] * 10 > n * 4:
                probs.append(f"{CIRCLED[k - 1]} が {counts[k]}/{n} 問で 40% を超える")
    run, prev = 0, None
    for it in seq:
        run = run + 1 if it["correct"] == prev else 1
        prev = it["correct"]
        if run == 4:
            probs.append(f"同じ番号 {CIRCLED[prev - 1]} の正解が 4 問続く ({it['where']} まで)")
    if kind == "proficiency_test":
        groups = {}
        for it in seq:
            groups.setdefault(it["group"], []).append(it["correct"])
        for g, cs in groups.items():
            if len(cs) >= 4 and len(set(cs)) == 1:
                probs.append(f"{g} の 4 択の正解が全部 {CIRCLED[cs[0] - 1]}")
    if probs:
        r.err("E_POSITION", "正解の位置", "・".join(probs))
    if kind == "english_long" and n:
        longest = 0
        for it in seq:
            lens = [len(norm_ws(c)) for c in it["choices"]]
            c = lens[it["correct"] - 1]
            if all(c > x for i, x in enumerate(lens) if i != it["correct"] - 1):
                longest += 1
        if longest * 2 > n:
            r.warn("W_LONGEST", "正解の位置", f"正解がいちばん長い選択肢である問題が {longest}/{n} 問 (半分以下にする)")


def _tokens(s):
    en = {w.lower() for w in _EN_WORD_RE.findall(s) if len(w) >= 4} - _STOP_EN
    ja = set(_JA_TOKEN_RE.findall(s)) - _STOP_JA
    return en | ja


def _check_giveaway(r, items):
    for it in items:
        if it["correct"] is None or not it["choices"] or not it["stem"]:
            continue
        st = _tokens(it["stem"])
        ok = _tokens(it["choices"][it["correct"] - 1])
        other = set()
        for i, c in enumerate(it["choices"]):
            if i != it["correct"] - 1:
                other |= _tokens(c)
        hits = sorted(t for t in st if t in ok and t not in other)
        if hits:
            r.warn("W_GIVEAWAY", it["where"], f"問題文の語 {hits[:3]} が正解の選択肢にだけ出る (読まずに当たる)")


# ---------------------------------------------------------------------------
# 盲検の記録と解答用紙 (仕様書 6 章)
# ---------------------------------------------------------------------------
def _check_review(r, doc, items, base_dir):
    rv = doc.get("_review")
    if not isinstance(rv, dict) or rv.get("protocol") != REVIEW_PROTOCOL:
        r.err("E_REVIEW_MISSING", "_review", f"盲検の記録 (_review・protocol \"{REVIEW_PROTOCOL}\") が無い (仕様書 6 章)")
        r.review_status = "記録なし"
        return
    probs = []
    blind = rv.get("blind") if isinstance(rv.get("blind"), dict) else {}
    solvers = blind.get("solvers") if isinstance(blind.get("solvers"), list) else []
    dropped = blind.get("dropped_qids", [])
    if not isinstance(dropped, list) or not all(isinstance(x, str) for x in dropped):
        probs.append("dropped_qids は qid の配列")
        dropped = []
    present = {it["qid"] for it in items if it["qid"]}
    still = sorted(set(dropped) & present)
    if still:
        probs.append(f"dropped_qids の {still} がまだファイルに残っている (消してから書く)")
    for name, need_file in (("uniqueness_review", True), ("explanation_review", False)) + (
            (("fact_check", True),) if r.kind == "english_long" else ()):
        v = rv.get(name)
        if not (isinstance(v, dict) and isinstance(v.get("by"), str) and v.get("by").strip()
                and isinstance(v.get("date"), str) and _DATE_RE.match(v.get("date"))):
            probs.append(f"{name} ({{by, date" + (", notes_file" if need_file else "") + "}) が無い")
            continue
        if need_file:
            nf = v.get("notes_file")
            if not (isinstance(nf, str) and os.path.isfile(os.path.join(base_dir, nf))):
                probs.append(f"{name} の notes_file「{nf}」が見つからない")
    labels, files, answers = [], set(), {}
    for i, s in enumerate(solvers):
        if not isinstance(s, dict):
            probs.append(f"solvers[{i}] が object ではない")
            continue
        lab = s.get("label")
        if not (isinstance(lab, str) and lab.strip()) or lab in labels:
            probs.append(f"solvers[{i}] の label が無い・重複")
            continue
        if not (isinstance(s.get("date"), str) and _DATE_RE.match(s.get("date"))) or not (isinstance(s.get("kind"), str) and s.get("kind")):
            probs.append(f"解き手 {lab} の kind / date (YYYY-MM-DD) が無い")
        af = s.get("answers_file")
        full = os.path.realpath(os.path.join(base_dir, af)) if isinstance(af, str) and af else ""
        if not full or not os.path.isfile(full):
            probs.append(f"解き手 {lab} の解答用紙「{af}」が見つからない")
            continue
        if full in files:
            probs.append(f"解き手 {lab} の解答用紙が別の解き手と同じファイル")
            continue
        files.add(full)
        try:
            _, ans = read_json(full)
        except (OSError, ValueError) as e:
            probs.append(f"解き手 {lab} の解答用紙が読めない ({e})")
            continue
        if not isinstance(ans, dict) or ans.get("format") != ANSWERS_FORMAT or not isinstance(ans.get("answers"), list):
            probs.append(f"解き手 {lab} の解答用紙の形が違う (format \"{ANSWERS_FORMAT}\" と answers)")
            continue
        if ans.get("solver") != lab:
            probs.append(f"解き手 {lab} の解答用紙の solver が「{ans.get('solver')}」")
            continue
        amap = {}
        for a in ans["answers"]:
            if isinstance(a, dict) and isinstance(a.get("qid"), str):
                if a["qid"] in amap:
                    probs.append(f"解き手 {lab} の解答用紙に {a['qid']} が 2 回")
                amap[a["qid"]] = a
        labels.append(lab)
        answers[lab] = amap
    if len(labels) < 3:
        probs.append(f"解答用紙のそろった解き手が 3 名に足りない ({len(labels)} 名)")
    if probs:
        r.err("E_REVIEW_MISSING", "_review", "・".join(probs))
        r.review_status = "記録が不完全"
        return
    stale, mismatch, missing = {}, {}, {}
    for lab in labels:
        amap = answers[lab]
        exact = minus = plus = zero = 0
        rows = []
        for it in items:
            if not it["qid"] or it["hash"] is None or it["correct"] is None:
                continue
            a = amap.get(it["qid"])
            if a is None:
                missing.setdefault(it["qid"], []).append(lab)
                continue
            if a.get("item_hash") != it["hash"]:
                stale.setdefault(it["qid"], []).append(lab)
                continue
            cn = a.get("choice_no")
            note = a.get("note") if isinstance(a.get("note"), str) else ""
            rows.append((it, cn, note))
            if _is_int(cn):
                exact += cn == it["correct"]
                minus += cn == it["correct"] - 1
                plus += cn == it["correct"] + 1
                zero += cn == 0
        shifted = max(minus, plus)
        if zero or (shifted >= 2 and shifted > exact):
            r.err("E_BLIND_OFFSET", f"解き手 {lab}",
                  f"解答用紙の番号の基準がずれている疑い (正解と一致 {exact} 問・1 つ隣と一致 {shifted} 問"
                  + ("・0 番がある" if zero else "") + ")。choice_no は 1 始まり (① = 1) で書き直す")
            continue
        for it, cn, note in rows:
            why = ""
            if not _is_int(cn) or not (1 <= cn <= len(it["choices"])):
                why = f"choice_no {cn!r} が 1〜{len(it['choices'])} の整数でない"
            elif cn != it["correct"]:
                why = f"{CIRCLED[cn - 1]} と答えた (正解 {CIRCLED[it['correct'] - 1]})"
            if _AMBIG_RE.search(note):
                why = (why + "・" if why else "") + f"note「{note[:30]}」"
            if why:
                mismatch.setdefault(it["qid"], []).append(f"{lab}: {why}")
    for qid, labs in sorted(missing.items()):
        r.err("E_REVIEW_MISSING", qid, f"解き手 {'・'.join(labs)} の答えが無い")
    for qid, labs in sorted(stale.items()):
        r.err("E_BLIND_STALE", qid, f"解き手 {'・'.join(labs)} の答えは直す前の問題 (item_hash が違う)。直した問題の盲検をやり直す")
    for qid, whys in sorted(mismatch.items()):
        r.err("E_BLIND_MISMATCH", qid, "・".join(whys) + "。直して盲検をやり直すか、消して dropped_qids に書く")
    r.review_status = f"解き手 {len(labels)} 名 ({'・'.join(labels)}) の解答用紙を照合"


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def validate(path, check_review=True, check_location=True):
    """ファイル 1 本を検査して Report を返す。check_review=False は自己検査用 (盲検の照合を外す)。"""
    r = Report(path)
    if check_location:
        why = location_problem(path)
        if why:
            r.err("E_LOCATION", "ファイルの場所", f"{why}にある。リポジトリ・seed-data の外 (デスクトップの決まったフォルダ) に置く (仕様書 1-10)")
    try:
        raw, doc = read_json(path)
    except (OSError, ValueError) as e:
        r.err("E_FORMAT", "ファイル", str(e))
        return r
    r.file_sha256 = hashlib.sha256(raw).hexdigest()
    r.doc = doc
    if not isinstance(doc, dict):
        r.err("E_FORMAT", "ファイル", "ファイルの中身が JSON の object ではない")
        return r
    _check_hygiene(r, doc)
    if doc.get("format") != DOC_FORMAT:
        r.err("E_FORMAT", "format", f"\"format\": \"{DOC_FORMAT}\" が無い")
    kind = doc.get("kind")
    r.kind = kind if isinstance(kind, str) and kind in KIND_LABEL else ""
    if kind == "english_long":
        items = _check_english_long(r, doc)
    elif kind == "proficiency_test":
        items = _check_ptest(r, doc)
    else:
        r.err("E_FORMAT", "kind", "kind は \"english_long\" か \"proficiency_test\"")
        return r
    r.n_questions = len(items)
    for it in items:
        if it["qid"] and it["hash"]:
            r.item_hashes[it["qid"]] = it["hash"]
    _check_positions(r, kind, items)
    _check_giveaway(r, items)
    if check_review:
        _check_review(r, doc, items, os.path.dirname(os.path.abspath(path)))
    else:
        r.review_status = "照合していない (自己検査)"
    return r


def print_report(r, out=None):
    out = out or sys.stdout
    w = out.write
    w(f"検査: {r.path}\n")
    if r.kind:
        unit = "・".join(f"「{u}」" for u in r.units) or "(単元名が不正)"
        w(f"  {KIND_LABEL[r.kind]} ({r.kind})  {'set_id' if r.kind == 'english_long' else 'test_id'} {r.doc_id or '?'}  単元 {unit}"
          f"  {'本文' if r.kind == 'english_long' else '大問'} {r.n_groups}・設問 {r.n_questions}\n")
        w(f"  盲検: {r.review_status}\n")
    if r.errors:
        w(f"エラー {len(r.errors)} 件:\n")
        for c, where, m in r.errors:
            w(f"  ✗ {c}  {where}: {m}\n")
    if r.warnings:
        w(f"警告 {len(r.warnings)} 件 (中身を確かめる。取込スクリプトは --accept-warnings が無いと止まる):\n")
        for c, where, m in r.warnings:
            w(f"  ! {c}  {where}: {m}\n")
    if not r.errors:
        w("結果: エラーなし" + (f" (警告 {len(r.warnings)} 件)" if r.warnings else "") + "\n")
    else:
        only_review = all(c == "E_REVIEW_MISSING" for c, _, _ in r.errors)
        w("結果: エラーあり" + (" (盲検の記録だけ = 盲検に進めます: --make-blind)" if only_review else "") + "\n")


# ---------------------------------------------------------------------------
# 盲検のシート (仕様書 6 章 2)
# ---------------------------------------------------------------------------
class BlindError(Exception):
    pass


BLIND_INSTRUCTIONS = (
    "このシートには正解・解説・全訳が入っていません。本文と問題だけを読んで全問を解いてください。"
    "answer_template.json を写して solver (解き手の記号 A/B/C)・date (YYYY-MM-DD) を書き、各問の choice_no に選んだ番号を"
    "1 始まり (① = 1, ② = 2, …) で書きます。item_hash はシートの値をそのまま写します (変えない)。"
    "正解が 2 つある・どれも正しくない・問題があいまい、と思ったら note に書きます。"
    "作者・正解を見たセッションは解き手になれません。")


def blind_sheet(doc, hashes):
    kind = doc.get("kind")
    sheet = {"format": SHEET_FORMAT, "kind": kind, "instructions": BLIND_INSTRUCTIONS}
    groups = []
    if kind == "english_long":
        sheet.update({"set_id": doc.get("set_id"), "unit": doc.get("unit")})
        for p in doc.get("passages") or []:
            groups.append({"pid": p.get("pid"), "title": p.get("title"), "body": p.get("body"),
                           "questions": [{"qid": q.get("qid"), "item_hash": hashes.get(q.get("qid")), "type": q.get("type"),
                                          "stem": q.get("stem"), "choices": q.get("choices")} for q in p.get("questions") or []]})
        sheet["passages"] = groups
    else:
        sheet.update({"test_id": doc.get("test_id"), "title": doc.get("title"), "unit": ptest_unit_name(doc)})
        for s in doc.get("sections") or []:
            groups.append({"section_no": s.get("section_no"), "title": s.get("title"), "body": s.get("body"),
                           "questions": [{"qid": q.get("qid"), "item_hash": hashes.get(q.get("qid")),
                                          "stem": q.get("stem"), "choices": q.get("choices")} for q in s.get("questions") or []]})
        sheet["sections"] = groups
    return sheet


def blind_sheet_md(sheet):
    out = [f"# 盲検シート ({KIND_LABEL.get(sheet['kind'], sheet['kind'])}・{sheet.get('set_id') or sheet.get('test_id')})", "",
           sheet["instructions"], ""]
    for g in sheet.get("passages") or sheet.get("sections") or []:
        head = g.get("pid") or f"大問 {g.get('section_no')}"
        out.append(f"## {head}" + (f" {g['title']}" if g.get("title") else ""))
        out.append("")
        out.append("```")
        out.append(g.get("body") or "")
        out.append("```")
        out.append("")
        for q in g["questions"]:
            out.append(f"### {q['qid']}  (item_hash {q['item_hash']})")
            out.append("")
            out.append(q.get("stem") or "")
            out.append("")
            for i, c in enumerate(q.get("choices") or []):
                out.append(f"- {CIRCLED[i] if i < len(CIRCLED) else i + 1} {c}")
            out.append("")
    return "\n".join(out) + "\n"


def answer_template(sheet):
    qs = [q for g in (sheet.get("passages") or sheet.get("sections") or []) for q in g["questions"]]
    return {"format": ANSWERS_FORMAT, "solver": "", "date": "",
            "answers": [{"qid": q["qid"], "item_hash": q["item_hash"], "choice_no": None, "note": ""} for q in qs]}


def make_blind(outdir, path):
    """盲検のシート (blind_sheet.json / .md) と解答用紙のひな形 (answer_template.json) を outdir に書き、書いたパスを返す。
    ★出力先が git リポジトリ・seed-data の中なら何も作らずに BlindError。盲検の記録以外のエラーが残っているファイルも BlindError。"""
    why = location_problem(outdir)
    if why:
        raise BlindError(f"出力先が{why}にあります。何も書いていません (シートにはテストの問題が入るので、リポジトリの外に置く)")
    r = validate(path)
    other = [e for e in r.errors if e[0] not in REVIEW_ERRORS]
    if other:
        raise BlindError("盲検の記録以外のエラーが残っています (先に直す): "
                         + "・".join(f"{c} {w}" for c, w, _ in other[:5]))
    sheet = blind_sheet(r.doc, r.item_hashes)
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for name, text in (("blind_sheet.json", json.dumps(sheet, ensure_ascii=False, indent=1) + "\n"),
                       ("blind_sheet.md", blind_sheet_md(sheet)),
                       ("answer_template.json", json.dumps(answer_template(sheet), ensure_ascii=False, indent=1) + "\n")):
        p = os.path.join(outdir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        paths.append(p)
    return paths


# ---------------------------------------------------------------------------
# 自己検査 (引数なし。scripts/run_all_gates.py が毎 push 回す)
# ---------------------------------------------------------------------------
# item_hash の既知の値。★ここが変わる = 記録済みの盲検が全部無効になる。式を変えるなら仕様書と一緒に版を上げる
_HASH_VECTOR = (("Body ( 1 ) text.", "( 1 ) に入れるのに最も適切なものを選びなさい。", ["As a result", "In contrast"]), "591414cea42e4b56")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_doc(dirpath, name, doc):
    p = os.path.join(dirpath, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return p


def _set_first_line(q, text):
    lines = q["explanation"].split("\n")
    lines[0] = text
    q["explanation"] = "\n".join(lines)


def self_test():
    fx = os.path.join(HERE, "fixtures")
    if not os.path.isdir(fx):
        print("自己検査の fixtures/ が隣にありません。ファイルを検査するときは: python3 -I validate_drill_import.py <ファイル>")
        return 2
    bad = []
    done = []

    def expect(label, cond, detail=""):
        if cond:
            done.append(label)
        else:
            bad.append(f"{label}  {detail}"[:400])

    got_hash = item_hash(*_HASH_VECTOR[0])
    expect("item_hash の既知の値", got_hash == _HASH_VECTOR[1], f"{got_hash} != {_HASH_VECTOR[1]}")
    with tempfile.TemporaryDirectory(prefix="drill-validate-") as tmp:
        work = os.path.join(tmp, "fixtures")
        shutil.copytree(fx, work)
        names = sorted(n for n in os.listdir(work) if n.endswith(".json"))
        oks = [n for n in names if n.startswith("ok_")]
        bads = [n for n in names if n.startswith("bad_")]
        expect("fixtures に ok_ が 2 本以上・bad_ が 10 本以上", len(oks) >= 2 and len(bads) >= 10, (oks, len(bads)))
        kinds_ok = set()
        for n in oks:
            r = validate(os.path.join(work, n))
            kinds_ok.add(r.kind)
            expect(f"{n}: エラー・警告なし", not r.errors and not r.warnings,
                   [e[:2] for e in r.errors + r.warnings][:6])
        expect("ok_ に英語長文と習熟度テストの両方", kinds_ok == {"english_long", "proficiency_test"}, kinds_ok)
        seen_codes = set()
        for n in bads:
            d = _load(os.path.join(work, n))
            want = sorted(set(d.get("_expect") or []))
            review = "_review" in d or "E_REVIEW_MISSING" in want
            r = validate(os.path.join(work, n), check_review=review)
            seen_codes |= set(r.error_codes())
            expect(f"{n} → {' '.join(want)}", want and r.error_codes() == want,
                   f"出たコード {r.error_codes()} / {[e[:2] for e in r.errors][:4]}")
            expect(f"{n}: _fixture: true", d.get("_fixture") is True)
        # コードで組み立てる例 (メールはファイルに書かない: 公開リポジトリの個人情報検査に当たるため)
        el = _load(os.path.join(work, "ok_english_long.json"))
        pt = _load(os.path.join(work, "ok_proficiency_test.json"))
        d = json.loads(json.dumps(el))
        d["passages"][0]["questions"][0]["explanation"] += "\n【語句】連絡は " + "fixture" + "@" + "example.org" + " へ (架空)"
        r = validate(_write_doc(work, "code_email.json", d))
        expect("ASCII のメールアドレス → E_EMAIL (解説だけの変更なので盲検は有効のまま)", r.error_codes() == ["E_EMAIL"], r.error_codes())
        d = json.loads(json.dumps(el))
        d["unit"] = "長文 Lv.2"
        r = validate(_write_doc(work, "code_words.json", d), check_review=False)
        expect("単元の語数の目安の外 → W_WORDS (エラーなし)", not r.errors and "W_WORDS" in r.warning_codes(), (r.error_codes(), r.warning_codes()))
        d = json.loads(json.dumps(el))
        for q in d["passages"][0]["questions"][:3]:
            n = q["correct_choice_no"]
            q["choices"][n - 1] = q["choices"][n - 1] + " in every single part of the long story told here"
            _set_first_line(q, f"正解 {CIRCLED[n - 1]} {q['choices'][n - 1]}")
        r = validate(_write_doc(work, "code_longest.json", d), check_review=False)
        expect("正解がいちばん長い問題が半分超 → W_LONGEST (エラーなし)", not r.errors and r.warning_codes() == ["W_LONGEST"],
               (r.error_codes(), r.warning_codes()))
        d = json.loads(json.dumps(el))
        tgt = next(q for q in d["passages"][0]["questions"] if q["type"] == "内容一致")
        word = max(_tokens(tgt["choices"][tgt["correct_choice_no"] - 1]) - set().union(
            *[_tokens(c) for i, c in enumerate(tgt["choices"]) if i != tgt["correct_choice_no"] - 1]), key=len)
        tgt["stem"] = f"Which statement about the {word} is true?"
        r = validate(_write_doc(work, "code_giveaway.json", d), check_review=False)
        expect("問題文の語が正解にだけ出る → W_GIVEAWAY (エラーなし)", not r.errors and r.warning_codes() == ["W_GIVEAWAY"],
               (r.error_codes(), r.warning_codes()))
        d = json.loads(json.dumps(pt))
        sk = next(q for s in d["sections"] for q in s["questions"] if q.get("skill"))
        sk["skill"] = {"subject": "math", "unit": "二次関数"}
        r = validate(_write_doc(work, "code_skill.json", d))
        expect("高校の math の skill → W_SKILL (外して取り込む・エラーなし)", not r.errors and r.warning_codes() == ["W_SKILL"],
               (r.error_codes(), r.warning_codes()))
        d = json.loads(json.dumps(el))
        ch = d["passages"][0]["questions"][0]["choices"]
        ch[0] = " " + unicodedata.normalize("NFKC", ch[1]).upper().replace(" ", "  ").replace("A", "Ａ", 1) + " "
        r = validate(_write_doc(work, "code_dupchoice.json", d), check_review=False)
        expect("全角・大文字・空白だけの違いの選択肢 → E_CHOICES", "E_CHOICES" in r.error_codes(), r.error_codes())
        # 盲検のシート → 3 名が解く → 照合
        for n, doc in (("ok_english_long.json", el), ("ok_proficiency_test.json", pt)):
            src = os.path.join(work, n)
            out = os.path.join(tmp, "blind_" + n[:-5])
            paths = make_blind(out, src)
            expect(f"{n}: --make-blind で 3 ファイル", [os.path.basename(p) for p in paths]
                   == ["blind_sheet.json", "blind_sheet.md", "answer_template.json"], paths)
            text = "".join(open(p, encoding="utf-8").read() for p in paths)
            sheet = _load(paths[0])
            groups = doc.get("passages") or doc.get("sections")
            leaks = [k for k in ("correct_choice_no", "explanation", "body_ja", "skill", "【根拠】", "【他の選択肢】") if k in text]
            leaks += [g["body_ja"][:20] for g in groups if g.get("body_ja") and g["body_ja"][:20] in text]
            leaks += [q["explanation"].split("\n")[0] for g in groups for q in g["questions"] if q["explanation"].split("\n")[0] in text]
            expect(f"{n}: シートに正解・解説・全訳・skill が入っていない", not leaks, leaks[:3])
            r0 = validate(src)
            tmpl = _load(paths[2])
            expect(f"{n}: 解答用紙のひな形 = 全問・item_hash は検査と同じ・choice_no は空",
                   {a["qid"]: a["item_hash"] for a in tmpl["answers"]} == r0.item_hashes
                   and all(a["choice_no"] is None for a in tmpl["answers"]), tmpl["answers"][:2])
            expect(f"{n}: シートの問題数", sum(len(g["questions"]) for g in (sheet.get("passages") or sheet.get("sections")))
                   == r0.n_questions)
            correct = {q["qid"]: q["correct_choice_no"] for g in groups for q in g["questions"]}
            d = json.loads(json.dumps(doc))
            d.pop("_review", None)
            solvers = []
            for lab in "XYZ":
                ans = json.loads(json.dumps(tmpl))
                ans.update({"solver": lab, "date": "2026-10-21"})
                for a in ans["answers"]:
                    a["choice_no"] = correct[a["qid"]]
                _write_doc(out, f"filled_{lab}.json", ans)
                solvers.append({"label": lab, "kind": "ai", "date": "2026-10-21",
                                "answers_file": os.path.join(os.path.basename(out), f"filled_{lab}.json")})
            nf = os.path.join(os.path.basename(out), "notes.md")
            with open(os.path.join(tmp, nf), "w", encoding="utf-8") as f:
                f.write("架空の記録\n")
            rv = {"protocol": REVIEW_PROTOCOL, "blind": {"solvers": solvers, "dropped_qids": []},
                  "uniqueness_review": {"by": "fixture", "date": "2026-10-21", "notes_file": nf},
                  "explanation_review": {"by": "fixture", "date": "2026-10-21"}}
            if doc["kind"] == "english_long":
                rv["fact_check"] = {"by": "fixture", "date": "2026-10-21", "notes_file": nf}
            d["_review"] = rv
            r = validate(_write_doc(tmp, "roundtrip_" + n, d))
            expect(f"{n}: シート → 3 名が正しく解く → 照合でエラーなし", not r.errors, [e[:2] for e in r.errors][:4])
            ans = _load(os.path.join(out, "filled_Z.json"))
            for a in ans["answers"]:
                a["choice_no"] = a["choice_no"] - 1
            _write_doc(out, "filled_Z.json", ans)
            r = validate(os.path.join(tmp, "roundtrip_" + n))
            expect(f"{n}: 解き手 1 名が 0 始まりで書いた → E_BLIND_OFFSET だけ", r.error_codes() == ["E_BLIND_OFFSET"], r.error_codes())
        # リポジトリの中には書かない
        if location_problem(HERE):
            inside = os.path.join(HERE, "fixtures", "_must_not_be_created")
            try:
                make_blind(inside, os.path.join(work, "ok_english_long.json"))
                refused = False
            except BlindError:
                refused = True
            expect("--make-blind の出力先がリポジトリの中なら拒否して何も作らない", refused and not os.path.exists(inside))
            r = validate(os.path.join(fx, "ok_english_long.json"))
            expect("リポジトリの中のファイル → E_LOCATION", r.error_codes() == ["E_LOCATION"], r.error_codes())
        else:
            done.append("(リポジトリの外で実行: E_LOCATION の実物の確認は省略)")
        expect("seed-data の中 → 拒否", bool(location_problem(os.path.join(tmp, "seed-data", "x.json"))))
        # コマンドとして (python3 -I・別のフォルダから)
        cp = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--json", os.path.join(work, "ok_proficiency_test.json")],
                            cwd=tmp, capture_output=True, encoding="utf-8")
        try:
            js = json.loads(cp.stdout)
        except ValueError:
            js = {}
        expect("python3 -I で別のフォルダから --json: exit 0・ok", cp.returncode == 0 and js.get("ok") is True
               and js.get("kind") == "proficiency_test", (cp.returncode, cp.stderr[-200:]))
        cp = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), os.path.join(work, "bad_multi_select.json")],
                            cwd=tmp, capture_output=True, encoding="utf-8")
        expect("エラーのあるファイルは exit 1", cp.returncode == 1, cp.returncode)
    for x in done:
        print(f"  ok  {x}")
    if bad:
        print(f"\n✗ 自己検査で期待と違う結果 {len(bad)} 件:")
        for x in bad:
            print(f"  ✗ {x}")
        return 1
    print(f"\n自己検査 PASS: {len(done)} 項目 (ok_ {len(oks)} 本・bad_ {len(bads)} 本・コードで組んだ例・--make-blind・照合)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="科目別ドリルの取込ファイル (英語長文・習熟度テスト) の検査 (取込仕様書 v1)")
    ap.add_argument("file", nargs="?", help="drill.json / test.json")
    ap.add_argument("--json", action="store_true", help="結果を JSON で出す")
    ap.add_argument("--make-blind", metavar="OUTDIR", help="盲検のシートと解答用紙のひな形をこのフォルダに書く")
    ap.add_argument("--self-test", action="store_true", help="自己検査 (引数なしと同じ)")
    a = ap.parse_args(argv)
    if a.self_test or (not a.file and not a.make_blind):
        return self_test()
    if not a.file:
        ap.error("ファイルを指定してください")
    if not os.path.isfile(a.file):
        print(f"ファイルが見つかりません: {a.file}", file=sys.stderr)
        return 2
    if a.make_blind:
        try:
            paths = make_blind(a.make_blind, a.file)
        except BlindError as e:
            print(f"✗ 盲検のシートを作りませんでした: {e}", file=sys.stderr)
            return 1
        print("盲検のシートを書きました (解き手にはシートだけを渡す。元のファイルは見せない):")
        for p in paths:
            print(f"  {p}")
        return 0
    r = validate(a.file)
    if a.json:
        print(json.dumps(r.to_json(), ensure_ascii=False, indent=1))
    else:
        print_report(r)
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main())
