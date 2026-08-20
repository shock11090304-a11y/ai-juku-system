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
sys.exit(0)
