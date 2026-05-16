#!/usr/bin/env python3
"""ai-juku exam_questions pool health audit.

Two modes:
  --mode teiki     : 87 TEIKI_UNIT_INDEX 単元の topic ヒット数を audit (定期テスト)
  --mode daigaku   : 大学入試 daigaku/rikei rotation 各 tuple の count を audit

Usage:
  python3 scripts/audit_pool_health.py --mode teiki
  python3 scripts/audit_pool_health.py --mode daigaku
  python3 scripts/audit_pool_health.py --mode daigaku --threshold 10

Returns exit code:
  0  : all OK (no gaps)
  1  : gaps detected (< threshold)
  2  : connection error
"""
import argparse
import urllib.request
import urllib.parse
import json
import sys
import time

BASE_URL_DEFAULT = 'https://ai-juku-api-production.up.railway.app/api/exam-questions/bank'

# 87 TEIKI 単元 (frontend english-exam.js の TEIKI_UNIT_INDEX と同期)
TEIKI_UNITS = [
    ('math1a-二次関数', 'rikei', 'math_1a', 'kyotsu_rikei', '二次関数'),
    ('math1a-図形と計量', 'rikei', 'math_1a', 'kyotsu_rikei', '図形と計量'),
    ('math1a-データ', 'rikei', 'math_1a', 'kyotsu_rikei', 'データ'),
    ('math1a-確率', 'rikei', 'math_1a', 'kyotsu_rikei', '確率'),
    ('math1a-整数', 'rikei', 'math_1a', 'kyotsu_rikei', '整数'),
    ('math1a-二次方程式', 'rikei', 'math_1a', 'kyotsu_rikei', '二次方程式'),
    ('math1a-円と直線', 'rikei', 'math_1a', 'kyotsu_rikei', '円と直線'),
    ('math2b-三角関数', 'rikei', 'math_2b', 'kyotsu_rikei', '三角関数'),
    ('math2b-指数対数', 'rikei', 'math_2b', 'kyotsu_rikei', '指数対数'),
    ('math2b-微積', 'rikei', 'math_2b', 'kyotsu_rikei', '微積'),
    ('math2b-数列', 'rikei', 'math_2b', 'kyotsu_rikei', '数列'),
    ('math2b-ベクトル', 'rikei', 'math_2b', 'kyotsu_rikei', 'ベクトル'),
    ('phys-運動', 'rikei', 'phys_basic', 'kyotsu_rikei', '運動'),
    ('phys-力', 'rikei', 'phys_basic', 'kyotsu_rikei', '力'),
    ('phys-エネルギー', 'rikei', 'phys_basic', 'kyotsu_rikei', 'エネルギー'),
    ('phys-熱', 'rikei', 'phys_basic', 'kyotsu_rikei', '熱'),
    ('phys-波', 'rikei', 'phys_basic', 'kyotsu_rikei', '波'),
    ('phys-電気', 'rikei', 'phys_basic', 'kyotsu_rikei', '電気'),
    ('phys-運動量', 'rikei', 'phys_basic', 'kyotsu_rikei', '運動量'),
    ('phys-単振動', 'rikei', 'phys_basic', 'kyotsu_rikei', '単振動'),
    ('chem-mol', 'rikei', 'chem_basic', 'kyotsu_rikei', 'mol'),
    ('chem-周期表', 'rikei', 'chem_basic', 'kyotsu_rikei', '周期表'),
    ('chem-結合', 'rikei', 'chem_basic', 'kyotsu_rikei', '結合'),
    ('chem-酸塩基', 'rikei', 'chem_basic', 'kyotsu_rikei', '酸塩基'),
    ('chem-酸化還元', 'rikei', 'chem_basic', 'kyotsu_rikei', '酸化還元'),
    ('chem-反応', 'rikei', 'chem_basic', 'kyotsu_rikei', '反応'),
    ('chem-熱化学', 'rikei', 'chem_basic', 'kyotsu_rikei', '熱化学'),
    ('chem-反応速度', 'rikei', 'chem_basic', 'kyotsu_rikei', '反応速度'),
    ('bio-細胞', 'rikei', 'bio_basic', 'kyotsu_rikei', '細胞'),
    ('bio-DNA', 'rikei', 'bio_basic', 'kyotsu_rikei', 'DNA'),
    ('bio-体内環境', 'rikei', 'bio_basic', 'kyotsu_rikei', '体内環境'),
    ('bio-免疫', 'rikei', 'bio_basic', 'kyotsu_rikei', '免疫'),
    ('bio-生態系', 'rikei', 'bio_basic', 'kyotsu_rikei', '生態系'),
    ('bio-ATP', 'rikei', 'bio_basic', 'kyotsu_rikei', 'ATP'),
    ('bio-酵素', 'rikei', 'bio_basic', 'kyotsu_rikei', '酵素'),
    ('bio-自律神経', 'rikei', 'bio_basic', 'kyotsu_rikei', '自律神経'),
    ('eng-grammar-関係', 'daigaku', 'r_grammar', 'teiki', '関係'),
    ('eng-grammar-分詞', 'daigaku', 'r_grammar', 'teiki', '分詞'),
    ('eng-grammar-仮定法', 'daigaku', 'r_grammar', 'teiki', '仮定法'),
    ('eng-grammar-比較', 'daigaku', 'r_grammar', 'teiki', '比較'),
    ('eng-grammar-受動態', 'daigaku', 'r_grammar', 'teiki', '受動態'),
    ('eng-grammar-不定詞', 'daigaku', 'r_grammar', 'teiki', '不定詞'),
    ('eng-grammar-時制', 'daigaku', 'r_grammar', 'teiki', '時制'),
    ('eng-grammar-前置詞', 'daigaku', 'r_grammar', 'teiki', '前置詞'),
    ('eng-grammar-接続詞', 'daigaku', 'r_grammar', 'teiki', '接続詞'),
    ('eng-grammar-助動詞', 'daigaku', 'r_grammar', 'teiki', '助動詞'),
    ('eng-grammar-動名詞', 'daigaku', 'r_grammar', 'teiki', '動名詞'),
    ('eng-r_long-teiki', 'daigaku', 'r_long', 'teiki', ''),
    ('eng-r_short-teiki', 'daigaku', 'r_short', 'teiki', ''),
    ('eng-w_essay-teiki', 'daigaku', 'w_essay', 'teiki', ''),
    ('kobun-活用', 'daigaku', 'kobun', 'kyotsu', '活用'),
    ('kobun-助動詞', 'daigaku', 'kobun', 'kyotsu', '助動詞'),
    ('kobun-敬語', 'daigaku', 'kobun', 'kyotsu', '敬語'),
    ('kobun-単語', 'daigaku', 'kobun', 'kyotsu', '単語'),
    ('kobun-係り結び', 'daigaku', 'kobun', 'kyotsu', '係り結び'),
    ('kobun-識別', 'daigaku', 'kobun', 'kyotsu', '識別'),
    ('kobun-読解', 'daigaku', 'kobun', 'kyotsu', '読解'),
    ('kanbun-返り点', 'daigaku', 'kanbun', 'kyotsu', '返り点'),
    ('kanbun-書き下し', 'daigaku', 'kanbun', 'kyotsu', '書き下し'),
    ('kanbun-再読文字', 'daigaku', 'kanbun', 'kyotsu', '再読文字'),
    ('kanbun-句法', 'daigaku', 'kanbun', 'kyotsu', '句法'),
    ('kanbun-読解', 'daigaku', 'kanbun', 'kyotsu', '読解'),
    ('nihonshi-古代', 'daigaku', 'nihonshi', 'kyotsu', '古代'),
    ('nihonshi-中世', 'daigaku', 'nihonshi', 'kyotsu', '中世'),
    ('nihonshi-近世', 'daigaku', 'nihonshi', 'kyotsu', '近世'),
    ('nihonshi-近代', 'daigaku', 'nihonshi', 'kyotsu', '近代'),
    ('nihonshi-現代', 'daigaku', 'nihonshi', 'kyotsu', '現代'),
    ('nihonshi-文化', 'daigaku', 'nihonshi', 'kyotsu', '文化'),
    ('sekaishi-古代', 'daigaku', 'sekaishi', 'kyotsu', '古代'),
    ('sekaishi-中世', 'daigaku', 'sekaishi', 'kyotsu', '中世'),
    ('sekaishi-イスラーム', 'daigaku', 'sekaishi', 'kyotsu', 'イスラーム'),
    ('sekaishi-中国', 'daigaku', 'sekaishi', 'kyotsu', '中国'),
    ('sekaishi-近代', 'daigaku', 'sekaishi', 'kyotsu', '近代'),
    ('sekaishi-現代', 'daigaku', 'sekaishi', 'kyotsu', '現代'),
    ('chiri-気候', 'daigaku', 'chiri', 'kyotsu', '気候'),
    ('chiri-地形', 'daigaku', 'chiri', 'kyotsu', '地形'),
    ('chiri-人口', 'daigaku', 'chiri', 'kyotsu', '人口'),
    ('chiri-農業', 'daigaku', 'chiri', 'kyotsu', '農業'),
    ('chiri-工業', 'daigaku', 'chiri', 'kyotsu', '工業'),
    ('chiri-環境', 'daigaku', 'chiri', 'kyotsu', '環境'),
    ('kouminka-憲法', 'daigaku', 'kouminka', 'kyotsu', '憲法'),
    ('kouminka-三権', 'daigaku', 'kouminka', 'kyotsu', '三権'),
    ('kouminka-人権', 'daigaku', 'kouminka', 'kyotsu', '人権'),
    ('kouminka-地方', 'daigaku', 'kouminka', 'kyotsu', '地方'),
    ('kouminka-経済', 'daigaku', 'kouminka', 'kyotsu', '経済'),
    ('kouminka-国際', 'daigaku', 'kouminka', 'kyotsu', '国際'),
    ('kouminka-倫理', 'daigaku', 'kouminka', 'kyotsu', '倫理'),
]

