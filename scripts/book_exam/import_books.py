#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""変換した冊子 (JSON + PDF) を、冊子受験アプリへまとめて取り込む。

    python3 scripts/book_exam/import_books.py ~/Desktop/kyotsu_json --dry-run   # ★ まず予行
    python3 scripts/book_exam/import_books.py ~/Desktop/kyotsu_json             # 取り込む (非公開)
    python3 scripts/book_exam/import_books.py ~/Desktop/kyotsu_json --publish   # 検証まで通ったら公開も

    --pdf-dir DIR   問題 PDF の場所 (既定 lesson-prints)
    --only 国語     科目やファイル名で絞る (部分一致)

■ ログイン (講師のアカウント)
    環境変数 EXAM_TEACHER_EMAIL / EXAM_TEACHER_PASSWORD。無ければその場で聞く
    (画面に出ない)。★ パスワードをコマンド列やファイルに書かないこと。

■ なぜ要るか
    登録画面の手作業 (冊子を作る → PDF を選ぶ → JSON を読む → 保存 → 公開) は
    1 冊 2〜3 分かかり、冊子が増えるたびに塾長の時間を食う。ここに寄せれば
    1 コマンドで全冊入る。Claude のセッションからも同じスクリプトで入れられる
    (環境のネットワーク設定で supabase.co を許可した場合)。

■ ★ 安全の作り
    ・service_role は使わない。講師のメール+パスワードでログインし、
      **登録画面と同じ RLS の中**で動く。この script にできることは UI でできることと同じ。
    ・冊子は必ず **非公開** で作る。--publish を付けたときだけ、読み返し検証を
      通った冊子に限って公開する。
    ・保存済みの設問がある冊子 (同名) には触らない。設問 0 の同名冊子があれば
      そこへ入れ直す (前回の失敗からの再開)。何度回しても二重には入らない。
    ・投入後に必ず読み返して、問数と 1 問目の正解を突き合わせる。
    ・PDF は公開リポジトリに置かない (この script は読むだけ)。

■ ★ node が無くても動く
    設問の検証と DB 形への写像は exam-book-admin-model.mjs が正典だが、
    塾長の Mac に node は無い。ここでは Python で同じ規則を実装し、
    **二重管理のずれは scripts/book_exam/check_import_books.py が
    実物の .mjs と突き合わせて機械的に検出する** (CI で毎回)。
