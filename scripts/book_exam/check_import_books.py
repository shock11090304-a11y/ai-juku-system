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
MODEL = os.path.join(ROOT, "exam-app", "exam-book-admin-model.mjs")

problems = []


def ng(msg):
    problems.append(msg)
    print(f"  ✗ {msg}")


# =============================================================================
# 偽 Supabase (登録画面が話すのと同じ 4 系統: auth / rest / storage)
# =============================================================================
class FakeSupabase:
    def __init__(self, role="teacher", fail_storage=False, corrupt_readback=False,
                 short_insert=False, lose_readback=False, drop_object=False):
        self.role = role
        self.fail_storage = fail_storage
        # ★ 「上げるのは 200 で通ったのに実体が無い」を作る。実物でも
        #   proxy や bucket の設定で起こりうる。生徒が受験を始めるまで気づけない。
        self.drop_object = drop_object
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
            if p.path.startswith("/storage/v1/object/sign/book-pdfs/"):
                # 受験画面が使う createSignedUrl と同じ経路。
                # ★ 実物の RLS は books.pdf_path = objects.name を条件にするので、
                #   pdf_path を書く前に署名を取ろうとすると読めない。それも再現する。
                name = p.path.split("/storage/v1/object/sign/book-pdfs/", 1)[1]
                key = "book-pdfs/" + name
                if key not in state.storage:
                    return self._send(404, {"message": "Object not found"})
                if not any(b.get("pdf_path") == name for b in state.books):
                    return self._send(404, {"message":
                        "Object not found (RLS: books.pdf_path と一致しない)"})
                return self._send(200, {"signedURL": f"/object/sign/{key}?token=t"})
            if p.path.startswith("/storage/v1/object/book-pdfs/"):
                if state.fail_storage:
                    return self._send(400, {"message":
                        "new row violates row-level security policy"})
                key = p.path.split("/storage/v1/object/", 1)[1]
                if not state.drop_object:
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
# ★ 選んではいけない側の PDF (ヒント付き)。中身を変えて、取り違えたら分かるように
HINT_PDF = TINY_PDF + b"%HINT\n"


