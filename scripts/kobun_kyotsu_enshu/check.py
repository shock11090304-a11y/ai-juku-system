# -*- coding: utf-8 -*-
"""第4問（古文）演習問題集の決定的検査
   解答番号・配点・選択肢・傍線記号・注・現代語訳の対応・レベルの階段・正解の分布。
   引数で刷ったPDFを渡すと、データの全要素がPDFに出ているかも照合する。

     python3 check.py                       # データだけ検査（CIはこれ）
     python3 check.py <問題編.pdf> <解答解説編.pdf>
"""
import json, re, sys, os, glob, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build import LEVELS, body_chars, rules_on_page, page_chars   # レベル・字数・罫の判定はビルダーが正典
sys.path.insert(0, os.path.join(HERE, "src"))
from make_sets import COLLECTIVE          # 「いずれも」等の判定は make_sets が正典

CIRC = "①②③④⑤"
bad = []
def ng(m): bad.append(m); print("NG " + m)

def plain(s): return re.sub(r"\{\{/?[abcwxy]\}\}", "", s)

def deruby(s):
    """本文から、組版用の印（注番号）と校訂本文の読み仮名を落とす。
       設問は引用するときこの2つを書かないので、比べるときは両方から外す。"""
    return re.sub(r"\([ぁ-んァ-ヶー]+\)", "", re.sub(r"[（(]注\d+[)）]", "", s))

def pdf_text(path):
    """PDFの全文を、フッター行と傍線記号を除いて連結する（ページ跨ぎの文を照合できるように）"""
    import fitz
    d = fitz.open(path)
    out = []
    for pg in d:
        t = pg.get_text()
        t = re.sub(r"TRILLION\s*AI\s*学習塾[\s\S]*$", "", t)   # フッターは縦組みでも末尾にまとめて出る
        t = re.sub(r"\n\s*\d+\s*/\s*\d+\s*\n?", "\n", t)
        out.append(t)
    t = "".join(out)
    return re.sub(r"[0-9]", "", re.sub(r"\s", "", t))

# ★「これも」だけを数えるのは壊れ方の側から数えること。実際に「これも本文にない」を
#   「そのような記述も本文にない」に書き換えただけで素通りした。受け先を指す語の側も見る。
ANAPHORA = re.compile(r"^(?:も|[はが]?\s*、?\s*(?:これも|それも|同じく|同様に|こちらも))"
                      r"|[、。](?:これも|それも|同じく|同様に|こちらも|同じ一文|同じ理由)"
                      r"|[、。]\s*(?:そのような|その点|そこ)[^、。]{0,8}も"
                      r"|と同様|[、。][^、。]{0,6}も同じ(?:[。で]|誤り|理由|こと)"
                      r"|前者|後者")

def anaphora_in_kill(exp_line):
    """潰し文が前の文を受けている箇所を返す（「も」「これも」「同じく」…）。
       ★潰し文は sort_kills が番号順に並べ替えるので、**受け先が後ろへ回る**。
         「③ も妻を失ったことにしており、同じく結末と合わない。」が
         「思ひがけぬ」の話の直後に刷られ、受け先が無くなった（実際に起きた）。
       まとめて潰す形（「いずれも」等）は1文で閉じているので対象外。"""
    m = re.search(r"(?<![にの])よって\s*[①-⑤\s]+。(.*)$", exp_line)
    if not m: return []
    out = []
    for t in re.split(r"(?<=。)", m.group(1)):
        h = re.match(r"^\s*[①-⑤\s]*", t)
        rest = t[h.end():]
        if COLLECTIVE.match(rest): continue
        if ANAPHORA.search(rest): out.append(t.strip()[:34])
    return out

def kill_order(exp_line):
    """解説の「よって ④。」より後ろを、潰していくかたまりに割って番号を返す。
       戻り値は [[1], [2, 5], [4]] のような、1文ごとの番号の並び。
       ★文頭の1字だけを見てはいけない。「④ は…取り、⑤ は主語を…」のように1文で2つ潰すと、
         後ろの番号が見えず、順が飛んでいても「昇順」と報告してしまう（13行がこれで素通りしていた）。
       ★逆に、全部を1列に並べて昇順を求めるのも行きすぎ。「② ⑤ はいずれも…」と離れた番号を
         まとめて潰す文があると、そのあとに ④ が来るのは避けようがない。
         求めるのは「かたまりの先頭が昇順」かつ「かたまりの中も昇順」。"""
    m = re.search(r"(?<![にの])よって\s*[①-⑤\s]+。(.*)$", exp_line)
    if not m: return []
    out = []
    for t in re.split(r"(?<=。)", m.group(1)):
        ns = [CIRC.index(c) for c in t if c in CIRC]
        if not ns: continue
        if t.lstrip()[0] in CIRC or not out: out.append(ns)
        else: out[-1] += ns          # 丸数字で始まらない文は直前のかたまりの続き
    return out

def kill_order_ng(blocks):
    """潰す順の乱れを言葉にして返す（無ければ空文字）。
       ★生徒は自分が選んだ番号を頭から探す。だから見るのは「読む順に並べたとき昇順か」。
         かたまりの先頭と中だけを見ていたとき、「②③⑤ のあとに ④」のような
         飛び番号のかたまりが4件そのまま出荷されかけた。"""
    for b in blocks:
        if b != sorted(b): return f"かたまりの中が昇順でない {[x + 1 for x in b]}"
    heads = [b[0] for b in blocks]
    if heads != sorted(heads): return f"かたまりの先頭が昇順でない {[x + 1 for x in heads]}"
    flat = [n for b in blocks for n in b]
    if flat != sorted(flat): return f"読む順に並べると昇順でない {[x + 1 for x in flat]}"
    return ""

def nested_quotes(s):
    """「」の入れ子を返す。★入れ子にすると読み手が引用の切れ目を見失う。
       設問が本文を引用するとき、引用の中にさらに会話が入ることがある（第2回 問3 で実際に起きた）。
       内側は『』にする。本文そのもの（原典）は直さない。"""
    out, depth = [], 0
    for i, ch in enumerate(s):
        if ch == "「":
            depth += 1
            if depth >= 2: out.append(s[max(0, i - 10):i + 14])
        elif ch == "」":
            depth = max(0, depth - 1)
    return out

def page_body_lines(txt):
    """ページの中身の行（フッターとノンブルを除く）"""
    return [l for l in txt.split("\n")
            if l.strip() and "TRILLION" not in l and not re.fullmatch(r"\s*\d+\s*/\s*\d+\s*", l)]

