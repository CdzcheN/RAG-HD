"""Propose stable holdout, development folds and rule families before inference."""
from collections import defaultdict

from .challenges_v2 import canonical_title
from .io import fingerprint

SEEDS = (13, 42, 2026)


def development_splits(rows):
    if len({r['component_id'] for r in rows}) != len(rows):
        raise ValueError('Nominations must have independent source components')
    strata = defaultdict(list)
    test = []
    for row in rows:
        if row['planned_split'] == 'test':
            test.append(row['base_question_id'])
        else:
            strata[row['dataset'], row['proposed_challenge_type']].append(row['base_question_id'])
    if len(test) != 60 or len(strata) != 6 or any(len(ids) != 40 for ids in strata.values()):
        raise ValueError('Require 60 fixed test bases and six development strata of 40')
    result = {}
    for seed in SEEDS:
        train, validation = [], []
        for key, ids in sorted(strata.items()):
            ordered = sorted(ids, key=lambda sid: fingerprint([seed, list(key), sid]))
            train.extend(ordered[:30]); validation.extend(ordered[30:])
        result[str(seed)] = {'train': sorted(train), 'validation': sorted(validation), 'test': sorted(test)}
    return result


def verify_source_isolation(rows, reservations, splits):
    by_id = {r['base_question_id']: r for r in rows}
    noise = {r['base_question_id']: r for r in reservations}
    if len(by_id) != len(rows) or len(noise) != len(reservations) or set(noise) != set(by_id):
        raise ValueError('Every nominated base must have exactly one noise reservation')
    owner = {}
    for sid, row in by_id.items():
        if len(noise[sid]['evidence']) != 5:
            raise ValueError('Every base needs exactly five reserved distractors')
        titles = list(row['gold_titles'])+[d['title'] for d in noise[sid]['evidence']]
        if len({canonical_title(t) for t in titles}) != len(titles):
            raise ValueError('Duplicate canonical sources inside a base reservation')
        for title in titles:
            key = canonical_title(title)
            if key in owner and owner[key] != sid:
                raise ValueError('Shared target or distractor canonical source across base groups')
            owner[key] = sid
    summary = {}
    for seed, parts in splits.items():
        union = [sid for ids in parts.values() for sid in ids]
        if len(union) != len(set(union)) or set(union) != set(by_id):
            raise ValueError('Every base must occur in exactly one partition per seed')
        sources = {part: {title for title, sid in owner.items() if sid in set(ids)} for part, ids in parts.items()}
        if any(sources[a] & sources[b] for a in sources for b in sources if a != b):
            raise ValueError('Cross-partition source overlap')
        summary[seed] = {'base_counts': {part: len(ids) for part, ids in parts.items()},
                         'source_counts': {part: len(titles) for part, titles in sources.items()},
                         'cross_partition_canonical_source_overlap': 0}
    return summary


def rule_assignments(rows, families, seed):
    strata = defaultdict(list)
    for row in rows:
        strata[row['planned_split'], row['dataset'], row['proposed_challenge_type']].append(row)
    result = []
    for (split, dataset, kind), members in sorted(strata.items()):
        ordered = sorted(members, key=lambda r: fingerprint([seed, 'rule-family', r['base_question_id']]))
        for index, row in enumerate(ordered):
            if kind == 'retrieval_failure':
                family, exposure = 'plain_question', 'not_applicable'
            else:
                bank = families[kind]
                if split == 'test' and index % 2:
                    family, exposure = bank['heldout'][0], 'heldout_wording'
                else:
                    # Alternate compatible families on train/validation; even test rows alternate too.
                    family = bank['seen'][(index//2 if split == 'test' else index) % len(bank['seen'])]
                    exposure = 'seen_wording'
            result.append({'base_question_id': row['base_question_id'], 'component_id': row['component_id'],
                           'planned_split': split, 'dataset': dataset, 'challenge_type': kind,
                           'family': family, 'exposure': exposure,
                           'both_pair_members_use_same_rule': True, 'status': 'proposed_pending_source_review'})
    return sorted(result, key=lambda r: r['base_question_id'])
