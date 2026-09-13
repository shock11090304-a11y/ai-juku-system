# -*- coding: utf-8 -*-
"""sources/*.txt を、公開ページの校訂本文から取り直して照合する。

   ★これは通信するので、ふだんのゲート（run_all_gates.py）からは回らない。
     本文を差し替えたときと、ときどきの棚卸しのときに手で回す。
     ふだんの照合は check_source.py（保存してある sources/*.txt との突き合わせ）が担う。

     python3 refetch_sources.py          # 照合するだけ
     python3 refetch_sources.py --write   # 差があれば sources/*.txt を取り直して書き換える
"""
import html, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources")

# 保存してある本文の取得元。sources/*.txt の1行目の「# 取得元:」と同じものを書く。
PICKS = [
    ("set1.txt",        "https://yatanavi.org/text/kohon/kohon044"),
    ("set2.txt",        "https://yatanavi.org/text/yomeiuji/uji086"),
    ("set3.txt",        "https://yatanavi.org/text/chomonju/s_chomonju177"),
    ("set4.txt",        "https://yatanavi.org/text/mumyosho/u_mumyosho016"),
    ("set5.txt",        "https://yatanavi.org/text/mumyosho/u_mumyosho017"),
    ("set6.txt",        "https://yatanavi.org/text/hosshinju/h_hosshinju6-07"),
    ("shiryo_set1.txt", "https://yatanavi.org/text/yomeiuji/uji111"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (educational text retrieval)"})
    return urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")

def kotei_honbun(url):
    """ページの【校訂本文】の節だけを取り出す"""
    t = fetch(url)
    m = re.search(r"<!-- wikipage start -->(.*?)<!-- wikipage stop -->", t, re.S)
    body = m.group(1) if m else t
    parts = re.split(r"(<h[1-6][^>]*>.*?</h[1-6]>)", body, flags=re.S)
    def strip(s):
        s = re.sub(r"<br\s*/?>", "\n", s); s = re.sub(r"</p>", "\n", s)
        s = re.sub(r"<[^>]+>", "", s); s = html.unescape(s)
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t　]*\n[ \t　]*", "\n", s)).strip()
    cur, buf, out = "(先頭)", [], {}
    for p in parts:
        if re.match(r"<h[1-6]", p):
            if buf: out[cur] = strip("".join(buf))
            cur, buf = strip(p), []
        else: buf.append(p)
    if buf: out[cur] = strip("".join(buf))
    for h, v in out.items():
        if "校訂本文" in h:
            return "\n".join(l.strip() for l in v.split("\n")
                             if l.strip() and "PREV" not in l and "NEXT" not in l and "TOP" not in l)
    return None

def norm(s):
    s = re.sub(r"^#.*$", "", s, flags=re.M)     # 保存側の見出し行
    s = re.sub(r"\d+\)", "", s)                  # ページ側の脚注参照番号
    s = re.sub(r"[*/]", "", s)                   # wiki の強調記号
    return re.sub(r"[\s　]", "", s)

def main():
    write = "--write" in sys.argv
    bad = fatal = 0
    for name, url in PICKS:
        path = os.path.join(SRC, name)
        page = kotei_honbun(url)
        if page is None:
            # ★取得できなかったのは「原典を確かめられなかった」ということ。
            #   --write を付けていても失敗として扱う（正常と同じ終了コードにしない）。
            print(f"NG {name}: ページに校訂本文が見つからない {url}"); fatal += 1; continue
        mine = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if norm(mine) == norm(page):
            print(f"OK {name:16} {len(norm(page)):5}字 公開ページと一致")
            continue
        bad += 1
        print(f"NG {name}: 公開ページと一致しない（保存{len(norm(mine))}字／ページ{len(norm(page))}字）")
        a, b = norm(mine), norm(page)
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                print(f"   初差異 @{i}\n     保存…{a[max(0,i-24):i+24]}\n     ページ…{b[max(0,i-24):i+24]}"); break
        if write:
            head = mine.split("\n\n")[0] if mine else f"# 取得元: {url}"
            open(path, "w", encoding="utf-8").write(head + "\n\n" + page + "\n")
            print(f"   -> 取り直して書き換えた（★check_source.py と原稿の照合をやり直すこと）")
    print("\n" + ("保存してある原典は公開ページと一致" if not bad else f"要確認 {bad} 件"))
    return 1 if (fatal or (bad and not write)) else 0

if __name__ == "__main__":
    sys.exit(main())
