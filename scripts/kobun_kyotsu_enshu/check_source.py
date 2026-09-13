# -*- coding: utf-8 -*-
"""本文が原典どおりであることを、刷る側のデータと、保存してある校訂本文とで突き合わせる。

   ★この検査がこの問題集のいちばん下の土台である。
     設問も解説も、本文が原典どおりであることの上に成り立っている。
     sources/*.txt は「やたナビTEXT」が配布する校訂本文をそのまま保存したもので、
     編集してはならない（編集すればこの検査は無意味になる）。

   組版のための印（{{a}} 等）・注番号・段落の切れ目・冒頭の見出し行は照合から外す。
   それ以外の一字でも違えば落とす。改めた箇所がある回は、
   sources/emendations.json に「なぜ改めたか」を書いて明示的に登録する。
"""
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "sources")
bad = []
def ng(m): bad.append(m); print("NG " + m)

def norm(s):
    s = re.sub(r"\{\{/?[abcwxy]\}\}", "", s)        # 傍線・波線の印
    s = re.sub(r"[（(]注\d+[)）]", "", s)            # 注番号
    s = re.sub(r"^#.*$", "", s, flags=re.M)          # sources 側の見出し行
    s = re.sub(r"[\s　]", "", s)
    return s

def load_source(key):
    p = os.path.join(SRC, key + ".txt")
    if not os.path.exists(p): return None
    return norm(open(p, encoding="utf-8").read())

def emendations():
    p = os.path.join(SRC, "emendations.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def apply_emendations(src, rows, where):
    """登録した改訂を、保存してある校訂本文の側に当てて比較する。
       改訂が当たらなければ（＝原典の形が変わった／書き間違い）そこで落とす。"""
    for r in rows:
        a, b = norm(r["原典"]), norm(r["改めた形"])
        if a not in src:
            ng(f"{where}: 登録した改訂の元の形「{r['原典']}」が校訂本文に無い"); continue
        if src.count(a) != 1:
            ng(f"{where}: 改訂の元の形「{r['原典']}」が校訂本文に{src.count(a)}か所ある（一意でない）"); continue
        if not r.get("理由"):
            ng(f"{where}: 改訂「{r['原典']}」に理由が書かれていない")
        src = src.replace(a, b)
    return src

def main():
    em = emendations()
    cp = os.path.join(SRC, "cuts.json")
    cuts = json.load(open(cp, encoding="utf-8")) if os.path.exists(cp) else {}
    files = sorted(glob.glob(os.path.join(HERE, "sets", "set*.json")))
    if not files: ng("sets/set*.json が無い")
    for f in files:
        S = json.load(open(f, encoding="utf-8"))
        key = os.path.basename(f)[:-5]
        src = load_source(key)
        if src is None:
            ng(f"第{S['id']}回: sources/{key}.txt が無い（本文の典拠が保存されていない）"); continue
        src = apply_emendations(src, em.get(key, []), f"第{S['id']}回")
        got = norm(S["passage"])
        if got and got in src:
            i = src.index(got)
            before, after = src[:i], src[i + len(got):]
            decl = cuts.get(key, {})
            for name, part in (("前", before), ("後", after)):
                if not part: continue
                d = norm(decl.get(name, ""))
                if d != part:
                    ng(f"第{S['id']}回: 本文の{name}で{len(part)}字を落としているが、"
                       f"sources/cuts.json の申告と合わない …{part[:30] if name=='前' else part[-30:]}")
                elif not decl.get(f"{name}の理由"):
                    ng(f"第{S['id']}回: 本文の{name}を落とした理由が書かれていない")
            print(f"OK 第{S['id']}回 本文 {len(got)}字 が校訂本文と一致"
                  f"{'' if not (before or after) else f'（前{len(before)}字・後{len(after)}字は申告どおり切り出し）'}")
        else:
            for i in range(min(len(got), len(src))):
                if got[i] != src[i]:
                    ng(f"第{S['id']}回 本文が校訂本文と違う @{i}\n     こちら…{got[max(0,i-24):i+24]}\n     原典 …{src[max(0,i-24):i+24]}")
                    break
            else:
                ng(f"第{S['id']}回 本文が校訂本文の一続きになっていない（中略・抜き書きは認めない。こちら{len(got)}字／原典{len(src)}字）")
        # 資料（別本文）も同じように照合する
        for q in S["questions"]:
            if "【資料】" not in q["text"]: continue
            sk = f"shiryo_{key}"
            ssrc = load_source(sk)
            if ssrc is None:
                ng(f"第{S['id']}回 問{q['no']}: 【資料】の典拠 sources/{sk}.txt が無い"); continue
            ssrc = apply_emendations(ssrc, em.get(sk, []), f"第{S['id']}回の資料")
            # 資料は（中略）で飛ばすので、飛ばした各かたまりが原典に連続して在ることを見る
            m = re.search(r"^【資料】\s*$", q["text"], re.M)
            if not m: ng(f"第{S['id']}回 問{q['no']}: 【資料】が独立した行になっていない"); continue
            body = q["text"][m.end():]
            body = re.sub(r"（『[^』]*』[^）]*）\s*$", "", body.strip())   # 末尾の出典表示
            miss, at = 0, -1
            for part in re.split(r"（中略）", body):
                pn = norm(part)
                if len(pn) < 8: continue
                if pn not in ssrc:
                    miss += 1
                    for i in range(len(pn)):
                        if pn[:i+1] not in ssrc:
                            ng(f"第{S['id']}回 問{q['no']} 【資料】が原典と違う …{pn[max(0,i-24):i+8]}"); break
                    continue
                # ★原典に在るだけでなく、原典と同じ順に並んでいることも見る（入れかえ・重複を止める）
                j = ssrc.index(pn)
                if j <= at:
                    miss += 1
                    ng(f"第{S['id']}回 問{q['no']} 【資料】の順序が原典と違う …{pn[:24]}")
                at = j
            if not miss: print(f"OK 第{S['id']}回 問{q['no']} 【資料】が原典と一致")

    print("\n" + ("本文は原典どおり" if not bad else f"要修正 {len(bad)} 件"))
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
