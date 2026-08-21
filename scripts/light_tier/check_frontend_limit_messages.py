"""フロントの 429/403 ハンドラが「プラン上限」を一時障害と偽っていないかを機械で見る。

★このゲートを書いた理由 (2026-08-20):
   サーバ側で「上限は握り潰さず 429 を返す」と直したのに、**フロントが 429 を無条件で
   固定文言に置き換えていた**ため、生徒には「短い時間に何度も生成しています (1時間に5回まで)。
   少し時間をおいて…」と出ていた。翌月まで — 生涯枠なら永久に — 直らないものを
   「待てば直る」と案内し、押しても同じ結果になる再試行を促す形。
   人手のレビューで2回とも見落とし、3回目でようやく見つかった。だから機械で落とす。

規約:
  サーバは **プラン上限の 429/403 の detail に `AI_BUDGET_` 接頭辞を付ける**。
  AI を叩くフロントは、429 を扱うなら必ずこの接頭辞を見て、
  ついていれば **サーバの本文をそのまま出す** (固定文言に置き換えない)。

実行: PYTHONUNBUFFERED=1 python3 scripts/light_tier/check_frontend_limit_messages.py
"""
import io
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

# AI を叩く = これらのエンドポイントを参照しているフロントのファイル
AI_ENDPOINTS = ("/api/ai/call", "/api/ai/messages", "/api/curriculum/generate")
# 429 を扱っていると見なすパターン
RE_429 = re.compile(r"(===?\s*429|status\s*===?\s*429|429\s*===?\s*)")
# 接頭辞を見ている証拠
RE_PREFIX = re.compile(r"AI_BUDGET_")
# 接頭辞を剥がしている証拠 (生の "AI_BUDGET_LIGHT:" を画面に出さない)
RE_STRIP = re.compile(r"replace\(\s*/\^AI_BUDGET_")

FAIL = []
CHECKED = []


def scan():
    for name in sorted(os.listdir(ROOT)):
        if not (name.endswith(".js") or name.endswith(".html")):
            continue
        path = os.path.join(ROOT, name)
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if not any(ep in src for ep in AI_ENDPOINTS):
            continue
        handles_429 = bool(RE_429.search(src))
        sees_prefix = bool(RE_PREFIX.search(src))
        strips_prefix = bool(RE_STRIP.search(src))
        CHECKED.append((name, handles_429, sees_prefix, strips_prefix))
        if handles_429 and not sees_prefix:
            FAIL.append(
                f"{name}: 429 を扱っているのに AI_BUDGET_ 接頭辞を見ていない。"
                f"プラン上限を「待てば直る」と誤案内する。"
                f"（直し方: detail が /^AI_BUDGET_[A-Z0-9_]+:/ ならその本文をそのまま出す）"
            )
        if sees_prefix and not strips_prefix:
            FAIL.append(
                f"{name}: 接頭辞を判定しているのに剥がしていない。"
                f"生徒の画面に 'AI_BUDGET_LIGHT:' という内部文字列がそのまま出る。"
            )


def main():
    scan()
    print("=== フロントの上限メッセージ検査 ===")
    print(f"AI を叩くフロント {len(CHECKED)} ファイルを検査")
    for name, h429, prefix, strip in CHECKED:
        mark = "✓" if (not h429 or (prefix and strip)) else "✗"
        print(f"  {mark} {name:28s} 429処理={'有' if h429 else '無'} "
              f"接頭辞判定={'有' if prefix else '無'} 接頭辞剥がし={'有' if strip else '無'}")
    if not CHECKED:
        # ★対象0件は「合格」ではない。パス解決の失敗を緑で通さない。
        print("\n✗ 検査対象が0件。ROOT の解決に失敗している可能性がある。")
        sys.exit(1)
    print()
    if FAIL:
        print(f"=== ✗ 問題 {len(FAIL)} 件 ===")
        for f in FAIL:
            print(f"  ✗ {f}")
        sys.exit(1)
    print("=== ALL PASS (接頭辞) ===")



main()


# ── 追加検査: 上限の例外が Promise.allSettled に握り潰されていないか ───────────
# ★この検査を書いた理由 (2026-08-20):
#   上限 (429) のとき呼び出し元に正しい案内を出すため QUOTA_EXHAUSTED を throw するようにしたが、
#   受け側が Promise.allSettled で、reason を捨てて固定の Error を投げ直していたため、
#   足した「上限に達しました」パネルは **到達不能** だった。人手のレビュー5回目でようやく発覚。
#   allSettled は reject しないので、reason を拾わない限り理由は必ず消える。
RE_QUOTA_BRANCH = re.compile(r"startsWith\(\s*['\"]QUOTA_EXHAUSTED")


