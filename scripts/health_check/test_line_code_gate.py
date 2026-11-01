#!/usr/bin/env python3
"""🔒 LINE webhook が保護者のふつうのトークを「連携コード」と取り違えない (2026-11-01) の回帰テスト。

背景: 2026-11-01 本番で、保護者がメールアドレス入りのふつうの日本語のメッセージを送ると、bot が
  「⚠️ 連携コードが無効または期限切れです。マイページで新しいコードを発行してください。」と返した。
  webhook は本文全体を _normalize_link_code に通しており、これは [A-Za-z0-9_-] 以外を全部消す。
  日本語の文＋アドレス (例 …abcdefg1234@example.com…) が 20〜28 字の英数字に縮み、_LINE_CODE_LIKE に当たっていた。
  公式 LINE は有人チャットと併用で、bot が反応するのは決まった形 (連携コード・「やること」・「質問 …」) だけの約束。

固定する性質:
  [1] _line_code_candidate: 前後の空白・改行・全角空白・全角英数字・ゼロ幅文字 (ZWSP/BOM など) は吸収する。
      日本語・@・.・記号・文の途中の空白が残る本文は "" (コード判定に入れない)
  [2] 再現: 自然文＋アドレス・アドレスだけ・URL・空白入りの英文・日本語＋コードらしい英数字 → 連携済みでも未連携でも
      bot は何も返さない (reply も push もしない)。各例が旧の判定ではコードの分岐 (未連携なら「無効」・連携済みなら
      「すでに連携済み」) に入っていたことも確かめる (旧の判定はこのテストの中に固定して持つ)
  [3] 正しいコードは今までどおり連携できる (前後空白・改行・全角空白・全角・ZWSP 入り・BOM 付き・その組み合わせ)
  [4] 英数字だけの 20〜28 字 (全角・前後空白・ZWSP 付きも) は今までどおり「無効」を 1 回だけ返す。19 字・29 字は沈黙。
      連携済みの LINE が使用済みのコードを送り直したときの「すでに連携済み」も今までどおり
  [5] 前後に文の付いた有効なコード (「連携コード：…」「… よろしくお願いします」) は沈黙し、コードを消費しない
      (自然文はコード判定に入れない。保護者が質問の中にお子さまのコードを書いても、保護者の LINE に付かない)
  [6] 「やること」「質問 …」のコマンドは今までどおり。「質問 <英数字 20〜28 字>」は旧の判定では「無効」が返っていた
  [7] CI (server-tests.yml) に登録 (コメントでない run 行)

★_handle_line_event は例外を握りつぶしてログに出すだけなので、「何も返さない」が例外で途中終了した結果でないよう、
  送るたびに ERROR ログが出ていないことも見る。見えない文字はエスケープ表記で書く (エディタで消えても気づけるように)。
★外部通信なし (LINE API は偽物)・DB は一時 SQLite・生徒名とメールは架空 (公開リポジトリ)。

実行:
    python3 scripts/health_check/test_line_code_gate.py
    # exit 0 = PASS / 1 = FAIL
"""
import importlib.util
import logging
import os
import re
import sys
import tempfile
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []

INVALID = "⚠️ 連携コードが無効または期限切れです。マイページで新しいコードを発行してください。"
LINKED_OK = "✅ LINE連携が完了しました"
ALREADY = "✅ このLINEはすでに連携済みです。"

# 2026-11-01 までの webhook の判定 (本文全体から [A-Za-z0-9_-] 以外を消して 20〜28 字ならコードらしい)。
#   main.py の今の _LINE_CODE_LIKE / _normalize_link_code を将来変えても「再現」の前提が動かないよう、ここに固定する。
_OLD_LIKE = re.compile(r"^[A-Za-z0-9_-]{20,28}$")


def old_is_code_like(text):
    return bool(_OLD_LIKE.fullmatch(re.sub(r"[^A-Za-z0-9_-]", "", unicodedata.normalize("NFKC", text.strip()))))


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="line_code_gate_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        "DATABASE_URL": "",   # ★空にしないと本番 Postgres を見る
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_line_code_gate", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


