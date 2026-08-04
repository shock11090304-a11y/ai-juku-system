#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生徒の個人情報と秘密が **git に入る前に** 止めるゲート。

    python3 scripts/check_no_pii.py           # コミット対象になりうる全ファイル
    python3 scripts/check_no_pii.py --staged  # ステージ済みの **index の中身** だけ
    python3 scripts/check_no_pii.py <path>…   # そのファイルだけ（単発確認・負のテスト用）

★このリポジトリは **PUBLIC**（github.com/shock11090304-a11y/ai-juku-system）。
  氏名を1行書いてコミットすると、その瞬間に世界中から読める。しかも**履歴に永久に残る**ので、
  消すにはリポジトリ全体の履歴書き換えが要る。「あとで直す」が効かない種類の事故。

  2026-08-04 に実際に起きかけた: 教材ビルダー3本に `STUDENT = "<実在の生徒の氏名>"` が
  直書きされ、塾長用の指導メモ（氏名がファイル名にも入っている）と一緒に未追跡で置かれていた。
  「未追跡のスクリプトをまとめてコミットする」作業で危うく一緒に入るところだった
  （中身の走査だけしてファイル名を見落としかけた）。

■ 何を見るか（誤検出で使われなくなるより、**確実に危ないものだけ**を確実に止める）
  1. 宛名の直書き    STUDENT = "日本語の氏名" → 環境変数 STUDENT_NAME で渡すこと
                     ★コメント行・dict/list の値・`STUDENT_NAME="実名" python3 …` の
                       貼り付けも見る（手順書どおりに使うほど漏れる形なので）
  2. --name の実名   使用例に実名を書いたもの
  3. 連絡先          メールアドレス / 電話番号（全角・区切りなしも）
  4. 個人あて資料    指導メモ・面談・成績表・答案 … が **パスのどこか**にある
  5. 秘密のベタ書き  各種 API キー / DSN

  ★日本語の氏名そのものを一般に検出しようとすると誤検出だらけで使われなくなる。
    「宛名として使われている場所」に絞って確実に止める。

■ 「検査したつもり」を作らないための約束
  - **読めなかったファイルを黙って飛ばさない**。utf-8 で駄目なら cp932/utf-16 を試し、
    それでも駄目なら「未走査」として必ず一覧に出す（Excel 由来の名簿は cp932 が普通）。
  - **走査数が0なら失敗**。git 管理外で回すと ls-files が空を返し「ALL PASS」と出てしまう。
  - **パスは -z で受け取る**。`git ls-files` は既定で非ASCIIパスを "\346\214..." と
    octal quote するので、そのまま open すると**日本語ファイル名だけが黙って消える**
    （＝今回の事故そのものが素通りする）。
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 中身を見ないもの（バイナリ・生成物）。★「意図的に飛ばした」と「読めなかった」を区別するため、
#   ここに書いていないバイナリは「未走査」として一覧に出る。
# ★.svg は入れない。SVG はテキストで、このリポジトリは図版 (question_data.figure_svg)・
#   IG 素材・成績表を SVG で生成する。中身に氏名や連絡先が載りうる。
SKIP_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov",
            ".woff", ".woff2", ".ttf", ".otf", ".ico", ".zip", ".gz", ".db", ".sqlite3",
            ".pyc", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".numbers", ".pages"}

# 教材の例文に出てよい一般名・プレースホルダ
PLACEHOLDER = {"生徒名", "氏名", "姓 名", "姓名", "山田太郎", "山田 太郎", "太郎", "花子",
               "名前", "受験生", "生徒", "サンプル", "テスト", "例", "各自",
               # 人ではない語（プラン名・役職・一般的な宛名）
               "塾長", "保護者各位", "保護者", "塾生アドオン", "スタンダード", "プレミアム"}

# 連絡先の「これは個人情報ではない」除外。
# ★ここを緩めないと example.com やプレースホルダで 190 件超の誤検出になり、
#   ゲートが読まれなくなる。**誤検出で使われなくなるのが一番あぶない**ので、
#   「確実に危ないものだけを確実に止める」側に振る。
CONTACT_OK = re.compile(
    r"@(?:example\.(?:com|jp|net|org)"          # ドキュメント用の予約ドメイン
    r"|trillion-ai-juku\.com"                   # 自社の公開連絡先（LPに載せている）
    r"|(?:email|company|mail)\.com"             # 英語長文の教材本文に出る架空アドレス
    r"|test\.|localhost)"
    r"|^(?:noreply|no-reply|info|support|sample|test|your|dummy)@",
    re.I)