def scan_allsettled():
    """QUOTA_EXHAUSTED で分岐しているファイルは、allSettled の reason を拾っているか。"""
    out = []
    for name in sorted(os.listdir(ROOT)):
        if not name.endswith(".js"):
            continue
        path = os.path.join(ROOT, name)
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if not RE_QUOTA_BRANCH.search(src):
            continue
        uses_allsettled = "allSettled" in src
        # ★ファイル単位で ".reason" を探すのでは緩すぎる (別の場所にあれば通ってしまう。
        #   実際に変異テストで素通りした)。**allSettled の結果で分岐している箇所そのもの**を
        #   抜き出して、その中で reason を読んでいるかを見る。
        # ★判定は「ブロック内に reason があるか」ではなく **throw 文そのものが理由を運んでいるか**。
        #   前者だと `console.warn(settled.map(s => s.reason)); throw new Error('...')` のように
        #   「読んで捨てる」形を素通りする (実測で素通りした)。また `_meaningful` を if の外に
        #   出しただけの等価なリファクタを誤検出もしていた。throw の引数だけを見れば両方直る。
        # ★コメントを落としてから走査する。落とさないと、日本語コメント中の「throw」に
        #   正規表現が当たり、コメントの文面で合否が決まる (実測で変異テストを素通りした)。
        src_nc = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
        src_nc = re.sub(r"(?m)^\s*//.*$", "", src_nc)
        src_nc = re.sub(r"(?m)([^:\\'\"])//.*$", r"\1", src_nc)
        # ★判定は2つの意味で厳しくする:
        #   (1) 文字列リテラルを落としてから見る。落とさないと
        #       `throw new Error('... reason lost')` のように **本文に reason と書いただけ**の
        #       握り潰しが緑になる (実測で素通りした)。加えて `.reason` (プロパティ参照) を要求する。
        #   (2) allSettled サイトごとに判定し、**全サイトが理由を運んでいること**を要求する。
        #       OR にすると、新しく足した allSettled が理由を捨てても既存サイトのおかげで緑になる。
        sites = list(re.finditer(r"await\s+Promise\.allSettled", src_nc))
        reads_reason = bool(sites)
        for m in sites:
            tail = src_nc[m.end():m.end() + 4000]
            tm = re.search(r"\bthrow\s+([^;]{0,300});", tail, re.S)
            if not tm:
                continue   # この allSettled は throw で分岐していない = 対象外
            expr = tm.group(1)
            expr_nostr = re.sub(r"'[^']*'|\"[^\"]*\"|`[^`]*`", "''", expr)
            if not re.search(r"\.reason\b", expr_nostr):
                reads_reason = False
        out.append((name, uses_allsettled, reads_reason))
        if uses_allsettled and not reads_reason:
            FAIL.append(
                f"{name}: QUOTA_EXHAUSTED で分岐しているのに allSettled の reason を読んでいない。"
                f"allSettled は reject しないので理由が消え、上限用の分岐に到達しない。"
            )
    return out


_AS = scan_allsettled()
print("=== 上限の例外が allSettled に飲まれていないか ===")
# ★対象0件を「合格」にしない。app.js は必ず QUOTA_EXHAUSTED で分岐しているはずで、
#   0件になるのは (a) 分岐が消された (b) 正規表現がずれた のどちらか = 検査していない状態。
if not any(n == "app.js" for n, _u, _r in _AS):
    print("  ✗ app.js が QUOTA_EXHAUSTED の分岐を持っていない。"
          "上限時の案内が消えたか、この検査の正規表現がずれている。")
    sys.exit(1)
for name, uses, reads in _AS:
    mark = "✓" if (not uses or reads) else "✗"
    print(f"  {mark} {name:28s} allSettled={'有' if uses else '無'} reason参照={'有' if reads else '無'}")
print()
if FAIL:
    print(f"=== ✗ 問題 {len(FAIL)} 件 ===")
    for f in FAIL:
        print(f"  ✗ {f}")
    sys.exit(1)
print("=== ALL PASS (allSettled) ===")


# ── 追加検査: 作り話を「本物」として見せる経路を機械で塞ぐ ────────────────────
# ★2026-08-21。この節は **二度**「壊しても緑」だった。
#   1回目: 識別子の存在確認だったので、目印を残してガードだけ消す変異が素通り。
#   2回目: if 文のテキストは見るが **中身**も**述語の定義**も見ていなかったので、
#          「分岐は残して return を console.warn にする」「getToken を getTokenn と綴る」
#          「空白を1つ足した捏造定数を戻す」「記録の呼び出しを1つ消す」が全部素通り。
#   判定は **効果** (何が起きるか) で書き、下の SELF_TESTS で毎回自分を壊して確かめる。
import re as _re2


