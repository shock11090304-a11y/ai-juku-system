#!/usr/bin/env python3
"""📄 宿題の添付プリントを塾生アプリから開く (POST /api/student/homework/{id}/print) と、塾生アプリの宿題カードの JST の回帰テスト。

背景 (2026-10-18 塾長「◎のとおりでお願いします。ただし、記述式は採点が難しいのでしばらくは記号問題がいい」の第0段):
  - 塾生アプリ (class.html) の宿題カードには、塾長が添付した配布プリント (attachment_print) を開く入口が無かった。
    しかも塾生アプリのみ枠 (AIなし) は POST /api/student/lesson-prints/{id}/download が middleware の許可集合の外で 403。
    → 許可集合は変えず、元から許可されている prefix /api/student/homework/ の下に宿題 ID を路に持つルートを足した。
  - class.html の「提出:」は naive UTC の文字列を切っただけで 9 時間早く出ていた・期限切れの判定は UTC の日付だった
    (0:00〜9:00 の間は昨日が期限の宿題が「未提出」のまま)。

固定する性質:
  [0] middleware の許可集合は変えていない (新ルートは /api/student/homework/ に乗る・旧 download は AIなし枠で今も 403)
  [1] AIなし枠: 自分の宿題の添付プリント → 200 {file_path, title}・DL 履歴 1 行・download_count +1
  [2] 他人の宿題・存在しない宿題・添付なし・非公開・file_path が /lesson-prints/ の形でない → 404 で履歴は増えない
  [3] 未ログイン / 壊れたトークン → 401・塾長のなりすましは開けるが履歴を数えない
  [4] AIあり の生徒も同じルートで開ける・旧 download ルートは今までどおり
  [5] 宿題一覧に print_open: true・attachment_print は公開中だけ (非公開は None)
  [6] ルートは AI を呼ばない (ソース検査)
  [7] class.html の inline script を偽の DOM・偽の API で実行 (TZ=America/Los_Angeles = 端末のタイムゾーンに依らない):
      「📄 プリントを開く」は print_open のときだけ・添付のある宿題だけ・プリント名は escape・押した瞬間に空のタブ・
      POST /print → /lesson-prints/….pdf へ (+ は -)・タブを開けなければ同じタブ・404/未デプロイ/通信失敗/変な場所はタブを閉じて知らせる・
      「提出:」は JST (naive・マイクロ秒・Z・+00:00・+09:00)・期限切れは JST の今日で判定・メッセージの日時も JST
  [8] ソース検査: 旧 download ルートを class.html から呼ばない・toISOString の UTC の今日が残っていない・CI 登録

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript。AJ_JS_ENGINE で選べる。
  生徒名・メールは架空 (公開リポジトリ)。外部通信は一切しない。DB は一時 SQLite。

実行:
    python3 scripts/health_check/test_homework_print_open.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import os
import re
import subprocess
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CLASS_HTML = os.path.join(REPO, "class.html")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
HW_NOTICE_TEST = os.path.join(REPO, "scripts", "health_check", "test_hw_notice_js.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------------------------------------------
# サーバ
def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="hwprint_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_hwprint", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    """_verify_session_token の新フォーマット (session.sid.exp.sig)。"""
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email, ai_disabled):
    """通塾生 (course=kokuritsu_nankan・永年 trial)。ai_disabled=1 が「塾生アプリのみ枠」。"""
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, "trial", far, "kokuritsu_nankan", "高校2年", "国公立大学", int(ai_disabled)),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def make_print(mod, title, file_path, published=1):
    conn = mod.db()
    c = conn.cursor()
    c.execute("INSERT INTO lesson_prints (title, subject, file_path, is_published) VALUES (?, ?, ?, ?)",
              (title, "english", file_path, int(published)))
    conn.commit()
    c.execute("SELECT id FROM lesson_prints WHERE file_path = ?", (file_path,))
    pid = c.fetchone()["id"]
    conn.close()
    return pid


def make_homework(mod, sid, title, print_id=None):
    conn = mod.db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO homework_assignments (student_id, title, subject, due_date, attachment_print_id, status, created_by) "
        "VALUES (?, ?, ?, ?, ?, 'open', 'admin')",
        (sid, title, "english", "2030-01-01", print_id),
    )
    conn.commit()
    c.execute("SELECT id FROM homework_assignments WHERE student_id = ? ORDER BY id DESC LIMIT 1", (sid,))
    hid = c.fetchone()["id"]
    conn.close()
    return hid


def dl_rows(mod, sid=None):
    conn = mod.db()
    c = conn.cursor()
    if sid is None:
        c.execute("SELECT student_id, print_id FROM lesson_print_downloads ORDER BY id")
    else:
        c.execute("SELECT student_id, print_id FROM lesson_print_downloads WHERE student_id = ? ORDER BY id", (sid,))
    rows = [(r["student_id"], r["print_id"]) for r in c.fetchall()]
    conn.close()
    return rows


def dl_count(mod, pid):
    conn = mod.db()
    c = conn.cursor()
    c.execute("SELECT download_count FROM lesson_prints WHERE id = ?", (pid,))
    n = c.fetchone()["download_count"]
    conn.close()
    return int(n or 0)


def check_server():
    print("📄 宿題の添付プリント (POST /api/student/homework/{id}/print)\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)

    print("[0] middleware の許可集合は変えていない")
    check("新ルートは元からある prefix /api/student/homework/ に乗る",
          "/api/student/homework/1/print".startswith(mod._AI_DISABLED_ALLOWED_PREFIXES))
    check("旧 download ルートは許可集合の外 (AIなし枠で 403 = 新ルートが要る理由)",
          "/api/student/lesson-prints/1/download" not in mod._AI_DISABLED_ALLOWED_EXACT
          and not "/api/student/lesson-prints/1/download".startswith(mod._AI_DISABLED_ALLOWED_PREFIXES))
    check("prefix 集合に /api/student/homework/ が 1 本だけ (兄弟名の増殖なし)",
          sum(1 for p in mod._AI_DISABLED_ALLOWED_PREFIXES if p.startswith("/api/student/homework")) == 1)
    check("トリリオン・ライトの deny にも当たらない", not mod._is_light_denied_path("/api/student/homework/1/print"))

    sid_a = make_student(mod, "架空 プリント A", "hwprint-a@example.org", ai_disabled=1)   # 塾生アプリのみ枠
    sid_b = make_student(mod, "架空 プリント B", "hwprint-b@example.org", ai_disabled=1)
    sid_c = make_student(mod, "架空 プリント C", "hwprint-c@example.org", ai_disabled=0)   # AIあり
    p_ok = make_print(mod, "関係詞 確認プリント", "/lesson-prints/eng_kankeishi_check_01.pdf")
    p_hidden = make_print(mod, "非公開プリント", "/lesson-prints/eng_hidden_01.pdf", published=0)
    p_bad = make_print(mod, "外部を指すプリント", "https://evil.example/x.pdf")
    p_trav = make_print(mod, "上の階層を指すプリント", "/lesson-prints/../secret.pdf")
    hw_a = make_homework(mod, sid_a, "関係詞 プリント", p_ok)
    hw_a_none = make_homework(mod, sid_a, "音読 (プリントなし)")
    hw_a_hidden = make_homework(mod, sid_a, "非公開のプリント", p_hidden)
    hw_a_bad = make_homework(mod, sid_a, "変な場所のプリント", p_bad)
    hw_a_trav = make_homework(mod, sid_a, "上の階層のプリント", p_trav)
    hw_b = make_homework(mod, sid_b, "B の宿題", p_ok)
    hw_c = make_homework(mod, sid_c, "C の宿題", p_ok)
    tok_a = {"Authorization": "Bearer " + student_token(mod, sid_a)}
    tok_c = {"Authorization": "Bearer " + student_token(mod, sid_c)}
    imp_a = {"Authorization": "Bearer " + mod._sign_session_token(sid_a, token_type="impersonation")}

    print("\n[1] 塾生アプリのみ枠: 自分の宿題の添付プリントを開ける")
    r = client.post(f"/api/student/homework/{hw_a}/print", headers=tok_a)
    body = r.json() if r.status_code == 200 else {}
    check("POST /api/student/homework/{id}/print (自分の宿題) → 200 (middleware の 403 ではない)", r.status_code == 200,
          f"status={r.status_code} body={r.text[:200]}")
    check("file_path は添付したプリントの /lesson-prints/….pdf", body.get("file_path") == "/lesson-prints/eng_kankeishi_check_01.pdf", body)
    check("title・print_id・homework_id を返す", body.get("title") and body.get("print_id") == p_ok and body.get("homework_id") == hw_a, body)
    check("DL 履歴に (A, プリント) が 1 行", dl_rows(mod, sid_a) == [(sid_a, p_ok)], dl_rows(mod, sid_a))
    check("download_count が 1", dl_count(mod, p_ok) == 1, dl_count(mod, p_ok))
    r = client.post("/api/student/lesson-prints/%d/download" % p_ok, json={}, headers=tok_a)
    check("同じ生徒の旧 download ルートは今も 403 (許可集合は変えていない)", r.status_code == 403, f"status={r.status_code}")

    print("\n[2] 開けないものは 404 で履歴は増えない")
    for label, hid in (("他人 (B) の宿題", hw_b), ("他人 (C・AIあり) の宿題", hw_c), ("存在しない宿題", 999999),
                       ("添付なしの宿題", hw_a_none), ("非公開プリントの宿題", hw_a_hidden),
                       ("file_path が外部 URL", hw_a_bad), ("file_path に ..", hw_a_trav)):
        r = client.post(f"/api/student/homework/{hid}/print", headers=tok_a)
        check(f"{label} → 404", r.status_code == 404, f"status={r.status_code} body={r.text[:160]}")
        check(f"{label}: 本文に file_path を出さない", "file_path" not in r.text and "evil.example" not in r.text, r.text[:160])
    r = client.post(f"/api/student/homework/{hw_a_none}/print", headers=tok_a)
    check("添付なしの文言「この宿題にはプリントが付いていません」", "プリントが付いていません" in (r.json().get("detail") or ""), r.text[:160])
    r = client.post(f"/api/student/homework/{hw_b}/print", headers=tok_a)
    check("他人の宿題の文言は「あなたに出されていません」(添付の有無を漏らさない)", "あなたに出されていません" in (r.json().get("detail") or ""), r.text[:160])
    check("A の履歴は 1 行のまま・B / C は 0 行", dl_rows(mod, sid_a) == [(sid_a, p_ok)] and dl_rows(mod, sid_b) == [] and dl_rows(mod, sid_c) == [],
          dl_rows(mod))
    check("download_count は 1 のまま", dl_count(mod, p_ok) == 1, dl_count(mod, p_ok))

    print("\n[3] 認証・なりすまし")
    r = client.post(f"/api/student/homework/{hw_a}/print")
    check("Authorization 無し → 401", r.status_code == 401, f"status={r.status_code}")
    r = client.post(f"/api/student/homework/{hw_a}/print", headers={"Authorization": "Bearer bogus"})
    check("壊れたトークン → 401", r.status_code == 401, f"status={r.status_code}")
    r = client.post(f"/api/student/homework/{hw_a}/print", headers=imp_a)
    check("塾長のなりすまし → 200 (同じプリント)", r.status_code == 200 and r.json().get("print_id") == p_ok, f"status={r.status_code} {r.text[:160]}")
    check("なりすましは DL 履歴を数えない (1 行のまま・count 1)", dl_rows(mod, sid_a) == [(sid_a, p_ok)] and dl_count(mod, p_ok) == 1,
          (dl_rows(mod, sid_a), dl_count(mod, p_ok)))
    r = client.get(f"/api/student/homework/{hw_a}/print", headers=tok_a)
    check("GET では開かない (履歴を書くので POST だけ・404/405)", r.status_code in (404, 405) and "file_path" not in r.text,
          f"status={r.status_code} {r.text[:120]}")

    print("\n[4] AIあり の生徒も同じルートで開ける・旧ルートも今までどおり")
    r = client.post(f"/api/student/homework/{hw_c}/print", headers=tok_c)
    check("AIあり: 自分の宿題 → 200", r.status_code == 200 and r.json().get("file_path") == "/lesson-prints/eng_kankeishi_check_01.pdf",
          f"status={r.status_code} {r.text[:160]}")
    r = client.post("/api/student/lesson-prints/%d/download" % p_ok, json={}, headers=tok_c)
    check("AIあり: 旧 download ルートは今までどおり 200", r.status_code == 200, f"status={r.status_code}")
    r = client.post(f"/api/student/homework/{hw_a}/print", headers=tok_c)
    check("AIあり: 他人 (A) の宿題 → 404", r.status_code == 404, f"status={r.status_code}")

    print("\n[5] 宿題一覧: print_open と attachment_print")
    r = client.get("/api/student/homework", headers=tok_a)
    d = r.json() if r.status_code == 200 else {}
    check("GET /api/student/homework (AIなし枠) → 200", r.status_code == 200, f"status={r.status_code}")
    check("print_open: true (塾生アプリはこれを見てボタンを出す)", d.get("print_open") is True, d.get("print_open"))
    by_id = {it["id"]: it for it in d.get("items", [])}
    ap = (by_id.get(hw_a) or {}).get("attachment_print") or {}
    check("添付のある宿題に attachment_print {id, title}", ap.get("id") == p_ok and ap.get("title"), ap)
    check("非公開プリントの宿題は attachment_print = None (ボタンを出さない)", (by_id.get(hw_a_hidden) or {}).get("attachment_print") is None)
    check("添付なしは attachment_print = None", (by_id.get(hw_a_none) or {}).get("attachment_print") is None)

    print("\n[6] AI を呼ばない")
    src = inspect.getsource(mod.open_my_homework_print)
    hits = re.findall(r"_call_\w+|anthropic|openai|gemini|_ai_safe", src, re.I)
    check("open_my_homework_print のソースに AI 呼び出しが無い", not hits, hits)
    check("_require_study_log_course と本人の宿題の照合 (student_id = ?) をする",
          "_require_study_log_course(student)" in src and "WHERE id = ? AND student_id = ?" in src)
    check("列が無い DB では 503「準備中」", '_table_has_column("homework_assignments", "attachment_print_id")' in src and "503" in src)
    check("_safe_lesson_print_path: 正しい形だけ通す",
          mod._safe_lesson_print_path("/lesson-prints/a_b-1.pdf") == "/lesson-prints/a_b-1.pdf"
          and all(mod._safe_lesson_print_path(x) is None for x in (
              None, "", "/lesson-prints/", "https://x.example/a.pdf", "/lesson-prints/../a.pdf", "/lesson-prints//a.pdf",
              "/lesson-prints/a b.pdf", "/lesson-prints/a.pdf?x=1", "/lesson-prints/a.pdf#p", "/lesson-prints/a\\b.pdf",
              "/lesson-prints/a\n.pdf", "/other/a.pdf", 12)))


# ---------------------------------------------------------------------------------------------------------------
# 塾生アプリ (class.html)
JS_PRINT_SETUP = r"""
var OPENED = [], ASSIGNED = [], OPEN_MODE = 'tab', CALLS = [];
function FakeTab() {
  var self = this; this.closed = false; this.written = ''; this.location = { href: '' };
  this.document = { write: function (s) { self.written += String(s); } };
  this.close = function () { self.closed = true; };
}
window.open = function () { if (OPEN_MODE === 'blocked') return null; var tb = new FakeTab(); OPENED.push(tb); return tb; };
var __baseFetch = fetch;
fetch = function (url, opts) {
  var path = String(url).replace(/^https?:\/\/[^\/]+/, '');
  CALLS.push({ path: path, method: (opts && opts.method) || 'GET' });
  var key = path.split('?')[0];
  if (Object.prototype.hasOwnProperty.call(API, key) && API[key].reject) return Promise.reject(new TypeError('Failed to fetch'));
  return __baseFetch(url, opts);
};
window.fetch = fetch;
// 宿題欄の「📄 プリントを開く」を偽の DOM で拾う (renderHomework が querySelectorAll('.hw-print') で listener を付ける)
function wirePrintButtons() {
  var hb = document.getElementById('homeworkBody');
  hb._printBtns = [];
  hb.querySelectorAll = function (sel) {
    if (sel !== '.hw-print') return [];
    var out = [], re = /class="btn (btn-[a-z]+) hw-print" data-id="([^"]*)"/g, m;
    while ((m = re.exec(hb._html))) {
      var b = new FakeEl(); b.setAttribute('data-id', m[2]); b.btnClass = m[1]; b.textContent = '📄 プリントを開く'; out.push(b);
    }
    hb._printBtns = out;
    return out;
  };
  return hb;
}
async function bootPrintPage(search) {
  ELS = {}; TAB_BTNS = ['schedule', 'homework', 'videos', 'messages'].map(function (t) { var b = new FakeEl(); b.setAttribute('data-tab', t); return b; });
  HIST = []; FETCHES = []; TIMERS = []; CALLS = []; OPENED = []; ASSIGNED = [];
  setLoc('/class.html', search || '', '');
  location.assign = function (u) { ASSIGNED.push(String(u)); };
  wirePrintButtons();
  __bootClass();
  await flush();
}
function cards() { return String(ELS.homeworkBody.innerHTML).split('<div class="card">').slice(1); }
function cardOf(title) { var c = cards().filter(function (x) { return x.indexOf('<div class="card-title">' + title + '</div>') >= 0; }); return c[0] || ''; }
function hwList(items, extra) {
  var b = { ok: true, items: items, summary: { open: items.filter(function (x) { return x.status === 'open'; }).length, overdue: 0 } };
  for (var k in (extra || {})) b[k] = extra[k];
  return { status: 200, body: b };
}
var AP = { id: 77, title: '関係詞 <確認> プリント', subject: 'english' };
var HP = { id: 501, title: 'プリントだけの宿題', subject: 'english', topic: '', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2999-12-31', attachment_print: AP };
var HN = { id: 502, title: 'プリントなしの宿題', subject: 'english', topic: '', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2999-12-31', attachment_print: null };
var HD = { id: 503, title: '提出済みのプリント宿題', subject: 'english', topic: '', status: 'completed', created_at: '2026-10-01 01:00:00',
           completed_at: '2026-10-15 23:30:00.123456', attachment_print: { id: 78, title: '比較プリント', subject: 'english' } };
var HT = { id: 504, title: 'ドリルつきのプリント宿題', subject: 'english', topic: '関係詞', status: 'open', created_at: '2026-10-10 01:00:00', due_date: '2999-12-31',
           attachment_print: { id: 79, title: '関係詞 演習', subject: 'english' } };
var PRINT_OK = { status: 200, body: { ok: true, homework_id: 501, print_id: 77, title: '関係詞 確認プリント', file_path: '/lesson-prints/eng+kankeishi_01.pdf' } };
"""

JS_PRINT_CASES = r"""
(async function () {
  try {
    // (P1) print_open のある新しいサーバ: 添付のある宿題だけにボタン
    setApi({ '/api/student/homework': hwList([HP, HN, HD, HT], { print_open: true }), '/api/student/homework/501/print': PRINT_OK });
    await bootPrintPage('?tab=homework');
    var hb = ELS.homeworkBody, h = hb.innerHTML;
    eq('宿題タブに着地', visibleTab(), 'homework');
    eq('「📄 プリントを開く」は添付のある 3 枚だけ', count(h, '📄 プリントを開く'), 3);
    eq('ボタンの data-id は宿題 ID (プリント ID ではない)', hb._printBtns.map(function (b) { return b.getAttribute('data-id'); }), ['501', '503', '504']);
    eq('プリントだけの未提出は主ボタン・ドリルつきと提出済みは控えめ', hb._printBtns.map(function (b) { return b.btnClass; }), ['btn-primary', 'btn-ghost', 'btn-ghost']);
    ok('プリント名は escape して出す', cardOf('プリントだけの宿題').indexOf('📎 プリント: 関係詞 &lt;確認&gt; プリント') >= 0 && h.indexOf('<確認>') < 0, cardOf('プリントだけの宿題'));
    ok('プリントだけの宿題の案内は「プリントを解き終わったら」', cardOf('プリントだけの宿題').indexOf('プリントを解き終わったら「✓ 提出（完了）にする」を押してね') >= 0);
    ok('プリントなしの宿題は今までどおり (ボタンなし・「終わったら」)', cardOf('プリントなしの宿題').indexOf('📄') < 0
       && cardOf('プリントなしの宿題').indexOf('>終わったら「✓ 提出（完了）にする」') >= 0, cardOf('プリントなしの宿題'));
    ok('ドリルつきは「📝 ドリルで解く」も出る', cardOf('ドリルつきのプリント宿題').indexOf('📝 ドリルで解く') >= 0);
    ok('提出済みでもプリントは見直せる (ボタンあり・提出ボタンなし)', cardOf('提出済みのプリント宿題').indexOf('📄 プリントを開く') >= 0
       && cardOf('提出済みのプリント宿題').indexOf('hw-done') < 0);
    ok('提出: は JST (naive UTC 23:30:00.123456 → 翌日 08:30)', cardOf('提出済みのプリント宿題').indexOf('提出: 2026-10-16 08:30') >= 0, cardOf('提出済みのプリント宿題'));

    // (P2) 押す → 空のタブを先に開く → POST /print → /lesson-prints/….pdf へ
    var b0 = hb._printBtns[0];
    b0.dispatch('click');
    eq('押した瞬間 (通信の前) に空のタブを 1 つ開く (iPhone の Safari のポップアップ止め対策)', OPENED.length, 1);
    ok('空のタブに「準備中」を書く', OPENED[0] && OPENED[0].written.indexOf('準備中') >= 0);
    eq('開いたタブの opener を切る', OPENED[0] && OPENED[0].opener, null);
    eq('ボタンは準備中で押せない', [b0.disabled, b0.textContent], [true, '⏳ 準備中…']);
    b0.dispatch('click');
    eq('準備中にもう一度押しても 2 つ目のタブは開かない', OPENED.length, 1);
    await flush();
    var pc = CALLS.filter(function (c) { return c.path.indexOf('/print') >= 0; });
    eq('POST /api/student/homework/501/print を 1 回だけ', pc.map(function (c) { return c.method + ' ' + c.path; }), ['POST /api/student/homework/501/print']);
    eq('タブを /lesson-prints/….pdf へ (+ は - に・mypage.js と同じ)', OPENED[0].location.href, 'https://example.invalid/lesson-prints/eng-kankeishi_01.pdf');
    eq('タブは閉じない・同じタブの移動もしない', [OPENED[0].closed, ASSIGNED], [false, []]);
    ok('旧 download ルート (AIなし枠で 403) は使わない', CALLS.every(function (c) { return c.path.indexOf('/download') < 0; }), CALLS);

    // (P3) タブを開けない (ブロックされた) 端末は同じタブで開く
    OPEN_MODE = 'blocked';
    setApi({ '/api/student/homework': hwList([HP], { print_open: true }), '/api/student/homework/501/print': PRINT_OK });
    await bootPrintPage('?tab=homework');
    ELS.homeworkBody._printBtns[0].dispatch('click'); await flush();
    eq('タブを開けなければ同じタブで開く', ASSIGNED, ['https://example.invalid/lesson-prints/eng-kankeishi_01.pdf']);
    OPEN_MODE = 'tab';

    // (P4) 開けないとき: タブを閉じて理由を出す
    var ERRS = [
      ['サーバの 404 の文言をそのまま', { status: 404, body: { detail: 'この宿題にはプリントが付いていません' } }, 'この宿題にはプリントが付いていません'],
      ['新しいサーバがまだ出ていない (FastAPI の Not Found)', { status: 404, body: { detail: 'Not Found' } }, '準備中です。少し待ってからもう一度押してね'],
      ['503 準備中', { status: 503, body: { detail: '準備中です。少し待ってからもう一度開いてください。' } }, '準備中です。少し待ってからもう一度開いてください。'],
      ['401 はログインし直し', { status: 401, body: { detail: 'Unauthorized' } }, 'ログインし直してからもう一度押してね'],
      ['通信できない', { reject: true }, '通信できませんでした。電波のよいところでもう一度押してね'],
      ['場所が /lesson-prints/….pdf でない (外部 URL)', { status: 200, body: { ok: true, file_path: 'https://evil.example/x.pdf' } }, 'プリントの場所を読めませんでした。塾長に知らせてね'],
      ['場所に ..', { status: 200, body: { ok: true, file_path: '/lesson-prints/../x.pdf' } }, 'プリントの場所を読めませんでした。塾長に知らせてね'],
      ['PDF でない', { status: 200, body: { ok: true, file_path: '/lesson-prints/x.html' } }, 'プリントの場所を読めませんでした。塾長に知らせてね']
    ];
    for (var i = 0; i < ERRS.length; i++) {
      setApi({ '/api/student/homework': hwList([HP], { print_open: true }), '/api/student/homework/501/print': ERRS[i][1] });
      await bootPrintPage('?tab=homework');
      ELS.homeworkBody._printBtns[0].dispatch('click'); await flush();
      eq(ERRS[i][0] + ': タブを閉じて移動しない', [OPENED.length, OPENED[0] && OPENED[0].closed, OPENED[0] && OPENED[0].location.href, ASSIGNED], [1, true, '', []]);
      eq(ERRS[i][0] + ': 赤いトースト', [ELS.toast && ELS.toast.textContent, ELS.toast && ELS.toast.className], [ERRS[i][2], 'toast show err']);
    }

    // (P5) 古いサーバ (print_open なし) ではボタンを出さない (静的が API より先に出た窓・API を戻したとき)
    setApi({ '/api/student/homework': hwList([HP, HD]) });
    await bootPrintPage('?tab=homework');
    eq('print_open が無ければボタンは 0', count(ELS.homeworkBody.innerHTML, '📄 プリントを開く'), 0);
    ok('print_open が無くてもプリント名の行は出さない・カードは今までどおり', ELS.homeworkBody.innerHTML.indexOf('📎 プリント:') < 0
       && cardOf('プリントだけの宿題').indexOf('>終わったら「✓ 提出（完了）にする」') >= 0);
    setApi({ '/api/student/homework': hwList([HP], { print_open: 'yes' }) });
    await bootPrintPage('?tab=homework');
    eq('print_open は true のときだけ', count(ELS.homeworkBody.innerHTML, '📄 プリントを開く'), 0);

    // (T1) 「提出:」は JST (端末のタイムゾーンに依らない)
    var TS = [
      ['naive マイクロ秒', '2026-10-15 23:30:00.123456', '2026-10-16 08:30'],
      ['naive 秒まで', '2026-10-15 23:30:00', '2026-10-16 08:30'],
      ['T 区切り naive', '2026-10-15T23:30:00', '2026-10-16 08:30'],
      ['Z', '2026-10-15T23:30:00Z', '2026-10-16 08:30'],
      ['+00:00 (str(aware datetime))', '2026-10-15 23:30:00.5+00:00', '2026-10-16 08:30'],
      ['+09:00 はそのまま', '2026-10-16T08:30:00+09:00', '2026-10-16 08:30'],
      ['日付の変わり目 (UTC 14:59 = JST 23:59)', '2026-10-15 14:59:59', '2026-10-15 23:59'],
      ['読めない値は文字列のまま', 'bad-value', 'bad-value']
    ];
    var tsItems = TS.map(function (t, i) { return { id: 700 + i, title: '提出時刻 ' + i, subject: 'english', topic: '', status: 'completed', created_at: '2026-10-01 00:00:00', completed_at: t[1] }; });
    var DDONE = { drill_id: 801, title: '比較ドリル', unit: '比較', subject: 'english', status: 'completed', score_correct: 7, score_total: 10,
                  assigned_at: '2026-10-14 20:30:00', completed_at: '2026-10-15 23:30:00.123456' };
    var DOPEN = { drill_id: 802, title: '分詞ドリル', unit: '分詞', subject: 'english', status: 'open', score_total: 10, assigned_at: '2026-10-14 20:30:00.654321' };
    setApi({ '/api/student/homework': hwList(tsItems, { print_open: true }), '/api/student/grammar-drills': drillBody([DOPEN, DDONE]) });
    await bootPrintPage('?tab=homework');
    for (var j = 0; j < TS.length; j++) {
      ok('提出: ' + TS[j][0] + ' → ' + TS[j][2], cardOf('提出時刻 ' + j).indexOf('提出: ' + TS[j][2] + '<') >= 0, cardOf('提出時刻 ' + j));
    }
    var hd = ELS.homeworkBody.innerHTML;
    ok('単元ドリルのカードの「提出:」も JST (同じ gdLocalDate)', hd.indexOf('スコア 7 / 10 ・ 提出: 2026-10-16 08:30') >= 0, hd.slice(0, 900));
    ok('単元ドリルの「出題」も JST の日付 (UTC 20:30 = JST 翌日 05:30)', hd.indexOf('出題 2026-10-15') >= 0, hd.slice(0, 900));

    // (T2) 期限切れは JST の今日で判定 (UTC ではまだ 10-15 の JST 10-16 05:00)
    var realNow = Date.now;
    Date.now = function () { return Date.UTC(2026, 9, 15, 20, 0, 0); };
    var HY = { id: 901, title: '昨日が期限', subject: 'english', topic: '', status: 'open', created_at: '2026-10-01 00:00:00', due_date: '2026-10-15' };
    var HTD = { id: 902, title: '今日が期限', subject: 'english', topic: '', status: 'open', created_at: '2026-10-01 00:00:00', due_date: '2026-10-16' };
    var HDN = { id: 903, title: '期限なし', subject: 'english', topic: '', status: 'open', created_at: '2026-10-01 00:00:00', due_date: null };
    setApi({ '/api/student/homework': hwList([HY, HTD, HDN], { print_open: true }) });
    try {
      await bootPrintPage('?tab=homework');
    } finally {
      Date.now = realNow;
    }
    // ⏰ 2026-10-18 から 期限切れは「未提出」+「〆を過ぎました」・今日が期限は「未提出」+「〆今日」(hw-notice.js の dueState)
    ok('JST で昨日が期限 → 〆を過ぎました (UTC の日付ではまだ当日)', cardOf('昨日が期限').indexOf('chip-over">〆を過ぎました') >= 0, cardOf('昨日が期限'));
    ok('JST で今日が期限 → 未提出・〆今日 (〆を過ぎたではない)', cardOf('今日が期限').indexOf('chip-open">未提出') >= 0
       && cardOf('今日が期限').indexOf('chip-soon">〆今日') >= 0 && cardOf('今日が期限').indexOf('〆を過ぎました') < 0, cardOf('今日が期限'));
    ok('期限なし → 未提出', cardOf('期限なし').indexOf('chip-open">未提出') >= 0, cardOf('期限なし'));

    // (T3) メッセージの日時も JST (以前は fmtDate = 文字列を切っただけで 9 時間早く出ていた)
    var MTS = [
      ['naive マイクロ秒', '2026-10-15 23:30:00.123456', '2026-10-16 08:30'],
      ['naive 秒まで', '2026-10-15 23:30:00', '2026-10-16 08:30'],
      ['Z', '2026-10-15T23:30:00Z', '2026-10-16 08:30'],
      ['+09:00 はそのまま', '2026-10-16T08:30:00+09:00', '2026-10-16 08:30'],
      ['日付の変わり目 (UTC 15:00 = JST 翌日 00:00)', '2026-10-15 15:00:00', '2026-10-16 00:00'],
      ['日時なし', null, '']
    ];
    var msgs = MTS.map(function (t, i) { return { id: 950 + i, direction: i % 2 ? 'out' : 'in', subject: 'メッセージ ' + i, body: '本文 ' + i,
                                                  is_unread: false, created_at: t[1], attachment: null }; });
    setApi({ '/api/messages/me': { status: 200, body: { ok: true, messages: msgs, unread_count: 0, dl_ttl_seconds: 1800 } } });
    await bootPrintPage('');
    tab('messages'); await flush();
    var mb = ELS.messagesBody ? ELS.messagesBody.innerHTML : '';
    eq('メッセージのタブ', visibleTab(), 'messages');
    var mparts = String(mb).split('<div class="msg ').slice(1);
    eq('メッセージは 6 件', mparts.length, MTS.length);
    for (var mi = 0; mi < MTS.length; mi++) {
      var mpart = mparts.filter(function (x) { return x.indexOf('data-id="' + (950 + mi) + '"') >= 0; })[0] || '';
      ok('メッセージの日時: ' + MTS[mi][0] + ' → ' + (MTS[mi][2] || '(空)'), mpart.indexOf('</span><span>' + MTS[mi][2] + '</span></div>') >= 0, mpart.slice(0, 300));
    }
    ok('UTC のまま (2026-10-15 23:30) は出さない', mb.indexOf('2026-10-15 23:30') < 0, mb.slice(0, 600));
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""


def load_hw_notice_harness():
    """test_hw_notice_js.py の偽の DOM・偽の API・JS エンジンの選び方を借りる (同じ土台で class.html を動かす)。"""
    spec = importlib.util.spec_from_file_location("hw_notice_js_harness", HW_NOTICE_TEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_js(engine, program, label, env_extra=None):
    with tempfile.TemporaryDirectory(prefix="hw_print_js_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        env = dict(os.environ)
        env.update(env_extra or {})
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=180, env=env)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [l for l in text.split("\n") if l.startswith(("OK  ", "NG  ", "DONE "))]
    done = [l for l in lines if l.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return
    for l in lines:
        if l.startswith("OK  "):
            check(l[4:], True)
        elif l.startswith("NG  "):
            check(l[4:], False, l[4:])
    n = int(done[-1].split()[1])
    check(f"{label}: {n} 件の検査を実行", n > 0)


def check_class_html():
    print("\n[7] 塾生アプリ (class.html) の inline script を偽の DOM と偽の API で実行 (TZ=America/Los_Angeles)")
    H = load_hw_notice_harness()
    class_html = read(CLASS_HTML)
    inline = H.inline_scripts(class_html)
    eng = H.js_engine()
    print(f"  JS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng),
          "node も osascript も jsc も見つからない (AJ_JS_ENGINE の指定も確認)")
    check("class.html の inline script は 1 つ", len(inline) == 1, len(inline))
    if eng and len(inline) == 1:
        boot = "function __bootClass() {\n" + inline[0] + "\n}\n"
        prog = H.PRELUDE + H.POLYFILL + H.FAKE_DOM + H.JS_CLASS_SETUP + JS_PRINT_SETUP + boot + JS_PRINT_CASES
        # 端末のタイムゾーンが JST でなくても JST で出す (塾長の Mac は JST なので、UTC−7/−8 にして「端末任せ」の実装なら落ちるようにする)
        run_js(eng, prog, "[7]", {"TZ": "America/Los_Angeles"})

    print("\n[8] ソース検査")
    script = inline[0] if inline else ""
    check("class.html は旧 download ルート (/api/student/lesson-prints/…/download) を呼ばない", "/api/student/lesson-prints/" not in script)
    check("class.html: 宿題の期限切れの今日に UTC (new Date().toISOString().slice(0, 10)) を使わない",
          "new Date().toISOString().slice(0, 10)" not in script and "var today = jstToday();" in script)
    check("class.html: 宿題カードの「提出:」は gdLocalDate (JST)", "esc(gdLocalDate(it.completed_at, true))" in script
          and "fmtDate(it.completed_at)" not in script)
    check("class.html: メッセージの日時は gdLocalDate (JST)・UTC を切るだけの fmtDate は残っていない",
          "esc(gdLocalDate(m.created_at, true))" in script and "fmtDate(" not in script)
    check("class.html: POST /api/student/homework/{id}/print", "'/api/student/homework/' + encodeURIComponent(id) + '/print', { method: 'POST'" in script)
    check("class.html: ボタンは print_open === true のときだけ", "d.print_open === true" in script)
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_homework_print_open.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'class.html'", "'server/**'", "'scripts/health_check/test_*.py'"):
        check(f"CI の paths に {p}", p in paths_block)


def main():
    check_server()
    check_class_html()
    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("   -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
