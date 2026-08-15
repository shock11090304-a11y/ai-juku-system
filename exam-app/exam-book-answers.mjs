// =============================================================================
// 冊子受験画面 — 答案ペイン
//
// ★ 選択肢の値を作るのは choiceValue() **ただ 1 箇所**。
//   DB の correct_answer は 1 起算の数字文字列なので、0 起算や 'A' / '①' を
//   どこか 1 箇所で作ると **全員 0 点**になる。そしてそれを落とす検査は
//   採点 RPC にもスキーマにも無い (形式は正しいので通ってしまう)。
//
// ★ 進捗は attempts/RPC の answered_count を使わない。
//   answers 行は開始時に全問ぶん先に作るので、answered_count は常に満点分になる。
//   「何問答えたか」は user_answer が空でない件数を **自分で数える**。
// =============================================================================

/** 選択肢 i (0 起算) の保存値。★ここ以外で選択肢の値文字列を作らない。 */
export function choiceValue(i) { return String(i + 1); }

const NO_PAGE = 'none';
const FOLLOW_PAUSE_MS = 5000;    // 生徒が手で動かしたら自動追従を止める時間

const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};

export class AnswerPane {
  /**
   * @param {HTMLElement} host
   * @param {object} cb
   *   cb.onChange(qid, value, sec)  入力が変わった (保存キューへ)
   *   cb.onJump(page)               設問から冊子のページへ飛ぶ
   */
  constructor(host, cb = {}) {
    this.host = host;
    this.cb = { onChange: () => {}, onJump: () => {}, ...cb };
    this.qs = [];                 // student_questions の行 (表示順)
    this.cards = new Map();       // qid -> element
    this.values = new Map();      // qid -> string|null
    this.secs = new Map();        // qid -> 累計秒
    this.readonly = false;
    this.activeQid = null;
    this.activeAt = 0;
    this.followUntil = 0;

    this.head = el('div', 'ans-head');
    this.list = el('div', 'ans-list');
    host.innerHTML = '';
    host.appendChild(this.head);
    host.appendChild(this.list);

    // 生徒が答案ペインを手で動かしている間は、冊子スクロールへの追従を止める。
    // 止めないと「触ると勝手に戻る」ので、震えているように見える。
    const pause = () => { this.followUntil = Date.now() + FOLLOW_PAUSE_MS; };
    this.list.addEventListener('pointerdown', pause);
    this.list.addEventListener('wheel', pause, { passive: true });
    this.list.addEventListener('touchmove', pause, { passive: true });
  }

  // --- 生成 -------------------------------------------------------------------
  build(questions) {
    this.qs = [...questions].sort((a, b) => a.number - b.number);
    this.cards.clear();
    this.list.innerHTML = '';

    // ★ page が NULL の設問は「ページ指定なし」として **常に先頭**に出す。
    //   「このページの設問だけ」で絞ると永久に見えなくなり、解答できないまま提出される。
    const groups = new Map([[NO_PAGE, []]]);
    for (const q of this.qs) {
      const key = q.page == null ? NO_PAGE : String(q.page);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(q);
    }
    const keys = [NO_PAGE, ...[...groups.keys()].filter((k) => k !== NO_PAGE)
      .sort((a, b) => Number(a) - Number(b))];

    for (const key of keys) {
      const items = groups.get(key) || [];
      if (!items.length) continue;
      const sec = el('section', 'qgroup');
      sec.dataset.page = key;
      const h = el('h3', 'qgroup-h', key === NO_PAGE ? 'ページ指定なし' : `${key} ページ`);
      if (key !== NO_PAGE) {
        h.tabIndex = 0;
        h.addEventListener('click', () => this.cb.onJump(Number(key)));
      }
      sec.appendChild(h);
      for (const q of items) sec.appendChild(this._card(q));
      this.list.appendChild(sec);
    }
    this._renderHead();
  }

