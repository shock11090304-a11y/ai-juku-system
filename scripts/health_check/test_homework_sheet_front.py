#!/usr/bin/env python3
"""📝 記号の解答用紙 (マーク) の画面の回帰テスト — 塾生アプリ (class.html)・マイページ (mypage.js)・共通部品 hw-sheet.js・
CEO (ceo.html の CeoHwSheet = 生徒詳細「📚 宿題」と 📤 一括割当の「✍️ 答え方」・宿題履歴の結果・正解の訂正・やり直し)。

背景 (2026-10-18 塾長「◎のとおりでお願いします。ただし、記述式は採点が難しいのでしばらくは記号問題がいい」の第1段・画面):
  サーバ (test_homework_answer_sheet.py) は先の段で入った。ここは画面。塾長の決定 (◎): 提出したらすぐ点数と ○×・正解の記号は
  期限の翌日 (JST) から (期限なしは提出直後)・提出は 1 回で塾長が「やり直し」・解答用紙の宿題に ✓完了 を出さない・期限後も受け付けて
  「期限後」・記号は ①② / アイウ / ABC / abc / 正誤 の 2〜8 択・同じプリントは正解表を使い回す・直したら全員を採点し直す。

★サーバとの約束を本物で確かめる: 一時 SQLite の本物のサーバで宿題を割当て・提出して、一覧・提出・塾長の画面の**本物の応答**を
  画面のテストの API に入れる。画面が送った提出の本文 (answers) は、サーバが受け付けた本文と 1 文字まで同じかを見る。
  CEO の「✍️ 答え方」が作った answer_sheet は本物の割当 API に送って 200 になるか、正解表から入力欄に戻した文字は
  サーバの読み方 (_hw_validate_key) で同じ正解に読めるかを見る。

固定する性質:
  [1] hw-sheet.js の部品: 記号の並び (5 種・2〜8 択)・どれでも正解 / 全員正解の表示・状態 (none/open/submitted/unavailable/unsupported)・
      「✏️ 解答用紙に答える（全N問）」・📝 8/10・JST の提出時刻 (端末のタイムゾーンに依らない)・「正解の記号は M/D（期限の翌日）から」・
      空欄の確認文・エラーの文言 (404 未デプロイ / 503 = 準備中・422 = 理由・通信失敗 = 下書きは残る)・下書き (localStorage・
      問題数 / 択数 / やり直しの回数が違えば使わない・壊れた値・throw する端末はページ内で続ける)・escape・ES5
  [2] 塾生アプリ (class.html の inline script を偽の DOM・本物のサーバの応答で、TZ=America/Los_Angeles):
      解答用紙の宿題に ✓完了 を出さない・「✏️ 解答用紙に答える（全N問）」→ 問ごとの記号のボタン・押すと選ぶ / もう一度で消す・
      下書きが残る (一覧に戻って開き直しても)・空欄は確認してから・1 回だけ送る (二度押ししても 1 回)・送る本文はサーバが受け付けた本文と同じ・
      提出したら点数と ○×・期限前は正解を出さず「M/D から」・バッジを 1 減らす・一覧に戻ると 📝 4/5・「📝 結果を見る」・
      409 (別の端末で提出済み) は一覧を読み直して提出済みの結果 (期限の翌日を過ぎていれば正解の記号・期限後)・422 / 503 / 404 / 通信失敗・
      answer_sheet_ready が無ければ今までどおり・hw-sheet.js が読めない / 正解表が無いときは ✓完了 を出さずに案内・
      やり直し後は前の下書きを使わない・プリントのボタン
  [3] マイページ (mypage.js の宿題欄を偽の DOM で): ✅ 完了する を出さない・画面いっぱいの重ねで解答用紙・提出・閉じたら読み直す・
      提出済みは「✅ 提出 (JST)」と 📝 4/5・期限後・完了時刻は JST
  [4] CEO の CeoHwSheet (ceo.html の inline script を本物のサーバの応答で): 表が無ければ「✍️ 答え方」を出さない・確認表 (問1 ウ …)・
      数が合わない / 確認中は割当を止める・正誤は 2 択に固定・同じプリントの前の正解表を入れる (打った正解は勝手に消さない)・
      プリント / 科目を替えたら前のプリントから自動で入れた正解は消して止める (正解表の無いプリントに前の正解を ✅ のまま付けない)・
      前のプリントの「入れる」は出さない・📤 一括割当 (hwbAssign をそのまま) は出した後も答え方を残す = 同じプリントの次の組にも
      解答用紙が付く・別のプリントに替えたら消える・全員スキップなら何も変えない・解答用紙なしでプリントに正解表があれば確認に ⚠・
      宿題履歴の 📝 4/5・提出時刻・期限後・📊 問ごとの正解率と選ばれた記号・✏️ 正解を直す (確認 → PUT → 採点し直し)・↩️ やり直し (確認 → POST)・
      実施状況のチップの点数・escape
  [5] サーバに戻して確かめる: CEO が作った answer_sheet で割当 / 一括割当が 200・正解表 → 入力欄の文字 → サーバの読み方で同じ正解
  [6] ソース検査: 読み込み順と ?v=・ES5・CEO の payload は解答用紙のときだけ answer_sheet を足す・案内文・CI 登録

★JS エンジンが無ければ FAIL (飛ばさない)。CI (ubuntu) は node、塾長の Mac は osascript -l JavaScript。AJ_JS_ENGINE で選べる。
  生徒名・メールは架空 (公開リポジトリ)。外部通信は一切しない。DB は一時 SQLite。

実行:
    python3 scripts/health_check/test_homework_sheet_front.py
    # exit 0 = PASS / 1 = FAIL
"""
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
CLASS_HTML = os.path.join(REPO, "class.html")
MYPAGE_HTML = os.path.join(REPO, "mypage.html")
MYPAGE_JS = os.path.join(REPO, "mypage.js")
CEO_HTML = os.path.join(REPO, "ceo.html")
HW_SHEET_JS = os.path.join(REPO, "hw-sheet.js")
HW_NOTICE_JS = os.path.join(REPO, "hw-notice.js")
CI_YML = os.path.join(REPO, ".github", "workflows", "server-tests.yml")

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 偽の DOM・JS エンジンの選び方は test_hw_notice_js.py、サーバの作り方は test_homework_answer_sheet.py を借りる (同じ土台)
H = load_module("hw_notice_js_harness_front", os.path.join(HERE, "test_hw_notice_js.py"))
S = load_module("hw_sheet_server_harness_front", os.path.join(HERE, "test_homework_answer_sheet.py"))


