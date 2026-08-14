// 冊子受験画面のスモークテスト用の偽 Supabase。
// ★ updated_at の CAS と 42501 の凍結だけは本物と同じ意味にする (そこを試したいので)。
const S = (globalThis.__DB = {
  books: [{ id: 'b1', title: 'テスト冊子', pdf_path: 'demo/book.pdf',
            time_limit_sec: null, page_count: 2, is_published: true,
            created_at: '2026-08-01T00:00:00Z' },
          // 設問が 1 問も無い未公開の本。「設問 0 の冊子は公開できない」の確認に使う。
          { id: 'b2', title: '設問なしの本 (未公開)', subject: 'grammar', level: null,
            pdf_path: 'books/b2.pdf', page_count: 2, time_limit_sec: null,
            is_published: false, created_at: '2026-08-02T00:00:00Z' }],
  questions: [
    { id: 'q1', book_id: 'b1', number: 1, page: 1, answer_type: 'choice', choice_count: 4,
      points: 1, unit_tag: null, correct_answer: '2', accepted_answers: null,
      explanation: '解説 1' },
    { id: 'q2', book_id: 'b1', number: 2, page: 2, answer_type: 'short', choice_count: null,
      points: 2, unit_tag: null, correct_answer: 'apple', accepted_answers: null,
      explanation: '解説 2' },
    { id: 'q3', book_id: 'b1', number: 3, page: null, answer_type: 'choice', choice_count: 3,
      points: 1, unit_tag: null, correct_answer: '1', accepted_answers: null,
      explanation: '解説 3' },
  ],
  revealed: false,          // 提出すると true になる (student_questions が返し始める)
  attempts: [], answers: [], annotations: [],
  // 先生用の登録画面はここの role を見る。検査から差し替えられるようにする。
  profiles: [{ id: 'u1', display_name: '見本 先生', role: 'student' }],
  // ★ 生徒向けの view。提出するまで正解と解説を返さない (実物の student_questions と同じ)。
  get student_questions() {
    return this.questions.map((q) => ({
      ...q,
      revealed: this.revealed,
      correct_answer: this.revealed ? q.correct_answer : null,
      accepted_answers: this.revealed ? q.accepted_answers : null,
      explanation: this.revealed ? q.explanation : null,
    }));
  },
  log: [], rpcCalls: [],
  offline: false,        // 機内モード (annotations の書き込みを通信断にする)
  offlineAnswers: false, // 答案の保存だけを通信断にする
  clock: 0,
});
// 検査用: ログイン中のユーザーの役割を差し込む (講師専用画面の確認に使う)
try {
  const r = globalThis.localStorage.getItem('__smoke_role');
  if (r) S.profiles[0].role = r;
} catch (_) { /* localStorage が無い環境 */ }

// 検査用: 制限時間を差し込む (時間切れ自動提出の経路を通すため)
try {
  const t = Number(globalThis.localStorage.getItem('__smoke_time_limit'));
  if (t > 0) S.books[0].time_limit_sec = t;
} catch (_) { /* localStorage が無い環境 */ }

// ★ 実時間を使う。固定の過去だと started_at からの経過が常に制限時間を超え、
//   残り時間の計算とタイマーの経路を一度も試せない。
//   clock は同じミリ秒に 2 回書いたとき updated_at が並ばないようにする足し込み
//   (並ぶと CAS が「版が変わっていない」と誤認する)。
const now = () => new Date(Date.now() + (S.clock++)).toISOString();
const err = (code, message) => ({ code, message, details: '', hint: '' });

class Q {
  constructor(table) { this.t = table; this.f = []; this.op = 'select'; this.one = null; this.payload = null; }
  select() { if (this.op === 'select') this.op = 'select'; return this; }
  eq(c, v) { this.f.push([c, v]); return this; }
  is(c, v) { this.f.push([c, v]); return this; }
  order() { return this; }
  single() { this.one = 'single'; return this; }
  maybeSingle() { this.one = 'maybe'; return this; }
  insert(rows) { this.op = 'insert'; this.payload = rows; return this; }
  update(patch) { this.op = 'update'; this.payload = patch; return this; }
  _match(r) { return this.f.every(([c, v]) => (r[c] ?? null) === (v ?? null)); }