  _card(q) {
    const card = el('article', 'q');
    card.dataset.qid = q.id;
    card.dataset.number = String(q.number);
    if (q.page != null) card.dataset.page = String(q.page);

    const head = el('div', 'q-head');
    head.appendChild(el('span', 'q-no', `問 ${q.number}`));
    if (q.points > 1) head.appendChild(el('span', 'q-pt', `${q.points}点`));
    if (q.page != null) {
      const jump = el('button', 'q-jump', `p.${q.page}`);
      jump.type = 'button';
      jump.addEventListener('click', () => this.cb.onJump(q.page));
      head.appendChild(jump);
    }
    card.appendChild(head);

    // 設問が「アクティブ」な間の秒数を time_spent_sec に積む
    card.addEventListener('pointerdown', () => this._activate(q.id));
    card.addEventListener('focusin', () => this._activate(q.id));

    card.appendChild(q.answer_type === 'choice' ? this._choices(q) : this._short(q));
    card.appendChild(el('div', 'q-res'));
    this.cards.set(q.id, card);
    return card;
  }

  _choices(q) {
    const box = el('div', 'q-choices');
    box.setAttribute('role', 'radiogroup');
    box.setAttribute('aria-label', `問 ${q.number} の選択肢`);
    const n = Math.max(2, Number(q.choice_count) || 4);
    for (let i = 0; i < n; i++) {
      const v = choiceValue(i);                 // ★ 唯一の生成箇所を通す
      const b = el('button', 'choice', v);
      b.type = 'button';
      b.dataset.value = v;
      b.setAttribute('role', 'radio');
      b.setAttribute('aria-checked', 'false');
      b.addEventListener('click', () => {
        if (this.readonly) return;
        // 再タップで解除できる (誤タップを消せないと、消すために別を選ぶしかなくなる)
        const cur = this.values.get(q.id);
        this._commit(q.id, cur === v ? null : v);
      });
      box.appendChild(b);
    }
    return box;
  }

  _short(q) {
    const box = el('div', 'q-short');
    const inp = el('input', 'short');
    inp.type = 'text';
    // ★ iOS の自動修正は英単語を別の語に化けさせる。3 つとも必須。
    inp.autocapitalize = 'off';
    inp.setAttribute('autocorrect', 'off');
    inp.spellcheck = false;
    inp.autocomplete = 'off';
    inp.setAttribute('aria-label', `問 ${q.number} の解答`);
    inp.addEventListener('input', () => {
      if (this.readonly) return;
      this._commit(q.id, inp.value);
    });
    inp.addEventListener('blur', () => {
      if (this.readonly) return;
      this._commit(q.id, inp.value);
    });
    box.appendChild(inp);
    return box;
  }

  // --- 入力 -------------------------------------------------------------------
  _activate(qid) {
    if (this.activeQid === qid) return;
    this._bank();
    this.activeQid = qid;
    this.activeAt = Date.now();
  }

  /** アクティブだった設問の経過秒を積む。 */
  _bank() {
    if (this.activeQid == null) return;
    const add = Math.round((Date.now() - this.activeAt) / 1000);
    if (add > 0) this.secs.set(this.activeQid, (this.secs.get(this.activeQid) || 0) + add);
    this.activeAt = Date.now();
  }

  /** タブが隠れた / 提出した。計測を止める。 */
  pauseTiming() { this._bank(); this.activeQid = null; }

  _commit(qid, value) {
    const v = (value == null || value === '') ? null : String(value);
    this.values.set(qid, v);
    this._bank();
    this._paint(qid);
    this._renderHead();
    this.cb.onChange(qid, v, this.secs.get(qid) || 0);
  }

  /** 復元 (サーバから読んだ値を入れる)。★ onChange は呼ばない。 */
  setValue(qid, value, sec) {
    this.values.set(qid, (value == null || value === '') ? null : String(value));
    if (sec != null) this.secs.set(qid, Number(sec) || 0);
    this._paint(qid);
    this._renderHead();
  }

  _paint(qid) {
    const card = this.cards.get(qid);
    if (!card) return;
    const v = this.values.get(qid) || null;
    card.classList.toggle('answered', v != null);
    for (const b of card.querySelectorAll('.choice')) {
      const on = b.dataset.value === v;
      b.classList.toggle('on', on);
      b.setAttribute('aria-checked', on ? 'true' : 'false');
    }
    const inp = card.querySelector('input.short');
    if (inp && inp.value !== (v || '')) inp.value = v || '';
  }

  // --- 進捗 -------------------------------------------------------------------
  /** ★ 自前で数える (answered_count は使えない — §9.2)。 */
  progress() {
    let answered = 0;
    for (const q of this.qs) if (this.values.get(q.id) != null) answered++;
    return { answered, total: this.qs.length };
  }