def thin_page(body):
    """★空白ではないが数行しか無い紙も刷ってはいけない。
       典拠の1行だけが次ページへこぼれて、2行しか無いページが1枚できたことがある
       （解答解説編の最終ページ）。空白ページの検査は「0行」しか見ないので素通りしていた。"""
    return 0 < len(body) < 4

def check_glyphs(path, label):
    """刷り上がりに、出てはいけない文字が出ていないか（豆腐・制御文字・タグやMarkdownの露出）"""
    import fitz
    d = fitz.open(path)
    t = "".join(p.get_text() for p in d)
    ctrl = "".join(chr(c) for c in list(range(0, 9)) + [11, 12] + list(range(14, 32)))
    if t.count("\ufffd"): ng(f"{label}: 字形の出ない文字（豆腐）が {t.count(chr(0xfffd))} 個")
    ctrls = sorted({hex(ord(c)) for c in t if c in ctrl})
    if ctrls: ng(f"{label}: 制御文字が出ている {ctrls}")
    tags = re.findall(r"<[a-zA-Z/][^>]{0,20}>", t)
    if tags: ng(f"{label}: HTMLのタグがそのまま出ている {tags[:3]}")
    if "**" in t: ng(f"{label}: Markdownの強調記号がそのまま出ている")
    # ★組版のときに使う「印」が刷り上がりに漏れていないか（注番号の退避に私用領域を使っている）
    pua = sorted({hex(ord(c)) for c in t if "\ue000" <= c <= "\uf8ff"})
    if pua: ng(f"{label}: 私用領域の文字が出ている {pua[:4]}（組版用の印が刷り上がりに漏れた）")
    for i, p in enumerate(d):
        if not [b for b in p.get_text("blocks") if b[4].strip()]:
            ng(f"{label}: {i+1}ページが空白")
        # ★「空白ではないが、数行しか無い紙」も刷ってはいけない。
        #   典拠の1行だけが次ページへこぼれて、2行しか無いページが1枚できたことがある（解答解説編の最終ページ）。
        body = page_body_lines(p.get_text())
        if thin_page(body):
            ng(f"{label}: {i+1}ページが{len(body)}行しか無い（前のページから離さないこと）→ {body[0][:30]}")
    print(f"   {label}: {len(d)}ページ／{len(t)}字（豆腐・制御文字・タグ露出なし）")

def check_layout(path, label, skip_pages=2):
    """版面の欠陥。★「肢が1つだけ次ページに残る」「傍線の罫だけが余白に取り残される」は
       文字を照合するだけの検査では絶対に見えない（どちらも実際に起きた）。"""
    import fitz
    d = fitz.open(path)
    for i, p in enumerate(d, 1):
        if i <= skip_pages: continue          # 巻頭は手順の①〜⑥なので選択肢ではない
        lines = [l.strip() for l in p.get_text().split("\n") if l.strip()]
        c1 = sum(1 for l in lines if l.startswith("①"))
        c5 = sum(1 for l in lines if l.startswith("⑤"))
        if c1 != c5:
            ng(f"{label} {i}ページ: 選択肢のかたまりがページをまたいでいる（①が{c1}個・⑤が{c5}個）")
        # 傍線（縦組みなので縦の線）は、必ずそのすぐ隣に本文がある。
        # 本文の無い所に残った線＝改ページで装飾だけ取り残された罫（実際に起きた）。
        # ★罫の拾い方は rules_on_page に一本化する。長さのしきい値で「表の枠かどうか」を
        #   当てる書き方は、傍線の箱が吐く上下辺（16.5pt）と本物の枠（22.5pt）の差が
        #   4pt も無く、1字幅の囲み（約15pt）を傍線と取り違える。
        #   rules_on_page は「同じ x に隙間なく3つ以上積み上がり、太さぶんの対になっている」で絞るので、
        #   しきい値の当てずっぽうが要らない。
        segs = rules_on_page(p)
        words = p.get_text("words")
        stray = []
        for x, y0, y1 in segs:
            near = [w for w in words if abs((w[0] + w[2]) / 2 - x) < 12 and w[3] > y0 and w[1] < y1]
            if not near: stray.append(round(x, 1))
        if stray:
            ng(f"{label} {i}ページ: 本文の無い所に縦線が{len(stray)}本（傍線だけが取り残されている）x={stray[:4]}")
    print(f"   {label}: 版面の欠陥なし（選択肢の分断・取り残された罫）")

def style_violations(txt, marks, n_sets, ids):
    """縦組みの体裁の違反を並べて返す（純関数。PDFに触らないので自己テストができる）。
         txt   … 問題編の本文。フッターを除き、空白を落としたもの。
         marks … 傍線の記号として刷られた span の [(文字列, 縦の高さpt), ...]
       ★ここは「読めるかどうか」ではなく「第1版と同じ流儀か」を見る。
         文字を突き合わせるだけの検査では絶対に出てこない
         （どちらの流儀でも同じ文字列が出るので、照合はどちらでも通ってしまう）。
       ① 縦組みの見出しと配点は漢数字（第四問・配点四五点・得点／四五）。
          解答番号・分・字数・設問番号・注番号は算用数字のまま（第1版と本番の冊子の使い分け）。
       ② 傍線の記号は半角かっこ (ア) を縦中横にして、本文1字ぶんの1マスに収める。
          全角の（ア）を素の3字で置くと縦に3マス使い、列がそこだけ押し下げられる。"""
    v = []
    for sid in ids:
        if f"第四問（古文）演習問題第{sid}回" not in txt:
            v.append(f"第{sid}回の見出しが「第四問（古文）　演習問題　第{sid}回」でない")
    for word, why in (("配点四五点", "配点は漢数字"), ("得点／四五", "得点欄の満点は漢数字")):
        if txt.count(word) != n_sets:
            v.append(f"「{word}」が{txt.count(word)}回（{n_sets}回あるべき／{why}）")
    if "第4問" in txt:
        v.append("縦組みの本体に算用数字の「第4問」が出ている（見出しは第四問）")
    for lab in ("ア", "イ", "ウ", "Ａ", "Ｂ"):
        if f"（{lab}）" in txt:
            v.append(f"傍線の記号が全角の（{lab}）になっている（半角かっこ＋縦中横で1マスに収める）")
    found = collections.Counter()
    for t, h in marks:
        found[t] += 1
        if h > 14:
            v.append(f"傍線の記号 {t} が縦に{h:.1f}pt（1マス＝約11ptに収めること）")
    if len(found) != 5 or any(c != n_sets for c in found.values()):
        v.append(f"傍線の記号の数が合わない {dict(found)}（5種×{n_sets}回）")
    return v

