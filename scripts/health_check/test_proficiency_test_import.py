#!/usr/bin/env python3
"""🧪 習熟度テスト (科目 proficiency_test) の取込・出題順・自動配信からの除外の回帰テスト (2026-10-15 塾長決定)。

習熟度テストは Codex が作ったファイル (1 ファイル = 1 回分・番号は 1 始まり) を取込スクリプトが 0 始まりに直して送る。
1 回分 = 1 単元 (大問 1 つ = 本文 1 つ)。塾長が CEO で配り、全大問を出題順のまま 1 本のドリルにする。自動配信には一切出さない。
このテストでは取込スクリプトの変換 (1 始まり → 0 始まり) を手書きの to_payload で再現する (中身はすべて架空・_fixture)。

  (1) 取込: 大問 3・設問 9 が入る・kv_settings 'ptest_meta:<単元>' (大問数・設問数・skill)
  (2) 1 始まり → 0 始まり: DB の choices[answer] がファイルの choices[correct_choice_no - 1] と全問一致
  (3) 拒否: 単元名の形違い (errors + unknown_units)・questions[] (422)・review なし (422)・大問 13 / 設問 61 (422)・
      ptest_meta の skill が単元ドリルに無い / 設問がテストに無い / 2 回分まとめて (422)・dry_run は kv も書かない
  (4) 取込済みの単元に新しい本文 → ok:false・同じ要求の再送 → already_imported・「第1回改1」は入る
  (5) 配信: passage_count・levels は無視して全大問を取込順・設問はファイルの qid 順 (5 回とも同じ)・題名「🧪 …（全N問）」・
      exclude_drill_id と単元なしは 422・同じ生徒への 2 回目は already_taken・全員なら 409 (ドリルを作らない)・allow_retake
  (6) 👀 プレビュー: 本数・レベルの指定に関わらずテスト全体を出題順に答えつきで
  (7) 生徒の取得は答えを伏せる・正解どおりに出すと満点・分析の名簿と問題別正答率
  (8) 解答は subject='proficiency_test'・topic=単元 → 弱点にならない / PTEST_FEEDS_WEAKNESS=1 なら skill つきの誤答が
      english/関係詞 の解答と弱点になり、skill なしは proficiency_test のまま
  (9) 習熟度テストしか無い DB: 今日の1問・初回診断は 503・3日ドリルは配らない・1 問ずつ / 本文の自動の抽出は 0
      (env AUTO_DELIVERY_REVIEWED_SOURCES で proficiency_test=* と書いても)
  (10) 英検の本文の順は今もランダム (ORDER BY id は習熟度テストだけ)
  (11) CEO の配信済み一覧 subject=proficiency_test はテストだけ・単元一覧は 高校/中学・回・改 の順
  (12) 自動配信の関数のソースに proficiency_test / _PTEST_SUBJECT が出てこない (許可リストに入れていない静的な確認)・
      お知らせのメールの件名「🧪 習熟度テスト「…」が届きました」

実行:
    python3 scripts/health_check/test_proficiency_test_import.py
    # exit 0 = PASS / 1 = FAIL

外部通信はしない。DB は一時 SQLite。生徒名・メール・テストの中身は架空 (公開リポジトリ・テストの本物は置かない)。
"""
import base64
import copy
import datetime
import hashlib
import hmac
import importlib.util
import inspect
import json
import os
import random
import sys
import tempfile
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
CIRCLED = "①②③④⑤⑥⑦⑧"


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:400]}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="ptest_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** に書き込む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "BASE_URL": "https://example.invalid",
        "CRON_SECRET": "test-cron-secret",
    })
    for k in ("AUTO_DELIVERY_REVIEWED_SOURCES", "HOMEWORK_NOTIFY_LINE", "PTEST_FEEDS_WEAKNESS"):
        os.environ.pop(k, None)
    os.environ["HOMEWORK_NOTIFY_EMAIL"] = "off"   # 配信のたびのお知らせ (メール) は回さない。件名は [12] で直接確かめる
    spec = importlib.util.spec_from_file_location("aijuku_main_ptest", MAIN_PY)
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


