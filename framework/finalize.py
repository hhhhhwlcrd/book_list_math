#!/usr/bin/env python3
"""Stage 4: apply verified merges, number duplicates, write the final table.

Usage: finalize.py <scratch_dir> <out.md>
Reads  <scratch>/keys.json, <scratch>/candidates.json,
       <scratch>/verify/verdicts_*.json (optional)
Writes <out.md>  (path | full_title | topic | duplicate)
"""
import glob
import json
import sys
from collections import defaultdict


class DSU:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def main():
    scratch, out = sys.argv[1], sys.argv[2]
    keys = {int(k): v for k, v in json.load(open(f'{scratch}/keys.json')).items()}
    dsu = DSU()
    for ln in keys:
        dsu.find(ln)

    # exact-key groups always merge
    by_key = defaultdict(list)
    for ln, v in keys.items():
        by_key[(v['ak'], v['tk'], v['gk'], v['pk'])].append(ln)
    for lns in by_key.values():
        for other in lns[1:]:
            dsu.union(lns[0], other)

    # verified fuzzy candidates
    verdict = {}
    for f in glob.glob(f'{scratch}/verify/verdicts_*.json'):
        for r in json.load(open(f)):
            verdict[r['id']] = r['same']
    cands = {c['id']: c for c in json.load(open(f'{scratch}/candidates.json'))} \
        if glob.glob(f'{scratch}/candidates.json') else {}
    merged = 0
    for cid, c in cands.items():
        if verdict.get(cid):
            dsu.union(c['a'][0], c['b'][0])
            merged += 1

    # number copies within each connected component, by file order
    comp = defaultdict(list)
    for ln in keys:
        comp[dsu.find(ln)].append(ln)
    dup_no = {}
    for lns in comp.values():
        for i, ln in enumerate(sorted(lns), 1):
            dup_no[ln] = i

    rows = []
    for ln in sorted(keys):
        v = keys[ln]
        rows.append((v['path'], v['full_title'], v['topic'], dup_no[ln]))

    def esc(s):
        return s.replace('|', '\\|').replace('\n', ' ')

    with open(out, 'w', encoding='utf-8') as fo:
        fo.write('| path | full_title | topic | duplicate |\n')
        fo.write('|------|------------|-------|-----------|\n')
        for path, title, topic, d in rows:
            fo.write(f'| {esc(path)} | {esc(title)} | {topic} | {d} |\n')

    dup_rows = sum(1 for d in dup_no.values() if d > 1)
    print(f'wrote {len(rows)} rows to {out}; {merged} fuzzy merges applied; '
          f'{dup_rows} rows are duplicates (copy №>1)')


main()
