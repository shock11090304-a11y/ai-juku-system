#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📖🧪 英語長文 (english_long)・習熟度テスト (proficiency_test) の取込ファイルを本番の科目別ドリルに入れる (塾長が手元で実行する)。

    python3 -I import_drill_file.py <drill.json|test.json>             # 試運転 (既定): 本番には書かず、入る本数・問題数を表示
    python3 -I import_drill_file.py <drill.json|test.json> --apply     # 塾長が数を確かめてから本番に入れる (入れた後に読み返して確かめる)
    python3 -I import_drill_file.py <ファイル> --offline                # 通信しない (検査と変換だけ)

流れ (docs/drill-import-spec.md 8 章):
  1. 隣の validate_drill_import.py で検査する。エラーが 1 件でもあれば止まる。警告は --accept-warnings が無ければ止まる。
  2. 1 始まりの correct_choice_no を 0 始まりの answer に直して API の形にする (build_payloads・通信しない純関数)。
     変換の後にもう一度「解説の 1 行目 = 正解 ③ <選択肢>」を照合し、番号ずれのまま送らない。
  3. 試運転: /api/admin/grammar/import に dry_run: true で送り、サーバが数えた本数・問題数・飛ばす数を表示する (何も書かない)。
  4. --apply: 同じ実行の試運転が「エラー 0・飛ばす本文 0・数が一致」のときだけ本番に送る。すでに全部入っていれば「取込済み」と言って送らない。
     送った後に単元の本文の本数と 👀 プレビュー (習熟度テストは全大問・英語長文はランダムの 3 本) を読み返し、ファイルと照らす。
  結果はファイルの隣の <ファイル名>.import_log.json に残す (秘密は書かない)。