"""
import argparse
import getpass
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONFIG_MJS = os.path.join(ROOT, "exam-book-config.mjs")
# EXAM_PDF_METADATA は検査 (check_import_books.py) が差し替えるためだけの口
METADATA = os.environ.get("EXAM_PDF_METADATA") \
    or os.path.join(ROOT, "lesson-prints", "_metadata.json")

# 科目名 → 制限時間 (分)。本番準拠。bundle の time_limit_min が null のとき使う。
TIME_LIMIT_MIN = {
    "英語R": 80, "国語": 90, "数学IA": 70, "数学IIB": 60,
    "物理": 60, "化学": 60, "生物": 60, "世界史": 60, "日本史": 60,
}

MAX_PDF_BYTES = 52428800          # bucket の上限 (…_storage.sql と揃える)


# =============================================================================
# 設定 (exam-book-config.mjs が正典。書き写さない)
# =============================================================================
def load_config():
    """exam-book-config.mjs から url と anonKey を読む。

    ★ テスト用に EXAM_SUPABASE_URL / EXAM_SUPABASE_ANON で上書きできる。
      本番の値を env に書く必要はない (config が正典)。
    """
    url = os.environ.get("EXAM_SUPABASE_URL", "").strip()
    key = os.environ.get("EXAM_SUPABASE_ANON", "").strip()
    if url and key:
        return url.rstrip("/"), key
    src = open(CONFIG_MJS, encoding="utf-8").read()
    m_url = re.search(r"url:\s*'([^']+)'", src)
    # anonKey は '...' + '...' + '...' と分割して書いてある (改行対策)。全部つなぐ。
    m_key = re.search(r"anonKey:\s*((?:'[^']*'\s*\+?\s*)+)", src)
    if not (m_url and m_key):
        raise SystemExit("✗ exam-book-config.mjs から url / anonKey を読めませんでした")
    key = "".join(re.findall(r"'([^']*)'", m_key.group(1)))
    return m_url.group(1).rstrip("/"), key


# =============================================================================
# HTTP (標準ライブラリだけ。塾長の Mac に何も入れさせない)
# =============================================================================
class Api:
    def __init__(self, base, anon):
        self.base = base
        self.anon = anon
        self.token = None

    def call(self, method, path, body=None, headers=None, raw=None):
        url = self.base + path
        h = {"apikey": self.anon,
             "Authorization": f"Bearer {self.token or self.anon}"}
        if headers:
            h.update(headers)
        data = raw
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode()
            h.setdefault("Content-Type", "application/json")
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:400]
            raise ApiError(f"{method} {path} → {e.code}: {text}") from None
        except urllib.error.URLError as e:
            raise ApiError(
                f"{method} {path} → 接続できない ({e.reason})。\n"
                f"  ・Mac から回しているなら回線を確認\n"
                f"  ・Claude のセッションから回しているなら、環境のネットワーク設定で\n"
                f"    {urllib.parse.urlparse(self.base).hostname} が許可されているか確認"
            ) from None
        return json.loads(text) if text.strip() else None

    def login(self, email, password):
        r = self.call("POST", "/auth/v1/token?grant_type=password",
                      {"email": email, "password": password})
        self.token = r["access_token"]
        return r["user"]["id"]


class ApiError(Exception):
    pass


# =============================================================================
# 検証と DB 形への写像 (正典は exam-book-admin-model.mjs。パリティは CI が見張る)
# =============================================================================
def validate_questions_py(rows):
    """exam-book-admin-model.mjs の validateQuestions と同じ規則。

    ★ ここで弾く目的はただ 1 つ:「全員 0 点」の冊子を作らないこと。
      選択式の正解は 1..choice_count の数字文字列でなければならない。
    @returns エラー文の一覧 (空なら合格)
    """
    errors = []
    if not rows:
        return ["設問が 1 問もありません"]
    seen = {}
    for i, q in enumerate(rows):
        at = f"{i + 1} 行目"
        n = q.get("number")
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            errors.append(f"{at} number: 1 以上の整数にしてください")
        elif n in seen:
            errors.append(f"{at} number: 番号 {n} が {seen[n] + 1} 行目と重複しています")
        else:
            seen[n] = i
        page = q.get("page")
        if page is not None and (not isinstance(page, int) or isinstance(page, bool) or page < 1):
            errors.append(f"{at} page: 1 以上の整数か、空にしてください")
        pts = q.get("points")
        if not isinstance(pts, int) or isinstance(pts, bool) or pts < 1:
            errors.append(f"{at} points: 1 以上の整数にしてください")
        ca = str(q.get("correct_answer") or "").strip()
        if ca == "":
            errors.append(f"{at} correct_answer: 正解を入れてください")
        acc = q.get("accepted_answers") or []
        if q.get("answer_type") == "choice":
            cc = q.get("choice_count")
            if not isinstance(cc, int) or isinstance(cc, bool) or cc < 2 or cc > 10:
                errors.append(f"{at} choice_count: 選択肢の数は 2〜10 にしてください")
            if ca and not re.fullmatch(r"[1-9][0-9]?", ca):
                errors.append(f"{at} correct_answer: 選択式の正解は「1」「2」… の数字で"
                              f"入れてください (0 起算や A・① は不可)")
            elif ca and isinstance(cc, int) and not (1 <= int(ca) <= cc):
                errors.append(f"{at} correct_answer: 1〜{cc} の範囲で入れてください")
            if acc:
                errors.append(f"{at} accepted_answers: 別解は記述のときだけ使えます")
        elif q.get("answer_type") == "short":
            if q.get("choice_count") is not None:
                errors.append(f"{at} choice_count: 記述では選択肢の数を空にしてください")
            if re.fullmatch(r"[0-9]+", ca):
                errors.append(f"{at} correct_answer: 記述の正解が数字だけです。"
                              f"選択式にするつもりではありませんか")
            for a in acc:
                if not str(a).strip():
                    errors.append(f"{at} accepted_answers: 別解に空のものが混ざっています")
        else:
            errors.append(f"{at} answer_type: choice / short 以外 ({q.get('answer_type')!r})")
    return errors


def question_payload_py(q, book_id):
    """exam-book-admin-model.mjs の questionPayload と同じ写像。"""
    acc = q.get("accepted_answers") or []
    return {
        "book_id": book_id,
        "number": q.get("number"),
        "page": q.get("page"),
        "answer_type": q.get("answer_type"),
        "choice_count": q.get("choice_count"),
        "correct_answer": q.get("correct_answer"),
        "accepted_answers": acc if (q.get("answer_type") == "short" and acc) else None,
        "points": q.get("points"),
        "unit_tag": q.get("unit_tag"),
        "explanation": q.get("explanation"),
    }


# =============================================================================
# PDF
# =============================================================================
def pdf_page_count(path):
    """ページ数。lesson-prints/_metadata.json → pypdf の順で見る。

    ★ 当てずっぽうで数えない。page_count が違うと、後から設問にページを
      入れるときの検証 (page ≤ page_count) が狂う。
    """
    name = os.path.basename(path)
    if os.path.exists(METADATA):
        try:
            for p in json.load(open(METADATA, encoding="utf-8"))["prints"]:
                if os.path.basename(p.get("file_path") or "") == name and p.get("pages"):
                    return int(p["pages"]), "_metadata.json"
        except Exception:
            pass
    try:
        from pypdf import PdfReader
        return len(PdfReader(path).pages), "pypdf"
    except ImportError:
        raise SystemExit(
            f"✗ {name} のページ数が分かりません。_metadata.json に無い PDF は"
            f" pypdf が要ります:\n    python3 -m pip install --user pypdf")


def find_pdf(bundle, pdf_dir):
    """bundle に合う問題 PDF を 1 つに絞る。絞れなければ理由を返す。

    ★ 2 つ以上当たったら選ばない。間違った PDF が付くと、生徒は「設問と
      違う冊子」を開くことになり、画面は壊れないのに全部が狂う。

    探す順 (2026-08-15 に実物 8,000 本のフォルダで学んだ):
      1. **元 YAML の名前から組んだ完全一致**。変換器の source が
         「…共通テスト世界史_マーク式.yaml」なら PDF は
         「…共通テスト世界史_マーク式_問題.pdf」(組版の命名規則)。これが一番堅い。
      2. 科目名を含み **_問題.pdf で終わる** もの (「ヒント付き問題」は除く —
         "_ヒント付き問題.pdf" も「問題」を含むので、含む/含まないでは選べない)。
    """
    pdfs = sorted(glob.glob(os.path.join(pdf_dir, "**", "*.pdf"), recursive=True))
    if not pdfs:
        return None, f"PDF が 1 つもありません (探した場所 {pdf_dir})"

    # --- 1. 元 YAML の名前からの完全一致 -----------------------------------
    stem = os.path.splitext(os.path.basename(bundle.get("source") or ""))[0]
    if stem:
        for want in (f"{stem}_問題.pdf", f"{stem}.pdf"):
            got = [p for p in pdfs if os.path.basename(p) == want]
            if len(got) == 1:
                return got[0], None
            if len(got) > 1:
                return None, (f"同じ名前の PDF が {len(got)} 個あります "
                              f"({want})。--pdf-dir をどちらかのフォルダに絞ってください")

    # --- 2. 科目名 + _問題.pdf 終わり (ヒント付きは除く) ---------------------
    subj = bundle.get("subject_name") or ""
    title = (bundle.get("book") or {}).get("title") or ""
    for word in (subj, title):
        if not word:
            continue
        got = [p for p in pdfs
               if word in os.path.basename(p)
               and os.path.basename(p).endswith("_問題.pdf")
               and "ヒント" not in os.path.basename(p)]
        if len(got) > 1:
            # 「数学IA」が「数学IIB」にも部分一致する類いを、より長い一致で絞る
            exact = [p for p in got if f"共通テスト{word}_" in os.path.basename(p)]
            if len(exact) == 1:
                return exact[0], None
            return None, (f"PDF の候補が {len(got)} 個あって選べません "
                          f"({' / '.join(os.path.basename(x) for x in got[:3])})。"
                          f"元 YAML と同名の「{stem or '◯◯'}_問題.pdf」があれば"
                          f"それを最優先で選ぶので、--pdf-dir をその場所にしてください")
        if len(got) == 1:
            return got[0], None
    return None, (f"PDF が見つかりません (探した場所 {pdf_dir}、"
                  f"探した名前 {stem + '_問題.pdf' if stem else (subj or title)!r})")


# =============================================================================
# 取り込み本体
# =============================================================================
def load_bundles(src, only):
    files = sorted(glob.glob(os.path.join(src, "*.json")))
    if only:
        files = [f for f in files if any(k in f for k in only)]
    out = []
    for f in files:
        try:
            b = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            raise SystemExit(f"✗ {os.path.basename(f)} が読めない ({e})")
        if not (isinstance(b, dict) and isinstance(b.get("questions"), list)
                and isinstance(b.get("book"), dict)):
            raise SystemExit(f"✗ {os.path.basename(f)} は変換器の JSON ではありません "
                             f"(book / questions が無い)")
        b["_file"] = f
        out.append(b)
    return out


def existing_book(api, title):
    """同名の冊子と、その保存済み設問数。"""
    q = urllib.parse.quote(title)
    rows = api.call("GET", f"/rest/v1/books?title=eq.{q}"
                           f"&select=id,title,pdf_path,is_published,questions(count)")
    if not rows:
        return None
    b = rows[0]
    n = 0
    qs = b.get("questions")
    if isinstance(qs, list) and qs and isinstance(qs[0], dict):
        n = qs[0].get("count") or 0
    return {"id": b["id"], "pdf_path": b.get("pdf_path"),
            "is_published": b.get("is_published"), "n_questions": n}


def import_one(api, bundle, pdf_dir, publish, dry):
    """1 冊ぶん。@returns (状態, 詳細)  状態: ok / skip / fail"""
    book = bundle["book"]
    title = (book.get("title") or "").strip()
    subj_name = bundle.get("subject_name") or ""
    qs = bundle["questions"]
    if not title:
        return "fail", "タイトルが空"

    # --- 0. 検証 (ネットワークに出る前に)。1 件でも駄目なら触らない --------
    errs = validate_questions_py(qs)
    if errs:
        return "fail", "検証を通らない: " + " / ".join(errs[:3])

    # --- 1. PDF ------------------------------------------------------------
    pdf, why = find_pdf(bundle, pdf_dir)
    if pdf is None:
        return "fail", why
    size = os.path.getsize(pdf)
    if size > MAX_PDF_BYTES:
        return "fail", f"PDF が大きすぎる ({size // 1024 // 1024}MB / 上限 50MB)"
    pages, src = pdf_page_count(pdf)

    tl_min = book.get("time_limit_min")
    if tl_min is None:
        tl_min = TIME_LIMIT_MIN.get(subj_name)

    plan = (f"{title}: {len(qs)} 問 / PDF {os.path.basename(pdf)} "
            f"({pages} 頁・{src}) / 科目 {book.get('subject')} / "
            f"制限 {tl_min if tl_min else '無し'} 分")
    if dry:
        return "ok", "[予行] " + plan

    # --- 2. 冊子の行 (既存があれば再利用) -----------------------------------
    ex = existing_book(api, title)
    if ex and ex["n_questions"] > 0:
        return "skip", (f"同名の冊子に設問が {ex['n_questions']} 問保存済み。触りません "
                        f"(入れ直すなら登録画面で確認を)")
    if ex:
        book_id = ex["id"]
        note = "既存の冊子 (設問 0) に入れ直し"
    else:
        rows = api.call("POST", "/rest/v1/books",
                        {"title": title, "subject": book.get("subject"),
                         "level": book.get("level"),
                         "page_count": pages,
                         "time_limit_sec": tl_min * 60 if tl_min else None,
                         "is_published": False},
                        headers={"Prefer": "return=representation"})
        if not rows:
            return "fail", "冊子の行を作れたか確認できない (返却 0 行)"
        book_id = rows[0]["id"]
        note = "新規"

    # --- 3. PDF を上げる ----------------------------------------------------
    path = f"books/{book_id}.pdf"
    with open(pdf, "rb") as f:
        api.call("POST", f"/storage/v1/object/book-pdfs/{path}",
                 raw=f.read(),
                 headers={"Content-Type": "application/pdf", "x-upsert": "true"})
    upd = api.call("PATCH", f"/rest/v1/books?id=eq.{book_id}",
                   {"pdf_path": path, "page_count": pages},
                   headers={"Prefer": "return=representation"})
    if not upd:
        return "fail", "pdf_path を記録できない (返却 0 行)"

    # --- 4. 設問 ------------------------------------------------------------
    payload = [question_payload_py(q, book_id) for q in qs]
    ins = api.call("POST", "/rest/v1/questions", payload,
                   headers={"Prefer": "return=representation"})
    if not isinstance(ins, list) or len(ins) != len(payload):
        return "fail", (f"設問の投入が {len(ins) if isinstance(ins, list) else 0}"
                        f"/{len(payload)} 行しか確認できない")

    # --- 5. 読み返して検証 --------------------------------------------------
    back = api.call("GET", f"/rest/v1/questions?book_id=eq.{book_id}"
                           f"&select=number,correct_answer&order=number")
    if len(back) != len(qs):
        return "fail", f"読み返すと {len(back)} 問 (入れたのは {len(qs)} 問)"
    want = {q["number"]: str(q["correct_answer"]) for q in qs}
    for row in back:
        if str(row["correct_answer"]) != want.get(row["number"]):
            return "fail", (f"問{row['number']} の正解が食い違う "
                            f"(入れた {want.get(row['number'])} / 読めた {row['correct_answer']})")

    # --- 6. 公開 (指定時のみ・検証を通った冊子だけ) --------------------------
    if publish:
        pub = api.call("PATCH", f"/rest/v1/books?id=eq.{book_id}",
                       {"is_published": True},
                       headers={"Prefer": "return=representation"})
        if not pub:
            return "fail", "公開に切り替えられない (返却 0 行)"

    state = "公開" if publish else "非公開"
    return "ok", f"{note} / {len(qs)} 問 / {pages} 頁 / {state} — {plan.split(': ', 1)[1]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="変換器が --out で書いた JSON のディレクトリ")
    ap.add_argument("--pdf-dir", default=os.path.join(ROOT, "lesson-prints"),
                    help="問題 PDF の場所 (既定 lesson-prints)")
    ap.add_argument("--only", nargs="*", default=[], help="名前で絞る (部分一致)")
    ap.add_argument("--publish", action="store_true",
                    help="検証を通った冊子を公開まで切り替える (既定は非公開で置く)")
    ap.add_argument("--dry-run", action="store_true", help="何も書かずに計画だけ出す")
    a = ap.parse_args()

    bundles = load_bundles(a.src, a.only)
    if not bundles:
        print(f"✗ {a.src} に JSON がありません")
        return 1

    url, anon = load_config()
    api = Api(url, anon)

    if not a.dry_run:
        email = os.environ.get("EXAM_TEACHER_EMAIL", "").strip() \
            or input("講師のメールアドレス: ").strip()
        password = os.environ.get("EXAM_TEACHER_PASSWORD", "") \
            or getpass.getpass("パスワード (画面に出ません): ")
        try:
            uid = api.login(email, password)
        except ApiError as e:
            print(f"✗ ログインできません: {e}")
            return 1
        prof = api.call("GET", f"/rest/v1/profiles?id=eq.{uid}&select=role")
        if not prof or prof[0].get("role") != "teacher":
            print("✗ このアカウントは講師ではありません。登録画面に入れるアカウントで")
            return 1

    print(f"=== 冊子の取り込み ({url}) — {len(bundles)} 冊 ===")
    results = []
    for b in bundles:
        try:
            state, detail = import_one(api, b, a.pdf_dir, a.publish, a.dry_run)
        except (ApiError, SystemExit) as e:
            state, detail = "fail", str(e)
        mark = {"ok": "○", "skip": "→", "fail": "✗"}[state]
        print(f"  {mark} {(b['book'].get('title') or b['_file'])}")
        print(f"      {detail}")
        results.append((state, b))

    ok = [b for s, b in results if s == "ok"]
    fail = [b for s, b in results if s == "fail"]
    skip = [b for s, b in results if s == "skip"]
    print(f"\n  取り込み {len(ok)} / 触らず {len(skip)} / 失敗 {len(fail)}")

    if ok and not a.dry_run:
        print("\n=== 照合表 — 1 冊 1 問だけ、解説 PDF と見比べてください ===")
        for b in ok:
            pv = (b.get("preview") or [{}])[0]
            q1 = b["questions"][0]
            print(f"  {b['book']['title']}: 問{q1['number']} の正解 = {q1['correct_answer']}"
                  + (f" 「{pv.get('correct_text', '')}」" if pv.get("correct_text") else ""))
        if not a.publish:
            print("\n  ★ すべて非公開で置いてあります。照合できたら登録画面で公開に"
                  "切り替えるか、--publish を付けて回し直してください (二重には入りません)")

    if fail:
        print("\n★ 失敗した冊子は途中の状態 (非公開) で残っています。"
              "直して回し直せば続きから入ります (二重には入りません)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
