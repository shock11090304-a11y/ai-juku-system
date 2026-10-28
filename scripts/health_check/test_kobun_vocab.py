#!/usr/bin/env python3
"""📜 AI 単語帳の古文 (2026-10-28) の回帰テスト (in-process・一時 SQLite)。

守ること:
  A. データ: server/kobun_vocab_v1.json が scripts/kobun_vocab/ の正本から作り直したものと一致し、
     語ごとに誤答 3 つ (正解と別・正解の語の意味と重ならない) がそろっている
  B. 古文の API (subject=kobun): 初回に DB の行が JSON に合わせて入る・出題は古文の語だけ・
     選択肢は「正解 + 固定の誤答 3 つ」・回答後の補足 (漢字・ほかの意味・メモ) が付く・統計/間違えた単語は古文だけ
  C. 英語の API (subject 省略): 古文の行を出題にも誤答の候補にも統計にも入れない (古文を入れる前と同じ値)
  D. JSON を直して再起動したら、DB の古文の行も直る (同期は 1 プロセス 1 回)。後から足した基礎の語も基礎→標準→難関の順で出る
  E. 画面の配線: kobun.html が data-subject="kobun" で vocab.js を読み、vocab.js が subject を送る
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
sys.path.insert(0, os.path.join(REPO, "server"))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="kobun_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb, "DATABASE_URL": "", "STRIPE_SECRET_KEY": "", "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0", "EXAM_QUESTIONS_ENABLED": "0", "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_kobun", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def main():
    print("📜 AI 古文単語 回帰テスト\n")

    print("A. データ")
    r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "kobun_vocab", "build.py"), "--check"],
                       capture_output=True, text=True)
    check("build.py --check (正本と一致・機械検査 0 件)", r.returncode == 0, (r.stdout + r.stderr)[-600:])
    data = json.load(open(os.path.join(REPO, "server", "kobun_vocab_v1.json"), encoding="utf-8"))
    words = data["words"]
    check("300 語以上ある", len(words) >= 300, len(words))
    check("レベルは基礎・標準・難関の 3 つ", {w["level"] for w in words} == {"kobun_kiso", "kobun_hyojun", "kobun_nankan"})
    bad = [w["word"] for w in words if len(set(w["distractors"])) != 3 or w["meaning_jp"] in w["distractors"]]
    check("全語に正解と別の誤答が 3 つ", not bad, bad[:5])
    byw = {w["word"]: w for w in words}
    check("出題時の見出しは括弧の漢字を外す (かる（離る）→ かる)・たまふの四段/下二段だけ残す",
          byw["かる（離る）"]["display"] == "かる" and byw["たまふ（四段）"]["display"] == "たまふ（四段）"
          and all("（" not in w["display"] for w in words if not w["word"].startswith("たまふ")))
    order = [w["level"] for w in words]
    check("並びは基礎→標準→難関 (初回の取込はこの順)",
          order == sorted(order, key=["kobun_kiso", "kobun_hyojun", "kobun_nankan"].index))

    mod = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app)
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO students (name, email, grade, goal) VALUES (?,?,?,?)", ("テスト 生徒", "kobun@example.invalid", "高3", "x"))
    conn.commit()
    c.execute("SELECT id FROM students WHERE email=?", ("kobun@example.invalid",))
    sid = c.fetchone()[0]
    # 英単語 4 語 (うち 1 語は復習期限切れの進捗あり)
    for w, pos, m in (("abandon", "verb", "〜を捨てる"), ("acquire", "verb", "〜を得る"),
                      ("adapt", "verb", "適応する"), ("adopt", "verb", "〜を採用する")):
        c.execute("INSERT INTO vocab_words (word, pos, meaning_jp, level) VALUES (?,?,?,?)", (w, pos, m, "eiken_g2"))
    c.execute("SELECT id FROM vocab_words WHERE word='abandon'")
    eng_id = c.fetchone()[0]
    c.execute("INSERT INTO vocab_progress (student_id, word_id, box, next_review_at, review_count, correct_count) "
              "VALUES (?,?,?,?,?,?)", (sid, eng_id, 1, "2000-01-01T00:00:00+00:00", 2, 1))
    conn.commit(); conn.close()
    H = {"Authorization": "Bearer " + mod._sign_session_token(sid)}

    print("C. 英語の API (古文を入れる前の値)")
    before = client.get("/api/vocab/stats", headers=H).json()
    check("英語の総語数は 4", before.get("total_words_in_pool") == 4, before)
    check("英語の応答は subject=eng", before.get("subject") == "eng", before)

    print("B. 古文の API")
    st = client.get("/api/vocab/stats?subject=kobun", headers=H).json()
    check("初回の古文 API で JSON の全語が DB に入る", st.get("total_words_in_pool") == len(words), st)
    check("古文の応答は subject=kobun (画面はこれが無いと準備中と出す)", st.get("subject") == "kobun", st)
    check("古文の進捗はまだ 0", st.get("due_now") == 0 and st.get("mistakes_count") == 0, st)
    q = client.get("/api/vocab/quiz?subject=kobun&limit=20", headers=H).json()["quiz"]
    byword = {w["word"]: w for w in words}
    check("出題は 20 問・すべて古文の語", len(q) == 20 and all(x["word"] in byword for x in q), [x["word"] for x in q][:5])
    check("新しい語は基礎から出る", all(x["level"] == "kobun_kiso" for x in q), {x["level"] for x in q})
    ok_choices = all(sorted(x["choices"]) == sorted([byword[x["word"]]["meaning_jp"]] + byword[x["word"]]["distractors"])
                     and x["choices"][x["correct_index"]] == byword[x["word"]]["meaning_jp"] for x in q)
    check("選択肢 = 正解 + その語の固定の誤答 3 つ・correct_index が正解を指す", ok_choices)
    check("回答後の補足 (note・kanji・other_meanings・例文) と出題時の見出し (display) が付く",
          all("note" in x and "kanji" in x and "other_meanings" in x and x["example_en"] and x.get("display") for x in q))
    lv = client.get("/api/vocab/quiz?subject=kobun&level=kobun_nankan&limit=5", headers=H).json()["quiz"]
    check("レベル指定 (難関) はその語だけ", lv and all(x["level"] == "kobun_nankan" for x in lv), [x["level"] for x in lv])
    lv2 = client.get("/api/vocab/quiz?level=kobun_hyojun&limit=5", headers=H).json()["quiz"]
    check("level が kobun_ なら subject 省略でも古文", lv2 and all(x["level"] == "kobun_hyojun" for x in lv2))

    # 古文で 1 問まちがえる → 間違えた単語・統計は古文だけに出る
    kid = q[0]["id"]
    g = client.post("/api/vocab/grade", json={"word_id": kid, "knew": False}, headers=H)
    check("古文の語も同じ採点 API で記録できる", g.status_code == 200 and g.json().get("ok"), g.text[:200])
    mk = client.get("/api/vocab/mistaken-words?subject=kobun", headers=H).json()["items"]
    check("古文の間違えた単語は古文の語だけ (補足付き)", [x["word"] for x in mk] == [q[0]["word"]] and "note" in mk[0], mk)
    st2 = client.get("/api/vocab/stats?subject=kobun", headers=H).json()
    check("古文の統計に古文の進捗が数えられる", st2.get("mistakes_count") == 1 and st2.get("total_reviews") == 1, st2)
    mo = client.get("/api/vocab/quiz?subject=kobun&mistakes_only=1", headers=H).json()["quiz"]
    check("古文の「間違えた単語だけ」は古文の語", [x["word"] for x in mo] == [q[0]["word"]], [x["word"] for x in mo])

    print("C. 英語の API (古文を入れた後)")
    after = client.get("/api/vocab/stats", headers=H).json()
    same = {k: after.get(k) for k in ("total_words_in_pool", "due_now", "mistakes_count", "total_reviews", "by_box")} == \
           {k: before.get(k) for k in ("total_words_in_pool", "due_now", "mistakes_count", "total_reviews", "by_box")}
    check("英語の統計は古文を入れる前と同じ (古文の語・進捗を数えない)", same, (before, after))
    eq = client.get("/api/vocab/quiz?limit=20", headers=H).json()["quiz"]
    kob_means = {w["meaning_jp"] for w in words} | {d for w in words for d in w["distractors"]}
    check("英語の出題に古文の語が出ない", eq and all(not x["level"].startswith("kobun_") for x in eq), [x["word"] for x in eq])
    check("英語の 4 択に古文の意味が混ざらない (誤答が足りないときの全レベルからの補充も英語だけ)",
          all(not (set(x["choices"]) & kob_means) for x in eq), [x["choices"] for x in eq])
    em = client.get("/api/vocab/mistaken-words", headers=H).json()["items"]
    check("英語の間違えた単語に古文の語が出ない", [x["word"] for x in em] == ["abandon"], [x["word"] for x in em])
    eqm = client.get("/api/vocab/quiz?mistakes_only=1", headers=H).json()["quiz"]
    check("英語の「間違えた単語だけ」に古文の語が出ない", [x["word"] for x in eqm] == ["abandon"], [x["word"] for x in eqm])
    qu = client.get("/api/vocab/queue?limit=50", headers=H).json()["queue"]
    check("英語の queue に古文の語が出ない", qu and all(not x["level"].startswith("kobun_") for x in qu))
    check("認証なしは 401 のまま", client.get("/api/vocab/stats?subject=kobun").status_code == 401)

    print("D. JSON を直したら DB も直る")
    target = words[0]["word"]
    mod._KOBUN_VOCAB[target] = dict(mod._KOBUN_VOCAB[target], meaning_jp="(テストで書き換えた意味)")
    mod._KOBUN_SYNC.update({"done": False, "tried_at": 0.0})
    client.get("/api/vocab/stats?subject=kobun", headers=H)
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT meaning_jp, COUNT(*) FROM vocab_words WHERE word=? GROUP BY meaning_jp", (target,))
    rows = c.fetchall(); conn.close()
    check("変わった語は UPDATE (行は増えない)", len(rows) == 1 and rows[0][0] == "(テストで書き換えた意味)" and rows[0][1] == 1, rows)

    # JSON から外した語: 進捗 (間違えた・期限切れ) があっても、古文の出題・統計・間違えた単語に残らない
    gone = q[0]["word"]  # B で 1 回まちがえた語
    conn = mod.db(); c = conn.cursor()
    c.execute("UPDATE vocab_progress SET next_review_at=? WHERE student_id=?", ("2000-01-01T00:00:00+00:00", sid))
    conn.commit(); conn.close()
    saved = mod._KOBUN_VOCAB.pop(gone)
    mod._KOBUN_SYNC.update({"done": False, "tried_at": 0.0})
    st3 = client.get("/api/vocab/stats?subject=kobun", headers=H).json()
    check("外した語は古文の総語数・今日の復習・間違えた単語の数から外れる",
          st3.get("total_words_in_pool") == len(words) - 1 and st3.get("due_now") == 0 and st3.get("mistakes_count") == 0, st3)
    q3 = client.get("/api/vocab/quiz?subject=kobun&limit=20", headers=H).json()["quiz"]
    check("外した語は出題されず、出題の窓も埋めない (20 問出る)", len(q3) == 20 and gone not in [x["word"] for x in q3], len(q3))
    check("外した語は古文の間違えた単語に出ない", client.get("/api/vocab/mistaken-words?subject=kobun", headers=H).json()["items"] == [])
    check("外した語は英語にも混ざらない", gone not in [x["word"] for x in client.get("/api/vocab/quiz?limit=50", headers=H).json()["quiz"]])
    mod._KOBUN_VOCAB[gone] = saved
    mod._KOBUN_SYNC.update({"done": False, "tried_at": 0.0})
    st4 = client.get("/api/vocab/stats?subject=kobun", headers=H).json()
    check("JSON に戻せば元のレベルに戻り、進捗も戻る", st4.get("total_words_in_pool") == len(words) and st4.get("mistakes_count") == 1, st4)

    # 後から足した基礎の語 (id が大きい) は、先に入っている標準・難関の語より先に出る
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO students (name, email, grade, goal) VALUES (?,?,?,?)", ("テスト 生徒2", "kobun2@example.invalid", "高3", "x"))
    c.execute("SELECT id FROM students WHERE email=?", ("kobun2@example.invalid",))
    sid2 = c.fetchone()[0]
    c.execute("INSERT INTO vocab_words (word, pos, meaning_jp, level, tags) VALUES (?,?,?,?,?)",
              ("（後から足した基礎の語）", "名詞", "テスト", "kobun_kiso", "kobun"))
    c.execute("SELECT id FROM vocab_words WHERE word=?", ("（後から足した基礎の語）",))
    late_id = c.fetchone()[0]
    c.execute("SELECT id FROM vocab_words WHERE level='kobun_kiso' AND id<>?", (late_id,))
    for (wid,) in c.fetchall():  # ほかの基礎の語は学習済み (期限はずっと先)
        c.execute("INSERT INTO vocab_progress (student_id, word_id, box, next_review_at, review_count, correct_count) "
                  "VALUES (?,?,?,?,?,?)", (sid2, wid, 3, "2999-01-01T00:00:00+00:00", 1, 1))
    conn.commit(); conn.close()
    H2 = {"Authorization": "Bearer " + mod._sign_session_token(sid2)}
    q5 = client.get("/api/vocab/queue?subject=kobun&limit=3", headers=H2).json()["queue"]
    check("後から足した基礎の語は、先に入っている標準・難関の語より先に出る",
          [x["word"] for x in q5][:1] == ["（後から足した基礎の語）"] and [x["level"] for x in q5][1:] == ["kobun_hyojun"] * 2,
          [(x["word"], x["level"]) for x in q5])

    print("E. 画面の配線")
    kh = open(os.path.join(REPO, "kobun.html"), encoding="utf-8").read()
    vj = open(os.path.join(REPO, "vocab.js"), encoding="utf-8").read()
    mp = open(os.path.join(REPO, "mypage.html"), encoding="utf-8").read()
    check("kobun.html は data-subject=\"kobun\" で vocab.js を読む", 'data-subject="kobun"' in kh and "vocab.js?v=" in kh)
    check("kobun.html と vocab.html は同じ ?v= の vocab.js を読む",
          kh.split("vocab.js?v=")[1].split('"')[0] == open(os.path.join(REPO, "vocab.html"), encoding="utf-8").read().split("vocab.js?v=")[1].split('"')[0])
    check("kobun.html に回答後の補足欄 (vcCardNote) がある", 'id="vcCardNote"' in kh)
    check("vocab.js は古文のとき subject=kobun を送る", "params.set('subject', 'kobun')" in vj and "&subject=kobun" in vj)
    check("vocab.js は読み上げボタンが無い画面でも落ちない", "if (speakBtn)" in vj and "if (speakExBtn)" in vj)
    check("mypage に AI 古文単語の入口と復習の欄がある", 'href="kobun.html"' in mp and "renderKobunSrsWidget('kobunSrsWidget'" in mp)
    check("mypage の古文は高校生だけ (中学生・小学生は入口も復習欄も出さない)",
          "if (_ajMode === 'kosei') renderKobunSrsWidget(" in mp and "getElementById('kobunMenuCard'); if (_kc) _kc.style.display = 'none'" in mp)
    check("古文の画面は subject=kobun の無い応答を使わない (サーバ未反映の間に英単語を出さない)",
          "function kobunNotReady(data)" in vj and vj.count("kobunNotReady(") >= 4 and "d.subject !== 'kobun'" in mp)
    check("出題時は display を出す", "textContent = w.display || w.word" in vj)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 件失敗")
        sys.exit(1)
    print("✅ すべて通過")


if __name__ == "__main__":
    main()
