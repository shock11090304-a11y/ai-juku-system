// =============================================================================
// 冊子受験画面 — 保存キュー / ローカル写し / 答案の I/O
//
// ★ この画面で「消えた」が起きるとしたら、ほぼ全部この 1 ファイルの中。
//   設計 (docs/book-exam.md §8) の 4 つの不変条件をここで守る:
//
//   1. **ページ単位・単一飛行**。同じページに 2 本同時に飛ばさない。
//      飛ばすと後着が先着を上書きして、間に足した線が消える。
//   2. **CAS (updated_at)**。update は必ず `.eq('updated_at', 既知の版)` を付け、
//      **返却行数**で判定する。0 行でもエラーにならないので、error だけ見ると
//      「保存しました」と出しながら 1 文字も書かれない状態が作れる。
//   3. **エラーは 4 分岐**。全部リトライにすると 1 点の NaN で永久に叩き続けて
//      試験が終われなくなる。全部あきらめると黙って消える。
//   4. **ローカル写しは pointerup で同期に書く**。守りたい窓は
//      「サーバに入る前に iOS がタブを捨てる」で、それはアイドル 1.2 秒の中にある。
//      flush 時に書いたのでは間に合わない。
// =============================================================================
import { validateStrokes, parseStrokes, mergeAppend } from '/exam-book-model.mjs?v=1';
import { sb, run, KIND } from '/exam-book-sb.mjs?v=1';

const IDLE_MS = 1200;             // 最終描画からこれだけ静かなら送る
const FORCE_MS = 8000;            // 書き続けていても最初の dirty からこれで必ず送る
const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000, 30000];
const LOCAL_INLINE_MAX = 256 * 1024;   // これを超えたら写しは tail 追記方式へ
const ANSWER_DEBOUNCE_MS = 600;

const nop = () => {};

// =============================================================================
// ローカル写し
//
// ★ これが唯一の実質的な保険。pagehide での送信は当てにできない
//   (sendBeacon は Authorization を付けられず 401、keepalive は 64KB 上限)。
// =============================================================================
export class LocalCopy {
  /** @param {string} attemptId @param {(msg:string)=>void} onFail 控えが取れない事を画面に出す */
  constructor(attemptId, onFail = nop) {
    this.attempt = attemptId;
    this.onFail = onFail;
    this.big = new Set();          // tail 追記に切り替えたページ
    this.broken = false;           // 一度でも書けなかった (画面に出したら黙る)
    this.ls = (() => {
      try { const s = globalThis.localStorage; s.getItem('_'); return s; } catch (_) { return null; }
    })();
    if (!this.ls) this._fail('この端末では控えを保存できません (プライベートブラウズ?)');
  }

  _key(page) { return `ink:${this.attempt}:${page}`; }
  _tail(page) { return `ink:${this.attempt}:${page}:tail`; }
  _meta() { return `inkmeta:${this.attempt}`; }

  _fail(msg) {
    if (this.broken) return;
    this.broken = true;
    this.onFail(msg);
  }

  /** 他の attempt の写しを古い順に捨てて場所を空ける。★今の attempt には触らない。 */
  _evict() {
    if (!this.ls) return false;
    const others = [];
    for (let i = 0; i < this.ls.length; i++) {
      const k = this.ls.key(i);
      const m = k && k.match(/^inkmeta:(.+)$/);
      if (m && m[1] !== this.attempt) others.push({ id: m[1], at: Number(this.ls.getItem(k)) || 0 });
    }
    if (!others.length) return false;
    others.sort((a, b) => a.at - b.at);
    const victim = others[0].id;
    const doomed = [];
    for (let i = 0; i < this.ls.length; i++) {
      const k = this.ls.key(i);
      if (k && (k.startsWith(`ink:${victim}:`) || k === `inkmeta:${victim}`)) doomed.push(k);
    }
    for (const k of doomed) this.ls.removeItem(k);
    return doomed.length > 0;
  }

  _set(key, value) {
    if (!this.ls) return false;
    for (let attempt = 0; attempt < 4; attempt++) {
      try {
        this.ls.setItem(key, value);
        this.ls.setItem(this._meta(), String(Date.now()));
        return true;
      } catch (e) {
        // QuotaExceededError。他の答案の控えを捨てて場所を作る。
        if (!this._evict()) {
          this._fail('端末側の控えが取れていません (保存領域が一杯です)');
          return false;
        }
      }
    }
    this._fail('端末側の控えが取れていません');
    return false;
  }