def jst_min(naive_utc):
    t = datetime.datetime.fromisoformat(str(naive_utc).replace(" ", "T")[:19])
    return (t + datetime.timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")


def md(d):
    return f"{d.month}/{d.day}"


# ---------------------------------------------------------------------------------------------------------------
# 本物のサーバで宿題を割当て・提出して、画面のテストに入れる応答を作る
def build_fixtures():
    print("[0] 本物のサーバ (一時 SQLite) で宿題を割当て・提出し、画面に渡す応答を作る")
    mod = S.load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    admin = {"Authorization": "Bearer " + mod._sign_admin_token()["token"]}
    fake_name = "架空 <マーク> 前面"   # 架空 (escape を見るために < > 入り)
    sid = S.make_student(mod, fake_name, "hwfront-a@example.org", ai_disabled=1)   # 塾生アプリのみ枠 (AIなし)
    tok = {"Authorization": "Bearer " + S.student_token(mod, sid)}
    p1 = S.make_print(mod, "関係詞 <確認> テスト", "/lesson-prints/eng_kankeishi_front_01.pdf")
    p2 = S.make_print(mod, "時制 (正解表なし) テスト", "/lesson-prints/eng_jisei_front_02.pdf")   # まだ正解表が無いプリント
    today = mod._today_jst()
    fut = today + datetime.timedelta(days=3)
    past = today - datetime.timedelta(days=2)

    def assign(payload):
        r = client.post("/api/admin/homework/assign", json=payload, headers=admin)
        check(f"割当「{payload['title']}」→ 200", r.status_code == 200, r.text[:300])
        return r.json()

    def sheet(nq, nc, style, key):
        return {"mode": "choice", "key": {"num_questions": nq, "num_choices": nc, "label_style": style, "key": key}}

    dA = assign({"student_id": sid, "title": "関係詞 <b>マーク</b>", "due_date": fut.isoformat(), "attachment_print_id": p1,
                 "answer_sheet": sheet(5, 4, "katakana", "ウアエイエ")})
    dB = assign({"student_id": sid, "title": "時制 マーク (期限切れ)", "due_date": past.isoformat(), "answer_sheet": sheet(3, 4, "circled", "312")})
    dC = assign({"student_id": sid, "title": "正誤 マーク", "answer_sheet": sheet(3, 2, "seigo", "正誤正")})
    dD = assign({"student_id": sid, "title": "音読の宿題"})
    dE = assign({"student_id": sid, "title": "8 択 マーク", "answer_sheet": sheet(2, 8, "upper", "HA")})
    A, B, C, D, E = (x.get("homework_id") for x in (dA, dB, dC, dD, dE))
    keyA = (dA.get("answer_sheet") or {}).get("key_id")
    L0 = client.get("/api/student/homework", headers=tok).json()
    check("一覧 (AIなし枠): answer_sheet_ready・print_open・5 件", L0.get("answer_sheet_ready") is True and L0.get("print_open") is True
          and len(L0.get("items") or []) == 5, json.dumps(L0, ensure_ascii=False)[:300])

    checks = {}
    for params in ({"num_questions": 5, "num_choices": 4, "label_style": "katakana", "key": "ウアエイ"},
                   {"num_questions": 5, "num_choices": 4, "label_style": "katakana", "key": "ウアエイエ"},
                   {"num_questions": 5, "num_choices": 4, "label_style": "katakana", "key": "ウ ア エ イ エ"}):
        r = client.post("/api/admin/homework/answer-keys/check", json=params, headers=admin)
        checks[json.dumps(params, ensure_ascii=False, separators=(",", ":"))] = {"status": r.status_code, "body": r.json()}
    check("確認表: 4 個は 422・5 個は 200 (サーバの読み方)", [v["status"] for v in checks.values()] == [422, 200, 200],
          [v["status"] for v in checks.values()])

    ANS_A = [3, 1, None, 2, 4]
    rA = client.post(f"/api/student/homework/{A}/sheet", json={"answers": ANS_A}, headers=tok)
    rB = client.post(f"/api/student/homework/{B}/sheet", json={"answers": [3, 2, 2]}, headers=tok)
    rB2 = client.post(f"/api/student/homework/{B}/sheet", json={"answers": [3, 2, 2]}, headers=tok)
    rC422 = client.post(f"/api/student/homework/{C}/sheet", json={"answers": [1]}, headers=tok)
    vA = (rA.json() or {}).get("answer_sheet") or {}
    check("提出 A (AIなし枠) → 200・4/5・期限前なので正解はまだ", rA.status_code == 200 and vA.get("score_correct") == 4
          and vA.get("score_total") == 5 and vA.get("reveal") is False, rA.text[:300])
    check("提出 B (期限後) → 200・late・正解あり / 二度目は 409 / C の数違いは 422",
          rB.status_code == 200 and (rB.json().get("answer_sheet") or {}).get("late") is True
          and (rB.json().get("answer_sheet") or {}).get("reveal") is True and rB2.status_code == 409 and rC422.status_code == 422,
          (rB.status_code, rB2.status_code, rC422.status_code))
    L1 = client.get("/api/student/homework", headers=tok).json()
    admin_list = client.get(f"/api/admin/homework/list?student_id={sid}", headers=admin).json()
    key_res_a = client.get(f"/api/admin/homework/answer-keys/{keyA}", headers=admin).json()
    keys_p1 = client.get(f"/api/admin/homework/answer-keys?print_id={p1}&limit=5", headers=admin).json()
    keys_p2 = client.get(f"/api/admin/homework/answer-keys?print_id={p2}&limit=5", headers=admin).json()
    probe = client.get("/api/admin/homework/answer-keys?limit=1", headers=admin)
    check("塾長の画面の応答 (一覧・正解表の結果・プリントの正解表・ready の確かめ) が取れる",
          admin_list.get("ok") and key_res_a.get("ok") and keys_p1.get("items") and probe.status_code == 200,
          (str(admin_list)[:120], str(key_res_a)[:120]))
    check("正解表の無いプリント (P2) の正解表の一覧は空", keys_p2.get("ok") is not False and keys_p2.get("items") == [], str(keys_p2)[:200])
    rReset = client.post(f"/api/admin/homework/{B}/sheet/reset", headers=admin)
    L2 = client.get("/api/student/homework", headers=tok).json()
    put_body = {"key": "ウ ア エ イ エ", "label_style": "katakana"}
    rPut = client.put(f"/api/admin/homework/answer-keys/{keyA}", json=put_body, headers=admin)
    check("やり直し (B) → 200・正解の訂正 (同じ正解) → 200・採点し直し 1 人", rReset.status_code == 200 and rPut.status_code == 200
          and rPut.json().get("regraded") == 1, (rReset.text[:160], rPut.text[:160]))
    # 📤 一括割当の本物の応答 (CEO の hwbAssign に返す)。上の一覧・正解表の一覧を取った後に出す (使った生徒の数などを変えない)
    bulk_sheet = sheet(5, 4, "katakana", "ウ ア エ イ エ")
    rBP1 = client.post("/api/admin/homework/assign-bulk", headers=admin,
                       json={"student_ids": [sid], "title": "関係詞 一括 マーク", "attachment_print_id": p1, "answer_sheet": bulk_sheet})
    rBSkip = client.post("/api/admin/homework/assign-bulk", headers=admin,
                         json={"student_ids": [sid + 100000], "title": "関係詞 一括 (全員スキップ)", "attachment_print_id": p1, "answer_sheet": bulk_sheet})
    rBNoPrint = client.post("/api/admin/homework/assign-bulk", headers=admin,
                            json={"student_ids": [sid], "title": "プリントなし 一括 マーク", "answer_sheet": sheet(5, 4, "katakana", "ウアエイエ")})
    rBPlain = client.post("/api/admin/homework/assign-bulk", headers=admin,
                          json={"student_ids": [sid], "title": "関係詞 一括 (完了ボタンだけ)", "attachment_print_id": p1})
    aBP1 = (rBP1.json() or {}).get("answer_sheet") or {}
    aBNo = (rBNoPrint.json() or {}).get("answer_sheet") or {}
    check("📤 一括 (P1・前と同じ正解) → 200・1 名・正解表 A を使い回す・print_id = P1", rBP1.status_code == 200 and rBP1.json().get("assigned_count") == 1
          and aBP1.get("key_id") == keyA and aBP1.get("reused_key") is True and aBP1.get("print_id") == p1, rBP1.text[:300])
    check("📤 一括 (全員スキップ) → 200・0 名・answer_sheet なし (正解表は保存しない)", rBSkip.status_code == 200 and rBSkip.json().get("assigned_count") == 0
          and rBSkip.json().get("skipped_count") == 1 and "answer_sheet" not in rBSkip.json(), rBSkip.text[:300])
    check("📤 一括 (プリントなし) → 200・新しい正解表・print_id なし", rBNoPrint.status_code == 200 and aBNo.get("key_id") not in (None, keyA)
          and aBNo.get("reused_key") is False and aBNo.get("print_id") is None, rBNoPrint.text[:300])
    check("📤 一括 (完了ボタンだけ) → 200・answer_sheet なし", rBPlain.status_code == 200 and "answer_sheet" not in rBPlain.json(), rBPlain.text[:300])

    fx = {
        "SID": sid, "NAME": fake_name, "A": A, "B": B, "C": C, "D": D, "E": E, "KEY_A": keyA, "P1": p1, "P2": p2,
        "L0": L0, "L1": L1, "L2": L2, "KEYS_P2": keys_p2,
        "R_A": {"status": rA.status_code, "body": rA.json()},
        "R_B409": {"status": rB2.status_code, "body": rB2.json()},
        "R_C422": {"status": rC422.status_code, "body": rC422.json()},
        "CHECKS": checks,
        "ADMIN_LIST": admin_list, "KEYRES_A": key_res_a, "KEYS_P1": keys_p1,
        "RESET_B": {"status": rReset.status_code, "body": rReset.json()},
        "PUT_A": {"status": rPut.status_code, "body": rPut.json()}, "PUT_BODY": put_body,
        "BULK_P1": {"status": rBP1.status_code, "body": rBP1.json()},
        "BULK_SKIP": {"status": rBSkip.status_code, "body": rBSkip.json()},
        "BULK_NOPRINT": {"status": rBNoPrint.status_code, "body": rBNoPrint.json()},
        "BULK_PLAIN": {"status": rBPlain.status_code, "body": rBPlain.json()},
        "ANS_A": ANS_A,
        "EXP": {
            "submitted_jst_A": jst_min(vA.get("submitted_at")),
            "reveal_md_A": md(fut + datetime.timedelta(days=1)),
            "completed_jst_A": jst_min(next(it for it in L1["items"] if it["id"] == A)["completed_at"]),
        },
    }
    return mod, client, admin, fx


# ---------------------------------------------------------------------------------------------------------------
# [1] hw-sheet.js の部品
JS_PURE = r"""
(function () {
  try {
    __loadHwSheet();
    var S = window.AJHwSheet;
    ok('AJHwSheet がある', !!S);
    var K4 = { label_style: 'katakana', num_choices: 4 };
    eq('記号: アイウエ (4 択)', S.labels(K4), ['ア', 'イ', 'ウ', 'エ']);
    eq('記号: ①〜⑧ (8 択)', S.labels({ label_style: 'circled', num_choices: 8 }).join(''), '①②③④⑤⑥⑦⑧');
    eq('記号: ABC (3 択)', S.labels({ label_style: 'upper', num_choices: 3 }), ['A', 'B', 'C']);
    eq('記号: abcde (5 択)', S.labels({ label_style: 'lower', num_choices: 5 }).join(''), 'abcde');
    eq('記号: 正誤', S.labels({ label_style: 'seigo', num_choices: 2 }), ['正', '誤']);
    eq('記号: サーバの labels を優先', S.labels({ label_style: 'katakana', num_choices: 3, labels: ['ア', 'イ', 'ウ'] }), ['ア', 'イ', 'ウ']);
    eq('どれでも正解は ア/ウ', S.labelOf([1, 3], K4), 'ア/ウ');
    eq('全員正解 (0)', S.labelOf(0, K4), '全員正解');
    eq('空欄は —', S.labelOf(null, K4), '—');
    var open = { id: 1, answer_sheet: { mode: 'choice', available: true, num_questions: 5, num_choices: 4, submitted: false } };
    eq('状態: 解答用紙なし', S.state({ id: 1, answer_sheet: null }, true), 'none');
    eq('状態: answer_sheet_ready でない', S.state(open, false), 'none');
    eq('状態: これから答える', S.state(open, true), 'open');
    eq('状態: 提出済み', S.state({ answer_sheet: { mode: 'choice', submitted: true } }, true), 'submitted');
    eq('状態: 正解表が無い', S.state({ answer_sheet: { mode: 'choice', available: false, num_questions: 5, num_choices: 4 } }, true), 'unavailable');
    eq('状態: 問題数が読めない', S.state({ answer_sheet: { mode: 'choice', available: true, num_questions: 0, num_choices: 4 } }, true), 'unavailable');
    eq('状態: 写真など別の答え方', S.state({ answer_sheet: { mode: 'photo' } }, true), 'unsupported');
    eq('ボタンの文言', S.answerButtonLabel({ num_questions: 5 }), '✏️ 解答用紙に答える（全5問）');
    eq('点数の文言', S.scoreText({ score_correct: 8, score_total: 10 }), '📝 8/10');
    eq('点数が無ければ空', S.scoreText({ score_correct: null, score_total: 10 }), '');
    var TS = [['2026-10-15 23:30:00.123456', '2026-10-16 08:30'], ['2026-10-15 23:30:00', '2026-10-16 08:30'], ['2026-10-15T23:30:00Z', '2026-10-16 08:30'],
              ['2026-10-15 23:30:00+00:00', '2026-10-16 08:30'], ['2026-10-16T08:30:00+09:00', '2026-10-16 08:30'], ['2026-10-15 14:59:59', '2026-10-15 23:59']];
    TS.forEach(function (t) { eq('提出時刻は JST: ' + t[0], S.fmtJst(t[0]), t[1]); });
    eq('期限の翌日から', S.revealNote({ reveal: false, reveal_on: '2026-10-22' }), '正解の記号は 10/22（期限の翌日）から見られます');
    eq('見せてよいときは案内なし', S.revealNote({ reveal: true }), '');
    var ct = S.confirmText([3, null, 1, null, null, null]);
    ok('空欄の確認: 問2・問4・問5 ほか・空欄 4 問・× になる', ct.indexOf('問2・問4・問5 ほか がまだです（空欄 4 問）') === 0 && ct.indexOf('空欄は × になります') >= 0, ct);
    ok('全部答えたら「提出は 1 回だけ」の確認', S.confirmText([1, 2]).indexOf('提出は 1 回だけ') >= 0);
    var ERR = [[{ status: 404, message: 'Not Found' }, '準備中です。少し待ってからもう一度押してね'],
               [{ status: 503, message: '解答用紙は準備中です' }, '準備中です。少し待ってからもう一度押してね'],
               [{ status: 422, message: '答えの数が 1 個です' }, '答えの数が 1 個です'],
               [{ status: 404, message: 'この宿題には解答用紙がありません' }, 'この宿題には解答用紙がありません'],
               [{ message: 'Failed to fetch' }, '通信できませんでした。電波のよいところでもう一度押してね（答えはこの端末に残っています）'],
               [{ status: 500, message: 'Internal Server Error' }, '通信できませんでした。電波のよいところでもう一度押してね（答えはこの端末に残っています）'],
               [{ status: 401, message: 'Unauthorized' }, 'ログインし直してからもう一度押してね（答えはこの端末に残っています）']];
    ERR.forEach(function (x) { eq('エラーの文言: ' + JSON.stringify(x[0]), S.errText(x[0]), x[1]); });

    // 下書き
    var st = memStore(); S._useStorage(st); S._clearMemory();
    var SH = { num_questions: 3, num_choices: 4, reset_count: 0 };
    S.saveDraft(7, 11, SH, [1, null, 4]);
    eq('下書きのキーは aj_hw_sheet_v1:<生徒>:<宿題>', Object.keys(st._m), ['aj_hw_sheet_v1:7:11']);
    eq('下書きを読める', S.loadDraft(7, 11, SH), [1, null, 4]);
    eq('択数が違う下書きは使わない', S.loadDraft(7, 11, { num_questions: 3, num_choices: 3, reset_count: 0 }), null);
    eq('問題数が違う下書きは使わない', S.loadDraft(7, 11, { num_questions: 4, num_choices: 4, reset_count: 0 }), null);
    eq('やり直しの後は前の下書きを使わない', S.loadDraft(7, 11, { num_questions: 3, num_choices: 4, reset_count: 1 }), null);
    st._m['aj_hw_sheet_v1:7:12'] = JSON.stringify({ v: 1, n: 3, c: 4, r: 0, a: [9, 'x', 2] });
    eq('範囲外・文字は空欄にする', S.loadDraft(7, 12, SH), [null, null, 2]);
    st._m['aj_hw_sheet_v1:7:13'] = '{broken';
    eq('壊れた下書きは無視 (throw しない)', S.loadDraft(7, 13, SH), null);
    S.clearDraft(7, 11);
    eq('提出したら消す', [S.loadDraft(7, 11, SH), Object.prototype.hasOwnProperty.call(st._m, 'aj_hw_sheet_v1:7:11')], [null, false]);
    var boom = { getItem: function () { throw new Error('denied'); }, setItem: function () { throw new Error('quota'); }, removeItem: function () { throw new Error('x'); } };
    S._useStorage(boom); S._clearMemory();
    var threw = false;
    try { S.saveDraft(7, 21, SH, [2, 2, 2]); } catch (e) { threw = true; }
    ok('localStorage が throw する端末でも止まらない', !threw);
    eq('… ページ内の下書きで続ける', S.loadDraft(7, 21, SH), [2, 2, 2]);
    S._useStorage(memStore()); S._clearMemory();
    S.saveDraft('', 22, SH, [1, 1, 1]);
    eq('生徒が分からないときは端末に保存しない (ページ内だけ)', S.loadDraft('', 22, SH), [1, 1, 1]);

    var hw = { id: 5, title: '<img src=x onerror=alert(1)>', due_date: '2026-10-20', attachment_print: null };
    var sh = { mode: 'choice', num_questions: 2, num_choices: 4, label_style: 'katakana', labels: ['ア', 'イ', 'ウ', '<b>'] };
    var fh = S.formHtml(hw, sh, [null, 4], {});
    ok('解答用紙の題名・記号は escape', fh.indexOf('&lt;img src=x onerror=alert(1)&gt;') >= 0 && fh.indexOf('<img') < 0 && fh.indexOf('&lt;b&gt;') >= 0 && fh.indexOf('<b>') < 0, fh.slice(0, 400));
    var rh = S.resultHtml(hw, { submitted: true, answers: [1, null], results: [true, false], score_correct: 1, score_total: 2, reveal: false, reveal_on: '2026-10-21',
                                label_style: 'katakana', num_questions: 2, num_choices: 4 }, {});
    ok('結果: 期限前は正解の記号を出さない・「10/21 から」', rh.indexOf('正解:') < 0 && rh.indexOf('正解の記号は 10/21（期限の翌日）から見られます') >= 0, rh);
    ok('結果: 空欄は「（空欄）」で ×', rh.indexOf('あなた: （空欄）') >= 0 && count(rh, 'hs-r hs-ng') === 1 && count(rh, 'hs-r hs-ok') === 1, rh);
    var rh2 = S.resultHtml(hw, { submitted: true, answers: [1, 3], results: [true, false], score_correct: 1, score_total: 2, reveal: true, correct: [1, [2, 4]],
                                 label_style: 'katakana', num_questions: 2, num_choices: 4, late: true, submitted_at: '2026-10-15 23:30:00' }, {});
    ok('結果: 見せてよいときは正解の記号 (どれでも正解は イ/エ)・期限後・JST', rh2.indexOf('正解: ア') >= 0 && rh2.indexOf('正解: イ/エ') >= 0
       && rh2.indexOf('期限後') >= 0 && rh2.indexOf('提出: 2026-10-16 08:30') >= 0, rh2);
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# ---------------------------------------------------------------------------------------------------------------
# [2] 塾生アプリ (class.html)
JS_CLASS_SHEET_SETUP = r"""
var CALLS = [], CONFIRMS = [], CONFIRM_OK = true;
window.confirm = function (m) { CONFIRMS.push(String(m)); return CONFIRM_OK; };
fetch = function (url, opts) {
  var path = String(url).replace(/^https?:\/\/[^\/]+/, '');
  var key = path.split('?')[0];
  CALLS.push({ path: path, method: (opts && opts.method) || 'GET', body: opts && opts.body });
  var r = Object.prototype.hasOwnProperty.call(API, key) ? API[key] : { status: 200, body: {} };
  if (typeof r === 'function') r = r(opts);
  if (r && r.reject) return Promise.reject(new TypeError('Failed to fetch'));
  return Promise.resolve({ ok: r.status >= 200 && r.status < 300, status: r.status,
                           json: function () { return Promise.resolve(JSON.parse(JSON.stringify(r.body))); } });
};
window.fetch = fetch;
function clone(o) { return JSON.parse(JSON.stringify(o)); }
function itemOf(list, id) { return list.items.filter(function (x) { return x.id === id; })[0]; }
function wireBody() {
  var hb = document.getElementById('homeworkBody');
  hb._sheetBtns = [];
  hb.querySelectorAll = function (sel) {
    if (sel !== '.hw-sheet') return [];
    var out = [], re = /class="btn (btn-[a-z]+) hw-sheet" data-id="([^"]*)">([^<]*)</g, m;
    while ((m = re.exec(hb._html))) { var b = new FakeEl(); b.setAttribute('data-id', m[2]); b.btnClass = m[1]; b.textContent = m[3]; out.push(b); }
    hb._sheetBtns = out;
    return out;
  };
  return hb;
}
async function bootSheetPage() {
  ELS = {}; TAB_BTNS = ['schedule', 'homework', 'videos', 'messages'].map(function (t) { var b = new FakeEl(); b.setAttribute('data-tab', t); return b; });
  HIST = []; FETCHES = []; TIMERS = []; CALLS = []; CONFIRMS = [];
  setLoc('/class.html', '?tab=homework', '');
  if (window.AJHwNotice) window.AJHwNotice._clearMemory();
  wireBody();
  __bootClass();
  await flush();
}
function body() { return ELS.homeworkBody; }
function cards() { return String(body().innerHTML).split('<div class="card">').slice(1); }
function cardOf(id) { var c = cards().filter(function (x) { return x.indexOf('data-id="' + id + '"') >= 0; }); return c[0] || ''; }
function cardByTitle(t) { var c = cards().filter(function (x) { return x.indexOf('<div class="card-title">' + t + '</div>') >= 0; }); return c[0] || ''; }
function sheetBtn(id) { return body()._sheetBtns.filter(function (b) { return b.getAttribute('data-id') === String(id); })[0]; }
function target(attrs) {
  var e = new FakeEl();
  for (var k in attrs) e.setAttribute(k, attrs[k]);
  return { el: e, closest: function (sel) { var m = /^\[([a-z-]+)\]$/.exec(sel); return (m && e.getAttribute(m[1]) !== null) ? e : null; } };
}
function clickIn(el, attrs) { var t = target(attrs); el.dispatch('click', { target: t, preventDefault: function () {} }); return t.el; }
function press(q, v, el) { return clickIn(el || body(), { 'data-hs-q': String(q), 'data-hs-v': String(v) }); }
function act(name, el) { return clickIn(el || body(), { 'data-hs-act': name }); }
function row(i, el) { return (el || body())._qs['[data-hs-row="' + i + '"]']; }
function posts() { return CALLS.filter(function (c) { return c.method === 'POST'; }); }
"""

JS_CLASS_SHEET_CASES = r"""
(async function () {
  try {
    __loadHwNotice(); __loadHwSheet();
    var store = memStore(); window.AJHwSheet._useStorage(store); window.AJHwSheet._clearMemory();
    window.AJHwNotice._useStorage(memStore());
    var A = FX.A, B = FX.B, C = FX.C, D = FX.D, E = FX.E;
    var POST_A = '/api/student/homework/' + A + '/sheet';
    // (C1) 一覧: 解答用紙の宿題に ✓完了 を出さない
    setApi({ '/api/student/homework': { status: 200, body: FX.L0 } });
    await bootSheetPage();
    var h = body().innerHTML;
    eq('解答用紙の宿題 4 枚に「✏️ 解答用紙に答える」(問題数つき)', body()._sheetBtns.map(function (b) { return [b.getAttribute('data-id'), b.btnClass, b.textContent]; }).sort(),
       [[String(A), 'btn-primary', '✏️ 解答用紙に答える（全5問）'], [String(B), 'btn-primary', '✏️ 解答用紙に答える（全3問）'],
        [String(C), 'btn-primary', '✏️ 解答用紙に答える（全3問）'], [String(E), 'btn-primary', '✏️ 解答用紙に答える（全2問）']].sort());
    eq('✓完了 は解答用紙なしの宿題 (音読) だけ', count(h, 'hw-done'), 1);
    ok('解答用紙なしの宿題は今までどおり ✓完了', cardOf(D).indexOf('✓ 提出（完了）にする') >= 0, cardOf(D));
    ok('解答用紙の宿題の案内 (提出は 1 回だけ)', cardOf(A).indexOf('解答用紙に答えの記号を入れて提出してね（提出は 1 回だけ）') >= 0 && cardOf(A).indexOf('hw-done') < 0, cardOf(A));
    ok('プリントつきは「プリントを解いたら」・プリントのボタンは控えめ', cardOf(A).indexOf('プリントを解いたら、解答用紙') >= 0 && cardOf(A).indexOf('class="btn btn-ghost hw-print"') >= 0, cardOf(A));
    ok('題名は escape', h.indexOf('関係詞 &lt;b&gt;マーク&lt;/b&gt;') >= 0 && h.indexOf('<b>マーク') < 0);
    eq('バッジ = 未提出 5 (解答用紙の宿題も未提出に数える = hw-notice.js と同じ)', ELS.hwBadge && ELS.hwBadge.textContent, 5);
    ok('解答用紙の宿題にも 🆕 新着 (届いたばかり)', cardOf(A).indexOf('🆕 新着') >= 0);

    // (C2) 開く → 問ごとの記号のボタン
    sheetBtn(A).dispatch('click');
    h = body().innerHTML;
    ok('解答用紙の画面', h.indexOf('data-hs-view="form"') >= 0 && h.indexOf('一覧に戻る') >= 0, h.slice(0, 300));
    eq('5 問 × 4 択 = 20 個のボタン (まだ何も選んでいない)', [count(h, 'data-hs-row='), count(h, 'class="hs-c"'), count(h, 'hs-sel')], [5, 20, 0]);
    ok('記号はアイウエ・押しやすい大きさの CSS', h.indexOf('aria-label="問1 ア">ア</button>') >= 0 && h.indexOf('aria-label="問5 エ">エ</button>') >= 0);
    ok('題名は escape', h.indexOf('✏️ 関係詞 &lt;b&gt;マーク&lt;/b&gt;') >= 0 && h.indexOf('<b>') < 0);
    ok('解答用紙の画面にもプリントのボタン (宿題 ID とプリント ID)', h.indexOf('data-hs-act="print" data-id="' + A + '" data-print-id="' + FX.P1 + '"') >= 0, h);
    ok('「全 5 問 ・ 記号 ア〜エ ・ 提出は 1 回だけ」', h.indexOf('全 5 問 ・ 記号 ア〜エ ・ 提出は 1 回だけ') >= 0);

    // (C3) 押す・もう一度で消す・下書き
    press(0, 3); press(1, 1); press(3, 2); press(4, 4);
    ok('押した記号が選ばれる (問1 ウ)', row(0).innerHTML.indexOf('class="hs-c hs-sel" data-hs-q="0" data-hs-v="3" aria-pressed="true"') >= 0, row(0).innerHTML);
    eq('残りの問題数', body()._qs['[data-hs-progress]'].textContent, 'あと 1 問（全 5 問）');
    var dkey = 'aj_hw_sheet_v1:7:' + A;
    eq('押すたびに端末に下書き', JSON.parse(store._m[dkey]).a, [3, 1, null, 2, 4]);
    press(1, 1);
    eq('同じ記号をもう一度押すと消せる', JSON.parse(store._m[dkey]).a, [3, null, null, 2, 4]);
    press(1, 1); press(9, 1); press(0, 5); press(0, 0);
    eq('範囲外の問・記号は無視', JSON.parse(store._m[dkey]).a, [3, 1, null, 2, 4]);

    // (C4) 一覧に戻って開き直しても答えが残る
    var nList = CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework') === 0 && c.method === 'GET'; }).length;
    act('back'); await flush();
    ok('戻ると一覧を読み直す', CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework') === 0 && c.method === 'GET'; }).length === nList + 1 && body().innerHTML.indexOf('data-hs-view') < 0);
    sheetBtn(A).dispatch('click');
    h = body().innerHTML;
    ok('開き直すと下書きが入っている', h.indexOf('class="hs-c hs-sel" data-hs-q="0" data-hs-v="3"') >= 0 && h.indexOf('class="hs-c hs-sel" data-hs-q="4" data-hs-v="4"') >= 0
       && count(h, 'hs-sel') === 4, h.slice(0, 200));

    // (C5) 空欄があると確認する・やめたら送らない
    CONFIRM_OK = false;
    act('submit'); await flush();
    eq('確認でやめたら送らない', posts().length, 0);
    ok('確認文: 問3 がまだ・空欄 1 問・× になる・1 回だけ', CONFIRMS[0] && CONFIRMS[0].indexOf('問3 がまだです（空欄 1 問）') === 0 && CONFIRMS[0].indexOf('提出は 1 回だけ') >= 0, CONFIRMS);
    ok('空欄の問に印', row(2) && row(2).classList.contains('hs-blank'));
    eq('空欄の案内', body()._qs['[data-hs-msg]'].textContent, '⚠ 問3 がまだです（あと 1 問）');

    // (C6) 提出 → 本物の応答 → 点数と ○×
    CONFIRM_OK = true;
    API[POST_A] = FX.R_A;
    var sb = act('submit');
    eq('送信中はボタンを止める', [sb.disabled, sb.textContent], [true, '⏳ 採点中…']);
    act('submit');
    await flush();
    eq('二度押ししても 1 回だけ送る', posts().map(function (c) { return c.path; }), [POST_A]);
    eq('送る本文はサーバが受け付けた本文と同じ (1 始まり・空欄は null)', posts()[0] && posts()[0].body, JSON.stringify({ answers: FX.ANS_A }));
    h = body().innerHTML;
    ok('結果の画面「提出しました」4 / 5', h.indexOf('data-hs-view="result"') >= 0 && h.indexOf('提出しました<span class="hs-n">4 / 5</span>') >= 0, h.slice(0, 600));
    eq('問ごとの ○× (○4・×1)', [count(h, 'class="hs-r hs-ok"'), count(h, 'class="hs-r hs-ng"')], [4, 1]);
    ok('期限前は正解の記号を出さず「M/D（期限の翌日）から」', h.indexOf('正解:') < 0 && h.indexOf('正解の記号は ' + FX.EXP.reveal_md_A + '（期限の翌日）から見られます') >= 0, h);
    ok('提出時刻は JST', h.indexOf('提出: ' + FX.EXP.submitted_jst_A) >= 0, FX.EXP.submitted_jst_A);
    ok('空欄は「（空欄）」', h.indexOf('あなた: （空欄）') >= 0);
    eq('トースト', ELS.toast && ELS.toast.textContent, '提出しました！ 4 / 5 正解');
    eq('提出できたら下書きを消す', Object.prototype.hasOwnProperty.call(store._m, dkey), false);
    eq('バッジを 1 減らす', ELS.hwBadge.textContent, 4);

    // (C7) 一覧に戻る → 📝 4/5・結果を見る
    API['/api/student/homework'] = { status: 200, body: FX.L1 };
    act('back'); await flush();
    ok('提出済みは完了・📝 4/5・「📝 結果を見る」・✓完了 なし', cardOf(A).indexOf('chip-done">完了') >= 0 && cardOf(A).indexOf('📝 4/5') >= 0
       && cardOf(A).indexOf('📝 結果を見る') >= 0 && cardOf(A).indexOf('hw-done') < 0, cardOf(A));
    ok('期限後の提出には「期限後」', cardOf(B).indexOf('📝 2/3') >= 0 && cardOf(B).indexOf('期限後') >= 0, cardOf(B));
    ok('提出: は JST', cardOf(A).indexOf('提出: ' + FX.EXP.completed_jst_A) >= 0, cardOf(A));
    eq('バッジは読み直した未提出の数 (C・D・E)', ELS.hwBadge.textContent, 3);
    sheetBtn(A).dispatch('click');
    h = body().innerHTML;
    ok('「結果を見る」は結果の画面 (提出の画面は出さない)', h.indexOf('data-hs-view="result"') >= 0 && h.indexOf('採点結果<span class="hs-n">4 / 5</span>') >= 0 && h.indexOf('data-hs-act="submit"') < 0, h.slice(0, 300));

    // (C8) 409: 別の端末で提出済み → 一覧を読み直して結果 (期限の翌日を過ぎていれば正解・期限後)
    setApi({ '/api/student/homework': { status: 200, body: FX.L0 } });
    await bootSheetPage();
    sheetBtn(B).dispatch('click');
    press(0, 3); press(1, 2); press(2, 2);
    API['/api/student/homework/' + B + '/sheet'] = FX.R_B409;
    API['/api/student/homework'] = { status: 200, body: FX.L1 };
    act('submit'); await flush();
    h = body().innerHTML;
    eq('409 はトーストで知らせる', ELS.toast && ELS.toast.textContent, 'この解答用紙はもう提出済みです');
    ok('409 → 提出済みの結果 (2 / 3・期限後・正解の記号 ③①②)', h.indexOf('data-hs-view="result"') >= 0 && h.indexOf('2 / 3') >= 0 && h.indexOf('期限後') >= 0
       && h.indexOf('正解: ③') >= 0 && h.indexOf('正解: ①') >= 0 && h.indexOf('正解: ②') >= 0, h);
    eq('409 の後は下書きを消す', Object.prototype.hasOwnProperty.call(store._m, 'aj_hw_sheet_v1:7:' + B), false);

    // (C9) 422 / 503 / 未デプロイの 404 / 通信失敗: 理由を出し、ボタンを戻し、下書きは残す
    var ERRS = [['422 (サーバの理由)', FX.R_C422, FX.R_C422.body.detail],
                ['503', { status: 503, body: { detail: '解答用紙は準備中です。少し待ってからもう一度提出してください。' } }, '準備中です。少し待ってからもう一度押してね'],
                ['未デプロイ (Not Found)', { status: 404, body: { detail: 'Not Found' } }, '準備中です。少し待ってからもう一度押してね'],
                ['通信失敗', { reject: true }, '通信できませんでした。電波のよいところでもう一度押してね（答えはこの端末に残っています）']];
    for (var i = 0; i < ERRS.length; i++) {
      setApi({ '/api/student/homework': { status: 200, body: FX.L0 } });
      API['/api/student/homework/' + C + '/sheet'] = ERRS[i][1];
      await bootSheetPage();
      sheetBtn(C).dispatch('click');
      if (i === 0) { press(0, 1); press(1, 2); press(2, 1); }
      var b2 = act('submit'); await flush();
      eq(ERRS[i][0] + ': 理由を出す', body()._qs['[data-hs-msg]'].textContent, '❌ 提出できませんでした。' + ERRS[i][2]);
      eq(ERRS[i][0] + ': ボタンを戻す', [b2.disabled, b2.textContent], [false, '📤 提出する（1 回だけ）']);
      eq(ERRS[i][0] + ': 下書きは残る', JSON.parse(store._m['aj_hw_sheet_v1:7:' + C] || '{}').a, [1, 2, 1]);
      ok(ERRS[i][0] + ': 解答用紙の画面のまま', body().innerHTML.indexOf('data-hs-view="form"') >= 0);
    }

    // (C10) answer_sheet_ready が無い (表が無い・旧サーバ) → 今までどおり ✓完了
    var L0nr = clone(FX.L0); delete L0nr.answer_sheet_ready;
    setApi({ '/api/student/homework': { status: 200, body: L0nr } });
    await bootSheetPage();
    eq('answer_sheet_ready が無ければ解答用紙のボタンを出さない・✓完了 は 5 枚', [body()._sheetBtns.length, count(body().innerHTML, 'hw-done')], [0, 5]);

    // (C11) hw-sheet.js が読めない端末 → ✓完了 を出さずに再読み込みの案内
    var keep = window.AJHwSheet; window.AJHwSheet = undefined;
    setApi({ '/api/student/homework': { status: 200, body: FX.L0 } });
    await bootSheetPage();
    window.AJHwSheet = keep;
    ok('hw-sheet.js なし: 解答用紙の宿題に ✓完了 を出さず「開けませんでした」', cardOf(A).indexOf('hw-done') < 0 && cardOf(A).indexOf('解答用紙を開けませんでした。再読み込みしてね') >= 0
       && count(body().innerHTML, 'hw-done') === 1, cardOf(A));

    // (C12) 正解表が無い → 準備中の案内 (✓完了 も答えるボタンも出さない)
    var L0u = clone(FX.L0); itemOf(L0u, E).answer_sheet.available = false;
    setApi({ '/api/student/homework': { status: 200, body: L0u } });
    await bootSheetPage();
    var cE = cardByTitle('8 択 マーク');
    ok('正解表が無い: 「解答用紙を準備中です」(✓完了 も答えるボタンも無し)', cE.indexOf('解答用紙を準備中です。塾長に知らせてね') >= 0 && cE.indexOf('hw-done') < 0
       && !sheetBtn(E), cE);

    // (C13) やり直し (reset_count 1) の後は前の下書きを使わない
    window.AJHwSheet.saveDraft(7, B, { num_questions: 3, num_choices: 4, reset_count: 0 }, [1, 1, 1]);
    setApi({ '/api/student/homework': { status: 200, body: FX.L2 } });
    await bootSheetPage();
    ok('やり直しで開き直した宿題は未提出・答えるボタン', !!sheetBtn(B) && cardOf(B).indexOf('chip-over">期限切れ') >= 0, cardOf(B));
    sheetBtn(B).dispatch('click');
    eq('やり直しの前の下書きは入れない', count(body().innerHTML, 'hs-sel'), 0);

    // (C14) プリントのボタン → 塾生アプリの「プリントを開く」と同じ処理 (POST /print)
    setApi({ '/api/student/homework': { status: 200, body: FX.L0 } });
    API['/api/student/homework/' + A + '/print'] = { status: 200, body: { ok: true, file_path: '/lesson-prints/eng_kankeishi_front_01.pdf' } };
    await bootSheetPage();
    var OPENED = [];
    window.open = function () { var t = { closed: false, location: { href: '' }, document: { write: function () {} }, close: function () { this.closed = true; } }; OPENED.push(t); return t; };
    sheetBtn(A).dispatch('click');
    var pb = clickIn(body(), { 'data-hs-act': 'print', 'data-id': String(A), 'data-print-id': String(FX.P1) });
    await flush();
    eq('解答用紙の画面の「プリントを開く」は POST /api/student/homework/{id}/print', CALLS.filter(function (c) { return c.path.indexOf('/print') >= 0; }).map(function (c) { return c.method + ' ' + c.path; }),
       ['POST /api/student/homework/' + A + '/print']);
    eq('… 先に開いたタブをプリントへ', OPENED[0] && OPENED[0].location.href, 'https://example.invalid/lesson-prints/eng_kankeishi_front_01.pdf');
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# ---------------------------------------------------------------------------------------------------------------
# [3] マイページ (mypage.js の宿題欄)
JS_MYPAGE_SHEET_SETUP = r"""
var location = { search: '', pathname: '/mypage.html', hash: '' }; window.location = location;
window.innerHeight = 800;
var TODO = {};
var AJ_TODO = { set: function (k, v) { TODO[k] = v; } }; window.AJ_TODO = AJ_TODO;
var TIMERS = [];
function setTimeout(fn, ms) { TIMERS.push({ fn: fn, ms: ms }); return TIMERS.length; }
function clearTimeout(id) { if (TIMERS[id - 1]) TIMERS[id - 1].fn = null; }
var CONFIRMS = [], CONFIRM_OK = true, ALERTS = [];
window.confirm = function (m) { CONFIRMS.push(String(m)); return CONFIRM_OK; };
function confirm(m) { return window.confirm(m); }
function alert(m) { ALERTS.push(String(m)); }
function getCurrentStudent() { return { id: 7, name: 'テスト生徒A' }; }   // 架空
function _canUseStudyMgmt() { return true; }
function _gdRich(s) { return String(s == null ? '' : s); }
var API = {}, CALLS = [];
function slApiFetch(path, opts) {
  var key = String(path).split('?')[0];
  CALLS.push({ path: String(path), method: (opts && opts.method) || 'GET', body: opts && opts.body });
  var r = Object.prototype.hasOwnProperty.call(API, key) ? API[key] : { status: 200, body: {} };
  if (r && r.status >= 400) { var e = new Error((r.body && r.body.detail) || ('HTTP ' + r.status)); e.status = r.status; return Promise.reject(e); }
  return Promise.resolve(JSON.parse(JSON.stringify(r.body)));
}
var SECTION, ELS, BODY = new FakeEl('body'), HEAD = new FakeEl('head');
BODY.appendChild = function (c) { this.children.push(c); c.parentNode = this; return c; };
BODY.removeChild = function (c) { this.children = this.children.filter(function (x) { return x !== c; }); c.parentNode = null; return c; };
function newSection() {
  SECTION = new FakeEl('homeworkSection');
  ELS = {};
  ['#homeworkList', '#homeworkBadge', '#homeworkCompletedToggle', '#homeworkShowCompleted', '#homeworkTitleText', '#homeworkIntro'].forEach(function (s) { ELS[s] = new FakeEl(s.slice(1)); });
  SECTION.querySelector = function (sel) { return ELS[sel] || null; };
}
var document = {
  querySelector: function (sel) { return sel === '.homework-section' ? SECTION : null; },
  getElementById: function (id) { return id === 'homeworkSection' ? SECTION : null; },
  createElement: function () { return new FakeEl(); },
  body: BODY, head: HEAD
};
window.document = document;   // hw-sheet.js は root.document を使う (node では var が module の中に閉じるので明示する)
window._gdOpenDrill = function () {};
function list() { return ELS['#homeworkList']; }
function setLists(hw) {
  API['/api/student/grammar-drills'] = { status: 200, body: { ok: true, items: [] } };
  API['/api/student/homework'] = { status: 200, body: hw };
}
function clickList(attr, id) {
  var btn = new FakeEl(); btn.setAttribute(attr, String(id));
  list().dispatch('click', { target: { closest: function (sel) { return sel === '[' + attr + ']' ? btn : null; } } });
}
function target(attrs) {
  var e = new FakeEl();
  for (var k in attrs) e.setAttribute(k, attrs[k]);
  return { el: e, closest: function (sel) { var m = /^\[([a-z-]+)\]$/.exec(sel); return (m && e.getAttribute(m[1]) !== null) ? e : null; } };
}
function clickIn(el, attrs) { var t = target(attrs); el.dispatch('click', { target: t, preventDefault: function () {} }); return t.el; }
function overlay() { return BODY.children.filter(function (c) { return c.className === 'hs-overlay'; })[0]; }
function cardsOf(html) { return String(html).split('<div class="hw-item"').slice(1); }
function cardOf(id) { return cardsOf(list().innerHTML).filter(function (x) { return x.indexOf('data-hw-id="' + id + '"') >= 0; })[0] || ''; }
"""

JS_MYPAGE_SHEET_CASES = r"""
(async function () {
  try {
    __loadHwNotice(); __loadHwSheet();
    var store = memStore(); window.AJHwSheet._useStorage(store); window.AJHwSheet._clearMemory();
    window.AJHwNotice._useStorage(memStore());
    var A = FX.A, B = FX.B, D = FX.D;
    newSection(); setLists(FX.L0);
    await initHomeworkSection(); await flush();
    var h = list().innerHTML;
    ok('解答用紙の宿題は「✏️ 解答用紙に答える（全5問）」・✅ 完了する なし', cardOf(A).indexOf('data-hw-sheet="' + A + '"') >= 0 && cardOf(A).indexOf('✏️ 解答用紙に答える（全5問）') >= 0
       && cardOf(A).indexOf('data-hw-complete') < 0, cardOf(A));
    eq('✅ 完了する は解答用紙なしの宿題だけ', count(h, 'data-hw-complete='), 1);
    ok('解答用紙なしの宿題は今までどおり', cardOf(D).indexOf('data-hw-complete="' + D + '"') >= 0);
    ok('題名は escape', h.indexOf('関係詞 &lt;b&gt;マーク&lt;/b&gt;') >= 0 && h.indexOf('<b>マーク') < 0);

    // 開く → 画面いっぱいの重ね
    clickList('data-hw-sheet', A);
    var ov = overlay();
    ok('重ねを body に足す・下の画面はスクロールさせない', !!ov && BODY.style.overflow === 'hidden');
    var inner = ov && ov.children[0];
    ok('重ねの中に解答用紙 (「× 閉じる」)', inner && inner.innerHTML.indexOf('data-hs-view="form"') >= 0 && inner.innerHTML.indexOf('× 閉じる') >= 0, inner && inner.innerHTML.slice(0, 200));
    FX.ANS_A.forEach(function (v, i) { if (v != null) clickIn(inner, { 'data-hs-q': String(i), 'data-hs-v': String(v) }); });
    API['/api/student/homework/' + A + '/sheet'] = FX.R_A;
    clickIn(inner, { 'data-hs-act': 'submit' }); await flush();
    var p = CALLS.filter(function (c) { return c.method === 'POST'; });
    eq('マイページも同じ本文で 1 回だけ提出', p.map(function (c) { return [c.path, c.body]; }), [['/api/student/homework/' + A + '/sheet', JSON.stringify({ answers: FX.ANS_A })]]);
    ok('重ねの中に結果 (4 / 5)', inner.innerHTML.indexOf('提出しました<span class="hs-n">4 / 5</span>') >= 0, inner.innerHTML.slice(0, 300));
    ok('トーストを出す', BODY.children.some(function (c) { return c.id === 'aj-hw-sheet-toast' && c.textContent === '提出しました！ 4 / 5 正解'; }));

    // 閉じる → 重ねを外して一覧を読み直す
    setLists(FX.L1);
    var nGet = CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework?') === 0; }).length;
    clickIn(inner, { 'data-hs-act': 'back' }); await flush();
    ok('閉じたら重ねを外す・スクロールを戻す', !overlay() && BODY.style.overflow === '');
    eq('提出したので一覧を読み直す', CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework?') === 0; }).length, nGet + 1);
    TIMERS = [];
    var doneBtn = ELS['#homeworkShowCompleted'];
    doneBtn.dispatch('click');
    ok('提出済み: 「✅ 提出 (JST)」と 📝 4/5・「📝 結果を見る」', cardOf(A).indexOf('✅ 提出 (' + FX.EXP.completed_jst_A + ') 📝 4/5') >= 0 && cardOf(A).indexOf('📝 結果を見る') >= 0
       && cardOf(A).indexOf('data-hw-complete') < 0, cardOf(A));
    ok('期限後の提出には「期限後」', cardOf(B).indexOf('期限後') >= 0 && cardOf(B).indexOf('📝 2/3') >= 0, cardOf(B));

    // 結果を見る (提出済み) → 閉じても読み直さない (何も変わっていない)
    clickList('data-hw-sheet', A);
    inner = overlay().children[0];
    ok('提出済みは結果の画面', inner.innerHTML.indexOf('data-hs-view="result"') >= 0 && inner.innerHTML.indexOf('data-hs-act="submit"') < 0);
    nGet = CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework?') === 0; }).length;
    clickIn(inner, { 'data-hs-act': 'back' }); await flush();
    eq('見ただけなら読み直さない', CALLS.filter(function (c) { return c.path.indexOf('/api/student/homework?') === 0; }).length, nGet);

    // answer_sheet_ready が無い → 今までどおり / hw-sheet.js が読めない → ✅ 完了する を出さない
    var L0nr = JSON.parse(JSON.stringify(FX.L0)); delete L0nr.answer_sheet_ready;
    newSection(); setLists(L0nr);
    await initHomeworkSection(); await flush();
    eq('answer_sheet_ready が無ければ今までどおり ✅ 完了する (5 枚)', [count(list().innerHTML, 'data-hw-complete='), count(list().innerHTML, 'data-hw-sheet=')], [5, 0]);
    var keep = window.AJHwSheet; window.AJHwSheet = undefined;
    newSection(); setLists(FX.L0);
    await initHomeworkSection(); await flush();
    window.AJHwSheet = keep;
    ok('hw-sheet.js なし: ✅ 完了する を出さず再読み込みの案内', cardOf(A).indexOf('data-hw-complete') < 0 && cardOf(A).indexOf('ページを再読み込みしてね') >= 0, cardOf(A));
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""

# ---------------------------------------------------------------------------------------------------------------
# [4] CEO の CeoHwSheet
JS_CEO_SETUP = r"""
var TIMERS = [];
function setTimeout(fn, ms) { TIMERS.push({ fn: fn, ms: ms }); return TIMERS.length; }
function clearTimeout(id) { if (TIMERS[id - 1]) TIMERS[id - 1].fn = null; }
async function runTimers() { var t = TIMERS; TIMERS = []; t.forEach(function (x) { if (x.fn) x.fn(); }); await flush(); }
var CONFIRMS = [], CONFIRM_OK = true, ALERTS = [];
window.confirm = function (m) { CONFIRMS.push(String(m)); return CONFIRM_OK; };
window.alert = function (m) { ALERTS.push(String(m)); };
function alert(m) { ALERTS.push(String(m)); }
var REQS = [], PROBE_STATUS = 200, UNEXPECTED = [], DEFER = null, BULK_NEXT = [];
var AdminAuth = {
  getToken: function () { return 't'; },
  fetch: function (url, opts) {
    var method = (opts && opts.method) || 'GET', body = opts && opts.body;
    REQS.push({ url: url, method: method, body: body });
    var r;
    if (url === '/api/admin/homework/answer-keys?limit=1') r = { status: PROBE_STATUS, body: PROBE_STATUS === 200 ? { ok: true, items: [] } : { detail: '記号の解答用紙は準備中です。' } };
    else if (url === '/api/admin/homework/answer-keys/check') r = FX.CHECKS[body] || null;
    else if (url === '/api/admin/homework/answer-keys?print_id=' + FX.P1 + '&limit=5') r = { status: 200, body: FX.KEYS_P1 };
    else if (url === '/api/admin/homework/answer-keys?print_id=' + FX.P2 + '&limit=5') r = { status: 200, body: FX.KEYS_P2 };
    else if (url === '/api/admin/homework/answer-keys/' + FX.KEY_A && method === 'GET') r = { status: 200, body: FX.KEYRES_A };
    else if (url === '/api/admin/homework/answer-keys/' + FX.KEY_A && method === 'PUT') r = FX.PUT_A;
    else if (url === '/api/admin/homework/' + FX.B + '/sheet/reset' && method === 'POST') r = FX.RESET_B;
    else if (url === '/api/admin/homework/assign-bulk' && method === 'POST') r = BULK_NEXT.shift() || null;   // 本物のサーバの応答を順に返す
    if (!r) { UNEXPECTED.push(method + ' ' + url + ' ' + body); r = { status: 599, body: { detail: 'テストに無い呼び出し' } }; }
    var resp = { ok: r.status >= 200 && r.status < 300, status: r.status, json: function () { return Promise.resolve(JSON.parse(JSON.stringify(r.body))); } };
    if (DEFER && url === '/api/admin/homework/answer-keys/check') return new Promise(function (res) { DEFER.push(function () { res(resp); }); });
    return Promise.resolve({ ok: r.status >= 200 && r.status < 300, status: r.status, json: function () { return Promise.resolve(JSON.parse(JSON.stringify(r.body))); } });
  }
};
window.AdminAuth = AdminAuth;
function formRoot() {
  var R = new FakeEl('root');
  R.querySelector('.hws-mode').value = 'none';
  R.querySelector('.hws-nc').value = '4';
  R.querySelector('.hws-style').value = 'circled';
  R.querySelector('.hws-nq').value = '';
  R.querySelector('.hws-key').value = '';
  R.querySelector('.hws-detail').hidden = true;
  R.querySelector('.hws-box').hidden = true;
  return R;
}
function el(R, c) { return R.querySelector(c); }
function setVal(R, c, v, ev) { var e = el(R, c); e.value = v; e.dispatch(ev || 'input'); }
function emit(tag, v) { __out.push('OUT ' + tag + ' ' + JSON.stringify(v)); }
// 📤 一括割当: ceo.html の hwbAssign をそのまま __makeBulk に入れて動かす (画面の要素は偽物・生徒は架空の 1 人・応答は本物のサーバ)
function bulkEnv(ctl, printId) {
  var els = {};
  ['hwbMsg', 'hwbTitle', 'hwbDesc', 'hwbSubject', 'hwbDue', 'hwbPrint'].forEach(function (id) { els[id] = new FakeEl(id); });
  els.hwbPrint.value = printId == null ? '' : String(printId);
  var env = { sheet: ctl, esc: window.CeoHwSheet._h, selected: [], checked: [], els: els };
  env.document = {
    getElementById: function (id) { return els[id] || null; },
    querySelectorAll: function (sel) { return sel === '.hwb-st:checked' ? env.checked : []; }
  };
  env.run = __makeBulk(env);
  env.pick = function () { env.checked = [{ value: String(FX.SID) }]; };   // 配信グループのチップで組を選んだのと同じ
  return env;
}
function bulkBodies() { return REQS.filter(function (r) { return r.url === '/api/admin/homework/assign-bulk'; }).map(function (r) { return JSON.parse(r.body); }); }
function lastBulk() { var b = bulkBodies(); return b[b.length - 1]; }
"""

JS_CEO_CASES = r"""
(async function () {
  try {
    __loadCeo();
    var W = window.CeoHwSheet;
    ok('CeoHwSheet がある', !!W);
    var fh = W.formHtml('X;', 'Y;');
    ok('「✍️ 答え方」は最初は隠す (表があると分かってから出す)', fh.indexOf('<div class="hws-box" hidden') >= 0);
    ok('答え方: 完了ボタンだけ / 記号の解答用紙', fh.indexOf('<option value="none">完了ボタンだけ（今までどおり）</option>') >= 0 && fh.indexOf('<option value="choice">記号の解答用紙') >= 0);
    eq('選択肢の数は 2〜8 (既定 4)', (fh.match(/<option value="(\d)"( selected)?>\d 択<\/option>/g) || []).length, 7);
    ok('既定は 4 択', fh.indexOf('<option value="4" selected>4 択</option>') >= 0);
    ok('記号は ①… / ア… / A… / a… / 正誤', ['circled', 'katakana', 'upper', 'lower', 'seigo'].every(function (s) { return fh.indexOf('<option value="' + s + '">') >= 0; }));

    // (E1) 表がある → 出す
    var R = formRoot();
    var ctl = W.wire(R); await flush();
    eq('表があれば「✍️ 答え方」を出す', el(R, '.hws-box').hidden, false);
    eq('完了ボタンだけ = answer_sheet なし (今までと同じ payload)', ctl.getAnswerSheet(), { ok: true, value: null });

    // (E2) 記号の解答用紙を選ぶ → 確認表
    setVal(R, '.hws-mode', 'choice', 'change');
    eq('記号を選ぶと細かい設定を出す', el(R, '.hws-detail').hidden, false);
    await runTimers();
    ok('問題数が無い → 理由', el(R, '.hws-check').innerHTML.indexOf('❌ 問題数を入れてください') >= 0, el(R, '.hws-check').innerHTML);
    eq('確認が通るまで割当を止める', ctl.getAnswerSheet().ok, false);
    setVal(R, '.hws-nq', '5');
    setVal(R, '.hws-style', 'katakana', 'change');
    setVal(R, '.hws-key', 'ウアエイ');
    eq('打っている間は確認中で止める', [ctl.getAnswerSheet().ok, ctl.getAnswerSheet().error], [false, '正解を確認中です。少し待ってからもう一度押してください']);
    var n0 = REQS.length;
    await runTimers();
    eq('続けて打っても確認は最後の 1 回だけ', REQS.length - n0, 1);
    var c422 = FX.CHECKS[JSON.stringify({ num_questions: 5, num_choices: 4, label_style: 'katakana', key: 'ウアエイ' })].body.detail;
    ok('数が合わない → サーバの理由 (正解が 4 個…)', el(R, '.hws-check').innerHTML.indexOf('❌ ' + c422) >= 0 && c422.indexOf('正解が 4 個') >= 0, el(R, '.hws-check').innerHTML);
    var g = ctl.getAnswerSheet();
    ok('数が合わなければ割当を止める (理由つき)', g.ok === false && g.error.indexOf(c422) >= 0, g);
    setVal(R, '.hws-key', 'ウアエイエ'); await runTimers();
    var ch = el(R, '.hws-check').innerHTML;
    ok('確認表: ✅ 5 問ぶん・問1 ウ … 問5 エ', ch.indexOf('✅ 5 問ぶん読めました（4 択・ア イ ウ…）') >= 0 && ch.indexOf('問1 <b>ウ</b>') >= 0 && ch.indexOf('問5 <b>エ</b>') >= 0, ch);
    g = ctl.getAnswerSheet();
    eq('通ったら answer_sheet (打った文字のまま・サーバが読む)', g.value, { mode: 'choice', key: { num_questions: 5, num_choices: 4, label_style: 'katakana', key: 'ウアエイエ' } });
    eq('確認の文言', g.label, '📝 記号の解答用紙つき（5 問・4 択・ア イ ウ…）');
    emit('SHEET', g.value);
    // 通信中の確認の応答は、打ち直した後に届いても使わない (古い正解を「確認済み」にして割当ててしまわない)
    DEFER = [];
    setVal(R, '.hws-key', 'ウアエイエ'); await runTimers();
    eq('確認が通信中', DEFER.length, 1);
    setVal(R, '.hws-key', 'ウアエイ');
    DEFER[0](); await flush();
    eq('打ち直した後に前の応答が届いても割当は止めたまま', [ctl.getAnswerSheet().ok, ctl.getAnswerSheet().error], [false, '正解を確認中です。少し待ってからもう一度押してください']);
    DEFER = null;
    await runTimers();
    eq('… 打ち直した正解 (4 個) で確認し直して止める', ctl.getAnswerSheet().ok, false);
    setVal(R, '.hws-key', 'ウアエイエ'); await runTimers();
    eq('… 5 個に戻すと通る', ctl.getAnswerSheet().ok, true);

    // (E3) 正誤は 2 択に固定
    setVal(R, '.hws-style', 'seigo', 'change');
    eq('正誤を選ぶと 2 択に固定', [el(R, '.hws-nc').value, el(R, '.hws-nc').disabled], ['2', true]);
    setVal(R, '.hws-style', 'katakana', 'change'); setVal(R, '.hws-nc', '4', 'change');
    eq('正誤から戻すと択数を選べる', el(R, '.hws-nc').disabled, false);
    TIMERS = [];

    // (E4) プリントを選ぶ → 前の正解表。打った正解は勝手に消さない
    await ctl.setPrint(FX.P1); await flush();
    var reuse = el(R, '.hws-reuse');
    ok('打った正解があるときは「入れる」ボタンだけ', reuse.innerHTML.indexOf('このプリントには前の正解表があります') >= 0 && el(R, '.hws-key').value === 'ウアエイエ', reuse.innerHTML);
    reuse.querySelector('.hws-fill').dispatch('click');
    eq('「入れる」→ 前の正解表の問題数・択数・記号・正解', [el(R, '.hws-nq').value, el(R, '.hws-nc').value, el(R, '.hws-style').value, el(R, '.hws-key').value],
       ['5', '4', 'katakana', 'ウ ア エ イ エ']);
    ok('入れたことを知らせる (使った生徒の数)', reuse.innerHTML.indexOf('♻️ このプリントの前の正解表（5 問・4 択・ア イ ウ…・使った生徒 1 人）を入れました') >= 0, reuse.innerHTML);
    await runTimers();
    ok('入れた正解も確認表を通す', el(R, '.hws-check').innerHTML.indexOf('✅ 5 問ぶん読めました') >= 0, el(R, '.hws-check').innerHTML);
    emit('K2T', [{ key: FX.KEYS_P1.items[0].key, style: FX.KEYS_P1.items[0].label_style, nq: 5, nc: 4, text: el(R, '.hws-key').value }]);
    // 空のフォームでプリントを選ぶ → すぐ入れる / 「完了ボタンだけ」のときは案内だけ
    var R2 = formRoot(); var ctl2 = W.wire(R2); await flush();
    await ctl2.setPrint(FX.P1); await flush();
    ok('「完了ボタンだけ」のときは案内だけ (勝手に解答用紙にしない)', el(R2, '.hws-hint').textContent.indexOf('このプリントには前に使った正解表があります') >= 0
       && el(R2, '.hws-key').value === '' && ctl2.getAnswerSheet().value === null, el(R2, '.hws-hint').textContent);
    setVal(R2, '.hws-mode', 'choice', 'change');
    eq('記号の解答用紙にすると前の正解表が入る', el(R2, '.hws-key').value, 'ウ ア エ イ エ');
    await runTimers();
    eq('… そのまま割当てられる', ctl2.getAnswerSheet().ok, true);
    ctl2.reset();
    eq('割当てたら元に戻す', [el(R2, '.hws-mode').value, el(R2, '.hws-detail').hidden, el(R2, '.hws-key').value, el(R2, '.hws-nq').value, ctl2.getAnswerSheet().value],
       ['none', true, '', '', null]);

    // (E4b) プリントを替えたら、前のプリントから自動で入れた正解は消す (2026-10-18 点検: 正解表の無い P2 に替えても P1 の正解が ✅ のまま
    //   付き、サーバはそれを P2 の正解表として保存 → 次から P2 の「前の正解表」として入ってしまう)
    var R4 = formRoot(); var ctl4 = W.wire(R4); await flush();
    setVal(R4, '.hws-mode', 'choice', 'change'); TIMERS = [];
    await ctl4.setPrint(FX.P1); await flush(); await runTimers();
    eq('P1 を選ぶと前の正解表が入って通る', [el(R4, '.hws-key').value, ctl4.getAnswerSheet().ok], ['ウ ア エ イ エ', true]);
    await ctl4.setPrint(FX.P2); await flush();
    eq('正解表の無いプリントに替えると、P1 から入れた問題数・択数・記号・正解を消す',
       [el(R4, '.hws-nq').value, el(R4, '.hws-nc').value, el(R4, '.hws-style').value, el(R4, '.hws-key').value], ['', '4', 'circled', '']);
    ok('… ✅ の確認表と ♻️ の案内も消す', el(R4, '.hws-check').innerHTML.indexOf('✅') < 0 && el(R4, '.hws-reuse').innerHTML === '',
       [el(R4, '.hws-check').innerHTML, el(R4, '.hws-reuse').innerHTML]);
    eq('… P1 の正解では割当てない', ctl4.getAnswerSheet().ok, false);
    await runTimers();
    ok('… 理由は「問題数を入れてください」・答え方は記号のまま', el(R4, '.hws-check').innerHTML.indexOf('❌ 問題数を入れてください') >= 0
       && el(R4, '.hws-mode').value === 'choice' && ctl4.getAnswerSheet().ok === false, el(R4, '.hws-check').innerHTML);
    await ctl4.setPrint(FX.P1); await flush(); await runTimers();
    eq('P1 に戻すとまた入る', [el(R4, '.hws-key').value, ctl4.getAnswerSheet().ok], ['ウ ア エ イ エ', true]);
    await ctl4.setPrint(null); await flush();
    eq('科目を替える (プリントなし) ときも P1 の正解を消して止める', [el(R4, '.hws-key').value, el(R4, '.hws-nq').value, ctl4.getAnswerSheet().ok], ['', '', false]);
    await ctl4.setPrint(FX.P1); await flush(); await runTimers();
    setVal(R4, '.hws-mode', 'none', 'change');
    await ctl4.setPrint(FX.P2); await flush();
    setVal(R4, '.hws-mode', 'choice', 'change');
    eq('「完了ボタンだけ」の間に替えても、記号に戻すと空', [el(R4, '.hws-key').value, el(R4, '.hws-nq').value], ['', '']);
    await runTimers();
    eq('… 割当は止める', ctl4.getAnswerSheet().ok, false);
    // 塾長が打ち直した正解は消さない (打ったもの)。替えたことだけ知らせる
    await ctl4.setPrint(FX.P1); await flush(); await runTimers();
    setVal(R4, '.hws-key', 'ウアエイエ'); await runTimers();
    eq('P1 の正解を打ち直して通る', ctl4.getAnswerSheet().ok, true);
    var WARN = '⚠ プリントを変えました。入っている正解が、いま選んだプリントの正解か確かめてください';
    await ctl4.setPrint(FX.P2); await flush();
    ok('打ち直した正解は消さず、プリントを変えたことを知らせる', el(R4, '.hws-key').value === 'ウアエイエ'
       && el(R4, '.hws-reuse').innerHTML.indexOf(WARN) >= 0, el(R4, '.hws-reuse').innerHTML);
    await ctl4.setPrint(null); await flush();
    await ctl4.setPrint(FX.P2); await flush();
    ok('… 科目を替えてから別のプリントを選んでも知らせたまま', el(R4, '.hws-reuse').innerHTML.indexOf(WARN) >= 0, el(R4, '.hws-reuse').innerHTML);
    setVal(R4, '.hws-key', 'ウアエイエ'); await runTimers();
    await ctl4.setPrint(FX.P2); await flush();
    eq('… このプリントで打ち直したら知らせない', el(R4, '.hws-reuse').innerHTML, '');
    // 打った正解があるときの P1 の「入れる」(押すと P1 の正解が入る) は、P2 に替えたら出さない
    var R5 = formRoot(); var ctl5 = W.wire(R5); await flush();
    setVal(R5, '.hws-mode', 'choice', 'change');
    setVal(R5, '.hws-nq', '5'); setVal(R5, '.hws-style', 'katakana', 'change'); setVal(R5, '.hws-key', 'ウアエイエ'); await runTimers();
    await ctl5.setPrint(FX.P1); await flush();
    ok('打った正解があるときは P1 の「入れる」ボタン', el(R5, '.hws-reuse').innerHTML.indexOf('hws-fill') >= 0, el(R5, '.hws-reuse').innerHTML);
    await ctl5.setPrint(FX.P2); await flush();
    ok('P2 に替えたら P1 の「入れる」を消す (打った正解はそのまま・プリントを選ぶ前に打った正解なので案内も出さない)',
       el(R5, '.hws-reuse').innerHTML === '' && el(R5, '.hws-key').value === 'ウアエイエ', el(R5, '.hws-reuse').innerHTML);
    // reset() (個別で出した後) の後にプリントを選ぶと、正解表は案内だけ
    ctl4.reset(); await ctl4.setPrint(FX.P1); await flush();
    ok('reset() の後: 答え方は元に戻し、プリントの前の正解表は案内だけ', el(R4, '.hws-mode').value === 'none' && el(R4, '.hws-key').value === ''
       && el(R4, '.hws-reuse').innerHTML === '' && el(R4, '.hws-hint').textContent.indexOf('このプリントには前に使った正解表があります') >= 0
       && ctl4.getAnswerSheet().value === null, [el(R4, '.hws-mode').value, el(R4, '.hws-key').value, el(R4, '.hws-hint').textContent]);
    setVal(R4, '.hws-mode', 'choice', 'change');
    eq('… 記号にするとそのプリントの正解表が入る', el(R4, '.hws-key').value, 'ウ ア エ イ エ');
    await ctl4.setPrint(FX.P2); await flush(); await runTimers();
    eq('… 続けて正解表の無いプリントに替えると空で止める', [el(R4, '.hws-key').value, ctl4.getAnswerSheet().ok], ['', false]);
    TIMERS = [];

    // (E4c) 📤 一括割当 (ceo.html の hwbAssign をそのまま・応答は本物のサーバ): 出した後も「✍️ 答え方」を残す (2026-10-18 点検:
    //   reset() で「完了ボタンだけ」に戻すと、題名・プリント・期限は残ったまま、次の組は黙って ✓完了 の宿題になった)
    CONFIRM_OK = true;
    var RB = formRoot(); var cb = W.wire(RB); await flush();
    var BK = bulkEnv(cb, FX.P1);
    BK.els.hwbTitle.value = '関係詞 一括';
    setVal(RB, '.hws-mode', 'choice', 'change'); TIMERS = [];
    await cb.setPrint(String(FX.P1)); await flush(); await runTimers();
    eq('一括: P1 を選ぶと前の正解表が入って通る', [el(RB, '.hws-key').value, cb.getAnswerSheet().ok], ['ウ ア エ イ エ', true]);
    var nB = bulkBodies().length;
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_P1];
    await BK.run(); await flush();
    var b1 = lastBulk();
    eq('組 A: 1 回送る・answer_sheet つき', [bulkBodies().length - nB, !!(b1 && b1.answer_sheet)], [1, true]);
    ok('組 A: 確認に 📝 の 1 行', CONFIRMS.length === 1 && CONFIRMS[0].indexOf('📝 記号の解答用紙つき（5 問・4 択・ア イ ウ…）') >= 0, CONFIRMS);
    ok('組 A: 出せた (✅ 1名・正解表 #A・前の正解表を使い回し)', BK.els.hwbMsg.innerHTML.indexOf('✅ 1名に宿題') >= 0
       && BK.els.hwbMsg.innerHTML.indexOf('正解表 #' + FX.KEY_A + '・前の正解表を使い回し') >= 0, BK.els.hwbMsg.innerHTML);
    eq('組 A の後: 生徒の選択は外す・答え方は記号のまま・正解も確認表も残る',
       [BK.selected, el(RB, '.hws-mode').value, el(RB, '.hws-key').value, cb.getAnswerSheet().ok, cb.getAnswerSheet().value],
       [[false], 'choice', 'ウ ア エ イ エ', true, b1 && b1.answer_sheet]);
    ok('… 「💾 正解表 #A として保存しました」と知らせる', el(RB, '.hws-reuse').innerHTML.indexOf('💾 この正解を正解表 #' + FX.KEY_A + ' として保存しました') >= 0,
       el(RB, '.hws-reuse').innerHTML);
    emit('BULK', b1);
    // 組 B (同じ題名・プリント・期限): そのまま 📤 → 記号の解答用紙が付く
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_P1];
    await BK.run(); await flush();
    var b2 = lastBulk();
    eq('組 B: 同じプリントを続けて出すと、同じ answer_sheet が付く', [bulkBodies().length - nB, b2.answer_sheet, b2.attachment_print_id], [2, b1.answer_sheet, FX.P1]);
    ok('組 B: 確認にも 📝 の 1 行', CONFIRMS.length === 1 && CONFIRMS[0].indexOf('📝 記号の解答用紙つき') >= 0, CONFIRMS);
    emit('BULK', b2);
    // 「完了ボタンだけ」で出すのに、このプリントに正解表がある → 確認に ⚠ の 1 行
    setVal(RB, '.hws-mode', 'none', 'change');
    var gn = cb.getAnswerSheet();
    ok('完了ボタンだけ + 正解表のあるプリント: answer_sheet なし・warn つき', gn.ok === true && gn.value === null && String(gn.warn).indexOf('⚠ 記号の解答用紙なし') === 0, gn);
    ok('… 案内の行も出す', el(RB, '.hws-hint').textContent.indexOf('このプリントには前に使った正解表があります') >= 0, el(RB, '.hws-hint').textContent);
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_PLAIN];
    await BK.run(); await flush();
    var b3 = lastBulk();
    ok('… 確認に ⚠「記号の解答用紙なし（このプリントには正解表があります…）」・📝 は出さない', CONFIRMS.length === 1
       && CONFIRMS[0].indexOf('\n⚠ 記号の解答用紙なし（このプリントには正解表があります') >= 0 && CONFIRMS[0].indexOf('📝') < 0, CONFIRMS);
    eq('… payload は今までと同じ (answer_sheet なし)', Object.keys(b3).sort(), ['attachment_print_id', 'description', 'due_date', 'student_ids', 'subject', 'title']);
    emit('BULK', b3);
    setVal(RB, '.hws-mode', 'choice', 'change');
    eq('記号に戻すと、いま保存した正解表 (A) が入る', el(RB, '.hws-key').value, 'ウ ア エ イ エ');
    ok('… 使った生徒の数は出さない (この画面では分からない)', el(RB, '.hws-reuse').innerHTML.indexOf('♻️ このプリントの前の正解表（5 問・4 択・ア イ ウ…）を入れました') >= 0,
       el(RB, '.hws-reuse').innerHTML);
    await runTimers();
    eq('… そのまま出せる', cb.getAnswerSheet().ok, true);
    // 別のプリント (正解表なし) に替えたら、保存した正解は消える (前のプリントの正解を付けない)
    BK.els.hwbPrint.value = String(FX.P2);
    await cb.setPrint(String(FX.P2)); await flush();
    eq('出した後に P2 へ替えると P1 の正解を消して止める', [el(RB, '.hws-key').value, el(RB, '.hws-nq').value, el(RB, '.hws-reuse').innerHTML, cb.getAnswerSheet().ok],
       ['', '', '', false]);
    TIMERS = [];
    // 打ち直した正解で出した → P1 の正解表になったので、P2 に替えたら消える (⚠ で残さない)
    BK.els.hwbPrint.value = String(FX.P1);
    await cb.setPrint(String(FX.P1)); await flush(); await runTimers();
    setVal(RB, '.hws-key', 'ウアエイエ'); await runTimers();
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_P1];
    await BK.run(); await flush();
    var b4 = lastBulk();
    eq('打ち直した正解で出す → 打った文字のまま送る', b4.answer_sheet && b4.answer_sheet.key.key, 'ウアエイエ');
    emit('BULK', b4);
    eq('… 出した後も残る', [el(RB, '.hws-key').value, cb.getAnswerSheet().ok], ['ウアエイエ', true]);
    BK.els.hwbPrint.value = String(FX.P2);
    await cb.setPrint(String(FX.P2)); await flush();
    eq('… P2 に替えると消える (P1 に保存した正解表なので ⚠ で残さない)', [el(RB, '.hws-key').value, el(RB, '.hws-reuse').innerHTML], ['', '']);
    TIMERS = [];
    // 全員スキップ (保存されない) → 何も変えない = 打った正解でそのまま出し直せる
    BK.els.hwbPrint.value = String(FX.P1);
    await cb.setPrint(String(FX.P1)); await flush(); await runTimers();
    setVal(RB, '.hws-key', 'ウアエイエ'); await runTimers();
    var keyPrintBefore = cb._state.keyPrint;
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_SKIP];
    await BK.run(); await flush();
    ok('全員スキップ: 0 名・⚠ スキップの知らせ', BK.els.hwbMsg.innerHTML.indexOf('✅ 0名に宿題') >= 0 && BK.els.hwbMsg.innerHTML.indexOf('1名スキップ') >= 0, BK.els.hwbMsg.innerHTML);
    eq('… 答え方・打った正解・確認表はそのまま (💾 にしない)',
       [el(RB, '.hws-mode').value, el(RB, '.hws-key').value, cb.getAnswerSheet().ok, el(RB, '.hws-reuse').innerHTML.indexOf('💾') < 0, cb._state.keyPrint === keyPrintBefore && keyPrintBefore != null],
       ['choice', 'ウアエイエ', true, true, true]);
    CONFIRMS = []; BK.pick(); BULK_NEXT = [FX.BULK_P1];
    await BK.run(); await flush();
    eq('… 選び直して出し直すと answer_sheet が付く', lastBulk().answer_sheet && lastBulk().answer_sheet.key.key, 'ウアエイエ');
    // 送った後に打ち直した / プリントが違う → 保存した表として扱わない (いま入っているのは保存したものではない)
    var sentNow = cb.getAnswerSheet().value;
    eq('markSaved: 送った正解と違えば何もしない', cb.markSaved(FX.BULK_P1.body.answer_sheet,
       { mode: 'choice', key: { num_questions: 5, num_choices: 4, label_style: 'katakana', key: 'アアアアア' } }), false);
    eq('markSaved: 保存したプリントが違えば何もしない', cb.markSaved({ key_id: FX.KEY_A, print_id: FX.P2 }, sentNow), false);
    eq('markSaved: 同じなら保存した表にする', cb.markSaved(FX.BULK_P1.body.answer_sheet, sentNow), true);
    TIMERS = [];
    // プリントなしで出す → 次の組にも付く・プリントを選んだら消える
    var RN = formRoot(); var cn = W.wire(RN); await flush();
    var BN = bulkEnv(cn, null);
    BN.els.hwbTitle.value = 'プリントなし 一括';
    setVal(RN, '.hws-mode', 'choice', 'change');
    setVal(RN, '.hws-nq', '5'); setVal(RN, '.hws-style', 'katakana', 'change'); setVal(RN, '.hws-key', 'ウアエイエ'); await runTimers();
    CONFIRMS = []; BN.pick(); BULK_NEXT = [FX.BULK_NOPRINT];
    await BN.run(); await flush();
    var bn1 = lastBulk();
    ok('プリントなし: 「💾 … 次の組にも同じ宿題を出すなら」', el(RN, '.hws-reuse').innerHTML.indexOf('💾 この正解を正解表 #' + FX.BULK_NOPRINT.body.answer_sheet.key_id
       + ' として保存しました。次の組にも同じ宿題を') >= 0, el(RN, '.hws-reuse').innerHTML);
    emit('BULK', bn1);
    CONFIRMS = []; BN.pick(); BULK_NEXT = [FX.BULK_NOPRINT];
    await BN.run(); await flush();
    eq('… 続けて出しても answer_sheet が付く', [lastBulk().answer_sheet, lastBulk().attachment_print_id], [bn1.answer_sheet, null]);
    BN.els.hwbPrint.value = String(FX.P2);
    await cn.setPrint(String(FX.P2)); await flush();
    eq('… プリント (正解表なし) を選んだら消して止める', [el(RN, '.hws-key').value, cn.getAnswerSheet().ok], ['', false]);
    eq('📤 一括: 応答は全部使った', BULK_NEXT.length, 0);
    TIMERS = [];

    // (E5) 正解表 → 入力欄の文字 (サーバで読み戻す)
    var K = [[[3, 1, 4, 2], 'katakana', 4, 4], [[3, [1, 4], 0, 2], 'circled', 4, 4], [[1, 2, 1], 'seigo', 3, 2], [[8, 1, [2, 3]], 'upper', 3, 8], [[5, 1], 'lower', 2, 6]];
    emit('K2T', K.map(function (x) { return { key: x[0], style: x[1], nq: x[2], nc: x[3], text: W.keyToText(x[0], x[1]) }; }));
    eq('入力欄の文字の形', W.keyToText([3, [1, 4], 0, 2], 'circled'), '③ [①④] * ②');

    // (E6) 宿題履歴
    var items = FX.ADMIN_LIST.items, byId = {};
    items.forEach(function (it) { byId[it.id] = it; });
    var fmt = function (s) { return 'JST(' + s + ')'; };
    var hA = W.historyHtml(byId[FX.A], fmt), hB = W.historyHtml(byId[FX.B], fmt), hC = W.historyHtml(byId[FX.C], fmt), hD = W.historyHtml(byId[FX.D], fmt);
    ok('提出済み: 📝 4/5・提出時刻 (JST の関数を通す)', hA.indexOf('📝 4/5') >= 0 && hA.indexOf('提出 JST(' + byId[FX.A].answer_sheet.submitted_at + ')') >= 0, hA);
    ok('提出済み: 📊 問ごとの結果・✏️ 正解を直す・↩️ やり直し', hA.indexOf('data-hws-act="stats"') >= 0 && hA.indexOf('data-hws-act="edit"') >= 0 && hA.indexOf('data-hws-act="reset"') >= 0);
    ok('期限後の提出は「期限後」', hB.indexOf('期限後') >= 0 && hB.indexOf('📝 2/3') >= 0, hB);
    ok('未提出は「未提出」・やり直しは出さない', hC.indexOf('未提出') >= 0 && hC.indexOf('data-hws-act="reset"') < 0 && hC.indexOf('3 問・2 択・正 誤') >= 0, hC);
    eq('解答用紙なしの宿題には何も足さない', hD, '');
    eq('実施状況のチップの点数', [W.overviewScore({ sheet: { submitted: true, score_correct: 4, score_total: 5, late: true } }).indexOf('✍️4/5 期限後') >= 0,
                                W.overviewScore({ sheet: { submitted: false, score_correct: null, score_total: 5 } }), W.overviewScore({ sheet: null })], [true, '', '']);

    // (E7) 📊 問ごとの結果 / ✏️ 正解を直す / ↩️ やり直し (委任)
    var HB = new FakeEl('hist'), panes = {};
    [FX.A, FX.B].forEach(function (id) { var p = new FakeEl(); p.setAttribute('data-hw-id', String(id)); p.hidden = true; panes[id] = p; });
    HB.querySelectorAll = function (sel) { return sel === '.hws-pane' ? [panes[FX.A], panes[FX.B]] : []; };
    HB.contains = function () { return true; };
    var changed = 0;
    W.wireHistory(HB, items, { studentName: FX.NAME, onChanged: function () { changed++; return Promise.resolve(); } });
    function clickHist(actName, id, keyId) {
      var b = new FakeEl(); b.setAttribute('data-hws-act', actName); b.setAttribute('data-hw-id', String(id)); if (keyId != null) b.setAttribute('data-key-id', String(keyId));
      HB.dispatch('click', { target: { closest: function (sel) { return sel === '[data-hws-act]' ? b : null; } } });
      return b;
    }
    clickHist('stats', FX.A, FX.KEY_A); await flush();
    var ps = panes[FX.A].innerHTML;
    var pq = FX.KEYRES_A.stats.per_question;
    ok('📊 問ごとの正解率 (全員の集計)', !panes[FX.A].hidden && pq.every(function (q) { return ps.indexOf('問' + q.no + '</td>') >= 0 && ps.indexOf((q.correct_rate == null ? '—' : q.correct_rate + '%')) >= 0; }), ps.slice(0, 400));
    ok('📊 この生徒の答えと ○×・選ばれた記号の数', ps.indexOf('（空欄）') >= 0 && ps.indexOf('ア 1') >= 0 && ps.indexOf('○</span>') >= 0, ps);
    ok('📊 生徒名は escape', ps.indexOf(FX.NAME.replace('<', '&lt;').replace('>', '&gt;')) >= 0 && ps.indexOf(FX.NAME) < 0, ps);
    clickHist('stats', FX.A, FX.KEY_A); await flush();
    eq('もう一度押すと閉じる', panes[FX.A].hidden, true);
    // ✏️ 正解を直す
    clickHist('edit', FX.A, FX.KEY_A); await flush();
    var ep = panes[FX.A];
    eq('✏️ 今の正解と記号を入力欄に (ウ ア エ イ エ)', [ep.querySelector('.hws-e-key').value, ep.querySelector('.hws-e-style').value], ['ウ ア エ イ エ', 'katakana']);
    await flush();
    ok('✏️ 開いたらすぐ確認表', ep.querySelector('.hws-e-check').innerHTML.indexOf('✅ 5 問ぶん読めました') >= 0, ep.querySelector('.hws-e-check').innerHTML);
    ok('✏️ の画面: 提出済みの人数と「まとめて採点し直します」', ep.innerHTML.indexOf('まとめて採点し直します') >= 0 && ep.innerHTML.indexOf('ウ ア エ イ エ</textarea>') >= 0, ep.innerHTML.slice(0, 500));
    ep.querySelector('.hws-e-key').value = 'ウ ア エ イ エ';
    ep.querySelector('.hws-e-style').value = 'katakana';
    ep.querySelector('.hws-e-key').dispatch('input'); await runTimers();
    ok('✏️ 確認表を通す', ep.querySelector('.hws-e-check').innerHTML.indexOf('✅ 5 問ぶん読めました') >= 0, ep.querySelector('.hws-e-check').innerHTML);
    CONFIRMS = []; CONFIRM_OK = false;
    ep.querySelector('.hws-e-save').dispatch('click'); await flush();
    ok('保存の前に確認 (提出済み N 人を採点し直す)', CONFIRMS[0] && CONFIRMS[0].indexOf('提出済みの生徒 ' + FX.KEYRES_A.stats.submitted + ' 人を、まとめて採点し直します') >= 0, CONFIRMS);
    eq('確認でやめたら送らない', REQS.filter(function (r) { return r.method === 'PUT'; }).length, 0);
    CONFIRM_OK = true;
    ep.querySelector('.hws-e-save').dispatch('click'); await flush();
    var put = REQS.filter(function (r) { return r.method === 'PUT'; });
    eq('PUT /api/admin/homework/answer-keys/{key_id} {key, label_style}', put.map(function (r) { return [r.url, JSON.parse(r.body)]; }),
       [['/api/admin/homework/answer-keys/' + FX.KEY_A, FX.PUT_BODY]]);
    ok('サーバの文言 (採点し直した人数) を出す', ep.querySelector('.hws-e-msg').innerHTML.indexOf(FX.PUT_A.body.message) >= 0, ep.querySelector('.hws-e-msg').innerHTML);
    await runTimers();
    eq('直したら履歴を読み直す', changed, 1);
    // ↩️ やり直し
    CONFIRMS = [];
    clickHist('reset', FX.B); await flush();
    ok('やり直しの確認 (生徒名・題名・もう一度提出できる)', CONFIRMS[0] && CONFIRMS[0].indexOf(FX.NAME + ' さんの解答用紙「時制 マーク (期限切れ)」を提出前に戻します') === 0
       && CONFIRMS[0].indexOf('もう一度提出できる') >= 0, CONFIRMS);
    eq('POST /api/admin/homework/{id}/sheet/reset', REQS.filter(function (r) { return r.url.indexOf('/sheet/reset') >= 0; }).map(function (r) { return r.method + ' ' + r.url; }),
       ['POST /api/admin/homework/' + FX.B + '/sheet/reset']);
    eq('やり直したら履歴を読み直す', changed, 2);
    eq('テストに無い呼び出しをしていない', UNEXPECTED, []);

    // (E8) 表が無い (503) → 「✍️ 答え方」を出さない
    PROBE_STATUS = 503;
    __loadCeo();
    var R3 = formRoot(); var ctl3 = window.CeoHwSheet.wire(R3); await flush();
    setVal(R3, '.hws-mode', 'choice', 'change');
    eq('表が無ければ隠したまま・answer_sheet は付けない', [el(R3, '.hws-box').hidden, ctl3.getAnswerSheet().value], [true, null]);
  } catch (e) {
    ok('例外なし', false, String((e && e.stack) || e));
  }
  __emit();
})();
"""


def run_js(engine, program, label, env_extra=None):
    """OK / NG / DONE / OUT の行を読む (OUT = サーバに戻して確かめる値)。"""
    outs = []
    with tempfile.TemporaryDirectory(prefix="hw_sheet_front_") as td:
        path = os.path.join(td, "case.js")
        with open(path, "w", encoding="utf-8") as f:
            f.write(program)
        env = dict(os.environ)
        env.update(env_extra or {})
        try:
            r = subprocess.run(engine + [path], capture_output=True, text=True, timeout=240, env=env)
        except Exception as e:  # noqa: BLE001
            check(f"{label}: JS を実行できた", False, f"{type(e).__name__}: {e}")
            return outs
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    lines = [l for l in text.split("\n") if l.startswith(("OK  ", "NG  ", "DONE ", "OUT "))]
    done = [l for l in lines if l.startswith("DONE ")]
    if r.returncode != 0 or not done:
        check(f"{label}: JS が最後まで走った (exit {r.returncode})", False, text[-1500:])
        return outs
    for l in lines:
        if l.startswith("OK  "):
            check(l[4:], True)
        elif l.startswith("NG  "):
            check(l[4:], False, l[4:])
        elif l.startswith("OUT "):
            tag, _, js = l[4:].partition(" ")
            outs.append((tag, json.loads(js)))
    n = int(done[-1].split()[1]) - len(outs)
    check(f"{label}: {n} 件の検査を実行", n > 0)
    return outs


def ceo_block(ceo_html):
    blocks = [b for b in H.inline_scripts(ceo_html) if "window.CeoHwSheet = (function" in b]
    return blocks[0] if len(blocks) == 1 else None


def bulk_assign_src(ceo_html):
    """ceo.html の 📤 一括割当 hwbAssign() の本文 (そのまま JS のテストで動かす)。見つからなければ None。"""
    i = ceo_html.find("    async function hwbAssign() {")
    if i < 0:
        return None
    j = ceo_html.find("\n    }\n", i)
    return ceo_html[i:j + len("\n    }\n")] if j > i else None


def bulk_maker(src):
    # hwbAssign が使う document / _hwbSheet / escapeHtml / hwbSelectAll は、このテストの偽物に差し替える (閉包で見える名前)
    body = src or "async function hwbAssign() { throw new Error('ceo.html に hwbAssign が無い'); }"
    return ("function __makeBulk(env) {\n  var document = env.document, _hwbSheet = env.sheet, escapeHtml = env.esc;\n"
            "  function hwbSelectAll(v) { env.selected.push(v); env.checked = []; }\n" + body + "\n  return hwbAssign;\n}\n")


def main():
    mod, client, admin, fx = build_fixtures()
    class_html, mypage_html, mypage_js, ceo_html = read(CLASS_HTML), read(MYPAGE_HTML), read(MYPAGE_JS), read(CEO_HTML)
    sheet_src, notice_src = read(HW_SHEET_JS), read(HW_NOTICE_JS)
    class_inline = H.inline_scripts(class_html)
    blk = ceo_block(ceo_html)
    bulk = bulk_assign_src(ceo_html)
    eng = H.js_engine()
    print(f"\nJS エンジン: {eng[0] if eng else 'なし'}")
    check("JS の実行環境がある (node / osascript / jsc。無ければ FAIL)", bool(eng), "node も osascript も jsc も見つからない (AJ_JS_ENGINE の指定も確認)")
    check("class.html の inline script は 1 つ", len(class_inline) == 1, len(class_inline))
    check("ceo.html に CeoHwSheet の inline script がちょうど 1 つ", blk is not None)
    check("ceo.html に 📤 一括割当の hwbAssign() がある (JS のテストでそのまま動かす)", bulk is not None)
    loaders = ("function __loadHwSheet() {\n" + sheet_src + "\n}\n" + "function __loadHwNotice() {\n" + notice_src + "\n}\n"
               + "var FX = " + json.dumps(fx, ensure_ascii=True) + ";\n")
    tz = {"TZ": "America/Los_Angeles"}   # 端末のタイムゾーンが JST でなくても JST で出す
    outs = []
    if eng:
        print("\n[1] hw-sheet.js の部品")
        run_js(eng, H.PRELUDE + H.FAKE_DOM + loaders + JS_PURE, "[1]", tz)
        if len(class_inline) == 1:
            print("\n[2] 塾生アプリ (class.html の inline script・本物のサーバの応答・TZ=America/Los_Angeles)")
            boot = "function __bootClass() {\n" + class_inline[0] + "\n}\n"
            run_js(eng, H.PRELUDE + H.POLYFILL + H.FAKE_DOM + loaders + H.JS_CLASS_SETUP + JS_CLASS_SHEET_SETUP + boot + JS_CLASS_SHEET_CASES, "[2]", tz)
        print("\n[3] マイページ (mypage.js の宿題欄)")
        try:
            sl = H.mypage_homework_slice(mypage_js)
        except ValueError:
            sl = None
            check("mypage.js の宿題欄の範囲が見つかる", False)
        if sl:
            run_js(eng, H.PRELUDE + H.POLYFILL + H.FAKE_DOM + loaders + JS_MYPAGE_SHEET_SETUP + sl + "\n" + JS_MYPAGE_SHEET_CASES, "[3]", tz)
        if blk:
            print("\n[4] CEO の CeoHwSheet (本物のサーバの応答)")
            prog = (H.PRELUDE + H.POLYFILL + H.FAKE_DOM + loaders + JS_CEO_SETUP + bulk_maker(bulk)
                    + "function __loadCeo() {\n" + blk + "\n}\n" + JS_CEO_CASES)
            outs = run_js(eng, prog, "[4]", tz)

    print("\n[5] 画面が作った値をサーバに戻して確かめる")
    sheets = [v for t, v in outs if t == "SHEET"]
    k2t = [x for t, v in outs if t == "K2T" for x in v]
    check("CEO の「✍️ 答え方」が作った answer_sheet を受け取った", len(sheets) == 1, outs[:3])
    if sheets:
        r = client.post("/api/admin/homework/assign", headers=admin, json={"student_id": fx["SID"], "title": "CEO の答え方から", "answer_sheet": sheets[0]})
        a = (r.json() or {}).get("answer_sheet") or {}
        check("その answer_sheet で個別割当 → 200・5 問・4 択・katakana", r.status_code == 200 and a.get("num_questions") == 5 and a.get("num_choices") == 4
              and a.get("label_style") == "katakana", r.text[:300])
        r = client.post("/api/admin/homework/assign-bulk", headers=admin, json={"student_ids": [fx["SID"]], "title": "CEO の答え方から (一括)", "answer_sheet": sheets[0]})
        check("その answer_sheet で 📤 一括割当 → 200・1 名", r.status_code == 200 and r.json().get("assigned_count") == 1 and r.json().get("answer_sheet"), r.text[:300])
    # 📤 一括割当 (hwbAssign) が送った本文を本物のサーバに送り直す: 解答用紙つきは 200・P1 なら正解表 A の使い回し・なしは今までどおり
    bulks = [v for t, v in outs if t == "BULK"]
    check("📤 一括割当 (hwbAssign) が送った本文を 5 つ受け取った (組 A・組 B・完了ボタンだけ・打ち直し・プリントなし)", len(bulks) == 5, len(bulks))
    for i, b in enumerate(bulks):
        r = client.post("/api/admin/homework/assign-bulk", headers=admin, json=b)
        d = r.json() if r.status_code == 200 else {}
        a = d.get("answer_sheet") or {}
        if "answer_sheet" not in b:
            ok_b = r.status_code == 200 and d.get("assigned_count") == 1 and "answer_sheet" not in d
        elif b.get("attachment_print_id") == fx["P1"]:
            ok_b = r.status_code == 200 and d.get("assigned_count") == 1 and a.get("key_id") == fx["KEY_A"] and a.get("reused_key") is True
        else:
            ok_b = r.status_code == 200 and d.get("assigned_count") == 1 and a.get("key_id") and a.get("print_id") is None
        check(f"📤 一括の本文 {i + 1} (answer_sheet {'あり' if 'answer_sheet' in b else 'なし'}) をサーバに送り直す → 200", ok_b, r.text[:300])
    check("正解表 → 入力欄の文字を 6 つ以上受け取った", len(k2t) >= 6, len(k2t))
    for x in k2t:
        try:
            got = mod._hw_validate_key(x["text"], x["nq"], x["nc"], x["style"])
        except ValueError as e:
            got = f"ValueError: {e}"
        check(f"入力欄の文字「{x['text']}」({x['style']}) はサーバで同じ正解に読める", got == x["key"], (got, x["key"]))

    print("\n[6] ソース検査")
    script = class_inline[0] if class_inline else ""
    m_cls = re.search(r'<script src="hw-sheet\.js\?v=([^"]+)"></script>', class_html)
    m_my = re.search(r'<script src="hw-sheet\.js\?v=([^"]+)"></script>', mypage_html)
    check("class.html と mypage.html が hw-sheet.js?v= を読む・?v= がそろう", bool(m_cls and m_my and m_cls.group(1) == m_my.group(1)),
          (m_cls and m_cls.group(1), m_my and m_my.group(1)))
    i_n, i_s, i_in = class_html.find('src="hw-notice.js'), class_html.find('src="hw-sheet.js'), class_html.find("<script>", class_html.find('src="hw-sheet.js'))
    check("class.html: hw-notice.js → hw-sheet.js → inline script の順", 0 <= i_n < i_s < i_in, (i_n, i_s, i_in))
    check("mypage.html: hw-sheet.js を mypage.js より前に読む", 0 <= mypage_html.find('src="hw-sheet.js') < mypage_html.find('src="mypage.js?v='))
    code = re.sub(r"(^|\s)//.*$", r"\1", re.sub(r"/\*.*?\*/", "", sheet_src, flags=re.S), flags=re.M)
    es6 = [p for p in (r"=>", r"\blet\s", r"\bconst\s", r"`", r"\bclass\s", r"\.\.\.") if re.search(p, code)]
    check("hw-sheet.js は ES5 (=> / let / const / ` / class / ... を使わない)", not es6, es6)
    check("hw-sheet.js は提出に POST /api/student/homework/{id}/sheet だけ (旧 download・AI のルートを呼ばない)",
          "'/api/student/homework/' + encodeURIComponent(String(hwId)) + '/sheet'" in sheet_src and "/api/student/lesson-prints" not in sheet_src
          and not re.search(r"/api/(ai|chat|tutor|grade|vision)", sheet_src))
    check("hw-sheet.js の下書きのキーは aj_hw_sheet_v1:", "var DRAFT_PREFIX = 'aj_hw_sheet_v1:';" in sheet_src)
    check("class.html: 解答用紙の宿題は ✓完了 の分岐より先 (if (sheetSt !== 'none') … else if (!done))",
          "if (sheetSt !== 'none') {" in script and script.find("if (sheetSt !== 'none') {") < script.find("} else if (!done) {"))
    check("class.html: 解答用紙は answer_sheet_ready === true のときだけ", "hwSheetReady = !!(d && d.answer_sheet_ready === true);" in script)
    check("mypage.js: ✅ 完了する は解答用紙なしのときだけ・ready は一覧から", "let completeBtn = (isOpen && sheetSt === 'none')" in mypage_js
          and "_hwSheetReady = !!(data && data.answer_sheet_ready === true);" in mypage_js)
    my_code = re.sub(r"(^|\s)//.*$", r"\1", re.sub(r"/\*.*?\*/", "", mypage_js, flags=re.S), flags=re.M)
    check("mypage.js の AJHwSheet は _hwSheetLib() 経由だけ", len(re.findall(r"window\.AJHwSheet", my_code)) == 2
          and not re.findall(r"(?<!window\.)\bAJHwSheet\b", my_code))
    check("CEO: 個別と 📤 一括の payload は解答用紙のときだけ answer_sheet を足す (無ければ今までと同じ)",
          ceo_html.count("if (sheet.value) body.answer_sheet = sheet.value;") == 2)
    check("CEO: 確認表が通っていなければ割当を止める (個別・一括)", ceo_html.count("getAnswerSheet() : { ok: true, value: null };") == 2
          and "if (!sheet.ok) { formMsg.style.color = '#fca5a5'; formMsg.textContent = '❌ ' + sheet.error; return; }" in ceo_html)
    check("CEO: プリントを選んだら前の正解表を探す (個別・一括)", "sheetCtl.setPrint(printSel.value || null)" in ceo_html and "_hwbSheet.setPrint(pp.value || null)" in ceo_html)
    i_bulk = ceo_html.find("async function hwbAssign() {")
    bulk_src = ceo_html[i_bulk:ceo_html.find("\n    }\n", i_bulk)] if i_bulk >= 0 else ""
    bulk_saved = "if (_hwbSheet && sheet.value && data.answer_sheet) _hwbSheet.markSaved(data.answer_sheet, sheet.value);"
    check("CEO: 📤 一括割当は出せたら「✍️ 答え方」を戻さず markSaved (同じプリントの次の組にも付く・別のプリントに替えたら消える)・reset() は呼ばない",
          bulk_saved in bulk_src and bulk_src.find("hwbSelectAll(false);") < bulk_src.find(bulk_saved)
          and bulk_src.find("if (!res.ok) {") < bulk_src.find(bulk_saved) and "_hwbSheet.reset()" not in bulk_src, len(bulk_src))
    check("CEO: 📤 一括の確認は 📝 の 1 行 / 解答用紙なしでプリントに正解表があれば ⚠ の 1 行 (sheet.warn)",
          "const sheetLine = sheet.value ? '\\n' + sheet.label : (sheet.warn ? '\\n' + sheet.warn : '');" in bulk_src
          and "${sheetLine}\\nよろしいですか？" in bulk_src)
    check("CEO: 個別は出せたら sheetCtl.reset() (前の正解を残さない)", "if (sheetCtl) sheetCtl.reset();" in ceo_html)
    check("CEO: 宿題履歴に結果・📊・✏️・↩️ (CeoHwSheet.historyHtml / wireHistory)", "CeoHwSheet.historyHtml(it, fmtDate)" in ceo_html
          and "CeoHwSheet.wireHistory(histBox, items, { studentName, onChanged: refreshList });" in ceo_html)
    check("CEO: 添付プリントの案内は「生徒のアプリで」(マイページだけではない)", ceo_html.count("生徒のアプリでPDFを開けます") == 2 and "生徒のマイページでPDF" not in ceo_html)
    check("CEO: 正解の読み方はサーバの 1 か所 (確認表は POST …/answer-keys/check)", "const CHECK_URL = '/api/admin/homework/answer-keys/check';" in (blk or ""))
    ci = read(CI_YML)
    check("CI (server-tests.yml) にこのテストの step がある", "python3 scripts/health_check/test_homework_sheet_front.py" in ci)
    paths_block = ci.split("pull_request:")[0]
    for p in ("'hw-sheet.js'", "'class.html'", "'mypage.js'", "'mypage.html'", "'ceo.html'"):
        check(f"CI の paths に {p} (画面だけの push でも走らせる)", p in paths_block)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES[:20]))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
