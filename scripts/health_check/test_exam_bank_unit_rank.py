#!/usr/bin/env python3
"""🎯 公開 bank (GET /api/exam-questions/bank) の topic 窓を単元タグ優先にする — 回帰テスト。

背景 (2026-10-05 scripts/kosei_dojo/eibunpo_v2/kosei_baseline.py の基準取り):
  topic 指定時の bank は `question_data LIKE '%<topic>%' ORDER BY created_at DESC LIMIT <limit>` だった。
  単元別カード (dojo-drill.html UNIT_PRESETS・limit は min(50, agg*8)) の多くで、この窓が「topic に言及するだけの行」や
  古い AI 生成行で満杯 (助動詞・日本史 古代・世界史 古代/中世/近代・生物 植生・物理基礎 運動/波・化学基礎 酸化還元 50/50、数列 48/48)。
  画面は unitExact (小問 unit の接頭辞が filter で始まる) で捨てるので、実際に出る問題は窓より少なく、
  新しい手作り行を足すと古い単元タグ行が窓から押し出されていた。

固定する性質:
  1. 小問の unit 接頭辞 (「(」「（」「:」「：」より前・前後の空白を除く) が topic で始まる行が、より新しい未タグ行より先に並ぶ。
     同じ組の中は新しい順 (同時刻は id の大きい順)。窓 (limit) より古い単元タグ行も、多めに取る範囲 (_BANK_TOPIC_OVERFETCH) の中なら拾う
  2. 接頭辞の規則は画面の unitExact と同じ (「熱力学」は「力学」に数えない・全角コロン/全角括弧・前の空白・
     大問の中の 1 小問だけタグでも先頭組)。dojo-drill.html の規則の文字列もソースで照合する
  3. topic に当たる行が 0 件なら従来どおりプール全体の新しい順 (fallback・並べ替えない)。topic なしも従来どおり
  4. limit を守る (all は limit 行まで・limit は 50 で頭打ち)。多めに取るのは従来の窓 (新しい順 limit 行) が満杯のときだけ・
     _BANK_TOPIC_OVERFETCH 行 (1000 以下) まで・1 行 _BANK_TOPIC_OVERFETCH_MAX_CHARS 文字以下の行だけ
     (公開 API で図つきの大きな行を何百行も読まされない。窓の中の大きな行は従来どおり出る)
  5. _matches_topic の後段フィルタは残る (設問・解説に topic が無く本文だけで LIKE に当たった行は落ちる)。
     eiken_grade の絞り込み・eiken_grade 無しの経路も同じ並び

実行:
    python3 scripts/health_check/test_exam_bank_unit_rank.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import importlib.util
import json
import os
import re
import sqlite3
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
DOJO_HTML = os.path.join(REPO, "dojo-drill.html")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="bankrank_"), "test.db")
    os.environ.update({
        "DB_PATH": tmpdb,
        # ★DATABASE_URL を空にしないと **本番 Postgres** を読む (USE_POSTGRES はこれで決まる)
        "DATABASE_URL": "",
        "STRIPE_SECRET_KEY": "",
        "MONITORING_ENABLED": "0",
        "POST_DEPLOY_SMOKE_ENABLED": "0",
        # 補充 (AI 生成) を起こさない
        "EXAM_QUESTIONS_ENABLED": "0",
        "RESEND_API_KEY": "",
        "BASE_URL": "https://example.invalid",
    })
    spec = importlib.util.spec_from_file_location("aijuku_main_bankrank", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod, tmpdb


class Pool:
    """exam_questions に行を直接入れる (created_at を明示して並びを決める)。"""
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.n = 0

    def add(self, part, grade, questions, exam="daigaku", passage="", ts=None):
        self.n += 1
        ts = ts or f"2026-01-01 00:00:{self.n % 60:02d}"
        cur = self.conn.execute(
            "INSERT INTO exam_questions (exam_id, part_key, eiken_grade, question_data, model, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (exam, part, grade, json.dumps({"passage": passage, "questions": questions}, ensure_ascii=False), "test", ts))
        self.conn.commit()
        return cur.lastrowid


def q(unit, expl, stem="( ) に入るもの"):
    return {"stem": stem, "choices": ["a", "b", "c", "d"], "answer": 0, "unit": unit, "explanation": expl}


def ts(day, i):
    """day 日目の i 秒目 (同じ日の中で i が大きいほど新しい)。"""
    return f"2026-{(day // 28) + 1:02d}-{(day % 28) + 1:02d} {i // 3600:02d}:{(i // 60) % 60:02d}:{i % 60:02d}"


def main():
    print("🎯 bank の topic 窓 (単元タグ優先) 回帰テスト\n")
    mod, tmpdb = load_main()
    from fastapi.testclient import TestClient
    client = TestClient(mod.app, raise_server_exceptions=False)
    pool = Pool(tmpdb)

    # bank が流した SQL を記録する (多めに取る 2 本目のクエリが要るときだけ走ることを見る)
    sqls = []
    _orig_db = mod.db

    class _SpyCur:
        def __init__(self, cur): self._cur = cur
        def execute(self, sql, *a, **k):
            sqls.append(sql)
            return self._cur.execute(sql, *a, **k)
        def __getattr__(self, n): return getattr(self._cur, n)

    class _SpyConn:
        def __init__(self, conn): self._conn = conn
        def cursor(self): return _SpyCur(self._conn.cursor())
        def __getattr__(self, n): return getattr(self._conn, n)

    mod.db = lambda: _SpyConn(_orig_db())

    def overfetched():
        return sum(1 for x in sqls if "length(question_data)" in x)

    def bank(**params):
        del sqls[:]
        mod._RATE_LIMIT_STORE.clear()
        r = client.get("/api/exam-questions/bank", params=params)
        return r.status_code, (r.json() if r.status_code == 200 else {"_text": r.text[:200]})

    def ids(d):
        return [it.get("_question_id") for it in (d.get("all") or [])]

    OVER = getattr(mod, "_BANK_TOPIC_OVERFETCH", None)
    check("多めに取る行数 _BANK_TOPIC_OVERFETCH が limit の上限 (50) より大きい", isinstance(OVER, int) and OVER > 50, repr(OVER))

    # ── [1] タグ付きの古い行が、新しい未タグ行に勝つ ─────────────────────────────
    print("\n[1] 単元タグの古い行 5 本 vs 新しい未タグ行 60 本 (topic=助動詞・limit=50)")
    tagged = [pool.add("r_grammar", "teiki", [q("助動詞(may)", f"【単元】助動詞(may)。古い手作り {i}")], ts=ts(10, i)) for i in range(5)]
    untagged = [pool.add("r_grammar", "teiki", [q("語法(say)", f"助動詞ではなく語法の問題 {i}")], ts=ts(40, i)) for i in range(60)]
    # 別の grade の単元タグ行 (最も新しい) は混ざらない
    other_grade = pool.add("r_grammar", "kyotsu", [q("助動詞(must)", "【単元】助動詞(must)。")], ts=ts(80, 0))
    c0 = pool.conn.execute(
        "SELECT id FROM exam_questions WHERE exam_id='daigaku' AND part_key='r_grammar' AND eiken_grade='teiki' "
        "AND question_data LIKE '%助動詞%' ORDER BY created_at DESC LIMIT 50").fetchall()
    check("前提: 従来の窓 (新しい順 50 行) には単元タグ行が 1 本も入らない", not (set(tagged) & {r[0] for r in c0}))
    code, d = bank(exam="daigaku", part="r_grammar", eiken_grade="teiki", topic="助動詞", limit=50)
    got = ids(d)
    check("200 で返り all は 50 行", code == 200 and len(got) == 50, f"{code} {len(got)}")
    check("先頭 5 行が単元タグ行 (新しい順)", got[:5] == list(reversed(tagged)), f"{got[:5]} vs {list(reversed(tagged))}")
    check("残り 45 行は未タグ行の新しい順 45 本", got[5:] == list(reversed(untagged))[:45])
    check("別の eiken_grade の行は入らない", other_grade not in got)
    # 画面の pref (`String(u == null ? '' : u).split(/[（(：:]/)[0].trim()`) の写し
    pref = lambda u: re.split(r"[（(：:]", "" if u is None else str(u))[0].strip()
    exact = [x for it in d.get("all") or [] for x in it.get("questions") or [] if pref(x.get("unit")).startswith("助動詞")]
    check("画面の unitExact で残る小問が 5 問 (従来は 0 問)", len(exact) == 5, str(len(exact)))
    check("count / selected は窓の中から (count=50)", d.get("count") == 50 and (d.get("selected") or {}).get("_question_id") in got)
    check("窓が満杯なので多めに取る 2 本目のクエリが 1 回走る", overfetched() == 1, str(sqls))
    code, d = bank(exam="daigaku", part="r_grammar", eiken_grade="teiki", topic=" 助動詞　", limit=50)
    check("前後に空白のある topic でも同じ並び (LIKE と同じく前後を削った topic で判定)", ids(d)[:5] == list(reversed(tagged)), f"{ids(d)[:5]}")
    code, d = bank(exam="daigaku", part="r_grammar", topic="助動詞", limit=50)
    got = ids(d)
    check("eiken_grade を渡さない経路も多めに取って並べる (別 grade のタグ行 → 単元タグ行 5 → 未タグ行 44)",
          got == [other_grade] + list(reversed(tagged)) + list(reversed(untagged))[:44], f"{got[:7]} … ({len(got)} 行)")

    # ── [2] 接頭辞の規則 = 画面の unitExact ───────────────────────────────────
    print("\n[2] 接頭辞の規則 (topic=力学・limit=5)")
    netsu = [pool.add("phys_kyotsu", "kyotsu_rikei", exam="rikei", questions=[q("熱力学(気体の状態変化)", f"熱力学は力学ではない {i}")], ts=ts(50, i)) for i in range(10)]
    t_colon = pool.add("phys_kyotsu", "kyotsu_rikei", exam="rikei", questions=[q("力学：運動方程式", "力学の基本")], ts=ts(20, 1))
    t_space = pool.add("phys_kyotsu", "kyotsu_rikei", exam="rikei", questions=[q("　力学（円運動）", "力学の円運動")], ts=ts(20, 2))
    t_mixed = pool.add("phys_kyotsu", "kyotsu_rikei", exam="rikei", questions=[q("電磁気(コンデンサー)", "力学ではなく電磁気"), q("力学(剛体)", "剛体のつり合い")], ts=ts(20, 3))
    no_unit = pool.add("phys_kyotsu", "kyotsu_rikei", exam="rikei", questions=[q(None, "力学の問題 (unit なし)")], ts=ts(60, 0))
    code, d = bank(exam="rikei", part="phys_kyotsu", eiken_grade="kyotsu_rikei", topic="力学", limit=5)
    got = ids(d)
    check("先頭 3 行が単元タグ行 (全角コロン・全角括弧と前の全角空白・2 問中 1 問だけタグ) の新しい順",
          got[:3] == [t_mixed, t_space, t_colon], f"{got[:3]}")
    check("「熱力学」「unit なし」は単元タグに数えず、新しい順で後ろに続く (limit 5 で切る)",
          got[3:] == [no_unit, netsu[-1]], f"{got[3:]}")
    for u, want in (("熱力学(気体)", False), ("力学", True), ("力学:x", True), (" 力学（x）", True), ("", False), (None, False), ("電磁気(力学的)", False)):
        check(f"_bank_unit_prefix({u!r}).startswith('力学') == {want} (画面の pref と一致)",
              mod._bank_unit_prefix(u).startswith("力学") == want == pref(u).startswith("力学"))
    for u, want in (("力学(剛体)", "力学"), ("力学（剛体）", "力学"), ("力学:剛体", "力学"), ("力学：剛体", "力学"),
                    ("　力学（円運動）", "力学"), (" 助動詞 (may)", "助動詞"), ("数列(等差):(1)", "数列"), (None, ""), (5, "5")):
        check(f"_bank_unit_prefix({u!r}) == {want!r} (画面の pref と同じ)", mod._bank_unit_prefix(u) == want == pref(u),
              repr(mod._bank_unit_prefix(u)))
    # 画面の unitExact の塊 (「if (preset.unitExact && preset.filter) {」〜「if (exact.length) questions = exact;」) だけを照合する
    #   (同じ正規表現は findPresetForWeakness にもあるので、ファイル全体で探すと unitExact 側だけ変わっても通ってしまう)。
    #   ★ここが落ちたら: 規則を変えたなら server/main.py の _bank_unit_prefix も同じに直す。名前の変更だけならこの照合を直す。
    src = open(DOJO_HTML, encoding="utf-8").read()
    i = src.find("if (preset.unitExact && preset.filter) {")
    j = src.find("if (exact.length) questions = exact;", i)
    blk = src[i:j] if 0 <= i < j else ""
    check("dojo-drill.html の unitExact が同じ規則のまま (split(/[（(：:]/)[0].trim() → startsWith(preset.filter))",
          bool(blk) and "split(/[（(：:]/)[0].trim()" in blk and ".startsWith(preset.filter)" in blk, f"塊 {len(blk)} 文字")
    check("dojo-drill.html は bank に topic=preset.filter を送る", "&topic=${encodeURIComponent(preset.filter)}" in src)

    # ── [3] fallback と topic なし ──────────────────────────────────────────
    print("\n[3] topic に当たる行が 0 件 → 従来どおりプール全体の新しい順")
    fb = [pool.add("chiri", "kyotsu", [q("地形(河川)", f"扇状地 {i}")], ts=ts(30, i)) for i in range(8)]
    code, d = bank(exam="daigaku", part="chiri", eiken_grade="kyotsu", topic="存在しない単元", limit=5)
    check("fallback: 新しい順 5 行", code == 200 and ids(d) == list(reversed(fb))[:5], f"{ids(d)}")
    code, d2 = bank(exam="daigaku", part="chiri", eiken_grade="kyotsu", limit=5)
    check("topic なし: 同じく新しい順 5 行", ids(d2) == list(reversed(fb))[:5], f"{ids(d2)}")

    # ── [4] limit ──────────────────────────────────────────────────────────
    print("\n[4] limit を守る")
    code, d = bank(exam="daigaku", part="r_grammar", eiken_grade="teiki", topic="助動詞", limit=7)
    got = ids(d)
    check("limit=7 → all 7 行・count 7・先頭 5 行は単元タグ行", len(got) == 7 and d.get("count") == 7 and got[:5] == list(reversed(tagged)),
          f"{len(got)} {d.get('count')}")
    code, d = bank(exam="daigaku", part="r_grammar", eiken_grade="teiki", topic="助動詞", limit=500)
    check("limit=500 → 50 行で頭打ち", len(ids(d)) == 50, str(len(ids(d))))
    code, d = bank(exam="daigaku", part="r_grammar", eiken_grade="teiki", topic="助動詞", limit=1)
    check("limit=1 → 最も新しい単元タグ行 1 行", ids(d) == [tagged[-1]], f"{ids(d)}")
    check("多めに取る行数は 1000 行以下 (1 リクエストで question_data を読みすぎない)", isinstance(OVER, int) and OVER <= 1000, repr(OVER))
    if isinstance(OVER, int):
        old = pool.add("bio_basic", "kyotsu_rikei", exam="rikei", questions=[q("代謝(呼吸)", "【単元】代謝(呼吸)。")], ts=ts(1, 0))
        for i in range(min(OVER, 1001)):
            pool.add("bio_basic", "kyotsu_rikei", exam="rikei", questions=[q("細胞(構造)", f"代謝ではなく細胞 {i}")], ts=ts(100, i))
        code, d = bank(exam="rikei", part="bio_basic", eiken_grade="kyotsu_rikei", topic="代謝", limit=10)
        check(f"多めに取るのは {OVER} 行まで (それより古い単元タグ行は窓の外・取得は無制限にしない)",
              len(ids(d)) == 10 and old not in ids(d), f"{len(ids(d))}")
        check("LIKE が多めに取る上限を超えたカードは log に出す (1 回だけ記録)",
              ("rikei", "bio_basic", "kyotsu_rikei", "代謝") in getattr(mod, "_BANK_OVERFETCH_SATURATED_LOGGED", ()))
    # 同じ created_at の行 (取込は 1 トランザクションで同時刻になる) は id の大きい順で、limit の境目でも決まった行が残る
    same = [pool.add("chem_basic", "kyotsu_rikei", exam="rikei", questions=[q("酸化還元(酸化数)", f"【単元】酸化還元(酸化数)。{i}")],
                     ts="2026-03-03 03:03:03") for i in range(4)]
    newer = pool.add("chem_basic", "kyotsu_rikei", exam="rikei", questions=[q("結合(イオン)", "酸化還元ではない")], ts="2026-04-04 04:04:04")
    code, d = bank(exam="rikei", part="chem_basic", eiken_grade="kyotsu_rikei", topic="酸化還元", limit=3)
    check("同時刻の単元タグ行は id の大きい順 (limit=3 の境目で残る行が決まる)", ids(d) == list(reversed(same))[:3], f"{ids(d)}")
    code, d = bank(exam="rikei", part="chem_basic", topic="酸化還元", limit=3)
    check("eiken_grade を渡さない経路でも同じ", ids(d) == list(reversed(same))[:3] and newer not in ids(d), f"{ids(d)}")
    # 大きな行 (図つき等): 窓の外にある大きな単元タグ行は多めに取る対象にしない・窓の中なら従来どおり出て先頭に並ぶ
    MAXC = getattr(mod, "_BANK_TOPIC_OVERFETCH_MAX_CHARS", None)
    check("1 行の文字数の上限 _BANK_TOPIC_OVERFETCH_MAX_CHARS がある (道場の行 2.3 万字より大きく 10 万字以下)",
          isinstance(MAXC, int) and 23000 < MAXC <= 100000, repr(MAXC))
    if isinstance(MAXC, int):
        big = "図" * (MAXC + 10)
        big_old = pool.add("r_long", "kyotsu", [q("長文(図表)", "【単元】長文(図表)。")], passage=big, ts=ts(5, 0))
        small_old = pool.add("r_long", "kyotsu", [q("長文(要旨)", "【単元】長文(要旨)。")], ts=ts(6, 0))
        filler = [pool.add("r_long", "kyotsu", [q("語法(x)", f"長文ではない {i}")], ts=ts(70, i)) for i in range(4)]
        big_new = pool.add("r_long", "kyotsu", [q("長文(図表)", "【単元】長文(図表)。新")], passage=big, ts=ts(90, 0))
        code, d = bank(exam="daigaku", part="r_long", eiken_grade="kyotsu", topic="長文", limit=4)
        got = ids(d)
        check("窓の中の大きな単元タグ行は先頭・窓の外の小さな単元タグ行は拾う・窓の外の大きな行は拾わない",
              got == [big_new, small_old, filler[-1], filler[-2]] and big_old not in got, f"{got}")
        code, d = bank(exam="daigaku", part="r_long", eiken_grade="kyotsu", topic="長文", limit=10)
        check("窓が満杯でなければ 2 本目のクエリは走らず、窓の中で並べ替えるだけ (大きな行も全部出る)",
              overfetched() == 0 and ids(d) == [big_new, small_old, big_old] + list(reversed(filler)), f"{ids(d)} {overfetched()}")

    # ── [5] 後段フィルタ・eiken_grade 無しの経路 ────────────────────────────────
    print("\n[5] _matches_topic の後段フィルタと eiken_grade 無しの経路")
    p_tag = pool.add("seiji_keizai", "kyotsu", [q("国際(国連)", "【単元】国際(国連)。安全保障理事会")], ts=ts(15, 0))
    p_txt = pool.add("seiji_keizai", "kyotsu", [q("政治(国会)", "国際条約の承認は国会")], ts=ts(16, 0))
    p_passage = pool.add("seiji_keizai", "kyotsu", [q("経済(財政)", "財政の基本")], passage="国際収支の資料を読み", ts=ts(17, 0))
    code, d = bank(exam="daigaku", part="seiji_keizai", eiken_grade="kyotsu", topic="国際", limit=10)
    got = ids(d)
    check("本文だけで LIKE に当たった行 (設問・解説に topic なし) は従来どおり落ちる", p_passage not in got, f"{got}")
    check("残りは単元タグ行 → 解説で言及する行の順", got == [p_tag, p_txt], f"{got}")
    code, d = bank(exam="daigaku", part="seiji_keizai", topic="国際", limit=10)
    check("eiken_grade を渡さない経路も同じ並び", ids(d) == [p_tag, p_txt], f"{ids(d)}")
    check("窓が満杯でない (3 行 < limit 10) ので 2 本目のクエリは走らない", overfetched() == 0, str(sqls))

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for x in FAILURES:
            print("   -", x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