def _read(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8", errors="replace").read()


RE_DEMO_SITE = _re2.compile(r"demoResponse\(")
# ★述語の**定義**まで固定する。名前だけ見ると `const _hasSession = false;` や
#   `window.AuthGuard.getTokenn()` (タイポ) で常に false になっても緑になる。
RE_HAS_SESSION_DEF = _re2.compile(
    r"const\s+_hasSession\s*=\s*!!\(\(\s*window\.AuthGuard\s*&&\s*window\.AuthGuard\.getToken\s*&&"
    r"\s*window\.AuthGuard\.getToken\(\)\s*\)\s*\|\|\s*localStorage\.getItem\('ai_juku_session_token'\)\)", _re2.S)
RE_SP_SESSION_DEF = _re2.compile(
    r"const\s+_spHasSession\s*=\s*!!\(\(\s*window\.AuthGuard\s*&&\s*window\.AuthGuard\.getToken\s*&&"
    r"\s*window\.AuthGuard\.getToken\(\)\s*\)\s*\|\|\s*localStorage\.getItem\('ai_juku_session_token'\)\)", _re2.S)
RE_SP_GUARD = _re2.compile(r"if\s*\(\s*!\s*_spHasSession\s*&&")
RE_QUOTA_ASSIGN = _re2.compile(r"_meta\.quotaKnown\s*=\s*isKnownLimit\s*;")
RE_CSKIP_EXPR = _re2.compile(
    r"const\s+_cSkip\s*=\s*_cMeta\.quotaBlocked\s*\|\|\s*_cMeta\.usedDemo\s*\|\|")
RE_ISPLANBLOCK_EXPR = _re2.compile(
    r"const\s+_isPlanBlock\s*=\s*/\^PLAN_BLOCKED:/\.test\(String\(errMsg\)\)")
# demoResponse の呼び出し箇所の基準値 (定義1 + ガード内0 + demo分岐1 + 仮の応答1 = 3)
DEMO_SITE_BASELINE = 3
RE_GATE_WRITER = _re2.compile(r'_record_gate_failure_async\(\s*"([a-z0-9_]+)"')

# 生徒に「この生徒の事実」として出ていた捏造の定数。二度と戻さない。
# ★照合は **空白を全部落としてから**。"78 %" のように1文字空けるだけで抜けられては意味がない。
FABRICATED = [
    ("app.js", "今週の学習時間: 12.5時間", "保護者レポートのプロンプトに直書きされた学習時間"),
    ("app.js", "平均正答率: 78%", "保護者レポートのプロンプトに直書きされた正答率"),
    ("app.js", "学習時間12.5h/週", "面談準備のプロンプトに直書きされた学習データ"),
    ("app.js", "現代文評論 82%", "面談準備のプロンプトに直書きされた架空の単元別正答率"),
    ("app.js", "stats.total || 47", "質問0件の生徒に「47・積極性◎」と出る既定値"),
    ("app.js", "[8, 9.5, 10, 12.5]", "週別学習時間グラフの固定データ"),
    ("app.js", "{ 英語: 70, 数学: 65, 国語: 75 }", "科目別レーダーの架空の既定偏差値"),
    ("app.js", "subjects: { 英語: 60, 数学: 60, 国語: 60 }", "新規登録で発明される偏差値"),
    ("app.js", "subjects.英語 = 75", "一括取込が講座名から推定する偏差値"),
    ("app.js", "s.fee || 39800", "保護者メールに出る架空の請求額"),
    ("index.html", 'id="kpiHours">12.5h', "KPI タイルの固定値 (どこからも代入されない)"),
    ("index.html", 'id="kpiAccuracy">78%', "KPI タイルの固定値"),
    ("index.html", 'id="kpiProgress">64%', "KPI タイルの固定値"),
    ("index.html", 'id="kpiQuestions">47', "KPI タイルの固定値"),
]


def _nows(t):
    """空白を全部落とす (「78 %」で抜けられないように)。"""
    return _re2.sub(r"\s+", "", t)


def _strip_js_comments(src):
    out = _re2.sub(r"/\*.*?\*/", " ", src, flags=_re2.S)
    out = _re2.sub(r"(?m)^\s*//.*$", "", out)
    out = _re2.sub(r"(?m)([^:\\'\"])//.*$", r"\1", out)
    return out


def _strip_html_comments(src):
    return _re2.sub(r"<!--.*?-->", " ", src, flags=_re2.S)


def _demo_body(src):
    """demoResponse 本体だけを返す (無ければ空文字)。
    ★以前は buildDemo* も一緒に落としていて、app.js の 981 行 (8.6%) が検査から消えていた。
      落とす範囲は **サンプル文言が実在する demoResponse だけ**に絞る。"""
    lines = src.split("\n")
    out, inside = [], False
    for line in lines:
        if line.startswith("function "):
            inside = line.startswith("function demoResponse(")
        if inside:
            out.append(line)
    return "\n".join(out)


def _block_after(src, opener):
    """`opener` で始まるブロックの中身を、波括弧を数えて返す。無ければ空文字。"""
    i = src.find(opener)
    if i < 0:
        return ""
    j = src.find("{", i)
    if j < 0:
        return ""
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j + 1:k]
        k += 1
    return ""


