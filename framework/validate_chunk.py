#!/usr/bin/env python3
"""Gate for extraction agents: validate_chunk.py <chunk.json> <first_ln> <last_ln>

Prints OK and exits 0 only when the chunk is structurally valid AND consistent
with the source lines in list.md. Otherwise prints one problem per line, exit 1.
"""
import json
import re
import sys

LIST_MD = '/home/user/book_list_math/list.md'
LEVELS = {'primary', 'middle', 'high', 'university', 'unknown'}
SUBJECTS = {'geometry', 'algebra', 'calculus', 'probability', 'general'}
BOOL_FIELDS = ['olympiad', 'exam_prep', 'teacher_book', 'popular']
FIELDS = {'ln', 'authors', 'title', 'grade', 'part', 'level', 'subject', *BOOL_FIELDS}


def main():
    path, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    problems = []
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f'FAIL: not valid JSON: {e}')
        sys.exit(1)
    if not isinstance(data, list):
        print('FAIL: top level must be a JSON array')
        sys.exit(1)

    expected = list(range(a, b + 1))
    got = [r.get('ln') for r in data if isinstance(r, dict)]
    if got != expected:
        problems.append(
            f'ln sequence wrong: need exactly {a}..{b} in order '
            f'({len(expected)} records), got {len(got)} records starting {got[:5]}')

    src = open(LIST_MD, encoding='utf-8').readlines()

    for r in data:
        if not isinstance(r, dict):
            problems.append('record is not an object')
            continue
        ln = r.get('ln')
        missing = FIELDS - set(r)
        if missing:
            problems.append(f'ln {ln}: missing fields {sorted(missing)}')
            continue
        if not isinstance(r['authors'], list) or not all(
                isinstance(x, str) and x.strip() for x in r['authors']):
            problems.append(f'ln {ln}: authors must be a list of non-empty strings')
        t = r['title']
        if not isinstance(t, str) or len(t.strip()) < 3:
            problems.append(f'ln {ln}: title empty or too short')
        elif re.search(r'[<>]', t):
            problems.append(f'ln {ln}: title contains <> placeholder — reconstruct the real title from the path')
        g = r['grade']
        if not isinstance(g, str) or not re.fullmatch(r'|\d{1,2}([-–—]\d{1,2})?', g):
            problems.append(f"ln {ln}: grade must be '' or like '3' or '5-6', got {g!r}")
        p = r['part']
        if not isinstance(p, str) or not re.fullmatch(r'|\d{1,2}', p):
            problems.append(f"ln {ln}: part must be '' or a number like '1', got {p!r}")
        if r['level'] not in LEVELS:
            problems.append(f"ln {ln}: level must be one of {sorted(LEVELS)}, got {r['level']!r}")
        if r['subject'] not in SUBJECTS:
            problems.append(f"ln {ln}: subject must be one of {sorted(SUBJECTS)}, got {r['subject']!r}")
        for k in BOOL_FIELDS:
            if not isinstance(r[k], bool):
                problems.append(f'ln {ln}: {k} must be true or false')

        # cross-checks against the source line
        if isinstance(ln, int) and 1 <= ln <= len(src):
            line = src[ln - 1].lower()
            if isinstance(g, str) and g == '' and re.search(r'\d{1,2}\s*[-–—]?\s*(кл\b|klass|kl[._-])', line):
                problems.append(f'ln {ln}: grade is empty but the source line mentions a class/kl — set it')
            title_part = src[ln - 1].split('\t')[1] if '\t' in src[ln - 1] else ''
            prefix = title_part.split(' - ')[0] if ' - ' in title_part else ''
            if r.get('authors') == [] and re.search(r'[А-ЯЁ]\.\s*(?:[А-ЯЁ]\.)?\s*[А-ЯЁ][а-яё]+|[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.', prefix):
                problems.append(f'ln {ln}: authors is empty but the source title starts with an author name')

    if problems:
        print('FAIL:')
        for pr in problems[:40]:
            print(' -', pr)
        sys.exit(1)
    print('OK')


main()