  /** 未解答の設問。提出確認に出す。 */
  unanswered() {
    return this.qs.filter((q) => this.values.get(q.id) == null)
      .map((q) => ({ id: q.id, number: q.number, page: q.page }));
  }

  _renderHead() {
    const { answered, total } = this.progress();
    this.head.innerHTML = '';
    this.head.appendChild(el('span', 'ans-count', `解答 ${answered} / ${total}`));
    const bar = el('div', 'ans-bar');
    const fill = el('div', 'ans-bar-fill');
    fill.style.width = total ? `${Math.round((answered / total) * 100)}%` : '0%';
    bar.appendChild(fill);
    this.head.appendChild(bar);
  }

  // --- 冊子とページ連動 -------------------------------------------------------
  /** 設問カードまでスクロールして目立たせる。 */
  focusQuestion(qid) {
    const card = this.cards.get(qid);
    if (!card) return;
    this.followUntil = Date.now() + FOLLOW_PAUSE_MS;
    card.scrollIntoView({ block: 'center', behavior: 'smooth' });
    card.classList.add('hl');
    setTimeout(() => card.classList.remove('hl'), 1600);
  }

  /** 冊子側のスクロールから呼ぶ。手で動かした直後は何もしない。 */
  followPage(page) {
    if (Date.now() < this.followUntil) return;
    const sec = this.list.querySelector(`.qgroup[data-page="${page}"]`);
    if (!sec) return;
    for (const s of this.list.querySelectorAll('.qgroup.cur')) s.classList.remove('cur');
    sec.classList.add('cur');
    // .ans-list は position: relative なので offsetTop がそのままスクロール量になる
    this.list.scrollTo({ top: Math.max(0, sec.offsetTop - 8), behavior: 'smooth' });
  }

  // --- 状態 -------------------------------------------------------------------
  setReadonly(on) {
    this.readonly = !!on;
    this.host.classList.toggle('readonly', this.readonly);
    for (const inp of this.list.querySelectorAll('input.short')) inp.disabled = this.readonly;
    for (const b of this.list.querySelectorAll('.choice')) b.disabled = this.readonly;
    if (this.readonly) this.pauseTiming();
  }

  // --- 結果 (復習モード) ------------------------------------------------------
  /**
   * ★ 引数の rows は **提出直後にメモリへ取り込んだもの**を渡し続ける。
   *   「もう一度受験する」を押すと student_questions.revealed がブック単位で false に
   *   落ちるので、再取得すると ○× だけ残って解説が空になる (一番分かりにくい壊れ方)。
   * @param {Array} rows student_questions の行 (correct_answer / explanation を含む)
   * @param {Map}  answers qid -> {user_answer, is_correct}
   */
  showResult(rows, answers) {
    this.setReadonly(true);
    const byId = new Map(rows.map((r) => [r.id, r]));
    let revealed = 0;

    for (const q of this.qs) {
      const card = this.cards.get(q.id);
      if (!card) continue;
      const r = byId.get(q.id) || {};
      const a = answers.get(q.id) || {};
      const box = card.querySelector('.q-res');
      box.innerHTML = '';

      const ok = a.is_correct === true;
      card.classList.toggle('correct', ok);
      card.classList.toggle('wrong', a.is_correct === false);
      box.appendChild(el('div', 'res-mark', ok ? '正解' : '不正解'));

      if (r.correct_answer != null) {
        revealed++;
        box.appendChild(el('div', 'res-ans', `正答: ${r.correct_answer}`));
        if (r.accepted_answers && r.accepted_answers.length) {
          box.appendChild(el('div', 'res-alt', `別解: ${r.accepted_answers.join(' / ')}`));
        }
        if (r.explanation) {
          const ex = el('div', 'res-exp');
          ex.textContent = r.explanation;      // ★ Markdown は解釈しない (HTML 注入を作らない)
          box.appendChild(ex);
        }
      }
      // 選択式は正答の選択肢に印を付ける
      if (r.correct_answer != null) {
        for (const b of card.querySelectorAll('.choice')) {
          if (b.dataset.value === String(r.correct_answer)) b.classList.add('ans');
        }
      }
    }

    if (revealed === 0 && rows.length) {
      const note = el('div', 'res-hidden',
        '正解と解説は、このブックの受験中の答案がすべて提出されると表示されます。');
      this.list.prepend(note);
    }
    return revealed;
  }
}