  /**
   * ★ pointerup から **同期で**呼ぶ。ここで await を挟まない。
   * @param {number} page @param {Array} strokes ページ全量
   */
  write(page, strokes) {
    if (!this.ls) return;
    if (this.big.has(page)) {
      // 大きいページ: 毎回 300KB を stringify するとペンがカクつくので最後の 1 本だけ足す。
      const last = strokes[strokes.length - 1];
      if (!last) return;
      const cur = this.ls.getItem(this._tail(page));
      const add = JSON.stringify(last);
      this._set(this._tail(page), cur ? cur + '\n' + add : add);
      return;
    }
    const body = JSON.stringify({ v: 1, strokes });
    if (body.length > LOCAL_INLINE_MAX) {
      // ここで一度だけ本体を書き、以後は追記に切り替える。
      this.big.add(page);
      this._set(this._key(page), body);
      this.ls.removeItem(this._tail(page));
      return;
    }
    this._set(this._key(page), body);
  }

  /** サーバ保存が確定した。★ここでしか消さない。 */
  clear(page) {
    if (!this.ls) return;
    this.ls.removeItem(this._key(page));
    this.ls.removeItem(this._tail(page));
    this.big.delete(page);
  }

  /**
   * 復帰時。サーバの内容にこの端末の未送信分を重ねた候補を返す。
   * @returns {{hasLocal:boolean, strokes:Array}}
   */
  recover(page, serverStrokes) {
    if (!this.ls) return { hasLocal: false, strokes: serverStrokes };
    const body = this.ls.getItem(this._key(page));
    const tail = this.ls.getItem(this._tail(page));
    if (!body && !tail) return { hasLocal: false, strokes: serverStrokes };

    let base = serverStrokes;
    if (body) {
      try {
        const p = parseStrokes(JSON.parse(body));
        if (p.ok) base = p.strokes;
      } catch (_) { /* 壊れた写しは無視して サーバ側を使う */ }
    }
    const extra = [];
    for (const line of (tail || '').split('\n')) {
      if (!line.trim()) continue;
      try { extra.push(JSON.parse(line)); } catch (_) { /* 途中で切れた行は捨てる */ }
    }
    const v = validateStrokes(extra);
    const merged = mergeAppend(v.ok ? v.payload.strokes : [], base);
    return { hasLocal: true, strokes: merged };
  }

  /** 提出後に「送れなかったページ」が残っているか (結果画面に出す)。★自動では消さない。 */
  leftovers() {
    if (!this.ls) return [];
    const out = new Set();
    for (let i = 0; i < this.ls.length; i++) {
      const k = this.ls.key(i);
      const m = k && k.match(new RegExp(`^ink:${this.attempt}:(\\d+)(:tail)?$`));
      if (m) out.add(Number(m[1]));
    }
    return [...out].sort((a, b) => a - b);
  }
}

// =============================================================================
// 同一ブラウザの 2 タブ目を読み取り専用にする
//
// ★ 別端末は CAS が捕まえるが、同一ブラウザの 2 タブは同じ localStorage を共有するので
//   写しが混ざる。先に開いていた方を書き手にする。
// =============================================================================
export class TabLock {
  constructor(attemptId, onDemote = nop) {
    this.since = Date.now();
    this.leader = true;
    this.onDemote = onDemote;
    try {
      this.ch = new BroadcastChannel('exam-book:' + attemptId);
    } catch (_) { this.ch = null; return; }
    this.ch.onmessage = (e) => {
      const m = e.data || {};
      if (m.t === 'hello') {
        if (this.leader) this.ch.postMessage({ t: 'here', since: this.since });
      } else if (m.t === 'here' && this.leader && m.since < this.since) {
        this.leader = false;
        this.onDemote();
      }
    };
    this.ch.postMessage({ t: 'hello', since: this.since });
  }
  close() { try { this.ch && this.ch.close(); } catch (_) {} }
}

