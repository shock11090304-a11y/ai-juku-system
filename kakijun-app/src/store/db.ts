/**
 * IndexedDB ラッパ (§9.3, §12.6)。
 * IndexedDB を選ぶ理由は非同期・容量・構造化データ（耐久性ではない）。
 * ITP 対策として起動時に navigator.storage.persist() を要求し (main.tsx)、
 * 確実なバックアップは保護者画面のエクスポート機能で提供する。
 */
import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type { CharProgress } from './progress';
import type { Settings } from './settings';

export type DaySession = { date: string; seconds: number };

interface KakijunDB extends DBSchema {
  progress: { key: string; value: CharProgress };
  settings: { key: string; value: Settings };
  sessions: { key: string; value: DaySession };
}

let dbPromise: Promise<IDBPDatabase<KakijunDB>> | null = null;

export function getDB(): Promise<IDBPDatabase<KakijunDB>> {
  if (!dbPromise) {
    dbPromise = openDB<KakijunDB>('kakijun', 1, {
      upgrade(db) {
        db.createObjectStore('progress', { keyPath: 'charId' });
        db.createObjectStore('settings');
        db.createObjectStore('sessions', { keyPath: 'date' });
      },
    });
    // 失敗した Promise を永久キャッシュすると以後の保存が全部無言で失われる。
    // 失敗時はキャッシュを捨てて次回の呼び出しで開き直す
    dbPromise.catch(() => {
      dbPromise = null;
    });
  }
  return dbPromise;
}