# 全 136 大学入試 + 英検 + 理系 rotation tuples
# (server/main.py の EXAM_QUESTION_ROTATION と同期)
DAIGAKU_TUPLES = [
    # === daigaku 81 tuples ===
    ('daigaku', 'r_long', 'todai'),
    ('daigaku', 'r_summary', 'todai'),
    ('daigaku', 'w_essay', 'todai'),
    ('daigaku', 'r_translation', 'todai'),
    ('daigaku', 'r_long', 'kyodai'),
    ('daigaku', 'r_translation', 'kyodai'),
    ('daigaku', 'w_essay', 'kyodai'),
    ('daigaku', 'r_long', 'osaka'),
    ('daigaku', 'w_essay', 'osaka'),
    ('daigaku', 'g_grammar', 'osaka'),
    ('daigaku', 'r_long', 'tokoda'),
    ('daigaku', 'r_long', 'hitotsu'),
    ('daigaku', 'r_translation', 'hitotsu'),
    ('daigaku', 'r_long', 'nagoya'),
    ('daigaku', 'r_long', 'waseda'),
    ('daigaku', 'w_essay', 'waseda'),
    ('daigaku', 'g_grammar', 'waseda'),
    ('daigaku', 'r_long', 'keio'),
    ('daigaku', 'w_essay', 'keio'),
    ('daigaku', 'r_long', 'sophia'),
    ('daigaku', 'r_long', 'icu'),
    ('daigaku', 'r_long', 'meiji'),
    ('daigaku', 'r_long', 'aogaku'),
    ('daigaku', 'r_long', 'rikkyo'),
    ('daigaku', 'r_long', 'chuo'),
    ('daigaku', 'r_long', 'hosei'),
    ('daigaku', 'r_long', 'kandai'),
    ('daigaku', 'r_long', 'kangaku'),
    ('daigaku', 'r_long', 'doshisha'),
    ('daigaku', 'r_long', 'ritsumei'),
    ('daigaku', 'r_long', 'hokudai'),
    ('daigaku', 'w_essay', 'hokudai'),
    ('daigaku', 'r_translation', 'hokudai'),
    ('daigaku', 'r_long', 'tohoku'),
    ('daigaku', 'w_essay', 'tohoku'),
    ('daigaku', 'r_translation', 'tohoku'),
    ('daigaku', 'r_long', 'kyushu'),
    ('daigaku', 'w_essay', 'kyushu'),
    ('daigaku', 'r_translation', 'kyushu'),
    ('daigaku', 'r_long', 'kobe'),
    ('daigaku', 'w_essay', 'kobe'),
    ('daigaku', 'r_translation', 'kobe'),
    ('daigaku', 'r_long', 'yokokoku'),
    ('daigaku', 'w_essay', 'yokokoku'),
    ('daigaku', 'r_long', 'chiba'),
    ('daigaku', 'r_translation', 'chiba'),
    ('daigaku', 'r_long', 'tsukuba'),
    ('daigaku', 'w_essay', 'tsukuba'),
    ('daigaku', 'r_long', 'gakushuin'),
    ('daigaku', 'r_long', 'seikei'),
    ('daigaku', 'r_long', 'seijo'),
    ('daigaku', 'r_long', 'musashi'),
    ('daigaku', 'r_long', 'igakubu_kokoritsu'),
    ('daigaku', 'r_translation', 'igakubu_kokoritsu'),
    ('daigaku', 'w_essay', 'igakubu_kokoritsu'),
    ('daigaku', 'r_long', 'igakubu_shiritsu'),
    ('daigaku', 'r_long', 'kyotsu'),
    ('daigaku', 'r_short', 'kyotsu'),
    ('daigaku', 'l_part1_2', 'kyotsu'),
    ('daigaku', 'l_part3_4', 'kyotsu'),
    ('daigaku', 'r_long', 'center'),
    ('daigaku', 'r_grammar', 'center'),
    ('daigaku', 'l_listening', 'center'),
    ('daigaku', 'kobun', 'kyotsu'),
    ('daigaku', 'kanbun', 'kyotsu'),
    ('daigaku', 'kobun', 'todai'),
    ('daigaku', 'kanbun', 'todai'),
    ('daigaku', 'kobun', 'kyodai'),
    ('daigaku', 'kanbun', 'kyodai'),
    ('daigaku', 'r_long', 'kiso'),
    ('daigaku', 'r_short', 'kiso'),
    ('daigaku', 'r_grammar', 'kiso'),
    ('daigaku', 'w_essay', 'kiso'),
    ('daigaku', 'r_long', 'teiki'),
    ('daigaku', 'r_short', 'teiki'),
    ('daigaku', 'r_grammar', 'teiki'),
    ('daigaku', 'w_essay', 'teiki'),
    ('daigaku', 'nihonshi', 'kyotsu'),
    ('daigaku', 'sekaishi', 'kyotsu'),
    ('daigaku', 'chiri', 'kyotsu'),
    ('daigaku', 'kouminka', 'kyotsu'),
    # === eiken 19 tuples ===
    ('eiken', 'r_q1', 'gp1'),
    ('eiken', 'r_q3', 'gp1'),
    ('eiken', 'w_essay', 'gp1'),
    ('eiken', 'r_q1', 'g2'),
    ('eiken', 'r_q3', 'g2'),
    ('eiken', 'r_q3b', 'g2'),
    ('eiken', 'w_opinion', 'g2'),
    ('eiken', 'w_summary', 'g2'),
    ('eiken', 'r_q1', 'g3'),
    ('eiken', 'r_q1', 'g1'),
    ('eiken', 'r_q3', 'g1'),
    ('eiken', 'w_summary', 'g1'),
    ('eiken', 'w_essay', 'g1'),
    ('eiken', 'r_q1', 'gp2'),
    ('eiken', 'r_q3b', 'gp2'),
    ('eiken', 'w_email', 'gp2'),
    ('eiken', 'w_opinion', 'gp2'),
    ('eiken', 'r_q1', 'g4'),
    ('eiken', 'r_q1', 'g5'),
    # === rikei 36 tuples ===
    ('rikei', 'math_1a', 'kyotsu_rikei'),
    ('rikei', 'math_2b', 'kyotsu_rikei'),
    ('rikei', 'phys_basic', 'kyotsu_rikei'),
    ('rikei', 'chem_basic', 'kyotsu_rikei'),
    ('rikei', 'bio_basic', 'kyotsu_rikei'),
    ('rikei', 'math_q1', 'todai_rikei'),
    ('rikei', 'math_q2', 'todai_rikei'),
    ('rikei', 'math_q3', 'todai_rikei'),
    ('rikei', 'phys_q1', 'todai_rikei'),
    ('rikei', 'phys_q2', 'todai_rikei'),
    ('rikei', 'chem_q1', 'todai_rikei'),
    ('rikei', 'chem_q3', 'todai_rikei'),
    ('rikei', 'math_q1', 'kyodai_rikei'),
    ('rikei', 'math_q2', 'kyodai_rikei'),
    ('rikei', 'phys_q1', 'kyodai_rikei'),
    ('rikei', 'chem_q2', 'kyodai_rikei'),
    ('rikei', 'math_q1', 'osaka_rikei'),
    ('rikei', 'phys_q1', 'osaka_rikei'),
    ('rikei', 'math_q1', 'tokoda_rikei'),
    ('rikei', 'phys_q1', 'tokoda_rikei'),
    ('rikei', 'math_q1', 'nagoya_rikei'),
    ('rikei', 'math_q1', 'waseda_rikei'),
    ('rikei', 'phys_q1', 'waseda_rikei'),
    ('rikei', 'math_q1', 'keio_rikei'),
    ('rikei', 'math_q2', 'keio_rikei'),
    ('rikei', 'bio_q1', 'keio_rikei'),
    ('rikei', 'math_q1', 'sophia_rikei'),
    ('rikei', 'math_q1', 'igakubu_kokoritsu_rikei'),
    ('rikei', 'phys_q1', 'igakubu_kokoritsu_rikei'),
    ('rikei', 'chem_q1', 'igakubu_kokoritsu_rikei'),
    ('rikei', 'bio_q1', 'igakubu_kokoritsu_rikei'),
    ('rikei', 'math_q1', 'igakubu_shiritsu_rikei'),
    ('rikei', 'phys_q1', 'igakubu_shiritsu_rikei'),
    ('rikei', 'math_basic', 'march_rikei'),
    ('rikei', 'phys_basic_q', 'march_rikei'),
    ('rikei', 'chem_basic_q', 'march_rikei'),
]
# 旧 list 形式 (priority subset) は不要だが、旧呼び出しとの互換のため空 list を残す
_DAIGAKU_LEGACY_PRIORITY = [
    ('daigaku', 'r_long', u) for u in []
] + [
    ('rikei', 'math_q2', 'todai_rikei'),
    ('rikei', 'math_q3', 'todai_rikei'),
    ('rikei', 'math_q2', 'kyodai_rikei'),
    ('rikei', 'math_q2', 'keio_rikei'),
] + [
    # rikei 物理 phys_q1
    ('rikei', 'phys_q1', u) for u in [
        'todai_rikei', 'kyodai_rikei', 'osaka_rikei', 'tokoda_rikei',
        'waseda_rikei', 'igakubu_kokoritsu_rikei', 'igakubu_shiritsu_rikei',
    ]
] + [
    ('rikei', 'phys_q2', 'todai_rikei'),
    # rikei 化学
    ('rikei', 'chem_q1', 'todai_rikei'),
    ('rikei', 'chem_q3', 'todai_rikei'),
    ('rikei', 'chem_q2', 'kyodai_rikei'),
    ('rikei', 'chem_q1', 'igakubu_kokoritsu_rikei'),
    # rikei 生物
    ('rikei', 'bio_q1', 'keio_rikei'),
    ('rikei', 'bio_q1', 'igakubu_kokoritsu_rikei'),
    # MARCH 理工
    ('rikei', 'math_basic', 'march_rikei'),
    ('rikei', 'phys_basic_q', 'march_rikei'),
    ('rikei', 'chem_basic_q', 'march_rikei'),
]


