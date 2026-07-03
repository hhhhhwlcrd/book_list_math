"""Deterministic normalization and topic derivation shared by pipeline stages."""
import re

DROP_TOKENS = {
    'изд', 'издание', 'издательство', 'переработанное', 'дополненное',
    'исправленное', 'стереотипное', 'фгос',
}

TOPICS = [
    'Primary School Olympiads', 'Primary School', 'High School Olympiads',
    'Exam Prep', 'Geometry', 'Algebra', 'Calculus', 'Probability & Statistics',
    'Middle School Math', 'Higher Mathematics', 'Popular Math & Puzzles',
    'Teaching Methodology', 'General Math',
]

SUBJECT_TOPIC = {
    'geometry': 'Geometry',
    'algebra': 'Algebra',
    'calculus': 'Calculus',
    'probability': 'Probability & Statistics',
}


def norm_text(s):
    """lowercase, ё→е, strip punctuation/years, drop edition boilerplate."""
    s = s.lower().replace('ё', 'е')
    s = re.sub(r'[^a-zа-я0-9\s]', ' ', s)
    s = re.sub(r'\b(19|20)\d{2}\b', ' ', s)
    return ' '.join(t for t in s.split() if t not in DROP_TOKENS)


def author_key(authors):
    """Sorted, normalized surnames joined by '-'. Defensive against initials."""
    surnames = set()
    for a in authors:
        toks = [t for t in norm_text(a).split() if len(t) > 1]
        if toks:
            surnames.add(max(toks, key=len))
    return '-'.join(sorted(surnames))


def grade_key(g):
    return g.strip().replace('–', '-').replace('—', '-')


def grade_hi(g):
    nums = re.findall(r'\d+', g)
    return max(map(int, nums)) if nums else None


def keys(rec):
    """(author_key, title_key, grade_key, part) — exact-duplicate identity."""
    return (author_key(rec['authors']), norm_text(rec['title']),
            grade_key(rec['grade']), rec['part'].strip())


def topic(rec):
    hi = grade_hi(rec['grade'])
    primary = rec['level'] == 'primary' or (hi is not None and hi <= 4)
    if primary:
        return 'Primary School Olympiads' if rec['olympiad'] else 'Primary School'
    if rec['olympiad']:
        return 'High School Olympiads'
    if rec['exam_prep']:
        return 'Exam Prep'
    if rec['subject'] in SUBJECT_TOPIC:
        return SUBJECT_TOPIC[rec['subject']]
    if rec['level'] == 'university':
        return 'Higher Mathematics'
    if rec['popular']:
        return 'Popular Math & Puzzles'
    if rec['teacher_book']:
        return 'Teaching Methodology'
    if rec['level'] == 'middle' or grade_key(rec['grade']) in ('5', '6', '5-6'):
        return 'Middle School Math'
    return 'General Math'