def selftest_style():
    """★判定表そのものの自己テスト。
       この検査は刷ったPDFを渡したときしか動かないので、CI（--no-pdf 相当）では一度も実行されない。
       壊れていても誰も気づかないまま「体裁は見ている」と言い続けることになるので、
       素の入力と、わざと崩した入力の両方を、毎回ここで通す。"""
    ids = [1, 2]
    ok_txt = ("第四問（古文）演習問題第1回配点四五点得点／四五(ア)(イ)(ウ)(Ａ)(Ｂ)"
              "第四問（古文）演習問題第2回配点四五点得点／四五(ア)(イ)(ウ)(Ａ)(Ｂ)")
    ok_marks = [(m, 10.8) for m in ("(ア)", "(イ)", "(ウ)", "(Ａ)", "(Ｂ)")] * 2
    if style_violations(ok_txt, ok_marks, 2, ids):
        ng("check_style の自己テスト: 正しい体裁に文句を言っている "
           + str(style_violations(ok_txt, ok_marks, 2, ids)))
    cases = [
        ("見出しが算用数字", ok_txt.replace("第四問（古文）演習問題第1回", "第4問（古文）第1回"),
         ok_marks, "見出しが"),
        ("配点が算用数字", ok_txt.replace("配点四五点", "配点45点", 1), ok_marks, "配点四五点"),
        ("得点欄が算用数字", ok_txt.replace("得点／四五", "得点／45", 1), ok_marks, "得点／四五"),
        ("記号が全角", ok_txt.replace("(ア)", "（ア）", 1), ok_marks, "全角の（ア）"),
        ("記号が縦に3マス", ok_txt, [("(ア)", 32.4)] + ok_marks[1:], "縦に"),
        ("記号が1つ足りない", ok_txt, ok_marks[:-1], "記号の数が合わない"),
    ]
    for name, txt, marks, want in cases:
        got = style_violations(txt, marks, 2, ids)
        if not any(want in g for g in got):
            ng(f"check_style の自己テスト: 「{name}」を崩しても拾わない（出た違反: {got}）")
    # ほぼ白紙のページの判定表も、ここで一緒に試す
    foot = "TRILLION AI 学習塾　共通テスト形式 国語 第4問（古文）"
    thin = "\n".join(["本文の典拠：発心集", "校訂の記録は講師用メモに載せた。", foot, "37 / 37"])
    full = "\n".join(["あ", "い", "う", "え", "お", foot, "37 / 37"])
    if not thin_page(page_body_lines(thin)):
        ng("check_glyphs の自己テスト: 2行しか無いページを見逃す")
    if thin_page(page_body_lines(full)):
        ng("check_glyphs の自己テスト: 5行あるページに文句を言っている")
    if page_body_lines(full) != ["あ", "い", "う", "え", "お"]:
        ng(f"check_glyphs の自己テスト: フッターとノンブルを落とせていない {page_body_lines(full)}")
    if not nested_quotes("傍線部(Ａ)「そばの人は、「謀るなり」と笑ひける」とあるが"):
        ng("nested_quotes の自己テスト: かぎかっこの入れ子を見逃す")
    if nested_quotes("傍線部(Ａ)「そばの人は、『謀るなり』と笑ひける」とあるが、「なぜか」"):
        ng("nested_quotes の自己テスト: 入れ子でない引用に文句を言っている")
    if kill_order("本文の説明。よって ③。① は甲。② ⑤ はいずれも乙。④ は丙。") != [[0], [1, 4], [3]]:
        ng("kill_order の自己テスト: かたまりに割れていない")
    if kill_order_ng([[0], [1, 3], [4]]):
        ng("kill_order の自己テスト: 正しい並びに文句を言っている")
    if not kill_order_ng([[0], [1, 4], [3]]):
        ng("kill_order の自己テスト: 飛び番号のかたまりを拾えていない")
    if not kill_order_ng([[1], [0]]):
        ng("kill_order の自己テスト: かたまりの先頭の狂いを拾えていない")
    if not kill_order_ng([[4, 2]]):
        ng("kill_order の自己テスト: かたまりの中の狂いを拾えていない")
    # 墨の有無の判定表。★これは刷ったPDFを渡したときしか動かないので、ここで毎回試す。
    import fitz
    black = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, 80, 80), False)
    black.clear_with(0)
    white = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, 80, 80), False)
    white.clear_with(255)
    if not ink(black, 8, 1.0, 1.0, 8.0): ng("ink の自己テスト: 真っ黒な罫を「墨なし」と言う")
    if ink(white, 8, 1.0, 1.0, 8.0): ng("ink の自己テスト: 真っ白な所を「墨あり」と言う")
    # 罫1本の判定表
    if not note_split([120.0, 140.7]): ng("note_split の自己テスト: 列をまたいだ注番号を見逃す")
    if note_split([120.0, 122.1, 120.0]): ng("note_split の自己テスト: 同じ列の注番号に文句を言っている")
    for want, args in (("right", (240.0, 22, 0)), ("left", (240.0, 0, 22)),
                       ("lonely", (240.0, 1, 0)), ("stray", (240.0, 0, 0)),
                       ("right", (10.5, 1, 0))):
        if rule_verdict(*args) != want:
            ng(f"rule_verdict の自己テスト: {args} を {rule_verdict(*args)} と言う（{want} のはず）")
    # 1文で2つ潰す形（文頭以外の丸数字）も拾えること
    if kill_order("よって ①。④ は甲で、② は乙。") != [[3, 1]]:
        ng("kill_order の自己テスト: 文中の丸数字を拾えていない")
    if kill_order("よってと書いていない解説。① は甲。"):
        ng("kill_order の自己テスト: 「よって」の無い文まで拾っている")
    if not anaphora_in_kill("よって ①。② は甲。③ も乙であり、同じく合わない。"):
        ng("anaphora_in_kill の自己テスト: 前の文を受けている潰し文を拾えていない")
    if anaphora_in_kill("よって ①。② は甲。③ ④ はいずれも乙。"):
        ng("anaphora_in_kill の自己テスト: まとめ潰しに文句を言っている")
    if anaphora_in_kill("よって ①。② は甲である。③ は乙である。"):
        ng("anaphora_in_kill の自己テスト: ふつうの潰し文に文句を言っている")

