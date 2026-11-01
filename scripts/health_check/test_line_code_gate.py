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
  [3] 正しいコードは今までどおり連携できる (前後空白・改行・全角空白・全角・ZWSP 入り・BOM 付き・その組み合わせ)。
      英数字と空白・改行だけの本文 (4 字ごとに空白・途中で改行) も、詰めた形が有効なコードと一致すれば連携する
  [4] 英数字だけの 20〜28 字 (全角・前後空白・ZWSP 付きも) は今までどおり「無効」を 1 回だけ返す。19 字・29 字は沈黙。
      連携済みの LINE が使用済みのコードを送り直したときの「すでに連携済み」も今までどおり
  [5] 前後に文の付いた有効なコード (「連携コード：…」「… よろしくお願いします」・前に「－」「①」がくっついた形) は
      連携も消費もせず、reply で 1 回だけ返す (保護者が質問の中にお子さまのコードを書いても、保護者の LINE に付かない)。
      返事はコードだけを送ったときと同じ順の事前判定で決める: この LINE が別の生徒に連携済み → taken・生徒が別の LINE と
      連携済み → _LINE_STUDENT_LINKED_OTHER・同じ LINE で連携済み → 「すでに連携済み」・どれでもない → 「コードだけを
      送り直す」案内 (お子さまに渡す選択肢を先に書く)。グループ (userId なし)・使用済みのコード・「質問 …」では返さない。
      1 通あたりの照合は _LINE_EMBEDDED_CODE_MAX_TRIES 回まで・同じかたまりは 1 回だけ・24 字の候補だけ (実コードは常に 24 字)。
      英数字の無いふつうのトークは DB に問い合わせない。生徒が別の LINE と連携済みで断ったときは events.line_bind_refused (stage=text)
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
import json
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
TAKEN = "⚠️ このLINEは既に別の生徒アカウントに連携済みです。"

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


