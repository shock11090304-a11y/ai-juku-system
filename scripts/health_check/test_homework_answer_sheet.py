#!/usr/bin/env python3
"""📝 記号の解答用紙 (マーク) のサーバの回帰テスト (2026-10-18 塾長「◎のとおりでお願いします。ただし、記述式は採点が難しいので
しばらくは記号問題がいい」の第1段)。

塾長の決定 (◎): 提出したらすぐ点数と問ごとの ○×・正解の番号は期限の翌日 (JST) から (期限なしは提出直後)・提出は 1 回で塾長が
「やり直し」・解答用紙の宿題は ✓完了 で閉じない (完了 = 提出)・期限後も受け付けて「期限後」・AI 読み取りなし・弱点集計に入れない・
個別割当と 📤 一括割当から。記号は ①② / アイウ / ABC / abc / 正誤、2〜8 択。同じプリントは正解表を使い回し、直したら全員を採点し直す。

固定する性質:
  [0] AIなし枠の許可集合は変えていない (新しい生徒ルートは /api/student/homework/{id}/sheet)・ルートは def・AI を呼ばない
  [1] 正解の読み方: 「3142」「３１４２」「3,1,4,2」「問1③ 問2①…」「ウアエイ」「うあえい」「ｳｱｴｲ」「CADB」「cadb」「正誤正正」「○×○○」
      「(1)ウ(2)ア」「1.ウ 2.ア」・[14] = どれでも正解・* = 全員正解・配列でも可・1 始まりで保存。数が違う・範囲外・読めない文字は理由つきで止める
  [2] 採点: どれでも正解・全員正解 (空欄も ○)・空欄は ×
  [3] 個別割当: answer_sheet があれば宿題の行・正解表・解答用紙の行を同じトランザクションで作る (RETURNING id)・同じプリント + 同じ正解 → 正解表を使い回す・
      違う正解 → 新しい表・key_id 指定 → その表・answer_sheet なし → 今までと同じ応答 (解答用紙の行を作らない)・
      正解がおかしい / 写真 (mode=photo) / プリントの食い違い → 422 で宿題の行も作らない
  [4] 📤 一括割当: 正解表は全員で 1 つ・対象外の生徒は飛ばす・正解がおかしいと誰にも割当てない・answer_sheet なしは今までと同じ
  [5] 生徒の宿題一覧: answer_sheet (問題数・択数・記号) を付ける・提出前は正解を出さない (期限が過ぎても)・answer_sheet_ready
  [6] ✓完了 (/complete) は解答用紙の宿題では 400 (古い画面からも閉じない)・解答用紙なしの宿題は今までどおり
  [7] 提出: 他人 / 無い宿題 / 解答用紙なし → 404・数が違う / 範囲外 → 422・採点はサーバ (画面の点数は無視)・宿題が completed・
      二度目は 409・期限後は late・正解の番号は期限の翌日から (期限の日は出さない・期限なしはすぐ)・なりすましの提出は印つき・
      question_attempts は 1 行も増えない・events は点数だけ (答えは残さない)・未ログイン 401・AIなし枠でも通る
  [8] 塾長: 宿題 1 件の解答用紙 (答え・○×・正解・問ごとの正解率)・正解表の一覧 (?print_id=)・確認表 (保存しない)・
      正解を直す → 全員を採点し直す (提出済みがいると問題数は変えられない)・「やり直し」で開き直して再提出できる・
      生徒詳細の宿題一覧と実施状況 (overview) に点数・生徒のトークンでは開けない
  [9] 削除と統合: 宿題の削除・生徒の削除・purge の孤児掃除 (生徒なし / 宿題なし)・統合で解答用紙も消える / 付け替わる
  [10] 表が無い DB (init_db が巻き戻った): 生徒の提出・解答用紙つきの割当・塾長の画面は 503「準備中」・一覧は answer_sheet なし・
      ✓完了 は今までどおり・生徒の削除は止まらない
  [11] ソース検査: 解答用紙の割当は RETURNING id (題名で引き直さない)・CI 登録

生徒名・メールは架空 (公開リポジトリ)。外部通信は一切しない。DB は一時 SQLite。

実行:
    python3 scripts/health_check/test_homework_answer_sheet.py
    # exit 0 = PASS / 1 = FAIL
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import json
import os
import re
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="hwsheet_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_hwsheet", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email, ai_disabled=1, course="kokuritsu_nankan", plan=None):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, plan, grade, goal, ai_disabled) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, email, "trial", far, course, plan, "高校2年", "国公立大学", int(ai_disabled)),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def make_print(mod, title, file_path):
    conn = mod.db()
    c = conn.cursor()
    c.execute("INSERT INTO lesson_prints (title, subject, file_path, is_published) VALUES (?, ?, ?, 1)", (title, "english", file_path))
    conn.commit()
    c.execute("SELECT id FROM lesson_prints WHERE file_path = ?", (file_path,))
    pid = c.fetchone()["id"]
    conn.close()
    return pid


def q(mod, sql, params=()):
    conn = mod.db()
    c = conn.cursor()
    c.execute(sql, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def ex(mod, sql, params=()):
    conn = mod.db()
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    conn.close()


def check_parser(mod):
    print("[1] 正解の読み方 (1 始まりで保存)")
    P = mod._hw_validate_key
    cases = [
        ("3142", 4, 4, "circled", [3, 1, 4, 2]),
        ("３１４２", 4, 4, "circled", [3, 1, 4, 2]),
        ("3, 1, 4, 2", 4, 4, "circled", [3, 1, 4, 2]),
        ("3\n1\n4\n2", 4, 4, "circled", [3, 1, 4, 2]),
        ("①③②④", 4, 4, "circled", [1, 3, 2, 4]),
        ("問1③ 問2① 問3④ 問4②", 4, 4, "circled", [3, 1, 4, 2]),
        ("問1 3 問2 1 問3 4 問4 2", 4, 4, "circled", [3, 1, 4, 2]),
        ("ウアエイ", 4, 4, "katakana", [3, 1, 4, 2]),
        ("うあえい", 4, 4, "katakana", [3, 1, 4, 2]),
        ("ｳｱｴｲ", 4, 4, "katakana", [3, 1, 4, 2]),
        ("3142", 4, 4, "katakana", [3, 1, 4, 2]),
        ("問1ウ 問2ア 問3エ 問4イ", 4, 4, "katakana", [3, 1, 4, 2]),
        ("(1)ウ(2)ア(3)エ(4)イ", 4, 4, "katakana", [3, 1, 4, 2]),
        ("1.ウ 2.ア 3.エ 4.イ", 4, 4, "katakana", [3, 1, 4, 2]),
        ("CADB", 4, 4, "upper", [3, 1, 4, 2]),
        ("cadb", 4, 4, "upper", [3, 1, 4, 2]),
        ("ＣＡＤＢ", 4, 4, "upper", [3, 1, 4, 2]),
        ("cadb", 4, 4, "lower", [3, 1, 4, 2]),
        ("Q1 c Q2 a", 2, 4, "lower", [3, 1]),
        ("正誤正正", 4, 2, "seigo", [1, 2, 1, 1]),
        ("○×○○", 4, 2, "seigo", [1, 2, 1, 1]),
        ("1211", 4, 2, "seigo", [1, 2, 1, 1]),
        ("3[14]2", 3, 4, "circled", [3, [1, 4], 2]),
        ("ウ[アイ]エ", 3, 4, "katakana", [3, [1, 2], 4]),
        ("3*2", 3, 4, "circled", [3, 0, 2]),
        ("8172", 4, 8, "circled", [8, 1, 7, 2]),
        ("クアキイ", 4, 8, "katakana", [8, 1, 7, 2]),
        ([3, 1, 4, 2], 4, 4, "circled", [3, 1, 4, 2]),
        (["ウ", "ア", "エ", "イ"], 4, 4, "katakana", [3, 1, 4, 2]),
        ([[1, 3], 2, 0], 3, 4, "circled", [[1, 3], 2, 0]),
        ([["ア", "ウ"], "イ"], 2, 4, "katakana", [[1, 3], 2]),
        ([[2, 2], 1], 2, 4, "circled", [2, 1]),
    ]
    for raw, nq, nc, style, want in cases:
        try:
            got = P(raw, nq, nc, style)
        except ValueError as e:
            got = f"ValueError: {e}"
        check(f"{style} {raw!r} → {want}", got == want, got)
    errors = [
        ("314", 4, 4, "circled", "正解が 3 個"),
        ("31425", 4, 4, "circled", "正解が 5 個"),
        ("3152", 4, 4, "circled", "範囲外"),
        ("ウアオイ", 4, 4, "katakana", "範囲外"),
        ("ウアエイ", 4, 4, "upper", "読めない文字"),
        ("3102", 4, 4, "circled", "0 は番号に使えません"),
        ("3[14", 3, 4, "circled", "閉じていません"),
        ("3]14", 3, 4, "circled", "対応する ["),
        ("3[]2", 3, 4, "circled", "空です"),
        ("[3*]", 1, 4, "circled", "外に書きます"),
        ("", 4, 4, "circled", "正解を入れてください"),
        ([3, None, 4, 2], 4, 4, "circled", "問2 の正解がありません"),
        ([3, True, 4, 2], 4, 4, "circled", "問2 の正解がありません"),
        ([3, "アイ", 4, 2], 4, 4, "katakana", "問2 の正解"),
        ([[0, 1]], 1, 4, "circled", "0 / *"),
        (None, 4, 4, "circled", "正解を入れてください"),
        ("正誤正", 4, 2, "seigo", "正解が 3 個"),
    ]
    for raw, nq, nc, style, frag in errors:
        try:
            P(raw, nq, nc, style)
            got = "通ってしまった"
        except ValueError as e:
            got = str(e)
        check(f"{style} {raw!r} は止める (「{frag}」)", frag in got, got)
    for args, frag in (((0, 4, "circled"), "1〜100"), ((101, 4, "circled"), "1〜100"), ((True, 4, "circled"), "整数"),
                       ((4, 9, "circled"), "2〜8"), ((4, 1, "circled"), "2〜8"), ((4, 4, "seigo"), "正誤は 2 択"),
                       ((4, 4, "roman"), "記号の種類"), ((4, "x", "circled"), "整数")):
        try:
            mod._hw_sheet_params(*args)
            got = "通ってしまった"
        except ValueError as e:
            got = str(e)
        check(f"問題数・択数・記号 {args} は止める (「{frag}」)", frag in got, got)
    check("択数を省くと 4 択・正誤は 2 択", mod._hw_sheet_params(5, None, "katakana") == (5, 4, "katakana")
          and mod._hw_sheet_params(5, None, "seigo") == (5, 2, "seigo") and mod._hw_sheet_params(5, None, None) == (5, 4, "circled"))
    check("確認表 (問1 ウ / 問2 [ア/イ] / 問3 全員正解)",
          mod._hw_key_display([3, [1, 2], 0], "katakana") == [{"no": 1, "label": "ウ"}, {"no": 2, "label": "ア/イ"}, {"no": 3, "label": "全員正解"}],
          mod._hw_key_display([3, [1, 2], 0], "katakana"))
    check("記号の並び (katakana 5 択 / upper 3 択 / 正誤)",
          mod._hw_sheet_labels("katakana", 5) == list("アイウエオ") and mod._hw_sheet_labels("upper", 3) == list("ABC")
          and mod._hw_sheet_labels("seigo", 2) == ["正", "誤"] and mod._hw_sheet_labels("circled", 8) == list("①②③④⑤⑥⑦⑧"))

    print("\n[2] 採点 (サーバだけ)")
    G = mod._hw_grade_choice
    check("全問正解", G([3, 1, 4, 2], [3, 1, 4, 2]) == (4, 4, [True, True, True, True]))
    check("空欄は ×", G([3, 1, 4, 2], [3, None, 4, 1]) == (2, 4, [True, False, True, False]))
    check("どれでも正解 ([1,4]) は 1 も 4 も ○・2 は ×", G([[1, 4], [1, 4], [1, 4]], [1, 4, 2]) == (2, 3, [True, True, False]))
    check("全員正解 (0) は空欄でも ○", G([0, 0], [None, 3]) == (2, 2, [True, True]))
    check("答えが短くても落ちない (足りない分は ×)", G([1, 2, 3], [1]) == (1, 3, [True, False, False]))


def main():
    print("📝 記号の解答用紙 (homework_answer_keys / homework_sheets)\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)

    print("[0] AIなし枠の許可集合は変えていない・AI を呼ばない")
    check("生徒の提出ルートは元からある prefix /api/student/homework/ に乗る",
          "/api/student/homework/1/sheet".startswith(mod._AI_DISABLED_ALLOWED_PREFIXES))
    check("prefix 集合に /api/student/homework/ が 1 本だけ", sum(1 for p in mod._AI_DISABLED_ALLOWED_PREFIXES if p.startswith("/api/student/homework")) == 1)
    check("トリリオン・ライトの deny にも当たらない", not mod._is_light_denied_path("/api/student/homework/1/sheet"))
    new_fns = [mod.submit_my_homework_sheet, mod._attach_homework_answer_sheets, mod._hw_sheet_view, mod._hw_resolve_answer_key,
               mod.admin_homework_answer_keys, mod.admin_homework_answer_key_check, mod.admin_homework_answer_key_results,
               mod.admin_homework_answer_key_update, mod.admin_homework_sheet, mod.admin_homework_sheet_reset]
    for fn in new_fns:
        src = inspect.getsource(fn)
        hits = re.findall(r"_call_\w+|anthropic|openai|gemini|_ai_safe", src, re.I)
        check(f"{fn.__name__}: AI 呼び出しが無い", not hits, hits)
        check(f"{fn.__name__}: async def ではない (同期 DB をイベントループに載せない)", not inspect.iscoroutinefunction(fn))
    src_submit = inspect.getsource(mod.submit_my_homework_sheet)
    check("提出は question_attempts に書かない (弱点集計に入れない)",
          "INSERT INTO question_attempts" not in src_submit and "_record_question_attempt" not in src_submit and "weakness" not in src_submit.lower().replace("弱点", ""))
    routes = {(getattr(r, "path", ""), m) for r in mod.app.routes for m in (getattr(r, "methods", None) or ())}
    for path, m in (("/api/student/homework/{homework_id}/sheet", "POST"), ("/api/admin/homework/answer-keys", "GET"),
                    ("/api/admin/homework/answer-keys/check", "POST"), ("/api/admin/homework/answer-keys/{key_id}", "GET"),
                    ("/api/admin/homework/answer-keys/{key_id}", "PUT"), ("/api/admin/homework/{homework_id}/sheet", "GET"),
                    ("/api/admin/homework/{homework_id}/sheet/reset", "POST")):
        check(f"ルート {m} {path} がある", (path, m) in routes)
    check("表が 2 つとも作られている (init_db)", mod._hw_sheet_ready())

    print()
    check_parser(mod)

    admin = {"Authorization": "Bearer " + mod._sign_admin_token()["token"]}
    sid_a = make_student(mod, "架空 マーク A", "hwsheet-a@example.org", ai_disabled=1)   # 塾生アプリのみ枠
    sid_b = make_student(mod, "架空 マーク B", "hwsheet-b@example.org", ai_disabled=1)
    sid_c = make_student(mod, "架空 マーク C", "hwsheet-c@example.org", ai_disabled=0)   # AIあり
    sid_x = make_student(mod, "架空 対象外 X", "hwsheet-x@example.org", ai_disabled=0, course=None, plan="standard")
    tok = {s: {"Authorization": "Bearer " + student_token(mod, s)} for s in (sid_a, sid_b, sid_c)}
    imp_b = {"Authorization": "Bearer " + mod._sign_session_token(sid_b, token_type="impersonation")}
    p1 = make_print(mod, "関係詞 確認テスト", "/lesson-prints/eng_kankeishi_mark_01.pdf")
    p2 = make_print(mod, "時制 確認テスト", "/lesson-prints/eng_jisei_mark_01.pdf")
    today = mod._today_jst()
    d_future = (today + datetime.timedelta(days=3)).isoformat()
    d_today = today.isoformat()
    d_past = (today - datetime.timedelta(days=2)).isoformat()

    def assign(payload):
        return client.post("/api/admin/homework/assign", json=payload, headers=admin)

    def sheets_of(hid):
        return q(mod, "SELECT * FROM homework_sheets WHERE homework_id = ?", (hid,))

    print("\n[3] 個別割当")
    n_hw0 = len(q(mod, "SELECT id FROM homework_assignments"))
    r = assign({"student_id": sid_a, "title": "解答用紙なしの宿題", "due_date": d_future})
    d = r.json()
    check("answer_sheet なし → 200・応答の項目は今までと同じ", r.status_code == 200 and set(d.keys()) ==
          {"ok", "homework_id", "student_id", "student_name", "title", "due_date", "message"}, r.text[:300])
    check("answer_sheet なし: 文言も今までどおり", d.get("message") == "✅ 架空 マーク A さんに宿題「解答用紙なしの宿題」を割当てました", d.get("message"))
    hw_plain = d.get("homework_id")
    check("answer_sheet なし: 宿題の行はでき、解答用紙の行は作らない", hw_plain and sheets_of(hw_plain) == [], hw_plain)
    r = assign({"student_id": sid_a, "title": "mode none", "answer_sheet": {"mode": "none"}})
    check("answer_sheet {mode:'none'} → 解答用紙なしと同じ", r.status_code == 200 and "answer_sheet" not in r.json()
          and sheets_of(r.json()["homework_id"]) == [], r.text[:200])

    sheet_kata = {"mode": "choice", "key": {"num_questions": 4, "num_choices": 4, "label_style": "katakana", "key": "ウアエイ"}}
    r = assign({"student_id": sid_a, "title": "関係詞 マーク", "due_date": d_future, "attachment_print_id": p1, "answer_sheet": sheet_kata})
    d = r.json()
    hw_a1 = d.get("homework_id")
    ash = d.get("answer_sheet") or {}
    check("解答用紙つき → 200・answer_sheet {key_id, 4 問, 4 択, katakana, print}", r.status_code == 200 and ash.get("num_questions") == 4
          and ash.get("num_choices") == 4 and ash.get("label_style") == "katakana" and ash.get("print_id") == p1 and ash.get("reused_key") is False,
          r.text[:300])
    check("文言に「📝 記号の解答用紙つき・4 問」", "記号の解答用紙つき・4 問" in (d.get("message") or ""), d.get("message"))
    key1 = ash.get("key_id")
    krow = q(mod, "SELECT * FROM homework_answer_keys WHERE id = ?", (key1,))
    check("正解表: 1 始まりで保存・print_id = 添付プリント・題名", krow and json.loads(krow[0]["key_json"]) == [3, 1, 4, 2]
          and krow[0]["print_id"] == p1 and krow[0]["title"] == "関係詞 マーク" and krow[0]["reveal_policy"] == "after_due", krow)
    srow = sheets_of(hw_a1)
    check("解答用紙の行: 宿題 1 行に 1 行・生徒・key_id・未提出", len(srow) == 1 and srow[0]["student_id"] == sid_a and srow[0]["key_id"] == key1
          and srow[0]["mode"] == "choice" and srow[0]["submitted_at"] is None, srow)
    r = assign({"student_id": sid_b, "title": "関係詞 マーク (B)", "due_date": d_future, "attachment_print_id": p1,
                "answer_sheet": {"mode": "choice", "key": {"num_questions": 4, "label_style": "katakana", "key": "3142"}}})
    ash = r.json().get("answer_sheet") or {}
    hw_b1 = r.json().get("homework_id")
    check("同じプリント + 同じ正解 (数字で打っても) → 同じ正解表を使い回す", r.status_code == 200 and ash.get("key_id") == key1
          and ash.get("reused_key") is True, r.text[:300])
    r = assign({"student_id": sid_b, "title": "関係詞 マーク 別解", "attachment_print_id": p1,
                "answer_sheet": {"mode": "choice", "key": {"num_questions": 4, "label_style": "katakana", "key": "ウアエウ"}}})
    key1b = (r.json().get("answer_sheet") or {}).get("key_id")
    check("同じプリントでも正解が違えば新しい正解表 (既存の表は書き換えない)", r.status_code == 200 and key1b and key1b != key1
          and json.loads(q(mod, "SELECT key_json FROM homework_answer_keys WHERE id = ?", (key1,))[0]["key_json"]) == [3, 1, 4, 2], r.text[:200])
    hw_b_other = r.json().get("homework_id")
    r = assign({"student_id": sid_c, "title": "関係詞 マーク (C)", "due_date": d_past, "answer_sheet": {"mode": "choice", "key_id": key1}})
    hw_c1 = r.json().get("homework_id")
    check("key_id 指定 → その正解表 (添付なしでも)", r.status_code == 200 and (r.json().get("answer_sheet") or {}).get("key_id") == key1
          and sheets_of(hw_c1)[0]["key_id"] == key1, r.text[:200])
    n_before = len(q(mod, "SELECT id FROM homework_assignments"))
    for label, sheet, extra, code in (
        ("正解の数が違う", {"mode": "choice", "key": {"num_questions": 5, "key": "3142"}}, {}, 422),
        ("範囲外", {"mode": "choice", "key": {"num_questions": 4, "num_choices": 3, "key": "3142"}}, {}, 422),
        ("写真 (mode=photo) はまだ", {"mode": "photo"}, {}, 422),
        ("key も key_id も無い", {"mode": "choice"}, {}, 422),
        ("key_id が数字でない", {"mode": "choice", "key_id": "abc"}, {}, 422),
        ("存在しない key_id", {"mode": "choice", "key_id": 999999}, {}, 404),
        ("添付プリントと解答用紙のプリントが違う", {"mode": "choice", "print_id": p2, "key": {"num_questions": 1, "key": "1"}},
         {"attachment_print_id": p1}, 422),
        ("存在しない解答用紙のプリント", {"mode": "choice", "print_id": 999999, "key": {"num_questions": 1, "key": "1"}}, {}, 404),
        ("見せる時期がおかしい", {"mode": "choice", "reveal": "never", "key": {"num_questions": 1, "key": "1"}}, {}, 422),
        ("answer_sheet が文字列", "3142", {}, 422),
    ):
        r = assign(dict({"student_id": sid_a, "title": "失敗するはずの宿題", "answer_sheet": sheet}, **extra))
        check(f"{label} → {code} (理由つき)", r.status_code == code and (r.json().get("detail") or ""), f"status={r.status_code} {r.text[:200]}")
    check("失敗した割当は宿題の行を 1 つも作らない", len(q(mod, "SELECT id FROM homework_assignments")) == n_before)
    r = assign({"student_id": sid_a, "title": "答え方 正誤", "answer_sheet": {"mode": "choice", "key": {"num_questions": 3, "label_style": "seigo", "key": "○×○"}}})
    check("正誤 (○× で打っても・択数省略 = 2 択)", r.status_code == 200 and (r.json().get("answer_sheet") or {}).get("num_choices") == 2
          and json.loads(q(mod, "SELECT key_json FROM homework_answer_keys WHERE id = ?", (r.json()["answer_sheet"]["key_id"],))[0]["key_json"]) == [1, 2, 1],
          r.text[:200])
    hw_seigo = r.json().get("homework_id")
    r = assign({"student_id": sid_x, "title": "対象外", "answer_sheet": sheet_kata})
    check("学習管理の対象外の生徒 → 400 (今までどおり)・解答用紙も作らない", r.status_code == 400
          and not q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_x,)), r.text[:200])

    print("\n[4] 📤 一括割当")
    r = client.post("/api/admin/homework/assign-bulk", headers=admin, json={
        "student_ids": [sid_a, sid_b, sid_x], "title": "時制 マーク 一括", "due_date": d_future, "attachment_print_id": p2,
        "answer_sheet": {"mode": "choice", "key": {"num_questions": 5, "num_choices": 5, "label_style": "upper", "key": "CADBE"}}})
    d = r.json()
    ash = d.get("answer_sheet") or {}
    check("一括 → 200・2 名に割当・対象外 1 名は飛ばす", r.status_code == 200 and d.get("assigned_count") == 2 and d.get("skipped_count") == 1, r.text[:300])
    bulk_ids = [a.get("homework_id") for a in d.get("assigned", [])]
    bulk_sheets = q(mod, "SELECT homework_id, student_id, key_id FROM homework_sheets WHERE key_id = ?", (ash.get("key_id"),))
    check("正解表は全員で 1 つ・解答用紙は割当てた 2 名ぶん (宿題の行と同じ ID)", ash.get("key_id") and len(bulk_sheets) == 2
          and sorted(x["homework_id"] for x in bulk_sheets) == sorted(bulk_ids) and {x["student_id"] for x in bulk_sheets} == {sid_a, sid_b},
          (ash, bulk_sheets, bulk_ids))
    check("一括の正解表は 1 行だけ (print_id = 添付)", len(q(mod, "SELECT id FROM homework_answer_keys WHERE print_id = ?", (p2,))) == 1)
    hw_bulk_a = [x["homework_id"] for x in bulk_sheets if x["student_id"] == sid_a][0]
    hw_bulk_b = [x["homework_id"] for x in bulk_sheets if x["student_id"] == sid_b][0]
    n_before = len(q(mod, "SELECT id FROM homework_assignments"))
    r = client.post("/api/admin/homework/assign-bulk", headers=admin, json={
        "student_ids": [sid_a, sid_b], "title": "壊れた正解", "answer_sheet": {"mode": "choice", "key": {"num_questions": 5, "key": "3142"}}})
    check("一括で正解がおかしい → 422・誰にも割当てない", r.status_code == 422 and len(q(mod, "SELECT id FROM homework_assignments")) == n_before,
          r.text[:200])
    r = client.post("/api/admin/homework/assign-bulk", headers=admin, json={"student_ids": [sid_a, sid_b], "title": "一括 解答用紙なし"})
    d = r.json()
    check("一括 answer_sheet なし → 今までと同じ応答・解答用紙の行なし", r.status_code == 200 and "answer_sheet" not in d
          and set(d.keys()) == {"ok", "assigned_count", "skipped_count", "assigned", "skipped", "title", "message"}
          and all(set(a.keys()) == {"id", "name"} for a in d.get("assigned", []))
          and not q(mod, "SELECT s.id FROM homework_sheets s JOIN homework_assignments h ON h.id = s.homework_id WHERE h.title = ?", ("一括 解答用紙なし",)),
          r.text[:300])

    print("\n[5] 生徒の宿題一覧")
    r = client.get("/api/student/homework", headers=tok[sid_a])
    d = r.json()
    check("AIなし枠 → 200・answer_sheet_ready: true", r.status_code == 200 and d.get("answer_sheet_ready") is True, r.text[:200])
    by_id = {it["id"]: it for it in d.get("items", [])}
    a1 = (by_id.get(hw_a1) or {}).get("answer_sheet") or {}
    check("解答用紙の宿題に answer_sheet {mode, 4 問, 4 択, katakana, ア〜エ, 未提出}", a1.get("mode") == "choice" and a1.get("num_questions") == 4
          and a1.get("num_choices") == 4 and a1.get("label_style") == "katakana" and a1.get("labels") == list("アイウエ")
          and a1.get("submitted") is False and a1.get("available") is True, a1)
    check("提出前は正解・点数・○× を出さない", a1.get("correct") is None and a1.get("score_correct") is None and a1.get("results") is None
          and a1.get("reveal") is False, a1)
    check("正解表の中身・key_id を生徒に返さない", "key_json" not in r.text and "key_id" not in r.text and "key_display" not in r.text, r.text[:200])
    check("reveal_on = 期限の翌日", a1.get("reveal_on") == (today + datetime.timedelta(days=4)).isoformat(), a1.get("reveal_on"))
    check("解答用紙なしの宿題は answer_sheet = None", (by_id.get(hw_plain) or {}).get("answer_sheet", "missing") is None)
    _real_today = mod._today_jst
    try:
        mod._today_jst = lambda: today + datetime.timedelta(days=30)
        r = client.get("/api/student/homework", headers=tok[sid_a])
        a1 = ({it["id"]: it for it in r.json().get("items", [])}.get(hw_a1) or {}).get("answer_sheet") or {}
        check("期限が過ぎても、提出していない生徒には正解を出さない (見てから写して出せない)", a1.get("correct") is None and a1.get("reveal") is False, a1)
    finally:
        mod._today_jst = _real_today

    print("\n[6] ✓完了 (/complete)")
    r = client.post(f"/api/student/homework/{hw_a1}/complete", json={}, headers=tok[sid_a])
    check("解答用紙の宿題を ✓完了 → 400 (提出が完了)", r.status_code == 400 and "解答用紙" in (r.json().get("detail") or ""), r.text[:200])
    check("400 のあと宿題は open のまま", q(mod, "SELECT status FROM homework_assignments WHERE id = ?", (hw_a1,))[0]["status"] == "open")
    r = client.post(f"/api/student/homework/{hw_plain}/complete", json={"student_note": "やりました"}, headers=tok[sid_a])
    check("解答用紙なしの宿題は今までどおり ✓完了 できる", r.status_code == 200 and r.json().get("status") == "completed", r.text[:200])

    print("\n[7] 提出 (POST /api/student/homework/{id}/sheet)")
    n_qa0 = len(q(mod, "SELECT id FROM question_attempts"))
    url_a1 = f"/api/student/homework/{hw_a1}/sheet"
    r = client.post(url_a1, json={"answers": [3, 1, 4, 2]})
    check("未ログイン → 401", r.status_code == 401, r.status_code)
    for label, hid, code in (("他人 (B) の宿題", hw_b1, 404), ("存在しない宿題", 999999, 404), ("解答用紙なしの宿題", hw_plain, 404)):
        r = client.post(f"/api/student/homework/{hid}/sheet", json={"answers": [3, 1, 4, 2]}, headers=tok[sid_a])
        check(f"{label} → {code}", r.status_code == code, f"status={r.status_code} {r.text[:160]}")
    check("他人の宿題は 1 文字も書かない (B の解答用紙は未提出のまま)", sheets_of(hw_b1)[0]["submitted_at"] is None)
    for label, ans in (("数が足りない", [3, 1, 4]), ("数が多い", [3, 1, 4, 2, 1]), ("範囲外 (5)", [3, 1, 5, 2]), ("0", [3, 0, 4, 2]),
                       ("文字", [3, "ウ", 4, 2]), ("true", [3, True, 4, 2]), ("配列でない", "3142"), ("小数", [3, 1.5, 4, 2])):
        r = client.post(url_a1, json={"answers": ans}, headers=tok[sid_a])
        check(f"答えが {label} → 422", r.status_code == 422 and (r.json().get("detail") or ""), f"status={r.status_code} {r.text[:160]}")
    check("422 のあとも未提出のまま", sheets_of(hw_a1)[0]["submitted_at"] is None)
    r = client.post(url_a1, json={"answers": [3, 2, None, "2"], "score_correct": 4, "score": 100, "results": [True] * 4,
                                  "student_note": "マークしました"}, headers=tok[sid_a])
    d = r.json()
    v = d.get("answer_sheet") or {}
    check("提出 (AIなし枠) → 200・status completed", r.status_code == 200 and d.get("status") == "completed", r.text[:300])
    check("採点はサーバ (画面の点数は無視): 2/4・○×・空欄は ×", v.get("score_correct") == 2 and v.get("score_total") == 4
          and v.get("results") == [True, False, False, True] and v.get("answers") == [3, 2, None, 2], v)
    check("期限前の提出: 期限後ではない・正解の番号はまだ出さない (期限の翌日から)", v.get("late") is False and v.get("reveal") is False
          and v.get("correct") is None and v.get("submitted") is True and v.get("submitted_at"), v)
    hw_row = q(mod, "SELECT status, completed_at, student_note FROM homework_assignments WHERE id = ?", (hw_a1,))[0]
    check("宿題が completed になり完了時刻とメモが入る (同じトランザクション)", hw_row["status"] == "completed" and hw_row["completed_at"]
          and hw_row["student_note"] == "マークしました", hw_row)
    srow = sheets_of(hw_a1)[0]
    check("解答用紙の行: 答え (1 始まり)・点数・提出時刻・なりすましではない", json.loads(srow["answers_json"]) == [3, 2, None, 2]
          and srow["score_correct"] == 2 and srow["score_total"] == 4 and srow["submitted_at"] and srow["by_impersonation"] == 0
          and srow["late"] == 0, srow)
    r = client.post(url_a1, json={"answers": [3, 1, 4, 2]}, headers=tok[sid_a])
    check("二度目の提出 → 409・点数は変わらない", r.status_code == 409 and sheets_of(hw_a1)[0]["score_correct"] == 2, r.text[:200])
    # 二重提出の競合: 最初の SELECT のあと・書く前に別の提出が確定した (2 台の端末から同時に押した)
    r = assign({"student_id": sid_a, "title": "同時に提出", "due_date": d_future, "answer_sheet": {"mode": "choice", "key_id": key1}})
    hw_race = r.json().get("homework_id")
    _real_validate = mod._hw_validate_answers

    def _racing_validate(raw, nq, nc):
        out = _real_validate(raw, nq, nc)
        ex(mod, "UPDATE homework_sheets SET answers_json = ?, score_correct = 1, score_total = 4, submitted_at = CURRENT_TIMESTAMP "
                "WHERE homework_id = ?", (json.dumps([1, 1, 1, 1]), hw_race))
        return out
    try:
        mod._hw_validate_answers = _racing_validate
        r = client.post(f"/api/student/homework/{hw_race}/sheet", json={"answers": [3, 1, 4, 2]}, headers=tok[sid_a])
    finally:
        mod._hw_validate_answers = _real_validate
    srow = sheets_of(hw_race)[0]
    check("同時に提出: 後から書く方は 409 (submitted_at IS NULL の UPDATE が 0 行)・先の提出を上書きしない",
          r.status_code == 409 and json.loads(srow["answers_json"]) == [1, 1, 1, 1] and srow["score_correct"] == 1, (r.status_code, srow))
    check("同時に提出: 409 の側は宿題を completed にしない (ロールバック)",
          q(mod, "SELECT status FROM homework_assignments WHERE id = ?", (hw_race,))[0]["status"] == "open")
    ex(mod, "DELETE FROM homework_sheets WHERE homework_id = ?", (hw_race,))
    ex(mod, "DELETE FROM homework_assignments WHERE id = ?", (hw_race,))
    check("question_attempts は 1 行も増えない (弱点集計に入れない)", len(q(mod, "SELECT id FROM question_attempts")) == n_qa0)
    ev = q(mod, "SELECT props FROM events WHERE name = 'homework_sheet_submitted'")
    evp = json.loads(ev[-1]["props"]) if ev else {}
    check("events は点数だけ (答えは残さない)", ev and evp.get("score_correct") == 2 and evp.get("score_total") == 4 and "answers" not in evp, evp)
    r = client.get("/api/student/homework", headers=tok[sid_a])
    a1 = ({it["id"]: it for it in r.json().get("items", [])}.get(hw_a1) or {}).get("answer_sheet") or {}
    check("一覧でも提出後は点数と ○× (正解の番号はまだ)", a1.get("submitted") is True and a1.get("score_correct") == 2
          and a1.get("results") == [True, False, False, True] and a1.get("correct") is None, a1)
    try:
        mod._today_jst = lambda: today + datetime.timedelta(days=3)   # 期限の日
        a1 = ({it["id"]: it for it in client.get("/api/student/homework", headers=tok[sid_a]).json().get("items", [])}.get(hw_a1) or {}).get("answer_sheet") or {}
        check("期限の日 (JST) は正解の番号を出さない", a1.get("correct") is None and a1.get("reveal") is False, a1)
        mod._today_jst = lambda: today + datetime.timedelta(days=4)   # 期限の翌日
        a1 = ({it["id"]: it for it in client.get("/api/student/homework", headers=tok[sid_a]).json().get("items", [])}.get(hw_a1) or {}).get("answer_sheet") or {}
        check("期限の翌日 (JST) から正解の番号 (1 始まり) を出す", a1.get("reveal") is True and a1.get("correct") == [3, 1, 4, 2], a1)
    finally:
        mod._today_jst = _real_today

    # 期限が過ぎてからの提出 (C・AIあり・期限は 2 日前) → late・すぐ正解 (期限の翌日を過ぎている)
    r = client.post(f"/api/student/homework/{hw_c1}/sheet", json={"answers": [3, 1, 4, 2]}, headers=tok[sid_c])
    v = r.json().get("answer_sheet") or {}
    check("AIあり の生徒も同じルートで提出できる", r.status_code == 200, r.text[:200])
    check("期限後の提出は受け付けて late (「期限後」)・期限の翌日を過ぎているので正解も出す", v.get("late") is True and v.get("reveal") is True
          and v.get("correct") == [3, 1, 4, 2] and v.get("score_correct") == 4, v)
    # 期限なし (正誤) → 提出したらすぐ正解
    r = client.post(f"/api/student/homework/{hw_seigo}/sheet", json={"answers": [1, 1, 1]}, headers=tok[sid_a])
    v = r.json().get("answer_sheet") or {}
    check("期限なしは提出したらすぐ正解の番号を出す・期限後ではない", r.status_code == 200 and v.get("reveal") is True and v.get("correct") == [1, 2, 1]
          and v.get("late") is False and v.get("score_correct") == 2 and v.get("labels") == ["正", "誤"], v)
    # 期限の日の提出は期限内
    r = assign({"student_id": sid_b, "title": "期限が今日", "due_date": d_today, "answer_sheet": {"mode": "choice", "key_id": key1}})
    hw_b_today = r.json().get("homework_id")
    # なりすまし (塾長が B の画面で提出)
    r = client.post(f"/api/student/homework/{hw_b_today}/sheet", json={"answers": [3, 1, 4, 1]}, headers=imp_b)
    v = r.json().get("answer_sheet") or {}
    check("期限の日の提出は期限内 (late でない)・正解は翌日から", r.status_code == 200 and v.get("late") is False and v.get("reveal") is False, v)
    check("塾長のなりすましで出した提出は by_impersonation=1", sheets_of(hw_b_today)[0]["by_impersonation"] == 1, sheets_of(hw_b_today))

    print("\n[8] 塾長の画面")
    r = client.get(f"/api/admin/homework/{hw_a1}/sheet", headers=tok[sid_a])
    check("生徒のトークンでは塾長の解答用紙を開けない (401)", r.status_code == 401, r.status_code)
    r = client.get(f"/api/admin/homework/{hw_a1}/sheet", headers=admin)
    d = r.json()
    sv = d.get("sheet") or {}
    check("宿題 1 件: 答え・○×・点数・正解 (期限前でも塾長には出す)・確認表", r.status_code == 200 and sv.get("answers") == [3, 2, None, 2]
          and sv.get("results") == [True, False, False, True] and sv.get("score_correct") == 2 and sv.get("correct") == [3, 1, 4, 2]
          and [x["label"] for x in sv.get("key_display", [])] == list("ウアエイ") and sv.get("by_impersonation") is False, r.text[:400])
    st = d.get("key_stats") or {}
    pq = st.get("per_question") or []
    # key1 の提出: A [3,2,None,2]=2点 / C [3,1,4,2]=4点 / B(なりすまし) [3,1,4,1]=3点
    check("同じ正解表の集計: 提出 3・平均 3.0・点数の分布", st.get("submitted") == 3 and st.get("avg_score") == 3.0
          and st.get("histogram") == [0, 0, 1, 1, 1], st)
    check("問ごとの正解率と選ばれた番号の分布 (問3: 正解 2/3・空欄 1)", len(pq) == 4 and pq[0]["correct_rate"] == 100
          and pq[1]["correct_count"] == 2 and pq[1]["dist"] == [2, 1, 0, 0] and pq[2]["correct_count"] == 2 and pq[2]["blank"] == 1
          and pq[3]["correct_rate"] == 66, pq)
    r = client.get(f"/api/admin/homework/{hw_plain}/sheet", headers=admin)
    check("解答用紙なしの宿題 → 404", r.status_code == 404, r.status_code)
    r = client.get(f"/api/admin/homework/answer-keys?print_id={p1}", headers=admin)
    items = r.json().get("items", [])
    check("正解表の一覧 ?print_id: 同じプリントの 2 表 (新しい順)・使っている数・提出数・プリント名", r.status_code == 200
          and [it["id"] for it in items] == [key1b, key1] and items[1]["used"] == 4 and items[1]["submitted"] == 3
          and items[1]["print_title"] and items[1]["key"] == [3, 1, 4, 2], r.text[:400])
    r = client.post("/api/admin/homework/answer-keys/check", headers=admin, json={"num_questions": 3, "label_style": "katakana", "key": "問1ウ 問2[アイ] 問3*"})
    d = r.json()
    check("確認表 (保存しない): 問1 ウ / 問2 ア/イ / 問3 全員正解", r.status_code == 200 and d.get("key") == [3, [1, 2], 0]
          and [x["label"] for x in d.get("key_display", [])] == ["ウ", "ア/イ", "全員正解"], r.text[:300])
    r = client.post("/api/admin/homework/answer-keys/check", headers=admin, json={"num_questions": 4, "label_style": "katakana", "key": "ウアエ"})
    check("確認表: 数が合わなければ 422 と理由 (「正解が 3 個あります (問題数は 4 問)」)", r.status_code == 422
          and "正解が 3 個あります" in (r.json().get("detail") or ""), r.text[:200])
    n_keys = len(q(mod, "SELECT id FROM homework_answer_keys"))
    check("確認表は正解表を作らない", n_keys == len(q(mod, "SELECT id FROM homework_answer_keys")))

    # 正解を直す: 問2 の正解を ア → [ア/イ] (A の 2 が正解になる)・問4 を全員正解に
    r = client.put(f"/api/admin/homework/answer-keys/{key1}", headers=admin, json={"key": "ウ[アイ]エ*"})
    d = r.json()
    check("正解を直す → 提出済み 3 人を採点し直し・点数が変わったのは 2 人 (A 2→3 (問3 は空欄)・B 3→4)", r.status_code == 200 and d.get("regraded") == 3
          and d.get("changed") == 2 and d.get("key", {}).get("key") == [3, [1, 2], 4, 0], r.text[:300])
    check("採点し直した点数が保存されている (A 3/4・C 4/4・B 4/4)", sheets_of(hw_a1)[0]["score_correct"] == 3 and sheets_of(hw_c1)[0]["score_correct"] == 4
          and sheets_of(hw_b_today)[0]["score_correct"] == 4, (sheets_of(hw_a1), sheets_of(hw_c1)))
    try:
        mod._today_jst = lambda: today + datetime.timedelta(days=4)
        a1 = ({it["id"]: it for it in client.get("/api/student/homework", headers=tok[sid_a]).json().get("items", [])}.get(hw_a1) or {}).get("answer_sheet") or {}
        check("生徒の画面も直した正解で採点 (3/4・正解の番号も新しい表)", a1.get("score_correct") == 3 and a1.get("results") == [True, True, False, True]
              and a1.get("correct") == [3, [1, 2], 4, 0], a1)
    finally:
        mod._today_jst = _real_today
    ev = q(mod, "SELECT props FROM events WHERE name = 'homework_answer_key_updated'")
    check("events に直す前と後の正解・採点し直した数", ev and json.loads(ev[-1]["props"]).get("old_key") == [3, 1, 4, 2]
          and json.loads(ev[-1]["props"]).get("regraded") == 3)
    r = client.put(f"/api/admin/homework/answer-keys/{key1}", headers=admin, json={"key": "ウアエイア", "num_questions": 5})
    check("提出済みがいる表の問題数は変えられない (409)", r.status_code == 409, r.text[:200])
    r = client.put(f"/api/admin/homework/answer-keys/{key1}", headers=admin, json={"key": "ウアエ"})
    check("直す正解の数が違う → 422 (表はそのまま)", r.status_code == 422
          and json.loads(q(mod, "SELECT key_json FROM homework_answer_keys WHERE id = ?", (key1,))[0]["key_json"]) == [3, [1, 2], 4, 0], r.text[:200])
    r = client.put(f"/api/admin/homework/answer-keys/{key1b}", headers=admin, json={"key": "ウアエイア", "num_questions": 5, "num_choices": 5})
    check("まだ誰も提出していない表は問題数・択数も変えられる", r.status_code == 200 and r.json().get("regraded") == 0
          and r.json()["key"]["num_questions"] == 5, r.text[:200])
    r = client.put("/api/admin/homework/answer-keys/999999", headers=admin, json={"key": "1"})
    check("存在しない正解表 → 404", r.status_code == 404, r.status_code)
    r = client.get(f"/api/admin/homework/answer-keys/{key1}", headers=admin)
    d = r.json()
    check("正解表ごとの結果: 4 人 (提出 3)・生徒名・宿題名・期限後の印", r.status_code == 200 and len(d.get("students", [])) == 4
          and d.get("stats", {}).get("submitted") == 3 and {x["student_name"] for x in d["students"]} >= {"架空 マーク A", "架空 マーク C"}
          and any(x["late"] for x in d["students"] if x["student_id"] == sid_c), r.text[:400])

    # やり直し
    r = client.post(f"/api/admin/homework/{hw_a1}/sheet/reset", headers=admin)
    check("「やり直し」 → 200", r.status_code == 200 and r.json().get("reset") is True, r.text[:200])
    srow = sheets_of(hw_a1)[0]
    hw_row = q(mod, "SELECT status, completed_at FROM homework_assignments WHERE id = ?", (hw_a1,))[0]
    check("やり直し: 答え・点数・提出時刻を空に・reset_count 1・宿題は open に戻る", srow["answers_json"] is None and srow["submitted_at"] is None
          and srow["score_correct"] is None and srow["reset_count"] == 1 and hw_row["status"] == "open" and hw_row["completed_at"] is None, (srow, hw_row))
    ev = q(mod, "SELECT props FROM events WHERE name = 'homework_sheet_reset'")
    check("やり直しの前の答えと点数を events に残す", ev and json.loads(ev[-1]["props"]).get("prev_score_correct") == 3
          and json.loads(ev[-1]["props"]).get("prev_answers") == [3, 2, None, 2])
    check("やり直しは他の生徒の提出に触れない (C は提出済みのまま)", sheets_of(hw_c1)[0]["submitted_at"] is not None)
    r = client.post(f"/api/admin/homework/{hw_a1}/sheet/reset", headers=admin)
    check("未提出をもう一度やり直し → already_open (何もしない)", r.status_code == 200 and r.json().get("already_open") is True
          and sheets_of(hw_a1)[0]["reset_count"] == 1, r.text[:200])
    r = client.post(url_a1, json={"answers": [3, 1, 4, 2]}, headers=tok[sid_a])
    check("やり直しのあとはもう一度提出できる", r.status_code == 200 and (r.json().get("answer_sheet") or {}).get("score_correct") == 4
          and (r.json().get("answer_sheet") or {}).get("reset_count") == 1, r.text[:200])

    r = client.get(f"/api/admin/homework/list?student_id={sid_a}", headers=admin)
    d = r.json()
    li = {it["id"]: it for it in d.get("items", [])}
    av = (li.get(hw_a1) or {}).get("answer_sheet") or {}
    check("生徒詳細の宿題一覧: answer_sheet (点数・答え・正解・key_id)・answer_sheet_ready", r.status_code == 200 and d.get("answer_sheet_ready") is True
          and av.get("score_correct") == 4 and av.get("correct") == [3, [1, 2], 4, 0] and av.get("key_id") == key1
          and (li.get(hw_plain) or {}).get("answer_sheet", "missing") is None, r.text[:300])
    r = client.get("/api/admin/homework/overview", headers=admin)
    found = {}
    for g in r.json().get("groups", []):
        for s_ in g.get("students", []):
            found[s_["homework_id"]] = s_.get("sheet", "missing")
    check("実施状況 (overview): 解答用紙の宿題に点数 {submitted, score_correct, score_total, late}・なしは None",
          (found.get(hw_c1) or {}).get("score_correct") == 4 and (found.get(hw_c1) or {}).get("late") is True
          and (found.get(hw_bulk_a) or {}).get("submitted") is False and (found.get(hw_bulk_a) or {}).get("score_total") == 5
          and found.get(hw_plain, "x") is None, {k: found.get(k) for k in (hw_c1, hw_bulk_a, hw_plain)})
    for path, method in ((f"/api/admin/homework/answer-keys?print_id={p1}", "get"), (f"/api/admin/homework/answer-keys/{key1}", "get"),
                         (f"/api/admin/homework/{hw_a1}/sheet/reset", "post")):
        r = getattr(client, method)(path, headers=tok[sid_c])
        check(f"生徒のトークンでは {method.upper()} {path.split('?')[0]} を使えない (401)", r.status_code == 401, r.status_code)

    print("\n[9] 削除と統合")
    r = client.delete(f"/api/admin/homework/{hw_b_other}", headers=admin)
    check("宿題を削除すると解答用紙の行も消える (正解表は残す)", r.status_code == 200 and sheets_of(hw_b_other) == []
          and q(mod, "SELECT id FROM homework_answer_keys WHERE id = ?", (key1b,)), r.text[:200])
    # 生徒の削除 (C)
    r = client.post(f"/api/admin/students/{sid_c}/delete", headers=admin, json={"confirm_email": "hwsheet-c@example.org", "dry_run": True})
    rc = (r.json().get("snapshot") or {}).get("related_counts") or {}
    check("生徒削除のプレビューに homework_sheets の件数", r.status_code == 200 and rc.get("homework_sheets") == 1, rc)
    r = client.post(f"/api/admin/students/{sid_c}/delete", headers=admin, json={"confirm_email": "hwsheet-c@example.org"})
    check("生徒を削除すると解答用紙の行も消える", r.status_code == 200 and not q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_c,)),
          r.text[:200])
    # 孤児: 生徒がいない行・宿題がない行
    ex(mod, "INSERT INTO homework_sheets (homework_id, student_id, mode, key_id) VALUES (?, ?, 'choice', ?)", (8_000_001, 7_000_001, key1))
    ex(mod, "INSERT INTO homework_sheets (homework_id, student_id, mode, key_id) VALUES (?, ?, 'choice', ?)", (8_000_002, sid_a, key1))
    conn = mod.db()
    try:
        out = mod._sweep_student_orphans(conn, conn.cursor(), False)
    finally:
        conn.close()
    check("purge の孤児掃除: 生徒のいない行と宿題のない行を消す", out.get("homework_sheets") == 1 and out.get("homework_sheets(宿題なし)") == 1
          and not q(mod, "SELECT id FROM homework_sheets WHERE homework_id IN (8000001, 8000002)"), out)
    check("孤児掃除は在籍生徒の解答用紙に触れない", len(q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_a,))) >= 3)
    # 統合: B を A に
    n_b = len(q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_b,)))
    n_a = len(q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_a,)))
    r = client.post(f"/api/admin/students/{sid_a}/merge", headers=admin, json={"from_id": sid_b, "dry_run": False})
    check("統合で解答用紙も残す側へ付け替わる", r.status_code == 200 and n_b > 0
          and len(q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_a,))) == n_a + n_b
          and not q(mod, "SELECT id FROM homework_sheets WHERE student_id = ?", (sid_b,)), r.text[:300])
    check("付け替えた解答用紙は宿題の行と同じ生徒 (ずれない)", not q(mod, "SELECT s.id FROM homework_sheets s JOIN homework_assignments h ON h.id = s.homework_id "
                                                         "WHERE s.student_id <> h.student_id"))

    print("\n[10] 表が無い DB (init_db のまとめ実行が巻き戻った)")
    ex(mod, "DROP TABLE homework_sheets")
    mod._HAS_COL_CACHE.clear()
    check("_hw_sheet_ready() が False", mod._hw_sheet_ready() is False)
    r = client.post(url_a1, json={"answers": [3, 1, 4, 2]}, headers=tok[sid_a])
    check("提出 → 503「準備中」", r.status_code == 503 and "準備中" in (r.json().get("detail") or ""), r.text[:200])
    n_before = len(q(mod, "SELECT id FROM homework_assignments"))
    r = assign({"student_id": sid_a, "title": "表なし", "answer_sheet": sheet_kata})
    check("解答用紙つきの割当 → 503 で宿題の行も作らない", r.status_code == 503 and len(q(mod, "SELECT id FROM homework_assignments")) == n_before, r.text[:200])
    r = client.post("/api/admin/homework/assign-bulk", headers=admin, json={"student_ids": [sid_a], "title": "表なし", "answer_sheet": sheet_kata})
    check("解答用紙つきの一括 → 503", r.status_code == 503, r.text[:200])
    r = assign({"student_id": sid_a, "title": "表なし 解答用紙なし"})
    check("解答用紙なしの割当は表が無くても今までどおり", r.status_code == 200, r.text[:200])
    hw_nosheet_tbl = r.json().get("homework_id")
    r = client.get("/api/student/homework", headers=tok[sid_a])
    d = r.json()
    check("生徒の一覧は 200・answer_sheet_ready false・answer_sheet は全部 None", r.status_code == 200 and d.get("answer_sheet_ready") is False
          and all(it.get("answer_sheet") is None for it in d.get("items", [])), r.text[:200])
    r = client.post(f"/api/student/homework/{hw_nosheet_tbl}/complete", json={}, headers=tok[sid_a])
    check("✓完了 は表が無くても今までどおり", r.status_code == 200, r.text[:200])
    for path, method in (("/api/admin/homework/answer-keys", "get"), (f"/api/admin/homework/answer-keys/{key1}", "get"),
                         (f"/api/admin/homework/{hw_a1}/sheet", "get"), (f"/api/admin/homework/{hw_a1}/sheet/reset", "post")):
        r = getattr(client, method)(path, headers=admin)
        check(f"塾長 {method.upper()} {path} → 503", r.status_code == 503, r.status_code)
    r = client.get(f"/api/admin/homework/list?student_id={sid_a}", headers=admin)
    check("塾長の宿題一覧は 200 (answer_sheet なし)", r.status_code == 200 and r.json().get("answer_sheet_ready") is False, r.text[:200])
    r = client.get("/api/admin/homework/overview", headers=admin)
    check("overview は 200 (点数なし)", r.status_code == 200, r.text[:200])
    r = client.delete(f"/api/admin/homework/{hw_nosheet_tbl}", headers=admin)
    check("宿題の削除は表が無くても動く", r.status_code == 200 and r.json().get("deleted") == 1, r.text[:200])
    sid_d = make_student(mod, "架空 削除 D", "hwsheet-d@example.org")
    r = client.post(f"/api/admin/students/{sid_d}/delete", headers=admin, json={"confirm_email": "hwsheet-d@example.org"})
    check("生徒の削除は表が無くても止まらない", r.status_code == 200 and not q(mod, "SELECT id FROM students WHERE id = ?", (sid_d,)), r.text[:200])
    mod.init_db()
    mod._HAS_COL_CACHE.clear()
    check("init_db をもう一度回せば表が戻る (CREATE TABLE IF NOT EXISTS)", mod._hw_sheet_ready() is True)

    print("\n[11] ソース検査")
    src_assign = inspect.getsource(mod.admin_homework_assign)
    check("個別割当の解答用紙つきは INSERT … RETURNING id (題名で引き直さない)",
          "VALUES (?, ?, ?, ?, ?, ?, 'open', 'admin') RETURNING id" in src_assign
          and src_assign.index("'open', 'admin') RETURNING id") > src_assign.index("if sheet is None:"))
    check("個別割当の解答用紙なしは今までの経路 (lastrowid → 題名の fallback) のまま", "hw_id = c.lastrowid" in src_assign
          and "WHERE student_id = ? AND title = ?" in src_assign)
    src_bulk = inspect.getsource(mod.admin_homework_assign_bulk)
    check("一括の解答用紙つきも RETURNING id", "RETURNING id" in src_bulk)
    check("正解表の新規も RETURNING id", "RETURNING id" in inspect.getsource(mod._hw_resolve_answer_key))
    check("提出は submitted_at IS NULL の行だけを書き、0 行なら 409", "AND submitted_at IS NULL" in src_submit and "rowcount == 0" in src_submit)
    main_src = open(MAIN_PY, encoding="utf-8").read()
    ddl = main_src[main_src.index("CREATE TABLE IF NOT EXISTS students ("):main_src.index("_migrations = [")]
    check("2 表とも init_db のまとめ実行 (CREATE TABLE IF NOT EXISTS) にある", "CREATE TABLE IF NOT EXISTS homework_answer_keys" in ddl
          and "CREATE TABLE IF NOT EXISTS homework_sheets" in ddl)
    check("既存の表への ALTER を足していない", not re.search(r"ALTER TABLE (homework_assignments|homework_sheets|homework_answer_keys)\b[^\n]*(answer|sheet|key_id)", main_src))
    ci = open(CI_YML, encoding="utf-8").read()
    check("CI (server-tests.yml) に登録", "test_homework_answer_sheet.py" in ci)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("  -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