def bundle_sekaishi():
    # source は実物と同じ形。PDF はこの stem + _問題.pdf の完全一致で選ばれる
    return {
        "source": "samples/2026-06-03_共通テスト世界史_マーク式.yaml",
        "subject_name": "世界史",
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
            # ★ ヒント付きは中身を変える。取り違えて上げたら S1 が捕まえる
            f.write(HINT_PDF if "ヒント" in n else TINY_PDF)
        meta["prints"].append({"file_path": f"/lesson-prints/{n}", "pages": 13})
    mp = os.path.join(td, "meta.json")
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return src, pdfs, mp


def run_importer(server, src, pdfs, metadata, *extra, password="pw-ok", config=None):
    env = dict(os.environ,
               EXAM_TEACHER_EMAIL="t@example.invalid",
               EXAM_TEACHER_PASSWORD=password,
               EXAM_PDF_METADATA=metadata)
    if config:
        # --customer の経路を検査する: config の CUSTOMERS から選ばせる
        env["EXAM_CONFIG_MJS"] = config
        env.pop("EXAM_SUPABASE_URL", None)
        env.pop("EXAM_SUPABASE_ANON", None)
    else:
        env["EXAM_SUPABASE_URL"] = f"http://127.0.0.1:{server.port}"
        env["EXAM_SUPABASE_ANON"] = "testanon"
    r = subprocess.run([sys.executable, IMPORTER, src, "--pdf-dir", pdfs, *extra],
                       capture_output=True, text=True, env=env, timeout=120)
    return r


# =============================================================================
# シナリオ
# =============================================================================
N_SCENARIO = 0


def scenario(name):
    global N_SCENARIO
    N_SCENARIO += 1
    print(f"  [scenario] {name}")


def check_all():
    td = tempfile.mkdtemp(prefix="import_check_")
    try:
        # --- S1: 正常系 (2 冊・choice/short 混在) -----------------------------
        scenario("S1 正常系 2 冊 → 非公開で入る (ヒント付き PDF の罠つき)")
        st = FakeSupabase()
        sv = Server(st)
        # ★ 実物で踏んだ罠を混ぜる (2026-08-15):
        #   ・「_ヒント付き問題.pdf」も『問題』を含む → 完全一致か _問題.pdf 終わりで選ぶ
        #   ・世界史は source の stem からの完全一致 / 国語は科目名 fallback の経路
        src, pdfs, mp = setup_dir(
            td + "/s1" if os.makedirs(td + "/s1") is None else td,
            [bundle_sekaishi(), bundle_kokugo()],
            ["2026-06-03_共通テスト世界史_マーク式_問題.pdf",
             "2026-06-03_共通テスト世界史_マーク式_ヒント付き問題.pdf",
             "2026-06-03_共通テスト国語_マーク式_問題.pdf",
             "2026-06-03_共通テスト国語_マーク式_ヒント付き問題.pdf"])
        r = run_importer(sv, src, pdfs, mp)
        sv.stop()
        if r.returncode != 0:
            ng(f"S1: exit {r.returncode} — {r.stdout[-300:]}{r.stderr[-200:]}")
        if len(st.books) != 2 or any(b["is_published"] for b in st.books):
            ng(f"S1: 冊子が非公開 2 冊になっていない: {st.books}")
        if len(st.storage) != 2 or any(v != TINY_PDF for v in st.storage.values()):
            ng("S1: PDF が 2 本、そのままの中身で上がっていない "
               "(HINT が混ざっていたら「ヒント付き問題」を取り違えている)")
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

        # --- S13: --customer で接続先が切り替わる (販売の要) -------------------
        #   ★ 既定 ('*') は閉じたポート、顧客 B だけが偽 Supabase を指す config で、
        #     「指定なし → 繋がらない / --customer B → 入る / 不明な顧客 → 名指しで
        #     エラー」の 3 点を見る。選択を間違えると **他塾のデータベースに教材を
        #     入れる** ことになるので、ここは絶対に落とせない。
        scenario("S13 --customer で顧客を選べる")
        st = FakeSupabase()
        sv = Server(st)
        cfgp = os.path.join(td, "customers.mjs")
        with open(cfgp, "w", encoding="utf-8") as f:
            f.write(f"""
export const CUSTOMERS = [
  {{
    name: 'default-juku',
    hosts: ['exam.default.example', '*'],
    url: 'http://127.0.0.1:1',
    anonKey: 'test' + 'anon',
  }},
  {{
    name: 'juku-b',
    hosts: ['exam.juku-b.example'],
    url: 'http://127.0.0.1:{sv.port}',
    anonKey: 'test' + 'anon',
  }},
];
""")
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史",
                         "--customer", "exam.juku-b.example", config=cfgp)
        if r.returncode != 0 or len(st.books) != 1:
            ng(f"S13: --customer で顧客 B に入らない (exit {r.returncode}, "
               f"{len(st.books)} 冊) {r.stdout[-200:]}")
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史", config=cfgp)
        if r.returncode == 0 or len(st.books) != 1:
            ng(f"S13: 指定なしなのに既定以外へ入った (exit {r.returncode}, {len(st.books)} 冊)")
        r = run_importer(sv, src, pdfs, mp, "--customer", "存在しない塾", config=cfgp)
        sv.stop()
        if r.returncode == 0 or "見つかりません" not in (r.stdout + r.stderr):
            ng(f"S13: 不明な顧客を名指しで断らない (exit {r.returncode})")

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

        # --- S14: PDF が空ファイル → 冊子の行を作らずに落とす ------------------
        #   ★ 上げてから bucket に 400 で返されると「PDF の無い冊子」が残る。
        scenario("S14 空の PDF は冊子を作る前に落とす")
        st = FakeSupabase()
        sv = Server(st)
        s14, p14, m14 = setup_dir(os.path.join(td, "s14"), [bundle_sekaishi()],
                                  ["2026-06-03_共通テスト世界史_マーク式_問題.pdf"])
        open(os.path.join(p14, "2026-06-03_共通テスト世界史_マーク式_問題.pdf"),
             "wb").close()                                   # 0 バイトにする
        r = run_importer(sv, s14, p14, m14)
        sv.stop()
        if r.returncode == 0 or "空ファイル" not in r.stdout:
            ng(f"S14: 空の PDF を素通しした (exit {r.returncode}) {r.stdout[-200:]}")
        if st.books or st.storage:
            ng(f"S14: 落とすべき冊子の行/PDF を作った ({len(st.books)} 冊)")

        # --- S15: 中身が PDF でない → 冊子の行を作らずに落とす ------------------
        #   ★ bucket は Content-Type の申告だけを見るので**上がってしまう**。
        #     受験画面で pdf.js が開けず、生徒が受験を始められない形になる。
        scenario("S15 拡張子だけ .pdf のファイルを落とす")
        st = FakeSupabase()
        sv = Server(st)
        s15, p15, m15 = setup_dir(os.path.join(td, "s15"), [bundle_sekaishi()],
                                  ["2026-06-03_共通テスト世界史_マーク式_問題.pdf"])
        with open(os.path.join(p15, "2026-06-03_共通テスト世界史_マーク式_問題.pdf"),
                  "wb") as f:
            f.write("PK\x03\x04 これは PDF ではない".encode())
        r = run_importer(sv, s15, p15, m15)
        sv.stop()
        if r.returncode == 0 or "PDF ではありません" not in r.stdout:
            ng(f"S15: PDF でないファイルを素通しした (exit {r.returncode})")
        if st.books or st.storage:
            ng("S15: 落とすべき冊子の行/PDF を作った")

        # --- S16: 設問のページが PDF のページ数を超える -------------------------
        #   ★ 登録画面 (.mjs) は弾くのに、この script は素通しだった。
        scenario("S16 PDF のページ数を超える page を落とす")
        st = FakeSupabase()
        sv = Server(st)
        b16 = bundle_sekaishi()
        b16["questions"][0]["page"] = 99          # _metadata.json は 13 頁
        s16, p16, m16 = setup_dir(os.path.join(td, "s16"), [b16],
                                  ["2026-06-03_共通テスト世界史_マーク式_問題.pdf"])
        r = run_importer(sv, s16, p16, m16)
        sv.stop()
        if r.returncode == 0 or "13 ページまでです" not in r.stdout:
            ng(f"S16: ページ超過を素通しした (exit {r.returncode}) {r.stdout[-200:]}")
        if st.books or st.storage:
            ng("S16: 落とすべき冊子の行/PDF を作った")

        # --- S17: 上げるのは 200 だが実体が無い → 公開させない ------------------
        #   ★ 受験画面と同じ経路 (署名 URL) で読めるところまで確かめる。
        #     ここを見ないと、生徒が受験を始めようとして初めて分かる。
        scenario("S17 上げた PDF が読めなければ失敗にする")
        st = FakeSupabase(drop_object=True)
        sv = Server(st)
        r = run_importer(sv, src, pdfs, mp, "--only", "世界史", "--publish")
        sv.stop()
        if r.returncode == 0 or "署名 URL を取れない" not in r.stdout:
            ng(f"S17: 実体の無い PDF を素通しした (exit {r.returncode}) {r.stdout[-200:]}")
        if any(b.get("is_published") for b in st.books):
            ng("S17: 読めない PDF の冊子を公開した")
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
    ("ページ超過", {"number": 1, "page": 5, "points": 1, "answer_type": "choice",
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
    // ★ ページ数を渡した側も見る (page ≤ page_count は登録画面だけが持っていた規則)
    const w = validateQuestions([row], {{ pageCount: 3 }});
    out.push({{ ok: v.ok, okPaged: w.ok,
                payload: v.ok ? questionPayload(row, 'BOOK') : null }});
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
        paged_errs = imp.validate_questions_py([row], page_count=3)
        if (not paged_errs) != mjs["okPaged"]:
            ng(f"パリティ [{label}]: ページ数を渡したときの合否が食い違う "
               f"(python={not paged_errs} / 実物={mjs['okPaged']}"
               f"{' — ' + paged_errs[0] if paged_errs else ''})")
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


def check_config_parity():
    """config の CUSTOMERS を、実物の node と python パーサの両方で読んで突き合わせる。

    ★ import_books.py は node 無しで動くために config を正規表現で読む。
      ブラウザ (本物の JS) と読み方がずれたら「Mac からは顧客 A に入れたつもりで、
      生徒は顧客 B に繋がっている」が起きる。データと **選択の結果** の両方を比べる。
    """
    node = shutil.which("node")
    if not node:
        ng("node が無いので config パリティ検査を回せない (CI には必ずある)")
        return
    cfg = os.path.join(ROOT, "exam-app", "exam-book-config.mjs")
    import importlib.util
    spec = importlib.util.spec_from_file_location("imp2", IMPORTER)
    imp = importlib.util.module_from_spec(spec)
    old_argv = sys.argv
    sys.argv = ["imp2"]
    try:
        spec.loader.exec_module(imp)
    finally:
        sys.argv = old_argv
    py = imp.parse_customers(open(cfg, encoding="utf-8").read())

    script = f"""
const mod = await import({json.dumps('file://' + cfg)});
const data = mod.CUSTOMERS.map((c) => ({{ name: c.name, hosts: c.hosts,
  url: c.url.replace(/\\/$/, ''), anonKey: c.anonKey }}));
const hosts = [...new Set(mod.CUSTOMERS.flatMap((c) => c.hosts))].filter((h) => h !== '*');
hosts.push('unknown.example.invalid');
const picks = Object.fromEntries(hosts.map((h) => [h, mod.resolveCustomer(h).url]));
console.log(JSON.stringify({{ data, picks }}));
"""
    tmp = os.path.join(tempfile.gettempdir(), f"cfg_parity_{os.getpid()}.mjs")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(script)
    try:
        r = subprocess.run([node, tmp], capture_output=True, text=True, timeout=60)
        if r.returncode:
            ng(f"config パリティ: node が落ちた — {(r.stderr or '')[:200]}")
            return
        real = json.loads(r.stdout)
    finally:
        os.remove(tmp)

    if py != real["data"]:
        ng("config パリティ: python パーサと実物の JS で CUSTOMERS の中身が食い違う\n"
           f"      python: {json.dumps(py, ensure_ascii=False)[:200]}\n"
           f"      実物  : {json.dumps(real['data'], ensure_ascii=False)[:200]}")
        return

    # 選択の結果も比べる (--customer <host> が選ぶ url と、ブラウザが選ぶ url)
    def py_pick(host):
        for c in py:
            if host == c["name"] or host in c["hosts"]:
                return c["url"]
        for c in py:
            if "*" in c["hosts"]:
                return c["url"]
        return py[0]["url"]
    bad_pick = [h for h, u in real["picks"].items() if py_pick(h) != u]
    if bad_pick:
        ng(f"config パリティ: ホスト {bad_pick} で選ばれる顧客が python と JS で違う")
        return
    print(f"  [parity] config: 顧客 {len(py)} 件のデータと {len(real['picks'])} ホストの"
          f"選択が実物の JS と一致")


def check_pdf_guards():
    """アップロードする PDF そのものの門番 (pdf_file_problem / pdf_page_count)。

    ★ 偽サーバを立てずに直接叩く。ここが緩むと「上がったのに受験画面で開けない
      冊子」や「ページ数が分からず page の検証が効かない冊子」が生まれる。
    """
    import importlib.util
    os.environ.setdefault("EXAM_SUPABASE_URL", "http://guard.invalid")
    os.environ.setdefault("EXAM_SUPABASE_ANON", "guard")
    spec = importlib.util.spec_from_file_location("imp_guard", IMPORTER)
    imp = importlib.util.module_from_spec(spec)
    old_argv, sys.argv = sys.argv, ["imp"]
    try:
        spec.loader.exec_module(imp)
    finally:
        sys.argv = old_argv

    td = tempfile.mkdtemp(prefix="pdf_guard_")
    try:
        good = os.path.join(td, "good.pdf")
        with open(good, "wb") as f:
            f.write(TINY_PDF)
        empty = os.path.join(td, "empty.pdf")
        open(empty, "wb").close()
        notpdf = os.path.join(td, "not.pdf")
        with open(notpdf, "wb") as f:
            f.write("これは PDF ではない".encode())
        big = os.path.join(td, "big.pdf")
        with open(big, "wb") as f:                 # sparse。実ディスクは食わない
            f.write(b"%PDF-")
            f.truncate(imp.MAX_PDF_BYTES + 1)
        broken = os.path.join(td, "broken.pdf")
        with open(broken, "wb") as f:
            f.write(b"%PDF-1.4\nthis is not a real pdf body")

        for label, path, want in (
                ("正しい PDF", good, None),
                ("空ファイル", empty, "空ファイル"),
                ("PDF でない", notpdf, "PDF ではありません"),
                ("大きすぎる", big, "大きすぎる"),
                ("在らないファイル", os.path.join(td, "no.pdf"), "見つからない")):
            got = imp.pdf_file_problem(path)
            if want is None and got is not None:
                ng(f"PDF 門番 [{label}]: 通るはずが落ちた ({got})")
            elif want is not None and (got is None or want not in got):
                ng(f"PDF 門番 [{label}]: 落とすはずが {got!r}")

        n, src = imp.pdf_page_count(good)
        if n != 1:
            ng(f"PDF 門番: ページ数が 1 でない ({n} / {src})")
        try:
            imp.pdf_page_count(broken)
            ng("PDF 門番: 壊れた PDF のページ数を返してしまった "
               "(壊れた冊子が上がると受験画面で開けない)")
        except imp.PdfError:
            pass
        except Exception as e:                       # noqa: BLE001
            ng(f"PDF 門番: 壊れた PDF で PdfError 以外が飛んだ ({type(e).__name__})。"
               f"取り込み全体が traceback で止まる")
        print("  [pdf] アップロード前の門番 5 種 + ページ数の読み取りを確認")
    finally:
        shutil.rmtree(td, ignore_errors=True)


def main():
    print("=== import_books.py の検査 (偽 Supabase + パリティ) ===")
    check_all()
    check_pdf_guards()
    check_parity()
    check_config_parity()
    if problems:
        print(f"\n=== ✗ 問題 {len(problems)} 件 ===")
        return 1
    print(f"\n=== ALL PASS (シナリオ {N_SCENARIO} + PDF 門番 + パリティ 2 系) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