# 連番・ゾロ目のダミー電話（090-1234-5678 / 03-0000-0000 など）
PHONE_OK = re.compile(r"[-\s]?(?:1234[-\s]?5678|0000[-\s]?0000|1111[-\s]?1111"
                      r"|9999[-\s]?9999|xxxx[-\s]?xxxx)$", re.I)
# ★`here` を裸で置くと "Adherence" のような普通の語に当たって**本物の鍵を消す**。語として限定する。
SECRET_OK = re.compile(r"your[-_]?key|key[-_]?here|xxxx+|placeholder|example|dummy|<[^>]+>", re.I)

JP = r"[ぁ-んァ-ヶー々一-龥]"

# 敬称の前に来ても人名ではない語。「保護者様専用」「お客様専用」を氏名扱いしないため。
# ★これを入れないと、LP の普通の文言（student-upgrade.html / support.html / style.css /
#   server/main.py）が個人あての記述として落ちる（実測6件）。
# ★正規表現の lookahead だけで除こうとすると **開始位置を1文字ずらして回避される**
#   （「保護者様専用」→「護者様専用」、「はお客様専用」）。日本語には語境界が無いので、
#   マッチした文字列に一般語が含まれるかを**後から**見るのが確実。
# ★判定は **endswith**（敬称の直前の語）で行う。`in`（含むか）にすると `皆川さん` の「皆」で
#   **実在の姓を握りつぶす**（PUBLIC リポジトリで氏名が素通りする）。endswith なら
#   "皆川".endswith("皆") は False なので安全に「皆様」を除外できる。
GENERIC_WORDS = ("保護者", "塾生", "会員", "生徒", "受験生", "お客", "お子", "父兄",
                 "ご家族", "関係者", "各位", "新入生", "在校生", "受講生", "利用者",
                 "皆", "みな", "みんな", "全員")
# 「氏名らしき塊 + 敬称 + その人あての資料を示す語」。
# ★「課題」「メモ」を単独で拾うと `夏休み課題プリント.md` `設計メモ.md` が落ちる（実測6/6誤検出）。
# ★氏名部分を名前つきグループで取り出す。判定は「**敬称の直前の語**が一般語か」で行う。
#   `in`（含むか）だと 皆川さん の「皆」で実在の姓を握りつぶし、`startswith`（先頭か）だと
#   「機能を生徒様専用」のように前置きが付いた途端に外れる。どちらも実測で踏んだ。
ADDRESSEE = (r"(?P<nm>[ぁ-んァ-ヶー々一-龥]{2,5})\s*(?:さん|くん|ちゃん|様)\s*"
             r"(?:の|用|向け)?\s*[_\-]?\s*"
             r"(?:専用|進捗|課題|メモ|記録|カルテ|面談|プリント|レポート|指導)")


def _is_generic_addressee(m):
    """マッチが「人名あて」ではなく一般的な呼びかけか（保護者様専用・生徒様専用…）。"""
    nm = m.groupdict().get("nm") or ""
    return any(nm.endswith(w) for w in GENERIC_WORDS)

# 宛名として使われる識別子。
# ★`name` や `who` まで広げると、プラン名 (`name: "スタンダード"`) や画面のサンプル表示
#   (`alerts.js` のダミー生徒) まで拾って **891 件** の誤検出になった（実測）。
#   誤検出で読まれなくなるゲートは無いのと同じなので、`student` / `宛名` 系に絞る。
#   これで今回の事故 (`STUDENT = "<氏名>"` と `STUDENT_NAME="<氏名>" python3 …`) は確実に捕まる。
# ★`名前` `宛先` `student_*` を丸ごと入れると、教材の実データに当たる:
#   古文の活用表 `{"名前": "けり"}`、英語長文の本文 `宛先: <架空の人物>`、
#   `student_grade = "高3"` `studentPlan = "塾生プラン"` … いずれも宛名ではない（実測9件）。
#   宛名として使う識別子だけに絞る。
NAMEISH = (r"(?:STUDENTS?|STUDENT_NAME|PUPIL|宛名|受講生|氏名|生徒名"
           r"|[Ss]tudents?(?:[_-]?(?:[Nn]ames?|[Ll]ist))?)")