def query(base_url, exam_id, part_key, eiken_grade, topic=None):
    params = {'exam': exam_id, 'part': part_key, 'limit': '50'}
    if eiken_grade:
        params['eiken_grade'] = eiken_grade
    if exam_id == 'daigaku' and eiken_grade:
        params['univ'] = eiken_grade
    if topic:
        params['topic'] = topic
    url = base_url + '?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
            return data.get('count', 0), None
    except Exception as e:
        return -1, str(e)


def audit_teiki(base_url, threshold):
    gaps = []
    ok_count = 0
    print(f"{'Unit':35s} | {'Count':>5s} | Status")
    print("-" * 70)
    for label, exam_id, part_key, eiken_grade, topic in TEIKI_UNITS:
        count, err = query(base_url, exam_id, part_key, eiken_grade, topic)
        if count < 0:
            print(f"{label:35s} | {'ERR':>5s} | {err}")
            continue
        if count < threshold:
            print(f"{label:35s} | {count:>5d} | ❌ LOW")
            gaps.append((label, count, exam_id, part_key, eiken_grade, topic))
        else:
            print(f"{label:35s} | {count:>5d} | ✓")
            ok_count += 1
        time.sleep(0.05)
    print(f"\nTEIKI: {len(TEIKI_UNITS)} units, OK={ok_count}, GAPS(<{threshold})={len(gaps)}")
    return gaps


