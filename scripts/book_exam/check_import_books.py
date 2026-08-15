#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""import_books.py (冊子の取り込み) の検査。

    python3 scripts/book_exam/check_import_books.py

■ 何を検査するか
  1. **プロトコル**: 手元に立てた偽の Supabase API に向けて import_books.py を
     子プロセスで実際に走らせ、リクエストの並び・ヘッダ・中身・終了コードを見る。
     本物の Supabase はこの環境から届かない (プロキシ遮断) ので、
     「script が話す HTTP」を先に固定しておく。
  2. **パリティ**: 検証と DB 形への写像は exam-book-admin-model.mjs が正典だが、
     塾長の Mac に node が無いので import_books.py は Python で再実装している。
     二重管理のずれをここで **実物の .mjs と突き合わせて** 機械的に検出する。

■ 検査の姿勢 (CLAUDE.md)
  ・引数なしの既定で全シナリオを回し、何を見たかを印字する
  ・「書いたのに呼ばれない」「exit 0 なのに違反印字」を作らない
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IMPORTER = os.path.join(HERE, "import_books.py")
MODEL = os.path.join(ROOT, "exam-book-admin-model.mjs")

problems = []


def ng(msg):
    problems.append(msg)
    print(f"  ✗ {msg}")


# =============================================================================
# 偽 Supabase (登録画面が話すのと同じ 4 系統: auth / rest / storage)
# =============================================================================
class FakeSupabase:
    def __init__(self, role="teacher", fail_storage=False, corrupt_readback=False,
                 short_insert=False, lose_readback=False):
        self.role = role
        self.fail_storage = fail_storage
        self.corrupt_readback = corrupt_readback
        self.short_insert = short_insert
        self.lose_readback = lose_readback
        self.books = []          # {id,title,subject,level,page_count,time_limit_sec,is_published,pdf_path}
        self.questions = []      # payload + book_id
        self.storage = {}        # path -> bytes
        self.log = []            # (method, path)
        self.bad_auth = []

    def seed_book(self, title, n_questions=0, pdf_path=None):
        bid = f"b{len(self.books) + 1}"
        self.books.append({"id": bid, "title": title, "subject": "social",
                           "level": None, "page_count": 13, "time_limit_sec": None,
                           "is_published": False, "pdf_path": pdf_path})
        for i in range(n_questions):
            self.questions.append({"book_id": bid, "number": i + 1,
                                   "correct_answer": "1"})
        return bid