★拒否するファイル: git リポジトリの中 (祖先のどこかに .git) と seed-data の中 (公開されるため・テストの答えが漏れる)。
★秘密: 環境変数 CRON_SECRET、無ければ ~/.ai-juku-cron-secret (自分だけが読める 0600 のファイル・1 行)。画面にもログにも出さない。
★送り先: 環境変数 AI_JUKU_API_BASE (既定 https://ai-juku-api-production.up.railway.app)。https 以外は手元の 127.0.0.1 / localhost だけ。
★Python 3.9 の標準ライブラリだけ・どのフォルダからでも `python3 -I` で動く (隣の validate_drill_import.py を読み込む)。
終了コード: 0 = 試運転 OK・取り込んだ・取込済み / 1 = 検査・サーバの応答・読み返しで止めた / 2 = 使い方・場所・秘密・送り先の問題
"""
import argparse
import datetime
import importlib.util
import json
import os
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True   # _tools/ に __pycache__ を作らない (-I では PYTHONDONTWRITEBYTECODE が効かない)
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BASE = "https://ai-juku-api-production.up.railway.app"
SECRET_FILE = os.path.expanduser("~/.ai-juku-cron-secret")
TIMEOUT = 90
USER_AGENT = "ai-juku-drill-import/1"


def _load_validator():
    path = os.path.join(HERE, "validate_drill_import.py")
    if not os.path.isfile(path):
        raise SystemExit(f"隣に validate_drill_import.py がありません ({path})。2 本を同じフォルダに置いてください")
    spec = importlib.util.spec_from_file_location("validate_drill_import", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _load_validator()


class ImportStop(Exception):
    """ここで止める (code = 終了コード)。メッセージはそのまま塾長に見せる。"""

    def __init__(self, msg, code=1):
        Exception.__init__(self, msg)
        self.code = code


# ---------------------------------------------------------------------------
# 変換 (通信しない純関数。scripts/health_check/test_proficiency_test_import.py も呼ぶ)
# ---------------------------------------------------------------------------
def _question(q, source):
    return {"stem": q["stem"], "choices": list(q["choices"]), "answer": int(q["correct_choice_no"]) - 1,
            "explanation": q["explanation"], "source": source}


def _check_converted(payload):
    """変換の後の照合 (送る前の最後の砦)。1 始まり → 0 始まりで番号がずれていないか・出典の長さ (サーバが切り詰める長さ)。"""
    probs = []
    for p in payload["passages"]:
        if not p.get("unit") or len(p.get("source") or "") > 60:
            probs.append(f"本文 {p.get('source')!r} の単元・出典 (60 字まで)")
        for q in p["questions"]:
            a, ch = q["answer"], q["choices"]
            if not (isinstance(a, int) and 0 <= a < len(ch)):
                probs.append(f"{q['source']}: answer {a} が範囲外")
                continue
            head = V.norm_ws((q.get("explanation") or "").split("\n")[0])
            if head != V.norm_ws(f"正解 {V.CIRCLED[a]} {ch[a]}"):
                probs.append(f"{q['source']}: 解説の 1 行目「{head[:30]}」が 0 始まりの answer={a} の選択肢と合わない")
            if len(q["source"]) > 30:
                probs.append(f"{q['source']}: 出典が 30 字を超える (サーバで切れて別の問題と区別できなくなる)")
    if payload["subject"] == V.PTEST_SUBJECT and not V.PTEST_UNIT_RE.match(payload["passages"][0]["unit"]):
        probs.append(f"習熟度テストの単元名「{payload['passages'][0]['unit']}」がサーバの形に合わない")
    if probs:
        raise ValueError("変換の後の照合で止めました: " + "・".join(probs[:5]))


def build_payloads(doc, file_sha256=""):
    """取込ファイル (1 始まり) → /api/admin/grammar/import に送る payload の配列 (0 始まり)。通信しない。
    ★検査 (validate_drill_import.validate) でエラー 0 を確かめてから呼ぶこと。盲検の要約に all_agree: true を付ける
      (サーバは形しか見ない。中身の照合は検査スクリプトが済ませている前提)。
    英語長文: 出典 = 設問 'el-<set_id>-<qid>'・本文 'englong:<set_id>:<pid>' (自動配信の許可リストの形)。
    習熟度テスト: 単元「<高校|中学><科目> <series_ja> 第<round>回(改<revision>)」・大問は section_no の順・
      出典 = 設問 'pt-<test_id>-<qid>'・本文 'ptest:<test_id>:S<nn>'・skill は ptest_meta.skills {設問の出典: '科目|単元'}
      (単元名が決まっていない科目の skill は外す = 検査の W_SKILL)。"""
    kind = doc.get("kind")
    rv = doc.get("_review") if isinstance(doc.get("_review"), dict) else {}
    blind = rv.get("blind") if isinstance(rv.get("blind"), dict) else {}
    solvers = [{"label": str(s.get("label") or ""), "kind": str(s.get("kind") or ""), "date": str(s.get("date") or "")}
               for s in (blind.get("solvers") or []) if isinstance(s, dict)]
    if len({s["label"] for s in solvers if s["label"] and s["date"]}) < 3:
        raise ValueError("盲検の解き手 (_review.blind.solvers) が 3 名に足りません。検査スクリプトを先に通してください")
    review = {"protocol": V.REVIEW_PROTOCOL, "all_agree": True, "validator": V.TOOL_VERSION, "file_sha256": file_sha256,
              "kind": kind, "solvers": solvers}
    if kind == "english_long":
        set_id, unit = doc["set_id"], doc["unit"]
        review["set_id"] = set_id
        passages = []
        for p in doc["passages"]:
            passages.append({"subject": "english_long", "unit": unit, "level": "standard", "title": p.get("title") or None,
                             "body": p["body"], "body_ja": p.get("body_ja"), "source": f"englong:{set_id}:{p['pid']}",
                             "questions": [_question(q, f"el-{set_id}-{q['qid']}") for q in p["questions"]]})
        payload = {"subject": "english_long", "dedup": True, "all_or_nothing": True, "passages": passages, "review": review}
    elif kind == V.PTEST_SUBJECT:
        test_id, unit = doc["test_id"], V.ptest_unit_name(doc)
        review["test_id"] = test_id
        passages, skills = [], {}
        for sec in sorted(doc["sections"], key=lambda s: s["section_no"]):
            qs = []
            for q in sec["questions"]:
                src = f"pt-{test_id}-{q['qid']}"
                qs.append(_question(q, src))
                sk = q.get("skill")
                if isinstance(sk, dict) and isinstance(sk.get("subject"), str) and isinstance(sk.get("unit"), str) \
                        and sk["unit"] in V.SKILL_UNITS.get(sk["subject"], ()):
                    skills[src] = f"{sk['subject']}|{sk['unit']}"
            passages.append({"subject": V.PTEST_SUBJECT, "unit": unit, "level": "standard", "title": sec.get("title") or None,
                             "body": sec["body"], "body_ja": sec.get("body_ja"),
                             "source": f"ptest:{test_id}:S{int(sec['section_no']):02d}", "questions": qs})
        payload = {"subject": V.PTEST_SUBJECT, "dedup": True, "all_or_nothing": True, "passages": passages, "review": review,
                   "ptest_meta": {"test_id": test_id, "title": doc.get("title"), "target": doc.get("target"),
                                  "subject": doc.get("subject"), "round": doc.get("round"), "revision": doc.get("revision") or 0,
                                  "time_limit_min": doc.get("time_limit_min"), "skills": skills}}
    else:
        raise ValueError(f"kind {kind!r} は english_long / proficiency_test のどちらか")
    _check_converted(payload)
    return [payload]


# ---------------------------------------------------------------------------
# 通信 (HTTP はテストで差し替える)
# ---------------------------------------------------------------------------
def _urllib_http(method, url, headers, body=None):
    data = None
    hdrs = dict(headers)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    except urllib.error.URLError as e:
        raise ImportStop(f"サーバにつながりません ({e.reason})。ネットワークと AI_JUKU_API_BASE を確かめてください", 2)
    except OSError as e:
        raise ImportStop(f"サーバにつながりません ({type(e).__name__})", 2)
    try:
        return status, json.loads(raw.decode("utf-8"))
    except ValueError:
        return status, {"_text": raw[:300].decode("utf-8", "replace")}


HTTP = _urllib_http


def api_base():
    b = (os.environ.get("AI_JUKU_API_BASE") or "").strip() or DEFAULT_BASE
    u = urllib.parse.urlparse(b)
    if not ((u.scheme == "https" and u.netloc) or (u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost", "::1"))):
        raise ImportStop("AI_JUKU_API_BASE は https:// で始める (手元の試験だけ http://127.0.0.1 可)。秘密を平文で送らないため", 2)
    return b.rstrip("/")


def read_secret():
    """X-Cron-Secret の値。環境変数 CRON_SECRET、無ければ SECRET_FILE (自分の 0600 のファイル)。★値は表示しない。"""
    v = (os.environ.get("CRON_SECRET") or "").strip()
    if v:
        return v
    p = SECRET_FILE
    try:
        st = os.lstat(p)
    except FileNotFoundError:
        raise ImportStop(f"秘密のファイル {p} がありません。Railway の CRON_SECRET と同じ値を 1 行で書いて保存し、"
                         f"`chmod 600 {p}` を実行してください", 2)
    if not stat.S_ISREG(st.st_mode):
        raise ImportStop(f"{p} が普通のファイルではありません (リンク不可)", 2)
    if st.st_uid != os.getuid():
        raise ImportStop(f"{p} の持ち主が自分ではありません", 2)
    if st.st_mode & 0o077:
        raise ImportStop(f"{p} は自分以外も読める設定です ({oct(st.st_mode & 0o777)})。`chmod 600 {p}` を実行してから", 2)
    with open(p, encoding="utf-8") as f:
        v = f.read().strip()
    if not v or "\n" in v:
        raise ImportStop(f"{p} の中身が空か、2 行以上あります (1 行だけ)", 2)
    return v


class Api:
    def __init__(self, base, secret):
        self.base = base
        self._headers = {"X-Cron-Secret": secret, "User-Agent": USER_AGENT, "Accept": "application/json"}

    def call(self, method, path, params=None, body=None):
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        status, js = HTTP(method, url, self._headers, body)
        if status == 401:
            raise ImportStop("401 未認証: 秘密 (CRON_SECRET) が Railway の値と違います", 2)
        return status, js


def _detail(js):
    d = js.get("detail") if isinstance(js, dict) else None
    if isinstance(d, (dict, list)):
        d = json.dumps(d, ensure_ascii=False)
    return str(d or js.get("_text") or js)[:400]


def _post_import(api, payload, dry_run):
    status, js = api.call("POST", "/api/admin/grammar/import", body=dict(payload, dry_run=dry_run))
    if status != 200:
        hint = ""
        if status == 422 and "subject" in _detail(js):
            hint = " (サーバがまだ英語長文・習熟度テストに対応していない = アプリの更新前の可能性)"
        raise ImportStop(f"取込 API が {status} を返しました: {_detail(js)}{hint}")
    return js


def _unit_passages(api, subject, unit):
    status, js = api.call("GET", "/api/admin/grammar/units", params={"subject": subject})
    if status != 200 or js.get("subject") != subject:
        raise ImportStop(f"単元一覧を読めません ({status}・subject={js.get('subject')!r})")
    for u in js.get("units") or []:
        if u.get("unit") == unit:
            return int(u.get("passages") or 0)
    return 0


def _verify_preview(api, payload, out):
    """👀 プレビューを読み返して、ファイルの設問 (本文・問題文・選択肢・0 始まりの答え・解説) と照らす。食い違いの説明の配列を返す。"""
    subject = payload["subject"]
    unit = payload["passages"][0]["unit"]
    mine = {}      # (本文, 問題文) -> [設問…] (同じ本文に「本文の内容に合うものを選びなさい。」が 2 問あることがある)
    n_mine = 0
    for p in payload["passages"]:
        for q in p["questions"]:
            mine.setdefault((V.squash(p["body"]), q["stem"].strip()), []).append(q)
            n_mine += 1
    bad, seen = [], set()
    tries = 1 if subject == V.PTEST_SUBJECT else 5
    for _ in range(tries):
        status, js = api.call("GET", "/api/admin/grammar/preview",
                              params={"subject": subject, "unit": unit, "passage_count": 3, "levels": "standard"})
        if status != 200:
            raise ImportStop(f"👀 プレビューを読めません ({status}: {_detail(js)})")
        bodies = {str(k): V.squash(v.get("body") or "") for k, v in (js.get("passages") or {}).items()}
        got = []
        for item in js.get("questions") or []:
            cands = mine.get((bodies.get(str(item.get("passage_id")), ""), (item.get("stem") or "").strip()))
            if not cands:
                continue          # 英語長文: 同じ単元の別のファイルの本文
            q = next((c for c in cands if c["choices"] == item.get("choices")), None)
            if q is None:
                bad.append(f"本文と問題文が同じ設問「{(item.get('stem') or '')[:20]}」の選択肢が本番とファイルで違う")
                continue
            got.append(q["source"])
            if q["source"] in seen:
                continue
            seen.add(q["source"])
            if item.get("answer") != q["answer"] or (item.get("explanation") or "") != q["explanation"]:
                bad.append(f"{q['source']}: 本番の答え・解説がファイルと違う")
        if subject == V.PTEST_SUBJECT:
            want = [q["source"] for p in payload["passages"] for q in p["questions"]]
            if got != want:
                bad.append(f"習熟度テストの出題順・問題数がファイルと違う (本番 {len(got)} 問 / ファイル {len(want)} 問)")
    out.write(f"  読み返し: 👀 プレビューで {len(seen)}/{n_mine} 問をファイルと照合"
              + (" (英語長文はランダムに出る本文のうち、このファイルの分だけ)" if subject != V.PTEST_SUBJECT else "") + "\n")
    return bad


def _write_log(path, entry):
    lp = path + ".import_log.json"
    runs = []
    try:
        with open(lp, encoding="utf-8") as f:
            old = json.load(f)
        if isinstance(old, list):
            runs = old
    except (OSError, ValueError):
        pass
    runs.append(entry)
    tmp = lp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=1)
    os.replace(tmp, lp)
    return lp


def _counts(js):
    return {k: js.get(k) for k in ("ok", "dry_run", "passages_inserted", "passages_skipped", "inserted", "skipped", "errors",
                                   "already_imported", "ptest_meta_saved", "reason", "unknown_units") if k in js}


def run(argv=None, out=None):
    out = out or sys.stdout
    ap = argparse.ArgumentParser(description="英語長文・習熟度テストの取込ファイルを本番の科目別ドリルに入れる (既定は試運転)")
    ap.add_argument("file", help="drill.json / test.json")
    ap.add_argument("--apply", action="store_true", help="本番に書く (試運転が通ったときだけ送る)")
    ap.add_argument("--accept-warnings", action="store_true", help="検査の警告を確かめたうえで進める")
    ap.add_argument("--offline", action="store_true", help="通信しない (検査と変換だけ)")
    a = ap.parse_args(argv)
    w = out.write
    path = os.path.abspath(a.file)
    if not os.path.isfile(path):
        w(f"✗ ファイルが見つかりません: {a.file}\n")
        return 2
    why = V.location_problem(path)
    if why:
        w(f"✗ このファイルは{why}にあります。取り込みません (リポジトリ・seed-data は公開されるので置かない。仕様書 1-10)\n")
        return 2
    r = V.validate(path)
    V.print_report(r, out)
    if r.errors:
        w("✗ 検査のエラーを直してから取り込んでください (何も送っていません)\n")
        return 1
    if r.warnings and not a.accept_warnings:
        w("✗ 警告があります。中身を確かめ、問題なければ --accept-warnings を付けて実行してください (何も送っていません)\n")
        return 1
    try:
        payloads = build_payloads(r.doc, r.file_sha256)
    except ValueError as e:
        w(f"✗ {e} (何も送っていません)\n")
        return 1
    n_p = sum(len(p["passages"]) for p in payloads)
    n_q = sum(len(x["questions"]) for p in payloads for x in p["passages"])
    unit = payloads[0]["passages"][0]["unit"]
    subject = payloads[0]["subject"]
    w(f"変換: 科目 {subject}・単元「{unit}」・本文 {n_p} 本・設問 {n_q} 問 (answer は 0 始まりに直した)\n")
    if a.offline:
        w("--offline: 送っていません (検査と変換だけ)\n")
        return 0
    entry = {"at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds"),
             "file": os.path.basename(path), "file_sha256": r.file_sha256, "kind": r.kind, "id": r.doc_id, "unit": unit,
             "mode": "apply" if a.apply else "dry-run", "passages": n_p, "questions": n_q}
    code = 1
    try:
        base = api_base()
        entry["base"] = base
        api = Api(base, read_secret())
        w(f"送り先: {base}\n")
        dry = [_post_import(api, p, True) for p in payloads]
        entry["dry_run"] = [_counts(x) for x in dry]
        for x in dry:
            if x.get("ok") is not True:
                raise ImportStop(f"試運転でサーバが止めました (reason={x.get('reason')}): {x.get('detail') or _detail(x)}")
            if x.get("errors") or x.get("unknown_units"):
                raise ImportStop(f"試運転でエラー {x.get('errors')} 件・知らない単元 {x.get('unknown_units')}: {x.get('warning') or ''}")
        if all(x.get("already_imported") is True for x in dry):
            w("取込済みです: このファイルの本文はすべて本番に入っています。何も送っていません\n")
            entry["result"] = "already_imported"
            code = 0
            return code
        got_p = sum(int(x.get("passages_inserted") or 0) for x in dry)
        got_q = sum(int(x.get("inserted") or 0) for x in dry)
        skipped = sum(int(x.get("passages_skipped") or 0) for x in dry)
        w(f"試運転: 本文 {got_p} 本・設問 {got_q} 問が入る見込み・飛ばす本文 {skipped} 本 (本番には書いていません)\n")
        if skipped or got_p != n_p or got_q != n_q:
            raise ImportStop(f"試運転の数がファイルと合いません (ファイル: 本文 {n_p}・設問 {n_q})。一部だけ取込済みの可能性があります。"
                             "CEO の「📝 科目別 単元ドリル」で単元の在庫を確かめてください (送っていません)")
        if subject == V.PTEST_SUBJECT and not all(x.get("ptest_meta_saved") for x in dry):
            raise ImportStop("試運転でテストの情報 (ptest_meta) が保存されない見込みです (送っていません)")
        if not a.apply:
            w("試運転 OK。数を確かめてから、同じコマンドの末尾に --apply を付けて実行すると本番に入ります\n")
            entry["result"] = "dry_run_ok"
            code = 0
            return code
        before = _unit_passages(api, subject, unit)
        res = [_post_import(api, p, False) for p in payloads]
        entry["apply"] = [_counts(x) for x in res]
        for x in res:
            if x.get("ok") is not True or x.get("errors"):
                raise ImportStop(f"本番の取込でサーバが止めました (reason={x.get('reason')}): {x.get('detail') or _detail(x)}。"
                                 "all_or_nothing なので何も入っていないはずです。CEO で在庫を確かめてください")
        put_p = sum(int(x.get("passages_inserted") or 0) for x in res)
        put_q = sum(int(x.get("inserted") or 0) for x in res)
        w(f"本番: 本文 {put_p} 本・設問 {put_q} 問を入れました\n")
        after = _unit_passages(api, subject, unit)
        bad = []
        if put_p != n_p or put_q != n_q:
            bad.append(f"入った数がファイルと違う (本文 {put_p}/{n_p}・設問 {put_q}/{n_q})")
        if after - before != n_p:
            bad.append(f"単元「{unit}」の本文の本数が {before} → {after} (+{n_p} のはず)")
        bad += _verify_preview(api, payloads[0], out)
        entry["readback"] = {"unit_passages_before": before, "unit_passages_after": after, "problems": bad}
        if bad:
            for b in bad:
                w(f"  ✗ {b}\n")
            raise ImportStop("読み返しで食い違いが見つかりました。取込は済んでいるので、CEO の 👀 問題を見る で確かめ、"
                             "必要なら止めて (retire) 直した版を新しい ID で入れ直してください")
        w("✅ 取り込みました (読み返しも一致)。CEO の「📝 科目別 単元ドリル」で科目を選ぶと在庫に出ます\n")
        entry["result"] = "applied"
        code = 0
        return code
    except ImportStop as e:
        w(f"✗ {e}\n")
        entry["result"] = "stopped"
        entry["message"] = str(e)[:500]
        code = e.code
        return code
    finally:
        if "base" in entry:
            try:
                lp = _write_log(path, entry)
                w(f"記録: {lp}\n")
            except OSError as e:
                w(f"(記録を書けませんでした: {e})\n")


if __name__ == "__main__":
    sys.exit(run())