def note_split(xs):
    """注番号「(注N)」の4〜5字が、同じ列に収まっているか。
       ★同じ列なら x はほぼ同じ（縦中横の数字だけ数pt ずれる）。1列ぶん離れたら割れている。
         テキストを連結して照合する検査では「(注」と「5)」が別の列に分かれていても
         同じ文字列に見えるので、絶対に出てこない（実際に p27 で1件割れていた）。"""
    return bool(xs) and max(xs) - min(xs) > 6

def rule_verdict(length, n_right, n_left):
    """罫1本の判定。right＝正しく字の右／left＝字の左／lonely＝長さのわりに字が足りない／stray＝字が無い。
       ★「隣に1字あれば合格」にしてはいけない。240ptの罫が1字で免責される
         （第6回 傍線部(Ｂ) の23字ぶんが刷られていなかったのを、そのせいで見逃した）。"""
    need = max(1, int(length / 10.4) - 1)
    if n_right >= need: return "right"
    if n_left >= need: return "left"
    if n_right or n_left: return "lonely"
    return "stray"

def ink(pix, Z, x, y0, y1, floor=0.30):
    """罫の芯に本当に墨が乗っているか（紙に出ているか）を画素で確かめる。
       ★get_drawings はクリップされたパスも返すので、描画リストを数えるだけでは
         「紙に出ていない罫」を1本も捕まえられない。窓を罫の芯をまたぐように取ると、
         実測で正常な罫は98本すべて 0.429、消えた罫は 0。floor=0.30 なら
         「半分だけクリップされた罫」も捕まる（0.10 だと 0.14pt の毛でも通る）。"""
    W, H, buf, n = pix.width, pix.height, pix.samples, pix.n
    area = dark = 0
    for yy in range(max(0, int(y0 * Z)), min(H, int(y1 * Z))):
        row = yy * W
        # ★窓は罫の芯をまたぐように取る。rules_on_page は罫の左辺と右辺の2本を返すので、
        #   片側だけの窓だと右辺から測ったとき墨が 0.12 しか出ず、しきい値 0.10 との差が 0.02 になる。
        for xx in range(max(0, int((x - 0.9) * Z)), min(W, int((x + 0.85) * Z))):
            area += 1
            if buf[(row + xx) * n] < 200: dark += 1
    return bool(area) and dark / area >= floor

def check_underlines(path, sets, label="問題編"):
    """傍線が本当に引かれているか、引かれている側とアキが第1版どおりかを測る。
       ★文字を突き合わせる検査は、傍線が1本も刷られていなくても緑になる
         （記号 (ア) は文字なので出る）。罫は罫として測らないと見えない。
       ★第1版は文字の右に 4.56pt 離して引いている。box-shadow: inset だと
         文字ボックスの左内側に出て字に食い込み、隣の列の波線と 0.4pt まで近づいた。"""
    import fitz, statistics
    d = fitz.open(path)
    right = left = 0
    gaps, pages, stray, faint, lonely = [], 0, [], [], []
    Z = 8
    for page in d:
        # ★描画命令を数えるだけでは「紙に出ていない罫」を1本も捕まえられない。
        #   Chrome はクリップされたパスもそのまま書き出すので、命令はあるのに墨が無い
        #   （overflow: clip を入れたとき、第2回の傍線が 0.08pt の毛になっていたのを緑で見逃した）。
        pix = page.get_pixmap(matrix=fitz.Matrix(Z, Z), colorspace=fitz.csGRAY)
        chars = [c["bbox"] for bl in page.get_text("rawdict")["blocks"] for ln in bl.get("lines", [])
                 for sp in ln["spans"] for c in sp["chars"] if c["c"].strip()]
        n = 0
        for x, y0, y1 in rules_on_page(page):
            same = [c for c in chars if c[1] < y1 - 1 and c[3] > y0 + 1]
            r = [c for c in same if 2.5 <= x - c[2] <= 8.0]
            l = [c for c in same if -2.0 <= x - c[0] <= 3.0]
            # ★「隣に1字あれば合格」にしてはいけない。240ptの罫が1字で免責される
            #   （第6回 傍線部(Ｂ) の23字ぶんが刷られていなかったのを、そのせいで見逃した）。
            v = rule_verdict(y1 - y0, len(r), len(l))
            if v == "right": right += 1; gaps.append(min(x - c[2] for c in r)); n += 1
            elif v == "left": left += 1; n += 1
            elif v == "lonely": lonely.append((page.number + 1, round(x, 1), round(y1 - y0), len(r or l)))
            else: stray.append((page.number + 1, round(x, 1), round(y1 - y0)))
            if not ink(pix, Z, x, y0, y1): faint.append((page.number + 1, round(x, 1), round(y1 - y0)))
        pages += 1 if n else 0
    if right + left == 0:
        ng(f"{label}: 傍線の罫が1本も刷られていない"); return
    if left:
        ng(f"{label}: 傍線が文字の左に出ている帯が{left}本（右のアキに引くこと・右は{right}本）")
    med = statistics.median(gaps) if gaps else 0
    # ★第1版は 4.47pt だが、版面の右端に接する1列目の罫が紙に出る上限（padding 3.8pt）で
    #   決まるので、いまは中央値 3.41pt。域は実測に合わせて置く。
    if not 2.5 <= med <= 5.0:
        ng(f"{label}: 傍線と文字のアキが中央値{med:.2f}pt（想定 2.5〜5.0pt・第1版は4.47pt）")
    # ★改ページで、文字を伴わない罫だけが前のページの余白に残ることがある
    #   （第6回の傍線部(Ｂ)が p33→p34 にまたがったとき、p33 の左余白に高さ239ptの罫が1本残った）。
    #   check_layout の「近くに文字が無い縦線」は窓が16ptと広く、隣の列の文字を拾って見逃していた。
    if stray:
        ng(f"{label}: 文字を伴わない傍線の罫が{len(stray)}本（改ページで取り残された）{stray[:4]}")
    if lonely:
        ng(f"{label}: 罫の長さに対して隣の字が足りない箇所が{len(lonely)}本"
           f"（改ページで途中から刷られていない）{lonely[:4]}")
    if faint:
        ng(f"{label}: 描画の命令はあるのに紙に墨が乗っていない罫が{len(faint)}本"
           f"（クリップで消えている）{faint[:4]}")
    # ★「罫のあるページ数」では、ある回の傍線が1本も刷られなくても他の回が2ページに散れば通る。
    if right + left < 5 * len(sets):
        ng(f"{label}: 傍線の罫が{right + left}本（5種×{len(sets)}回＝{5 * len(sets)}本に足りない）")
    if pages < len(sets):
        ng(f"{label}: 傍線のあるページが{pages}ページしかない（{len(sets)}回ぶんに足りない）")
    print(f"   {label}: 傍線の罫 {right + left}本（右 {right}・左 {left}・宙に浮き {len(stray)}）アキ中央値 {med:.2f}pt")