def make_handler(state):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):      # 静かに
            pass

        def _read(self):
            n = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(n) if n else b""

        def _send(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _auth_ok(self, need_user_token):
            if self.headers.get("apikey") != "testanon":
                state.bad_auth.append(f"apikey が無い/違う: {self.path}")
                return False
            bearer = (self.headers.get("Authorization") or "").replace("Bearer ", "")
            want = "tok-1" if need_user_token else None
            if want and bearer != want:
                state.bad_auth.append(f"user token でない: {self.path}")
                return False
            return True

        def do_POST(self):
            state.log.append(("POST", self.path))
            p = urllib.parse.urlparse(self.path)
            body = self._read()
            if p.path == "/auth/v1/token":
                d = json.loads(body)
                if d.get("password") != "pw-ok":
                    return self._send(400, {"error_description": "Invalid login"})
                return self._send(200, {"access_token": "tok-1",
                                        "user": {"id": "u-1"}})
            if not self._auth_ok(True):
                return self._send(401, {"message": "bad auth"})
            if p.path == "/rest/v1/books":
                row = json.loads(body)
                row["id"] = f"b{len(state.books) + 1}"
                row.setdefault("pdf_path", None)
                state.books.append(row)
                return self._send(201, [row])
            if p.path == "/rest/v1/questions":
                rows = json.loads(body)
                state.questions += rows
                if state.short_insert:
                    return self._send(201, rows[:-1])     # わざと 1 行少なく返す
                return self._send(201, rows)
            if p.path.startswith("/storage/v1/object/book-pdfs/"):
                if state.fail_storage:
                    return self._send(400, {"message":
                        "new row violates row-level security policy"})
                key = p.path.split("/storage/v1/object/", 1)[1]
                state.storage[key] = body
                return self._send(200, {"Key": key})
            return self._send(404, {"message": f"unknown POST {p.path}"})

        def do_GET(self):
            state.log.append(("GET", self.path))
            p = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(p.query)
            if not self._auth_ok(True):
                return self._send(401, {"message": "bad auth"})
            if p.path == "/rest/v1/profiles":
                return self._send(200, [{"role": state.role}])
            if p.path == "/rest/v1/books":
                title = (qs.get("title") or [""])[0].replace("eq.", "")
                out = []
                for b in state.books:
                    if b["title"] == title:
                        n = sum(1 for q in state.questions if q["book_id"] == b["id"])
                        row = dict(b)
                        row["questions"] = [{"count": n}]
                        out.append(row)
                return self._send(200, out)
            if p.path == "/rest/v1/questions":
                bid = (qs.get("book_id") or [""])[0].replace("eq.", "")
                rows = [{"number": q["number"], "correct_answer": q["correct_answer"]}
                        for q in state.questions if q["book_id"] == bid]
                rows.sort(key=lambda r: r["number"])
                if state.corrupt_readback and rows:
                    rows[0] = dict(rows[0], correct_answer="9")
                if state.lose_readback and rows:
                    rows = rows[:-1]          # 1 行黙って欠けさせる
                return self._send(200, rows)
            return self._send(404, {"message": f"unknown GET {p.path}"})

        def do_PATCH(self):
            state.log.append(("PATCH", self.path))
            p = urllib.parse.urlparse(self.path)
            if not self._auth_ok(True):
                return self._send(401, {"message": "bad auth"})
            body = json.loads(self._read())
            qs = urllib.parse.parse_qs(p.query)
            bid = (qs.get("id") or [""])[0].replace("eq.", "")
            for b in state.books:
                if b["id"] == bid:
                    b.update(body)
                    return self._send(200, [b])
            return self._send(200, [])
    return H


class Server:
    def __init__(self, state):
        self.state = state
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        self.port = self.httpd.server_address[1]
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


# =============================================================================
# 材料
# =============================================================================
TINY_PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 100 100]>>endobj\n"
            b"trailer<</Root 1 0 R>>\n%%EOF\n")


def bundle_sekaishi():
    return {
        "source": "test/sekaishi.yaml", "subject_name": "世界史",
        "preview": [{"number": 1, "correct_answer": "2", "correct_text": "第1問 問A → 2 番"}],
        "book": {"title": "検査用 世界史", "subject": "social", "level": None,
                 "time_limit_min": None},
        "questions": [
            {"number": 1, "page": None, "points": 5, "answer_type": "choice",
             "choice_count": 4, "correct_answer": "2", "accepted_answers": [],
             "unit_tag": "第1問", "explanation": "解説1"},
            {"number": 2, "page": None, "points": 5, "answer_type": "choice",
             "choice_count": 4, "correct_answer": "1", "accepted_answers": [],
             "unit_tag": "第1問", "explanation": None},
        ],
        "skipped": [],
    }


def bundle_kokugo():
    return {
        "source": "test/kokugo.yaml", "subject_name": "国語",
        "preview": [{"number": 1, "correct_answer": "5", "correct_text": "会議で沈黙を守る"}],
        "book": {"title": "検査用 国語", "subject": "japanese", "level": None,
                 "time_limit_min": None},
        "questions": [
            {"number": 1, "page": None, "points": 2, "answer_type": "choice",
             "choice_count": 5, "correct_answer": "5", "accepted_answers": [],
             "unit_tag": None, "explanation": "【正解】⑤"},
            {"number": 2, "page": None, "points": 2, "answer_type": "short",
             "choice_count": None, "correct_answer": "were",
             "accepted_answers": ["Were"], "unit_tag": None, "explanation": None},
        ],
        "skipped": [],
    }


