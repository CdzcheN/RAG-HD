"""Cache MiniCheck re-scoring after visible source/date policy selection."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.io import file_sha256, fingerprint, read_jsonl, write_json, write_jsonl
from rag_hd.schema import visible_input
from rag_hd.valid_evidence import select, features


def extract(run, output):
    output.mkdir(parents=True,exist_ok=True)
    records = read_jsonl(run/'records.jsonl')
    config = json.loads((run/'config.json').read_text())
    implementation = {name:file_sha256(ROOT/'src/rag_hd'/name) for name in ('valid_evidence.py','minicheck_adapter.py')}
    expected = {r['sample_id']:fingerprint([visible_input(r),r['answer'],r['minicheck']['risk'],
                 config['minicheck'],implementation]) for r in records}
    path = output/'valid_evidence_cache.jsonl'
    cached = {r['sample_id']:r for r in read_jsonl(path)} if path.exists() else {}
    if any(sid not in expected or row['cache_key']!=expected[sid] for sid,row in cached.items()):
        raise ValueError('Stale policy score cache; choose a new output directory')
    needing_model=[]
    for r in records:
        if r['sample_id'] in cached:
            continue
        public = visible_input(r)
        selected = select(public)
        original = r['minicheck']['risk']
        row = {'sample_id':r['sample_id'],'cache_key':expected[r['sample_id']],
               'visible_input_sha256':fingerprint(public),'answer_sha256':fingerprint(r['answer']),
               'selection':selected,'original_risk':original}
        if r['is_refusal'] or original is None:
            row.update(filtered_risk=None,filtered_score={'status':'refusal_or_missing_baseline'},features=None)
        elif selected['evidence']==public['evidence']:
            row.update(filtered_risk=original,filtered_score={'status':'unchanged_reused_original'})
        elif not selected['evidence'].strip():
            row.update(filtered_risk=1.0,filtered_score={'status':'no_effective_evidence'})
        else:
            needing_model.append((r,row))
            continue
        cached[r['sample_id']]=row
    if needing_model:
        from rag_hd.minicheck_adapter import AnswerScorer
        from rag_hd.resources import GpuUsage
        meter=GpuUsage(config['generation']['memory_limit_mib'])
        try:
            with meter:
                scorer=AnswerScorer(config['minicheck'],ROOT/'.cache/minicheck/models')
                for index,(record,row) in enumerate(needing_model,1):
                    scored=scorer.score({'question':record['question'],'visible_evidence':row['selection']['evidence']},record['answer'])
                    row.update(filtered_risk=scored['risk'],filtered_score=scored)
                    cached[record['sample_id']]=row
                    write_jsonl(path,[cached[r['sample_id']] for r in records if r['sample_id'] in cached])
                    print(f'effective evidence MiniCheck {index}/{len(needing_model)}',flush=True)
        finally:
            if hasattr(meter,'result'):
                write_json(output/'resources.json',meter.result)
                write_jsonl(output/'vram_samples.jsonl',meter.samples)
        if not meter.result['within_limit']:
            raise RuntimeError('Resource limit or measurement failed')
    for record in records:
        row=cached[record['sample_id']]
        if row['original_risk'] is not None and row['filtered_risk'] is not None:
            row['features']=features(visible_input(record),record['answer'],row['original_risk'],row['filtered_risk'],row['selection'])
    write_jsonl(path,[cached[r['sample_id']] for r in records])
    write_json(output/'feature_manifest.json',{'rows':len(records),'new_model_calls':len(needing_model),
               'source_records_sha256':file_sha256(run/'records.jsonl'),'implementation':implementation,
               'feature_cache_sha256':file_sha256(path),'label_inputs_used':False,
               'purpose':'Development prototype; reviewed pilot is not a held-out final test.'})
    print(f'Cached {len(cached)} rows; {len(needing_model)} new MiniCheck calls.',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    extract(args.run_dir,args.output_dir)
