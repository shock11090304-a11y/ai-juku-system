#!/usr/bin/env python3
"""🎬 アーカイブ専用クラス (server/main.py の _ARCHIVE_CLASSES・2026-11-17 塾長指示) の回帰テスト。

背景: ライブ授業の無い 3 クラス (「アーカイブ 関関同立」「アーカイブ 旧帝大・神戸大」「アーカイブ 人気国公立」「アーカイブ 日東駒専・産近甲龍」) に
  毎週 2 本の講義動画 (YouTube 限定公開) を配る。曜日・時限が無いので _TIMETABLE_CLASSES には入れず、
  label の照合 (_TIMETABLE_LABELS) にだけ入れる。

固定する性質:
  1. 照合の表: _TIMETABLE_LABELS に 3 クラス・_TIMETABLE_CLASSES (曜日+時限のコマ) には無い・自動宿題の表は hold。
  2. 登録フォームの subjects: 「日東駒専・産近甲龍」の「・」で割らない (_split_class_subjects・承認で class_labels に入る)。
  3. CEO: timetable-classes に archive=true で出る・受講クラスの保存 / クラス別一括登録 / クラス別配布ファイル / クラス宿題が受け付ける。
  4. 出欠: アーカイブ専用クラスの出欠は生徒も塾長も 400 (授業の出欠申告も 400)。
  5. feed: label と同じ題名の授業に紐づけた録画は、そのクラスの受講生にだけ・受講開始月以降の分だけ出る。
     受講していない生徒には授業ごと出ない。授業には archive=true が付く。
  6. 録画の自動割り当て (class_recording_assign.build_plan) はアーカイブ専用クラスの授業を見ない
     (見ると「再生リストが無い授業」で blocking が立ち、全クラスの割り当てが止まる)。

実行:
    python3 scripts/health_check/test_archive_classes.py      # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
KKDR = "アーカイブ 関関同立"
KOKU = "アーカイブ 旧帝大・神戸大"
NINKI = "アーカイブ 人気国公立"
NTKS = "アーカイブ 日東駒専・産近甲龍"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="archivecls_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_archivecls", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def student_token(mod, sid, hours=1):
    exp = int(time.time()) + hours * 3600
    payload = f"session.{sid}.{exp}"
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}.{sig}".encode()).decode().rstrip("=")


def make_student(mod, name, email, labels, start_month=None):
    conn = mod.db()
    c = conn.cursor()
    far = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)).isoformat()
    c.execute(
        "INSERT INTO students (name, email, status, trial_end, course, grade, goal, ai_disabled, class_labels, start_month) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
        (name, email, "trial", far, "kokuritsu_nankan", "高校3年", "大学受験", json.dumps(labels, ensure_ascii=False), start_month),
    )
    conn.commit()
    c.execute("SELECT id FROM students WHERE LOWER(email) = ?", (email.lower(),))
    sid = c.fetchone()["id"]
    conn.close()
    mod._AI_DISABLED_CACHE.pop(sid, None)
    return sid


def main():
    print("🎬 アーカイブ専用クラス 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    adm = {"Authorization": "Bearer " + admin_token(mod)}

    print("[1] 照合の表")
    arch = {KKDR, KOKU, NINKI, NTKS}
    check("_ARCHIVE_CLASS_LABELS = 3 クラス", mod._ARCHIVE_CLASS_LABELS == arch, sorted(mod._ARCHIVE_CLASS_LABELS))
    check("_TIMETABLE_LABELS に入っている", arch <= mod._TIMETABLE_LABELS)
    check("_TIMETABLE_CLASSES (曜日+時限のコマ) には入っていない = 出欠・時間割・毎朝の宿題・ブリーフが回さない",
          not (arch & {c_["label"] for c_ in mod._TIMETABLE_CLASSES}))
    check("自動宿題の表は hold", all(mod._CLASS_HW_ROUTINE_MAP[lb]["kind"] == "hold" for lb in arch))
    check("自動宿題の範囲は無し (配らない)", not any(mod._class_hw_range(lb, g) for lb in arch for g in ("kosei", "chugaku")))

    print("\n[2] 登録フォームの subjects (label 内の「・」)")
    sp = mod._split_class_subjects
    check("「日東駒専・産近甲龍」を 1 つの label に戻す", sp(NTKS) == [NTKS], sp(NTKS))
    mixed = "国公立難関大コース・水曜3限 国公立コース 英文法・" + NTKS + "・" + KOKU
    check("コース名・コマ・アーカイブが混ざっても割り方が正しい",
          sp(mixed) == ["国公立難関大コース", "水曜3限 国公立コース 英文法", NTKS, KOKU], sp(mixed))
    check("知らない語はそのまま 1 語ずつ (dropped_subjects に出せる)", sp("謎のクラス・" + KKDR + "・") == ["謎のクラス", KKDR], sp("謎のクラス・" + KKDR))
    check("空 / None は []", sp("") == [] and sp(None) == [])
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO course_applications (name, email, status, referrer, grade, subjects) VALUES (?,?,?,?,?,?)",
              ("アーカイブ承認テスト", "arch-new@example.org", "pending", "塾生アプリ", "高3", NTKS + "・" + KKDR))
    c.execute("SELECT id FROM course_applications WHERE email = ?", ("arch-new@example.org",)); app_id = c.fetchone()["id"]
    conn.commit(); conn.close()
    mod._send_message_email = lambda *a, **k: {"sent": True}
    r = client.post(f"/api/admin/course-applications/{app_id}/approve", json={"ai_disabled": True, "merge_siblings": True}, headers=adm)
    j = r.json() if r.status_code == 200 else {}
    check("承認 → 200", r.status_code == 200, r.text[:200])
    check("承認: class_labels に 2 クラスとも入る・捨てた語なし", j.get("class_labels") == [NTKS, KKDR] and j.get("dropped_subjects") == [],
          str({k: j.get(k) for k in ("class_labels", "dropped_subjects")}))

    print("\n[3] CEO の API")
    r = client.get("/api/admin/class/timetable-classes", headers=adm)
    cls = r.json().get("classes", []) if r.status_code == 200 else []
    ar = [x for x in cls if x.get("archive")]
    check("timetable-classes: 18 クラス・アーカイブ 3 つは archive=true・dow/time は None",
          len(cls) == 19 and [x["label"] for x in ar] == [KKDR, KOKU, NINKI, NTKS] and all(x["dow"] is None and x["time"] is None for x in ar), str(ar))
    sid_in = make_student(mod, "アーカイブ受講 A", "arch-a@example.org", [KOKU], start_month="2026-11")
    sid_out = make_student(mod, "アーカイブ非受講 B", "arch-b@example.org", ["水曜2限 GMARCH"])
    sid_all = make_student(mod, "アーカイブ受講 C", "arch-c@example.org", [KOKU])   # start_month NULL = 全部
    r = client.post("/api/admin/class/student-classes", json={"student_id": sid_out, "class_labels": ["水曜2限 GMARCH", NTKS]}, headers=adm)
    check("受講クラスの保存: アーカイブ専用クラスを捨てない", r.status_code == 200 and r.json().get("class_labels") == ["水曜2限 GMARCH", NTKS], r.text[:200])
    r = client.post("/api/admin/class/class-roster", json={"class_label": NTKS, "student_ids": []}, headers=adm)
    check("クラス別一括登録: アーカイブ専用クラスを受け付ける (外すと B から消える)", r.status_code == 200, r.text[:200])
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT class_labels FROM students WHERE id = ?", (sid_out,)); lb = json.loads(c.fetchone()["class_labels"] or "[]")
    conn.close()
    check("B は GMARCH だけに戻る", lb == ["水曜2限 GMARCH"], lb)
    r = client.post("/api/admin/class/files", json={"title": "国公立 第1週 プリント", "filename": "w1.pdf", "mime": "application/pdf",
                                                    "data_b64": base64.b64encode(b"%PDF-1.4\n%test\n").decode(), "class_label": KOKU}, headers=adm)
    check("クラス別配布ファイル: アーカイブ専用クラスに配れる", r.status_code == 200, r.text[:200])

    print("\n[4] 出欠は無い")
    tok = {s: {"Authorization": "Bearer " + student_token(mod, s)} for s in (sid_in, sid_out, sid_all)}
    r = client.post("/api/student/class/attend", json={"class_label": KOKU, "att_date": "2026-11-20", "status": "present"}, headers=tok[sid_in])
    check("生徒の出欠申告 → 400", r.status_code == 400, r.text[:160])
    r = client.post("/api/admin/class/attend", json={"class_label": KOKU, "att_date": "2026-11-20", "status": "present", "student_id": sid_in}, headers=adm)
    check("塾長の出欠記録 → 400", r.status_code == 400, r.text[:160])
    r = client.get("/api/admin/class/attend", params={"att_date": "2026-11-20", "class_label": KOKU}, headers=adm)
    check("塾長の出欠名簿 → 400", r.status_code == 400, r.text[:160])

    print("\n[5] feed: 受講生にだけ・受講開始月以降だけ")
    r = client.post("/api/admin/class/sessions", json={"title": KOKU, "subject": "アーカイブ"}, headers=adm)
    check("授業 (動画の入れ物) を作れる", r.status_code == 200, r.text[:160])
    sess = r.json().get("id") if r.status_code == 200 else None
    for title, url, ld in (("第1講 10月公開", "https://youtu.be/ArchOct0001", "2026-10-28"),
                           ("第2講 11月公開", "https://youtu.be/ArchNov0001", "2026-11-04")):
        r = client.post("/api/admin/class/recordings", json={"title": title, "video_url": url, "session_id": sess, "lesson_date": ld}, headers=adm)
        check(f"録画「{title}」を授業日 {ld} で登録", r.status_code == 200 and r.json().get("lesson_date") == ld, r.text[:160])

    def feed(s):
        r_ = client.get("/api/student/class/feed", headers=tok[s])
        return r_.json() if r_.status_code == 200 else {}

    def recs(d):
        return sorted(x["title"] for se in d.get("sessions", []) for x in se.get("recordings", []))

    fa, fb, fc = feed(sid_in), feed(sid_out), feed(sid_all)
    check("A (11月開始): 11月公開の 1 本だけ・非表示 1 本", recs(fa) == ["第2講 11月公開"] and fa.get("hidden_recordings") == 1, f"{recs(fa)} hidden={fa.get('hidden_recordings')}")
    check("A: 授業に archive=true", any(se.get("archive") is True and se["title"] == KOKU for se in fa.get("sessions", [])))
    check("C (開始月なし): 2 本とも", recs(fc) == ["第1講 10月公開", "第2講 11月公開"], recs(fc))
    check("B (非受講): 授業ごと出ない・録画 0 本", recs(fb) == [] and not any(se["title"] == KOKU for se in fb.get("sessions", [])), recs(fb))
    check("A: クラス別配布ファイルが見える / B には出ない",
          [f["title"] for f in fa.get("labeled_files", [])] == ["国公立 第1週 プリント"] and not fb.get("labeled_files"))
    r = client.post("/api/student/class/attendance", json={"session_id": sess, "status": "present"}, headers=tok[sid_in])
    check("アーカイブの授業への出欠申告 → 400", r.status_code == 400, r.text[:160])

    print("\n[6] 録画の自動割り当てはアーカイブ専用クラスの授業を見ない")
    import class_recording_assign as cra
    today = datetime.date(2026, 11, 17)
    rep = cra.build_plan(today, [], [(1, KOKU), (2, NTKS)], [], {})
    check("アーカイブだけ → blocking 0・no_playlist 空", rep["blocking"] == 0 and rep["no_playlist"] == [] and rep["sessions_total"] == 0,
          str({k: rep[k] for k in ("blocking", "no_playlist", "sessions_total")}))
    rep = cra.build_plan(today, [], [(1, KOKU), (3, "日曜 高校国語")], [], {})
    check("普通の授業は今までどおり見る (再生リストが無ければ blocking)", rep["blocking"] == 1 and rep["no_playlist"] == ["日曜 高校国語"], str(rep["no_playlist"]))
    check("slot_of は label を曜日+限と読まない", all(cra.slot_of(lb) is None for lb in arch))

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)}件")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("✅ ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
