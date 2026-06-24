#!/usr/bin/env python3
"""seed の大問を閲覧できる自己完結HTMLウィジェットを生成 (/tmp/eng_viewer.html)。
使い方: generate_viewer.py [max_per_format] [only_fmt]
  max_per_format: 各形式の表示上限 (既定=全件)
  only_fmt      : FMT3 等を指定するとその形式のみ
"""
import json, os, sys

SEED = os.path.join(os.path.dirname(__file__), '..', '..', 'seed-data', 'dojo_eng_kyotsu2026_manual.json')
OUT = '/tmp/eng_viewer.html'
MAX_PER = int(sys.argv[1]) if len(sys.argv) > 1 else 999
ONLY = sys.argv[2] if len(sys.argv) > 2 else None

LABELS = {
    'FMT1': '第1問 短文・対話', 'FMT2': '第2問 調査・意見', 'FMT3': '第3問 物語＋順序',
    'FMT4': '第4問 文章校正', 'FMT5': '第5問 複数資料統合', 'FMT6': '第6問 物語＋アウトライン',
    'FMT7': '第7問 論説＋スライド', 'FMT8': '第8問 意見統合＋資料',
    'FMT_GRAPH': '調査・グラフ', 'FMT_GRAPH8': '第8問 意見統合＋グラフ',
}

SEED = sys.argv[3] if len(sys.argv) > 3 else SEED  # 第3引数で seed パス上書き可
rows = json.load(open(SEED))['questions']
# 並びを FMT1..8 に整える
order = {f: i for i, f in enumerate(['FMT1','FMT2','FMT3','FMT4','FMT5','FMT6','FMT7','FMT8','FMT_GRAPH8','FMT_GRAPH'])}
rows.sort(key=lambda r: order.get(r['question_data'].get('format_type'), 9))

# 形式ごとに上限/絞り込み
seen = {}
sel = []
for r in rows:
    f = r['question_data'].get('format_type')
    if ONLY and f != ONLY:
        continue
    if seen.get(f, 0) >= MAX_PER:
        continue
    seen[f] = seen.get(f, 0) + 1
    sel.append(r)
rows = sel

data = []
for r in rows:
    qd = r['question_data']
    data.append({
        'fmt': qd.get('format_type'),
        'part': r['part_key'],
        'passage': qd['passage'],
        'figure': qd.get('figure_svg', ''),
        'questions': [{
            'stem': q['stem'], 'choices': q['choices'], 'answer': q['answer'],
            'unit': q['unit'], 'explanation': q['explanation'],
        } for q in qd['questions']],
    })

data_json = json.dumps({'labels': LABELS, 'rows': data}, ensure_ascii=False).replace('<', '\\u003c')

