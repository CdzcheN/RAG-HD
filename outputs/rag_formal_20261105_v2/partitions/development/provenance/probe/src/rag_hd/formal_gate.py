"""Require saved training/validation model state before opening held-out inference."""
import json
from pathlib import Path

from .io import read_jsonl, fingerprint, file_sha256


def validate_test_freeze(run):
    run = Path(run)
    path = run/'model_freeze.json'
    if not path.exists():
        raise ValueError('Final test is held out: model/validation-threshold freeze is required before inference')
    certificate = json.loads(path.read_text())
    if (certificate.get('protocol_version')!='formal-model-freeze-v1' or
            certificate.get('threshold_origin')!='formal_validation_only'):
        raise ValueError('Invalid formal model freeze protocol')
    parent = run.parent.parent
    development = run.parent/'development'
    test_ids = {r['base_question_id'] for r in read_jsonl(run/'prepared.jsonl')}
    frozen_splits = json.loads((parent/'frozen_splits.json').read_text())
    if certificate.get('final_test_ids_sha256') != fingerprint(sorted(test_ids)):
        raise ValueError('Frozen final-test identities changed')
    confirmation = json.loads((development/'review_confirmation.json').read_text())
    if (confirmation['status']!='user_confirmed' or
            certificate.get('development_confirmation_sha256')!=file_sha256(development/'review_confirmation.json') or
            certificate.get('development_records_sha256')!=file_sha256(development/'records.jsonl')):
        raise ValueError('Training labels changed after model freeze')
    for seed in ('13','42','2026'):
        assignment = certificate['development_splits'][seed]
        for part in ('train','validation'):
            if set(assignment[part])!=set(frozen_splits[seed][part]) or set(assignment[part]) & test_ids:
                raise ValueError('Frozen training/validation sources mismatch or overlap final test')
    if not certificate.get('artifacts_sha256'):
        raise ValueError('No frozen model and threshold artifacts')
    for filename, digest in certificate['artifacts_sha256'].items():
        if file_sha256(Path(filename))!=digest:
            raise ValueError('Model/threshold artifact changed after freeze')
    return certificate
