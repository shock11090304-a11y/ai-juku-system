export const meta = {
  name: 'chugaku-verify-lean',
  description: 'lean生成27単元の追加独立検証: blindビューを別エージェントが再解答(+社会理科はWebSearch事実照合)。保存済キーとの不一致を洗い出す。',
  phases: [{ title: 'Verify', detail: 'blind再解答 + 事実照合' }],
}

const TARGETS = [{"part": "eng", "filter": "be動詞・一般動詞", "gi": 0, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__0.json"}, {"part": "eng", "filter": "時制", "gi": 1, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__1.json"}, {"part": "eng", "filter": "助動詞", "gi": 2, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__2.json"}, {"part": "eng", "filter": "名詞・代名詞・冠詞", "gi": 3, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__3.json"}, {"part": "eng", "filter": "比較", "gi": 4, "subject": "英語", "factcheck": false, "n": 9, "blind_path": "scripts/chugaku_dojo/blind/eng__4.json"}, {"part": "eng", "filter": "不定詞・動名詞", "gi": 5, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__5.json"}, {"part": "eng", "filter": "分詞", "gi": 6, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__6.json"}, {"part": "eng", "filter": "受動態", "gi": 7, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__7.json"}, {"part": "eng", "filter": "現在完了", "gi": 8, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__8.json"}, {"part": "eng", "filter": "関係代名詞", "gi": 9, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__9.json"}, {"part": "eng", "filter": "接続詞・前置詞", "gi": 10, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__10.json"}, {"part": "eng", "filter": "会話表現", "gi": 11, "subject": "英語", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/eng__11.json"}, {"part": "math", "filter": "正負の数", "gi": 13, "subject": "数学", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/math__13.json"}, {"part": "math", "filter": "式の計算", "gi": 14, "subject": "数学", "factcheck": false, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/math__14.json"}, {"part": "rika", "filter": "生殖と遺伝", "gi": 46, "subject": "理科", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/rika__46.json"}, {"part": "rika", "filter": "天気", "gi": 48, "subject": "理科", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/rika__48.json"}, {"part": "shakai", "filter": "世界地理", "gi": 50, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__50.json"}, {"part": "shakai", "filter": "日本地理", "gi": 51, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__51.json"}, {"part": "shakai", "filter": "歴史 古代", "gi": 52, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__52.json"}, {"part": "shakai", "filter": "歴史 中世", "gi": 53, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__53.json"}, {"part": "shakai", "filter": "歴史 近世", "gi": 54, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__54.json"}, {"part": "shakai", "filter": "歴史 近代", "gi": 55, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__55.json"}, {"part": "shakai", "filter": "歴史 現代", "gi": 56, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__56.json"}, {"part": "shakai", "filter": "公民 政治", "gi": 57, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__57.json"}, {"part": "shakai", "filter": "公民 経済", "gi": 58, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__58.json"}, {"part": "shakai", "filter": "公民 国際", "gi": 59, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__59.json"}, {"part": "shakai", "filter": "資料読み取り", "gi": 60, "subject": "社会", "factcheck": true, "n": 10, "blind_path": "scripts/chugaku_dojo/blind/shakai__60.json"}]

const ANS_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['answers'],
  properties: {
    answers: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false, required: ['i', 'choice_index', 'confident'],
        properties: { i: { type: 'integer' }, choice_index: { type: 'integer', minimum: 0, maximum: 3 }, confident: { type: 'boolean' } },
      },
    },
  },
}

function solvePrompt(t) {
  return `中学「${t.subject}」単元「${t.filter}」の4択問題を独立に解答します。ファイル ${t.blind_path} を Read ツールで読み、各設問(i, stem, choices, passage)について最も正しい選択肢の0始まりindexを1つ選び、answers[{i,choice_index,confident}] で返してください。confident=一意に自信があるか。正解や解説は与えられていません(blindビュー)。出力は指定スキーマJSONのみ。`
}
function factPrompt(t) {
  return `あなたは中学「${t.subject}」の事実照合者です。ファイル ${t.blind_path} を Read ツールで読み、各設問について「事実として正しい選択肢」を独立に判定してください。年号・人名・制度・地名・数値・法則・実験結果などは、少しでも不確かなら WebSearch(必要なら ToolSearch で有効化)で裏取りする。各設問の事実的な正答の0始まりindexを answers[{i,choice_index,confident}] で返す(confident=裏取りできたか)。出力は指定スキーマJSONのみ。`
}

const out = await pipeline(
  TARGETS,
  async (t) => {
    const checks = [() => agent(solvePrompt(t), { label: `solve:${t.part}/${t.filter}`, phase: 'Verify', schema: ANS_SCHEMA, agentType: 'general-purpose' })]
    if (t.factcheck) checks.push(() => agent(factPrompt(t), { label: `fact:${t.part}/${t.filter}`, phase: 'Verify', schema: ANS_SCHEMA, agentType: 'general-purpose', effort: 'high' }))
    const res = await parallel(checks)
    const solver = res[0] || null
    const fact = t.factcheck ? (res[1] || null) : null
    return {
      part: t.part, gi: t.gi, filter: t.filter, subject: t.subject, n: t.n,
      solver_answers: (solver && solver.answers) || [],
      fact_answers: (fact && fact.answers) || [],
    }
  }
)

return { units: out.filter(Boolean) }
