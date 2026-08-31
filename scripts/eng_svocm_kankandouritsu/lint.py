# -*- coding: utf-8 -*-
"""分解 DSL の契約チェッカ（CLI ＋ ライブラリ）。

    python3 lint.py items.json        # 全件を検査して人が読める形で出す
    python3 lint.py items.json --json # 機械可読（executor / エディタ用）

★check.py はこのファイルの `validate_item()` を import して使う。
  「原稿を書くときに通す検査」と「ビルド前のゲート」を別々に書くと必ず片方だけ緩くなるので、
  契約は**この 1 ファイルにしか書かない**。

items.json の 1 件:
    {"id": "A1",                  # 表示用。任意
     "mode": "drill" | "kaishaku",# drill=第1部（①②③に切り出す）/ kaishaku=第3部（精密分解）
     "dsl":  "{S:...} {V:...} .",
     "en":   "...",               # DSL から復元される英文と 1 文字も違わないこと
     "pat":  "第5文型（SVOC）",
     "notes": ["...", "..."],     # 任意（あれば HTML 健全性を見る）
     "ja":   "..."}               # 任意
"""
import json
import re
import sys

from layout import (
    DRILL_LABELS, PATTERN_CORE, infer_pattern, normalize, parse, plain_text, top_segments,
)

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

# 解説文で許可する HTML タグ。これ以外の生 '<' は Chrome が語ごと飲み込む。
TAG_OK = re.compile(r'</?(?:b|u|i|br|span(?:\s+class="[a-z0-9 _-]+")?)\s*/?>')
ENT_OK = re.compile(r"&(?:lt|gt|amp|nbsp|quot|#\d+);")
PAT_NAME = re.compile(r"第[1-5]文型")


def markup_errors(s):
    """生タグ・未エスケープの & ・タグの開閉不一致を列挙する。"""
    out = []
    for m in re.finditer(r"<", s):
        if not TAG_OK.match(s, m.start()):
            out.append(f"未エスケープの '<'（&lt; と書く）: …{s[m.start():m.start() + 30]}…")
    for m in re.finditer(r"&", s):
        if not ENT_OK.match(s, m.start()):
            out.append(f"未エスケープの '&': …{s[m.start():m.start() + 22]}…")
    opens = sorted(re.findall(r"<(b|u|i|span)\b", s))
    closes = sorted(re.findall(r"</(b|u|i|span)>", s))
    if opens != closes:
        out.append(f"タグの開閉が不一致: open={opens} close={closes}")
    return out


def depth_errors(root):
    """ラベルのダッシュ本数 <= 括弧のネスト深さ。S'' が主節に出るなどを弾く。"""
    out = []

    def walk(nd, d):
        for k in nd.kids:
            if k.kind == "chunk":
                if k.label.count("'") > d:
                    out.append(f"ラベル {k.label} の深さ超過"
                               f"（ネスト深さ {d} / ダッシュ {k.label.count(chr(39))}）: {k.text!r}")
            elif k.kind == "group":
                if k.label.count("'") > d:
                    out.append(f"カタマリのラベル {k.label} の深さ超過（ネスト深さ {d}）")
                walk(k, d + 1)

    walk(root, 0)
    return out