// =============================================================================
// annotations の保存キュー
// =============================================================================
export class InkQueue {
  /**
   * @param {object} o
   * @param {string} o.attemptId
   * @param {(page:number)=>Array} o.getStrokes ページ全量を返す (モデルから)
   * @param {LocalCopy} o.local
   * @param {object} o.on コールバック集
   *   on.pending(n)        未保存ページ数が変わった
   *   on.frozen(reason)    提出前の 42501。全ページ凍結して知らせる
   *   on.invalid(page,msg) 23514。そのページを凍結して赤で知らせる
   *   on.conflict(page)    CAS 0 行。上書きする**前**に検出した
   *   on.saved(page)
   */
  constructor({ attemptId, getStrokes, local, on = {} }) {
    this.attempt = attemptId;
    this.getStrokes = getStrokes;
    this.local = local;
    this.on = {
      pending: nop, frozen: nop, invalid: nop, conflict: nop, saved: nop, ...on,
    };
    this.pages = new Map();
    this.submitted = false;     // 提出後は 42501 を「正常」として静かに扱う
    this.stopped = false;       // 全停止 (提出手順の FREEZE / 凍結)
  }

  _st(page) {
    if (!this.pages.has(page)) {
      this.pages.set(page, {
        page, dirty: false, inFlight: null, again: false, frozen: false,
        known: null, exists: false, tries: 0,
        idleT: null, forceT: null, backoffT: null, invalidRetried: false,
      });
    }
    return this.pages.get(page);
  }

  /** サーバから読み終えたページの版を記録する。★これを呼ぶ前に書かせない (§8.1 loaded)。 */
  markLoaded(page, updatedAt) {
    const st = this._st(page);
    st.known = updatedAt || null;
    st.exists = !!updatedAt;
  }

  /** 未保存ページ数。ヘッダに出し続ける。 */
  pending() {
    let n = 0;
    for (const st of this.pages.values()) if (st.dirty || st.inFlight) n++;
    return n;
  }
  _emitPending() { this.on.pending(this.pending()); }

  /**
   * ★ Ink の pointerup から呼ばれる唯一の入口。
   *   ① ローカル写しを **同期で** 書く ② dirty ③ タイマー
   */
  touch(page) {
    const st = this._st(page);
    if (st.frozen || this.stopped) return;
    this.local.write(page, this.getStrokes(page));   // ← 同期。await を挟まない
    st.dirty = true;
    this._emitPending();
    this._schedule(st);
  }

  _schedule(st) {
    if (this.stopped || st.frozen) return;
    if (st.idleT) clearTimeout(st.idleT);
    st.idleT = setTimeout(() => { st.idleT = null; this.flush(st.page); }, IDLE_MS);
    if (!st.forceT) {
      st.forceT = setTimeout(() => { st.forceT = null; this.flush(st.page); }, FORCE_MS);
    }
  }

  _clearTimers(st) {
    for (const k of ['idleT', 'forceT', 'backoffT']) {
      if (st[k]) { clearTimeout(st[k]); st[k] = null; }
    }
  }

  /** そのページを即時保存。単一飛行なので飛行中なら予約だけする。 */
  flush(page) {
    const st = this._st(page);
    this._clearTimers(st);
    if (this.stopped || st.frozen || !st.dirty) return st.inFlight || Promise.resolve();
    if (st.inFlight) { st.again = true; return st.inFlight; }
    st.inFlight = this._send(st).finally(() => {
      st.inFlight = null;
      this._emitPending();
      if (st.again && !st.frozen && !this.stopped) { st.again = false; this.flush(st.page); }
    });
    return st.inFlight;
  }

