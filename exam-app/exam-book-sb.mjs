// =============================================================================
// 冊子受験画面 — Supabase の入口
//
// ★ ここ以外で sb.from(...) を直に呼ばない。エラーの分類と行数の判定を
//   1 箇所に集めるため。散らすと「0 行更新なのに成功と表示」が必ず紛れ込む。
// =============================================================================
import { createClient } from '/vendor/supabase-js/supabase.mjs?v=2';
import { SUPABASE, assertAnonKey } from '/exam-book-config.mjs?v=1';

let _sb = null;

export function sb() {
  if (_sb) return _sb;
  assertAnonKey(SUPABASE.anonKey);
  _sb = createClient(SUPABASE.url, SUPABASE.anonKey, {
    auth: { persistSession: true, autoRefreshToken: true },
    // ★ fetch を包んで毎レスポンスの Date ヘッダを拾う。これが serverNow() の素。
    global: { fetch: (...a) => globalThis.fetch(...a).then(noteResponse) },
  });
  return _sb;
}

// --- サーバ時刻 --------------------------------------------------------------
// 端末の時計はずれる (生徒が自分で変えることもある)。締切の表示はサーバ時刻を基準にする。
// ★ 通信のたびに更新するので、試験中に端末の時計をいじられても追従する。
let _skewMs = 0;
let _sawServerDate = false;

export function noteServerDate(dateHeader) {
  if (!dateHeader) return;
  const t = Date.parse(dateHeader);
  if (Number.isFinite(t)) { _skewMs = t - Date.now(); _sawServerDate = true; }
}

function noteResponse(res) {
  try { noteServerDate(res.headers.get('date')); } catch (_) { /* 取れなくても続ける */ }
  return res;
}

/** サーバ時刻を一度でも観測したか。false のうちは残り時間を「およそ」と表示する。 */
export const haveServerClock = () => _sawServerDate;
export const serverNow = () => new Date(Date.now() + _skewMs);

// --- エラー分類 --------------------------------------------------------------
// ★ 設計の核。ここを 4 分岐にしないと「無限リトライで試験が終われない」か
//   「消えたのに黙っている」のどちらかになる。
export const KIND = Object.freeze({
  RETRY:   'retry',    // 通信断・5xx。指数バックオフで再送する
  FROZEN:  'frozen',   // 42501 = 提出済み/他人の答案。**再送しない**。凍結して知らせる
  INVALID: 'invalid',  // 23514 = 形が DB に拒否された。**再送しない**。捨てて知らせる
  CONFLICT:'conflict', // CAS が 0 行。読み直してマージし直す
});

export function classify(error, rowCount) {
  if (!error) {
    if (rowCount === 0) return KIND.CONFLICT;   // 更新できていない = 版がずれた or 権限
    return null;
  }
  const code = String(error.code || '');
  if (code === '42501') return KIND.FROZEN;     // permission denied / RLS violation
  if (code === '23514') return KIND.INVALID;    // check_violation
  if (code === '23505') return KIND.CONFLICT;   // unique_violation (同時 insert)
  if (code === 'PGRST301' || code === '401') return KIND.FROZEN;  // JWT 切れ
  return KIND.RETRY;
}

/** 更新系は必ずこれを通す。**返却行数で判定する** (0 行でもエラーにならないため)。 */
export async function run(query) {
  const { data, error, status } = await query;
  const rows = Array.isArray(data) ? data.length : (data ? 1 : 0);
  return { data, error, status, rows, kind: classify(error, rows) };
}
