#!/usr/bin/env python3
"""📖 英検 長文ドリルのシード seed-data/eiken_reading_pool_v1.json を作る (2026-09-24 塾長「長文読解・長文空所補充も単元ドリルに」→ 案 A)。

単元 (科目 eiken・level は全部 standard・本文 1 つに設問 2〜5):
  「2級 長文空所補充」「2級 長文 内容一致」「準1級 長文空所補充」「準1級 長文 内容一致」

出所 (全部この塾の書き下ろし・過去問なし):
  準1級  本番形式演習 第1弾/第2弾 (JSON: EIKEN_P1_MOCK_DIR/eikenp1_mock*/part{2,3}/S*.json)
         完全模試 全3回 (EIKEN_P1_ZENMOSHI_DIR/pre1_set{1,2,3}_data.py: P2A/P2B/P3A/P3B・P2_QUESTIONS/P3_QUESTIONS は 1 始まり)
         総合対策問題集 SET1-6 (EIKEN_P1_SOGO_DIR/part2_data.py・part3_data.py: answer は 1 始まり)
  2級    対策問題集 Vol.1 (scripts/eiken_2kyu/data/part2_cloze.json・part3_reading.json: answer は 0 始まり・全訳は無いので VOL1_JA に持つ)
         対策問題集 Vol.2 (PDF を PyMuPDF で起こす: EIKEN2_WB2_PDF)
         完全模試 全3回 (PDF: EIKEN2_MOCK_DIR/{第1回_修正版,第2回,第3回}/問題冊子 + 採点・解説冊子)
         オリジナル模試 第1弾 2026-06 (Markdown: EIKEN2_MOCK_JUNE_DIR/2級_模試第1弾_{問題,解答スクリプト,詳細解説}.md)

出力の形 (server の /api/admin/grammar/import の passages[] と同じ):
  {"subject": "eiken", "passages": [{unit, level, title, body, body_ja, source,
                                      questions: [{stem, choices, answer(0始まり), explanation, source}]}]}
  空所は本文中で「( 1 )」「( 2 )」… に付け直す (出所の (19) (41) ((1)) 等はすべて 1 始まりに正規化)。
  空所補充の stem は「( n ) に入れるのに最も適切なものを選びなさい。」で本文をまたいで同文になる
  (→ server は passages の設問を stem で dedup しない)。

使い方:
  python3 scripts/eiken_vocab/build_eiken_reading_seed.py                 # seed-data/eiken_reading_pool_v1.json を書く
  python3 scripts/eiken_vocab/build_eiken_reading_seed.py --blind DIR     # 盲検用 (答え・解説・全訳なし) と正解表を DIR に書く
  --out PATH で出力先を変えられる。入力の場所は環境変数 (下の *_DIR / *_PDF) で変えられる。

★盲検 3 名の全員一致だけを採用する工程は必須 ([[exam-material-review-rule]] / [[grammar-drill-pool-v2-2026-09-17]])。
  盲検の生出力 (scripts/eiken_vocab/blind/) はコミットしない。修正は下の OVERRIDES / DROP に書いて再ビルドする。
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import date

HOME = os.path.expanduser("~")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
P1_MOCK_DIR = os.environ.get("EIKEN_P1_MOCK_DIR", f"{HOME}/Desktop/📚 教材/英語/_生成元_英語教材_202609/data")
P1_ZENMOSHI_DIR = os.environ.get("EIKEN_P1_ZENMOSHI_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/模擬試験/準1級/英検準1級_完全模試_リスニング除外_全3回_20260923/_制作ソース")
P1_SOGO_DIR = os.environ.get("EIKEN_P1_SOGO_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/準1級/英検準1級_総合対策問題集_20260924/_制作ソース")
E2_WB1_DIR = os.environ.get("EIKEN2_WB1_DIR", os.path.join(REPO, "scripts", "eiken_2kyu", "data"))
E2_WB2_PDF = os.environ.get("EIKEN2_WB2_PDF", f"{HOME}/Desktop/📚 教材/英語/04_英検/2級/英検2級_対策問題集_Vol2.pdf")
E2_MOCK_DIR = os.environ.get("EIKEN2_MOCK_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/模擬試験/2級/英検2級_完全模試_リスニング除外_全3回_20260922")
E2_MOCK_JUNE_DIR = os.environ.get("EIKEN2_MOCK_JUNE_DIR", f"{HOME}/Desktop/📚 教材/英語/04_英検/模擬試験/2級")
OUT_DEFAULT = os.path.join(REPO, "seed-data", "eiken_reading_pool_v1.json")

U_P1_CLOZE = "準1級 長文空所補充"
U_P1_READ = "準1級 長文 内容一致"
U_2_CLOZE = "2級 長文空所補充"
U_2_READ = "2級 長文 内容一致"
UNITS = (U_2_CLOZE, U_2_READ, U_P1_CLOZE, U_P1_READ)

CIRCLED = "①②③④⑤⑥"
problems = []   # 出所の不整合 (最後に一覧して exit 1)

# ── 盲検の結果を反映する場所 ─────────────────────────────────────────
#   キー = 本文 id (下の pid: "出所タグ:本文の識別子")、値 = {設問番号(1始まり): 正解の 0 始まり添字}
#   本文ごと落とすときは DROP に pid を入れる。理由は必ずコメントに書く。
OVERRIDES = {}
DROP = set()
# 設問だけ落とす: {pid: {設問番号(1始まり), ...}}。空所補充なら本文の空所を正解語で埋めて残りの空所を付け直す。
#   2026-09-24 盲検 (3 名 × 4 分割・328 問): 327 問が全員一致 = 正解表どおり。唯一の不一致:
#   完全模試 第1回 P2B 空所 1 (As a result) は 3 名とも「In contrast も成立する」→ 全員一致だけ採用の原則で落とす。
DROP_Q = {"eikenp1-zenmoshi-1:P2B": {1}}

# 本番形式演習の全訳は 6 本だけ空所の訳が「( 21 )」のまま抜けている (出所の JSON がそう) → 正解の句の訳を空所番号の後ろに足す
MOCK_JA_FILL = {
    "eikenp1-mock-v1:S2-A": {1: "それでも", 2: "こうした修理で驚くべきなのは", 3: "その費用を払おうとする者はほとんどいない"},
    "eikenp1-mock-v1:S2-B": {1: "身体に触れる必要のない診療", 2: "そのため最も助けを必要とする患者ほど取り残される", 3: "一方、画面だけではそうはならない"},
    "eikenp1-mock-v1:S5-A": {1: "まだ知られていない問題への答え", 2: "保存された種子は気づかれないまま死んでいることがあるからだ", 3: "対照的に"},
    "eikenp1-mock-v1:S5-B": {1: "そのため字幕が標準になった", 2: "映像と言葉の一部", 3: "対照的に"},
    "eikenp1-mock-v2:V2S6-A": {1: "雨のあとには岸からあふれ出した", 2: "船を持ち上げるエンジンはなく", 3: "速さと確実さ"},
    "eikenp1-mock-v2:V2S6-B": {1: "さもなければ", 2: "動き回る人混みの陰に隠れてしまう", 3: "何を省くかを決めること"},
}

# 2級 対策問題集 Vol.1 の JSON には全訳が無い → ここで持つ (本文 6 本)
VOL1_JA = {
    "p2_1": "最近では、多くの人が店に行く代わりにオンラインで買い物をする。何かを注文すると、それは家まで届けられる。しかし、よくある問題が一つある。配達員が来たとき、家に誰もいないことが多いのだ。( 1 )そのような場合、配達員は荷物を置いていくことができず、後でもう一度来なければならない。これは時間とエネルギーの両方を無駄にする。大都市では、この種の問題がほぼ毎日起きていて、客にとっても配送会社にとっても頭痛の種になっている。この問題を解決するために、一部のマンションでは宅配ロッカーを使い始めた。配達員が来ると、荷物をロッカーの中に入れて鍵をかける。客は後で、メールかスマートフォンのアプリのメッセージで暗証番号を( 2 )受け取る。この番号を使えば、客はいつでもロッカーを開けて荷物を取り出せる。この仕組みは、一日中家で待っていなくてよいので便利だ。朝早くや夜遅く、通勤や通学の途中に荷物を受け取ることもできる。配達員にとっても良いことがある。( 3 )例えば、同じ家を何度も訪ねる必要がない。その結果、より短い時間でより多くの荷物を届けられる。こうした利点のおかげで、宅配ロッカーは世界中の多くの都市でますます普及してきている。",
    "p2_2": "冬になると、多くの野生動物にとって食べ物が見つけにくくなる。植物は育つのをやめ、ほとんどの昆虫は姿を消す。( 1 )しかし、クマやリスなどの一部の動物は、寒い季節を生き延びる賢い方法を見つけた。いちばん寒い数か月のあいだ、長い眠りにつくのだ。この深い眠りは冬眠と呼ばれる。冬が来る前に、これらの動物はできるだけたくさん食べる。体は余分な食べ物を皮膚の下の脂肪として( 2 )蓄える。そして眠っているあいだ、体はこの脂肪をエネルギーとして使うことができる。実際、大きなクマは何も食べずに何か月も生きられる。冬眠中、動物の心臓はとてもゆっくり打ち、体は冷たくなる。こうして動物はエネルギーを節約し、食べる必要がなくなる。ほとんど動かないので、一日に使うエネルギーはごくわずかだ。数週間しか眠らない動物もいれば、( 3 )一方で数か月眠る動物もいる。春が来て再び暖かくなると、彼らは目を覚ます。長い眠りのあとで、おなかをすかせてやせている。そのころには植物が育ち始め、昆虫も戻っているので、動物はまた簡単に食べ物を見つけられる。科学者によれば、冬眠は、食べる物がほとんど無い季節を動物が生き抜くための最も賢い方法の一つだという。",
    "p2_3": "「図書館」という言葉を聞くと、人はたいてい本でいっぱいの静かな部屋を思い浮かべる。長いあいだ、図書館はまさにそういう場所だった。人々は主に本を借りるためや、新聞や雑誌を読むために訪れた。( 1 )しかし、今日の図書館は変わりつつあり、本以外にもはるかに多くのものを提供している。この変化の理由の一つはインターネットだ。今では人々はスマートフォンでほとんどどんな情報でも見つけられるので、何かを調べるためだけに来る人は減っている。役に立ち続けるために、多くの図書館は新しい種類のサービスを( 2 )提供し始めた。例えば、DVD や音楽、さらには道具やおもちゃまで貸し出す図書館もある。英語教室や小さな子ども向けの読み聞かせの時間、コンピューターの使い方を学べる講習会を開くところもある。現代の図書館は、人々が集まって一緒に作業する場所にもなった。多くの図書館には今、座り心地のよい席、無料の Wi-Fi、勉強のための静かな部屋がある。学生はよくテストの準備のためにそこへ行き、( 3 )一方で大人の中には会議室を自分の仕事に使う人もいる。このように、図書館はもはや本を保管するだけの場所ではない。あらゆる年代の人が学び、くつろぎ、一緒に時間を過ごせる地域の中心になったのだ。こうした努力のおかげで、図書館はインターネットの時代にも重要であり続けている。",
    "p3_1": "田中ケンは日本の北部の小さな町で育った。子どものころ、祖母が駅の近くで小さなパン屋を営んでいた。毎朝、ケンは早起きして祖母がパンを作るのを見ていた。台所いっぱいに広がる温かい香りが大好きだった。重い小麦粉の袋を運ぶのをよく手伝い、祖母は手で生地の形を作る方法を教えてくれた。\n\nしかし、高校を卒業した後、ケンはパン職人にはならなかった。両親が東京の大きな会社で働くことを望んだので、彼は都会に出て銀行に就職した。給料はよかったが、ケンは幸せではなかった。一日中コンピューターの前で過ごし、誰かと話すこともほとんどなかった。毎晩、彼は祖母の温かい台所のことを思い出していた。\n\nある冬、ケンの祖母が病気になり、パン屋を続けられなくなった。ケンは祖母を助けるために故郷へ戻ることにした。最初は数週間だけ滞在するつもりだった。しかし、もう一度パンを焼き始めると、自分がどれほどそれを愛していたかを思い出した。彼は祖母に昔のレシピを教えてほしいと頼み、祖母は喜んで引き受けた。\n\nケンは腕を上げるために懸命に働いた。地元の果物をパンに加えるといった新しいアイデアを試し、まもなく他の町からも客が買いに来るようになった。小さなパン屋は再びにぎわいを取り戻した。今ではケンが一人で店を切り盛りし、祖母はときどき窓辺に座って彼が働く様子を眺めている。ケンはよく、銀行の仕事を辞めたことは人生で最良の決断だったと言う。今は心から愛することをしているからだ。",
    "p3_2": "タコは海の中で最も興味深い動物の一つだ。8本の腕と、骨のない柔らかい体を持っている。骨がないので、タコは簡単に体の形を変えられる。この能力は、自分を食べようとする大きな動物から隠れるのに役立つ。コイン一枚ほどの小さな穴を体ごとくぐり抜けられるタコさえいる。\n\nタコは色を変えるのもとても得意だ。皮膚にある特別な細胞のおかげで、1秒足らずで周囲の色に合わせることができる。岩の上で休んでいるタコは、その岩とほとんど見分けがつかなくなる。この技は隠れるためだけでなく、えさとして狙う小魚やカニを驚かせるためにも役立つ。\n\n科学者たちは、タコが多くの人が思うよりはるかに賢いことを発見した。ある実験で、研究者はタコに、おいしそうなカニが入ったガラスのびんを与えた。ふたはきつく閉められていたが、タコは腕を使ってそれを開けることを学んだ。空の貝殻を海底で運んでいるタコも観察されている。あとで彼らはその貝殻を、身を守るための隠れ家のように使うのだ。\n\nしかし、タコの寿命はふつう短い。ほとんどの種類は1、2年しか生きない。メスのタコは何千個もの卵を産み、ふ化するまで注意深く守る。この間、メスはえさを探しに出かけず、しばしばとても弱ってしまう。悲しいことに、多くの母ダコは赤ちゃんが生まれてすぐに死んでしまう。それでも、この驚くべき動物は、研究する科学者たちを驚かせ続けている。",
    "p3_3": "今日、チョコレートは世界で最も人気のあるお菓子の一つだ。しかし、昔の人々が食べていたチョコレートは、私たちが今楽しんでいるものとは大きく違っていた。チョコレートは、中央アメリカと南アメリカの暖かい地域に育つカカオの木の種から作られる。何千年も前、その土地の人々は、この種を特別な飲み物にできることを発見した。\n\n古代マヤやアステカの文化の人々は、この飲み物をとても愛した。彼らはカカオの種を乾かし、すりつぶして粉にし、その粉を水と混ぜた。しかし、その飲み物は現代のホットチョコレートのように甘くはなかった。むしろ苦く、より強い味にするために唐辛子などの香辛料をよく加えた。こうした人々にとってカカオはとても貴重だった。実際、アステカの人々は、食べ物やその他の品物を買うためのお金としてカカオの種を使うこともあった。\n\n16世紀、ヨーロッパから来た探検家たちがこの飲み物を味わい、カカオの種を自分たちの国へ持ち帰った。最初はヨーロッパの人々もこの飲み物を苦すぎると感じた。やがて誰かが砂糖とはちみつを加えることを思いつき、その飲み物はたちまち裕福な人々のあいだで人気になった。カカオは高価だったので、長年のあいだ、裕福な家庭だけがそれを飲む余裕があった。\n\n19世紀にすべてが変わった。新しい機械によって、チョコレートを速く安く作ることが可能になった。ある会社が初めて、飲むのではなく食べられる固形のチョコレートバーを作った。まもなくチョコレートは金持ちだけのものではなくなり、ふつうの人々も楽しめるようになった。今日、世界中の工場がカカオの種を何千種類もの製品に変えている。現代のチョコレートは大きく変わったが、それでも、人々が大昔に初めて使ったのと同じ小さな種から始まっているのだ。",
}


# ── 共通ヘルパー ──────────────────────────────────────────────────────
def norm_space(s):
    return re.sub(r"[ \t　]+", " ", str(s or "")).strip()


def tidy_ja(s):
    """PDF 起こしの日本語は行末で改行されている → 日本語文字どうしの改行/空白は詰める。"""
    s = str(s or "")
    s = re.sub(r"(?<=[^\x00-\x7F])[ \t]*\n[ \t]*(?=[^\x00-\x7F])", "", s)
    s = re.sub(r"(?<=[^\x00-\x7F])[ \t]+(?=[^\x00-\x7F])", "", s)
    s = re.sub(r"[ \t]*\n[ \t]*", " ", s)
    return norm_space(s)


def strip_choice(s):
    s = norm_space(s)
    s = re.sub(r"^[①②③④⑤⑥]\s*", "", s)
    s = re.sub(r"^\(?[1-6]\)?[\.．:：]?\s+", "", s)
    return s.strip()


def stem_cloze(k):
    return f"( {k} ) に入れるのに最も適切なものを選びなさい。"


def circled(i0):
    return CIRCLED[i0] if 0 <= i0 < len(CIRCLED) else str(i0 + 1)


def fmt_expl(choices, ans0, main, wrongs=None, evidence=None, extra=None):
    """解説を 1 つの形にそろえる: 正解 → 本文 → 【根拠】 → 【他の選択肢】。wrongs は {0始まり添字: 理由}。"""
    lines = [f"正解 {circled(ans0)} {choices[ans0]}"]
    main = norm_space(main)
    if main:
        lines.append(main)
    if evidence:
        lines.append(f"【根拠】{norm_space(evidence)}")
    if wrongs:
        lines.append("【他の選択肢】")
        for i, ch in enumerate(choices):
            if i == ans0:
                continue
            r = norm_space(wrongs.get(i, ""))
            if r.lower().startswith(norm_space(ch).lower()):
                r = r[len(norm_space(ch)):].lstrip(" …:：・、,")
            lines.append(f"{circled(i)} {ch}" + (f" … {r}" if r else ""))
    if extra:
        lines.append(norm_space(extra))
    return "\n".join(lines)


def match_wrongs(choices, ans0, why_wrong_list):
    """誤答理由のリスト (正解を飛ばした順) を選択肢の添字に対応づける。理由が選択肢の文で始まる/引用していれば文で照合、
    さもなければ順番で対応づける。"""
    wrong_idx = [i for i in range(len(choices)) if i != ans0]
    out = {}
    used = set()
    unmatched = []
    for w in why_wrong_list or []:
        w = str(w or "")
        wl = norm_space(w).lower()
        cands = []
        for i in wrong_idx:
            if i in used:
                continue
            full = norm_space(choices[i]).lower()
            frag = full[:28]
            if full and full in wl:
                cands.append((2, len(full), i))       # 文全体が含まれる
            elif frag and frag in wl:
                cands.append((1, len(full), i))       # 先頭 28 字だけ (「the government」「the government's …」の取り違え防止に最長を採る)
        hit = max(cands)[2] if cands else None
        if hit is None:
            unmatched.append(w)
        else:
            used.add(hit)
            out[hit] = w
    rest = [i for i in wrong_idx if i not in used]
    for i, w in zip(rest, unmatched):
        out[i] = w
    return out


def renumber_markers(text, pattern=r"\(\s*(\d{1,2})\s*\)"):
    """本文の空所を出現順に ( 1 ) ( 2 ) … に付け直す → (本文, {旧番号: 新番号})。"""
    order = []
    for m in re.finditer(pattern, text):
        n = int(m.group(1))
        if n not in order:
            order.append(n)
    mapping = {old: k for k, old in enumerate(order, 1)}
    text2 = re.sub(pattern, lambda m: f"( {mapping[int(m.group(1))]} )", text)
    return text2, mapping


def renum_text(text, mapping):
    """解説・全訳の中の旧番号 (19) / ( 19 ) / ((19)) / 【19】 を新番号の ( 1 ) に直す。旧番号に無いものは触らない。"""
    if not text or not mapping:
        return text or ""

    def rep(m):
        n = int(m.group(1))
        return f"( {mapping[n]} )" if n in mapping else m.group(0)
    return re.sub(r"\(\(?\s*(\d{1,2})\s*\)?\)|【\s*(\d{1,2})\s*】", lambda m: rep(m) if m.group(1) else (f"( {mapping[int(m.group(2))]} )" if int(m.group(2)) in mapping else m.group(0)), text)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mask_email(s):
    """教材のメール文の架空アドレス (差出人欄の 名前@団体名.org のような値) の @ を全角 ＠ にする。
    見た目は同じで、公開リポジトリの PII ゲート (ASCII の @ を探す) に掛からない。実在アドレスは出所に無い。"""
    return re.sub(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1＠\2", str(s or ""))


def passage(unit, title, body, body_ja, source, questions, pid):
    return {"pid": pid, "unit": unit, "level": "standard", "title": norm_space(title) or None,
            "body": mask_email(body.strip()), "body_ja": mask_email((body_ja or "").strip()) or None,
            "source": source[:60], "questions": questions}


def q(stem, choices, ans0, explanation, source):
    return {"stem": mask_email(norm_space(stem)), "choices": [mask_email(strip_choice(c)) for c in choices], "answer": int(ans0),
            "explanation": mask_email(explanation.strip()), "source": source[:30]}


# ── 準1級 本番形式演習 (JSON) ───────────────────────────────────────────
def load_p1_mock():
    out = []
    for sub, tag in (("eikenp1_mock", "eikenp1-mock-v1"), ("eikenp1_mock2", "eikenp1-mock-v2")):
        for part, unit in (("part2", U_P1_CLOZE), ("part3", U_P1_READ)):
            files = sorted(glob.glob(f"{P1_MOCK_DIR}/{sub}/{part}/S*.json"), key=lambda f: int(re.search(r"S(\d+)", os.path.basename(f)).group(1)))
            if not files:
                problems.append(f"準1級 本番形式演習の JSON が無い: {P1_MOCK_DIR}/{sub}/{part}")
            for f in files:
                for p in json.load(open(f, encoding="utf-8")):
                    body = "\n\n".join(norm_space(x) for x in p["paragraphs"])
                    ja = p.get("translation") or ""
                    body_ja = "\n\n".join(ja) if isinstance(ja, list) else str(ja)
                    qs = []
                    pid = f"{tag}:{p['id']}"
                    if part == "part2":
                        mapping = {}
                        for k, b in enumerate(p["blanks"], 1):
                            mk = b["marker"]
                            if body.count(mk) != 1:
                                problems.append(f"{pid}: 空所 {mk} が本文に {body.count(mk)} 回")
                            body = body.replace(mk, f"( {k} )")
                            mm = re.search(r"(\d+)", mk)
                            if mm:
                                mapping[int(mm.group(1))] = k
                            if b.get("no") is not None:
                                mapping[int(b["no"])] = k   # 全訳は本番の番号 (19) で書かれている
                        body_ja = renum_text(body_ja, mapping)
                        for k, fill in (MOCK_JA_FILL.get(pid) or {}).items():
                            if not re.search(r"\(\s*%d\s*\)" % k, body_ja):
                                problems.append(f"{pid}: 全訳に空所 ( {k} ) が無いのに MOCK_JA_FILL がある")
                            body_ja = re.sub(r"\s*\(\s*%d\s*\)\s*" % k, f"( {k} ){fill}", body_ja, count=1)
                        for k, b in enumerate(p["blanks"], 1):
                            wr = match_wrongs(b["choices"], b["answer"], b.get("why_wrong"))
                            qs.append(q(stem_cloze(k), b["choices"], b["answer"],
                                        fmt_expl(b["choices"], b["answer"], renum_text(b.get("why_correct", ""), mapping),
                                                 {i: renum_text(w, mapping) for i, w in wr.items()}), tag))
                    else:
                        for qq in p["questions"]:
                            wr = match_wrongs(qq["choices"], qq["answer"], qq.get("why_wrong"))
                            qs.append(q(qq["stem"], qq["choices"], qq["answer"],
                                        fmt_expl(qq["choices"], qq["answer"], qq.get("why_correct", ""), wr, evidence=qq.get("evidence")), tag))
                    out.append(passage(unit, p.get("title"), body, body_ja, f"{tag} {p['id']}", qs, pid))
    return out


# ── 準1級 完全模試 (python データ) ─────────────────────────────────────
_SEITO_RE = re.compile(r"^正答は?\s*(\d)\s*[。．.]?\s*|\s*正答は?\s*(\d)\s*[。．.]?\s*$")


def strip_seito(text, ans0, where):
    """完全模試の解説の「正答3。」(先頭) /「正答は3。」(末尾) を落とす。番号が answer と違えば出所の不整合として記録。"""
    text = norm_space(text)
    for m in _SEITO_RE.finditer(text):
        n = int(m.group(1) or m.group(2))
        if n - 1 != ans0:
            problems.append(f"{where}: 解説の正答 {n} と answer {ans0 + 1} が食い違う")
    return _SEITO_RE.sub("", text).strip()


def load_p1_zenmoshi():
    out = []
    for n in (1, 2, 3):
        path = f"{P1_ZENMOSHI_DIR}/pre1_set{n}_data.py"
        if not os.path.exists(path):
            problems.append(f"準1級 完全模試のデータが無い: {path}")
            continue
        m = load_module(path, f"pre1_set{n}_data")
        tag = f"eikenp1-zenmoshi-{n}"
        expl = getattr(m, "READING_EXPLANATIONS", {})
        p3keys = sorted(m.P3_QUESTIONS)
        p3_split = {"P3A": p3keys[:3], "P3B": p3keys[3:]}
        for nm in ("P2A", "P2B"):
            body = getattr(m, nm).strip()
            body, mapping = renumber_markers(body)
            qs = []
            for old, k in sorted(mapping.items(), key=lambda kv: kv[1]):
                choices, ans1 = m.P2_QUESTIONS[old]
                e = strip_seito(expl.get(old, ""), ans1 - 1, f"{tag} {nm} 問{old}")
                qs.append(q(stem_cloze(k), choices, ans1 - 1, fmt_expl(choices, ans1 - 1, renum_text(e, mapping)), tag))
            if len(qs) != 3:
                problems.append(f"{tag} {nm}: 空所が {len(qs)} 個 (3 のはず)")
            out.append(passage(U_P1_CLOZE, getattr(m, nm + "_TITLE", ""), body, renum_text(getattr(m, nm + "_JP", ""), mapping),
                               f"{tag} {nm}", qs, f"{tag}:{nm}"))
        for nm in ("P3A", "P3B"):
            body = getattr(m, nm).strip()
            qs = []
            for old in p3_split[nm]:
                qtext, choices, ans1 = m.P3_QUESTIONS[old]
                e = strip_seito(expl.get(old, ""), ans1 - 1, f"{tag} {nm} 問{old}")
                qs.append(q(qtext, choices, ans1 - 1, fmt_expl(choices, ans1 - 1, e), tag))
            out.append(passage(U_P1_READ, getattr(m, nm + "_TITLE", ""), body, getattr(m, nm + "_JP", ""), f"{tag} {nm}", qs, f"{tag}:{nm}"))
    return out


# ── 準1級 総合対策問題集 (python データ) ─────────────────────────────────
def parse_distractor_notes(s):
    """「1：…／3：…／4：…」→ {0: …, 2: …, 3: …}"""
    out = {}
    for m in re.finditer(r"([1-6])[：:]\s*(.*?)(?=(?:／|/|\s)[1-6][：:]|$)", str(s or "")):
        out[int(m.group(1)) - 1] = norm_space(m.group(2)).rstrip("／/")
    return out


def load_p1_sogo():
    out = []
    p2p = f"{P1_SOGO_DIR}/part2_data.py"
    p3p = f"{P1_SOGO_DIR}/part3_data.py"
    if not (os.path.exists(p2p) and os.path.exists(p3p)):
        problems.append(f"準1級 総合対策のデータが無い: {P1_SOGO_DIR}")
        return out
    p2 = load_module(p2p, "sogo_part2_data").PART2_BY_SET
    p3 = load_module(p3p, "sogo_part3_data").PART3_BY_SET
    for set_no in sorted(p2):
        e = p2[set_no]
        tag = f"eikenp1-sogo-{set_no}"
        body, mapping = renumber_markers(e["passage"].strip())
        # 出所の全訳は編集中に段落内へ改行 1 つが混じることがある (2026-09-24 に 2 本) → 段落の切れ目 (空行) だけ残して詰める
        ja_src = re.sub(r"(?<!\n)\n(?!\n)", "", e.get("translation", "").strip())
        ja, _ = renumber_markers(ja_src, pattern=r"【\s*(\d{1,2})\s*】")
        qs = []
        for k, qq in enumerate(e["questions"], 1):
            ans0 = int(qq["answer"]) - 1
            qs.append(q(stem_cloze(k), qq["options"], ans0,
                        fmt_expl(qq["options"], ans0, qq.get("rationale", ""), parse_distractor_notes(qq.get("distractor_notes"))), tag))
        if len(qs) != len(mapping):
            problems.append(f"{tag} part2: 設問 {len(qs)} と空所 {len(mapping)} が合わない")
        out.append(passage(U_P1_CLOZE, e.get("title"), body, ja, f"{tag} part2", qs, f"{tag}:P2"))
    for set_no in sorted(p3):
        e = p3[set_no]
        tag = f"eikenp1-sogo-{set_no}"
        qs = []
        for qq in e["questions"]:
            ans0 = int(qq["answer"]) - 1
            qs.append(q(qq["question"], qq["options"], ans0,
                        fmt_expl(qq["options"], ans0, qq.get("rationale", ""), parse_distractor_notes(qq.get("distractor_notes")),
                                 evidence=qq.get("evidence")), tag))
        out.append(passage(U_P1_READ, e.get("title"), e["passage"].strip(), e.get("translation", ""), f"{tag} part3", qs, f"{tag}:P3"))
    return out


# ── 2級 対策問題集 Vol.1 (JSON・全訳なし) ────────────────────────────────
def load_e2_wb1():
    out = []
    tag = "eiken2-wb-vol1"
    p2 = f"{E2_WB1_DIR}/part2_cloze.json"
    p3 = f"{E2_WB1_DIR}/part3_reading.json"
    if not (os.path.exists(p2) and os.path.exists(p3)):
        problems.append(f"2級 Vol.1 の JSON が無い: {E2_WB1_DIR}")
        return out
    for p in json.load(open(p2, encoding="utf-8"))["passages"]:
        body, mapping = renumber_markers(norm_space(p["text"]))
        qs = []
        for b in p["blanks"]:
            k = mapping.get(int(b["n"]), int(b["n"]))
            qs.append(q(stem_cloze(k), b["choices"], b["answer"], fmt_expl(b["choices"], b["answer"], b.get("rationale", "")), tag))
        out.append(passage(U_2_CLOZE, p.get("title"), body, VOL1_JA.get(p["id"], ""), f"{tag} {p['id']}", qs, f"{tag}:{p['id']}"))
    for p in json.load(open(p3, encoding="utf-8"))["passages"]:
        body = "\n\n".join(norm_space(x) for x in p["paragraphs"])
        qs = []
        for qq in p["questions"]:
            wr = {}
            for letter, reason in (qq.get("why_others_wrong") or {}).items():
                i = "ABCDEF".find(str(letter).strip().upper()[:1])
                if i >= 0:
                    wr[i] = reason
            qs.append(q(qq["q"], qq["choices"], qq["answer"], fmt_expl(qq["choices"], qq["answer"], "", wr, evidence=qq.get("evidence")), tag))
        out.append(passage(U_2_READ, p.get("title"), body, VOL1_JA.get(p["id"], ""), f"{tag} {p['id']}", qs, f"{tag}:{p['id']}"))
    return out


# ── PDF 起こし (PyMuPDF) ──────────────────────────────────────────────
def pdf_lines(path, pages=None):
    """(page_no, x0, x1, text, y0, y1) の行リスト。ページ内は上から順。"""
    import fitz  # PyMuPDF
    d = fitz.open(path)
    out = []
    for i, pg in enumerate(d):
        if pages is not None and i not in pages:
            continue
        rows = []
        for bl in pg.get_text("dict")["blocks"]:
            for ln in bl.get("lines", []):
                txt = "".join(s["text"] for s in ln["spans"])
                if txt.strip():
                    rows.append((i, ln["bbox"][0], ln["bbox"][2], txt, ln["bbox"][1], ln["bbox"][3]))
        rows.sort(key=lambda r: (round(r[4]), r[1]))
        out += rows
    return out


def split_paras_gap(lines, ja=False):
    """行 [(page, x0, x1, text, y0, y1)] を段落に分ける。段落の切れ目 = 行間が通常の行送りより広い所、または前の行が
    右端まで届いていない所 (ページをまたぐ所も同じ)。段落内は英語なら空白、日本語なら詰めて連結。
    メールの見出し (From/To/Date/Subject・送信者/宛先/日付/件名) どうし、ごく短い行どうし (署名) は改行 1 つでつなぐ。"""
    if not lines:
        return ""
    left = min(r[1] for r in lines)
    right = max(r[2] for r in lines)
    width = max(right - left, 1)
    pitches = sorted(b[4] - a[4] for a, b in zip(lines, lines[1:]) if a[0] == b[0] and b[4] > a[4])
    pitch = pitches[len(pitches) // 2] if pitches else 12.0
    hdr = re.compile(r"^(From|To|Date|Subject|送信者|宛先|日付|件名)[:：]")

    def short(r):
        return (r[2] - left) < width * 0.88

    def very_short(r):
        return (r[2] - left) < width * 0.45

    def ends_terminal(r):
        return bool(re.search(r"[.?!:;。！？」』）)\"”’]\s*$", r[3]))
    groups = [[lines[0]]]
    for prev, cur in zip(lines, lines[1:]):
        # 段落の切れ目: 行間が広い / 前の行が右端まで届かず文末で終わる (右揃えでないメール文で、折り返しの短い行を切らない) /
        # ごく短い行 (見出し・署名・呼びかけ) の後 / 見出し行の前後
        new = ((prev[0] == cur[0] and (cur[4] - prev[4]) > pitch * 1.25)
               or (short(prev) and (ends_terminal(prev) or very_short(prev)))
               or (very_short(cur) and ends_terminal(prev) and not ends_terminal(cur))   # 文末の直後のごく短い行 (Sincerely, / 敬具) は署名の始まり (段落末の短い折り返し行は「。」で終わるので除く)
               or bool(hdr.match(prev[3].strip())) or bool(hdr.match(cur[3].strip())))
        (groups.append([cur]) if new else groups[-1].append(cur))
    texts = []
    for g in groups:
        t = g[0][3].strip()
        for a, b in zip(g, g[1:]):
            tb = b[3].strip()
            if ja and re.search(r"[^\x00-\x7F]$", t) and re.match(r"^[^\x00-\x7F]", tb):
                t += tb
            else:
                t += " " + tb
        texts.append((norm_space(t), g[0], g[-1]))
    out = []
    for text, first, last in texts:
        if out:
            _pt, _pf, _pl = out[-1]
            same_hdr = bool(hdr.match(text)) and bool(hdr.match(_pt.split("\n")[-1]))
            # 署名 (Sincerely, / 氏名 / 肩書) のようにごく短い行が続くときだけ改行 1 つでつなぐ。前の行が文末 (。 や .) なら別段落
            both_short = (very_short(first) and very_short(_pl) and not hdr.match(text) and not hdr.match(_pt.split("\n")[-1])
                          and not re.search(r"[.。！？!?]\s*$", _pl[3]))
            if same_hdr or both_short:
                out[-1] = (_pt + "\n" + text, _pf, last)
                continue
        out.append((text, first, last))
    return "\n\n".join(t for t, _, _ in out)


def pdf_blocks(path, pages=None):
    """(page_no, x0, y0, text) のブロックリスト (段落はブロックで分かれている PDF 向け)。"""
    import fitz
    d = fitz.open(path)
    out = []
    for i, pg in enumerate(d):
        if pages is not None and i not in pages:
            continue
        for b in sorted(pg.get_text("blocks"), key=lambda b: (round(b[1]), b[0])):
            if b[4].strip():
                out.append((i, b[0], b[1], b[4]))
    return out


def pdf_text(path):
    import fitz
    d = fitz.open(path)
    return "\n".join(pg.get_text() for pg in d)


# ── 2級 対策問題集 Vol.2 (PDF) ─────────────────────────────────────────
_TITLE_RE = re.compile(r"^(.+?)\s*［(.+?)］\s*$")
_WORDS_RE = re.compile(r"^\d+\s*words$")


def load_e2_wb2():
    out = []
    tag = "eiken2-wb-vol2"
    if not os.path.exists(E2_WB2_PDF):
        problems.append(f"2級 Vol.2 の PDF が無い: {E2_WB2_PDF}")
        return out
    lines = pdf_lines(E2_WB2_PDF)
    # 1) 問題編: 「大問2　長文の語句空所補充」〜「大問4」の間
    starts = [i for i, ln in enumerate(lines) if ln[3].startswith("大問2") and "空所補充" in ln[3]]
    ends = [i for i, ln in enumerate(lines) if re.match(r"^大問4", ln[3]) or "ライティング" in ln[3][:6]]
    if not starts:
        problems.append("2級 Vol.2: 大問2 の見出しが見つからない")
        return out
    s = starts[0]
    e = next((i for i in ends if i > s), len(lines))
    seg = lines[s:e]
    right_edge = max(ln[2] for ln in seg)
    passages = []   # {title, genre, paras:[[lines]], questions:[{no, qtext, choices}], part}
    cur = None
    cur_q = None
    part = 2
    para = []

    def flush_para():
        nonlocal para
        if cur is not None and para:
            cur["paras"].append(" ".join(norm_space(x) for x in para))
        para = []

    for pno, x0, x1, txt, _y0, _y1 in seg:
        t = txt.strip()
        if t.startswith("大問3"):
            part = 3
            continue
        if t.startswith("大問2") or t.startswith("本文を読み") or t.startswith("本文の内容に関する"):
            continue
        m = _TITLE_RE.match(t)
        if m and x0 < 50:
            flush_para()
            cur = {"title": m.group(1).strip(), "genre": m.group(2).strip(), "paras": [], "questions": [], "part": part}
            passages.append(cur)
            cur_q = None
            continue
        if _WORDS_RE.match(t):
            continue
        if cur is None:
            continue
        if re.fullmatch(r"\d{2}", t) and x0 < 50:
            flush_para()
            cur_q = {"no": int(t), "qtext": "", "choices": []}
            cur["questions"].append(cur_q)
            continue
        if cur_q is not None:
            if t[:1] in CIRCLED:
                cur_q["choices"].append(t)
            elif cur_q["choices"]:
                cur_q["choices"][-1] = norm_space(cur_q["choices"][-1] + " " + t)
            else:
                cur_q["qtext"] = norm_space(cur_q["qtext"] + " " + t)
            continue
        # 本文の行
        para.append(t)
        if x1 < right_edge - 25:   # 行が右端まで届かない = 段落の最後の行
            flush_para()
    flush_para()
    # 2) 解答一覧 (大問2（長文空所補充）41 … 49 ③ …)
    full = pdf_text(E2_WB2_PDF)
    key = {}
    for head in ("大問2（長文空所補充）", "大問3（内容一致）"):
        i = full.find(head)
        if i < 0:
            problems.append(f"2級 Vol.2: 解答一覧の {head} が無い")
            continue
        chunk = full[i + len(head): i + len(head) + 400]
        nums = [int(x) for x in re.findall(r"(?m)^(\d{2})$", chunk)]
        marks = re.findall(r"[①②③④]", chunk)
        nums = nums[:len(marks)]
        for n, mk in zip(nums, marks):
            key[n] = CIRCLED.index(mk)
    # 3) 解説 (「NN 正解 ③…」〜) と全訳
    expl = {}
    zenyaku = {}   # title -> 全訳
    kaisetsu_start = None
    for m in re.finditer(r"大問2　解説", full):
        kaisetsu_start = m.start()
    if kaisetsu_start is None:
        problems.append("2級 Vol.2: 解説編の 大問2 が無い")
    else:
        kt = full[kaisetsu_start:]
        end_m = re.search(r"大問4　解説|ライティング　解説|大問4　", kt)
        if end_m:
            kt = kt[:end_m.start()]
        # 題名ごとに区切る
        pieces = re.split(r"(?m)^(.+?\s*［.+?］)\s*$", kt)
        # pieces: [前置き, title1, body1, title2, body2, ...]
        for ti in range(1, len(pieces) - 1, 2):
            title = _TITLE_RE.match(pieces[ti].strip()).group(1).strip()
            bodytxt = pieces[ti + 1]
            # 全訳
            zm = re.search(r"^全訳\s*$([\s\S]*?)(?=^重要語句\s*$|\Z)", bodytxt, re.M)
            if zm:
                z = zm.group(1)
                z = re.sub(r"\n=+ PAGE \d+ =+\n", "\n", z)
                paras = [tidy_ja(x) for x in re.split(r"【第\d+段落】", z) if tidy_ja(x)]
                zenyaku[title] = "\n\n".join(paras)
            # 設問解説
            qparts = re.split(r"(?m)^(\d{2})\s*正解\s*([①②③④])\s*(.*)$", bodytxt)
            for qi in range(1, len(qparts) - 3, 4):
                no = int(qparts[qi]); mk = qparts[qi + 1]; rest = qparts[qi + 3]
                rest = rest.split("\n全訳")[0]
                lab = []
                prev_label = None
                for ln in rest.split("\n"):
                    ln2 = ln.strip()
                    if not ln2 or ln2.startswith("====="):
                        continue
                    # ラベルは行頭に貼り付いている (前Owners… / 後( 41 )… / 根拠She… / 訳彼女は… / 誤答In contrast… / コツ接続語…)。
                    # 「前文は…」のような普通の文を 【前】 にしないため、前/後/根拠/誤答 は直後が英字か括弧のときだけラベル扱い
                    mm = re.match(r"^(前|後|根拠|誤答)(?=[A-Za-z(（『「])(.*)$", ln2) or re.match(r"^(訳|コツ)(.*)$", ln2)
                    if mm:
                        lab.append(f"\x00【{mm.group(1)}】{mm.group(2)}")
                        prev_label = mm.group(1)
                    elif re.match(r"^[①②③④]", ln2):
                        lab.append("\x00" + ln2)
                        prev_label = None
                    elif prev_label in ("前", "後", "根拠") and re.match(r"^[^\x00-\x7F]", ln2):
                        lab.append("\x00" + ln2)   # 英文のラベル行の次に日本語の説明が始まる
                        prev_label = None
                    else:
                        lab.append(ln2)
                # 行の折り返しを戻す (日本語どうしは詰める・それ以外は空白)。\x00 = 意図した改行
                text = "\n".join(lab)
                text = re.sub(r"(?<=[^\x00-\x7F])\n(?=[^\x00-\x7F])", "", text)
                text = text.replace("\n", " ")
                text = re.sub(r"\s*\x00\s*", "\n", text).strip()
                expl[no] = (CIRCLED.index(mk), text)
    # 4) 組み立て
    for p in passages:
        unit = U_2_CLOZE if p["part"] == 2 else U_2_READ
        ja = zenyaku.get(p["title"], "")
        if p["part"] == 2 or not re.search(r"【第\d+段落】", full):
            body_join = " ".join(p["paras"]) if p["part"] == 2 else "\n\n".join(p["paras"])
        else:
            body_join = "\n\n".join(p["paras"])
        if p["part"] == 3 and ja and ja.count("\n\n") + 1 != len(p["paras"]):
            problems.append(f"{tag} {p['title']}: 段落数 本文 {len(p['paras'])} ≠ 全訳 {ja.count(chr(10) * 2) + 1}")
        body, mapping = renumber_markers(body_join)
        qs = []
        for qq in p["questions"]:
            no = qq["no"]
            if len(qq["choices"]) != 4:
                problems.append(f"{tag} {p['title']} 問{no}: 選択肢 {len(qq['choices'])} 個")
                continue
            ans_key = key.get(no)
            ans_ex = expl.get(no, (None, ""))[0]
            if ans_key is None and ans_ex is None:
                problems.append(f"{tag} 問{no}: 正解が見つからない")
                continue
            if ans_key is not None and ans_ex is not None and ans_key != ans_ex:
                problems.append(f"{tag} 問{no}: 解答一覧 {ans_key + 1} と解説 {ans_ex + 1} が食い違う")
            ans0 = ans_key if ans_key is not None else ans_ex
            etext = renum_text(expl.get(no, (None, ""))[1], mapping)
            if p["part"] == 3:
                _ql = norm_space(qq["qtext"]).lower()
                _cl = norm_space(strip_choice(qq["choices"][ans0])).lower() if 0 <= ans0 < len(qq["choices"]) else ""
                etext = "\n".join(ln for ln in etext.split("\n")
                                  if norm_space(ln).lower() != _ql and norm_space(strip_choice(ln)).lower() != _cl
                                  and not norm_space(ln).lower().startswith(_ql + " "))
            if p["part"] == 2:
                k = mapping.get(no)
                if k is None:
                    problems.append(f"{tag} {p['title']}: 空所 ( {no} ) が本文に無い")
                    continue
                stem = stem_cloze(k)
            else:
                stem = qq["qtext"]
            choices = [strip_choice(c) for c in qq["choices"]]
            qs.append(q(stem, choices, ans0, fmt_expl(choices, ans0, "", None) + ("\n" + etext if etext else ""), tag))
        out.append(passage(unit, p["title"], body, renum_text(ja, mapping), f"{tag} {p['title']}", qs, f"{tag}:{p['title']}"))
    return out


# ── 2級 完全模試 (PDF ×3) ───────────────────────────────────────────────
def _mock_paths(r):
    sub = {1: "第1回_修正版", 2: "第2回", 3: "第3回"}[r]
    qp = f"{E2_MOCK_DIR}/{sub}/英検2級_完全模試_第{r}回_問題冊子（リスニング除外）.pdf"
    ap = f"{E2_MOCK_DIR}/{sub}/英検2級_完全模試_第{r}回_採点・解説冊子（リスニング除外）.pdf"
    return qp, ap


_HDR_RE = re.compile(r"^(Grade 2|オリジナル模試・非公式|•\s*\d+\s*•|\d|[AB]|英検2級 完全模試.*|次の英文.*|最も適切なもの.*|選びなさい。?|各空所に.*)$")


def load_e2_zenmoshi():
    out = []
    for r in (1, 2, 3):
        qp, ap = _mock_paths(r)
        if not (os.path.exists(qp) and os.path.exists(ap)):
            problems.append(f"2級 完全模試 第{r}回 の PDF が無い: {qp}")
            continue
        tag = f"eiken2-zenmoshi-{r}"
        blocks = pdf_blocks(qp)
        qlines = pdf_lines(qp)
        # 大問2 の指示ブロックから、大問4 (ライティング) の前まで
        idx_s = next((i for i, b in enumerate(blocks) if b[3].lstrip().startswith("次の英文A、Bを読み")), None)
        if idx_s is None:
            problems.append(f"{tag}: 大問2 の指示が見つからない")
            continue
        # ★表紙の注意事項にも「英文要約」が出るので、終端は大問2 の指示より後ろで探す
        idx_e = next((i for i, b in enumerate(blocks) if i > idx_s and b[3].strip().startswith("ライティング")), len(blocks))
        passages = []
        cur = None
        part = 2
        for pno, x0, y0, txt in blocks[idx_s:idx_e]:
            t = txt.strip()
            if t.startswith("次の英文A、Bの内容に関して"):
                part = 3
                continue
            lines = [ln for ln in t.split("\n") if ln.strip()]
            if all(_HDR_RE.match(ln.strip()) for ln in lines):
                continue
            # 新しい本文の始まり (メールの見出し / 中央寄せの題名) は設問の途中でも優先して見る
            if t.startswith("From:"):
                # メールは 1 ブロックに全部入っていて段落が分からない → 行 (x0/x1/y) から段落を作る。
                # ★次のページに続くことがある (第2回は 245 語) ので、From: の行から最初の (NN) の行までをページをまたいで拾い、
                #   ページ見出し (Grade 2 / 3 / B / オリジナル模試・非公式 / • 10 •) は落とす
                si = next((i for i, ln in enumerate(qlines) if ln[0] == pno and ln[3].strip().startswith("From:")), None)
                ei = next((i for i, ln in enumerate(qlines) if si is not None and i > si and re.fullmatch(r"\(\d{2}\)", ln[3].strip())), len(qlines))
                body_lines = [ln for ln in qlines[si:ei] if not _HDR_RE.match(ln[3].strip())] if si is not None else []
                email_text = split_paras_gap(body_lines) if body_lines else t
                cur = {"title": None, "paras": [email_text], "qraw": [], "part": part, "email": True}
                sm = re.search(r"Subject:\s*(.+)", t)
                cur["title"] = f"Eメール（{sm.group(1).strip()}）" if sm else "Eメール"
                passages.append(cur)
                continue
            if len(lines) == 1 and x0 > 120 and not t.endswith((".", "?")) and len(t) < 70 and re.match(r"^[A-Za-z]", t):
                cur = {"title": t, "paras": [], "qraw": [], "part": part, "email": False}
                passages.append(cur)
                continue
            # 設問ブロック: (NN) で始まる / 1 で始まる (選択肢だけ) / 設問文のみ (以降その本文の設問が終わるまで続く)
            if cur is not None and (re.match(r"^\(\d{2}\)", t) or re.fullmatch(r"1\n[\s\S]*", t) or cur.get("in_q")):
                cur["in_q"] = True
                if re.search(r"[A-Za-z]", t) or not re.search(r"[^\x00-\x7F]", t):   # 「リーディングテストはこれで終わりです…」のような日本語だけの案内は設問ではない ((24) だけの行は設問)
                    cur["qraw"].append(t)
                continue
            if cur is not None and not cur.get("email"):   # メールは行から作った本文が全部 (2 ページ目の続きも) 入っている
                cur["paras"].append(" ".join(norm_space(x) for x in lines))
        # 設問の切り出し
        for p in passages:
            raw = "\n".join(p["qraw"])
            p["questions"] = []
            for m in re.finditer(r"\((\d{2})\)\n([\s\S]*?)(?=\n\(\d{2}\)\n|\Z)", raw):
                no = int(m.group(1)); rest = m.group(2)
                parts = re.split(r"(?m)^([1-4])\n", rest)
                qtext = norm_space(parts[0])
                choices = []
                for ci in range(1, len(parts) - 1, 2):
                    choices.append(norm_space(parts[ci + 1].replace("\n", " ")))
                p["questions"].append({"no": no, "qtext": qtext, "choices": choices})
        # 採点・解説冊子: 全文和訳 と 設問解説
        atext = pdf_text(ap)
        atext = re.sub(r"(?m)^(英検2級 完全模試 第\d回　採点・解説冊子|オリジナル模試・非公式|\d{1,2})\s*$\n?", "", atext)
        i2 = atext.find("大問2 長文の語句空所補充")
        i4 = re.search(r"大問4|ライティング", atext[i2:]) if i2 >= 0 else None
        seg = atext[i2:(i2 + i4.start()) if i4 else len(atext)] if i2 >= 0 else ""
        zens = []
        alines = [ln for ln in pdf_lines(ap)
                  if not re.fullmatch(r"(英検2級 完全模試 第\d回　採点・解説冊子|オリジナル模試・非公式|\d{1,2})", ln[3].strip())]
        _zi = None
        for i, ln in enumerate(alines):
            if ln[3].strip() == "全文和訳":
                _zi = i + 1
            elif ln[3].strip() == "設問解説" and _zi is not None:
                zens.append(split_paras_gap(alines[_zi:i], ja=True))
                _zi = None
        expl = {}
        for m in re.finditer(r"\((\d{2})\)\s*正答\s*(\d)\n([\s\S]*?)(?=\n\(\d{2}\)\s*正答|\n全文和訳|\n大問3|\n[A-Z][^\n]{3,60}\n[A-Z]|\Z)", seg):
            no = int(m.group(1)); ans1 = int(m.group(2))
            body = m.group(3).strip().split("\n")
            expl[no] = (ans1 - 1, body)
        if len(zens) != len(passages):
            problems.append(f"{tag}: 本文 {len(passages)} 本に対し 全文和訳 {len(zens)} 本")
        for pi, p in enumerate(passages):
            unit = U_2_CLOZE if p["part"] == 2 else U_2_READ
            body_raw = "\n\n".join(p["paras"])
            body, mapping = renumber_markers(body_raw)
            ja = zens[pi] if pi < len(zens) else ""
            qs = []
            for qq in p["questions"]:
                no = qq["no"]
                if len(qq["choices"]) != 4:
                    problems.append(f"{tag} 問{no}: 選択肢 {len(qq['choices'])} 個")
                    continue
                if no not in expl:
                    problems.append(f"{tag} 問{no}: 解説が見つからない")
                    continue
                ans0, elines = expl[no]
                # 解説の 1 行目 (空所補充: 正解の文 / 内容一致: 設問文 → 正解の文) を落として日本語だけ残す
                jp = [ln for ln in elines if re.search(r"[^\x00-\x7F]", ln)]
                etext = strip_seito(tidy_ja("\n".join(jp)), ans0, f"{tag} 問{no}")
                if p["part"] == 2:
                    k = mapping.get(no)
                    if k is None:
                        problems.append(f"{tag} {p['title']}: 空所 ( {no} ) が本文に無い")
                        continue
                    stem = stem_cloze(k)
                else:
                    stem = qq["qtext"]
                qs.append(q(stem, qq["choices"], ans0, fmt_expl(qq["choices"], ans0, renum_text(etext, mapping)), tag))
            out.append(passage(unit, p["title"], body, renum_text(ja, mapping), f"{tag} {p['title']}", qs, f"{tag}:{p['part']}-{pi + 1}"))
    return out



# ── 2級 オリジナル模試 第1弾 (Markdown・2026-06) ──────────────────────
JUNE_SUBJECT_JA = {"My summer visit": "夏の滞在について"}
def load_e2_mock_june():
    out = []
    tag = "eiken2-mock-2026-06"
    qf = f"{E2_MOCK_JUNE_DIR}/2級_模試第1弾_問題.md"
    af = f"{E2_MOCK_JUNE_DIR}/2級_模試第1弾_解答スクリプト.md"
    kf = f"{E2_MOCK_JUNE_DIR}/2級_模試第1弾_詳細解説.md"
    if not (os.path.exists(qf) and os.path.exists(af) and os.path.exists(kf)):
        problems.append(f"2級 模試第1弾 の md が無い: {E2_MOCK_JUNE_DIR}")
        return out
    qt = open(qf, encoding="utf-8").read()
    at = open(af, encoding="utf-8").read()
    kt = open(kf, encoding="utf-8").read()
    key = {int(m.group(1)): int(m.group(2)) - 1 for m in re.finditer(r"\*\*\((\d{2})\)\*\*\s*([1-4])", at)}
    # 問題: 大問2 と 大問3 の節
    sec2 = re.search(r"### 大問2[\s\S]*?(?=### 大問3)", qt).group(0)
    sec3 = re.search(r"### 大問3[\s\S]*?(?=### 大問4)", qt).group(0)
    # 解説: 全訳 (### [A] … の直後の **全訳** 〜 次の ####) と 設問解説 (#### (NN) 正解 N …)
    k2 = re.search(r"## 大問2[\s\S]*?(?=## 大問3)", kt).group(0)
    k3 = re.search(r"## 大問3[\s\S]*?(?=## 大問4)", kt).group(0)

    def zenyaku_map(ksec):
        m = {}
        for pm in re.finditer(r"### \[([AB])\][^\n]*\n([\s\S]*?)(?=\n### \[|\Z)", ksec):
            z = re.search(r"\*\*全訳\*\*\s*\n([\s\S]*?)(?=\n#### )", pm.group(2))
            if z:
                paras = [norm_space(x) for x in re.split(r"\n\s*\n", z.group(1).strip()) if norm_space(x)]
                m[pm.group(1)] = "\n\n".join(paras)
        return m

    def expl_map(ksec):
        m = {}
        for em in re.finditer(r"#### \((\d{2})\) 正解 ([1-4])[^\n]*\n([\s\S]*?)(?=\n#### |\n### |\Z)", ksec):
            no = int(em.group(1)); ans0 = int(em.group(2)) - 1; body = em.group(3)
            konkyo = re.search(r"\*\*根拠\*\*\s*(.*)", body)
            kaisetsu = re.search(r"\*\*解説\*\*\s*(.*)", body)
            wrongs = {}
            for wm in re.finditer(r"-\s*\*\*([1-4])\*\*\s*(.*)", body):
                wrongs[int(wm.group(1)) - 1] = norm_space(wm.group(2))
            ktext = norm_space(kaisetsu.group(1)) if kaisetsu else ""
            # ★この解説は選択肢の番号が本文の並びと合っていない箇所がある (書いた後に並べ替えたらしい) → 番号だけ落とす
            ktext = re.sub(r"正解は[1-4]「", "正解は「", ktext)
            ktext = re.sub(r"選択肢[1-4]の", "", ktext)
            ktext = re.sub(r"選択肢[1-4]が", "", ktext)
            m[no] = (ans0, ktext, norm_space(konkyo.group(1)).replace("*", "") if konkyo else "", wrongs)
        return m

    z2, z3 = zenyaku_map(k2), zenyaku_map(k3)
    e2, e3 = expl_map(k2), expl_map(k3)

    def build(sec, unit, zmap, emap, part):
        res = []
        for pm in re.finditer(r"#### \[([AB])\]\s*([^\n]*)\n([\s\S]*?)(?=\n#### \[|\Z)", sec):
            letter, title, body = pm.group(1), pm.group(2).strip(), pm.group(3)
            # 本文 = 最初の **(NN)** より前
            qpos = re.search(r"\*\*\((\d{2})\)\*\*", body)
            text = body[:qpos.start()] if qpos else body
            qtxt = body[qpos.start():] if qpos else ""
            paras = []
            email = False
            if "```" in text:
                email = True
                hm = re.search(r"```\n([\s\S]*?)```", text)
                header = "\n".join(norm_space(x) for x in hm.group(1).strip().split("\n"))
                # 宛先・送信者の架空アドレスは本文に出さない (公開リポジトリ・PII ゲート)
                header = re.sub(r"\s*<[^>]+@[^>]+>", "", header)
                paras.append(header)
                text = text[hm.end():]
                sm = re.search(r"Subject:\s*(.+)", header)
                title = f"Eメール（{sm.group(1).strip()}）" if sm else "Eメール"
            for x in re.split(r"\n\s*\n", text.strip()):
                if norm_space(x):
                    paras.append(norm_space(x))
            body_raw = "\n\n".join(paras)
            body_t, mapping = renumber_markers(body_raw)
            qs = []
            if part == 2:
                for qm in re.finditer(r"\*\*\((\d{2})\)\*\*\s*\n\s*\n(.*)", qtxt):
                    no = int(qm.group(1))
                    choices = [norm_space(c) for c in re.findall(r"\*\*[1-4]\*\*\s*(.*?)(?=\s*\*\*[1-4]\*\*|$)", qm.group(2))]
                    k = mapping.get(no)
                    if k is None or len(choices) != 4 or no not in key:
                        problems.append(f"{tag} 問{no}: 空所/選択肢/正解が取れない (k={k}, choices={len(choices)})")
                        continue
                    ans0, ktext, konkyo, wrongs = emap.get(no, (key[no], "", "", {}))
                    if ans0 != key[no]:
                        problems.append(f"{tag} 問{no}: 解答 {key[no] + 1} と解説 {ans0 + 1} が食い違う")
                    qs.append(q(stem_cloze(k), choices, key[no], fmt_expl(choices, key[no], renum_text(ktext, mapping), wrongs, evidence=konkyo or None), tag))
            else:
                for qm in re.finditer(r"\*\*\((\d{2})\)\*\*\s*(.+)\n\s*\n((?:\d\.\s.*\n?)+)", qtxt):
                    no = int(qm.group(1)); qtext = norm_space(qm.group(2))
                    choices = [norm_space(c) for c in re.findall(r"^\d\.\s*(.*)$", qm.group(3), re.M)]
                    if len(choices) != 4 or no not in key:
                        problems.append(f"{tag} 問{no}: 選択肢/正解が取れない")
                        continue
                    ans0, ktext, konkyo, wrongs = emap.get(no, (key[no], "", "", {}))
                    if ans0 != key[no]:
                        problems.append(f"{tag} 問{no}: 解答 {key[no] + 1} と解説 {ans0 + 1} が食い違う")
                    qs.append(q(qtext, choices, key[no], fmt_expl(choices, key[no], ktext, wrongs, evidence=konkyo or None), tag))
            ja = zmap.get(letter, "")
            if email and ja:
                ja = re.sub(r"\s*<[^>]+@[^>]+>", "", ja)
                # 全訳は本文から始まっているので、英文と同じ見出し 4 行 (氏名はそのまま・日付と件名は訳す) を先に付ける
                hdr = paras[0].split("\n")
                hj = []
                for hl in hdr:
                    hm = re.match(r"^(From|To|Date|Subject):\s*(.*)$", hl)
                    if not hm:
                        continue
                    key_, val = hm.group(1), hm.group(2).strip()
                    if key_ == "Date":
                        dm = re.match(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})$", val)
                        if dm:
                            val = f"{['January','February','March','April','May','June','July','August','September','October','November','December'].index(dm.group(1)) + 1}月{dm.group(2)}日"
                    if key_ == "Subject":
                        val = JUNE_SUBJECT_JA.get(val, val)
                    hj.append({"From": "送信者", "To": "宛先", "Date": "日付", "Subject": "件名"}[key_] + "：" + val)
                if hj and not ja.startswith("送信者"):
                    ja = "\n".join(hj) + "\n\n" + ja
            res.append(passage(unit, title, body_t, renum_text(ja, mapping), f"{tag} 大問{part}[{letter}]", qs, f"{tag}:{part}-{letter}"))
        return res

    out += build(sec2, U_2_CLOZE, z2, e2, 2)
    out += build(sec3, U_2_READ, z3, e3, 3)
    return out


# ── 検査・出力 ────────────────────────────────────────────────────────
def validate(passages):
    seen = set()
    for p in passages:
        pid = p["pid"]
        if p["unit"] not in UNITS:
            problems.append(f"{pid}: 単元が不正 {p['unit']!r}")
        words = len(re.findall(r"[A-Za-z]+", p["body"]))
        if words < 80:
            problems.append(f"{pid}: 本文が短すぎる ({words} 語)")
        h = hashlib.sha256(re.sub(r"\s+", " ", p["body"]).lower().encode()).hexdigest()[:16]
        if h in seen:
            problems.append(f"{pid}: 本文が重複")
        seen.add(h)
        if not (2 <= len(p["questions"]) <= 6):
            problems.append(f"{pid}: 設問が {len(p['questions'])} 問")
        if "空所" in p["unit"]:
            marks = re.findall(r"\(\s*(\d{1,2})\s*\)", p["body"])
            want = [str(i) for i in range(1, len(p["questions"]) + 1)]
            if marks != want:
                problems.append(f"{pid}: 空所の並び {marks} ≠ {want}")
            for i, qq in enumerate(p["questions"], 1):
                if not qq["stem"].startswith(f"( {i} )"):
                    problems.append(f"{pid}: 設問 {i} の stem が ( {i} ) で始まらない: {qq['stem'][:30]}")
        for i, qq in enumerate(p["questions"], 1):
            if len(qq["choices"]) != 4:
                problems.append(f"{pid} 問{i}: 選択肢 {len(qq['choices'])} 個")
            if len(set(c.lower() for c in qq["choices"])) != len(qq["choices"]):
                problems.append(f"{pid} 問{i}: 選択肢が重複")
            if not (0 <= qq["answer"] < len(qq["choices"])):
                problems.append(f"{pid} 問{i}: answer {qq['answer']} が範囲外")
            if not qq["stem"]:
                problems.append(f"{pid} 問{i}: stem が空")
            if any(not c for c in qq["choices"]):
                problems.append(f"{pid} 問{i}: 空の選択肢")
            if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", qq["stem"] + " ".join(qq["choices"]) + qq["explanation"]):
                problems.append(f"{pid} 問{i}: メールアドレスが混ざっている")
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", p["body"] + (p["body_ja"] or "")):
            problems.append(f"{pid}: 本文にメールアドレスが混ざっている (公開リポジトリ・PII ゲートに掛かる)")


def drop_questions(p, qnos):
    """設問を落とす。空所補充は本文 (と全訳) の「( k )」を正解の文で埋め、残りの空所を 1 から付け直して stem も合わせる。"""
    keep = [qq for i, qq in enumerate(p["questions"], 1) if i not in qnos]
    if "空所" in p["unit"]:
        body, ja = p["body"], p["body_ja"] or ""
        for i, qq in enumerate(p["questions"], 1):
            if i in qnos:
                body = body.replace(f"( {i} )", qq["choices"][qq["answer"]])
                ja = ja.replace(f"( {i} )", "")
        body, mapping = renumber_markers(body)
        ja = renum_text(ja, mapping)
        for k, qq in enumerate(keep, 1):
            qq["stem"] = stem_cloze(k)
            qq["explanation"] = renum_text(qq["explanation"], mapping)
        p["body"], p["body_ja"] = body, (ja or None)
    p["questions"] = keep


def apply_overrides(passages):
    out = []
    for p in passages:
        if p["pid"] in DROP:
            continue
        if p["pid"] in DROP_Q:
            drop_questions(p, DROP_Q[p["pid"]])
        ov = OVERRIDES.get(p["pid"]) or {}
        for qno, ans0 in ov.items():
            if 1 <= int(qno) <= len(p["questions"]):
                qq = p["questions"][int(qno) - 1]
                qq["answer"] = int(ans0)
                qq["explanation"] = re.sub(r"^正解 [①②③④⑤⑥] .*$", f"正解 {circled(int(ans0))} {qq['choices'][int(ans0)]}", qq["explanation"], count=1, flags=re.M)
                if re.search(r"正答は?\s*\d|[①②③④]\s*が正解|選択肢\s*\d", qq["explanation"].split("\n", 1)[-1]):
                    problems.append(f"OVERRIDES {p['pid']} 問{qno}: 解説の本文に番号参照が残る (手で書き直す)")
            else:
                problems.append(f"OVERRIDES {p['pid']}: 設問 {qno} が無い")
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--blind", default=None, help="盲検用ファイルと正解表を書くディレクトリ")
    a = ap.parse_args()
    passages = []
    for fn in (load_p1_mock, load_p1_zenmoshi, load_p1_sogo, load_e2_wb1, load_e2_wb2, load_e2_zenmoshi, load_e2_mock_june):
        got = fn()
        print(f"  {fn.__name__:20s} 本文 {len(got):3d} 本 / 設問 {sum(len(p['questions']) for p in got):3d} 問")
        passages += got
    passages = apply_overrides(passages)
    validate(passages)
    by_unit = {}
    for p in passages:
        s = by_unit.setdefault(p["unit"], [0, 0])
        s[0] += 1; s[1] += len(p["questions"])
    print("\n単元別:")
    for u in UNITS:
        n, m = by_unit.get(u, [0, 0])
        print(f"  {u:14s} 本文 {n:3d} 本 / 設問 {m:3d} 問")
    # 正解位置の偏り
    dist = {}
    for p in passages:
        for qq in p["questions"]:
            dist[qq["answer"]] = dist.get(qq["answer"], 0) + 1
    print("  正解位置:", {circled(k): v for k, v in sorted(dist.items())})
    if problems:
        print(f"\n❌ 出所の不整合 {len(problems)} 件:")
        for x in problems[:80]:
            print("   -", x)
        sys.exit(1)
    if a.blind:
        os.makedirs(a.blind, exist_ok=True)
        blind = []
        keyfile = {}
        for i, p in enumerate(passages, 1):
            blind.append({"pid": f"P{i:03d}", "unit": p["unit"], "title": p["title"], "body": p["body"],
                          "questions": [{"qid": f"P{i:03d}-{j}", "stem": qq["stem"], "choices": qq["choices"]}
                                        for j, qq in enumerate(p["questions"], 1)]})
            keyfile[f"P{i:03d}"] = {"src": p["pid"], "answers": [qq["answer"] for qq in p["questions"]]}
        json.dump(blind, open(os.path.join(a.blind, "blind_reading.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(keyfile, open(os.path.join(a.blind, "key_reading.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n盲検用: {a.blind}/blind_reading.json ({len(blind)} 本) と key_reading.json")
    out = {"subject": "eiken", "version": "v1", "generated": date.today().isoformat(),
           "note": "英検 長文ドリル (大問2 長文空所補充 / 大問3 内容一致)。全部この塾の書き下ろし。空所は ( 1 ) ( 2 ) … に正規化済み。",
           "units": {u: {"passages": by_unit.get(u, [0, 0])[0], "questions": by_unit.get(u, [0, 0])[1]} for u in UNITS},
           "passages": [{k: v for k, v in p.items() if k != "pid"} for p in passages]}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n✅ {a.out}: 本文 {len(passages)} 本 / 設問 {sum(len(p['questions']) for p in passages)} 問")


if __name__ == "__main__":
    main()