  async _send(st) {
    const page = st.page;
    const v = validateStrokes(this.getStrokes(page));
    if (!v.ok) {
      // 送る前に自分で気づけた。DB に投げない (23514 を食いに行かない)。
      st.dirty = false;
      st.frozen = true;
      this.on.invalid(page, v.reason || '書き込みの形が不正です');
      return;
    }
    st.dirty = false;   // ここから先に足された分は again で拾う

    let res;
    if (st.exists && st.known) {
      // ★ 楽観的排他。updated_at はサーバのトリガが now() で打つ単調な版番号。
      res = await run(
        sb().from('annotations')
          .update({ strokes: v.payload })
          .eq('attempt_id', this.attempt).eq('page', page).eq('updated_at', st.known)
          .select('updated_at'));
    } else {
      res = await run(
        sb().from('annotations')
          .insert({ attempt_id: this.attempt, page, strokes: v.payload })
          .select('updated_at'));
    }

    // --- 成功 ---------------------------------------------------------------
    if (!res.error && res.rows > 0) {
      const row = Array.isArray(res.data) ? res.data[0] : res.data;
      st.known = row && row.updated_at ? row.updated_at : null;
      st.exists = true;
      st.tries = 0;
      st.invalidRetried = false;
      if (!st.dirty && !st.again) this.local.clear(page);   // 追い書きがあるなら控えは残す
      this.on.saved(page);
      return;
    }

    // --- 失敗 ---------------------------------------------------------------
    const kind = res.kind;

    // insert が 23505 = 行は既にある (別タブ/前回の応答落ち)。版を読み直して update へ。
    if (kind === KIND.CONFLICT && !st.exists) {
      const cur = await sb().from('annotations')
        .select('updated_at').eq('attempt_id', this.attempt).eq('page', page).maybeSingle();
      if (cur.data && cur.data.updated_at) {
        st.exists = true;
        st.known = cur.data.updated_at;
        st.dirty = true;
        st.again = true;
        return;
      }
      st.dirty = true;
      this._backoff(st);
      return;
    }

    if (kind === KIND.CONFLICT) {
      // ★ 上書きする**前**に検出できた。自動マージはしない (消した線が戻る)。
      st.dirty = true;
      this._clearTimers(st);
      this.on.conflict(page);
      return;
    }

    if (kind === KIND.FROZEN) {
      if (this.submitted) { this.stopAll(); return; }   // 提出後は正常。静かに止める
      this.stopAll();
      this.on.frozen('別の端末でこの答案が提出されたか、ログインが切れています');
      return;
    }

    if (kind === KIND.INVALID) {
      // validateStrokes を通ったのに DB が拒否した = こちらの検査に穴がある。
      // ★ 再試行は 1 回だけ。ここを無条件リトライにすると試験が終われなくなる。
      if (!st.invalidRetried) {
        st.invalidRetried = true;
        st.dirty = true;
        st.again = true;
        return;
      }
      st.frozen = true;
      this._clearTimers(st);
      this.on.invalid(page, (res.error && res.error.message) || 'DB に拒否されました');
      return;
    }

    // 通信 / 5xx。dirty は落とさない。
    st.dirty = true;
    this._backoff(st);
  }

  _backoff(st) {
    if (this.stopped || st.frozen) return;
    const wait = BACKOFF_MS[Math.min(st.tries, BACKOFF_MS.length - 1)];
    st.tries++;
    if (st.backoffT) clearTimeout(st.backoffT);
    st.backoffT = setTimeout(() => { st.backoffT = null; this.flush(st.page); }, wait);
  }

  /** 競合ダイアログの答え: サーバ側を読み直して版を取り直す。 */
  async refetch(page) {
    const r = await sb().from('annotations')
      .select('strokes, updated_at').eq('attempt_id', this.attempt).eq('page', page).maybeSingle();
    if (r.error) return { ok: false, error: r.error };
    const st = this._st(page);
    st.known = r.data ? r.data.updated_at : null;
    st.exists = !!r.data;
    const p = r.data ? parseStrokes(r.data.strokes) : { ok: true, strokes: [] };
    return { ok: true, strokes: p.ok ? p.strokes : [], legacy: p.legacy === true };
  }

  /** 全ページを即時 flush する。★ベストエフォート。返り値は送り切れなかったページ。 */
  async flushAll(totalMs = 45000) {
    const targets = [...this.pages.values()].filter((s) => (s.dirty || s.inFlight) && !s.frozen);
    if (!targets.length) return [];
    const all = Promise.all(targets.map((s) => {
      s.tries = BACKOFF_MS.length;   // 提出中に長いバックオフへ入らせない
      return this.flush(s.page);
    }));
    let timedOut = false;
    await Promise.race([
      all.catch(() => {}),
      new Promise((r) => setTimeout(() => { timedOut = true; r(); }, totalMs)),
    ]);
    const left = [...this.pages.values()].filter((s) => s.dirty || s.inFlight).map((s) => s.page);
    if (timedOut && !left.length) return [];
    return left.sort((a, b) => a - b);
  }

