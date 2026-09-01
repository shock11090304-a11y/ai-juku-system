#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗓 時間割クラスの写しが 5 ファイルで食い違っていないかを検査する (run_all_gates.py が拾う)。

    python3 scripts/class_timetable/check_timetable_sync.py

正典は server/main.py の `_TIMETABLE_CLASSES` / `_COURSE_CLASSES`。
同じ表を**手で写している**のが次の 4 か所で、ズレると別々の壊れ方をする:

  class.html          生徒アプリの週間時間割 + 出欠 UI。label は day+限+クラス名から**組み立てる**ので、
                      1文字でも違うと出欠・録画の紐づけキーが一致せず、その生徒の録画が 0 件になる。
  ceo.html            塾長の授業作成フォーム。ここからずれた title で授業を作ると、
                      feed の `title not in my_classes` 判定に落ちて誰にも録画が出ない。
  juku-register.html  塾生の登録フォーム。サーバは _TIMETABLE_LABELS に無い subjects を**黙って捨てる**ので、
                      ズレたラベルは「登録したのに受講クラスが空」になる (無言の取りこぼし)。
  academy.html / enrollment.html
                      公開サイトの時間割表。生徒・保護者が見る曜日はここ。

★このゲートが在る理由 (2026-09-01):
  「国公立コース 長文読解」は実際には**金曜3限**なのに、アプリ側の時間割だけが「木曜3限」だった。
  enrollment.html は同じページの中で「国公立難関大学コース = 水・金・日」と正しく書いていたのに、
  すぐ上の時間割表は木曜に置いていた = **同じ事実の写しが 2 つあって片方だけ直っていた**。
  録画の割り当てスクリプトはこのズレを SLOT_OVERRIDE (金→木の付け替え) で吸収していたため、
  画面はどこも正常に見えたまま 1 か月以上気づかれなかった。人の目視では二度と見つからない種類のズレ。