def q(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    out = [dict(r) for r in c.fetchall()]
    conn.close()
    return out


def ex(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    conn.commit(); conn.close()


def counts(mod):
    return {t: q(mod, f"SELECT COUNT(*) AS n FROM {t}")[0]["n"]
            for t in ("grammar_passages", "grammar_questions", "grammar_drills", "grammar_drill_assignments")}


class Env:
    def __init__(self, **kv):
        self.kv = kv

    def __enter__(self):
        self.old = {k: os.environ.get(k) for k in self.kv}
        for k, v in self.kv.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return self

    def __exit__(self, *a):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def ptest_doc(test_id="HSENG01", round_=1, revision=0, per=(3, 2, 4), target="kosei", subject_ja="英語"):
    """仕様書 (trillion-drill-import/v1) の形の架空のテスト。correct_choice_no は 1 始まり。"""
    sections, qn = [], 0
    for s, n in enumerate(per, 1):
        qs = []
        for _ in range(n):
            qn += 1
            ch = [f"架空の選択肢 {test_id} {qn}-{x}" for x in "abcd"]
            cno = (qn * 3) % 4 + 1
            qs.append({"qid": f"Q{qn:02d}", "stem": f"架空の設問 {test_id} 第{s}問 {qn}", "choices": ch, "correct_choice_no": cno,
                       "explanation": f"正解 {CIRCLED[cno - 1]} {ch[cno - 1]}\n【解説】架空\n【他の選択肢】\n…",
                       "skill": {"subject": "english", "unit": "関係詞"} if qn == 2 else None})
        sections.append({"section_no": s, "title": f"第{s}問", "body": f"第{s}問 架空の指示文 {test_id} 第{round_}回",
                         "body_ja": None, "questions": qs})
    return {"format": "trillion-drill-import/v1", "kind": "proficiency_test", "_fixture": True, "test_id": test_id,
            "target": target, "subject": "english", "subject_ja": subject_ja, "series_ja": "習熟度テスト", "round": round_,
            "revision": revision, "title": f"架空 習熟度テスト 第{round_}回", "time_limit_min": 60, "sections": sections}


def unit_of(doc):
    return (f"{'高校' if doc['target'] == 'kosei' else '中学'}{doc['subject_ja']} {doc['series_ja']} 第{doc['round']}回"
            + (f"改{doc['revision']}" if doc.get("revision") else ""))


def to_payload(doc):
    """取込スクリプト (scripts/drill_import の build_payloads) と同じ変換: 1 始まり → 0 始まり・出典 pt-<test_id>-<qid> /
    本文 ptest:<test_id>:S<nn>・skill は ptest_meta へ。"""
    unit, passages, skills = unit_of(doc), [], {}
    for sec in sorted(doc["sections"], key=lambda s: s["section_no"]):
        qs = []
        for qq in sec["questions"]:
            src = f"pt-{doc['test_id']}-{qq['qid']}"
            qs.append({"stem": qq["stem"], "choices": qq["choices"], "answer": qq["correct_choice_no"] - 1,
                       "explanation": qq["explanation"], "source": src})
            if qq.get("skill"):
                skills[src] = f"{qq['skill']['subject']}|{qq['skill']['unit']}"
        passages.append({"subject": "proficiency_test", "unit": unit, "level": "standard", "title": sec["title"],
                         "body": sec["body"], "body_ja": sec.get("body_ja"),
                         "source": f"ptest:{doc['test_id']}:S{sec['section_no']:02d}", "questions": qs})
    return {"subject": "proficiency_test", "dedup": True, "all_or_nothing": True, "passages": passages,
            "review": {"protocol": "trillion-blind/v1", "all_agree": True, "validator": "validate_drill_import/v1",
                       "file_sha256": "0" * 64, "kind": "proficiency_test", "test_id": doc["test_id"],
                       "solvers": [{"label": x, "kind": "ai", "date": "2026-10-21"} for x in "ABC"]},
            "ptest_meta": {"test_id": doc["test_id"], "title": doc["title"], "target": doc["target"], "subject": doc["subject"],
                           "round": doc["round"], "revision": doc.get("revision", 0), "time_limit_min": doc.get("time_limit_min"),
                           "skills": skills}}


def main():
    print("🧪 習熟度テスト (proficiency_test) 取込・出題順・自動配信からの除外 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    adm = {"Authorization": "Bearer " + admin_token(mod)}
    cron = {"X-Cron-Secret": "test-cron-secret"}

    def imp(body):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar/import", json=body, headers=adm)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})

    def create(**body):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post("/api/admin/grammar-drill/create", json=dict({"subject": "proficiency_test"}, **body), headers=adm)
        return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else {})

    seq = [0]

    def make(grade="高校2年", ai_disabled=0):
        seq[0] += 1
        conn = mod.db(); c = conn.cursor()
        c.execute("INSERT INTO students (name, email, status, grade, ai_disabled) VALUES (?, ?, 'paid', ?, ?) RETURNING id",
                  (f"架空 テスト{seq[0]:02d}", f"ptest-{seq[0]:02d}@example.org", grade, ai_disabled))
        sid = c.fetchone()["id"]
        conn.commit(); conn.close()
        mod._AI_DISABLED_CACHE.pop(sid, None)
        return sid

    check("科目 proficiency_test が canonical・別名「習熟度テスト」・ラベル「習熟度テスト」",
          "proficiency_test" in mod._GRAMMAR_CANON_SUBJECTS and mod._canon_grammar_subject("習熟度テスト") == "proficiency_test"
          and mod._grammar_subject_label_ja("proficiency_test") == "習熟度テスト")
    check("自動配信の禁止の科目 (env でも外せない)", "proficiency_test" in mod._AUTO_DELIVERY_DENY_SUBJECTS)

    # ------------------------------------------------------------------
    print("\n[1] 取込")
    doc = ptest_doc()
    unit = unit_of(doc)
    check("単元名は「高校英語 習熟度テスト 第1回」(_PTEST_UNIT_RE に合う)", unit == "高校英語 習熟度テスト 第1回" and bool(mod._PTEST_UNIT_RE.match(unit)))
    pl = to_payload(doc)
    code, d = imp(pl)
    check("大問 3・設問 9 が入る (ok・errors 0・already_imported false・ptest_meta_saved)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3 and d.get("inserted") == 9 and d.get("errors") == 0
          and d.get("already_imported") is False and d.get("ptest_meta_saved") is True, d)
    kv = q(mod, "SELECT value FROM kv_settings WHERE key = ?", ("ptest_meta:" + unit,))
    meta = json.loads(kv[0]["value"]) if kv else {}
    check("kv_settings 'ptest_meta:<単元>' に大問数・設問数・skill (設問の出典 → 科目|単元)",
          meta.get("section_count") == 3 and meta.get("question_count") == 9 and meta.get("test_id") == "HSENG01"
          and meta.get("skills") == {"pt-HSENG01-Q02": "english|関係詞"} and meta.get("time_limit_min") == 60, meta)
    rows = q(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'proficiency_test' AND passage_id IS NULL")
    check("習熟度テストの設問はすべて本文 (大問) に紐づく", rows[0]["n"] == 0)
    ev = q(mod, "SELECT props FROM events WHERE name = 'grammar_import_review'")
    check("events 'grammar_import_review' に記録 (test_id・単元)",
          len(ev) == 1 and json.loads(ev[0]["props"]).get("review", {}).get("test_id") == "HSENG01"
          and json.loads(ev[0]["props"]).get("units") == [unit], ev)

    # ------------------------------------------------------------------
    print("\n[2] 1 始まり → 0 始まり")
    by_src = {r["source"]: r for r in q(mod, "SELECT source, choices, answer FROM grammar_questions WHERE subject = 'proficiency_test'")}
    bad = []
    for sec in doc["sections"]:
        for qq in sec["questions"]:
            r = by_src.get(f"pt-HSENG01-{qq['qid']}")
            if not r or json.loads(r["choices"])[int(r["answer"])] != qq["choices"][qq["correct_choice_no"] - 1]:
                bad.append(qq["qid"])
    check("全 9 問で DB の choices[answer] == ファイルの choices[correct_choice_no - 1]", not bad and len(by_src) == 9, bad)

    # ------------------------------------------------------------------
    print("\n[3] 拒否")
    before = counts(mod)
    d2 = ptest_doc("HSENG02", round_=2)
    p2 = to_payload(d2)
    for p_ in p2["passages"]:
        p_["unit"] = "HSENG02 第2回"
    code, d = imp(dict(p2, all_or_nothing=False, ptest_meta=None))
    check("単元名の形違い (「HSENG02 第2回」) は入れずに errors 3・unknown_units・warning に正しい形",
          code == 200 and d.get("errors") == 3 and d.get("passages_inserted") == 0
          and (d.get("unknown_units") or [{}])[0].get("unit") == "HSENG02 第2回" and "高校英語 習熟度テスト 第1回" in (d.get("warning") or "")
          and counts(mod) == before, d)
    code, d = imp(dict(p2, ptest_meta=None))
    check("all_or_nothing なら ok:false (unknown_unit)・0 行", code == 200 and d.get("ok") is False and d.get("reason") == "unknown_unit"
          and counts(mod) == before, d)
    code, d = imp({"subject": "proficiency_test", "questions": [{"unit": unit, "stem": "x", "choices": ["a", "b"], "answer": 0}]})
    check("questions[] (1 問ずつ) → 422", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(dict(to_payload(ptest_doc("HSENG03", round_=3)), review=None))
    check("review なし → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(to_payload(ptest_doc("HSENG04", round_=4, per=(1,) * 13)))
    check("大問 13 (上限 12) → 422・0 行", code == 422 and "大問 12" in str(d.get("detail")) and counts(mod) == before, (code, d))
    code, d = imp(to_payload(ptest_doc("HSENG05", round_=5, per=(15, 15, 15, 15, 1))))
    check("設問 61 (上限 60) → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    p6 = to_payload(ptest_doc("HSENG06", round_=6))
    for bad_skill, why in (({"pt-HSENG06-Q02": "math|数と式"}, "高校の math (単元名が決まっていない)"),
                           ({"pt-HSENG06-Q02": "english|関係代名詞"}, "english に無い単元"),
                           ({"pt-HSENG06-Q02": "proficiency_test|x"}, "習熟度テスト自身"),
                           ({"pt-HSENG06-Q99": "english|関係詞"}, "テストに無い設問"),
                           ({"pt-HSENG06-Q02": "english"}, "'|' が無い")):
        code, d = imp(dict(p6, ptest_meta=dict(p6["ptest_meta"], skills=bad_skill)))
        check(f"ptest_meta の skill が不正 ({why}) → 422・0 行", code == 422 and counts(mod) == before, (code, d))
    code, d = imp(dict(p6, ptest_meta=dict(p6["ptest_meta"], skills={"pt-HSENG06-Q02": "chugaku|関係代名詞"})))
    check("skill は中学英語の単元も可 (chugaku|関係代名詞)", code == 200 and d.get("ok") is True and d.get("ptest_meta_saved") is True, d)
    two = to_payload(ptest_doc("HSENG07", round_=7))
    two["passages"] += to_payload(ptest_doc("HSENG08", round_=8))["passages"]
    code, d = imp(two)
    check("ptest_meta を 2 回分まとめて送る → 422", code == 422, (code, d))
    before = counts(mod)
    kv_before = q(mod, "SELECT COUNT(*) AS n FROM kv_settings")[0]["n"]
    code, d = imp(dict(to_payload(ptest_doc("HSENG09", round_=9)), dry_run=True))
    check("dry_run: 大問 3 と数え、本文・設問・kv (ptest_meta) は書かない",
          code == 200 and d.get("dry_run") is True and d.get("passages_inserted") == 3 and counts(mod) == before
          and q(mod, "SELECT COUNT(*) AS n FROM kv_settings")[0]["n"] == kv_before, d)

    # ------------------------------------------------------------------
    print("\n[4] 取込済みの単元・再送・改1")
    before = counts(mod)
    code, d = imp(pl)
    check("同じ要求の再送は already_imported: true・0 行", code == 200 and d.get("ok") is True and d.get("already_imported") is True
          and d.get("passages_inserted") == 0 and counts(mod) == before, d)
    more = copy.deepcopy(pl)
    more["passages"].append(dict(copy.deepcopy(more["passages"][0]), body="第4問 架空の追加の大問", source="ptest:HSENG01:S04"))
    more["ptest_meta"] = None
    code, d = imp(more)
    check("取込済みのテストに大問を足す要求は ok:false (group_exists)・0 行",
          code == 200 and d.get("ok") is False and d.get("reason") == "group_exists" and counts(mod) == before, d)
    rev = ptest_doc(revision=1)
    code, d = imp(to_payload(rev))
    check("直した版「高校英語 習熟度テスト 第1回改1」は入る (本文が同じでも単元が別)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3 and unit_of(rev) == "高校英語 習熟度テスト 第1回改1", d)

    # ------------------------------------------------------------------
    print("\n[5] 配信 (全大問を取込順・同じ生徒に 2 回は配らない)")
    want_src = [f"pt-HSENG01-{qq['qid']}" for sec in doc["sections"] for qq in sec["questions"]]
    src_of = {r["id"]: r["source"] for r in q(mod, "SELECT id, source FROM grammar_questions WHERE subject = 'proficiency_test'")}
    sa, sb, sc_ = make(), make(), make()
    code, d = create(unit=unit, passage_count=1, levels=["advanced"], count=5, student_ids=[sa])
    check("passage_count=1・levels=advanced を送っても全大問 3・全 9 問・題名「🧪 高校英語 習熟度テスト 第1回（全9問）」",
          code == 200 and d.get("passage_count") == 3 and d.get("question_count") == 9
          and d.get("title") == "🧪 高校英語 習熟度テスト 第1回（全9問）", d)
    drill_a = d.get("drill_id")
    qids = json.loads(q(mod, "SELECT question_ids FROM grammar_drills WHERE id = ?", (drill_a,))[0]["question_ids"])
    check("設問の順 = ファイルの qid 順 (Q01..Q09)", [src_of.get(x) for x in qids] == want_src, [src_of.get(x) for x in qids])
    orders = set()
    for _ in range(5):
        code, d = create(unit=unit, student_ids=[sc_], allow_retake=True)
        orders.add(tuple(json.loads(q(mod, "SELECT question_ids FROM grammar_drills WHERE id = ?", (d.get("drill_id"),))[0]["question_ids"]))
                   if code == 200 else None)
    check("5 回作っても同じ順 (allow_retake で同じ生徒にも配れる)", orders == {tuple(qids)}, orders)
    sa_st = q(mod, "SELECT score_total FROM grammar_drill_assignments WHERE drill_id = ?", (drill_a,))
    check("score_total = 設問数 9", sa_st and sa_st[0]["score_total"] == 9, sa_st)
    n_drills = counts(mod)["grammar_drills"]
    code, d = create(unit=unit, student_ids=[sa, sb])
    check("配信済みの生徒 A は外して B だけに配る (already_taken に A・message に「飛ばしました」)",
          code == 200 and [x["student_id"] for x in d.get("assigned", [])] == [sb]
          and [x["student_id"] for x in d.get("already_taken", [])] == [sa] and d["already_taken"][0].get("name")
          and "1名は飛ばしました" in (d.get("message") or ""), d)
    n_drills = counts(mod)["grammar_drills"]
    code, d = create(unit=unit, student_ids=[sa, sb])
    check("全員が配信済み → 409・空のドリルを作らない", code == 409 and counts(mod)["grammar_drills"] == n_drills
          and "全員このテストを配信済み" in str(d.get("detail")), (code, d))
    code, d = create(unit=unit, student_ids=[sa], allow_retake=True)
    check("allow_retake: true なら配れる (追試・CEO には出さない)", code == 200 and [x["student_id"] for x in d.get("assigned", [])] == [sa], d)
    code, d = create(unit=unit, student_ids=[sb], allow_retake="yes")
    check("allow_retake は true (真偽値) のときだけ ('yes' は 409)", code == 409, (code, d))
    code, d = create(unit=unit, exclude_drill_id=drill_a, student_ids=[make()])
    check("exclude_drill_id → 422 (弱点対策の再配信に使わない)", code == 422, (code, d))
    code, d = create(unit="", student_ids=[make()])
    check("単元なし (科目まるごと) → 422", code == 422, (code, d))
    code, d = create(unit="高校英語 習熟度テスト 第99回", student_ids=[make()])
    check("取り込んでいない単元 → 400", code == 400 and "取り込まれていません" in str(d.get("detail")), (code, d))
    check("_drill_create_message: 全員配信済みの文・一部の文",
          "全員このテストを配信済み" in mod._drill_create_message(0, "x", None, already_taken=2)
          and "（このテストを配信済みの 2名は飛ばしました）" in mod._drill_create_message(1, "x", {}, already_taken=2)
          and "飛ばしました" not in mod._drill_create_message(1, "x", {}))

    # ------------------------------------------------------------------
    print("\n[6] 👀 プレビュー")
    r = client.get("/api/admin/grammar/preview", params={"subject": "proficiency_test", "unit": unit, "passage_count": 1, "levels": "advanced"},
                   headers=adm)
    pv = r.json() if r.status_code == 200 else {}
    pq = pv.get("questions") or []
    check("本数・レベルの指定に関わらずテスト全体 (大問 3・9 問) を出題順に",
          r.status_code == 200 and pv.get("passage_count") == 3 and [src_of.get(x["id"]) for x in pq] == want_src, r.text[:200])
    want_ans = [qq["correct_choice_no"] - 1 for sec in doc["sections"] for qq in sec["questions"]]
    check("答え (0 始まり)・解説つき", [x.get("answer") for x in pq] == want_ans and all(x.get("explanation") for x in pq), pq[:2])

    # ------------------------------------------------------------------
    print("\n[7] 生徒の取得・提出・分析")
    tok = {"Authorization": "Bearer " + student_token(mod, sa)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.get(f"/api/student/grammar-drill/{drill_a}", headers=tok)
    g = r.json() if r.status_code == 200 else {}
    gq = g.get("questions") or []
    check("取得: 9 問・答えと解説を伏せる", r.status_code == 200 and len(gq) == 9 and all("answer" not in x and "explanation" not in x for x in gq),
          r.text[:200])
    answers = {str(x): a for x, a in zip(qids, want_ans)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill_a}/submit", json={"answers": answers}, headers=tok)
    s = r.json() if r.status_code == 200 else {}
    check("正解どおりに提出すると 9/9・subject は proficiency_test", r.status_code == 200 and s.get("score_correct") == 9
          and s.get("score_total") == 9 and s.get("subject") == "proficiency_test", r.text[:200])
    mod._RATE_LIMIT_STORE.clear()
    r = client.post(f"/api/student/grammar-drill/{drill_a}/submit", json={"answers": answers}, headers=tok)
    check("2 回目の提出は 409 (提出は 1 回だけ)", r.status_code == 409, r.status_code)
    r = client.get(f"/api/admin/grammar-drill/{drill_a}/analytics", headers=adm)
    a = r.json() if r.status_code == 200 else {}
    roster = a.get("students") or []
    check("分析: 名簿に提出済み 1 名・問題別正答率 100% が 9 問",
          r.status_code == 200 and a.get("summary", {}).get("completed") == 1
          and len(a.get("questions") or []) == 9 and all(x.get("correct_rate") == 100.0 for x in a.get("questions") or [])
          and any(x.get("student_id") == sa for x in roster), r.text[:300])

    # ------------------------------------------------------------------
    print("\n[8] 弱点に入れない (PTEST_FEEDS_WEAKNESS)")
    rows = q(mod, "SELECT subject, topic, metadata FROM question_attempts WHERE student_id = ?", (sa,))
    check("解答は subject='proficiency_test'・topic=単元・metadata.ptest_unit で 9 行",
          len(rows) == 9 and all(x["subject"] == "proficiency_test" and x["topic"] == unit
                                 and json.loads(x["metadata"]).get("ptest_unit") == unit for x in rows), rows[:2])
    mod._run_weakness_aggregation()
    w = q(mod, "SELECT subject, topic FROM student_weakness WHERE subject = 'proficiency_test' OR topic = ?", (unit,))
    check("弱点集計の後も proficiency_test の弱点は 0 行 (単元名が弱点にならない)", w == [], w)
    sf = make()
    code, d = create(unit=unit, student_ids=[sf])
    drill_f = d.get("drill_id")
    wrong = {str(x): (a + 1) % 4 for x, a in zip(qids, want_ans)}   # 全問まちがえる
    with Env(PTEST_FEEDS_WEAKNESS="1"):
        mod._RATE_LIMIT_STORE.clear()
        r = client.post(f"/api/student/grammar-drill/{drill_f}/submit", json={"answers": wrong},
                        headers={"Authorization": "Bearer " + student_token(mod, sf)})
    rows = q(mod, "SELECT exam_question_id, subject, topic, metadata FROM question_attempts WHERE student_id = ? ORDER BY id", (sf,))
    q02 = [x for x in rows if src_of.get(x["exam_question_id"]) == "pt-HSENG01-Q02"]
    others = [x for x in rows if src_of.get(x["exam_question_id"]) != "pt-HSENG01-Q02"]
    check("PTEST_FEEDS_WEAKNESS=1: skill つきの Q02 は english/関係詞 で記録 (metadata.ptest_skill)",
          r.status_code == 200 and len(q02) == 1 and q02[0]["subject"] == "english" and q02[0]["topic"] == "関係詞"
          and json.loads(q02[0]["metadata"]).get("ptest_skill") is True, q02)
    check("skill なしの 8 問は proficiency_test のまま", len(others) == 8 and all(x["subject"] == "proficiency_test" for x in others), others[:2])
    mod._run_weakness_aggregation()
    w = q(mod, "SELECT subject, topic FROM student_weakness WHERE student_id = ?", (sf,))
    check("弱点集計の後: english/関係詞 の弱点が立ち、proficiency_test の弱点は無い",
          {"subject": "english", "topic": "関係詞"} in w and not any(x["subject"] == "proficiency_test" for x in w), w)
    check("PTEST_FEEDS_WEAKNESS の既定は OFF", mod._ptest_feeds_weakness() is False)

    # ------------------------------------------------------------------
    print("\n[9] 習熟度テストしか無い DB: 自動・自己発行の経路に出ない")
    s9 = make()
    tok9 = {"Authorization": "Bearer " + student_token(mod, s9)}
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/today-question/start", headers=tok9)
    check("今日の1問 → 503", r.status_code == 503, (r.status_code, r.text[:200]))
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/student/diagnostic/start", headers=tok9)
    check("初回診断 → 503", r.status_code == 503, (r.status_code, r.text[:200]))
    ex(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) "
            "VALUES (?, 'proficiency_test', ?, 10, 0.1, 10)", (s9, unit))
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT id, name, email, line_user_id, grade, ai_disabled, ai_trial_until FROM students WHERE id = ?", (s9,))
    st = c.fetchone()
    reasons = {}
    p = mod._weakness_routine_plan(c, st, "kosei", rng=random.Random(1), reasons=reasons)
    check("3日ドリル: 習熟度テストの弱点の行があっても配らない (not_routine_subject:proficiency_test)",
          not p["ok"] and reasons.get("not_routine_subject:proficiency_test") == 1, (p, reasons))
    check("CEO の 1 問ずつの抽出 (科目まるごと) は 0 問",
          mod._grammar_pick_drill_question_ids(c, "proficiency_test", "", True, ["basic", "standard", "advanced"], 5, None) == [])
    for env_v in (None, "english=*;proficiency_test=*"):
        with Env(AUTO_DELIVERY_REVIEWED_SOURCES=env_v):
            r1 = mod._auto_pick_reviewed_question_ids(c, "proficiency_test", "", ["basic", "standard", "advanced"], 1, {}, rng=random.Random(1))
            r2 = mod._auto_pick_reviewed_passages(c, "proficiency_test", unit, ["standard"], 1, {}, rng=random.Random(1))
            idx = mod._auto_reviewed_passages(c, "proficiency_test", unit, ["standard"])
            check(f"自動の抽出 (3日ドリル・クラス自動宿題が使う 2 つ) は 0 (env={env_v!r})",
                  r1["ids"] == [] and r2["qids"] == [] and r2["reviewed_available"] == 0 and idx["passages"] == {}
                  and idx["rejected"]["unreviewed_body"] == 3, (r1, r2, idx["rejected"]))
            check(f"学年の区分の判定でも出ない (env={env_v!r})",
                  not any(mod._drill_subject_band_ok("proficiency_test", b) for b in ("kosei", "chugaku", "shougaku", "")))
    conn.close()
    mod._RATE_LIMIT_STORE.clear()
    r = client.post("/api/admin/weakness-drill-routine/run", json={"dry_run": True, "student_id": s9}, headers=cron)
    check("3日ドリルの dry-run: 配る生徒 0", r.status_code == 200 and r.json().get("delivered") == 0, r.text[:300])

    # ------------------------------------------------------------------
    print("\n[10] 英検の本文の順はランダムのまま")
    eik = []
    for n in range(6):
        eik.append({"unit": "準1級 長文 内容一致", "level": "standard", "title": f"架空 {n}", "body": f"Fictional eiken passage {n}. ( 1 )",
                    "source": f"test-eik-{n}", "questions": [{"stem": f"架空の設問 {n}", "choices": ["a", "b", "c", "d"], "answer": n % 4}]})
    code, d = imp({"subject": "eiken", "dedup": True, "passages": eik})
    check("英検の本文 6 本 (CEO の補充ボタンと同じ送り方・review なし) は従来どおり入る", code == 200 and d.get("passages_inserted") == 6, d)
    conn = mod.db(); c = conn.cursor()
    eorders = {tuple(mod._grammar_pick_drill_passages(c, "eiken", "準1級 長文 内容一致", ["standard"], 6, None)[1]) for _ in range(20)}
    porders = {tuple(mod._grammar_pick_drill_passages(c, "proficiency_test", unit, ["basic", "standard", "advanced"], 12, None)[1]) for _ in range(20)}
    conn.close()
    check("英検: 20 回で本文の順が 2 通り以上", len(eorders) >= 2, len(eorders))
    check("習熟度テスト: 20 回とも同じ順 (id の昇順)", len(porders) == 1 and list(next(iter(porders))) == sorted(next(iter(porders))), porders)

    # ------------------------------------------------------------------
    print("\n[11] CEO の配信済み一覧・単元一覧")
    sid_e = make()
    code, d = create(subject="eiken", unit="準1級 長文 内容一致", passage_count=1, student_ids=[sid_e])
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "proficiency_test", "kind": "all"}, headers=adm)
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("list?subject=proficiency_test はテストだけ (英検のドリルは出ない)",
          r.status_code == 200 and items and all(x.get("subject") == "proficiency_test" for x in items), [x.get("subject") for x in items])
    r = client.get("/api/admin/grammar-drill/list", params={"subject": "習熟度テスト"}, headers=adm)
    check("別名「習熟度テスト」でも絞れる", r.status_code == 200 and r.json().get("subject") == "proficiency_test", r.text[:200])
    for tid, rnd, tgt in (("HSENG10", 10, "kosei"), ("HSENG02X", 2, "kosei"), ("JHENG01", 1, "chugaku")):
        code, d = imp(to_payload(ptest_doc(tid, round_=rnd, target=tgt)))
        check(f"{tid} 第{rnd}回 ({tgt}) が入る", code == 200 and d.get("ok") is True and d.get("passages_inserted") == 3, d)
    r = client.get("/api/admin/grammar/units", params={"subject": "proficiency_test"}, headers=adm)
    names = [u["unit"] for u in (r.json().get("units", []) if r.status_code == 200 else [])]
    check("単元一覧は 高校 → 中学・回の数字の順・改は元の回の後",
          names == ["高校英語 習熟度テスト 第1回", "高校英語 習熟度テスト 第1回改1", "高校英語 習熟度テスト 第2回",
                    "高校英語 習熟度テスト 第6回", "高校英語 習熟度テスト 第10回", "中学英語 習熟度テスト 第1回"], names)

    # ------------------------------------------------------------------
    print("\n[12] 自動配信の関数に習熟度テストの名前が出てこない・お知らせ")
    funcs = [mod._run_weakness_drill_routine, mod._weakness_routine_pick_drills, mod._weakness_routine_plan,
             mod._create_routine_grammar_drill, mod.student_today_question_start, mod.student_diagnostic_start,
             mod._self_issued_subject, mod._self_issued_reviewed_ids, mod._auto_pick_reviewed_question_ids,
             mod._auto_pick_reviewed_passages, mod._auto_reviewed_passages]
    # クラス自動宿題 (コミット 11) の関数ができたらここに足す
    for name in ("_run_class_homework_routine", "_class_hw_deliver_group", "_class_hw_plan"):
        if hasattr(mod, name):
            funcs.append(getattr(mod, name))
    hits = [f.__name__ for f in funcs if "proficiency_test" in inspect.getsource(f) or "_PTEST_SUBJECT" in inspect.getsource(f)]
    check("自動配信・自己発行の関数のソースに proficiency_test / _PTEST_SUBJECT が無い (許可リスト方式・禁止は共通部品)", not hits, hits)
    mails = []
    orig_send, orig_sleep = mod._send_message_email, time.sleep
    mod._send_message_email = lambda to, subject, body, student_name=None: (mails.append((subject, body)), {"sent": True})[1]
    time.sleep = lambda s: None
    try:
        with Env(HOMEWORK_NOTIFY_EMAIL=None):   # 既定 = manual (塾長が手で配ったときだけメール)
            res = mod._notify_grammar_drill_assigned([{"id": sb, "name": "架空", "email": "ptest-02@example.org"}], unit, 9,
                                                     "proficiency_test", "manual")
    finally:
        mod._send_message_email, time.sleep = orig_send, orig_sleep
    check("メールの件名「🧪 習熟度テスト「高校英語 習熟度テスト 第1回」が届きました」",
          mails and mails[0][0] == "🧪 習熟度テスト「高校英語 習熟度テスト 第1回」が届きました", mails)
    check("本文に「全9問」と提出は 1 回・「解説がその場で」は書かない",
          mails and "全9問" in mails[0][1] and "提出は1回だけ" in mails[0][1] and "解説がその場で" not in mails[0][1], mails)
    check("LINE は送らない (既定)", res.get("line_ok") == 0 and res.get("channels", {}).get("line") is False, res)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print(f"   - {f}")
        return 1
    print("✅ PASS (習熟度テスト: 1 回分 = 1 本・取込順・同じ生徒に 2 回配らない・弱点と自動配信に入らない)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