  /**
   * ★ 提出手順の DRAIN。**予約済みの再送を全部取り消し**、飛行中だけを待つ。
   *   これをしないと RPC の後に届いた再送が 42501 で黙って消える。
   */
  async drain() {
    for (const st of this.pages.values()) { this._clearTimers(st); st.again = false; }
    const flying = [...this.pages.values()].map((s) => s.inFlight).filter(Boolean);
    await Promise.all(flying.map((p) => p.catch(() => {})));
  }

  /** 自動保存を全部止める (提出の FREEZE / 凍結)。 */
  stopAll() {
    this.stopped = true;
    for (const st of this.pages.values()) { this._clearTimers(st); st.again = false; }
  }

  resume() {
    this.stopped = false;
    for (const st of this.pages.values()) if (st.dirty && !st.frozen) this._schedule(st);
  }
}

// =============================================================================
// answers の I/O
//
// ★ upsert は使えない。PostgREST は payload の全列を ON CONFLICT DO UPDATE SET に
//   並べるので attempt_id/question_id が SET に入り、列 grant に無いため
//   **衝突していない初回 insert でも 42501** になる (権限判定はプラン時)。
// =============================================================================

/** 送信オブジェクトを作る唯一の関数。★この 2 列以外を絶対に入れない。 */
export function answerPatch(userAnswer, timeSpentSec) {
  return {
    user_answer: (userAnswer == null || userAnswer === '') ? null : String(userAnswer),
    time_spent_sec: Math.max(0, Math.round(Number(timeSpentSec) || 0)),
  };
}

export class AnswerQueue {
  /**
   * @param {object} o
   * @param {string} o.attemptId
   * @param {object} o.on  on.saved(qid) / on.frozen(msg) / on.error(msg) / on.pending(n)
   */
  constructor({ attemptId, on = {} }) {
    this.attempt = attemptId;
    this.on = { saved: nop, frozen: nop, error: nop, pending: nop, ...on };
    this.want = new Map();     // qid -> {value, sec}
    this.inFlight = new Map(); // qid -> promise
    this.timer = null;
    this.stopped = false;
  }

  pending() { return this.want.size + this.inFlight.size; }

  /**
   * 開始時に不足行だけ insert する。
   * ★ 事前作成は必須。student_questions.revealed は「提出済み attempt にその設問の
   *   answers 行がある」が条件で、行が無い設問は **提出後も永久に解説が出ない**
   *   (提出後は insert も 42501 で塞がる)。
   * @returns {{ok:boolean, created:number, error?:object}}
   */
  async seed(questionIds) {
    for (let round = 0; round < 3; round++) {
      const have = await sb().from('answers')
        .select('question_id').eq('attempt_id', this.attempt);
      if (have.error) return { ok: false, created: 0, error: have.error };
      const known = new Set((have.data || []).map((r) => r.question_id));
      const missing = questionIds.filter((id) => !known.has(id));
      if (!missing.length) return { ok: true, created: 0 };

      const rows = missing.map((id) => ({
        attempt_id: this.attempt, question_id: id, user_answer: null, time_spent_sec: 0,
      }));
      const res = await run(sb().from('answers').insert(rows).select('question_id'));
      if (!res.error) return { ok: true, created: res.rows };
      // 23505 = 別タブが同時に作った。読み直して差分を取り直す。
      if (res.kind !== KIND.CONFLICT) return { ok: false, created: 0, error: res.error };
    }
    return { ok: false, created: 0, error: { message: 'answers 行を用意できませんでした' } };
  }

  /** 入力のたびに呼ぶ。デバウンスして 2 列だけ update する。 */
  set(questionId, value, timeSpentSec) {
    if (this.stopped) return;
    this.want.set(questionId, { value, sec: timeSpentSec });
    this.on.pending(this.pending());
    if (this.timer) clearTimeout(this.timer);
    this.timer = setTimeout(() => { this.timer = null; this.flush(); }, ANSWER_DEBOUNCE_MS);
  }