def check_style(path, sets, label="問題編"):
    """刷り上がりから文字と記号を取り出して style_violations にかける"""
    import fitz
    d = fitz.open(path)
    # フッター（横組み）は「第4問」でよい。第1版のフッターも算用数字。縦組みの本体だけを見る。
    txt = re.sub(r"\s", "", "".join(
        re.sub(r"TRILLION\s*AI\s*学習塾[\s\S]*$", "", pg.get_text()) for pg in d))
    marks = []
    for page in d:
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for sp in ln["spans"]:
                    t = sp["text"].strip()
                    if re.fullmatch(r"\((?:ア|イ|ウ|Ａ|Ｂ)\)", t):
                        marks.append((t, sp["bbox"][3] - sp["bbox"][1]))
    # ★注番号が列をまたいで割れていないか。テキストを連結して照合する検査では
    #   「(注」と「5)」が別の列に分かれていても同じ文字列に見えるので、絶対に出てこない。
    for page in d:
        chars = [(c["c"], c["bbox"]) for b in page.get_text("rawdict")["blocks"]
                 for l in b.get("lines", []) for sp in l["spans"] for c in sp["chars"]]
        for i in range(len(chars) - 3):
            if chars[i][0] != "(" or chars[i + 1][0] != "注": continue
            j = i + 2
            while j < len(chars) and chars[j][0].isdigit(): j += 1
            if j >= len(chars) or chars[j][0] != ")": continue
            xs = [chars[k][1][0] for k in range(i, j + 1)]
            if note_split(xs):
                ng(f"{label}: {page.number + 1}ページの注番号が列をまたいで割れている"
                   f"（{''.join(c for c, _ in chars[i:j + 1])}・x の差 {max(xs) - min(xs):.1f}pt）")
    for m in style_violations(txt, marks, len(sets), [S["id"] for S in sets]):
        ng(f"{label}: {m}")
    print(f"   {label}: 体裁は第1版どおり（第四問・配点四五点・傍線の記号は1マスの縦中横）")

def check_stamp(sets, paths):
    """渡されたPDFが、いま刷るデータから作られたものかを確かめる。
       ★これが無いと、古いPDFを渡しても「データの全要素がPDFにある」だけは満たされて緑になる。"""
    import fitz
    from build import stamp
    want = stamp(sets)
    for path in paths:
        got = (fitz.open(path).metadata or {}).get("keywords", "")
        if got != "kobun-sets:" + want:
            ng(f"{os.path.basename(path)}: いまのデータから刷ったPDFではない"
               f"（PDFの指紋 {got or '（無し）'} ≠ {'kobun-sets:' + want}）。build.py を回し直すこと")

def check_pdf(sets, qpdf, apdf):
    """データの全要素が、刷り上がりに出ているかを逆向きに照合する"""
    qt, at = pdf_text(qpdf), pdf_text(apdf)
    base = lambda x: re.sub(r"[0-9]", "", re.sub(r"\s", "", x))
    st = base                                                    # 設問文・選択肢・解説はそのまま
    MARK = r"[（(](?:ア|イ|ウ|Ａ|Ｂ|A|B)[)）]"                       # 本文は組版時に記号が入るので除く
    stp = lambda x: re.sub(MARK, "", base(x))
    qtp = re.sub(MARK, "", qt)
    for S in sets:
        sid = S["id"]
        for ln in plain(S["passage"]).split("\n"):
            if stp(ln) and stp(ln) not in qtp: ng(f"第{sid}回 本文がPDFにない: {ln[:34]}")
        for q in S["questions"]:
            for ln in q["text"].split("\n"):      # 設問文は改行のたびに段落が分かれて組まれる
                if st(ln) and st(ln) not in qt: ng(f"第{sid}回 問{q['no']} 設問文がPDFにない: {ln[:34]}")
            for it in q["items"]:
                for c in it["choices"]:
                    if not st(c): ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢が空")
                    elif st(c) not in qt: ng(f"第{sid}回 問{q['no']}{it['label']} 選択肢がPDFにない: {c[:26]}")
            if st(q["exp"]) not in at: ng(f"第{sid}回 問{q['no']} 解説が解答編にない")
            # ★刷り上がりの「正解 ⑤」行が、データの answer（0始まり）と合っているか。
            #   0始まり/1始まりの取り違えはこのリポジトリで何度も起きている。
            want = "正解" + "".join((it["label"] or "") + CIRC[it["answer"]] for it in q["items"])
            if base(want) not in at:
                ng(f"第{sid}回 問{q['no']}: 解答編の「正解」行が合わない（期待 {want}）")
        for n in S["notes"]:
            if st(n["gloss"]) not in qt: ng(f"第{sid}回 注「{n['word']}」がPDFにない")
        for ln in S["translation"].split("\n"):
            if st(ln) and st(ln) not in at: ng(f"第{sid}回 現代語訳が解答編にない: {ln[:28]}")
        for g in S["grammar"]:
            if st(g["point"]) not in at: ng(f"第{sid}回 文法「{g['phrase'][:12]}」が解答編にない")
        for r in S["rules_used"]:
            if st(r["where"]) not in at: ng(f"第{sid}回 ルール「{r['rule'][:12]}」が解答編にない")