html = '''<h2 class="sr-only">共通テスト2026英語に類似して作成した40大問のビューア。形式を選び、各大問の本文・設問・正答・解説を確認できます。</h2>
<div style="padding:0.5rem 0;">
  <div id="eng-filter" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;"></div>
  <div id="eng-list" style="display:flex;flex-direction:column;gap:10px;"></div>
</div>
<script type="application/json" id="eng-data">__DATA__</script>
<script>
(function(){
  var D = JSON.parse(document.getElementById('eng-data').textContent);
  var LABELS = D.labels, ROWS = D.rows;
  var counts = {}; ROWS.forEach(function(r){counts[r.fmt]=(counts[r.fmt]||0)+1;});
  var fmts = Object.keys(LABELS).filter(function(f){return counts[f];});
  var active = 'ALL';
  function esc(s){return String(s==null?'':s).replace(/[&<>]/g,function(c){return({'&':'&amp;','<':'&lt;','>':'&gt;'})[c];});}
  function circ(i){return '①②③④⑤⑥'[i]||('['+i+']');}
  var fbar = document.getElementById('eng-filter');
  function chip(key,label){
    var b=document.createElement('button');
    b.textContent=label; b.style.cssText='font-size:13px;padding:5px 11px;border-radius:var(--border-radius-md);border:0.5px solid var(--color-border-secondary);cursor:pointer;background:transparent;color:var(--color-text-secondary);';
    b.onclick=function(){active=key;render();paint();};
    b.dataset.key=key; return b;
  }
  fbar.appendChild(chip('ALL','すべて ('+ROWS.length+')'));
  fmts.forEach(function(f){fbar.appendChild(chip(f, LABELS[f].split(' ')[0]+' ('+counts[f]+')'));});
  function paint(){
    Array.prototype.forEach.call(fbar.children,function(b){
      var on=b.dataset.key===active;
      b.style.background=on?'var(--color-background-info)':'transparent';
      b.style.color=on?'var(--color-text-info)':'var(--color-text-secondary)';
      b.style.borderColor=on?'var(--color-border-info)':'var(--color-border-tertiary)';
    });
  }
  var list=document.getElementById('eng-list');
  function qBlock(q){
    var wrap=document.createElement('div');
    wrap.style.cssText='margin-top:12px;border-top:0.5px solid var(--color-border-tertiary);padding-top:10px;';
    var stem=document.createElement('div');
    stem.style.cssText='font-size:14px;font-weight:500;margin-bottom:8px;white-space:pre-wrap;line-height:1.6;';
    stem.innerHTML=esc(q.stem)+' <span style="font-size:11px;color:var(--color-text-tertiary);font-weight:400;">['+esc(q.unit)+']</span>';
    wrap.appendChild(stem);
    q.choices.forEach(function(c,i){
      var ok=i===q.answer;
      var row=document.createElement('div');
      row.style.cssText='display:flex;gap:8px;align-items:flex-start;font-size:14px;padding:5px 8px;border-radius:var(--border-radius-md);margin-bottom:3px;line-height:1.55;'+(ok?'background:var(--color-background-success);':'');
      var key=ok?'<i class="ti ti-circle-check" style="color:var(--color-text-success);font-size:16px;" aria-hidden="true"></i>':'<span style="color:var(--color-text-tertiary);">'+circ(i)+'</span>';
      row.innerHTML='<span style="flex:0 0 18px;text-align:center;">'+key+'</span><span style="color:'+(ok?'var(--color-text-success)':'var(--color-text-primary)')+';">'+esc(c)+'</span>';
      wrap.appendChild(row);
    });
    var ex=document.createElement('div');
    ex.style.cssText='margin-top:6px;font-size:13px;color:var(--color-text-secondary);background:var(--color-background-secondary);padding:8px 10px;border-radius:var(--border-radius-md);white-space:pre-wrap;line-height:1.6;';
    ex.textContent=q.explanation;
    wrap.appendChild(ex);
    return wrap;
  }
  function card(r,idx){
    var c=document.createElement('div');
    c.style.cssText='background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);overflow:hidden;';
    var head=document.createElement('button');
    head.style.cssText='width:100%;text-align:left;display:flex;align-items:center;gap:10px;padding:12px 14px;background:transparent;border:none;cursor:pointer;';
    head.innerHTML='<span style="font-size:12px;color:var(--color-text-info);background:var(--color-background-info);padding:3px 9px;border-radius:var(--border-radius-md);">'+esc(LABELS[r.fmt])+'</span>'
      +'<span style="font-size:13px;color:var(--color-text-secondary);">'+r.questions.length+'問 · '+esc(r.part)+'</span>'
      +'<span style="flex:1;font-size:13px;color:var(--color-text-tertiary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+esc(r.passage.replace(/\\s+/g,' ').slice(0,46))+'…</span>'
      +'<i class="ti ti-chevron-down" data-chev style="font-size:18px;color:var(--color-text-tertiary);" aria-hidden="true"></i>';
    var body=document.createElement('div');
    body.style.cssText='padding:0 14px 14px;display:none;';
    var pa=document.createElement('div');
    pa.style.cssText='font-size:13.5px;white-space:pre-wrap;line-height:1.7;background:var(--color-background-secondary);padding:11px 13px;border-radius:var(--border-radius-md);margin-bottom:6px;';
    pa.textContent=r.passage;
    body.appendChild(pa);
    if(r.figure){ var fg=document.createElement('div'); fg.style.cssText='background:#0e1018;border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-md);padding:10px;margin:6px 0;text-align:center;'; fg.innerHTML=r.figure; body.appendChild(fg); }
    r.questions.forEach(function(q){body.appendChild(qBlock(q));});
    head.onclick=function(){
      var open=body.style.display==='block';
      body.style.display=open?'none':'block';
      head.querySelector('[data-chev]').className='ti ti-chevron-'+(open?'down':'up');
    };
    c.appendChild(head); c.appendChild(body);
    if(idx===0){body.style.display='block';head.querySelector('[data-chev]').className='ti ti-chevron-up';}
    return c;
  }
  function render(){
    list.innerHTML='';
    var shown=ROWS.filter(function(r){return active==='ALL'||r.fmt===active;});
    shown.forEach(function(r,i){list.appendChild(card(r,i));});
  }
  render(); paint();
})();
</script>'''.replace('__DATA__', data_json)

open(OUT, 'w').write(html)
print('wrote', OUT, 'bytes', len(html), '| 大問', len(rows))