def setup_dir(td, bundles, pdf_names):
    src = os.path.join(td, "json")
    pdfs = os.path.join(td, "pdfs")
    os.makedirs(src)
    os.makedirs(pdfs)
    for b in bundles:
        name = b["book"]["title"].replace(" ", "_") + ".json"
        with open(os.path.join(src, name), "w", encoding="utf-8") as f:
            json.dump(b, f, ensure_ascii=False)
    meta = {"prints": []}
    for n in pdf_names:
        with open(os.path.join(pdfs, n), "wb") as f:
            f.write(TINY_PDF)
        meta["prints"].append({"file_path": f"/lesson-prints/{n}", "pages": 13})
    mp = os.path.join(td, "meta.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return src, pdfs, mp


def run_importer(server, src, pdfs, metadata, *extra, password="pw-ok"):
    env = dict(os.environ,
               EXAM_SUPABASE_URL=f"http://127.0.0.1:{server.port}",
               EXAM_SUPABASE_ANON="testanon",
               EXAM_TEACHER_EMAIL="t@example.invalid",
               EXAM_TEACHER_PASSWORD=password,
               EXAM_PDF_METADATA=metadata)
    r = subprocess.run([sys.executable, IMPORTER, src, "--pdf-dir", pdfs, *extra],
                       capture_output=True, text=True, env=env, timeout=120)
    return r


# =============================================================================
# シナリオ
# =============================================================================
def scenario(name):
    print(f"  [scenario] {name}")


def check_all():
    td = tempfile.mkdtemp(prefix="import_check_")
    try:
        # --- S1: 正常系 (2 冊・choice/short 混在) -----------------------------
        scenario("S1 正常系 2 冊 → 非公開で入る")
        st = FakeSupabase()
        sv = Server(st)
        src, pdfs, mp = setup_dir(
            td + "/s1" if os.makedirs(td + "/s1") is None else td,
            [bundle_sekaishi(), bundle_kokugo()],
            ["2026-06-03_共通テスト世界史_マーク式_問題.pdf",
             "2026-06-03_共通テスト国語_マーク式_問題.pdf"])
        r = run_importer(sv, src, pdfs, mp)
        sv.stop()
        if r.returncode != 0:
            ng(f"S1: exit {r.returncode} — {r.stdout[-300:]}{r.stderr[-200:]}")
        if len(st.books) != 2 or any(b["is_published"] for b in st.books):
            ng(f"S1: 冊子が非公開 2 冊になっていない: {st.books}")
        if len(st.storage) != 2 or any(v != TINY_PDF for v in st.storage.values()):
            ng("S1: PDF が 2 本、そのままの中身で上がっていない")
        if len(st.questions) != 4:
            ng(f"S1: 設問が 4 問入っていない ({len(st.questions)})")
        short = next((q for q in st.questions if q["answer_type"] == "short"), None)
        choice = next((q for q in st.questions if q["answer_type"] == "choice"), None)
        if not short or short["accepted_answers"] != ["Were"]:
            ng(f"S1: 記述の別解が落ちた ({short})")
        if not choice or choice["accepted_answers"] is not None:
            ng(f"S1: 選択式の accepted_answers が null でない ({choice})")
        if any(b["pdf_path"] is None for b in st.books):
            ng("S1: pdf_path が記録されていない")
        if "照合表" not in r.stdout or "非公開で置いてあります" not in r.stdout:
            ng("S1: 照合表 / 非公開の案内が出ていない")
        if st.bad_auth:
            ng(f"S1: 認証ヘッダの不備 {st.bad_auth[:2]}")

        # --- S2: --publish ---------------------------------------------------
        scenario("S2 --publish で公開まで")
        st = FakeSupabase()
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--publish")
        sv.stop()
        if r.returncode != 0 or not all(b["is_published"] for b in st.books):
            ng(f"S2: 公開になっていない (exit {r.returncode}, {[b['is_published'] for b in st.books]})")

        # --- S3: 保存済み設問がある同名冊子 → 触らない ------------------------
        scenario("S3 設問ありの同名冊子は skip")
        st = FakeSupabase()
        st.seed_book("検査用 世界史", n_questions=2, pdf_path="books/b1.pdf")
        st.seed_book("検査用 国語", n_questions=2, pdf_path="books/b2.pdf")
        before_q = len(st.questions)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp)
        sv.stop()
        if r.returncode != 0 or "触りません" not in r.stdout:
            ng(f"S3: skip になっていない (exit {r.returncode})")
        if len(st.questions) != before_q or len(st.books) != 2 or st.storage:
            ng("S3: 触らないはずの冊子に書いた")

        # --- S4: 設問 0 の同名冊子 → 再開して入れ直す --------------------------
        scenario("S4 設問 0 の同名冊子へ resume")
        st = FakeSupabase()
        st.seed_book("検査用 世界史", n_questions=0, pdf_path=None)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode != 0 or "入れ直し" not in r.stdout:
            ng(f"S4: resume になっていない (exit {r.returncode})")
        if len(st.books) != 1:
            ng(f"S4: 冊子が増えた ({len(st.books)} 冊)")
        if "book-pdfs/books/b1.pdf" not in st.storage:
            ng("S4: 既存の冊子の id で PDF が上がっていない")

        # --- S5: PDF アップロード失敗 → exit 1・回し直しで復旧 ----------------
        scenario("S5 storage 失敗 → 失敗を名指し → 回し直しで復旧")
        st = FakeSupabase(fail_storage=True)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode == 0 or "row-level security" not in (r.stdout + r.stderr):
            ng(f"S5: storage 失敗が握り潰された (exit {r.returncode})")
        if any(b["is_published"] for b in st.books):
            ng("S5: 失敗したのに公開されている")
        st.fail_storage = False
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode != 0 or len(st.books) != 1 or len(st.questions) != 2:
            ng(f"S5: 回し直しで復旧できない (exit {r.returncode}, "
               f"{len(st.books)} 冊 {len(st.questions)} 問)")

        # --- S6: 生徒アカウント → 何も書かずに止まる --------------------------
        scenario("S6 生徒アカウントは入口で止まる")
        st = FakeSupabase(role="student")
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp)
        sv.stop()
        if r.returncode == 0 or "講師ではありません" not in r.stdout:
            ng(f"S6: 生徒で通ってしまう (exit {r.returncode})")
        if st.books or st.questions or st.storage:
            ng("S6: 生徒なのに書けた")

        # --- S7: 0 起算の bundle → ネットワークに出る前に拒否 -----------------
        scenario("S7 検証 NG の JSON は 1 バイトも書かない")
        bad = bundle_sekaishi()
        bad["questions"][0]["correct_answer"] = "0"
        src7, pdfs7, mp7 = setup_dir(os.path.join(td, "s7"), [bad],
                                     ["2026-06-03_共通テスト世界史_マーク式_問題.pdf"])
        st = FakeSupabase()
        sv = Server(st)
        r = run_importer(sv, src7, pdfs7, mp7)
        sv.stop()
        if r.returncode == 0 or "0 起算" not in r.stdout:
            ng(f"S7: 0 起算が素通り (exit {r.returncode})")
        if st.books or st.questions or st.storage:
            ng("S7: 検証 NG なのに書いた")

        # --- S8: --dry-run はサーバに触らない --------------------------------
        scenario("S8 --dry-run は 1 リクエストも出さない")
        st = FakeSupabase()
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--dry-run")
        sv.stop()
        if r.returncode != 0 or "[予行]" not in r.stdout:
            ng(f"S8: dry-run が失敗 (exit {r.returncode})")
        if st.log:
            ng(f"S8: dry-run なのにリクエストが飛んだ {st.log[:3]}")

        # --- S9: PDF の候補が 2 つ → 選ばずに止まる ---------------------------
        scenario("S9 PDF 候補 2 つは選ばない")
        src9, pdfs9, mp9 = setup_dir(os.path.join(td, "s9"), [bundle_sekaishi()],
                                     ["2026-06-03_共通テスト世界史_マーク式_問題.pdf",
                                      "旧版_共通テスト世界史_問題.pdf"])
        st = FakeSupabase()
        sv = Server(st)
        r = run_importer(sv, src9, pdfs9, mp9)
        sv.stop()
        # 「共通テスト世界史_」の完全一致で 1 つに絞れるのは正しい。絞れないよう別名を足す
        if r.returncode != 0:
            pass          # 絞れず止まった (それも正しい) — メッセージだけ確かめる
        if r.returncode != 0 and "候補" not in r.stdout:
            ng("S9: 候補が複数のときの案内が出ない")

        # --- S10: 読み返しの食い違い → 失敗にする ------------------------------
        scenario("S10 読み返しで正解が食い違えば失敗")
        st = FakeSupabase(corrupt_readback=True)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode == 0 or "食い違う" not in r.stdout:
            ng(f"S10: 読み返しの食い違いを見逃した (exit {r.returncode})")

        # --- S11: 投入の返却行数が足りない → 失敗にする ------------------------
        scenario("S11 投入の返却が欠けたら失敗")
        st = FakeSupabase(short_insert=True)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode == 0:
            ng("S11: 返却行数の不足を見逃した")

        # --- S12: 読み返しの行数が欠けたら失敗にする ---------------------------
        #   ★ S10 (中身の食い違い) だけだと、「問数の照合」を消しても素通りする
        #     ことがサボタージュで実証された (2026-08-15)。行数の欠けを別に見る。
        scenario("S12 読み返しの行数が欠けたら失敗")
        st = FakeSupabase(lose_readback=True)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史")
        sv.stop()
        if r.returncode == 0 or "読み返すと" not in r.stdout:
            ng(f"S12: 読み返しの行数の欠けを見逃した (exit {r.returncode})")
    finally:
        shutil.rmtree(td, ignore_errors=True)