def validate_item(it):
    """1 件を検査して (errors, info) を返す。errors が空なら合格。"""
    errs, info = [], {}
    mode = it.get("mode", "kaishaku")
    dsl = it.get("dsl", "")
    en = normalize(it.get("en", ""))
    pat = it.get("pat", "")

    try:
        root = parse(dsl)
    except ValueError as e:
        return [f"DSL パース失敗: {e}"], info

    recon = plain_text(root)
    info["recon"] = recon
    if recon != en:
        errs.append("復元英文が en と不一致\n"
                    f"     en   : {en}\n"
                    f"     復元 : {recon}")
    if recon[-1:] not in ".?!":
        errs.append(f"文末記号が無い: …{recon[-14:]!r}")
    for bad in "{}[]<>()@":
        if bad in en:
            errs.append(f"en に記号 {bad!r} が混ざっている（DSL をそのまま貼っていないか）")
            break
    errs += depth_errors(root)

    segs = top_segments(root)
    info["segs"] = segs
    top_lbl = [lb for lb, _t, _u in segs]
    info["top_labels"] = top_lbl

    if not any(lb in ("V", "助") for lb in top_lbl):
        errs.append("主節の V（述語動詞）が無い")
    if not any(lb in ("S", "真S") for lb in top_lbl) and "命令文" not in pat:
        errs.append("主節の S が無い（命令文なら pat に「命令文」と書く）")
    for lb, txt, unlabeled in segs:
        if unlabeled:
            errs.append(f"トップレベルにラベルの無い語が残っている: {txt!r}"
                        "（接続詞なら {接:...}、修飾語なら (M: ...) で囲む）")
        elif mode == "drill" and not lb:
            # ★ラベルの無いカタマリ ( … ) は「地の文」ではないので上の検査に掛からない。
            #   第1部では解答欄が1つ空白のまま刷られる（答えの無い番号ができる）ので必ず止める。
            errs.append(f"ラベルの無いカタマリがトップレベルにある: {txt!r}"
                        "（第1部は (M: ...) のように働きを必ず付ける）")

    if mode == "drill":
        bad = [lb for lb in top_lbl if lb and lb not in DRILL_LABELS]
        if bad:
            errs.append(f"第1部の主節ラベルは {DRILL_LABELS} だけ。使えないラベル: {sorted(set(bad))}"
                        "（等位接続で2文をつなぐ形は第1部に出さない）")
        if not (3 <= len(segs) <= 7):
            errs.append(f"切り出しが {len(segs)} 個（3〜7 個にする）")
        if len(segs) != len(set(t for _l, t, _u in segs)):
            errs.append("同じ文字列の区切りが2つある（①②の見分けがつかない）")

    got = infer_pattern(top_lbl)
    info["inferred_pat"] = got
    named = PAT_NAME.findall(pat)
    if not named:
        if "命令文" not in pat:
            errs.append(f"pat に文型の記載が無い: {pat!r}")
    elif got is None:
        errs.append(f"主節ラベル {top_lbl} からは文型を決められない（pat は {named[0]}）")
    elif len(set(named)) == 1 and named[0] != got:
        errs.append(f"pat は {named[0]} だが、主節ラベル {top_lbl} は {got}"
                    f"（{PATTERN_CORE[got]}）")

    for i, n in enumerate(it.get("notes") or []):
        for m in markup_errors(n):
            errs.append(f"notes[{i}]: {m}")
    if it.get("_require_notes") and len(it.get("notes") or []) < 2:
        errs.append("notes が 2 項目未満")
    if it.get("_require_ja") and not it.get("ja"):
        errs.append("ja（和訳）が空")
    return errs, info


def drill_line(segs):
    """判別問題として印字される 1 行（①②③…）を文字で再現する。"""
    return " ".join(f"{CIRCLED[i]}{t}" for i, (_l, t, _u) in enumerate(segs))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    items = json.load(open(argv[1], encoding="utf-8"))
    if isinstance(items, dict):
        items = [items]
    as_json = "--json" in argv
    report, ng = [], 0
    for i, it in enumerate(items, 1):
        errs, info = validate_item(it)
        ng += bool(errs)
        report.append({"id": it.get("id", f"#{i}"), "ok": not errs, "errors": errs,
                       "top_labels": info.get("top_labels"),
                       "inferred_pat": info.get("inferred_pat"),
                       "drill_line": drill_line(info["segs"]) if info.get("segs") else ""})
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for r in report:
            head = "OK  " if r["ok"] else "NG  "
            print(f"{head}{r['id']}  {r['inferred_pat'] or '-'}  {r['top_labels']}")
            if r["drill_line"]:
                print(f"      {r['drill_line']}")
            for e in r["errors"]:
                print(f"      - {e}")
        print(f"\n合計 {len(report)} 件 / NG {ng} 件")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