RULES = [
    # 1. 宛名の直書き。★行頭アンカーを付けない: コメント行・dict の値・引数にも同じ形で出る。
    #    `# STUDENT_NAME="姓 名" python3 build.py` の姓名を実名に置き換えて貼るのが
    #    最も現実的な漏洩経路（手順書どおりに使うほど漏れる）。
    ("宛名の直書き",
     # ★`[^"']*` は改行も食う。文字列の閉じ忘れがあると何十行もまたいでマッチするので
     #   改行を除外する（実測でソースコードの塊が1件の「氏名」として報告された）。
     # ★キー側のクォート（JSON の "studentName": "…"）と、代入先が list/dict/関数呼び出しの
     #   形（STUDENTS = ["…", …]）も拾う。複数の生徒を刷るビルダーはまさにこの形で、
     #   これを見ていなかったため api/past-due-invoice.py の実物を取りこぼしていた。
     re.compile(r"""["']?%s["']?\s*[=:]\s*[\[\{\(\s]*["']([^"'\n]*%s[^"'\n]*)["']"""
                % (NAMEISH, JP)),
     "環境変数から読むこと: STUDENT = os.environ.get('STUDENT_NAME', '')"),
    # 1b. list の2個目以降（["桜井 陽菜", "新垣 蒼真"] の2人目）。1 は先頭しか拾えない。
    ("宛名の一覧",
     re.compile(r"""%s\s*[=:]\s*\[([^\]\n]*%s[^\]\n]*)\]""" % (NAMEISH, JP)),
     "生徒の一覧をコードに書かない（DB / 環境変数から取ること）"),
    # 2. 使用例に実名（--name のあと。クォート有無どちらも）
    ("使用例に実名",
     re.compile(r"""--name[= ]+["']?((?:%s)+(?:\s+(?:%s)+)?)["']?""" % (JP, JP)),
     'プレースホルダにすること: --name "生徒名"'),
    # 2b. 本文に書かれた「◯◯さん専用」「◯◯さんの指導記録」。
    #     ★`.gitignore` に「教材/<氏名>さん専用.pdf」と書く、面談メモの本文に見出しを書く、
    #       といった経路は識別子を伴わないので上のルールでは拾えない。
    #       敬称＋資料語の並びに限れば教材本文で誤爆しない（単独の「面談」「課題」は拾わない）。
    ("宛名つきの記述",
     re.compile("(%s)" % ADDRESSEE),
     "個人あての記述はリポジトリに置かない"),
    # 3. 連絡先
    ("メールアドレス",
     re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|jp|net|org|co\.jp|ne\.jp|ac\.jp)"),
     "連絡先はリポジトリに置かない"),
    ("電話番号",
     # ★区切りなしの数字列まで拾うと、小数 (0.571428571) や連番 (0123456789)、
     #   計算結果が全部「電話番号」になる（実測13件すべて誤検出）。区切りを必須にする。
     #   区切りなしで拾うのは日本の携帯の形 (0[789]0 + 8桁) だけに限る。
     #   全角と括弧区切りも見る（フォームから貼るとこの形になる）。
     re.compile(r"(?<![0-9.０-９])(?:(?:\+81[-\s]?)?[0０][\d０-９]{1,3}[-－ー\s()（）]"
                r"[\d０-９]{2,4}[-－ー\s()（）][\d０-９]{4}"
                r"|[0０][789７８９][0０][\d０-９]{8})(?![0-9.０-９])"),
     "連絡先はリポジトリに置かない"),
    # 5. 秘密のベタ書き。★このアプリが実際に使う鍵をひととおり並べる。
    ("秘密のベタ書き",
     re.compile(r"(?:sk-ant-[A-Za-z0-9_-]{10,}|sk-proj-[A-Za-z0-9_-]{10,}"
                r"|sk_(?:live|test)_[A-Za-z0-9]{10,}|pk_(?:live|test)_[A-Za-z0-9]{10,}"
                r"|rk_live_[A-Za-z0-9]{10,}|whsec_[A-Za-z0-9]{10,}"
                # ★Resend の実キーは re_<公開ID>_<秘密> の2段。下線を丸ごと禁じると
                #   **本物が1つもマッチしない**。逆に下線を無制限に許すと Python の変数名
                #   (re_study_log_course) を拾う。2段構造＋各段の長さで区別する。
                r"|re_[A-Za-z0-9]{6,}_[A-Za-z0-9]{16,}"
                r"|AIza[0-9A-Za-z_-]{30,}|SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}"
                r"|xox[baprs]-[A-Za-z0-9-]{10,}"
                r"|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}"
                r"|(?:postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?)://[^\s\"']*:[^\s\"'@]+@)"),
     "環境変数から読むこと"),
]