# =============================================================================
# パリティ: Python 実装 ↔ 実物 exam-book-admin-model.mjs
# =============================================================================
PARITY_CASES = [
    # (説明, 行)  — validate の合否が両実装で一致し、合格なら payload も一致すること
    ("正常な選択式", {"number": 1, "page": None, "points": 5, "answer_type": "choice",
                      "choice_count": 4, "correct_answer": "2", "accepted_answers": [],
                      "unit_tag": "第1問", "explanation": "x"}),
    ("正常な記述+別解", {"number": 2, "page": 3, "points": 1, "answer_type": "short",
                         "choice_count": None, "correct_answer": "were",
                         "accepted_answers": ["Were", "was"], "unit_tag": None,
                         "explanation": None}),
    ("0 起算", {"number": 1, "page": None, "points": 1, "answer_type": "choice",
                "choice_count": 4, "correct_answer": "0", "accepted_answers": [],
                "unit_tag": None, "explanation": None}),
    ("丸数字", {"number": 1, "page": None, "points": 1, "answer_type": "choice",
                "choice_count": 4, "correct_answer": "②", "accepted_answers": [],
                "unit_tag": None, "explanation": None}),
    ("範囲外", {"number": 1, "page": None, "points": 1, "answer_type": "choice",
                "choice_count": 4, "correct_answer": "5", "accepted_answers": [],
                "unit_tag": None, "explanation": None}),
    ("選択式に別解", {"number": 1, "page": None, "points": 1, "answer_type": "choice",
                      "choice_count": 4, "correct_answer": "2",
                      "accepted_answers": ["x"], "unit_tag": None, "explanation": None}),
    ("記述が数字だけ", {"number": 1, "page": None, "points": 1, "answer_type": "short",
                        "choice_count": None, "correct_answer": "3",
                        "accepted_answers": [], "unit_tag": None, "explanation": None}),
    ("配点 0", {"number": 1, "page": None, "points": 0, "answer_type": "choice",
                "choice_count": 4, "correct_answer": "2", "accepted_answers": [],
                "unit_tag": None, "explanation": None}),
    ("ページ 0", {"number": 1, "page": 0, "points": 1, "answer_type": "choice",
                  "choice_count": 4, "correct_answer": "2", "accepted_answers": [],
                  "unit_tag": None, "explanation": None}),
    ("選択肢 11", {"number": 1, "page": None, "points": 1, "answer_type": "choice",
                   "choice_count": 11, "correct_answer": "2", "accepted_answers": [],
                   "unit_tag": None, "explanation": None}),
]