  then(res) {
    S.log.push({ t: this.t, op: this.op, f: this.f, payload: this.payload });
    // 検査用: 書き込みの取得だけを落とす (「取得失敗」と「白紙」の取り違えを見る)
    if (this.t === 'annotations' && this.op === 'select'
        && globalThis.localStorage.getItem('__smoke_fail_ann')) {
      return Promise.resolve({ data: null, error: { message: 'Failed to fetch' }, status: 0 })
        .then(res);
    }
    if (S.offlineAnswers && this.t === 'answers' && this.op === 'update') {
      return Promise.resolve({ data: null, error: { message: 'Failed to fetch' }, status: 0 })
        .then(res);
    }
    if (S.offline && this.t === 'annotations' && this.op !== 'select') {
      // 通信断。code が無いので classify() は RETRY に落ちる (本物と同じ)。
      return Promise.resolve({ data: null, error: { message: 'Failed to fetch' }, status: 0 })
        .then(res);
    }
    let out = { data: null, error: null, status: 200 };
    const rows = S[this.t] || [];
    try {
      if (this.op === 'select') {
        out.data = rows.filter((r) => this._match(r)).map((r) => ({ ...r }));
      } else if (this.op === 'insert') {
        const list = Array.isArray(this.payload) ? this.payload : [this.payload];
        const made = [];
        for (const r of list) {
          if (this.t === 'answers'
              && rows.some((x) => x.attempt_id === r.attempt_id && x.question_id === r.question_id)) {
            throw err('23505', 'duplicate key');
          }
          if (this.t === 'annotations'
              && rows.some((x) => x.attempt_id === r.attempt_id && x.page === r.page)) {
            throw err('23505', 'duplicate key');
          }
          if (this.t === 'annotations' || this.t === 'answers') {
            const at = S.attempts.find((a) => a.id === r.attempt_id);
            if (at && at.submitted_at) throw err('42501', 'permission denied');
          }
          const row = { id: `${this.t}-${rows.length + made.length + 1}`, ...r, updated_at: now() };
          // ★ DB 側の default now() を再現する。無いと started_at が undefined になり、
          //   残り時間が NaN になる (本物では default が入るので起きない)。
          if (this.t === 'attempts' && row.started_at == null) {
            // 検査用: 開始時刻が返ってこない状況も作れるようにする
            let omit = false;
            try { omit = !!globalThis.localStorage.getItem('__smoke_no_started_at'); } catch (_) {}
            if (!omit) row.started_at = now();
          }
          made.push(row);
        }
        rows.push(...made);
        out.data = made.map((r) => ({ ...r }));
      } else if (this.op === 'update') {
        const hit = rows.filter((r) => this._match(r));
        for (const r of hit) {
          const at = S.attempts.find((a) => a.id === r.attempt_id);
          if (at && at.submitted_at) throw err('42501', 'permission denied');
          Object.assign(r, this.payload, { updated_at: now() });
        }
        out.data = hit.map((r) => ({ ...r }));   // CAS: 版が違えば _match が外れて 0 行
      }
    } catch (e) {
      out = { data: null, error: e, status: 400 };
    }
    if (out.data && this.one) out.data = out.data.length ? out.data[0] : null;
    if (out.data === null && this.one === 'single' && !out.error) {
      out.error = err('PGRST116', 'no rows');
    }
    return Promise.resolve(out).then(res);
  }
}

export function createClient() {
  return {
    auth: {
      getSession: async () => ({ data: { session: { user: { id: 'u1' } } } }),
      signInWithPassword: async () => ({ error: null }),
      refreshSession: async () => ({ error: null }),
    },
    from: (t) => new Q(t),
    storage: {
      from: () => ({
        createSignedUrl: async (p) => ({ data: { signedUrl: `/__pdf/${p}` }, error: null }),
        list: async () => ({ data: [{ name: 'book.pdf', updated_at: '2026-08-01T00:00:00Z' }],
                             error: null }),
      }),
    },
    rpc: async (name, args) => {
      S.rpcCalls.push({ name, args });
      S.log.push({ t: 'rpc', op: name, f: [], payload: args });
      const at = S.attempts.find((a) => a.id === args.p_attempt);
      if (!at || at.submitted_at) return { data: null, error: err('42501', 'permission denied') };
      let total = 0, max = 0, correct = 0;
      for (const q of S.questions) {
        max += q.points;
        const a = S.answers.find((x) => x.attempt_id === at.id && x.question_id === q.id);
        if (!a) continue;
        const ok = String(a.user_answer ?? '').trim().toLowerCase()
                   === String(q.correct_answer).toLowerCase();
        a.is_correct = ok;
        if (ok) { total += q.points; correct++; }
      }
      at.submitted_at = now(); at.total_score = total; at.max_score = max; at.elapsed_sec = 42;
      S.revealed = true;
      return { data: [{ total_score: total, max_score: max, correct_count: correct,
                        answered_count: S.answers.length, question_count: S.questions.length }],
               error: null };
    },
  };
}