  /**
   * @param {number} depth 内部用。★ 再帰は 1 段まで。
   *   通信断のとき _write は want に戻すので、無条件に再帰すると
   *   バックオフ無しでサーバを叩き続け、**この await が永久に返らない**
   *   (提出手順の FLUSH_ANSWERS がそこで止まる)。
   */
  async flush(depth = 0) {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    const jobs = [];
    for (const [qid, v] of [...this.want]) {
      this.want.delete(qid);
      if (this.inFlight.has(qid)) { this.want.set(qid, v); continue; }  // 単一飛行
      const p = this._write(qid, v).finally(() => {
        this.inFlight.delete(qid);
        this.on.pending(this.pending());
      });
      this.inFlight.set(qid, p);
      jobs.push(p);
    }
    await Promise.all(jobs.map((p) => p.catch(() => {})));
    // 飛行中に上書きされた分をもう一度だけ拾う
    if (depth === 0 && this.want.size && !this.stopped) {
      const again = [...this.want.keys()].filter((q) => !this.inFlight.has(q));
      if (again.length) await this.flush(1);
    }
  }

  async _write(questionId, v) {
    const res = await run(
      sb().from('answers')
        .update(answerPatch(v.value, v.sec))
        .eq('attempt_id', this.attempt).eq('question_id', questionId)
        .select('question_id'));

    if (!res.error && res.rows > 0) { this.on.saved(questionId); return true; }

    if (res.kind === KIND.FROZEN) {
      this.stopped = true;
      this.on.frozen('この答案はもう変更できません (提出済みか、別のユーザです)');
      return false;
    }
    if (res.kind === KIND.CONFLICT) {
      // ★ 0 行 = 行が無いか権限が無い。**「保存しました」と出さない。**
      this.want.set(questionId, v);
      this.on.error('解答を保存できていません');
      return false;
    }
    if (res.kind === KIND.INVALID) {
      this.on.error('解答の形式が受け付けられませんでした');
      return false;
    }
    this.want.set(questionId, v);          // 通信断。次の flush で拾う
    this.on.error('通信できていません (解答は未保存です)');
    return false;
  }

  /**
   * ★ 提出手順の RECONCILE。行数を照合して不足分を補う。
   *   飛ばすと、その設問は無得点・復習キュー不参加・解説が永久に出ない の三重障害。
   */
  async reconcile(questionIds) {
    const r = await this.seed(questionIds);
    if (!r.ok) return r;
    const check = await sb().from('answers')
      .select('question_id').eq('attempt_id', this.attempt);
    if (check.error) return { ok: false, created: r.created, error: check.error };
    const n = (check.data || []).length;
    if (n < questionIds.length) {
      return { ok: false, created: r.created,
               error: { message: `解答行が ${n} 件しかありません (設問は ${questionIds.length} 件)` } };
    }
    return { ok: true, created: r.created };
  }
}

// =============================================================================
// 提出 (RPC)
// =============================================================================

/**
 * @returns {{state:'ok'|'blocked'|'retry', result?:object, message?:string}}
 */
export async function submitAttempt(attemptId) {
  const { data, error } = await sb().rpc('submit_attempt', { p_attempt: attemptId });
  if (!error) return { state: 'ok', result: data };

  const kind = classifyRpc(error);
  if (kind === KIND.FROZEN) {
    // 往復で応答だけ落ちた可能性がある。提出済みかを見てから決める。
    const chk = await sb().from('attempts')
      .select('submitted_at, score, question_count').eq('id', attemptId).maybeSingle();
    if (chk.data && chk.data.submitted_at) return { state: 'ok', result: chk.data };
    return { state: 'blocked',
             message: '提出できませんでした。別のユーザでログインしていませんか' };
  }
  if (kind === KIND.INVALID) {
    return { state: 'blocked', message: error.message || '提出が受け付けられませんでした' };
  }
  return { state: 'retry', message: error.message || '通信できませんでした' };
}

function classifyRpc(error) {
  const code = String((error && error.code) || '');
  if (code === '42501' || code === 'PGRST301' || code === '401') return KIND.FROZEN;
  if (code === '23514' || code === '22P02' || code === 'P0001') return KIND.INVALID;
  return KIND.RETRY;
}