# 4. 個人あて資料。★basename ではなく**パス全体**に当てる（親ディレクトリが個人あての形もある）。
#    ★このリポジトリの scripts/ 配下は **全部ローマ字命名**（chugaku_dojo, kobun_jodoushi …）。
#      日本語の語だけ見ていると、規約どおりに置いた scripts/karte/ や roster.csv を素通りする。
BAD_NAME = re.compile(
    r"指導メモ|指導記録|面談|カルテ|名簿|保護者連絡|成績表|答案|個人票|進路相談"
    r"|連絡先一覧|住所録|生徒一覧|出席簿|連絡網"
    r"|karte|shidou[-_]?memo|mendan|roster|meibo|seiseki|kojin[-_]?hyou"
    r"|student[-_]?list|parent[-_]?contact", re.I)

# 氏名が **ファイル名そのもの** に入っている形。
# ★「課題」「メモ」「専用」「進捗」を単独で拾うと、`夏休み課題プリント.md`
#   `設計メモ.md` `印刷専用.css` `学習進捗ダッシュボード.html` が全部落ちる（実測6/6が誤検出）。
#   `君`『様』も `専制君主` `図形の模様` のように語の一部に出る。
#   → **敬称（さん/くん/様）と、その人あての資料を示す語が並ぶとき**だけにする。
#     「桜井さん専用」は当たり、「夏休み課題」は当たらない。
BAD_NAME_JP = re.compile(ADDRESSEE)

# 例外。★_pii_baseline.txt は「許可した値そのもの」を並べたファイルなので、走査すると
#   自分自身を違反として検出して必ず落ちる。除外してよいのはこのゲート自身と baseline だけ。
#   （.gitignore や CLAUDE.md は「この個人ファイルを無視する」と氏名を書きやすい実在の経路なので
#     除外しない。誤検出が出たら baseline に個別登録する。）
#   _print_font_cmap.txt は 16進のコードポイント範囲だけの機械生成ファイル。
#   `0570-05F4` のような行が電話番号の形に見えるが、個人情報は入りようがない。
ALLOW_FILES = {"scripts/check_no_pii.py", "scripts/_pii_baseline.txt",
               "scripts/kaki_koushuu_eng/_print_font_cmap.txt"}

# ベースラインで黙らせてはいけない種別。
# ★「宛名の直書き」はここに入れたいところだが、既存コードに画面表示用の架空サンプル
#   （「佐藤 花子 (中3)」等）が実在するため入れられない。代わりに --write-baseline のとき
#   **必ず全件を表示して --yes を要求**し、この種別が混ざるときは強い警告を出す。
# ★氏名系は `--yes` でも **拒否**する。警告を出すだけでは止まらないので、
#   ゲート自身が氏名を _pii_baseline.txt（追跡ファイル）に書いて公開する運び手になる。
#   通したいなら中身を直すこと。既存の架空サンプル2件は登録済みなので運用は詰まらない。
NEVER_BASELINE = {"使用例に実名", "個人あて資料のパス", "宛名の直書き", "宛名の一覧"}
# 目視確認を強く促す種別（baseline には入れられるが、必ず全件表示して警告する）。
# ★連絡先は教材本文の架空アドレスが新しい seed のたびに増えるので拒否まではしない。
NEEDS_EYES = {"メールアドレス", "電話番号"}

BASELINE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_pii_baseline.txt")


