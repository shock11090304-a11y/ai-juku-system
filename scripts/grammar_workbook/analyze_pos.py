#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, glob, re
dist = {}; total = [0,0,0,0]; posref = []
for f in sorted(glob.glob('units/*.json')):
    d = json.load(open(f, encoding='utf-8')); slug = d['unit']
    c = [0,0,0,0]
    for q in d['questions']:
        if q['type'] == 'mc':
            ai = q['answer_index']; c[ai] += 1; total[ai] += 1
            txt = (q.get('explanation','') + ' ' + q.get('point',''))
            if re.search(r'[①②③④⑤]', txt) or re.search(r'\d+\s*番目|選択肢\s*[1-4１-４]', txt):
                posref.append(f"{slug}#{q['no']}: {txt[:50]}")
    dist[slug] = c
print('all mc answer_index dist [0,1,2,3]:', total, 'sum', sum(total))
for s, c in dist.items():
    flag = '  <<< skew' if sum(c) and max(c) >= sum(c)*0.7 else ''
    print(f'  {s}: {c}{flag}')
print('position-referencing explanations (unsafe to shuffle):', len(posref))
for p in posref[:30]:
    print('  ', p)