def check_all(app_src, ee_src, html_src, main_src, ceo_src):
    """全項目をまとめて判定し、失敗メッセージの一覧を返す。
    ★**引数で受け取る**こと。ファイルを直接読むと SELF_TESTS で変異を流し込めない。"""
    fails = []

    # (1) 上限だと断定できるか (quotaKnown) を呼び出し元へ渡しているか
    if not RE_QUOTA_ASSIGN.search(app_src):
        fails.append("app.js: `_meta.quotaKnown = isKnownLimit;` が無い。定数を代入すると、"
                     "上限だと断定できない 429 でも注意書きが「上限のため」になり本文と食い違う。")
    if "_cMeta.quotaKnown" not in app_src:
        fails.append("app.js: カリキュラムの注意書きが _cMeta.quotaKnown を読んでいない。")
    # ★述語は**式そのもの**を固定する。`const _cSkip = false;` に書き換えるだけで
    #   作り話の保存抑止も注意書きも丸ごと消える (存在確認だけでは捕まらない)。
    if not RE_CSKIP_EXPR.search(app_src):
        fails.append("app.js: _cSkip の式が想定と違う。定数化すると作り話のカリキュラムが"
                     "保存され、注意書きも出なくなる。")
    if not RE_ISPLANBLOCK_EXPR.search(ee_src):
        fails.append("english-exam.js: _isPlanBlock の式が想定と違う。定数化すると"
                     "プラン制限が「一時的なエラー」として再試行を促す表示に戻る。")

    # (2) demoResponse (作り話) の**全呼び出し**が守られているか
    #     ★見るのは3つ: 述語の定義 / 分岐の存在 / **分岐の中身が実際に return しているか**。
    # ★search ではなく **全定義**を数える。app.js には _hasSession の定義が2つある
    #   (callClaude と callClaudeVision)。search だと片方を壊してももう片方で緑になる。
    _n_decl = len(_re2.findall(r"const\s+_hasSession\s*=", app_src))
    _n_ok = len(RE_HAS_SESSION_DEF.findall(app_src))
    if _n_decl == 0 or _n_ok != _n_decl:
        fails.append(f"app.js: _hasSession の定義 {_n_decl} 個のうち {_n_ok} 個しか正規形でない。"
                     "述語が常に false になる書き換え (メソッド名のタイポ・定数化) で、"
                     "ログイン済みの生徒に作り話が戻る。")
    guard_body = _block_after(app_src, "if (_hasSession) {")
    if not guard_body:
        fails.append("app.js: `if (_hasSession) {` の分岐が無い。")
    else:
        if "jsonSafeFallback(" not in guard_body:
            fails.append("app.js: _hasSession の分岐が JSON kind を jsonSafeFallback に回していない。"
                         "problems の呼び出し元で JSON.parse が落ちる。")
        if guard_body.count("return") < 2:
            fails.append("app.js: _hasSession の分岐が return していない (中身を握り潰す書き換え)。"
                         "分岐だけ残して中身を消すと、そのまま下の demoResponse に落ちる。")
        # ★★これが本丸。「return が2個ある」は「作り話を返していない」を意味しない。
        #   ガードの中で demoResponse に差し戻す1行を入れるだけで、上の3項目を全部満たしたまま
        #   ログイン済みの生徒に架空の添削・弱点診断・保護者レポート・面談メモが戻る
        #   (敵対レビューが実演: 判定4項目すべて通過して緑だった)。**中身そのもの**を見る。
        if "demoResponse(" in guard_body:
            fails.append("app.js: _hasSession の分岐の中で demoResponse を返している。"
                         "ここは『ログイン済みには作り話を返さない』ための分岐なので、"
                         "作り話を返した瞬間にこの検査の目的が消える。")
        if "AI に接続できませんでした" not in guard_body:
            fails.append("app.js: _hasSession の分岐が正直な文言を返していない。"
                         "作り話でも上限案内でもない何かに差し替わっている。")
    sites = [m.start() for m in RE_DEMO_SITE.finditer(app_src)]
    # ★呼び出し箇所を**基準値で固定**する (このリポジトリの _pii_baseline / BASELINE と同じ流儀)。
    #   「前後 1600 字に if (_hasSession) があるか」だけだと、既存ガードの近くに無防備な
    #   呼び出しを1本足すだけで通ってしまう (敵対レビューが実演)。数が変わったら必ず人が見る。
    if len(sites) != DEMO_SITE_BASELINE:
        fails.append(f"app.js: demoResponse( の呼び出しが {len(sites)} 箇所 "
                     f"(基準値 {DEMO_SITE_BASELINE})。増減したら**必ず目で確認**し、"
                     "正当なら DEMO_SITE_BASELINE を実数に更新すること。")
    if not sites:
        fails.append("app.js: demoResponse( が1つも無い。目印が変わったのでこの検査はずれている。")
    for i in sites:
        win = app_src[max(0, i - 1600):i]
        if not ("if (_hasSession)" in win or "仮の応答" in win):
            fails.append("app.js: demoResponse の呼び出しが `if (_hasSession)` でも「仮の応答」表示でも"
                         "守られていない。backend が落ちただけのとき、ログイン済みの生徒に"
                         "架空の添削・弱点診断・保護者レポートが本物として描画される。")
            break

    # (3) speaking の固定スコア: 述語の定義と条件式の両方
    _sp_decl = len(_re2.findall(r"const\s+_spHasSession\s*=", app_src))
    _sp_ok = len(RE_SP_SESSION_DEF.findall(app_src))
    if _sp_decl == 0 or _sp_ok != _sp_decl:
        fails.append(f"app.js: _spHasSession の定義 {_sp_decl} 個のうち {_sp_ok} 個しか正規形でない。"
                     "常に false になる書き換えで、AI管理生に「発音72/文法68/流暢さ75」が戻る。")
    # ★callClaudeVision のガードも固定する。ここは差分のコメントが「作法を確立した関数」と
    #   呼んでいる当のコードなのに、条件式を誰も検査していなかった (敵対レビューが実演)。
    #   `&& !_hasSession` を外すと、detectBackendAI が3秒 timeout でこけただけで
    #   課金中・ログイン済みの生徒が模試写真をアップしたとき、架空の
    #   「全統記述模試 英語145/200 偏差値65…」が解析結果として返る。
    if "if (state.mode === 'demo' && !_hasSession) {" not in app_src:
        fails.append("app.js: callClaudeVision のガードが `state.mode === 'demo' && !_hasSession` "
                     "でない。`&& !_hasSession` を外すと、ログイン済みの生徒に架空の模試結果が"
                     "「解析結果」として返る (apiKey 無しの生徒は必ず mode='demo' に落ちるため)。")

    sp = app_src.find('{"pronunciation": 72')
    if sp < 0:
        fails.append('app.js: 目印 \'{"pronunciation": 72\' が無い。この検査はずれている。')
    elif not RE_SP_GUARD.search(app_src[max(0, sp - 1200):sp]):
        fails.append("app.js: speaking のサンプル採点の**条件式**が _spHasSession を見ていない。")

    # (4) _isPlanBlock / _planMsg が fallback alert から見える位置で宣言されているか
    i_alert = ee_src.find("alert('採点中にエラーが発生しました")
    box_decl = "const box = document.getElementById('questionBox');"
    if i_alert < 0:
        fails.append("english-exam.js: fallback alert が見つからない。この検査はずれている。")
    else:
        for name in ("const _isPlanBlock", "const _planMsg"):
            i_decl = ee_src.find(name)
            if not (0 <= i_decl < i_alert and box_decl in ee_src[i_decl:i_alert]):
                fails.append(f"english-exam.js: {name} が if (box) の内側で宣言されている"
                             "(または alert より後)。fallback alert が ReferenceError になり、"
                             "採点失敗の案内が丸ごと消える。")
        if "_isPlanBlock" not in ee_src[max(0, i_alert - 400):i_alert]:
            fails.append("english-exam.js: fallback alert が _isPlanBlock で分岐していない。"
                         "内部 marker 'PLAN_BLOCKED:' が生徒の画面に素で出る。")

    # (5) 捏造の定数が戻っていないか (空白を落として照合・コメントは対象外)
    demo = _demo_body(app_src)
    app_wo_demo = app_src.replace(demo, "") if demo else app_src
    stripped = {"app.js": _nows(_strip_js_comments(app_wo_demo)),
                "index.html": _nows(_strip_html_comments(html_src))}
    # ★金額はブラックリストでは守れない (数字を変えれば抜ける)。**書き方**を固定する。
    # ★禁止するのは「0 以外の既定値」。`s.fee || 0` は「金額なし」を表す正当な書き方なので通す。
    _fee_default = _re2.search(r"s\.fee\s*\|\|\s*([1-9]\d*)", _strip_js_comments(app_src))
    if _fee_default:
        fails.append(f"app.js: 金額が `s.fee || {_fee_default.group(1)}` になっている。"
                     "取込生徒は fee=0 (falsy) なので**常にその金額**が保護者へ送られる。"
                     "金額が無いときは金額を書かないこと (三項で出し分ける)。")
    for fname, needle, why in FABRICATED:
        if _nows(needle) in stripped[fname]:
            fails.append(f"{fname}: 捏造の定数 {needle!r} が復活している ({why})。")

    # (5b) 検査から外した demoResponse 本体に、**表示や状態を書き換える処理**を入れていないか
    #      ★対象外の帯は「サンプル文言の置き場」なので、そこに実処理を書くと検査の死角になる。
    # ★語の列挙は必ず漏れる (querySelector / textContent / sessionStorage が素通りした)。
    #   「文字列を返すだけ」から外れる手段をまとめて塞ぐ。
    for bad in ("document.", "window.", "localStorage", "sessionStorage", "fetch(",
                "XMLHttpRequest", ".textContent", ".innerHTML", ".value ="):
        if bad in demo:
            fails.append(f"app.js: demoResponse 本体に {bad!r} がある。ここは検査対象外の帯なので、"
                         "実処理を置くと捏造の検査をすり抜ける。文字列を返すだけにすること。")

    # (6) gate event の書き手と、読める場所が一致しているか
    #     ★subset ではなく **集合として一致**を要求する。subset だと書き手を消しても緑になる。
    written = set(RE_GATE_WRITER.findall(main_src))
    m_names = _re2.search(r"_GATE_EVENT_NAMES\s*=\s*\((.*?)\)", main_src, _re2.S)
    declared = set(_re2.findall(r'"([a-z0-9_]+)"', m_names.group(1))) if m_names else set()
    if not declared:
        fails.append("server/main.py: _GATE_EVENT_NAMES が読めない。この検査はずれている。")
    if written != declared:
        fails.append(f"server/main.py: gate event の書き手と _GATE_EVENT_NAMES が一致しない "
                     f"(書き手のみ={sorted(written - declared)} / 宣言のみ={sorted(declared - written)})。"
                     "呼び出しを消すと記録されず、宣言だけ足すと集計に出ない名前ができる。")
    # 読める場所: monitor/status の集計と ceo.html のラベル
    # ★3段すべてを要求する。1段でも欠けると「events に書いたのに誰も見ない」に戻る。
    #   (a) snapshot に載る → (b) アラート判定が読む → (c) エンドポイントが返す
    #   ★以前は「_collect_gate_failures という語があるか」だけを見ていたので、
    #     snapshot から外す変異が緑で通った (実測)。行そのものを固定する。
    if '"gate_failures": _collect_gate_failures(),' not in main_src:
        fails.append("server/main.py: _collect_health_snapshot が gate_failures を載せていない。"
                     "載せないと _evaluate_alerts から見えず、総合バッジが「✅ 全システム正常」のままになる。")
    if 'snapshot.get("gate_failures")' not in main_src:
        fails.append("server/main.py: _evaluate_alerts / monitor/status が snapshot の gate_failures を"
                     "読んでいない。CEO ダッシュの「監視・運用」は既定で display:none なので、"
                     "アラートに昇格させないと実質誰も見ない。")
    if '"key": "gate_failure_open"' not in main_src:
        fails.append("server/main.py: gate_failure_open アラートが無い。"
                     "フェイルオープンが何件あってもバッジは正常のままになる。")
    # ★ラベルの網羅も見る。見ていないのに main.py のコメントで「照合する」と書いていた
    #   (= ルール化したのに効かない、の典型)。名前を足してラベルを忘れると、
    #   塾長の画面に生の英語 event 名が出る。
    m_lbl = _re2.search(r"GATE_FAILURE_LABELS\s*=\s*\{(.*?)\n    \};", ceo_src, _re2.S)
    if not m_lbl:
        fails.append("ceo.html: GATE_FAILURE_LABELS が読めない。この検査はずれている。")
    else:
        # ★ラベルが揃っていても、呼び出しを消す/頭で return するだけで表示は死ぬ。
        if "renderGateFailures(data.gate_failures)" not in ceo_src:
            fails.append("ceo.html: loadMonitorHealth が renderGateFailures(data.gate_failures) を"
                         "呼んでいない。ラベルが揃っていても画面には何も出ない。")
        _rg = _block_after(ceo_src, "function renderGateFailures(gf) {")
        _first = [ln.strip() for ln in _rg.split("\n")
                  if ln.strip() and not ln.strip().startswith("//")]
        if not _first or "monGateFailuresBox" not in _first[0]:
            fails.append("ceo.html: renderGateFailures の先頭が描画先の取得になっていない "
                         f"(先頭: {_first[0][:60] if _first else 'なし'})。"
                         "頭で return すると、ラベルも呼び出しも残ったまま表示だけ死ぬ。")
        labelled = set(_re2.findall(r"'([a-z0-9_]+)'\s*:", m_lbl.group(1)))
        missing = declared - labelled
        if missing:
            fails.append(f"ceo.html: GATE_FAILURE_LABELS にラベルの無い gate event {sorted(missing)}。"
                         "塾長の監視パネルに生の英語名がそのまま出る。")
    return fails


