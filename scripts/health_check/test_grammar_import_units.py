#!/usr/bin/env python3
"""🧷 単元ドリルの取込 API (POST /api/admin/grammar/import) の単元名の検査 — 回帰テスト。

背景 (2026-09-29 fada278 のレビュー):
  english 以外は任意の unit を受けていたので、単元の並びが決まっている科目
  (中学英語 chugaku・中学数学 chugaku_math・英検 eiken = server の _GRAMMAR_SUBJECT_UNIT_ORDER) でも
  綴り違いの単元名 (「一時関数」等) が黙って入っていた。入った行は単元一覧の末尾に別単元として並び、
  弱点 topic も入試道場の単元フィルタと一致しない。取込は INSERT 専用なので、入ったら手で直すしかない。

固定する性質:
  1. コミット済みのシード (中学英語・中学数学・英検 語彙 v1/v2・英検 長文 v1/v2・高校数学) が CEO の補充ボタンと同じ送り方で全部入る
     (errors 0・skipped 0・unknown_units / warning なし)。取込後の単元一覧は _GRAMMAR_SUBJECT_UNIT_ORDER と完全一致で、
     どの単元にも在庫がある
  2. 3 科目とも、知らない単元名の問題は入れずに errors に数え、応答の unknown_units / warning に単元名が出る。
     同じ要求の正しい問題は入る。問ごとの subject (payload の既定より優先・別名「中学数学」も) でも同じ。
     前後の空白は従来どおり削って受ける。登録済みの単元と見た目が同じ綴り違い (全角の「１」・ゼロ幅スペース・ー/一) には
     looks_like でどの単元のつもりかを添える。見えない文字・改行・壊れたサロゲートは \\uXXXX で返す (500 にしない)。
     単元名が大量でも応答は 20 種類・長い単元名は切って返す。弾く判定は問題・本文とも重複判定より前
     (検査前に入った綴り違いの行があっても skip にならない)
  3. 英検の本文 (passages) も同じ: 知らない単元名の本文は設問ごと入らない
  4. 他の科目は変わらない: english の知らない単元は従来どおり skip (errors にせず warning も出さない)・
     高校の数学/国語/社会は任意の単元を受ける・english の本文は skip・国語の本文は任意の単元で入る・
     弱点特訓シード (英語 + 古文) は全部入る

実行:
    python3 scripts/health_check/test_grammar_import_units.py
    # exit 0 = PASS / 1 = FAIL

外部通信は一切しない。DB は一時 SQLite。
"""
import base64
import datetime
import hashlib
import hmac
import importlib.util
import json
import os
import re
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
MAIN_PY = os.path.join(REPO, "server", "main.py")
SEED_DIR = os.path.join(REPO, "seed-data")
sys.path.insert(0, os.path.join(REPO, "server"))

FAILURES = []
ZW_SPACE = chr(0x200B)     # ゼロ幅スペース (ソース上で見えるように chr で書く)
IDEO_SPACE = chr(0x3000)   # 全角スペース


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {detail}" if detail else ""))
    if not cond:
        FAILURES.append(label)


def load_main():
    tmpdb = os.path.join(tempfile.mkdtemp(prefix="gimport_"), "test.db")
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
    spec = importlib.util.spec_from_file_location("aijuku_main_gimport", MAIN_PY)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


def admin_token(mod, hours=1):
    exp = int((datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).timestamp())
    sig = hmac.new(mod.MAGIC_LINK_SECRET.encode(), f"admin.{exp}".encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"admin.{exp}.{sig}".encode()).decode().rstrip("=")


def load_seed(name):
    return json.load(open(os.path.join(SEED_DIR, name), encoding="utf-8"))


