"""読むだけ: 高校生 単元別 (弱点克服) 91 カードについて、本番の公開 bank API が生徒の画面と同じ条件で返す行・小問を数える。
    python3 scripts/kosei_dojo/eibunpo_v2/kosei_baseline.py
出力: カードごとに 行数 / 小問 / unitExact 後の小問 / unit タグ無しの小問 / 出どころ(source)の内訳 → ~/Desktop/kosei_baseline_<日付>.json。
本番には何も書かない。build.py は最新の kosei_baseline_*.json を本番の基準として読む (_lib.baseline_rows)。
★本番 API につなぐので CI からは回さない (名前はゲートの規則に当たらない)。"""
import json, re, sys, time, urllib.parse, urllib.request, collections, os
REPO = os.path.expanduser("~/Documents/GitHub/ai-juku-system")
API = "https://ai-juku-api-production.up.railway.app/api/exam-questions/bank"
html = open(os.path.join(REPO, "dojo-drill.html"), encoding="utf-8").read()
i = html.index("const UNIT_PRESETS = ["); j = html.index("];", i); blk = html[i:j]
cards = []
for m in re.finditer(r"\{([^{}]*)\}", blk):
    t = m.group(1)
    g = lambda k: (re.search(k + r":\s*'([^']*)'", t) or [None, None])[1]
    n = lambda k: (re.search(k + r":\s*(\d+)", t) or [None, None])[1]
    if g("name"): cards.append(dict(subj=g("subj"), name=g("name"), exam=g("exam"), part=g("part"), grade=g("grade"), filter=g("filter"), unitExact="unitExact: true" in t, agg=int(n("agg") or 0)))
pref = lambda u: re.split(r"[（(：:]", str(u or ""))[0].strip()
out = []
for c in cards:
    lim = min(50, c["agg"] * 8) if c["agg"] else 30
    params = {"exam": c["exam"], "part": c["part"], "eiken_grade": c["grade"], "limit": lim}
    if c["filter"]: params["topic"] = c["filter"]
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: d = json.loads(r.read().decode())
            break
        except Exception as e:
            if attempt == 2: raise
            time.sleep(3)
    rows = d.get("all") or ([d["selected"]] if d.get("selected") else [])
    subs = [(a, q) for a in rows for q in (a.get("questions") or [])]
    exact = [q for a, q in subs if c["filter"] and pref(q.get("unit")).startswith(c["filter"])]
    untagged = sum(1 for a, q in subs if not q.get("unit"))
    src = collections.Counter(str(a.get("source") or a.get("univ_simulated") or "?")[:28] for a in rows)
    rec = dict(c, lim=lim, rows=len(rows), subq=len(subs), exact=len(exact), untagged=untagged, src=dict(src))
    out.append(rec)
    flag = " ⚠️上限" if len(rows) >= lim else ""
    print(f"{c['subj']:5} {c['name']:<16} 行 {len(rows):2}/{lim} 小問 {len(subs):3} exact {len(exact):3} タグ無し {untagged:3}{flag}  {dict(src)}")
json.dump(out, open(os.path.expanduser("~/Desktop/kosei_baseline_" + time.strftime("%Y%m%d") + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n→ 保存: ~/Desktop/kosei_baseline_<日付>.json")
