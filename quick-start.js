/**
 * quick-start.js
 *
 * 「⚡ クイックスタート」+「📝 定期テスト勉強モード」セクション用のスタンドアロン JS。
 * 2026-05-21 塾長指示で english-exam.html から quick-start.html に分離。
 *
 * - クイックスタート 5 科目ボタン → QS_SUBJECT_HINT_KEY を localStorage に保存
 *   → english-exam.html?focus=<examId> に遷移 (english-exam.js の focus= ハンドラが
 *   exam-card auto-click → grade picker 表示)。
 * - 定期テスト プルダウン → unit info を URL params に詰めて
 *   english-exam.html?teiki_unit=1&exam_id=...&part_key=...&eiken_grade=...&topic=...
 *   に遷移 (english-exam.js の teiki_unit ハンドラが pickExamSections + startSection 起動)。
 *
 * TEIKI_UNIT_INDEX は元 english-exam.js (line ~4640) からコピー。
 */
(function () {
  'use strict';

  // english-exam.js と同一の localStorage key (subject hint で grade/sections フィルタ参照)
  const QS_SUBJECT_HINT_KEY = 'ai_juku_qs_subject_hint';

  // 定期テスト〜共通テスト基礎の単元インデックス。各単元 = exam_id/part_key/eiken_grade/topic 4 値
  const TEIKI_UNIT_INDEX = {
    '📐 数学 IA (共通テスト基礎)': [
      { label: '二次関数 (最大最小・頂点)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'二次関数' },
      { label: '図形と計量 (正弦/余弦定理)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'図形と計量' },
      { label: 'データの分析 (分散/相関/箱ひげ)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'データ' },
      { label: '場合の数と確率 (順列/組合せ/条件付)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'確率' },
      { label: '整数の性質 (合同式/不定方程式)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'整数' },
      { label: '二次方程式 (判別式・解の公式)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'二次方程式' },
      { label: '円と直線 (接線/弦)', exam_id:'rikei', part_key:'math_1a', eiken_grade:'kyotsu_rikei', topic:'円と直線' },
    ],
    '📐 数学 IIB (共通テスト基礎)': [
      { label: '三角関数 (加法定理/合成)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'三角関数' },
      { label: '指数対数 (方程式/不等式/桁数)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'指数対数' },
      { label: '微分積分 (極値/定積分/面積)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'微積' },
      { label: '数列 (等差/等比/漸化式)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'数列' },
      { label: 'ベクトル (内積/成分/空間)', exam_id:'rikei', part_key:'math_2b', eiken_grade:'kyotsu_rikei', topic:'ベクトル' },
    ],
    '⚛️ 物理基礎': [
      { label: '運動 (等加速度/自由落下)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'運動' },
      { label: '力 (F=ma/摩擦/円運動)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'力' },
      { label: '仕事とエネルギー', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'エネルギー' },
      { label: '熱 (比熱/熱効率)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'熱' },
      { label: '波 (音波/光波)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'波' },
      { label: '電気回路 (オーム法則/電力)', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'電気' },
      { label: '運動量と力積', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'運動量' },
      { label: '単振動', exam_id:'rikei', part_key:'phys_basic', eiken_grade:'kyotsu_rikei', topic:'単振動' },
    ],
    '🧪 化学基礎': [
      { label: 'mol 計算 (物質量)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'mol' },
      { label: '原子の構造と周期表', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'周期表' },
      { label: '化学結合 (イオン/共有)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'結合' },
      { label: '酸と塩基 (pH/中和)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'酸塩基' },
      { label: '酸化還元 (滴定含む)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'酸化還元' },
      { label: '化学反応 (反応式/量的関係)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'反応' },
      { label: '熱化学 (燃焼熱/ヘスの法則)', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'熱化学' },
      { label: '反応速度', exam_id:'rikei', part_key:'chem_basic', eiken_grade:'kyotsu_rikei', topic:'反応速度' },
    ],
    '🧬 生物基礎': [
      { label: '細胞 (小器官/構造)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'細胞' },
      { label: 'DNA (転写/翻訳/複製)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'DNA' },
      { label: '体内環境 (恒常性/腎臓/肝臓)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'体内環境' },
      { label: '免疫 (自然/獲得/血液型)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'免疫' },
      { label: '生態系 (物質循環/植生遷移)', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'生態系' },
      { label: 'ATP とエネルギー代謝', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'ATP' },
      { label: '酵素・タンパク質', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'酵素' },
      { label: '自律神経・ホルモン', exam_id:'rikei', part_key:'bio_basic', eiken_grade:'kyotsu_rikei', topic:'自律神経' },
    ],
    '🇬🇧 英語 文法 (定期テスト)': [
      { label: '関係代名詞 (who/which/whose)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'関係' },
      { label: '分詞構文', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'分詞' },
      { label: '仮定法', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'仮定法' },
      { label: '比較', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'比較' },
      { label: '受動態 (完了形含む)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'受動態' },
      { label: '不定詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'不定詞' },
      { label: '時制 (現在完了)', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'時制' },
      { label: '前置詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'前置詞' },
      { label: '接続詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'接続詞' },
      { label: '助動詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'助動詞' },
      { label: '動名詞', exam_id:'daigaku', part_key:'r_grammar', eiken_grade:'teiki', topic:'動名詞' },
    ],
    '📖 英語 長文 (定期テスト)': [
      { label: '長文読解 (教科書系トピック)', exam_id:'daigaku', part_key:'r_long', eiken_grade:'teiki', topic:'' },
    ],
    '✉️ 英語 実用短文 (定期テスト)': [
      { label: '実用文 (案内/メール/広告)', exam_id:'daigaku', part_key:'r_short', eiken_grade:'teiki', topic:'' },
    ],
    '✍️ 英作文 (定期テスト)': [
      { label: '英作文 (40-60 語の意見)', exam_id:'daigaku', part_key:'w_essay', eiken_grade:'teiki', topic:'' },
    ],
    '📜 古文 (共通テスト基礎)': [
      { label: '動詞の活用', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'活用' },
      { label: '助動詞 (けり/む/べし)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'助動詞' },
      { label: '敬語 (尊敬/謙譲/丁寧)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'敬語' },
      { label: '古典単語', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'単語' },
      { label: '係り結びの法則', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'係り結び' },
      { label: '識別問題 (に/なむ)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'識別' },
      { label: '読解 (竹取/枕草子/平家)', exam_id:'bunkei', part_key:'kobun', eiken_grade:'kobun_kyotsu', topic:'読解' },
    ],
    '🀄 漢文 (共通テスト基礎)': [
      { label: '返り点 (レ点/一二点)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'返り点' },
      { label: '書き下し文', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'書き下し' },
      { label: '再読文字', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'再読文字' },
      { label: '句法 (使役/受身/反語/比較)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'句法' },
      { label: '読解 (論語/孟子/史記)', exam_id:'bunkei', part_key:'kanbun', eiken_grade:'kanbun_kyotsu', topic:'読解' },
    ],
    '🗾 日本史 (共通テスト基礎)': [
      { label: '古代 (大化の改新/律令制)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'古代' },
      { label: '中世 (鎌倉/室町/応仁の乱)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'中世' },
      { label: '近世 (江戸/鎖国/享保改革)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'近世' },
      { label: '近代 (明治維新/自由民権)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'近代' },
      { label: '現代 (戦後復興/高度経済成長)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'現代' },
      { label: '文化史 (国風/天平/化政)', exam_id:'bunkei', part_key:'nihonshi', eiken_grade:'nihonshi_kyotsu', topic:'文化' },
    ],
    '🌍 世界史 (共通テスト基礎)': [
      { label: '古代 (ギリシア/ローマ)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'古代' },
      { label: '中世 (十字軍/百年戦争)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'中世' },
      { label: 'イスラーム史', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'イスラーム' },
      { label: 'アジア (中国通史/インド)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'中国' },
      { label: '近代 (フランス革命/産業革命)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'近代' },
      { label: '現代 (冷戦/中東/グローバル化)', exam_id:'bunkei', part_key:'sekaishi', eiken_grade:'sekaishi_kyotsu', topic:'現代' },
    ],
    '🗺 地理 (共通テスト基礎)': [
      { label: '気候 (ケッペン区分)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'気候' },
      { label: '地形 (プレート/河川/バイオーム)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'地形' },
      { label: '人口・都市 (メガシティ)', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'人口' },
      { label: '農業・食料', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'農業' },
      { label: '工業・鉱産資源', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'工業' },
      { label: '環境問題・エネルギー', exam_id:'bunkei', part_key:'chiri', eiken_grade:'chiri_kyotsu', topic:'環境' },
    ],
    '⚖️ 公民 (共通テスト基礎)': [
      { label: '憲法 (三大原則/9条)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'憲法' },
      { label: '三権分立 (国会/内閣/裁判所)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'三権' },
      { label: '基本的人権', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'人権' },
      { label: '地方自治・選挙', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'地方' },
      { label: '経済 (需給/GDP/金融)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'経済' },
      { label: '国際政治 (国連/EU)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'国際' },
      { label: '倫理 (思想家)', exam_id:'bunkei', part_key:'kouminka', eiken_grade:'kouminka_kyotsu', topic:'倫理' },
    ],
  };

  document.addEventListener('DOMContentLoaded', () => {
    // ---------- クイックスタート 5 科目ボタン ----------
    // プルダウン toggle (▾ ボタン)
    document.querySelectorAll('.qs-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const dropdown = btn.closest('.qs-dropdown');
        const menu = dropdown ? dropdown.querySelector('.qs-menu') : null;
        if (!menu) return;
        document.querySelectorAll('.qs-menu').forEach(m => { if (m !== menu) m.hidden = true; });
        document.querySelectorAll('.qs-toggle').forEach(t => { if (t !== btn) t.setAttribute('aria-expanded', 'false'); });
        const willOpen = menu.hidden;
        menu.hidden = !willOpen;
        btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      });
    });

    // document クリックで全 menu を閉じる
    document.addEventListener('click', (e) => {
      if (e.target.closest('.qs-dropdown')) return;
      document.querySelectorAll('.qs-menu').forEach(m => { m.hidden = true; });
      document.querySelectorAll('.qs-toggle').forEach(t => t.setAttribute('aria-expanded', 'false'));
    });

    // 全 [data-qs-exam] 要素を bind → english-exam.html?focus=<examId> に遷移
    document.querySelectorAll('[data-qs-exam]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const examId = btn.dataset.qsExam;
        if (!examId) return;
        const subject = btn.dataset.qsSubject;
        try {
          if (subject) localStorage.setItem(QS_SUBJECT_HINT_KEY, subject);
          else localStorage.removeItem(QS_SUBJECT_HINT_KEY);
        } catch (_) { /* localStorage 不可ブラウザ無視 */ }
        window.location.href = 'english-exam.html?focus=' + encodeURIComponent(examId);
      });
    });

    // ---------- 定期テスト 単元プルダウン ----------
    const subjSel = document.getElementById('teikiSubjectSel');
    const unitSel = document.getElementById('teikiUnitSel');
    const goBtn = document.getElementById('teikiUnitGo');
    if (!subjSel || !unitSel || !goBtn) return;

    // 科目 select を populate
    Object.keys(TEIKI_UNIT_INDEX).forEach(subj => {
      const opt = document.createElement('option');
      opt.value = subj; opt.textContent = subj;
      subjSel.appendChild(opt);
    });
    subjSel.addEventListener('change', () => {
      const subj = subjSel.value;
      unitSel.innerHTML = '<option value="">-- 単元を選択 --</option>';
      if (!subj || !TEIKI_UNIT_INDEX[subj]) {
        unitSel.disabled = true;
        goBtn.disabled = true;
        return;
      }
      TEIKI_UNIT_INDEX[subj].forEach((u, i) => {
        const opt = document.createElement('option');
        opt.value = String(i);
        opt.textContent = u.label;
        unitSel.appendChild(opt);
      });
      unitSel.disabled = false;
      goBtn.disabled = true;
    });
    unitSel.addEventListener('change', () => {
      goBtn.disabled = !unitSel.value;
    });
    goBtn.addEventListener('click', () => {
      const subj = subjSel.value;
      const idx = parseInt(unitSel.value, 10);
      if (!subj || isNaN(idx)) return;
      const unit = (TEIKI_UNIT_INDEX[subj] || [])[idx];
      if (!unit) return;
      const params = new URLSearchParams({
        teiki_unit: '1',
        exam_id: unit.exam_id,
        part_key: unit.part_key,
        eiken_grade: unit.eiken_grade,
        topic: unit.topic || '',
      });
      window.location.href = 'english-exam.html?' + params.toString();
    });
  });
})();