def load_baseline():
    if not os.path.exists(BASELINE_FILE):
        return set()
    with open(BASELINE_FILE, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def key(rel, label, found):
    return f"{rel}|{label}|{found}"


def git_paths(args):
    """git のパス一覧を **-z** で受け取る。

    ★`-z` を付けないと非ASCIIパスが "\\346\\214..." と octal quote されて返り、
      そのまま open すると**日本語ファイル名だけが黙って消える**。今回の事故ファイルは
      まさに日本語名だったので、ここを間違えると事故そのものを素通りさせる。
    """
    out = subprocess.run(["git"] + args + ["-z"], cwd=ROOT, capture_output=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def targets(staged, paths=None):
    """(パス, index から読むか) の一覧を返す。"""
    if paths:
        return [(p, False) for p in paths]        # 明示指定（負のテスト用・単発確認用）
    if staged:
        # ★index の中身を読む。作業ツリーを読むと「氏名入りを add したあと作業ツリーだけ直して
        #   add し忘れた」ときに、コミットされる中身と検査する中身がずれる。
        #   R(rename) も含める。個人あて名にリネームしただけの変更を取りこぼさないため。
        return [(p, True) for p in
                git_paths(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])]
    # コミット対象になりうるもの＝追跡済み + 未追跡（.gitignore で除外されないもの）
    both = set(git_paths(["ls-files"])) | set(git_paths(["ls-files", "-o", "--exclude-standard"]))
    return [(p, False) for p in sorted(both)]


def read_source(rel, from_index):
    """(テキスト, 未走査の理由) を返す。読めなければテキストは None。"""
    if from_index:
        r = subprocess.run(["git", "show", f":{rel}"], cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            return None, "index から読めない"
        raw = r.stdout
    else:
        path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            return None, "ファイルが見つからない"
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as e:
            return None, f"開けない ({e.__class__.__name__})"
    # ★UTF-16 は NUL バイトを含むので、NUL でバイナリ判定すると **utf-16 の分岐に到達しない**。
    #   Excel の「Unicode テキスト」書き出しは UTF-16 なので、名簿がまるごと素通りしていた。
    #   BOM を先に見る。
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        try:
            return raw.decode("utf-16"), None
        except UnicodeError:
            return None, "UTF-16 として読めない"
    if b"\0" in raw[:8192]:
        return None, "バイナリ"
    # ★utf-8 で駄目でも諦めない。日本語のCSVはExcel由来で cp932 が普通。
    for enc in ("utf-8", "cp932"):
        try:
            return raw.decode(enc), None
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None, "文字コードを判別できない"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="このファイルだけを見る（省略時は全体）")
    ap.add_argument("--staged", action="store_true", help="ステージ済みの index を見る")
    ap.add_argument("--write-baseline", action="store_true",
                    help="今の検出を既知として **追記** する（★中身を目で確認してから）")
    ap.add_argument("--yes", action="store_true", help="--write-baseline を確認なしで実行")
    a = ap.parse_args()

    baseline = load_baseline()
    files = targets(a.staged, a.paths)
    if not files and not a.staged:
        # ★対象0件で「ALL PASS」と出すのが一番あぶない (git 管理外で回すと ls-files が空を返す)。
        #   --staged だけは「差分なし」で正当に0件になりうるので許す。
        print("✗ 走査対象が0件。git リポジトリの中で回すこと（検査していないのに通ってしまう）")
        return 1

    hits, known, unread = [], [], []
    n = n_binary = n_allow = 0
    for rel, from_index in files:
        # ★ファイル名の検査は「中身が読めるか」より **先**。読めないファイル
        #   （日本語名・バイナリ・存在しない）でも名前は必ず見る。
        m_jp = BAD_NAME_JP.search(rel)
        if m_jp and _is_generic_addressee(m_jp):
            m_jp = None
        if BAD_NAME.search(rel) or m_jp:
            hits.append((rel, 0, "個人あて資料のパス", os.path.basename(rel),
                         "リポジトリの外に出すこと（.gitignore は公開を防ぐが検査からも消える）"))

        if os.path.splitext(rel)[1].lower() in SKIP_EXT:
            n_binary += 1          # 意図的に飛ばした分。件数は必ず出す（沈黙させない）
            continue
        if rel in ALLOW_FILES:
            n_allow += 1
            continue
        src, why = read_source(rel, from_index)
        if src is None:
            unread.append((rel, why))
            continue
        n += 1
        for label, pat, fix in RULES:
            for m in pat.finditer(src):
                found = (m.group(1) if m.groups() else m.group(0)).strip()
                # 「山田 太郎 (高2)」のような付随を剥がしてから一般語かどうかを見る
                core = re.sub(r"[(（].*?[)）]", "", found).strip().strip("\"' ")
                if found in PLACEHOLDER or core in PLACEHOLDER:
                    continue
                if label == "宛名つきの記述" and _is_generic_addressee(m):
                    continue        # 「保護者様専用」「生徒様専用」等は人名ではない
                if label == "メールアドレス" and CONTACT_OK.search(found):
                    continue
                if label == "電話番号" and PHONE_OK.search(found):
                    continue
                if label == "秘密のベタ書き" and SECRET_OK.search(found):
                    continue
                line = src[:m.start()].count("\n") + 1
                found = found[:60]
                # ★NEVER_BASELINE は「**新しく**baseline に足させない」種別であって、
                #   既に目視確認して登録済みのものまで無効にする意味ではない。
                #   ここで除外すると既存の架空サンプルで CI が常に赤になり、
                #   「うるさいゲート」として読まれなくなる（＝検査が無いのと同じ）。
                (known if key(rel, label, found) in baseline else hits).append(
                    (rel, line, label, found, fix))

    if a.write_baseline:
        blocked = [h for h in hits if h[2] in NEVER_BASELINE]
        if blocked:
            # ★生徒の個人情報を baseline で黙らせる経路を塞ぐ。ゲートが漏洩の運び手になる。
            print(f"✗ ベースラインに入れられない種別が {len(blocked)} 件ある。中身を直すこと:")
            for rel, line, label, found, _ in blocked:
                print(f"    {rel}:{line} [{label}] {found}")
            return 1
        add = sorted({key(r, la, fo) for r, _, la, fo, _ in hits} - baseline)
        if not add:
            print("ベースラインに追加するものは無い")
            return 0
        print(f"次の {len(add)} 件を既知として **追記** する:")
        for row in add:
            print(f"    {row}")
        eyes = [h for h in hits if h[2] in NEEDS_EYES and key(h[0], h[2], h[3]) in add]
        if eyes:
            print(f"\n★★ 連絡先が {len(eyes)} 件ある。**実在の生徒・保護者のものでないことを"
                  f"1件ずつ目で確かめる**こと。"
                  f"\n   ここで通すと PUBLIC リポジトリに永久に残り、消すには履歴の書き換えが要る。")
        if not a.yes:
            print("\n★中身を目で確認し、生徒の個人情報でないことを確かめてから --yes を付けて実行する")
            return 1
        with open(BASELINE_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(add) + "\n")
        print(f"{BASELINE_FILE} に追記した（既存行は消していない）")
        return 0

    print(f"個人情報ゲート: {n} ファイルを走査"
          + (f"（バイナリとして中身を飛ばした {n_binary} 件。名前は検査済み）" if n_binary else ""))
    if known:
        # ★黙殺しない。既知だから安全なのではなく、「確認済みだから今は落とさない」だけ。
        print(f"  既知 {len(known)} 件（_pii_baseline.txt。事業者自身の連絡先・取引先・テスト値）")
    if unread:
        # ★読めなかったものを黙って飛ばすと「検査したつもり」になる。必ず出す。
        print(f"\n--- 中身を走査できなかった {len(unread)} 件（名前だけ検査済み）---")
        for rel, why in unread[:20]:
            print(f"  ? {rel}  … {why}")

    if n == 0 and files and n_binary + n_allow < len(files):
        print("✗ 対象はあるのに1ファイルも走査できていない（検査していないのに通ってしまう）")
        return 1
    if not hits:
        print("=== ALL PASS（生徒の個人情報・秘密の新規混入なし）===")
        return 0

    print(f"\n=== 違反 {len(hits)} 件 ===")
    print("★このリポジトリは PUBLIC。コミットすると公開され、履歴に永久に残る。\n")
    for rel, line, label, found, fix in hits:
        where = f"{rel}:{line}" if line else rel
        print(f"  ✗ {where}")
        print(f"      [{label}] {found}")
        print(f"      → {fix}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
