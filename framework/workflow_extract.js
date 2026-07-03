export const meta = {
  name: 'extract-books',
  description: 'Stage 1: Haiku agents extract raw facts per book, gated by validate_chunk.py',
  phases: [{ title: 'Extract', detail: 'one Haiku agent per 30-book slice, must pass validator' }],
}

const SCRATCH = '/tmp/claude-0/-home-user-book-list-math/82f07ce2-9a0d-5b71-be3d-d22f587466fc/scratchpad'
const FW = '/home/user/book_list_math/framework'
const CHUNK = 30

// args.ranges = [[a,b],...] to target specific slices; omit to cover all data lines 3..1825
const ranges = (args && args.ranges) || (() => {
  const r = []
  for (let s = 3; s <= 1825; s += CHUNK) r.push([s, Math.min(s + CHUNK - 1, 1825)])
  return r
})()

const PROMPT = (a, b) => `You extract raw facts from a Russian math-book catalog. Do NOT normalize, translate, or judge topics — just copy what you see.

Run: sed -n '${a},${b}p' /home/user/book_list_math/list.md
Each line is: path<TAB>full_title. First line = file line ${a}, then ${a + 1}, etc.

For EVERY line output one JSON object with EXACTLY these fields:
- "ln": integer file line number (${a}..${b}).
- "authors": array of surname strings exactly as written (e.g. ["Узорова","Нефёдова"]). Keep Cyrillic, keep ё. Drop initials/first names, keep only surnames. If the full_title has no author (or shows a <...> placeholder), reconstruct author surnames from the path filename; if truly none, use [].
- "title": the work's title as written in full_title, with author/year/publisher/page-count REMOVED but everything else kept verbatim (grade, "рабочая тетрадь", "часть 1", subtitle). If full_title is a <...> placeholder, reconstruct a readable title from the path filename instead. Never output <> characters.
- "grade": school grade as written: "" or "3" or "5-6" (digits only, hyphen for ranges). No "класс"/"кл".
- "part": "" or a single digit if the book says часть/том N (e.g. "1"). Else "".
- "level": one of "primary" (grades 1-4 / начальная школа), "middle" (5-6), "high" (7-11 or unspecified school), "university" (вуз/высшая математика), "unknown".
- "subject": one of "geometry" (геометрия/стереометрия/планиметрия), "algebra" (алгебра), "calculus" (начала анализа/производная/интеграл/матанализ), "probability" (вероятност/статистика/комбинаторика), "general" (anything else or mixed).
- "olympiad": true if it is olympiad/competition/enrichment/кружок material (олимпиад, турнир, "36 занятий для будущих отличников", задачи повышенной трудности for competitions), else false.
- "exam_prep": true if its purpose is exam certification (ЕГЭ, ОГЭ, ГИА, ВПР, итоговая аттестация, экзамен), else false.
- "teacher_book": true if addressed to teachers (поурочные разработки, методические рекомендации, рабочая программа, конспекты уроков), else false.
- "popular": true if занимательная математика / головоломки / logic puzzles / popular science, else false.

Write the JSON array (${b - a + 1} objects, in line order) to: ${SCRATCH}/chunks/chunk_${a}.json

Then you MUST validate — run exactly:
python3 ${FW}/validate_chunk.py ${SCRATCH}/chunks/chunk_${a}.json ${a} ${b}
If it prints anything other than "OK", FIX the file to address each listed problem and re-run the validator. Repeat until it prints OK. Do not finish until it prints OK.

Return only: the number of records and whether the validator printed OK.`

const SCHEMA = {
  type: 'object',
  properties: { count: { type: 'number' }, validated: { type: 'boolean' } },
  required: ['count', 'validated'],
}

phase('Extract')
log(`Extracting ${ranges.length} chunks of up to ${CHUNK} books (Haiku)`)

const results = await parallel(ranges.map(([a, b]) => () =>
  agent(PROMPT(a, b), { label: `extract:${a}-${b}`, phase: 'Extract', schema: SCHEMA, model: 'haiku' })
))

const ok = results.filter(Boolean)
const failed = ranges.filter((_, i) => !results[i] || !results[i].validated).map(([a, b]) => `${a}-${b}`)
if (failed.length) log(`NOT validated: ${failed.join(', ')}`)
return {
  ranges: ranges.length,
  validated: ok.filter(r => r.validated).length,
  totalRecords: ok.reduce((s, r) => s + r.count, 0),
  failed,
}
