# Book-catalog classification framework

Pipeline for building `books_table.md` (path, full_title, topic, duplicate №) from `list.md`
using small-model (Haiku) agents safely.

## Design principles

Haiku agents proved unreliable at *normalization* and *rule precedence*, but fine at
*reading and copying facts*. So:

1. **Agents only extract raw facts** (authors, core title, grade, part, subject flags).
   No normalization, no topic decision, no dedup keys.
2. **All decisions are deterministic Python**: topic precedence (`derive.py`), key
   normalization, exact duplicate grouping, fuzzy candidate generation (`build_keys.py`),
   final numbering (`finalize.py`).
3. **Every agent output is gated by a validator** (`validate_chunk.py`, `validate_verdicts.py`).
   The agent must re-run the validator until it prints `OK` — malformed or rule-breaking
   output cannot enter the pipeline. Validators also cross-check against the source line
   (e.g. grade present in source but missing in the record).
4. **Small chunks** (30 books) and binary questions (same work: yes/no) — task shapes
   small models handle well.

## Stages

```
Stage 1  EXTRACT   workflow_extract.js  → scratch/chunks/chunk_<a>.json   (Haiku agents)
Stage 2  KEYS      build_keys.py        → scratch/keys.json, scratch/candidates.json  (deterministic)
Stage 3  VERIFY    workflow_verify.js   → scratch/verify/verdicts_<i>.json (Haiku agents, yes/no per pair)
Stage 4  FINALIZE  finalize.py          → books_table.md                   (deterministic)
```

Run:

```bash
SCRATCH=<scratch dir>
# 1. launch workflow_extract.js via the Workflow tool (args: {"ranges": [[3,32],...]} or omit for all)
# 2.
python3 framework/build_keys.py "$SCRATCH"
# 3. launch workflow_verify.js via the Workflow tool (args: {"n": <candidate count>})
# 4.
python3 framework/finalize.py "$SCRATCH" books_table.md
```

## Record schema (stage 1 output, one per book)

```json
{"ln": 3, "authors": ["Голубь"], "title": "Комплексная проверка знаний учащихся. Математика. 2 класс",
 "grade": "2", "part": "", "level": "primary", "subject": "general",
 "olympiad": false, "exam_prep": false, "teacher_book": false, "popular": false}
```

## Topic derivation (deterministic, `derive.py`)

Precedence: grades 1–4 → Primary School (Olympiads) · olympiad → High School Olympiads ·
exam_prep → Exam Prep · subject → Geometry / Algebra / Calculus / Probability & Statistics ·
university → Higher Mathematics · popular → Popular Math & Puzzles · teacher_book →
Teaching Methodology · grades 5–6 → Middle School Math · else General Math.

## Duplicate detection

Two entries are copies of the same work (any edition/year/publisher/scan) when their
normalized `(authors, title, grade, part)` keys match exactly, or when a near-match
candidate pair (same authors + title similarity ≥ 0.75, or same title + different author
spelling) is confirmed `same=true` by a verify agent. Copies are numbered 1, 2, … in
file order.
