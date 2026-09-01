#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 check_timetable_sync.py が本当にズレを捕まえるかを、変異を入れて確かめる (run_all_gates.py が拾う)。

    python3 scripts/class_timetable/check_timetable_sync_selftest.py

リポジトリを 1 文字も書き換えない。一時ディレクトリに正典 + 写し 5 ファイル + ゲート本体を
複製し、そこだけを壊してゲートを別プロセスで実行する (ゲートの ROOT は自分の __file__ から
決まるので、複製先を見に行く)。

★このゲートが在る理由 (2026-08-04 の CLAUDE.md「引数なしで回すと見本を検査して緑になる」と同型):
  写しの整合ゲートは**それ自身が空振りしても緑に見える**。実際、初版の check_timetable_sync.py は
  公開ページを「3限の行だけ・"国公立" の部分一致だけ」で見ていたため、
  水曜3限と金曜3限を丸ごと入れ替えても ALL PASS を出した (2026-09-01 のレビューで実証)。
  保護者が見る時間割だけが逆のまま「全ファイル一致」と報告する状態で、目視では気づけない。
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GATE = "check_timetable_sync.py"
COPY = ["server/main.py", "class.html", "ceo.html", "juku-register.html",
        "academy.html", "enrollment.html", "course-kokuritsu-nankan.html"]

# (ラベル, 対象ファイル, 置換前, 置換後)  ※どれも「ゲートが落ちる」ことを期待する
MUTATIONS = [
    ("正典の dow を label と食い違わせる", "server/main.py",
     '{"label": "金曜3限 国公立コース 長文読解", "dow": 5,',
     '{"label": "金曜3限 国公立コース 長文読解", "dow": 4,'),
    ("class.html の label を1文字変える", "class.html",
     "c: '国公立コース 長文読解', d: '国公立難関大コースに含む'",
     "c: '国公立コース 長文読解2', d: '国公立難関大コースに含む'"),
    ("ceo.html を旧ラベルに戻す", "ceo.html",
     "{ label: '金曜3限 国公立コース 長文読解',", "{ label: '木曜3限 国公立コース 長文読解',"),
    ("登録フォームを旧ラベルに戻す", "juku-register.html",
     "['金曜3限 国公立コース 長文読解', '3限 国公立 長文読解']",
     "['木曜3限 国公立コース 長文読解', '3限 国公立 長文読解']"),
    ("登録フォームのコース定義を食い違わせる", "juku-register.html",
     "'日曜 高校国語'\n      ] }", "'火曜3限 長文読解 Lv.2'\n      ] }"),
    # ★初版が見逃していた型: 公開ページだけ 木/金 が逆
    ("academy の3限を木曜に戻す", "academy.html",
     '<td class="empty">—</td>\n            <td><b>国公立コース</b><span>長文読解</span></td>',
     '<td><b>国公立コース</b><span>長文読解</span></td>\n            <td class="empty">—</td>'),
    ("enrollment の3限を木曜に戻す", "enrollment.html",
     "<td>国公立<br>英文法</td><td>—</td><td>国公立<br>長文読解</td>",
     "<td>国公立<br>英文法</td><td>国公立<br>長文読解</td><td>—</td>"),
    # ★初版が見逃していた型: 水3 と 金3 の科目を入れ替え (どちらも "国公立" を含むので部分一致では通る)
    ("academy の 水3 と 金3 の科目を入れ替える", "academy.html",
     "<td><b>国公立コース</b><span>英文法</span></td>\n            <td class=\"empty\">—</td>\n"
     "            <td><b>国公立コース</b><span>長文読解</span></td>",
     "<td><b>国公立コース</b><span>長文読解</span></td>\n            <td class=\"empty\">—</td>\n"
     "            <td><b>国公立コース</b><span>英文法</span></td>"),
    ("enrollment の 水3 と 金3 の科目を入れ替える", "enrollment.html",
     "<td>国公立<br>英文法</td><td>—</td><td>国公立<br>長文読解</td>",
     "<td>国公立<br>長文読解</td><td>—</td><td>国公立<br>英文法</td>"),
    # ★初版が見逃していた型: 3限以外の行 (10コマが無検査だった)
    ("academy の 1限 木曜を別クラスにする", "academy.html",
     "<td><b>英検準1級 対策</b><span>中高合同</span></td>", "<td><b>ダミー授業</b></td>"),
    ("enrollment の 2限 月/火 を入れ替える", "enrollment.html",
     "<td>英文法 Lv.1<br>標準・高1/2</td><td>英文法 Lv.2<br>難関・高3</td>",
     "<td>英文法 Lv.2<br>難関・高3</td><td>英文法 Lv.1<br>標準・高1/2</td>"),
    ("公開ページのコース曜日表記を壊す", "enrollment.html",
     '<div class="meta">水・金・日 ＋ スタサプ</div>', '<div class="meta">水・木・日 ＋ スタサプ</div>'),
    # ★空振り検出: 表の書き方を変えたらゲートは黙って通らず落ちること
    ("class.html の表の書き方を変える (空振りしないこと)", "class.html",
     "var TIMETABLE = {", "var TIMETABLE_X = {"),
    ("正典の変数名を変える (理由が印字されること)", "server/main.py",
     "_COURSE_CLASSES = {", "_COURSE_CLASSES_MOVED = {"),
    # ★承認側がコース名を展開しなくなると、登録フォームが送るコース名が黙って捨てられる
    ("承認処理からコース展開を外す", "server/main.py",
     "for _l in (_COURSE_CLASSES.get(_s) or ([_s] if _s in _TIMETABLE_LABELS else [])):",
     "for _l in ([_s] if _s in _TIMETABLE_LABELS else []):"),
    ("公開ページの日曜から高校国語を消す", "academy.html",
     '<span class="sc">高校国語（現代文・古文）</span>', '<span class="sc">現代文・古文</span>'),
    # ★申込フォームが受講クラスを送らないと、承認しても class_labels が空のまま (録画が0件になる)
    ("入塾申込のカードから data-tt を外す", "enrollment.html",
     'name="コース_GMARCH" value="ON" data-fee="12500" data-tt="水曜2限 GMARCH"',
     'name="コース_GMARCH" value="ON" data-fee="12500"'),
    ("入塾申込の data-tt を旧ラベルに戻す", "enrollment.html",
     'data-tt="国公立難関大コース"', 'data-tt="木曜3限 国公立コース 長文読解"'),
    # ★2枚のカードで data-tt を入れ替える (どちらも妥当な label なので、カード側の曜日を見ないと通る)
    ("入塾申込の data-tt を2枚で入れ替える", "enrollment.html",
     'name="コース_長文L1" value="ON" data-fee="7500" data-tt="月曜3限 長文読解 Lv.1"',
     'name="コース_長文L1" value="ON" data-fee="7500" data-tt="火曜3限 長文読解 Lv.2"'),
    ("入塾申込が subjects を送らなくなる", "enrollment.html",
     "subjects: buildSubjects() || undefined,", "// subjects は送らない"),
    ("コースLPに subjects を足してしまう (AIコースのLPなので誤り)", "course-kokuritsu-nankan.html",
     "              note: note || undefined,", "              note: note || undefined,\n              subjects: '国公立難関大コース',"),
]


