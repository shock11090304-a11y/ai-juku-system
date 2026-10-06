#!/usr/bin/env python3
"""📐 高校数学ドリルの直し (2026-10-06) の回帰テスト: 取込済みの問題を出典で直す同期 API と、弱点ルーティンの数学III 除外。

背景:
  取込 (/api/admin/grammar/import) は INSERT 専用で、取込済みの問題の解説・単元は押し直しても変わらない。
  問題集 675 問を入れた直後のレビューで、重複 23 組・解説の生の記号・単元の付け間違いが見つかったので、
  CEO の 📐 補充ボタンは取込の前に /api/admin/grammar/sync を呼んで本番の行を直す。
  塾長「数学Ⅲは自動配信は外して」→ 弱点ルーティンが数学を科目まるごとで配るときは 数学III の単元を出さない。

固定する性質:
  1. 同期: (subject, source, stem) が一致する行の unit / explanation をシードに合わせる。選択肢は、配信していない問題と、配信済みでも
     正解の文と位置が同じ問題 (誤答の差し替えだけ) は直し、正解が動く配信済みの問題は選択肢も解説も据え置いて kept_choices_delivered に数える。
     並び (表示位置) だけ違うのは書き換えない。source が束ごとの名前の在庫は、問題文なしでは触らない (ambiguous)。
     作り直した問題の旧版は (source, 旧い問題文) で止め、直した版は残る。
     同じ source が 2 行あれば 1 行だけ残して active=0 (deduped)。
     retire_sources は active=0 (行は消さない)。dry_run は数えるだけ。2 回目は何も書き換えない (押し直しても同じ)。
     汎用の source (pool) と知らない source は触らない。認証が無ければ 401。stem は変えない
  2. 同期のあとに取込を押しても、直した問題が二重に入らない (CEO のボタンと同じ順: 同期 → 取込)。
     同期より先に取込だけ押しても (古い CEO タブ)、同じ出典+問題文の行があれば単元が違っても入らない
  3. 弱点ルーティンの数学 (科目まるごと) に 数学III が入らない。数学III を除いて 10 問に足りなければ配信しない (None = 次の弱点へ)。
     数学III の弱点は自動配信の候補にしない (数学の候補にすると毎回選ばれ、ほかの科目の弱点が配られない)。
     CEO の単元指定 (数学III 極限) と科目まるごとの抽出 (除外なし) はこれまでどおり 数学III も出る。英語は変わらない

実行:
    python3 scripts/health_check/test_math_drill_sync.py      # exit 0 = PASS / 1 = FAIL
外部通信は一切しない。DB は一時 SQLite。
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_grammar_import_units import admin_token, check, import_like_ceo, load_main, load_seed, FAILURES, Api  # noqa: E402

SEEDS = ("math_drill_ct_mock_v1.json", "math_drill_workbook_v1.json")


def rows(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    out = [dict(r) for r in c.fetchall()]
    conn.close()
    return out


def execute(mod, sql, params=()):
    conn = mod.db(); c = conn.cursor()
    c.execute(sql, params)
    conn.commit(); conn.close()


def sync(api, body, auth=True):
    api.mod._RATE_LIMIT_STORE.clear()
    r = api.client.post("/api/admin/grammar/sync", json=body, headers=api.headers if auth else {})
    return r.status_code, (r.json() if r.status_code == 200 else {"_text": r.text[:200]})


def sync_like_ceo(api, questions, retire, dry=False):
    """CEO の 📐 ボタンと同じ送り方 (400 問ずつ・止める問題は 1 本目だけ)"""
    tot = {}
    for i in range(0, len(questions), 400):
        part = [{"source": q["source"], "stem": q["stem"], "unit": q["unit"], "explanation": q["explanation"], "choices": q["choices"], "answer": q["answer"]}
                for q in questions[i:i + 400]]
        code, d = sync(api, {"subject": "math", "questions": part, "retire_sources": retire if i == 0 else [], "dry_run": dry})
        tot.setdefault("status", set()).add(code)
        tot.setdefault("ok", set()).add(d.get("ok"))
        for k, v in d.items():
            if isinstance(v, int) and not isinstance(v, bool):
                tot[k] = tot.get(k, 0) + v
    return tot


def main():
    print("📐 高校数学ドリル 同期 API と弱点ルーティンの数学III 除外 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    api = Api(mod, TestClient(mod.app, raise_server_exceptions=False), {"Authorization": "Bearer " + admin_token(mod)})
    seeds = [load_seed(n) for n in SEEDS]
    qs = [q for s in seeds for q in s["questions"]]
    retire = [r for s in seeds for r in ((s.get("_meta") or {}).get("retired_sources") or [])]
    check("シードに本番で止める問題 (retired_sources) がある", len(retire) > 0, f"{len(retire)} 件")

    print("\n[1] 45f53ec で入った状態を作る (シードを入れてから、直す前の状態に戻す)")
    for s, n in zip(seeds, SEEDS):
        t = import_like_ceo(api, "questions", s["questions"], "math", 400)
        check(f"{n}: 全 {len(s['questions'])} 問が入る", t["inserted"] == len(s["questions"]) and t["errors"] == 0, str(t)[:200])
    wb = [q for q in seeds[1]["questions"]]
    by_src = {r["source"]: r for r in rows(mod, "SELECT id, source, unit, explanation, choices, answer, stem FROM grammar_questions WHERE subject = 'math'")}
    # 直す前の状態: 単元違い 2・解説違い 3・選択肢違い 2 (うち 1 問は配信済み)・並びだけ違う 1・止める問題の行 (今は active=1)
    old_unit = {wb[0]["source"]: "数学C 複素数平面", wb[1]["source"]: "数学A 図形の性質"}
    for src, u in old_unit.items():
        execute(mod, "UPDATE grammar_questions SET unit = ? WHERE source = ?", (u, src))
    old_expl = [wb[2]["source"], wb[3]["source"], wb[4]["source"]]
    for src in old_expl:
        execute(mod, "UPDATE grammar_questions SET explanation = ? WHERE source = ?", ("古い解説 3^{-1} √12", src))
    chg = [wb[5], wb[6]]
    # chg[0] = 配信していない問題の誤答が違う → 直る
    q0 = chg[0]; old = list(q0["choices"]); old[(q0["answer"] + 1) % 4] += "（旧）"
    execute(mod, "UPDATE grammar_questions SET choices = ? WHERE source = ?", (json.dumps(old, ensure_ascii=False), q0["source"]))
    # chg[1] = 配信済みで、旧版は正解の位置も違う (誤答も違う) → 据え置き (生徒の解答の番号と食い違う)
    q1 = chg[1]; old = list(q1["choices"]); old[(q1["answer"] + 1) % 4] += "（旧）"; old = old[1:] + old[:1]
    execute(mod, "UPDATE grammar_questions SET choices = ?, answer = ?, explanation = ? WHERE source = ?",
            (json.dumps(old, ensure_ascii=False), (q1["answer"] - 1) % 4, "配信済みの古い解説（古い誤答の説明）", q1["source"]))
    # same_key = 配信済みだが、正解の文と位置は同じで誤答だけ違う (英検 準1級 第8回 Q7 の形) → 配信済みでも直る
    qk = wb[9]; old = list(qk["choices"]); old[(qk["answer"] + 2) % 4] += "（別解になりうる旧い誤答）"
    execute(mod, "UPDATE grammar_questions SET choices = ?, explanation = ? WHERE source = ?",
            (json.dumps(old, ensure_ascii=False), "旧い誤答の解説", qk["source"]))
    # qa = 配信済み・正解の文と位置は同じだが、提出済みの解答が「差し替える誤答」の番号を選んでいる → 据え置き (過去の解答の表示が化ける)
    qa = wb[10]; old = list(qa["choices"]); ci = (qa["answer"] + 1) % 4; old[ci] += "（生徒が選んだ旧い誤答）"
    execute(mod, "UPDATE grammar_questions SET choices = ?, explanation = ? WHERE source = ?",
            (json.dumps(old, ensure_ascii=False), "旧い解説 (選ばれた誤答の説明)", qa["source"]))
    delivered_q = by_src[q1["source"]]
    execute(mod, "INSERT INTO grammar_drills (subject, title, unit, question_ids, created_by) VALUES ('math', 'テスト配信', '数学', ?, 'admin')",
            (json.dumps([delivered_q["id"], by_src[qk["source"]]["id"], by_src[qa["source"]]["id"]]),))
    execute(mod, "INSERT INTO grammar_drill_assignments (drill_id, student_id, status, score_correct, score_total, answers_json) "
                 "VALUES ((SELECT MAX(id) FROM grammar_drills), 1, 'completed', 0, 3, ?)",
            (json.dumps({str(by_src[qa["source"]]["id"]): ci}),))
    reorder = wb[7]
    ch = list(reorder["choices"]); a = reorder["answer"]
    rot = ch[1:] + ch[:1]
    execute(mod, "UPDATE grammar_questions SET choices = ?, answer = ? WHERE source = ?",
            (json.dumps(rot, ensure_ascii=False), rot.index(ch[a]), reorder["source"]))
    for k, src in enumerate(retire):
        execute(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                     "('math', '基礎数学 三角関数', 'basic', ?, ?, 0, '外す前の解説です。テスト用。', ?)",
                (f"外す前の問題 {k}", json.dumps(["a", "b", "c", "d"]), src))
    execute(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                 "('math', '基礎数学 微積', 'standard', '汎用 source の行', ?, 0, 'pool の行。', 'pool')", (json.dumps(["a", "b", "c", "d"]),))
    dupq = wb[8]
    execute(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                 "('math', '数学C 複素数平面', 'standard', ?, ?, ?, ?, ?)",
            (dupq["stem"], json.dumps(dupq["choices"], ensure_ascii=False), dupq["answer"], dupq["explanation"], dupq["source"]))
    print("\n[1b] 同期より先に取込だけ押しても二重に入らない (古い CEO タブ: 単元を直した問題も 同じ出典+問題文 で skip)")
    for s_, n in zip(seeds, SEEDS):
        t = import_like_ceo(api, "questions", s_["questions"], "math", 400)
        check(f"{n}: 新しく入る問題 0", t["inserted"] == 0, str(t)[:200])

    print("\n[2] 認証・dry_run")
    code, _ = sync(api, {"subject": "math", "questions": []}, auth=False)
    check("認証が無ければ 401", code == 401, str(code))
    code, d = sync(api, {"subject": "math", "questions": [], "retire_sources": [], "dry_run": True})
    check("新しい照合の印 match='source+stem' を返す (CEO はこれが無い古いサーバでは同期も取込もしない)", code == 200 and d.get("match") == "source+stem", str(d))
    t = sync_like_ceo(api, qs, retire, dry=True)
    check(f"dry_run は数えるだけ (単元 2・解説 4・選択肢 2・配信済み据え置き 2・二重の行 1・止める {len(retire)})",
          t["status"] == {200} and t["updated_unit"] == 2 and t["updated_explanation"] == 4 and t["updated_choices"] == 2
          and t["kept_choices_delivered"] == 2 and t["deduped"] == 1 and t["retired"] == len(retire), str(t))
    check("dry_run のあとも行は直る前のまま",
          rows(mod, "SELECT unit FROM grammar_questions WHERE source = ?", (wb[0]["source"],))[0]["unit"] == "数学C 複素数平面"
          and rows(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE active = 0")[0]["n"] == 0)

    print("\n[3] 同期 (CEO のボタンと同じ送り方)")
    t = sync_like_ceo(api, qs, retire)
    check("応答: matched = シードの全問・not_found 0・invalid 0",
          t["status"] == {200} and t["ok"] == {True} and t["matched"] == len(qs) and t["not_found"] == 0 and t["invalid"] == 0, str(t))
    check("単元 2・解説 4・選択肢 2 を直し (配信済みでも正解が同じ 1 問を含む)、正解が動く配信済み 1 問は選択肢も解説も据え置き・二重の行 1・retired を止める",
          t["updated_unit"] == 2 and t["updated_explanation"] == 4 and t["updated_choices"] == 2
          and t["kept_choices_delivered"] == 2 and t["deduped"] == 1 and t["multi_rows"] == 1 and t["retired"] == len(retire), str(t))
    now = {r["source"]: r for r in rows(mod, "SELECT source, unit, explanation, choices, answer, stem, active FROM grammar_questions "
                                         "WHERE subject = 'math' ORDER BY active ASC, id DESC")}   # 同じ source が 2 行なら active の行を後に読む
    check("単元がシードどおりに戻る", all(now[s]["unit"] == next(q["unit"] for q in wb if q["source"] == s) for s in old_unit))
    check("解説がシードどおりに戻る", all(now[s]["explanation"] == next(q["explanation"] for q in wb if q["source"] == s) for s in old_expl))
    c0 = chg[0]
    check("配信していない問題の選択肢はシードどおり", json.loads(now[c0["source"]]["choices"]) == c0["choices"] and now[c0["source"]]["answer"] == c0["answer"])
    check("配信済みで正解の位置が動く問題の選択肢は据え置き (生徒の解答の番号と食い違わない)", "（旧）" in now[chg[1]["source"]]["choices"])
    check("配信済みで、提出済みの解答が選んだ番号の誤答が変わる問題は据え置き (過去の解答が別の文に化けない)",
          "（生徒が選んだ旧い誤答）" in now[qa["source"]]["choices"] and now[qa["source"]]["explanation"] == "旧い解説 (選ばれた誤答の説明)")
    check("配信済みでも正解の文と位置が同じ問題は、誤答と解説を直す (採点は変わらない)",
          json.loads(now[qk["source"]]["choices"]) == qk["choices"] and now[qk["source"]]["explanation"] == qk["explanation"])
    check("配信済みで選択肢を据え置いた問題は解説も据え置き (【よくある誤り】が画面の誤答と食い違わない)",
          now[chg[1]["source"]]["explanation"] == "配信済みの古い解説（古い誤答の説明）")
    dup_rows = rows(mod, "SELECT id, unit, active FROM grammar_questions WHERE source = ? ORDER BY id", (dupq["source"],))
    check("二重に入った行は 1 つだけ active (id の小さい元の行) で、単元はシードどおり",
          [r_["active"] for r_ in dup_rows] == [1, 0] and dup_rows[0]["unit"] == dupq["unit"], str(dup_rows))
    check("並びだけ違う問題は書き換えない", json.loads(now[reorder["source"]]["choices"]) == rot)
    check("止める問題は active=0 (行は残る)", all(now[s]["active"] == 0 for s in retire) and len([s for s in retire if s in now]) == len(retire))
    check("汎用 source (pool) の行は触らない", now["pool"]["unit"] == "基礎数学 微積" and now["pool"]["active"] == 1)
    check("stem は変わらない", all(now[q["source"]]["stem"] == q["stem"] for q in qs))
    t2 = sync_like_ceo(api, qs, retire)
    check("2 回目は何も書き換えない (押し直しても同じ)",
          t2["updated_unit"] == t2["updated_explanation"] == t2["updated_choices"] == t2["retired"] == t2["deduped"] == 0
          and t2["already_retired"] == len(retire) and t2["kept_choices_delivered"] == 2, str(t2))
    code, d = sync(api, {"subject": "math", "questions": [{"source": "pool", "unit": "基礎数学 微積", "explanation": "x"}],
                         "retire_sources": ["pool", "mathwb-no-such"]})
    check("汎用 source は invalid・知らない source は not_found に数えるだけ",
          code == 200 and d["invalid"] == 2 and d["retire_not_found"] == 1 and d["retired"] == 0, str(d))

    print("\n[4] 同期のあとに取込 (CEO のボタンの 2 段目)")
    n_before = rows(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'math'")[0]["n"]
    for s, n in zip(seeds, SEEDS):
        t = import_like_ceo(api, "questions", s["questions"], "math", 400)
        check(f"{n}: 全部 skip (直した問題が二重に入らない)", t["inserted"] == 0 and t["skipped"] == len(s["questions"]), str(t)[:200])
    check("行数は変わらない", rows(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'math'")[0]["n"] == n_before)

    print("\n[5] 弱点ルーティンの数学 (科目まるごと) に 数学III が入らない")
    lv = ["standard", "advanced"]
    n3 = rows(mod, "SELECT COUNT(*) AS n FROM grammar_questions WHERE subject = 'math' AND active = 1 AND unit LIKE '数学III%' "
                   "AND level IN ('standard', 'advanced')")[0]["n"]
    check("在庫に標準・やや難の 数学III がある (このテストが意味を持つ)", n3 >= 10, str(n3))
    execute(mod, "INSERT INTO students (name, email, status, grade) VALUES ('テスト 文系', 'routine-test@example.invalid', 'paid', '高校3年')")
    sid = rows(mod, "SELECT id FROM students WHERE email = 'routine-test@example.invalid'")[0]["id"]
    st = {"name": "テスト 文系", "email": "routine-test@example.invalid", "line_user_id": None}
    units_seen = set()
    for _ in range(40):
        conn = mod.db(); c = conn.cursor()
        r = mod._create_routine_grammar_drill(c, conn, "math", "", 10, sid, st)
        conn.close()
        if not r:
            break
        d = rows(mod, "SELECT question_ids FROM grammar_drills WHERE created_by = ? ORDER BY id DESC LIMIT 1", (mod._WEAKNESS_ROUTINE_CREATED_BY,))[0]
        ids = json.loads(d["question_ids"])
        units_seen |= {x["unit"] for x in rows(mod, f"SELECT unit FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))}
    check("40 回配っても 数学III の単元が 1 問も入らない", units_seen and not any(u.startswith("数学III") for u in units_seen),
          f"{len(units_seen)} 単元: {sorted(u for u in units_seen if u.startswith('数学III'))}")
    conn = mod.db(); c = conn.cursor()
    unit3 = mod._grammar_pick_drill_question_ids(c, "math", "数学III 極限", False, ["basic", "standard", "advanced"], 5, None,
                                                  mod._ROUTINE_SUBJECT_LEVEL_EXCLUDE_UNIT_PREFIXES["math"])
    check("単元を指定した抽出 (CEO で 数学III 極限 を選ぶ) は除外の影響を受けない", len(unit3) == 5, str(len(unit3)))
    random.seed(0)
    whole = set()
    for _ in range(30):
        ids = mod._grammar_pick_drill_question_ids(c, "math", "", True, lv, 30, None)
        if ids:
            c.execute(f"SELECT unit FROM grammar_questions WHERE id IN ({','.join('?' * len(ids))})", tuple(ids))
            whole |= {r["unit"] for r in c.fetchall()}
    conn.close()
    check("除外を渡さない科目まるごとの抽出 (CEO の 📨 弱点ドリル) は 数学III も出る", any(u.startswith("数学III") for u in whole))
    # 数学III しか無い科目プールでは配信しない (数学III で埋めない)
    execute(mod, "UPDATE grammar_questions SET active = 0 WHERE subject = 'math' AND unit NOT LIKE '数学III%'")
    conn = mod.db(); c = conn.cursor()
    r = mod._create_routine_grammar_drill(c, conn, "math", "", 10, sid, st)
    conn.close()
    check("数学III しか残っていなければ配信しない (在庫不足 = None)", r is None, str(r)[:100])
    check("除外の表は数学だけ (英語などの自動配信は変わらない)", set(mod._ROUTINE_SUBJECT_LEVEL_EXCLUDE_UNIT_PREFIXES) == {"math"})
    print("\n[6] 数学III の弱点は自動配信の候補にしない (数学の候補が数III の弱点で毎回選ばれ、ほかの科目が配られなくなるのを防ぐ)")
    execute(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) VALUES (?, 'math', '数学III 微分法', 10, 0.1, 10)", (sid,))
    execute(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) VALUES (?, 'english', '時制の一致', 10, 0.4, 10)", (sid,))
    conn = mod.db(); c = conn.cursor()
    picks = mod._weakness_routine_pick_drills(c, sid)
    conn.close()
    check("数学III の弱点 (正答 10%) より軽い英語の弱点が選ばれ、数学は候補に入らない",
          [p_["subject"] for p_ in picks] == ["english"], str(picks))
    execute(mod, "INSERT INTO student_weakness (student_id, subject, topic, question_count, qa_accuracy, qa_attempts) VALUES (?, 'math', '基礎数学 二次関数', 10, 0.5, 10)", (sid,))
    conn = mod.db(); c = conn.cursor()
    picks = mod._weakness_routine_pick_drills(c, sid)
    conn.close()
    check("数学III 以外の数学の弱点があれば数学 (科目まるごと) も候補に入る", {"math", "english"} <= {p_["subject"] for p_ in picks}, str(picks))

    print("\n[7] source が束ごとの名前の在庫 (英文法の manual-drill-v1 など) は、問題文なしの同期・取り外しで触らない")
    for k in range(3):
        execute(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                     "('english', '時制', 'standard', ?, ?, 0, 'もとの解説', 'manual-drill-v1')", (f"束の問題 {k}", json.dumps(["a", "b", "c", "d"])))
    code, d = sync(api, {"subject": "english", "questions": [{"source": "manual-drill-v1", "unit": "時制", "explanation": "上書き"}],
                         "retire_sources": ["manual-drill-v1"]})
    eng = rows(mod, "SELECT explanation, active FROM grammar_questions WHERE source = 'manual-drill-v1'")
    check("問題文なしで送ると ambiguous に数えて書き換えも取り外しもしない",
          code == 200 and d["ambiguous"] == 2 and all(r_["explanation"] == "もとの解説" and r_["active"] == 1 for r_ in eng), str(d))
    code, d = sync(api, {"subject": "english", "questions": [{"source": "manual-drill-v1", "stem": "束の問題 1", "unit": "時制", "explanation": "直した解説"}]})
    eng = {r_["stem"]: r_ for r_ in rows(mod, "SELECT stem, explanation FROM grammar_questions WHERE source = 'manual-drill-v1'")}
    check("問題文つきなら、その 1 問だけ直す",
          d["updated_explanation"] == 1 and eng["束の問題 1"]["explanation"] == "直した解説"
          and eng["束の問題 0"]["explanation"] == eng["束の問題 2"]["explanation"] == "もとの解説", str(d))
    print("\n[8] 作り直した問題の旧版だけを (source, 旧い問題文) で止める (英検 準1級 第7回 Q18 の形)")
    for st in ("旧い問題文 (   ).", "直した問題文 (   )."):
        execute(mod, "INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES "
                     "('eiken', '準1級 単語', 'standard', ?, ?, 0, '解説', 'eikenp1-test-18')", (st, json.dumps(["a", "b", "c", "d"])))
    code, d = sync(api, {"subject": "eiken", "questions": [], "retire_sources": ["eikenp1-test-18"]})
    check("source だけで止めようとしても、問題文の違う生きている行が 2 つなら止めない", d.get("ambiguous") == 1 and d.get("retired") == 0, str(d))
    code, d = sync(api, {"subject": "eiken", "questions": [], "retire_sources": [{"source": "eikenp1-test-18", "stem": "旧い問題文 (   )."}]})
    ek = {r_["stem"]: r_["active"] for r_ in rows(mod, "SELECT stem, active FROM grammar_questions WHERE source = 'eikenp1-test-18'")}
    check("(source, 旧い問題文) なら旧版だけ active=0、直した版は残る", d.get("retired") == 1 and ek == {"旧い問題文 (   ).": 0, "直した問題文 (   ).": 1}, str(ek))

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件")
        for f in FAILURES:
            print("  -", f)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
