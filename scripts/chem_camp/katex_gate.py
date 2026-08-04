#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全問の $...$ を実際に KaTeX に食わせ、1つでもパースエラーがあれば落とすゲート。

  python3 katex_gate.py

なぜ要るか: build_chem.py は renderMathInElement を throwOnError:true で呼ぶ。
1つの数式がパースエラーになると、その数式は**描画されずに $0\\,^\\circ\\mathrm{C}$ のような
生の LaTeX ソースのまま印刷される**。PDF は正常に生成されるのでビルドは成功したように見え、
実際に紙を見るまで気づかない。実例: `\\,^\\circ`(薄いスペースの直後に上付き)は
KaTeX が "Got group of unknown type: 'internal'" で落とす —— \\ (バックスラッシュ+空白)なら通る。
"""
import os, re, sys, json, subprocess
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
KATEX = "file://" + os.path.join(REPO, "vendor", "katex")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MATH_RE = re.compile(r"\$([^$]+)\$")


def collect():
    """{数式: [出現場所...]} を返す。"""
    found, uno = {}, 0
    for n in range(1, 7):
        d = json.load(open(os.path.join(HERE, "parts_private", f"part{n}.json"), encoding="utf-8"))
        for m in MATH_RE.finditer(d.get("overview", "")):
            found.setdefault(m.group(1), []).append(f"part{n}:overview")
        for u in d["units"]:
            uno += 1
            for j, q in enumerate(u["problems"], 1):
                for field in ("stem", "answer", "explanation"):
                    for m in MATH_RE.finditer(q.get(field) or ""):
                        found.setdefault(m.group(1), []).append(f"C{uno:02d}-{j}:{field}")
    return found


RAW_TEX = re.compile(r"\\(?:mathrm|dfrac|frac|times|Delta|rightarrow|circ|log|sum)\b|\$")
OUTPUTS = ["kagaku_riron_soufukushu.pdf", "kagaku_jiko_saiten_sheet.pdf",
           "kagaku_shindan_key.pdf", "gasshuku_gakushu_keikaku.pdf"]


def scan_outputs():
    """出来上がった PDF 側に生の LaTeX が残っていないかを見る。

    ★問題集のソースだけ検査していたせいで、診断キーのビルドが KaTeX を読み込んで
      いないこと(=全128式が生ソースで印刷される)を素通りさせた。作った PDF は
      すべて見る。
    """
    bad = 0
    for name in OUTPUTS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            # ★以前はここで「(未生成)」と出して素通りし、**PDFが1つも無くても
            #   このゲートは PASS していた**。「直したのにビルドし忘れ」と同じ型で、
            #   検査していないのに検査した扱いになる。未生成は違反として数える。
            #   （PDFはリポジトリに置かないので、CI では run_all_gates.py が
            #     --no-pdf でこのゲートごと対象外にし、外したことを一覧に出す。）
            bad += 1
            print(f"  NG {name}: PDF が無い＝この紙は検査できていない（build を回すこと）")
            continue
        hits = []
        for i, page in enumerate(fitz.open(path), 1):
            m = RAW_TEX.search(page.get_text())
            if m:
                hits.append((i, m.group(0)))
        if hits:
            bad += len(hits)
            print(f"  NG {name}: {len(hits)}ページに生の LaTeX  例 p{hits[0][0]} '{hits[0][1]}'")
        else:
            print(f"  OK {name}: 生の LaTeX なし")
    return bad


def main():
    found = collect()
    exprs = list(found)
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<script src="{KATEX}/katex.min.js"></script></head>
<body><pre id="out" style="font-size:6pt;white-space:pre-wrap"></pre>
<script>
var tests = {json.dumps(exprs, ensure_ascii=False)};
var bad = [];
for (var i = 0; i < tests.length; i++) {{
  try {{ katex.renderToString(tests[i], {{throwOnError:true, strict:false}}); }}
  catch (e) {{ bad.push("###" + i + "@@@" + e.message.slice(0,90)); }}
}}
document.getElementById("out").textContent =
  "TOTAL " + tests.length + " BAD " + bad.length + "\\n" + bad.join("\\n");
document.title = "done";
</script></body></html>"""
    hp = os.path.join(HERE, "_katex_gate.html")
    pp = os.path.join(HERE, "_katex_gate.pdf")
    open(hp, "w", encoding="utf-8").write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", f"--print-to-pdf={pp}", "file://" + hp],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    txt = "".join(p.get_text() for p in fitz.open(pp))
    # PDF 抽出はタブや折り返しを改行に変えるので、独自マーカーで拾い直す
    head = re.search(r"TOTAL (\d+) BAD (\d+)", txt)
    if not head:
        sys.exit("KaTeX ゲートの実行に失敗(出力を読めなかった)")
    total, nbad = int(head.group(1)), int(head.group(2))
    print(f"KaTeX 数式 {total} 個を実際にレンダリング → 失敗 {nbad} 個")
    nbad += scan_outputs()
    if nbad:
        for chunk in txt.replace("\n", " ").split("###")[1:]:
            m = re.match(r"\s*(\d+)\s*@@@\s*(.*)", chunk)
            if not m:
                continue
            i = int(m.group(1))
            e = exprs[i] if i < len(exprs) else "?"
            print(f"  FAIL  ${e}$\n        {m.group(2).strip()[:80]}\n"
                  f"        出現({len(found[e])}箇所): {', '.join(found[e][:5])}")
    return 1 if nbad else 0


if __name__ == "__main__":
    sys.exit(main())