_N = [0]


def mk(mod, line_user_id=None):
    """架空の生徒を 1 人作る (名前・メールは連番の架空値)。"""
    _N[0] += 1
    n = _N[0]
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO students (name, email, status, line_user_id) VALUES (?,?,?,?)",
              (f"テスト生徒{n}", f"gate-student-{n}@example.invalid", "paid", line_user_id))
    conn.commit()
    c.execute("SELECT id FROM students WHERE email = ?", (f"gate-student-{n}@example.invalid",))
    sid = c.fetchone()["id"]
    conn.close()
    return sid


def uid(tag):
    """架空の LINE userId (U + 32 字)。"""
    return "U" + (tag * 32)[:32]


def line_of(mod, sid):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT line_user_id FROM students WHERE id = ?", (sid,))
    r = c.fetchone()
    conn.close()
    return r["line_user_id"] if r else "<no row>"


def used_at(mod, code):
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT used_at FROM line_link_tokens WHERE token = ?", (code,))
    r = c.fetchone()
    conn.close()
    return r["used_at"] if r else "<no row>"


def fullwidth(s):
    """ASCII の英数字・記号を全角に (スマホのかな入力のまま打った形)。"""
    return "".join(chr(ord(ch) + 0xFEE0) if "!" <= ch <= "~" else ch for ch in s)


class FakeLine:
    """_line_api_call の偽物。送った先 (reply / push) と本文を覚える。"""
    def __init__(self):
        self.calls = []

    def __call__(self, endpoint, body):
        self.calls.append((endpoint, body))
        return True

    def texts(self):
        return [m.get("text") for _, b in self.calls for m in (b.get("messages") or [])]


class ErrorLog(logging.Handler):
    """main.py の log に付ける。_handle_line_event が握りつぶした例外 (ERROR ログ) を覚える。"""
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


ERRORS = ErrorLog()
_EV = [0]


def send(mod, fake, user, text):
    fake.calls.clear()
    ERRORS.records.clear()
    _EV[0] += 1
    mod._handle_line_event({"type": "message", "replyToken": f"rt-{_EV[0]}", "webhookEventId": f"ev-{_EV[0]}",
                            "source": {"type": "user", "userId": user}, "message": {"type": "text", "text": text}})
    if ERRORS.records:   # 「何も返さない」が例外で途中終了した結果なら落とす
        check(f"例外なしで処理する: {text[:30]!r}", False, ERRORS.records)
    return fake.texts()