def check_fresh(sets):
    """原稿 src/setN.py から make_sets.py と同じ変換をその場でやり直し、sets/setN.json と丸ごと比べる。
       ★sets/*.json は生成物だが git に入っている。原稿を直して make_sets.py を回し忘れると、
         直したつもりの冊子がそのまま刷れる。どのゲートも sets/*.json しか読んでいなかった。
       ★項目を1つずつ数え上げる書き方にしてはいけない。足し忘れた列が永久に見えない
         （最初にそう書いたとき、解説・配点・解答番号・小問の見出し・文法・注の説明文・
           小問の末尾追加が全部素通りしていた）。並べ替えは md5 と positions.py で決まるので
         作り直せば1バイトまで再現する。positions.py や make_sets.py 自身を直して
         回し忘れた場合も、この形なら捕まる。"""
    # ★この Mac の python3 は sys.pycache_prefix を共有の場所に向けるので、
    #   パッケージ内に __pycache__ が見えなくても古い .pyc が残り、
    #   「原稿を直したのに古い原稿を検査して緑」になる。毎回まっさらな置き場を使う。
    import tempfile, atexit, shutil
    _pyc = tempfile.mkdtemp(prefix="kobun-check-pyc-")
    sys.pycache_prefix = _pyc
    atexit.register(lambda: shutil.rmtree(_pyc, ignore_errors=True))
    sys.path.insert(0, HERE)
    sys.path.insert(0, os.path.join(HERE, "src"))
    import make_sets
    for S in sets:
        src = os.path.join(HERE, "src", f"set{S['id']}.py")
        if not os.path.exists(src):
            ng(f"第{S['id']}回: 原稿 src/set{S['id']}.py が無い"); continue
        try:
            want = make_sets.build_set_multi(make_sets.load(src))
        except Exception as e:
            ng(f"第{S['id']}回: 原稿から作り直せない（{type(e).__name__}: {e}）"); continue
        # ★dict の == は 18 と 18.0 を同じとみなす。文字列にしてから比べる。
        want = json.loads(json.dumps(want, ensure_ascii=False))   # タプル→リストをそろえる
        if json.dumps(want, sort_keys=True, ensure_ascii=False) != \
           json.dumps(S, sort_keys=True, ensure_ascii=False):
            diff = [k for k in set(want) | set(S) if want.get(k) != S.get(k)]
            ng(f"第{S['id']}回: 原稿から作り直した結果と刷るデータが違う"
               f"（make_sets.py を回し忘れ）→ {sorted(diff)}")