# ── ゲート自身の自己テスト ──────────────────────────────────────────────
# ★変異は「敵対レビューが実際に緑にできた壊し方」を採用する。自分が書いた編集の裏返しだけだと、
#   著者の想像の範囲しか測れない (それで2回とも見逃した)。
def _self_test(app_src, ee_src, html_src, main_src, ceo_src):
    muts = [
        ("quotaKnown を定数に", lambda a, e, h, m, c:
            (a.replace("_meta.quotaKnown = isKnownLimit;", "_meta.quotaKnown = true;"), e, h, m, c)),
        ("_hasSession の分岐だけ削除 (宣言は残す)", lambda a, e, h, m, c:
            (_re2.sub(r"if \(_hasSession\) \{.*?\n    \}\n", "", a, count=1, flags=_re2.S), e, h, m, c)),
        ("★分岐は残して中身の return を潰す", lambda a, e, h, m, c:
            (a.replace("if (isJsonKind) return jsonSafeFallback('no backend (logged in)');",
                       "if (isJsonKind) console.warn('no backend');", 1)
              .replace("      return '⚠️ ただいま AI に接続できませんでした。",
                       "      console.warn('⚠️ ただいま AI に接続できませんでした。", 1), e, h, m, c)),
        # ★変異は **_hasSession の定義**を狙うこと。app.js の最初の getToken() は
        #   _aiCallToken (L1437) で、そこを書き換えても述語は壊れない = 変異が空振りする。
        ("★述語をタイポで常に false に", lambda a, e, h, m, c:
            (_re2.sub(r"(const _hasSession = !!\(\(window\.AuthGuard && window\.AuthGuard\.getToken"
                      r" && window\.AuthGuard\.getToken)(\(\))", r"\1n\2", a, count=1), e, h, m, c)),
        ("★speaking の述語を定数 false に", lambda a, e, h, m, c:
            (_re2.sub(r"const _spHasSession = !!\(\(window\.AuthGuard.*?\);",
                      "const _spHasSession = false;", a, count=1, flags=_re2.S), e, h, m, c)),
        ("speaking のガード条件を元に戻す", lambda a, e, h, m, c:
            (a.replace("if (!_spHasSession && (state.mode === 'demo' || !state.apiKey))",
                       "if (state.mode === 'demo' || !state.apiKey)"), e, h, m, c)),
        ("_planMsg だけ if (box) の内側へ", lambda a, e, h, m, c:
            (a, e.replace("    const _planMsg = String(errMsg).replace(/^PLAN_BLOCKED:/, '');\n", "", 1)
                  .replace("      const errBanner = document.createElement('div');",
                           "      const _planMsg = String(errMsg).replace(/^PLAN_BLOCKED:/, '');\n"
                           "      const errBanner = document.createElement('div');", 1), h, m, c)),
        ("★空白を足した捏造定数を戻す", lambda a, e, h, m, c:
            (a.replace("AIへの質問数 (この端末に残っている記録): ${_pStats.total || 0}件",
                       "平均正答率:  78 %", 1), e, h, m, c)),
        ("★demoResponse 本体に実処理を書く", lambda a, e, h, m, c:
            (a.replace("function demoResponse(system, user, options) {",
                       "function demoResponse(system, user, options) {\n"
                       "  document.getElementById('kpiHours').textContent = '12.5h';", 1), e, h, m, c)),
        ("★gate event の書き手を1つ消す", lambda a, e, h, m, c:
            (a, e, h, _re2.sub(r'_record_gate_failure_async\(\s*"route_gate_middleware_failed".*?\}\)',
                               "pass", m, count=1, flags=_re2.S), c)),
        ("snapshot から集計を外す", lambda a, e, h, m, c:
            (a, e, h, m.replace('"gate_failures": _collect_gate_failures(),', "", 1), c)),
        ("★アラートへの昇格を外す (バッジが正常のままになる)", lambda a, e, h, m, c:
            (a, e, h, m.replace('"key": "gate_failure_open"', '"key": "gate_failure_disabled"', 1), c)),
        # ★ラベルを忘れると塾長の画面に生の英語 event 名が出る。main.py のコメントが
        #   「照合する」と書いていたのに実際は見ていなかったので、検査を足した。
        ("★ceo.html のラベルを1つ落とす", lambda a, e, h, m, c:
            (a, e, h, m, c.replace("      'light_consume_failed': '🔓 ライト上限の計上失敗',\n", "", 1))),
        # ── ここから下は 2026-08-21 の敵対レビューが**実際に緑にできた**壊し方 ──────────
        #   著者の想像の外から来た変異なので、自己テストとしての価値が高い。消さないこと。
        ("★★ガードの中で demoResponse に差し戻す (F1)", lambda a, e, h, m, c:
            (a.replace("      return '⚠️ ただいま AI に接続できませんでした。",
                       "      return demoResponse(systemPrompt, userMessage, options); // '", 1), e, h, m, c)),
        ("★demoResponse 本体に querySelector で書き込む (F2)", lambda a, e, h, m, c:
            (a.replace("function demoResponse(system, user, options) {",
                       "function demoResponse(system, user, options) {\n"
                       "  document.querySelector('#kpiHours').textContent = '12.5h';", 1), e, h, m, c)),
        ("★金額の既定値を別の数字で復活 (F3)", lambda a, e, h, m, c:
            (a.replace("${s.fee ? '¥' + s.fee.toLocaleString() + '（税込）' : '別途ご案内いたします'}",
                       "¥${(s.fee || 24980).toLocaleString()}（税込）", 1), e, h, m, c)),
        ("★無防備な demoResponse 呼び出しを1本足す (F6)", lambda a, e, h, m, c:
            (a.replace("    _meta.usedDemo = true;   // ★作り話。",
                       "    if (kind === 'x') return demoResponse(systemPrompt, userMessage, options);\n"
                       "    _meta.usedDemo = true;   // ★作り話。", 1), e, h, m, c)),
        ("★_isPlanBlock を定数 false に (F7)", lambda a, e, h, m, c:
            (a, e.replace("const _isPlanBlock = /^PLAN_BLOCKED:/.test(String(errMsg));",
                          "const _isPlanBlock = false;", 1), h, m, c)),
        ("★_cSkip を定数 false に (F8)", lambda a, e, h, m, c:
            (_re2.sub(r"const _cSkip = _cMeta\.quotaBlocked[^;]*;",
                      "const _cSkip = false; void _cMeta.quotaKnown;", a, count=1), e, h, m, c)),
        ("★描画の呼び出しを消す (F9)", lambda a, e, h, m, c:
            (a, e, h, m, c.replace("        renderGateFailures(data.gate_failures);\n", "", 1))),
        ("★★vision のガードから !_hasSession を外す", lambda a, e, h, m, c:
            (a.replace("if (state.mode === 'demo' && !_hasSession) {",
                       "if (state.mode === 'demo') {", 1), e, h, m, c)),
        ("★描画の先頭で return する (F10)", lambda a, e, h, m, c:
            (a, e, h, m, c.replace("    function renderGateFailures(gf) {\n",
                                   "    function renderGateFailures(gf) {\n      if (true) return;\n", 1))),
    ]
    missed, inert = [], []
    for label, mutate in muts:
        mutated = mutate(app_src, ee_src, html_src, main_src, ceo_src)
        if mutated == (app_src, ee_src, html_src, main_src, ceo_src):
            # ★変異が当たらなかった = アンカーが消えた。「見逃した」とは区別して報告する
            #   (混同すると、退行ではなくゲート自身を疑う方向に診断が向く)。
            inert.append(label)
            continue
        if not check_all(*mutated):
            missed.append(label)
    return missed, inert, [m[0] for m in muts]