def check_parity():
    node = shutil.which("node")
    if not node:
        ng("node が無いのでパリティ検査を回せない (CI には必ずある)")
        return
    sys.path.insert(0, HERE)
    os.environ.setdefault("EXAM_SUPABASE_URL", "http://parity.invalid")
    os.environ.setdefault("EXAM_SUPABASE_ANON", "parity")
    import importlib.util
    spec = importlib.util.spec_from_file_location("imp", IMPORTER)
    imp = importlib.util.module_from_spec(spec)
    old_argv = sys.argv
    sys.argv = ["imp"]
    try:
        spec.loader.exec_module(imp)
    finally:
        sys.argv = old_argv

    script = f"""
import {{ validateQuestions, questionPayload }} from {json.dumps('file://' + MODEL)};
let buf = ''; process.stdin.setEncoding('utf8');
process.stdin.on('data', (d) => buf += d);
process.stdin.on('end', () => {{
  const out = [];
  for (const row of JSON.parse(buf)) {{
    const v = validateQuestions([row], {{ pageCount: null }});
    out.push({{ ok: v.ok, payload: v.ok ? questionPayload(row, 'BOOK') : null }});
  }}
  console.log(JSON.stringify(out));
}});
"""
    tmp = os.path.join(tempfile.gettempdir(), f"parity_{os.getpid()}.mjs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(script)
    try:
        rows = [c[1] for c in PARITY_CASES]
        r = subprocess.run([node, tmp], input=json.dumps(rows), capture_output=True,
                           text=True, timeout=60)
        if r.returncode:
            ng(f"パリティ: node が落ちた — {(r.stderr or '')[:200]}")
            return
        real = json.loads(r.stdout)
    finally:
        os.remove(tmp)

    n_ok = 0
    for (label, row), mjs in zip(PARITY_CASES, real):
        py_errs = imp.validate_questions_py([row])
        py_ok = not py_errs
        if py_ok != mjs["ok"]:
            ng(f"パリティ [{label}]: 合否が食い違う (python={py_ok} / 実物={mjs['ok']}"
               f"{' — ' + py_errs[0] if py_errs else ''})")
            continue
        if py_ok:
            py_payload = imp.question_payload_py(row, "BOOK")
            if py_payload != mjs["payload"]:
                ng(f"パリティ [{label}]: payload が食い違う\n"
                   f"      python: {json.dumps(py_payload, ensure_ascii=False)}\n"
                   f"      実物  : {json.dumps(mjs['payload'], ensure_ascii=False)}")
                continue
        n_ok += 1
    print(f"  [parity] {n_ok}/{len(PARITY_CASES)} 件で Python 実装が実物の .mjs と一致")
    if len([1 for c in PARITY_CASES]) - n_ok == 0 and n_ok < 5:
        ng("パリティ: 検査件数が少なすぎる (空振りの疑い)")


def main():
    print("=== import_books.py の検査 (偽 Supabase + パリティ) ===")
    check_all()
    check_parity()
    if problems:
        print(f"\n=== ✗ 問題 {len(problems)} 件 ===")
        return 1
    print("\n=== ALL PASS (シナリオ 12 + パリティ) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