def main():
    files = sorted(glob.glob(os.path.join(HERE, "sets", "set*.json")))
    if not files: ng("sets/set*.json が無い")
    # ★原稿・刷るデータ・正解位置表の3つで回がそろっているか。
    #   1つでも欠けると、5回分の冊子がそのまま刷られる（4ゲートとも緑だった）。
    sys.path.insert(0, os.path.join(HERE, "src"))
    import positions
    have = {int(re.search(r"\d+", os.path.basename(f)).group(0)) for f in files}
    drafts = {int(re.search(r"\d+", os.path.basename(f)).group(0))
              for f in glob.glob(os.path.join(HERE, "src", "set*.py"))}
    if have != drafts or have != set(positions.POS):
        ng(f"回が足りない／余っている: 刷るデータ{sorted(have)} 原稿{sorted(drafts)} 正解位置表{sorted(positions.POS)}")
    sets = sorted([json.load(open(f, encoding="utf-8")) for f in files], key=lambda x: x["id"])
    selftest_style()          # ★体裁の判定表は、PDFを渡さない回でも毎回ここで試す
    check_fresh(sets)         # ★原稿と刷るデータの食い違い（make_sets.py の回し忘れ）
    dist = collections.Counter()
    ladder = []
    refs = []
    for S in sets:
        sid = S["id"]
        if S["level_no"] not in LEVELS:
            ng(f"第{sid}回: level_no が {S['level_no']}（1〜3であるべき）"); continue
        # 1) 設問数・解答番号・配点
        if len(S["questions"]) != 5: ng(f"第{sid}回: 設問が{len(S['questions'])}問")
        nums, total = [], 0
        for q in S["questions"]:
            ns = [x.strip() for x in re.split(r"[・,、]", q["nums"]) if x.strip()]
            nums += ns
            if len(ns) != len(q["items"]):
                ng(f"第{sid}回 問{q['no']}: 解答番号{len(ns)}個 ≠ 小問{len(q['items'])}個")
            m = re.search(r"(\d+)", q["points"])
            if not m: ng(f"第{sid}回 問{q['no']}: 配点が読めない「{q['points']}」")
            else: total += int(m.group(1)) * len(q["items"])
            for it in q["items"]:
                if len(it["choices"]) != 5: ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢が{len(it['choices'])}個")
                if len(set(it["choices"])) != len(it["choices"]): ng(f"第{sid}回 問{q['no']}{it['label']}: 選択肢に重複")
                if not 0 <= it["answer"] < len(it["choices"]): ng(f"第{sid}回 問{q['no']}{it['label']}: 正解番号が範囲外")
                else: dist[CIRC[it["answer"]]] += 1
                if "pos" in it: ng(f"第{sid}回 問{q['no']}{it['label']}: pos が残っている（make_sets を通していない）")
            for tgt, what in ([(q["text"], "設問文"), (q.get("exp", ""), "解説")]
                              + [(c, "選択肢") for it in q["items"] for c in it["choices"]]):
                for n in nested_quotes(tgt):
                    ng(f"第{sid}回 問{q['no']} {what}: かぎかっこが入れ子（内側は『』にする）…{n}…")
            for ln in q.get("exp", "").split("\n"):
                if not ln.strip(): continue
                # ★結論を「よって ⑤。」の形で書く。ほかの書き方だと kill_order が
                #   何も拾えず、順の乱れがあっても黙って緑になる。
                if not re.search(r"(?<![にの])よって\s*[①-⑤\s]+。", ln):
                    ng(f"第{sid}回 問{q['no']}: 解説に「よって ⑤。」の形の結論がない → {ln[:28]}")
                    continue
                m = kill_order_ng(kill_order(ln))
                if m: ng(f"第{sid}回 問{q['no']}: 解説が誤答を潰す順で{m}")
                for t in anaphora_in_kill(ln):
                    ng(f"第{sid}回 問{q['no']}: 潰し文が前の文を受けている（並べ替えで受け先が後ろへ回る）→ {t}")
            if not q.get("rules"): ng(f"第{sid}回 問{q['no']}: 参照ルールがない")
            if len(q.get("exp", "")) < 120: ng(f"第{sid}回 問{q['no']}: 解説が{len(q.get('exp',''))}字と短い")
            if "[[" in q.get("exp", ""): ng(f"第{sid}回 問{q['no']}: 解説に未解決の選択肢参照が残っている")
            if re.search(r"[①-⑤]", "".join(c for it in q["items"] for c in it["choices"])):
                ng(f"第{sid}回 問{q['no']}: 選択肢の中に丸数字がある（並べ替えでずれる）")
        if nums != [str(n) for n in range(23, 30)]:
            ng(f"第{sid}回: 解答番号が23〜29の連番でない → {nums}")
        if total != 45: ng(f"第{sid}回: 配点合計が{total}点（45点であるべき）")

        # 2) 傍線・波線の記号
        p = S["passage"]
        for k in ("a", "b", "c", "w"):
            o, c = p.count("{{" + k + "}}"), p.count("{{/" + k + "}}")
            if o != 1 or c != 1: ng(f"第{sid}回 本文: 記号{k}が開き{o}個・閉じ{c}個（各1個であるべき）")
        for k in ("x", "y"):
            if p.count("{{" + k + "}}") != p.count("{{/" + k + "}}") or p.count("{{" + k + "}}") != 1:
                ng(f"第{sid}回 本文: 記号{k}の開閉が不一致")

        # 2') 線を引いた範囲が、設問の引用と1字ずつ同じか。
        #   ★「開き数が合っている」だけでは、線を引く位置がずれていても通る。
        #     実際に、かぎかっこの内側だけを引くつもりが『「いな、かくては受け取らじ』のように
        #     開きかっこから引き始めていて、設問の引用（かっこ無し）と食い違っていた。
        #   ★線はかぎかっこの内側に引く（本番の問題冊子も第1版もこの引き方）。
        #     かっこを含めると、設問側の引用符と見分けがつかなくなる。
        # ★記号は本文に (ア)(イ)(ウ)、(Ａ)(Ｂ) の順で現れること。
        #   順が入れかわっていても、開閉の個数も引用の照合も通ってしまう。
        for grp in (("a", "b", "c"), ("x", "y")):
            at = [p.find("{{" + k + "}}") for k in grp]
            if -1 not in at and at != sorted(at):
                ng(f"第{sid}回 本文: 記号 {grp} が出てくる順が入れかわっている {at}")
        qtext = "\n".join(q["text"] for q in S["questions"])
        for k, lab in (("a", "(ア)"), ("b", "(イ)"), ("c", "(ウ)"),
                       ("x", "(Ａ)"), ("y", "(Ｂ)"), ("w", "波線")):
            m = re.findall(r"\{\{" + k + r"\}\}(.*?)\{\{/" + k + r"\}\}", p, re.S)
            if len(m) != 1: continue                      # 開閉の異常は上で拾っている
            span = deruby(m[0])
            if not span: ng(f"第{sid}回 {lab}: 線を引いた範囲が空"); continue
            if span[0] in "「『" or span[-1] in "」』":
                ng(f"第{sid}回 {lab}: 線がかぎかっこにかかっている「{span[:18]}…」")
            # 引用の内側にさらにかぎかっこが来るときは『』にする（「」の入れ子は読み手が切れ目を見失う）。
            # 比べるときは『』を「」に戻してから突き合わせる。
            inner = lambda x: x.replace("『", "「").replace("』", "」")
            qt2 = inner(qtext)
            want = ("波線部「" if k == "w" else "傍線部" + lab + "「") + span + "」"
            if want not in qt2 and (lab + "「" + span + "」") not in qt2:
                ng(f"第{sid}回 {lab}: 本文に線を引いた範囲が設問の引用と違う → 本文「{span[:26]}」")

        # 3) 本文の分量と段落（レベルごとに想定が違う）
        body = plain(p)
        n = body_chars(S["passage"])
        lo, hi = LEVELS[S["level_no"]]["chars"]
        if not lo <= n <= hi:
            ng(f"第{sid}回（{LEVELS[S['level_no']]['name']}）本文: {n}字（{lo}〜{hi}字を想定）")
        marks = len(re.findall(r"[（(]注\d+[)）]", body))
        ladder.append((sid, S["level_no"], n, S["minutes"], n / max(marks, 1)))
        po = [x for x in body.split("\n") if x.strip()]
        tj = [x for x in S["translation"].split("\n") if x.strip()]
        if len(po) != len(tj): ng(f"第{sid}回: 本文{len(po)}段落 ≠ 現代語訳{len(tj)}段落")

        # 4) 注
        # ★どの本を写したかを刷り物に出す（第1版と同じ）。書いていないと異同を追えない。
        if not S.get("base"): ng(f"第{sid}回: 底本（base）が記録されていない")
        if not 10 <= len(S["notes"]) <= 20: ng(f"第{sid}回: 注が{len(S['notes'])}個（10〜20個を想定）")
        inline = [int(x) for x in re.findall(r"\(注(\d+)\)", p)]
        if inline != list(range(1, len(S["notes"]) + 1)):
            ng(f"第{sid}回: 本文の(注n)が1からの連番で注の数と合わない → {inline}")
        flat = re.sub(r"\s", "", re.sub(r"[（(][ぁ-んァ-ン]+[)）]", "", re.sub(r"[（(]注\d+[)）]", "", body)))
        for nt in S["notes"]:
            # ★先頭2字だけの照合では「ありもせぬ語」が素通りする（古文には「あり」が頻出）。
            #   見出し語そのものが本文にあることを求める。
            # 見出し語には本文と同じ読み仮名を添える（第1版の流儀）。照合のときは両方から外す。
            head = deruby(re.sub(r"[「」『』\s]", "", re.sub(r"^\d+\s*", "", nt["word"])))
            if head and head not in flat:
                ng(f"第{sid}回 注: 「{nt['word']}」が本文に見当たらない")
            # ★本文が読み仮名を付けている語は、注の見出しにも同じ読みを付ける。
            #   付いていないと、注を引いた生徒が本文のどの語か分からない（第1版は付けている）。
            #   ★「見出し語の末尾に読み仮名が来る場合」だけを見てはいけない。語の途中に付く
            #     （「国の政(まつりごと)したため行ふ」「郡(こほり)の司(つかさ)」）と素通りする。
            #     本文の中で、読み仮名を外すと見出し語に一致する所を探し、その生の形と見比べる。
            raw = re.sub(r"[（(]注\d+[)）]", "", re.sub(r"\s", "", body))
            spans = set()
            for m in re.finditer(re.escape(head[0]), raw):
                # 読み仮名を外すと見出し語に一致する切り出しを**全部**集める。
                # 最初に一致した所で打ち切ると、読み仮名の付いた形を取りこぼす（「笞」と「笞(しもと)」）。
                for e in range(m.start() + len(head), min(len(raw), m.start() + len(head) + 24) + 1):
                    if deruby(raw[m.start():e]) == head: spans.add(raw[m.start():e])
            want = re.sub(r"[「」『』\s]", "", nt["word"])
            # ★読み仮名を外した形は必ず本文に見つかるので、「本文にある形のどれか」では通ってしまう。
            #   本文が読み仮名を付けているなら、その付いた形でなければならない。
            rubied = [x for x in spans if x != head]
            if rubied and want not in rubied:
                ng(f"第{sid}回 注: 「{nt['word']}」が本文の形と違う（本文は「{max(rubied, key=len)}」）")
            elif spans and want not in spans:
                ng(f"第{sid}回 注: 「{nt['word']}」が本文の形と違う（本文は「{max(spans, key=len)}」）")

        # 4b) 解説や選択肢が「注n」と書いている箇所が、実在する注を指しているか
        #     ★注を1つ足すと以降の番号がずれる。参照だけ古いまま残る事故を止める。
        blob = "".join(q["exp"] + q["text"] + "".join(c for it in q["items"] for c in it["choices"])
                       for q in S["questions"])
        for m in re.finditer(r"注(\d+)", blob):
            k = int(m.group(1))
            if not 1 <= k <= len(S["notes"]):
                ng(f"第{sid}回: 解説・選択肢が存在しない注{k}を指している（注は{len(S['notes'])}個）")
            else:
                refs.append((sid, k, S["notes"][k - 1]["word"]))

        # 5) 文法・ルール
        if not 8 <= len(S["grammar"]) <= 16: ng(f"第{sid}回: 文法の項目が{len(S['grammar'])}個")
        for g in S["grammar"]:
            if re.sub(r"\s", "", g["phrase"])[:3] not in flat:
                ng(f"第{sid}回 文法: 「{g['phrase']}」が本文に見当たらない")
        seen = set()
        for r in S["rules_used"]:
            if not re.match(r"ルール(0[1-9]|1[0-9]|20)\s", r["rule"]):
                ng(f"第{sid}回: ルール名が規定の形式でない「{r['rule']}」")
            if r["rule"] in seen: ng(f"第{sid}回: ルールが重複「{r['rule'][:12]}」")
            seen.add(r["rule"])
        have = {m.group(0) for x in S["rules_used"] if (m := re.match(r"ルール\d\d", x["rule"]))}
        for q in S["questions"]:
            for t in q["rules"]:
                if t not in have: ng(f"第{sid}回 問{q['no']}: 参照ルール {t} が「使うルール」の表に無い")
        # 6) 典拠
        if not S.get("source_url", "").strip(): ng(f"第{sid}回: 典拠のURLがない")
        if len(S.get("confidence", "")) < 80: ng(f"第{sid}回: 典拠の確からしさの記録が短い")

    # 7) レベルの階段が本当に階段になっているか（基礎のほうが長い、では話が合わない）
    ladder.sort()
    for a, b in zip(ladder, ladder[1:]):
        if b[1] < a[1]: ng(f"第{b[0]}回: レベルが第{a[0]}回より下がっている（前から順に解く並びでない）")
        if b[2] <= a[2]: ng(f"第{b[0]}回: 本文が第{a[0]}回より短い（{a[2]}字→{b[2]}字）")
        # ★階段は「本文が長くなること」ではなく「1分あたりに読む量が増えること」で測る。
        #   時間も一緒に伸ばすと、進むほど時間的な圧力が下がって本番から遠ざかる（実際にそうなっていた）。
        if b[2] / b[3] <= a[2] / a[3]:
            ng(f"第{b[0]}回: 1分あたりの分量が第{a[0]}回より増えていない"
               f"（{a[2]/a[3]:.0f}字/分→{b[2]/b[3]:.0f}字/分）＝進むほど楽になっている")
    # 注の手厚さも階段でなければならない。基礎で手厚く、本番で最小限にする。
    base = [r for r in ladder if r[1] == 1]; hon = [r for r in ladder if r[1] == 3]
    if base and hon and min(h[4] for h in hon) <= max(b[4] for b in base):
        ng("注の手厚さが階段になっていない（本番の回が基礎の回より注が細かい）："
           + str([(f"第{r[0]}回", f"{r[4]:.0f}字に1個") for r in ladder]))
    HONBAN_MAX = 20      # 共通テスト国語（90分5大問）で古文にあてる目安の上限
    for sid, lv, n, m, dens in ladder:
        if lv == 3 and m > HONBAN_MAX:
            ng(f"第{sid}回（本番）: 目安{m}分は本番の配分（{HONBAN_MAX}分）より緩い")

    # 8) 正解番号の分布
    if dist:
        mx, mn = max(dist.values()), min(dist.values())
        if mx - mn >= 4: ng(f"正解番号の偏り: {dict(sorted(dist.items()))}")

    if len(sys.argv) == 2:
        sys.exit("問題編と解答解説編の2つを渡すこと（1つだけでは照合できない）")
    if len(sys.argv) > 2:
        print("刷り上がりとの照合:")
        check_stamp(sets, sys.argv[1:3])
        check_glyphs(sys.argv[1], "問題編"); check_glyphs(sys.argv[2], "解答解説編")
        check_layout(sys.argv[1], "問題編")   # 解答解説編は横組みで、縦線は表の罫なので対象外
        check_style(sys.argv[1], sets)
        check_underlines(sys.argv[1], sets)
        check_pdf(sets, sys.argv[1], sys.argv[2])

    print(f"\n題数 {len(sets)}／設問 {sum(len(S['questions']) for S in sets)}問／小問 {sum(len(q['items']) for S in sets for q in S['questions'])}個")
    print("レベルの階段:", [(f"第{a}回", LEVELS[b]['name'], f"{c}字", f"{d}分",
                              f"{c/d:.0f}字/分", f"注は{e:.0f}字に1個") for a, b, c, d, e in ladder])
    print("正解の分布:", dict(sorted(dist.items())))
    if refs: print("解説が指す注:", [f"第{a}回 注{b}＝{c}" for a, b, c in refs])
    if len(sys.argv) <= 2:
        print("※ 刷り上がりは検査していない（問題編と解答解説編のPDFを渡すと逆照合する）")
    print("問題なし" if not bad else f"要修正 {len(bad)} 件")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