class Api:
    def __init__(self, mod, client, headers):
        self.mod, self.client, self.headers = mod, client, headers

    def post(self, body):
        self.mod._RATE_LIMIT_STORE.clear()
        r = self.client.post("/api/admin/grammar/import", json=body, headers=self.headers)
        return r.status_code, (r.json() if r.status_code == 200 else {"_text": r.text[:200]})

    def post_raw(self, body):
        """json.dumps (ensure_ascii) の本文で送る。壊れたサロゲートも "\\ud83d" のエスケープのまま届く (json= は UTF-8 化で落ちうる)"""
        self.mod._RATE_LIMIT_STORE.clear()
        r = self.client.post("/api/admin/grammar/import", content=json.dumps(body).encode("ascii"),
                             headers={**self.headers, "Content-Type": "application/json"})
        return r.status_code, (r.json() if r.status_code == 200 else {"_text": r.text[:200]})

    def units(self, subject):
        """単元一覧 (在庫つき)。在庫 0 の単元も _GRAMMAR_SUBJECT_UNIT_ORDER の順に 0 で並ぶ"""
        r = self.client.get("/api/admin/grammar/units", params={"subject": subject}, headers=self.headers)
        return r.json().get("units", []) if r.status_code == 200 else []

    def unit_names(self, subject):
        return [u["unit"] for u in self.units(subject)]


def import_like_ceo(api, key, items, subject, chunk):
    """CEO の補充ボタンと同じ送り方 (questions は 400 問ずつ・passages は 20 本ずつ・payload に subject・dedup)。"""
    tot = {"inserted": 0, "skipped": 0, "errors": 0, "passages_inserted": 0, "passages_skipped": 0,
           "status": set(), "ok": set(), "warnings": [], "unknown": []}
    for i in range(0, len(items), chunk):
        code, d = api.post({key: items[i:i + chunk], "subject": subject, "dedup": True})
        tot["status"].add(code)
        tot["ok"].add(d.get("ok"))
        for k in ("inserted", "skipped", "errors", "passages_inserted", "passages_skipped"):
            tot[k] += int(d.get(k) or 0)
        if "warning" in d:
            tot["warnings"].append(d["warning"])
        tot["unknown"] += d.get("unknown_units") or []
    return tot


def count_rows(mod, table, unit):
    conn = mod.db(); c = conn.cursor()
    c.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE unit = ?", (unit,))
    n = int(c.fetchone()["n"])
    conn.close()
    return n


def delete_legacy(mod):
    """検査用に直接入れた「検査前の綴り違いの行」を消す (この先の単元一覧の検査に混ざらないように)"""
    conn = mod.db(); c = conn.cursor()
    c.execute("DELETE FROM grammar_questions WHERE source = 'legacy'")
    c.execute("DELETE FROM grammar_passages WHERE source = 'legacy'")
    conn.commit(); conn.close()


def q(unit, stem, subject=None):
    d = {"unit": unit, "level": "standard", "stem": stem, "choices": ["alpha", "beta", "gamma", "delta"],
         "answer": 1, "explanation": "正解は beta。テスト用の解説。", "source": "unit-guard-test"}
    if subject is not None:
        d["subject"] = subject
    return d


def passage(unit, n, subject="eiken"):
    return {"subject": subject, "unit": unit, "level": "standard", "title": f"Guard Passage {n}",
            "body": f"Guard passage {n}. The bridge opened in ( 1 ) after years of delay. ( 2 ), traffic fell by half.",
            "body_ja": f"本文 {n} の全訳。", "source": f"unit-guard-p{n}",
            "questions": [{"stem": f"( {k} ) に入るもの", "choices": [f"o{k}a", f"o{k}b", f"o{k}c", f"o{k}d"], "answer": k % 4,
                           "explanation": f"正解は o{k}{'abcd'[k % 4]}。"} for k in (1, 2)]}


