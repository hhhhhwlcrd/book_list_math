#!/usr/bin/env python3
"""Gate for verify agents: validate_verdicts.py <verdicts.json> <first_id> <last_id>

Prints OK only when the file is a JSON array covering exactly ids first..last,
each with a boolean "same". Otherwise prints problems, exit 1.
"""
import json
import sys


def main():
    path, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f'FAIL: not valid JSON: {e}')
        sys.exit(1)
    problems = []
    if not isinstance(data, list):
        print('FAIL: top level must be a JSON array')
        sys.exit(1)
    ids = [r.get('id') for r in data if isinstance(r, dict)]
    if sorted(ids) != list(range(a, b + 1)):
        problems.append(f'ids must be exactly {a}..{b}, got {sorted(ids)[:10]}... ({len(ids)} items)')
    for r in data:
        if not isinstance(r, dict) or not isinstance(r.get('same'), bool):
            problems.append(f'item {r!r:.80}: needs "id" and boolean "same"')
    if problems:
        print('FAIL:')
        for p in problems[:20]:
            print(' -', p)
        sys.exit(1)
    print('OK')


main()
