#!/usr/bin/env python3
"""💳 月末引き落としタブの使いやすさ・安全改修 (2026-09-08) の回帰テスト (静的検査 + Vercel 関数の単体検査・本番に触れない)。

3視点レビュー (使いやすさ / お金の安全 / データ整合) で決めた変更が残っていることを機械的に確認する:
  1. 結果モーダルがページ共通の .modal-overlay 方式 (以前は CSS の無い modal-backdrop で最下部に素の表が出ていた)
  2. 状況バナー・ステッパー・絶対月ラベル・名簿列・検索・全選択の要素が index.html にある
  3. app.js: ドライランの指紋ガード / 数名ずつの分割実行 / 失敗理由の日本語化 / 名簿反映の穴埋め / 台帳除外 / 同期
  4. execute.py: 成功履歴のある月は skip・KV エラーと請求済みの skip 理由を区別 (関数を直接呼んで検証)
  5. readonly.py: プレビューが doneStatus (pending=途中停止) を返す
  6. vercel.json: execute 関数の maxDuration
  7. app.js の ?v= が更新されている
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAILURES = []


def check(label, cond, detail=""):
    print(f"  {'✅' if cond else '❌'} {label}" + (f"  — {str(detail)[:300]}" if (detail and not cond) else ""))
    if not cond:
        FAILURES.append(label)


def read(rel):
    return open(os.path.join(REPO, rel), encoding="utf-8").read()


def main():
    print("💳 月末引き落としタブ 改修の回帰テスト\n")
    html = read("payment/index.html")
    js = read("payment/app.js")
    css = read("payment/style.css")

    print("1) 結果モーダル")
    check("modal-backdrop (CSS 未定義のクラス) を使っていない", "modal-backdrop" not in html and ".modal-backdrop" not in css)
    check("結果/reconcile モーダルは .modal-overlay + .modal", html.count('id="monthEndResultModal" class="modal-overlay hidden"') == 1 and html.count('id="reconcileModal" class="modal-overlay hidden"') == 1)
    check("閉じるボタンは data-modal-close (共通ハンドラで閉じる)", 'id="monthEndResultClose" data-modal-close' in html and 'id="reconcileModalClose" data-modal-close' in html)
    check("app.js: モーダル表示に display:'flex' / 'none' の直書きが残っていない", "modal.style.display = 'flex'" not in js and "reconcileModal').style.display = 'none'" not in js)

    print("2) 画面要素")
    for eid in ("monthEndStatusBanner", "monthEndStepper", "monthEndCurLabel", "monthEndNextLabel", "monthEndArrearsNote", "monthEndSearch", "monthEndSelectAll", "monthEndAlreadyLabel", "monthEndRules"):
        check(f"index.html に #{eid}", f'id="{eid}"' in html)
    check("運用ルールは折りたたみ (details)", '<details id="monthEndRules"' in html)
    check("表に「名簿」列 (紐付け / 月謝の食い違い / 入金済)", "名簿との突合" in html and 'colspan="6"' in html)
    check("実行ボタンは初期 disabled (ドライラン後に有効化)", 'id="monthEndExecuteBtn" disabled' in html)
    # ?v= はその後の改修でも進むので「この改修 (2026-09-08) より前の値に戻っていない」ことだけを見る
    _v = re.search(r"app\.js\?v=(\d{8})", html)
    check("app.js の ?v= が更新済み (20260908 以降)", bool(_v) and _v.group(1) >= "20260908", _v.group(0) if _v else "no ?v=")

    print("3) app.js の処理")
    for fn in ("monthEndFingerprint", "monthEndDryRunValid", "monthEndCurrentPlan", "renderMonthEndStepper", "renderMonthEndStatusBanner",
               "describeChargeError", "monthEndApplyLedgerToRoster", "monthEndSyncRosterFromCloud", "monthEndSetModeLabels", "monthEndSetButtonsBusy"):
        check(f"関数 {fn}", f"function {fn}(" in js)
    check("実行は数名ずつ分割 (MONTHEND_CHUNK)", "const MONTHEND_CHUNK = " in js and "chunk(selectedIds, MONTHEND_CHUNK)" in js)
    check("本番実行はドライラン一致が必須", "if (!monthEndDryRunValid(plan))" in js)
    check("本番実行の途中エラーで break し、成功でもエラーでも再プレビュー", "if (!dryRun) break;" in js and "if (!dryRun) setTimeout(() => fetchMonthEndPreview(), 500);   // 成功でもエラーでも必ず最新状態を取り直す" in js)
    check("個別請求・再請求・確定でも名簿に入金反映", js.count("markMonthEndChargedPaid(") >= 5)
    check("滞納判定は台帳で請求済み (カードで引き落とし済) の月を除外", "ledgerIndex" in js and "カードで引き落とし済の" in js)
    check("滞納を含む本番実行の前にクラウドの名簿を同期", "await monthEndSyncRosterFromCloud()" in js)
    check("パスワードは sessionStorage から復元し月末タブでも保存", "sessionStorage.getItem(CHAT_PW_KEY)" in js and "sessionStorage.setItem(CHAT_PW_KEY, v)" in js)
    check("請求対象月モードを記憶", "MONTHEND_BILLMODE_KEY" in js and "localStorage.setItem(MONTHEND_BILLMODE_KEY" in js)
    check("履歴の既定月は請求対象月 (UTC 月ではない)", "toISOString().slice(0, 7)" not in js[js.index("async function fetchChargeHistory"):js.index("function renderChargeHistory")])
    check("失敗理由: 3DS / 残高不足 / 期限切れ / 顧客消失 を日本語化", all(k in js for k in ("authentication_required", "insufficient_funds", "expired_card", "resource_missing")))
    check("KV エラーの skip は請求済みと区別して表示", "kv error" in js)
    # 構文 (jsc があれば)
    jsc = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
    node = shutil.which("node")
    if os.path.exists(jsc):
        r = subprocess.run([jsc, "-e", "try { new Function(readFile('payment/app.js')); print('OK'); } catch (e) { print('ERR ' + e); }"], cwd=REPO, capture_output=True, text=True)
        check("app.js の構文 (jsc)", "OK" in r.stdout, r.stdout + r.stderr)
    elif node:
        r = subprocess.run([node, "--check", "payment/app.js"], cwd=REPO, capture_output=True, text=True)
        check("app.js の構文 (node --check)", r.returncode == 0, r.stderr[:300])
    else:
        print("  ⏭ JS 構文検査はスキップ (jsc/node なし)")

    print("4) execute.py (Vercel 関数) の単体検査")
    spec = importlib.util.spec_from_file_location("ex_mod", os.path.join(REPO, "api", "admin-charge-month-end-execute.py"))
    ex = importlib.util.module_from_spec(spec)
    os.environ.setdefault("UPSTASH_REDIS_REST_URL", "")
    spec.loader.exec_module(ex)
    calls = []
    def fake_redis(cmd, *args):
        calls.append((cmd, args))
        if cmd == "MGET":
            return {"result": [("{\"x\":1}" if ("reg_hit" in k) else None) for k in args]}
        return None
    ex._redis = fake_redis
    hits = ex._history_hits(["reg_a", "reg_hit", "reg_b"], "2026-09")
    check("_history_hits: 成功履歴のある rid だけ返す", hits == {"reg_hit"}, hits)
    check("charge:history:{rid}:{month} を MGET", any(c[0] == "MGET" and "charge:history:reg_hit:2026-09" in c[1] for c in calls), calls[-1:])
    dh = ex._done_hits(["reg_hit", "reg_a"], "2026-09")
    check("_done_hits: charge:done を見る", dh == {"reg_hit"} and any("charge:done:reg_hit:2026-09" in c[1] for c in calls if c[0] == "MGET"), dh)
    ex._redis = lambda cmd, *a: None
    check("KV 応答なしなら hits は空 (安全側ではなく『判定しない』)", ex._history_hits(["reg_hit"], "2026-09") == set())
    src = read("api/admin-charge-month-end-execute.py")
    check("本番ループ: 成功履歴あり → skipped 'history exists'", "if not dry_run and rid in history_hits:" in src and "history exists" in src)
    check("ドライラン: done ロックあり → skipped (本番の結果に近づける)", "if dry_run and rid in done_hits:" in src)
    check("SET NX の応答なしは 'kv error' として請求済みと区別", "kv error" in src and "if nx.get(\"result\") != \"OK\":" in src)
    check("受講開始月より前の月は請求しない (翌月開始の登録月ガード・2026-09-23)", "_before_start_month(r, current_month)" in src and "受講開始月" in src)
    check("_before_start_month: 開始月より前なら開始月・同月/以降/未設定は空・first_charge_month でも判定",
          ex._before_start_month({"start_month": "2026-10"}, "2026-09") == "2026-10" and ex._before_start_month({"start_month": "2026-10"}, "2026-10") == ""
          and ex._before_start_month({"start_month": "2026-10"}, "2026-11") == "" and ex._before_start_month({"first_charge_month": "2026-10"}, "2026-09") == "2026-10"
          and ex._before_start_month({}, "2026-09") == "" and ex._before_start_month(None, "2026-09") == "")
    pdi = read("api/past-due-invoice.py")
    check("💳請求書 API も受講開始月より前の月を拒否", "before_start_month" in pdi and "受講開始月" in pdi)
    check("初回決済で払った月は台帳の有無によらず skip (翌月開始の二重請求の穴・2026-09-23)", "_paid_by_first_charge(r, current_month)" in src and "初回決済で支払済み" in src)
    check("_paid_by_first_charge: first_charge_month == 対象月 だけ True",
          ex._paid_by_first_charge({"first_charge_month": "2026-10"}, "2026-10") is True and ex._paid_by_first_charge({"first_charge_month": "2026-10"}, "2026-11") is False
          and ex._paid_by_first_charge({}, "2026-10") is False and ex._paid_by_first_charge(None, "2026-10") is False)
    check("app.js: 初回決済の月は滞納候補から外す・skip 文言", "pm === startMonth" in js and "初回決済で支払済み" in js)
    check("app.js: 滞納判定の下限は受講開始月・名簿の自動追加は初回決済の月を入塾月に", "c.startMonth" in js and "const floor" in js and "reg.firstChargeMonth : (STATE.currentMonth" in js)

    print("5) readonly.py (プレビュー)")
    ro = read("api/admin-charge-readonly.py")
    check("doneStatus を返す (pending = 途中停止の検出)", '"doneStatus": done_status' in ro and 'done_status = "pending" if str(_dv).strip() == "pending" else "success"' in ro)
    check("history 第二ゲートでも doneStatus=success", 'c["doneStatus"] = "success"' in ro)
    check("プレビューが startMonth を返す (滞納判定の下限)", '"startMonth":' in ro)
    check("プレビューは受講開始月より前を beforeStart にして合計から除く (ready は下ろさない)", '"beforeStart": before_start' in ro and 'if c.get("beforeStart") and c["ready"]' in ro)
    check("app.js: 入塾月より前は未入金/未払い/督促/請求書に出さない・月末タブは beforeStart を請求対象外表示・skip 文言・請求書エラーの日本語",
          js.count("isEnrolledFor(s, month)") >= 5 and "!c.beforeStart" in js and "受講開始月より前の月のため請求しませんでした" in js and "r.message || r.error" in js and "月分なし" in js)

    print("5b) past-due-invoice.py: カードで引き落とし済みの月には請求書を出さない (2026-09-23)")
    spec2 = importlib.util.spec_from_file_location("pdi_mod", os.path.join(REPO, "api", "past-due-invoice.py"))
    pdi_m = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(pdi_m)
    _store = {"charge:history:reg_p:2026-09": json.dumps({"status": "succeeded"}), "charge:history:reg_f:2026-09": json.dumps({"status": "failed", "failed_at": 1}),
              "charge:done:reg_d:2026-09": "pending", "charge:done:reg_s:2026-09": json.dumps({"status": "succeeded"}),
              "charge:done:reg_3ds:2026-09": json.dumps({"status": "requires_action"}), "charge:done:reg_u:2026-09": json.dumps({"status": "uncertain"}),
              "charge:done:reg_bad:2026-09": json.dumps([1, 2])}
    pdi_m._redis_safe = lambda cmd, *a: ({"result": _store.get(a[0])} if cmd == "GET" else None)
    check("成功履歴あり → 出さない", pdi_m._month_paid_by_card("reg_p", "2026-09", {}) is True)
    check("done に成功 → 出さない", pdi_m._month_paid_by_card("reg_s", "2026-09", {}) is True)
    check("失敗履歴だけ → 出せる (振込を頼む場面)", pdi_m._month_paid_by_card("reg_f", "2026-09", {}) is False)
    check("done=pending (処理中) → 成功ではないので出せる扱い", pdi_m._month_paid_by_card("reg_d", "2026-09", {}) is False)
    check("初回決済の月 → 台帳が無くても出さない", pdi_m._month_paid_by_card("reg_x", "2026-10", {"first_charge_month": "2026-10"}) is True)
    check("3DS 待ち / 要確認 の月 → 出さない (先に 🔧 確定)", pdi_m._month_paid_by_card("reg_3ds", "2026-09", {}) is True and pdi_m._month_paid_by_card("reg_u", "2026-09", {}) is True)
    check("台帳の JSON が dict でなくても落ちない・月の形式が不正なら False", pdi_m._month_paid_by_card("reg_bad", "2026-09", {}) is False and pdi_m._month_paid_by_card("reg_p", "", {}) is False and pdi_m._month_paid_by_card("reg_p", "2026-9", {"first_charge_month": ""}) is False)
    check("請求書 API は月の形式を検証する (invalid_month)", "invalid_month" in pdi and "_MONTH_RE.match(month)" in pdi)
    check("請求書 API の本体が _month_paid_by_card を呼ぶ (already_charged_by_card)", "_month_paid_by_card(_rid, month, registered)" in pdi and "already_charged_by_card" in pdi)
    check("プレビューも初回決済の月を「引き落とし済み」扱い", 'str(r.get("first_charge_month") or "").strip() == month_str' in ro)

    print("6) vercel.json")
    v = json.load(open(os.path.join(REPO, "vercel.json"), encoding="utf-8"))
    check("execute 関数の maxDuration が 60 秒", (v.get("functions") or {}).get("api/admin-charge-month-end-execute.py", {}).get("maxDuration") == 60, v.get("functions"))
    check("rewrites / headers は残っている", "rewrites" in v and "headers" in v)

    print()
    if FAILURES:
        print(f"❌ FAIL {len(FAILURES)} 件: " + " / ".join(FAILURES))
        sys.exit(1)
    print("✅ ALL PASS")


if __name__ == "__main__":
    main()