def main():
    print("🧷 単元ドリル 取込の単元名検査 回帰テスト\n")
    mod = load_main()
    from fastapi.testclient import TestClient
    # サーバ側の例外は 500 として受ける (既定の raise だと、壊れたサロゲートで 500 になる退行が「検査の失敗」でなくテストの異常終了になる)
    api = Api(mod, TestClient(mod.app, raise_server_exceptions=False), {"Authorization": "Bearer " + admin_token(mod)})
    ORDER = mod._GRAMMAR_SUBJECT_UNIT_ORDER
    check("単元の並びが決まっている科目に chugaku / chugaku_math / eiken がある",
          {"chugaku", "chugaku_math", "eiken"} <= set(ORDER), str(sorted(ORDER)))
    check("english と高校の他科目は並び順つき科目ではない (単元名の検査は従来どおり)",
          not ({"english", "math", "japanese", "social"} & set(ORDER)), str(sorted(ORDER)))

    print("\n[1] コミット済みのシードが CEO のボタンと同じ送り方で全部入る")
    # 英検は CEO のボタンと同じく v1 → v2 (本番形式演習 2026-10) の順に送る。v2 は v1 と重ならない (skipped 0) こと
    for fname, subj in (("chugaku_drill_pool_v1.json", "chugaku"), ("chugaku_math_pool_v1.json", "chugaku_math"),
                        ("eiken_vocab_pool_v1.json", "eiken"), ("eiken_vocab_pool_v2.json", "eiken"),
                        ("math_drill_ct_mock_v1.json", "math")):
        qs = load_seed(fname)["questions"]
        t = import_like_ceo(api, "questions", qs, subj, 400)
        check(f"{fname}: 全 {len(qs)} 問が入る (errors 0・skipped 0・警告なし)",
              t["status"] == {200} and t["inserted"] == len(qs) and t["skipped"] == 0 and t["errors"] == 0
              and not t["warnings"] and not t["unknown"],
              f"status={t['status']} inserted={t['inserted']} skipped={t['skipped']} errors={t['errors']} unknown={t['unknown'][:3]}")
    for rname in ("eiken_reading_pool_v1.json", "eiken_reading_pool_v2.json"):
        reading = load_seed(rname)["passages"]
        n_rq = sum(len(p.get("questions") or []) for p in reading)
        t = import_like_ceo(api, "passages", reading, "eiken", 20)
        check(f"{rname}: 本文 {len(reading)} 本・設問 {n_rq} 問が全部入る (errors 0・警告なし)",
              t["status"] == {200} and t["ok"] == {True} and t["passages_inserted"] == len(reading) and t["passages_skipped"] == 0
              and t["inserted"] == n_rq and t["errors"] == 0 and not t["warnings"] and not t["unknown"],
              f"status={t['status']} p_ins={t['passages_inserted']} p_skip={t['passages_skipped']} q_ins={t['inserted']} errors={t['errors']} unknown={t['unknown'][:3]}")
    # CEO の補充ボタンが読むシード (data-seed はカンマ区切り) が全部実在し、v1 と v2 の両方を含む
    ceo = open(os.path.join(REPO, "ceo.html"), encoding="utf-8").read()
    for btn, want in (("eikenPoolImportBtn", ("eiken_vocab_pool_v1.json", "eiken_vocab_pool_v2.json")),
                      ("eikenReadingImportBtn", ("eiken_reading_pool_v1.json", "eiken_reading_pool_v2.json")),
                      ("mathPoolImportBtn", ("math_drill_ct_mock_v1.json",))):
        m = re.search(r'id="%s"[^>]*data-seed="([^"]+)"' % btn, ceo)
        urls = [u.strip() for u in (m.group(1).split(",") if m else []) if u.strip()]
        check(f"ceo.html #{btn} の data-seed が {' → '.join(want)} を順に指し、どれも実在する",
              [u.rsplit("/", 1)[-1] for u in urls] == list(want) and all(os.path.exists(os.path.join(REPO, u.lstrip("/"))) for u in urls),
              str(urls))
    for subj in ("chugaku", "chugaku_math", "eiken"):
        got = api.units(subj)
        names = [u["unit"] for u in got]
        # 在庫 0 の単元も並ぶので、名前の一致だけでは「何も入っていない」でも通る → どの単元にも在庫があることも見る
        check(f"{subj}: 取込後の単元一覧が _GRAMMAR_SUBJECT_UNIT_ORDER と完全一致 (余分な単元なし・どの単元にも在庫あり)",
              names == ORDER[subj] and all(u.get("total") for u in got),
              f"extra={[u for u in names if u not in ORDER[subj]]} empty={[u['unit'] for u in got if not u.get('total')]}")

    print("\n[2] 知らない単元名 (綴り違い) の問題は入れずに errors + unknown_units / warning")
    for subj, good, bad, label in (("chugaku", "現在完了", "現在完了形", "中学英語"),
                                   ("chugaku_math", "一次関数", "一時関数", "中学数学"),
                                   ("eiken", "準1級 単語", "準１級 単語", "英検")):
        code, d = api.post({"subject": subj, "dedup": True, "questions": [
            q(good, f"[guard {subj}] ok ( )."), q(bad, f"[guard {subj}] ng1 ( )."), q(bad, f"[guard {subj}] ng2 ( ).")]})
        check(f"{subj}: 正しい 1 問は入り、「{bad}」の 2 問は errors (skipped にしない)",
              code == 200 and d.get("ok") is True and d.get("inserted") == 1 and d.get("errors") == 2 and d.get("skipped") == 0,
              json.dumps(d, ensure_ascii=False)[:240])
        # 全角の「１」は画面では登録済みの「準1級 単語」と見分けられないので、どの単元のつもりかを添える。ただの綴り違いには付けない
        lookalike = subj == "eiken"
        want = {"subject": subj, "unit": bad, "kind": "question", "count": 2}
        if lookalike:
            want["looks_like"] = good
        check(f"{subj}: unknown_units に単元名と件数" + (" と looks_like" if lookalike else " (looks_like なし)"),
              d.get("unknown_units") == [want], str(d.get("unknown_units")))
        w = d.get("warning") or ""
        check(f"{subj}: warning に科目ラベル・単元名・件数・直し方", all(x in w for x in (f"{label}「{bad}」2問", "_GRAMMAR_SUBJECT_UNIT_ORDER")), w)
        check(f"{subj}: 見た目が同じ綴り違いにだけ「登録済みの…」を添える ({'添える' if lookalike else '添えない'})",
              (f"(登録済みの「{good}」と見た目が同じで文字が違う)" in w) == lookalike and (("登録済みの" in w) == lookalike), w)
        check(f"{subj}: 「{bad}」の行は DB に無く、単元一覧も増えない",
              count_rows(mod, "grammar_questions", bad) == 0 and api.unit_names(subj) == ORDER[subj])

    # 問ごとの subject が payload の既定 (english) より優先される経路でも弾く。別名「中学数学」も同じ科目として見る
    code, d = api.post({"dedup": True, "questions": [
        q("一時関数", "[guard] per-q math 1", subject="chugaku_math"),
        q("一時関数", "[guard] per-q math 2", subject="中学数学"),
        q("現在完了形", "[guard] per-q eng 1", subject="chugaku"),
        q("時制", "[guard] per-q english ok ( ).")]})
    check("問ごとの subject・別名でも弾く (english の正しい 1 問は入る・errors 3)",
          code == 200 and d.get("inserted") == 1 and d.get("errors") == 3 and d.get("skipped") == 0, json.dumps(d, ensure_ascii=False)[:240])
    check("unknown_units は件数の多い順に科目ごと",
          d.get("unknown_units") == [{"subject": "chugaku_math", "unit": "一時関数", "kind": "question", "count": 2},
                                     {"subject": "chugaku", "unit": "現在完了形", "kind": "question", "count": 1}], str(d.get("unknown_units")))
    code, d = api.post({"subject": "chugaku_math", "dedup": True, "questions": [q(" 一次関数" + IDEO_SPACE, "[guard] padded unit")]})
    conn = mod.db(); c = conn.cursor()
    c.execute("SELECT unit FROM grammar_questions WHERE stem = ?", ("[guard] padded unit",))
    stored = [r["unit"] for r in c.fetchall()]
    conn.close()
    check("前後の空白 (全角含む) は従来どおり削って受ける (「一次関数」で入る)",
          code == 200 and d.get("inserted") == 1 and d.get("errors") == 0 and stored == ["一次関数"], f"{d} stored={stored}")
    code, d = api.post({"subject": "chugaku", "dedup": True,
                        "questions": [q(f"でたらめ単元{i:02d}", f"[guard] many {i}") for i in range(25)]})
    check("単元名が 25 種類でも応答は 20 種類で打ち切り、残りの数を warning に書く",
          code == 200 and d.get("errors") == 25 and len(d.get("unknown_units") or []) == 20 and "ほか 5 種類" in (d.get("warning") or ""),
          f"errors={d.get('errors')} n={len(d.get('unknown_units') or [])} warning={(d.get('warning') or '')[-80:]}")
    code, d = api.post({"subject": "chugaku", "dedup": True, "questions": [
        q("時制" + ZW_SPACE, "[guard] zero width"),
        q("長" * 150, "[guard] long unit"),
        q("ー次関数", "[guard] katakana choon", subject="chugaku_math"),   # 長音「ー」と漢数字「一」の取り違え
        q("時制\n[INFO] fake log line", "[guard] newline in unit")]})
    w = d.get("warning") or ""
    units_back = {x["unit"]: x for x in (d.get("unknown_units") or [])}
    check("見えない文字 (ゼロ幅スペース) は \\u200b と見える形で返し、登録済みの「時制」を添える",
          code == 200 and d.get("errors") == 4 and units_back.get("時制\\u200b", {}).get("looks_like") == "時制"
          and "「時制\\u200b」1問 (登録済みの「時制」と見た目が同じで文字が違う)" in w, w)
    check("長音「ー」と漢数字「一」の取り違えにも登録済みの「一次関数」を添える",
          units_back.get("ー次関数", {}).get("looks_like") == "一次関数" and "(登録済みの「一次関数」と見た目が同じで文字が違う)" in w, w)
    check("改行を含む単元名は \\u000a にして返す (warning とログの行を割らない)",
          "\n" not in w and "looks_like" not in units_back.get("時制\\u000a[INFO] fake log line", {"looks_like": "missing"}), w)
    check("長い単元名は warning で 40 字・unknown_units で 100 字に切り「…」を付ける",
          f"「{'長' * 40}…」1問" in w and ("長" * 100 + "…") in units_back, str([len(k) for k in units_back]))
    # 壊れたサロゲート (JSON の "\\ud83d" 単独) を含む単元名でも 500 にしない。応答の JSON 化 (UTF-8) で落ちると、
    #   その要求の正しい問題はコミット済みなのに CEO のボタンは失敗扱いになり、押し直しても毎回 500 になる
    code, d = api.post_raw({"subject": "chugaku_math", "dedup": True, "questions": [
        q(chr(0xD83D) + "次関数", "[guard] lone surrogate"), q("一次関数", "[guard] lone surrogate ok")]})
    check("壊れたサロゲート入りの単元名でも 200 (\\ud83d と見える形で返し、正しい 1 問は入る)",
          code == 200 and d.get("errors") == 1 and d.get("inserted") == 1
          and [x.get("unit") for x in d.get("unknown_units") or []] == ["\\ud83d次関数"], json.dumps(d)[:240])
    # ★弾く判定は重複判定より前 (2026-09-29 レビュー): 検査が入る前に綴り違いの行が本番に入っていても、直していない
    #   シードを押し直したとき「すでに入っている分 (skip)」の ✅ に戻らず、エラーとして見え続けること
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO grammar_questions (subject, unit, level, stem, choices, answer, explanation, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              ("chugaku_math", "一時関数", "standard", "[guard] legacy stray row", json.dumps(["a", "b", "c", "d"]), 0, "旧データ", "legacy"))
    conn.commit(); conn.close()
    code, d = api.post({"subject": "chugaku_math", "dedup": True, "questions": [q("一時関数", "[guard] legacy stray row")]})
    check("検査前に入っていた綴り違いの行と同じ問題を押し直しても skip ではなく errors (重複判定より先に弾く)",
          code == 200 and d.get("errors") == 1 and d.get("skipped") == 0 and d.get("inserted") == 0, json.dumps(d, ensure_ascii=False)[:200])
    delete_legacy(mod)

    print("\n[3] 英検の本文 (passages) も同じ")
    bad_p = "準1級 長文 空所補充"   # 正しくは「準1級 長文空所補充」(間に空白なし)
    code, d = api.post({"subject": "eiken", "dedup": True, "passages": [passage("2級 長文 内容一致", 1), passage(bad_p, 2)]})
    check("正しい本文は入り、知らない単元名の本文は errors 1 (本文 1 本・設問 2 問だけ入る)",
          code == 200 and d.get("ok") is True and d.get("passages_inserted") == 1 and d.get("passages_skipped") == 0
          and d.get("inserted") == 2 and d.get("errors") == 1, json.dumps(d, ensure_ascii=False)[:240])
    check("unknown_units に kind=passage", d.get("unknown_units") == [{"subject": "eiken", "unit": bad_p, "kind": "passage", "count": 1}],
          str(d.get("unknown_units")))
    check("warning は「本文1本」と数える", f"英検「{bad_p}」本文1本" in (d.get("warning") or ""), d.get("warning") or "")
    check("弾いた本文は本文も設問も DB に無い",
          count_rows(mod, "grammar_passages", bad_p) == 0 and count_rows(mod, "grammar_questions", bad_p) == 0)
    # 本文も重複判定 (本文ハッシュ) より前に弾く: 検査前に入った綴り違いの本文と同じものを押し直しても skip に戻らない
    legacy = passage(bad_p, 5)
    conn = mod.db(); c = conn.cursor()
    c.execute("INSERT INTO grammar_passages (subject, unit, level, title, body, body_ja, source, body_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              ("eiken", bad_p, "standard", legacy["title"], legacy["body"], None, "legacy", mod._grammar_passage_hash(legacy["body"])))
    conn.commit(); conn.close()
    code, d = api.post({"subject": "eiken", "dedup": True, "passages": [legacy]})
    check("検査前に入っていた綴り違いの本文を押し直しても skip ではなく errors (本文の重複判定より先に弾く)",
          code == 200 and d.get("errors") == 1 and d.get("passages_skipped") == 0 and d.get("passages_inserted") == 0,
          json.dumps(d, ensure_ascii=False)[:200])
    delete_legacy(mod)

    print("\n[4] 他の科目は変わらない")
    code, d = api.post({"dedup": True, "questions": [q("時制X", "[guard] english unknown ( ).")]})
    check("english の知らない単元は従来どおり skip (errors 0・warning なし)",
          code == 200 and d.get("skipped") == 1 and d.get("errors") == 0 and d.get("inserted") == 0
          and "warning" not in d and "unknown_units" not in d, json.dumps(d, ensure_ascii=False)[:200])
    code, d = api.post({"dedup": True, "questions": [q("自由な単元名A", "[guard] math free", subject="math"),
                                                     q("古文 助動詞", "[guard] japanese free", subject="japanese"),
                                                     q("世界史 近代", "[guard] social free", subject="social")]})
    check("高校の数学・国語・社会は任意の単元名を受ける (3 問入る・warning なし)",
          code == 200 and d.get("inserted") == 3 and d.get("errors") == 0 and "warning" not in d, json.dumps(d, ensure_ascii=False)[:200])
    code, d = api.post({"subject": "english", "dedup": True, "passages": [passage("長文読解", 3, subject="english")]})
    check("english の本文は従来どおり skip (errors 0・warning なし)",
          code == 200 and d.get("passages_skipped") == 1 and d.get("passages_inserted") == 0 and d.get("errors") == 0 and "warning" not in d,
          json.dumps(d, ensure_ascii=False)[:200])
    code, d = api.post({"subject": "japanese", "dedup": True, "passages": [passage("現代文 評論", 4, subject="japanese")]})
    check("国語 (並び順なし) の本文は任意の単元名で入る",
          code == 200 and d.get("passages_inserted") == 1 and d.get("errors") == 0 and "warning" not in d, json.dumps(d, ensure_ascii=False)[:200])
    wk = load_seed("grammar_drill_weakness_v1.json")["questions"]
    code, d = api.post({"questions": wk, "dedup": True})   # grammarWeaknessImport と同じ送り方 (subject なし)
    check(f"弱点特訓シード (英語 + 古文) {len(wk)} 問は全部入る (warning なし)",
          code == 200 and d.get("inserted") == len(wk) and d.get("errors") == 0 and d.get("skipped") == 0 and "warning" not in d,
          json.dumps(d, ensure_ascii=False)[:200])

    print()
    if FAILURES:
        print(f"❌ FAIL: {len(FAILURES)} 件")
        for x in FAILURES:
            print("   -", x)
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