def audit_daigaku(base_url, threshold):
    gaps = []
    ok_count = 0
    print(f"{'Tuple':50s} | {'Count':>5s} | Status")
    print("-" * 80)
    for exam_id, part_key, eiken_grade in DAIGAKU_TUPLES:
        count, err = query(base_url, exam_id, part_key, eiken_grade)
        label = f"{exam_id}/{part_key}/{eiken_grade}"
        if count < 0:
            print(f"{label:50s} | {'ERR':>5s} | {err}")
            continue
        if count < threshold:
            print(f"{label:50s} | {count:>5d} | ❌ LOW")
            gaps.append((label, count, exam_id, part_key, eiken_grade))
        else:
            print(f"{label:50s} | {count:>5d} | ✓")
            ok_count += 1
        time.sleep(0.05)
    print(f"\nDAIGAKU: {len(DAIGAKU_TUPLES)} tuples, OK={ok_count}, GAPS(<{threshold})={len(gaps)}")
    return gaps


def main():
    parser = argparse.ArgumentParser(description='ai-juku pool health audit')
    parser.add_argument('--mode', choices=['teiki', 'daigaku', 'all'], default='all')
    parser.add_argument('--threshold', type=int, default=5)
    parser.add_argument('--base-url', default=BASE_URL_DEFAULT)
    args = parser.parse_args()
    all_gaps = []
    try:
        if args.mode in ('teiki', 'all'):
            print("\n=== TEIKI 定期テスト pool audit ===\n")
            all_gaps.extend(audit_teiki(args.base_url, args.threshold))
        if args.mode in ('daigaku', 'all'):
            print("\n=== DAIGAKU 大学入試 pool audit ===\n")
            all_gaps.extend(audit_daigaku(args.base_url, args.threshold))
    except KeyboardInterrupt:
        print("\nAborted by user")
        sys.exit(130)
    print(f"\n=== TOTAL GAPS: {len(all_gaps)} ===")
    for g in all_gaps:
        print(f"  {g}")
    sys.exit(1 if all_gaps else 0)


if __name__ == '__main__':
    main()
