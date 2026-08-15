// =============================================================================
// 冊子受験画面 — 接続設定
//
// ★ ここに置く anon key は **公開鍵**。ブラウザに配られる前提のもので、秘密ではない。
//   守っているのは RLS であってキーの秘匿ではない。
//
// ★ service_role / secret キーは絶対に置かないこと。RLS を全部素通りするので、
//   置いた瞬間に全生徒の答案が誰からでも読める。下の assertAnonKey が形で弾く。
//
// ★ 既存の塾システム (Railway の auth-guard.js / OTP・LINE ログイン) とは
//   **別系統の認証**。この画面は Supabase Auth のセッションだけを見る。
//
// ★★ 運用の前提: Supabase 側でサインアップを招待制 / ドメイン制限 /
//   メール確認 ON のいずれかにすること。開いたままだと第三者が登録 →
//   公開ブックの PDF を署名付き URL で取得 → 適当に提出して correct_answer と
//   explanation まで取れる。**教材がそのまま流出する。**
// =============================================================================

export const SUPABASE = {
  url: 'https://ljrsrlaftirzwotoykty.supabase.co',
  // Settings → API Keys の anon public。role=anon を確認済み (secret ではない)。
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
         + '.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxqcnNybGFmdGlyendvdG95a3R5Iiwicm9sZSI6'
         + 'ImFub24iLCJpYXQiOjE3ODY2NjA0NDEsImV4cCI6MjEwMjIzNjQ0MX0'
         + '.JeWjNryUN1xH7a-07lpBgUizI0W8T7t7qjFzouVhfuM',
};

/** anon 以外のキーを貼る事故を形で止める。 */
export function assertAnonKey(key) {
  if (!key) throw new Error('anon key が設定されていません (exam-book-config.mjs)');
  // 新形式の publishable キー (sb_publishable_…) は JWT ではないので素通しする。
  // 旧形式の JWT はペイロードの role を見る。
  if (/^sb_secret_/i.test(key)) {
    throw new Error('secret キーが設定されています。anon (publishable) を使ってください');
  }
  const parts = String(key).split('.');
  if (parts.length !== 3) return;               // JWT でない形式
  try {
    const claims = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
    if (claims.role && claims.role !== 'anon') {
      throw new Error(`role="${claims.role}" のキーが設定されています。anon を使ってください`);
    }
  } catch (e) {
    if (e instanceof Error && e.message.includes('role=')) throw e;
    // base64 として読めない場合は形式不明として素通し
  }
}
