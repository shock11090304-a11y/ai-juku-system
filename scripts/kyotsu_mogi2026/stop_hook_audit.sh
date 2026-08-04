#!/usr/bin/env bash
# 教材の品質ゲート (Stop フック用)。
#
# セッション終了時に audit.py を走らせ、違反があれば decision:"block" を返して
# Claude に修正させる。CLAUDE.md に書くだけだと「読み落とし」で素通りするため、
# ハーネス側で必ず実行される層を用意する (2026-08-02 塾長指示)。
#
# 出力契約 (Claude Code の Stop フック):
#   合格 → 何も出さずに exit 0 (静かに通す)
#   違反 → {"decision":"block","reason":"..."} を stdout に出す → Claude が修正を求められる
#
# audit.py は約 1 秒。教材ファイルが無いリポジトリ状態では黙って抜ける。
set -uo pipefail

cd "$(dirname "$0")/../.." || exit 0

# 教材 seed が無ければ何もしない (このリポジトリの他の作業を邪魔しない)
ls seed-data/kyotsu_mogi2026_*.json >/dev/null 2>&1 || exit 0

OUT="$(python3 scripts/kyotsu_mogi2026/audit.py 2>&1)"
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  exit 0
fi

# 違反あり: 監査の出力をそのまま理由に載せて block する
python3 - "$OUT" <<'PY'
import json, sys
out = sys.argv[1]
# エラー行だけ抜き出して短くまとめる (全文だと長すぎる)
lines = [l.strip() for l in out.splitlines() if l.strip().startswith('-')]
head = "教材の品質監査 (scripts/kyotsu_mogi2026/audit.py) が失敗しました。"
body = "\n".join(lines[:20]) or out[-1500:]
tail = ("\n\n直し方: 問題は seed JSON を手で直さず、build_eng.py / build_math.py / "
        "build_math_exam.py を修正して再生成すること。PDF がずれている場合は build_pdf.py を再実行。")
print(json.dumps({"decision": "block", "reason": head + "\n" + body + tail}, ensure_ascii=False))
PY
exit 0