"""
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # scripts/class_timetable/ → リポジトリ直下
DOW_OF = {"日": 0, "月": 1, "火": 2, "水": 3, "木": 4, "金": 5, "土": 6}

violations = []
notes = []


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def fail(msg):
    violations.append(msg)


def block(src, start_marker, end_marker, where):
    """start_marker から end_marker までを切り出す。見つからなければ**違反**にする。

    ★ここを「見つからなければ素通り」にすると、表の書き方を変えた瞬間に
      検査が空振りして PASS が出る (= このゲートを書いた意味が消える)。
    """
    i = src.find(start_marker)
    if i < 0:
        fail(f"{where}: {start_marker!r} が見つからない — 書き方を変えたならこのゲートも直すこと")
        return None
    j = src.find(end_marker, i + len(start_marker))
    if j < 0:
        fail(f"{where}: {start_marker!r} の終端 {end_marker!r} が見つからない — このゲートも直すこと")
        return None
    return src[i + len(start_marker):j]


# ---------------------------------------------------------------- 正典 (server/main.py)
def canonical():
    """server/main.py を AST で読む (巨大ファイルだが正規表現より確実)。"""
    tree = ast.parse(read("server/main.py"))
    got = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id in ("_TIMETABLE_CLASSES", "_COURSE_CLASSES"):
                got[t.id] = ast.literal_eval(node.value)
    for name in ("_TIMETABLE_CLASSES", "_COURSE_CLASSES"):
        if name not in got:
            fail(f"server/main.py: {name} を module 直下の代入として読めない")
    return got.get("_TIMETABLE_CLASSES"), got.get("_COURSE_CLASSES")


# ---------------------------------------------------------------- class.html
def from_class_html():
    """生徒アプリ。label は class.html 自身と同じ組み立て方で作る (_classesForDow と同一)。"""
    b = block(read("class.html"), "var TIMETABLE = {", "\n    };", "class.html")
    if b is None:
        return None
    out = []
    for day, items in re.findall(r"\{ day: '(.)', items: \[([^\]]*)\]", b):
        for p, t, c, _d in re.findall(r"\{ p: '([^']*)', t: '([^']*)', c: '([^']*)', d: '([^']*)' \}", items):
            out.append((day + "曜" + p + " " + c, DOW_OF.get(day), t))
    sp = block(b, "special: [", "]", "class.html special")
    if sp is not None:
        for day, _lab, t, c, _d in re.findall(
                r"\{ day: '(.)', label: '([^']*)', t: '([^']*)', c: '([^']*)', d: '([^']*)' \}", sp):
            out.append((day + "曜 " + c, DOW_OF.get(day), t))
    if not out:
        fail("class.html: TIMETABLE から 1 コマも読めない — 書き方を変えたならこのゲートも直すこと")
    return out


# ---------------------------------------------------------------- ceo.html
def from_ceo_html():
    """塾長の授業作成フォーム。time は start–end (en dash) で組み立てる。"""
    b = block(read("ceo.html"), "var CLS_TIMETABLE = [", "\n    ];", "ceo.html")
    if b is None:
        return None
    out = []
    for label, _subject, start, end in re.findall(
            r"\{ label: '([^']*)', subject: '([^']*)', start: '([^']*)', end: '([^']*)' \}", b):
        out.append((label, DOW_OF.get(label[:1]), start + "–" + end))
    if not out:
        fail("ceo.html: CLS_TIMETABLE から 1 コマも読めない — 書き方を変えたならこのゲートも直すこと")
    return out


# ---------------------------------------------------------------- juku-register.html
def from_juku_register():
    """塾生の登録フォーム。label (checkbox の value) と COURSES を読む。"""
    src = read("juku-register.html")
    b = block(src, "var CLASSES = [", "\n    ];", "juku-register.html")
    labels = []
    if b is not None:
        for line in b.splitlines():
            m = re.match(r"\s*\['(.)',\s*\[(.*)\]\],?\s*$", line)
            if not m:
                continue
            day = m.group(1)
            for full, _short in re.findall(r"\['([^']*)',\s*'([^']*)'\]", m.group(2)):
                labels.append((full, DOW_OF.get(day)))
        if not labels:
            fail("juku-register.html: CLASSES から 1 コマも読めない — 書き方を変えたならこのゲートも直すこと")
    cb = block(src, "var COURSES = [", "\n    ];", "juku-register.html COURSES")
    courses = {}
    if cb is not None:
        for name, _note, ls in re.findall(
                r"\{ name: '([^']*)', note: '([^']*)', labels: \[([^\]]*)\]", cb):
            courses[name] = re.findall(r"'([^']*)'", ls)
        if not courses:
            fail("juku-register.html: COURSES から 1 コースも読めない — 書き方を変えたならこのゲートも直すこと")
    return labels, courses


# ---------------------------------------------------------------- 公開サイトの時間割表
# 公開ページは正典の写しを**人が読む表**として持っている。略記が入るので、
# 正典のクラス名を空白で割った語がセルに全部含まれることを見る (略記は下の ALIAS で吸収)。
# ★「国公立」だけ・「3限の行だけ」のような緩い一致にしないこと。それだと水3と金3を
#   入れ替えても両方 "国公立" を含むので通ってしまう (2026-09-01 のレビューで実証された穴)。
DAY_COLS = ["月", "火", "水", "木", "金"]
PERIODS = ["1限", "2限", "3限"]
# ページごとの略記。左=正典の語 / 右=そのページでの書き方。
ALIAS = {
    "academy.html": {"高2": "高校2年生"},
    "enrollment.html": {"国公立コース": "国公立"},
}


def _norm(html):
    """セルの HTML → 空白を全部落とした素のテキスト。"""
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", " ", html))


def _card_html(src, input_name):
    """その申込カード (<label class="course-card"> … </label>) の HTML を切り出す。"""
    i = src.find(f'name="{input_name}"')
    if i < 0:
        return ""
    j = src.rfind("<label", 0, i)
    k = src.find("</label>", i)
    return src[j if j >= 0 else i: k if k >= 0 else i + 400]


def _weekday_grid(canon_pairs):
    """正典 → {(限, 曜): クラス名}。日曜は別扱い (時限が無い)。"""
    grid = {}
    for label, _dow, _t in canon_pairs:
        m = re.match(r"^(.)曜(\d限)\s+(.+)$", label)
        if m:
            grid[(m.group(2), m.group(1))] = m.group(3)
    return grid


def check_public_table(rel, row_marker, row_end, period, grid):
    """公開ページの 1 時限分の行を「列 = 月火水木金」として読み、各セルを正典と照合する。"""
    row = block(read(rel), row_marker, row_end, f"{rel} {period}")
    if row is None:
        return
    cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
    if len(cells) != len(DAY_COLS):
        fail(f"{rel}: {period} の行が {len(cells)} 列 (期待 {len(DAY_COLS)}) — 表の形を変えたならこのゲートも直すこと")
        return
    alias = ALIAS.get(rel, {})
    bad = len(violations)
    for day, cell in zip(DAY_COLS, cells):
        text = _norm(cell)
        want = grid.get((period, day))
        if want is None:
            if "—" not in text and "-" not in text:
                fail(f"{rel}: {period} {day}曜 は空きコマのはずが {text!r}")
            continue
        missing = [w for w in want.split()
                   if w.replace(" ", "") not in text and alias.get(w, "\0").replace(" ", "") not in text]
        if missing:
            fail(f"{rel}: {period} {day}曜 は {want!r} のはずだが {missing} が無い (実際: {text!r})")
    if len(violations) == bad:
        print(f"  ✅ {rel}: {period} の {len(cells)} 列 一致")


def report():
    """違反の印字と終了コードを 1 か所に集める (早期 return からも必ずここを通す)。"""
    for n in notes:
        print(n)
    if violations:
        print(f"\n❌ VIOLATION {len(violations)}件")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("\n✅ ALL PASS — 時間割の写しは全ファイルで一致")
    return 0


def main():
    print("🗓 時間割クラスの写し 突き合わせ")
    canon, courses = canonical()
    if canon is None or courses is None:
        # ★ここで素の return 1 をすると、canonical() が積んだ理由を誰も印字しないまま終わる
        #   (CI のログに「ゲートが壊れた」のか「時間割がズレた」のか残らない)。必ず report() を通す。
        fail("正典を読めないので照合を打ち切った")
        return report()
    canon_pairs = [(c["label"], c["dow"], c["time"]) for c in canon]
    canon_labels = [c["label"] for c in canon]
    print(f"  正典 server/main.py: {len(canon_pairs)} コマ")

    # ① 正典そのものの整合 (label の曜日と dow が食い違っていないか)
    for label, dow, _t in canon_pairs:
        if DOW_OF.get(label[:1]) != dow:
            fail(f"server/main.py: {label!r} の dow={dow} が label の曜日と食い違う")

    # ② class.html / ceo.html は label + dow + 時刻まで一致すること
    for rel, got in (("class.html", from_class_html()), ("ceo.html", from_ceo_html())):
        if got is None:
            continue
        if got != canon_pairs:
            only_a = [x for x in canon_pairs if x not in got]
            only_b = [x for x in got if x not in canon_pairs]
            if only_a or only_b:
                for x in only_a:
                    fail(f"{rel}: 正典にあるが無い/違う → {x}")
                for x in only_b:
                    fail(f"{rel}: 正典に無い → {x}")
            else:
                notes.append(f"  ⚠ {rel}: 並び順だけが正典と違う (動作には影響しない)")
        else:
            print(f"  ✅ {rel}: {len(got)} コマ 一致")

    # ③ juku-register.html は label + dow (時刻は持たない)
    reg_labels, reg_courses = from_juku_register()
    if reg_labels:
        want = [(l, d) for l, d, _t in canon_pairs]
        for x in want:
            if x not in reg_labels:
                fail(f"juku-register.html: 登録フォームに無い/曜日違い → {x}")
        for x in reg_labels:
            if x not in want:
                fail(f"juku-register.html: 時間割に無い label → {x} (サーバが黙って捨てる)")
        if not [x for x in want if x not in reg_labels] and not [x for x in reg_labels if x not in want]:
            print(f"  ✅ juku-register.html: {len(reg_labels)} コマ 一致")

    # ④ コース定義 (server/main.py の _COURSE_CLASSES ⇄ juku-register.html の COURSES)
    if reg_courses:
        if set(reg_courses) != set(courses):
            fail(f"コース名が食い違う: server={sorted(courses)} / juku-register={sorted(reg_courses)}")
        for name in sorted(set(reg_courses) & set(courses)):
            if list(reg_courses[name]) != list(courses[name]):
                fail(f"コース {name!r} の中身が食い違う: server={courses[name]} / juku-register={reg_courses[name]}")
            for l in courses[name]:
                if l not in canon_labels:
                    fail(f"コース {name!r} に時間割に無い label: {l!r}")
        if not violations:
            print(f"  ✅ コース定義: {sorted(courses)} 一致")

    # ⑤ 登録フォームが送る subjects を、承認側と同じ規則で展開できること。
    #   ★juku-register.html はコース名を subjects の先頭に入れて送る。承認側
    #     (server/main.py admin_approve_course_application) が _COURSE_CLASSES で
    #     クラスへ展開しないと、コース名は _TIMETABLE_LABELS に無いので**黙って捨てられる**。
    labels_set = set(canon_labels)

    def expand(subjects):
        out = []
        for x in (y.strip() for y in subjects.split("・")):
            if not x:
                continue
            for l in (courses.get(x) or ([x] if x in labels_set else [])):
                if l not in out:
                    out.append(l)
        return out

    for name, want in sorted(courses.items()):
        sent = "・".join([name] + list(want))            # 登録フォームが実際に送る形
        if expand(sent) != list(want):
            fail(f"コース {name!r} の subjects {sent!r} を展開すると {expand(sent)} (期待 {list(want)})")
        elif expand(name) != list(want):
            fail(f"コース名だけの subjects {name!r} を展開すると {expand(name)} (期待 {list(want)})")
        else:
            print(f"  ✅ subjects の展開: {name} → {len(want)}コマ")
    # 承認側がその展開を本当にしているか (関数本体に _COURSE_CLASSES が出てくること)
    _src = read("server/main.py")
    _i = _src.find("def admin_approve_course_application(")
    # ★コメント行を落としてから探すこと。すぐ上の説明コメントが _COURSE_CLASSES に言及しているので、
    #   そのまま探すと**展開のコードを消しても緑のまま**になる (自己テストで実証済み)。
    _body = "\n".join(l for l in _src[_i:_i + 4000].splitlines()
                      if not l.lstrip().startswith("#")) if _i >= 0 else ""
    if _i < 0:
        fail("server/main.py: admin_approve_course_application が見つからない — このゲートも直すこと")
    elif "_COURSE_CLASSES" not in _body:
        fail("server/main.py: admin_approve_course_application が _COURSE_CLASSES を使っていない "
             "= 登録フォームが送るコース名が承認時に黙って捨てられる")
    else:
        print("  ✅ 承認処理が _COURSE_CLASSES を参照している")

    # ⑥ 申込フォームが受講クラスを送っていること
    #   ★入塾申込 (enrollment.html) と国公立コースLP (course-kokuritsu-nankan.html) は
    #     2026-09-01 まで subjects を送っておらず、承認しても students.class_labels が空だった。
    #     空だとクラス限定で配る録画がその生徒だけ 0 件になるのに、画面はどこも正常に見える。
    en = read("enrollment.html")
    cards = re.findall(r'<input type="checkbox" name="(コース_[^"]+)"[^>]*>', en)
    with_tt = dict(re.findall(r'<input type="checkbox" name="(コース_[^"]+)"[^>]*data-tt="([^"]*)"', en))
    # 時間割のコマを持たない商品 (ここに無いカードは必ず data-tt を持つこと)
    NO_CLASS_CARDS = {"コース_学習管理", "コース_AI管理生徒アドオン"}
    if not cards:
        fail("enrollment.html: 申込カードを1枚も読めない — 書き方を変えたならこのゲートも直すこと")
    for nm in cards:
        if nm in NO_CLASS_CARDS:
            if nm in with_tt:
                fail(f"enrollment.html: {nm} は時間割のコマを持たない商品なのに data-tt がある")
            continue
        tt = with_tt.get(nm)
        if not tt:
            fail(f"enrollment.html: {nm} に data-tt が無い = 申し込んでも受講クラスが空になる "
                 f"(時間割のコマを持たない商品なら check_timetable_sync.py の NO_CLASS_CARDS に足すこと)")
        elif tt not in labels_set and tt not in courses:
            fail(f"enrollment.html: {nm} の data-tt {tt!r} が時間割クラスにもコース名にも無い "
                 f"(サーバが黙って捨てる)")
        elif tt in labels_set:
            # ★カードに書いてある曜日・時限と data-tt が一致すること。
            #   ここを見ないと 2 枚のカードで data-tt を入れ替えても「どちらも妥当な label」で通ってしまい、
            #   保護者は申し込んだのと違うクラスに登録される (画面上はどこも壊れて見えない)。
            _card = _card_html(en, nm)
            _meta = re.search(r'<div class="meta">(.*?)</div>', _card, re.S)
            _mt = _norm(_meta.group(1)) if _meta else ""
            _md = re.search(r"([月火水木金土日])曜", _mt)
            _mp = re.search(r"([1-9])限", _mt)
            _ld = tt[:1]
            _lp = re.match(r".曜([1-9])限", tt)
            if _md and _md.group(1) != _ld:
                fail(f"enrollment.html: {nm} のカードは「{_md.group(1)}曜」と書いてあるのに "
                     f"data-tt は {tt!r} ({_ld}曜)")
            elif _mp and _lp and _mp.group(1) != _lp.group(1):
                fail(f"enrollment.html: {nm} のカードは「{_mp.group(1)}限」と書いてあるのに data-tt は {tt!r}")
            elif not _md:
                fail(f"enrollment.html: {nm} のカードに曜日が書かれていない "
                     f"(data-tt {tt!r} と突き合わせられない — meta に「◯曜 N限」を書くこと)")
    if not violations:
        print(f"  ✅ enrollment.html: 申込カード {len(cards)}枚 の受講クラス対応 一致")
    if "subjects: buildSubjects()" not in en:
        fail("enrollment.html: 送信 payload に subjects が無い = 承認しても受講クラスが空のままになる")
    # ★course-kokuritsu-nankan.html には subjects を**足さない**こと。
    #   あの LP の「国公立難関大学コース」は AI 学習管理コース (カリキュラム自動生成・模試分析・
    #   スタサプ連携) であって、時間割の「水3・金3・日」を受講する塾のコースとは別物 (同名の別商品)。
    #   コース名を送ると通っていない 3 コマが受講クラスに付き、そのクラス宛の一斉送信や
    #   配布ファイルの宛先に混ざる。2026-09-01 に一度入れてレビューで取り消した経緯がある。
    ck = read("course-kokuritsu-nankan.html")
    _ckc = [n for n in courses if f"subjects: '{n}'" in ck or f'subjects: "{n}"' in ck]
    if _ckc:
        fail(f"course-kokuritsu-nankan.html が subjects に {_ckc[0]!r} を送っている — "
             f"あの LP は AI 学習管理コースで、時間割の3コマとは別物。通っていないクラスが付く")
    else:
        print("  ✅ course-kokuritsu-nankan.html: subjects を送っていない (AI コースの LP なので正しい)")

    # ⑦ 公開サイトの時間割表 (生徒・保護者が実際に見る曜日)。★全時限を見る。
    grid = _weekday_grid(canon_pairs)
    ac_times = {"1限": "19:15–20:15 中学部", "2限": "20:25–21:25 高校部", "3限": "21:35–22:35 高校部"}
    en_times = {"1限": "19:15-20:15", "2限": "20:25-21:25", "3限": "21:35-22:35"}
    for period in PERIODS:
        check_public_table("academy.html",
                           f'<caption class="sr-only">{period} {ac_times[period]}の時間割</caption>',
                           "</tbody>", period, grid)
        check_public_table("enrollment.html",
                           f"<tr><th>{period}<br>{en_times[period]}</th>", "</tr>", period, grid)
    # 日曜 (時限が無いので別の形で書かれている)
    sun = [l for l, d, _t in canon_pairs if d == 0]
    for rel, marker in (("academy.html", '<div class="sun-line reveal">'),
                        ("enrollment.html", "<tr><th>日曜<br>21:15-22:15</th>")):
        src = read(rel)
        for label in sun:
            name = label.split(" ", 1)[1] if " " in label else label
            i = src.find(marker)
            seg = _norm(src[i:i + 600]) if i >= 0 else ""
            if i < 0:
                fail(f"{rel}: 日曜の記述 {marker!r} が見つからない — 書き方を変えたならこのゲートも直すこと")
            elif name.replace(" ", "") not in seg:
                fail(f"{rel}: 日曜に {name!r} が無い (実際: {seg[:80]!r})")
            else:
                print(f"  ✅ {rel}: 日曜 {name} 一致")

    # ⑧ 公開サイトのコース説明と _COURSE_CLASSES の曜日が矛盾しないこと
    #    (enrollment.html の「国公立難関大学コース … 水・金・日」がまさにこの事故の生き残りだった)
    kk = courses.get("国公立難関大コース")
    if kk:
        # 並びは月→日 (日曜が最後)。DOW_OF は日=0 なので週の始まりを月にずらして並べる。
        days = "・".join(sorted({l[0] for l in kk}, key=lambda d: (DOW_OF[d] - 1) % 7))
        if days not in read("enrollment.html"):
            fail(f"enrollment.html: 国公立難関大学コースの曜日表記が {days!r} になっていない")
        else:
            print(f"  ✅ enrollment.html: 国公立難関大学コース = {days} 一致")

    return report()


if __name__ == "__main__":
    sys.exit(main())
