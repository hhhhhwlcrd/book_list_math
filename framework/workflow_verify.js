export const meta = {
  name: 'verify-duplicates',
  description: 'Stage 3: Haiku agents decide same-work yes/no for each fuzzy candidate pair',
  phases: [{ title: 'Verify', detail: 'one Haiku agent per batch of candidate pairs' }],
}

const SCRATCH = '/tmp/claude-0/-home-user-book-list-math/82f07ce2-9a0d-5b71-be3d-d22f587466fc/scratchpad'
const FW = '/home/user/book_list_math/framework'
const BATCH = 20

// candidates.json is produced by build_keys.py; args.n = total candidate count.
const n = (args && args.n) || 0
if (!n) { log('no candidates to verify'); return { batches: 0, verified: 0 } }

const batches = []
for (let s = 0; s < n; s += BATCH) batches.push([s, Math.min(s + BATCH - 1, n - 1)])

const PROMPT = (a, b) => `You decide whether two catalog entries are THE SAME WORK (same book — any edition, year, publisher, printing, or re-scan counts as the same work). Different works include: a textbook vs its problem-book (задачник), часть 1 vs часть 2, different grade, or a genuinely different title.

Read the candidate file: python3 -c "import json; d=json.load(open('${SCRATCH}/candidates.json')); import sys; [print(json.dumps(c, ensure_ascii=False)) for c in d if ${a} <= c['id'] <= ${b}]"

Each line is a candidate: {"id":.., "a_lines":[...], "b_lines":[...]}. Compare the a_lines group against the b_lines group. They represent the same work if the underlying book is identical even when spelling of authors, publisher, year, or filename differs.

Write a JSON array to ${SCRATCH}/verify/verdicts_${a}.json with one object per candidate id ${a}..${b}:
[{"id": <id>, "same": true|false}, ...]

Then validate — run exactly:
python3 ${FW}/validate_verdicts.py ${SCRATCH}/verify/verdicts_${a}.json ${a} ${b}
If it does not print "OK", fix and re-run until it does. Do not finish until it prints OK.

Return only: how many pairs and whether the validator printed OK.`

const SCHEMA = {
  type: 'object',
  properties: { count: { type: 'number' }, validated: { type: 'boolean' } },
  required: ['count', 'validated'],
}

phase('Verify')
log(`Verifying ${n} candidate pairs in ${batches.length} batches (Haiku)`)

const results = await parallel(batches.map(([a, b]) => () =>
  agent(PROMPT(a, b), { label: `verify:${a}-${b}`, phase: 'Verify', schema: SCHEMA, model: 'haiku' })
))

const ok = results.filter(Boolean)
const failed = batches.filter((_, i) => !results[i] || !results[i].validated).map(([a, b]) => `${a}-${b}`)
if (failed.length) log(`NOT validated: ${failed.join(', ')}`)
return { batches: batches.length, validated: ok.filter(r => r.validated).length, failed }