_app = _read("app.js")
_ee = _read("english-exam.js")
_html = _read("index.html")
_main = io.open(os.path.join(ROOT, "server", "main.py"), encoding="utf-8", errors="replace").read()
_ceo = _read("ceo.html")

print()
print("=== ゲート自身の自己テスト (壊したら落ちるか) ===")
_missed, _inert, _labels = _self_test(_app, _ee, _html, _main, _ceo)
for label in _labels:
    mark = "✗" if label in _missed else ("?" if label in _inert else "✓")
    print(f"  {mark} {label}")
if _inert:
    print(f"\n=== ✗ 変異が当たらなかった {len(_inert)} 件 = 目印が変わっている。検査を直すこと ===")
    sys.exit(1)
if _missed:
    print(f"\n=== ✗ この検査は {len(_missed)} 件の壊し方を見逃す。緑を名乗れない ===")
    sys.exit(1)

print()
print("=== 作り話を本物として見せる経路 ===")
_FE_FAIL = check_all(_app, _ee, _html, _main, _ceo)
print(f"  demoResponse の呼び出し: {len(RE_DEMO_SITE.findall(_app))} 箇所")
print(f"  捏造の定数チェック: {len(FABRICATED)} 件 (空白を落として照合)")
_names = sorted(set(RE_GATE_WRITER.findall(_main)))
print(f"  gate event: {len(_names)} 種 (書き手と _GATE_EVENT_NAMES の集合一致を要求)")
if _FE_FAIL:
    print(f"\n=== ✗ 問題 {len(_FE_FAIL)} 件 ===")
    for f in _FE_FAIL:
        print(f"  ✗ {f}")
    sys.exit(1)
print("=== ALL PASS (作り話の経路) ===")
sys.exit(0)