def main():
    print("== LINE webhook: ふつうのトークを連携コードと取り違えない ==")
    mod = load_main()
    fake = FakeLine()
    mod._line_api_call = fake
    # コマンドの中身 (DB 集計・塾長へのメール) はこのテストの対象外。呼ばれたことと引数だけ覚える。
    todo_calls, question_calls = [], []
    mod._line_build_todo_text = lambda row: (todo_calls.append(row["id"]) or "TODO-STUB")
    mod._line_handle_question = lambda row, content, rt: question_calls.append((row["id"], content))
    mod.log.addHandler(ERRORS)
    mod.log.error("probe")
    check("ERROR ログを拾える", ERRORS.records == ["probe"], ERRORS.records)

    cand = mod._line_code_candidate

    print("[1] _line_code_candidate: コードだけの本文を取り出す")
    table = [
        ("", ""),
        (None, ""),
        ("  abc_DEF-123  ", "abc_DEF-123"),
        ("\nabc_DEF-123\n", "abc_DEF-123"),
        ("\u3000abc_DEF-123\u3000", "abc_DEF-123"),
        (fullwidth("abc_DEF-123"), "abc_DEF-123"),
        ("abc\u200b_DEF-123", "abc_DEF-123"),
        ("\ufeffabc_DEF-123", "abc_DEF-123"),
        ("abc\u200c\u200d\u2060_DEF-123", "abc_DEF-123"),
        ("\u200b abc_DEF-123 \u200b", "abc_DEF-123"),     # \u30bc\u30ed\u5e45\u6587\u5b57\u3092\u6d88\u3057\u3066\u304b\u3089\u524d\u5f8c\u306e\u7a7a\u767d\u3092\u843d\u3068\u3059
        ("abc_DEF-123\n\u200b", "abc_DEF-123"),
        ("abc_DEF-123\u2028", "abc_DEF-123"),             # NFKC \u3067 ASCII \u306b\u306a\u3089\u306a\u3044\u7a7a\u767d (\u884c\u533a\u5207\u308a)
        ("abc DEF", ""),
        ("abc\nDEF", ""),
        ("abc\u3000DEF", ""),
        ("abcdefg1234@example.com", ""),
        ("abc.def", ""),
        ("abc。", ""),
        ("コードabc", ""),
        ("abc!", ""),
        ("やること", ""),
    ]
    for given, want in table:
        got = cand(given)
        check(f"_line_code_candidate({given!r}) == {want!r}", got == want, got)

    print("[2] 再現: 自然文・アドレス・URL・英文には何も返さない (旧の判定では「無効」か「すでに連携済み」が返っていた)")
    linked_sid = mk(mod, line_user_id=uid("a"))
    natural = [
        "いつもお世話になっております。連絡先のメールアドレスを abcdefg1234@example.com に変更しました。よろしくお願いいたします。",
        "メールアドレスはabcdefg1234@example.comです",
        "abcdefg1234@example.com",
        "taro.parent1@example.jp",
        "こちらにお願いします https://example.com/abcdef",
        "See you next week teacher",
        "コードは abcdefghijklmnopqrstuvwx です",
        "abcdefghijklmnopqrstuvwx です",
        "abcdefghijklmnopqrstuvwx\nよろしくお願いします",
        "abcdefghij.klmnopqrstu",
    ]
    for text in natural:
        check(f"旧の判定ではコード扱いだった: {text[:30]!r}", old_is_code_like(text))
        check(f"新しい判定ではコードでない: {text[:30]!r}", cand(text.strip()) == "", cand(text.strip()))
        for who, user in (("連携済み", uid("a")), ("未連携", uid("b"))):
            got = send(mod, fake, user, text)
            check(f"{who}の LINE: 何も返さない: {text[:30]!r}", fake.calls == [], got)
    check("連携済みの生徒の LINE はそのまま", line_of(mod, linked_sid) == uid("a"), line_of(mod, linked_sid))

    print("[3] 正しいコードは今までどおり連携できる")
    variants = [
        ("前後空白・改行", lambda c: f"  {c}\n"),
        ("全角空白", lambda c: f"\u3000{c}\u3000"),
        ("全角", fullwidth),
        ("ZWSP 入り", lambda c: c[:8] + "\u200b" + c[8:]),
        ("BOM 付き", lambda c: "\ufeff" + c),
        ("組み合わせ", lambda c: " \u200b" + fullwidth(c[:12]) + c[12:] + "\u200b\n"),
    ]
    for i, (label, wrap) in enumerate(variants):
        sid = mk(mod)
        code = mod._create_line_link_token(sid)
        user = uid(chr(ord("c") + i))
        got = send(mod, fake, user, wrap(code))
        check(f"{label}: 連携完了を返す", len(got) == 1 and got[0].startswith(LINKED_OK), got)
        check(f"{label}: 生徒に LINE が付く", line_of(mod, sid) == user, line_of(mod, sid))
        check(f"{label}: コードは使用済み", used_at(mod, code) not in (None, "<no row>"), used_at(mod, code))

    print("[4] 英数字だけの 20〜28 字は今までどおり「無効」")
    code_like = [
        "abcdefghijklmnopqrstuvwx",                       # 24 字
        "abcdefghijklmnopqrst",                           # 20 字
        "abcdefghijklmnopqrstuvwxyzAB",                   # 28 字
        "abc-def_ghi-jkl_mno-pqr",                        # 記号入り 23 字
        " \u200b" + fullwidth("abcdefghijklmnopqrstuvwx") + "\n",  # 全角・ZWSP・前後空白
    ]
    for text in code_like:
        got = send(mod, fake, uid("z"), text)
        check(f"無効を 1 回だけ返す: {text!r}", got == [INVALID] and fake.calls[0][0] == "message/reply", fake.calls)
    for text in ("abcdefghijklmnopqrs", "abcdefghijklmnopqrstuvwxyzABC"):   # 19 字・29 字
        got = send(mod, fake, uid("z"), text)
        check(f"範囲外の長さは沈黙: {len(text)} 字", fake.calls == [], got)
    # 連携済みの LINE が使用済みのコードを送り直す
    sid = mk(mod)
    code = mod._create_line_link_token(sid)
    send(mod, fake, uid("y"), code)
    got = send(mod, fake, uid("y"), code)
    check("連携済みの LINE が使用済みのコードを送り直すと「すでに連携済み」", len(got) == 1 and got[0].startswith(ALREADY), got)

    print("[5] 前後に文の付いた有効なコードはコード判定に入れない")
    sid = mk(mod)
    code = mod._create_line_link_token(sid)
    for text in (f"連携コード：{code}", f"{code} よろしくお願いします", f"{code}\nよろしくお願いします",
                 f"「{code}」", f"このコードは子どもに渡せばいいですか？{code}"):
        got = send(mod, fake, uid("x"), text)
        check(f"何も返さない: {text[:12]!r}…", fake.calls == [], got)
        check(f"コードは消費しない: {text[:12]!r}…", used_at(mod, code) is None, used_at(mod, code))
        check(f"生徒に LINE は付かない: {text[:12]!r}…", line_of(mod, sid) in (None, ""), line_of(mod, sid))
    got = send(mod, fake, uid("x"), code)
    check("同じコードをそのまま送れば連携できる", len(got) == 1 and got[0].startswith(LINKED_OK), got)

    print("[6] 「やること」「質問 …」は今までどおり")
    q_sid = mk(mod, line_user_id=uid("q"))
    todo_calls.clear(); question_calls.clear()
    got = send(mod, fake, uid("q"), "やること")
    check("連携済み: やること → まとめを返す", got == ["TODO-STUB"] and todo_calls == [q_sid], (got, todo_calls))
    got = send(mod, fake, uid("w"), "やること")
    check("未連携: やること → 連携の案内", got == [mod._LINE_NOT_LINKED_GUIDE], got)
    for text, content in (("質問 howtousepresentperfect", "howtousepresentperfect"),
                          ("質問：abcdefghijklmnopqrstuvwx", "abcdefghijklmnopqrstuvwx"),
                          ("質問 仮定法の使い方がわかりません", "仮定法の使い方がわかりません")):
        question_calls.clear()
        got = send(mod, fake, uid("q"), text)
        check(f"質問を塾長へ回す: {text!r}", question_calls == [(q_sid, content)] and fake.calls == [], (question_calls, got))
    check("旧の判定では「質問 howtousepresentperfect」もコード扱いだった", old_is_code_like("質問 howtousepresentperfect"))
    got = send(mod, fake, uid("w"), "質問 howtousepresentperfect")
    check("未連携: 質問 → 質問用の連携の案内", got == [mod._LINE_QUESTION_NOT_LINKED], got)

    print("[7] CI 登録")
    with open(CI_YML, encoding="utf-8") as f:
        ci = f.read()
    check("server-tests.yml の run 行 (コメントでない) に test_line_code_gate.py",
          re.search(r"^\s+python3 scripts/health_check/test_line_code_gate\.py\s*$", ci, re.M) is not None)

    print()
    if FAILURES:
        print(f"❌ FAIL ({len(FAILURES)} 件)")
        for x in FAILURES:
            print(f"   - {x}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
