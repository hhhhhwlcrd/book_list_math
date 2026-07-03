#!/usr/bin/env python3
"""Stage 2: merge extraction chunks, derive topics/keys, group exact duplicates,
emit fuzzy near-duplicate candidates for agent verification.

Usage: build_keys.py <scratch_dir>
Reads  <scratch>/chunks/chunk_*.json
Writes <scratch>/keys.json        {ln: {topic, key, path, full_title}}
       <scratch>/candidates.json  [{id, a, b, a_lines, b_lines}]
"""
import glob
import json
import os
import sys
from collections import defaultdict
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import derive

LIST_MD = '/home/user/book_list_math/list.md'
SIM_THRESHOLD = 0.75


def main():
    scratch = sys.argv[1]
    src = open(LIST_MD, encoding='utf-8').readlines()

    recs = {}
    for f in glob.glob(f'{scratch}/chunks/chunk_*.json'):
        for r in json.load(open(f)):
            recs[r['ln']] = r
    lns = sorted(recs)
    print(f'loaded {len(recs)} records from {len(glob.glob(f"{scratch}/chunks/chunk_*.json"))} chunks')
    expected = set(range(3, 1826))
    missing = expected - set(lns)
    if missing:
        print(f'WARNING: {len(missing)} lines not covered yet (partial run), e.g. {sorted(missing)[:5]}')

    out = {}
    groups = defaultdict(list)  # exact key -> [ln]
    for ln in lns:
        r = recs[ln]
        cols = src[ln - 1].rstrip('\n').split('\t')
        key = derive.keys(r)
        groups[key].append(ln)
        out[ln] = {
            'path': cols[0],
            'full_title': cols[1] if len(cols) > 1 else '',
            'topic': derive.topic(r),
            'ak': key[0], 'tk': key[1], 'gk': key[2], 'pk': key[3],
        }

    json.dump(out, open(f'{scratch}/keys.json', 'w'), ensure_ascii=False)

    # ---- fuzzy candidates between groups ----
    group_list = [(k, sorted(v)) for k, v in groups.items()]
    by_ak = defaultdict(list)
    by_tgp = defaultdict(list)
    for i, (k, _) in enumerate(group_list):
        by_ak[k[0]].append(i)
        by_tgp[(k[1], k[2], k[3])].append(i)

    cand_pairs = set()
    # same author key, similar title, compatible grade/part
    for ak, idxs in by_ak.items():
        if not ak or len(idxs) > 80:
            continue
        for x in range(len(idxs)):
            for y in range(x + 1, len(idxs)):
                ka, kb = group_list[idxs[x]][0], group_list[idxs[y]][0]
                if ka[3] != kb[3]:
                    continue  # different part => different work
                if ka[2] and kb[2] and ka[2] != kb[2]:
                    continue  # different explicit grades => different work
                if SequenceMatcher(None, ka[1], kb[1]).ratio() >= SIM_THRESHOLD:
                    cand_pairs.add((idxs[x], idxs[y]))
    # same title+grade+part, different author key (spelling/missing co-author)
    for tgp, idxs in by_tgp.items():
        if not tgp[0]:
            continue
        for x in range(len(idxs)):
            for y in range(x + 1, len(idxs)):
                cand_pairs.add(tuple(sorted((idxs[x], idxs[y]))))

    candidates = []
    for cid, (x, y) in enumerate(sorted(cand_pairs)):
        (ka, la), (kb, lb) = group_list[x], group_list[y]
        candidates.append({
            'id': cid,
            'a': la, 'b': lb,
            'a_lines': [src[ln - 1].rstrip('\n') for ln in la[:3]],
            'b_lines': [src[ln - 1].rstrip('\n') for ln in lb[:3]],
        })
    json.dump(candidates, open(f'{scratch}/candidates.json', 'w'), ensure_ascii=False, indent=1)

    exact_dups = sum(len(v) - 1 for v in groups.values() if len(v) > 1)
    print(f'{len(groups)} exact groups, {exact_dups} exact duplicate rows, '
          f'{len(candidates)} fuzzy candidates for verification')


main()