def prepare(dst):
    for rel in COPY:
        d = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, rel), d)
    gd = os.path.join(dst, "scripts", "class_timetable")
    os.makedirs(gd, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, GATE), os.path.join(gd, GATE))
    return gd


def run_gate(gate_dir):
    r = subprocess.run([sys.executable, GATE], cwd=gate_dir, capture_output=True, text=True, timeout=120)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    failures = []
    tmp = tempfile.mkdtemp(prefix="tt_sync_selftest_")
    try:
        gate_dir = prepare(tmp)
        code, out = run_gate(gate_dir)
        if code != 0:
            print("❌ 変異を入れる前から落ちている — 複製が壊れているか、ゲート自体の不具合")
            print("\n".join("    " + l for l in out.splitlines()[:20]))
            return 1
        print(f"複製した写しでの素の実行: exit=0 (基準)")
        print("変異を入れてゲートが落ちること:")
        for label, rel, old, new in MUTATIONS:
            path = os.path.join(tmp, rel)
            orig = io.open(path, encoding="utf-8").read()
            if orig.count(old) != 1:
                failures.append(f"{label}: 置換前の文字列が {orig.count(old)} 箇所 (期待 1) — "
                                f"ファイルを変えたならこの自己テストも直すこと")
                print(f"  ❌ {label}: 置換対象が見つからない/複数ある")
                continue
            io.open(path, "w", encoding="utf-8").write(orig.replace(old, new))
            code, out = run_gate(gate_dir)
            io.open(path, "w", encoding="utf-8").write(orig)
            if code == 0:
                failures.append(f"{label}: ゲートが見逃した (exit=0)")
                print(f"  ❌ {label}: **見逃し** exit=0")
            elif "VIOLATION" not in out:
                # 落ちてはいるが理由が出ていない = CI のログに何も残らない
                failures.append(f"{label}: exit={code} だが理由 (VIOLATION 行) が印字されていない")
                print(f"  ❌ {label}: exit={code} だが理由が出ない")
                print("\n".join("      " + l for l in out.splitlines()[:8]))
            else:
                print(f"  ✅ {label}: exit={code} + 理由あり")
        # 復元できているか (最後にもう一度素で通ること)
        code, _ = run_gate(gate_dir)
        if code != 0:
            failures.append("変異の復元に失敗している (最後の素の実行が落ちた)")
            print("  ❌ 復元後の素の実行が落ちた")
        else:
            print("  ✅ 復元後の素の実行: exit=0")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print(f"\n❌ VIOLATION {len(failures)}件")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\n✅ ALL PASS — {len(MUTATIONS)} 通りのズレを全部捕まえた")
    return 0


if __name__ == "__main__":
    sys.exit(main())