def refused(mod, sid):
    """events.line_bind_refused のうち、この生徒の stage の並び。"""
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT props FROM events WHERE name = 'line_bind_refused' ORDER BY id")
    rows = [json.loads(r["props"]) for r in c.fetchall()]
    conn.close()
    return [r.get("stage") for r in rows if r.get("student_id") == sid]


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
    # 試しの 1 行は標準エラーに出さない: run_all_gates.py (material-gates) は終了コード 0 でも
    #   「ERROR:…」の行を印字したゲートを INCONSISTENT で落とす (2026-11-01 の push で実際に落ちた)
    _propagate = mod.log.propagate
    mod.log.propagate = False
    try:
        mod.log.error("probe")
    finally:
        mod.log.propagate = _propagate
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
        ("\u200b abc_DEF-123 \u200b", "abc_DEF-123"),     # ゼロ幅文字を消してから前後の空白を落とす
        ("abc_DEF-123\n\u200b", "abc_DEF-123"),
        ("abc_DEF-123\u2028", "abc_DEF-123"),             # NFKC で ASCII にならない空白 (行区切り)
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

    spaced = mod._line_spaced_code_candidate
    for given, want in (
        ("abcd efgh ijkl mnop qrst uvwx", "abcdefghijklmnopqrstuvwx"),
        ("abcdefghijkl\nmnopqrstuvwx", "abcdefghijklmnopqrstuvwx"),
        (fullwidth("abcd efgh ijkl mnop qrst uvwx"), "abcdefghijklmnopqrstuvwx"),
        ("abcd\u2060efgh ijkl mnop qrst uvwx", "abcdefghijklmnopqrstuvwx"),
        ("See you next week teacher", "Seeyounextweekteacher"),   # 形は当たるが、DB の完全一致でしか使わない ([2] で沈黙を確かめる)
        ("abcd efgh ijkl mnop qrs", ""),                          # 詰めて 19 字
        ("abcd efgh ijkl mnop qrst uvwx yzABC", ""),              # 詰めて 29 字
        ("コード abcd efgh ijkl mnop qrst uvwx", ""),
        ("abc@example.jp ghijklmnopqrstuvw", ""),
        ("", ""),
        (None, ""),
    ):
        got = spaced(given)
        check(f"_line_spaced_code_candidate({given!r}) == {want!r}", got == want, got)

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
        ("4 字ごとに空白 (手で打った形)", lambda c: " ".join(c[i:i + 4] for i in range(0, len(c), 4))),
        ("途中で改行 (写真から文字を読み取った形)", lambda c: c[:12] + "\n" + c[12:]),
        ("全角で 4 字ごとに全角空白", lambda c: "\u3000".join(fullwidth(c)[i:i + 4] for i in range(0, len(c), 4))),
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

    print("[5] 前後に文の付いた有効なコード: 連携も消費もせず reply で 1 回だけ返す")
    guide = mod._LINE_CODE_ONLY_GUIDE
    check("案内: 完了とは言わない・コードだけを送る・お子さまに渡す選択肢が先",
          guide.startswith("⚠️") and not guide.startswith(LINKED_OK) and "コードだけ" in guide
          and 0 <= guide.find("お子さまのLINEで受け取る") < guide.find("このLINEで受け取る"), guide)
    real_peek = mod._peek_line_link_token
    peeked = []

    def send_counting(user, text):
        peeked.clear()
        mod._peek_line_link_token = lambda t: (peeked.append(t) or real_peek(t))
        try:
            return send(mod, fake, user, text)
        finally:
            mod._peek_line_link_token = real_peek

    sid = mk(mod)
    code = mod._create_line_link_token(sid)
    embedded = [
        f"連携コード：{code}",
        f"{code} よろしくお願いします",
        f"{code}\nよろしくお願いします",
        f"「{code}」",
        f"このコードは子どもに渡せばいいですか？{code}",
        "連携コード：" + code[:8] + "\u200b" + code[8:],
        f"{code[:8]}\u2060{code[8:]} です。返信は abc@example.jp へ",       # 書式文字を消してからかたまりを探す
        "連携コード：" + fullwidth(code) + " 返信は abc@example.jp へ",       # かたまりの側も NFKC
        "連携コード：" + " ".join(fullwidth(code)[i:i + 4] for i in range(0, len(code), 4)),   # 本文全体の側も NFKC
        "連携コード－" + code,                                                 # － が - になってくっつく (末尾 24 字)
        f"{code}－です",                                                       # 後ろにくっつく (先頭 24 字)
        "きょうだい2人分です ①" + code,                                       # ① が 1 になってくっつく
        f"abcdefghijklmnopqrstuvwx と {code} のどちらですか",                 # 2 つ目のかたまりが有効
    ]
    for text in embedded:
        got = send(mod, fake, uid("x"), text)
        check(f"案内を reply で 1 回だけ: {text[:16]!r}…",
              got == [guide] and [e for e, _ in fake.calls] == ["message/reply"], fake.calls)
        check(f"コードは消費しない: {text[:16]!r}…", used_at(mod, code) is None, used_at(mod, code))
        check(f"生徒に LINE は付かない: {text[:16]!r}…", line_of(mod, sid) in (None, ""), line_of(mod, sid))
    # きょうだい 2 人分を番号付きで: ① の子のコードは使用済み・② が有効 (① ② は NFKC で 1 2 になりコードにくっつく)。
    #   照合するのは 24 字の候補だけなので、上限 5 回の中で ② の末尾 24 字にたどり着く
    used_code = mod._create_line_link_token(mk(mod))
    send(mod, fake, uid("u"), used_code)
    got = send(mod, fake, uid("x"), f"①{used_code}\n②{code}")
    check("番号付きの 2 つ目のコードを見つける (24 字の候補だけ照合)", got == [guide], got)
    got = send_counting(uid("x"), "明日は部活のため欠席します。よろしくお願いします。")
    check("英数字の無いふつうのトークは照合しない (DB 0 回)", fake.calls == [] and peeked == [], (got, peeked))
    got = send_counting(uid("x"), "メールアドレスを abcdefg1234@example.jp に変更しました")
    check("本番の形 (日本語＋アドレス) も照合しない (DB 0 回)", fake.calls == [] and peeked == [], (got, peeked))
    got = send_counting(uid("x"), "abcdefghijklmnopqrstuvwx " * 10 + f"{code} です")
    check("同じかたまりの繰り返しは 1 回だけ照合 (照合 2 回で見つける)", got == [guide] and len(peeked) == 2, (got, peeked))
    got = send(mod, fake, None, f"連携コード：{code}")
    check("グループ (userId なし) には返さない", fake.calls == [], got)
    # 照合の回数の上限: かたまりを 30 個並べても SELECT は上限まで (上限より後ろの有効なコードには返さない)
    got = send_counting(uid("x"), " ".join(f"abcdefghijklmnopqrstu{i:03d}" for i in range(30)) + f" {code} です")
    check(f"照合は {mod._LINE_EMBEDDED_CODE_MAX_TRIES} 回まで", len(peeked) == mod._LINE_EMBEDDED_CODE_MAX_TRIES, len(peeked))
    check("上限より後ろの有効なコードには返さない", fake.calls == [], got)
    check("照合の差し替えを元に戻した", mod._peek_line_link_token is real_peek)
    got = send(mod, fake, uid("x"), code)
    check("同じコードをそのまま送れば連携できる", len(got) == 1 and got[0].startswith(LINKED_OK), got)
    for who, user in (("連携した LINE", uid("x")), ("別の LINE", uid("v"))):
        got = send(mod, fake, user, f"連携コード：{code}")
        check(f"使用済みのコードが文の中にあっても返さない ({who})", fake.calls == [], got)

    print("[5b] 連携済みの家庭: コードだけを送ったときと同じ返事 (「まだ完了していません」と言わない)")
    # 子どもがマイページのコードで連携した後も、入塾承認メールのコード (保護者宛) は未使用のまま残る
    child_sid = mk(mod)
    send(mod, fake, uid("m"), mod._create_line_link_token(child_sid))
    mail_code = mod._create_line_link_token(child_sid)
    got = send(mod, fake, uid("n"), f"子どもに渡せばいいですか？{mail_code}")
    check("保護者の LINE: 生徒が別の LINE と連携済み → _LINE_STUDENT_LINKED_OTHER", got == [mod._LINE_STUDENT_LINKED_OTHER], got)
    check("  断った記録 (events.line_bind_refused) を stage=text で 1 件", refused(mod, child_sid) == ["text"], refused(mod, child_sid))
    got = send(mod, fake, uid("n"), mail_code)
    check("  (コードだけを送り直しても同じ返事)", got == [mod._LINE_STUDENT_LINKED_OTHER], got)
    got = send(mod, fake, uid("m"), f"連携コード：{mail_code}")
    check("連携した子どもの LINE: 「すでに連携済み」", len(got) == 1 and got[0].startswith(ALREADY), got)
    check("  承認メールのコードは消費しない・子どもの連携はそのまま",
          used_at(mod, mail_code) is None and line_of(mod, child_sid) == uid("m"), (used_at(mod, mail_code), line_of(mod, child_sid)))
    # きょうだい: 上の子に連携済みの LINE から、下の子のコードを文に入れて送る
    mk(mod, line_user_id=uid("o"))
    younger_sid = mk(mod)
    younger_code = mod._create_line_link_token(younger_sid)
    got = send(mod, fake, uid("o"), f"{younger_code} です")
    check("別の生徒に連携済みの LINE: taken の返事", len(got) == 1 and got[0].startswith(TAKEN), got)
    got = send(mod, fake, uid("o"), younger_code)
    check("  (コードだけを送り直しても同じ返事)", len(got) == 1 and got[0].startswith(TAKEN), got)
    check("  下の子のコードは消費しない・連携しない",
          used_at(mod, younger_code) is None and line_of(mod, younger_sid) in (None, ""), (used_at(mod, younger_code), line_of(mod, younger_sid)))

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
    q_code = mod._create_line_link_token(mk(mod))
    question_calls.clear()
    got = send(mod, fake, uid("q"), f"質問 {q_code}")
    check("「質問 <有効なコード>」は質問として回す (連携の案内を返さない・消費しない)",
          question_calls == [(q_sid, q_code)] and fake.calls == [] and used_at(mod, q_code) is None, (question_calls, got))
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
