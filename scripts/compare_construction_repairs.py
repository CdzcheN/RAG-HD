"""Source-only before/after examples; never rescore or relabel legacy predictions."""
import argparse
import csv
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rag_hd.io import read_jsonl,write_json,file_sha256
from rag_hd.construction_edits import locate,apply,quantity_change


def compare(previous,output):
    output.mkdir(parents=True,exist_ok=True)
    records=read_jsonl(previous/'prepared.jsonl')
    corpus={d['document_id']:d for d in read_jsonl(previous/'corpus.jsonl')}
    frozen={name:file_sha256(previous/name) for name in ('prepared.jsonl','generation.jsonl','minicheck.jsonl','records.jsonl')}
    cases=[];audit=[]
    for number in (51,56,58):
        record=records[2*number-2]
        documents=[corpus[doc_id] for doc_id in record['audit']['gold_document_ids']]
        before=[];after=[]
        for doc in documents:
            fields={'title':doc['title'],'text':doc['text']};edits=[]
            def edit(field,old,new,role,occurrence=None):
                if old in fields[field]:
                    edits.append(locate(field,fields[field],old,new,role,occurrence))
            if number==51:
                edit('title','Phil McGraw','Vincente Minnelli','entity_title')
                edit('text','Phil McGraw','Vincente Minnelli','cast_entity')
                edit('text','Phillip Calvin McGraw','Vincente Minnelli','canonical_entity')
                edit('text','Dr. Phil','Vincente Minnelli','person_alias',0)
                edit('text','McGraw first','Minnelli first','surname_reference')
            elif number==56:
                edit('title','Lester B. Pearson','Kaui Hart','entity_title')
                edit('text','Lester Bowles "Mike" Pearson','Kaui Hart','canonical_entity')
                edit('text','Lester B. Pearson','Kaui Hart','commission_entity')
            else:
                edit('title','Anna Nicole Smith','Lee Na-jeong','professional_name_title')
                edit('text','Anna Nicole Smith','Lee Na-jeong','professional_name')
                edit('text','Smith first','Lee first','professional_surname')
            mentions=[{'field':e.field,'start':e.start,'end':e.end,'text':e.before} for e in edits]
            modified,log=apply(fields,edits,mentions)
            if number==51 and 'host of the television show' in fields['text']:
                if '"Dr. Phil"' not in modified['text']:
                    raise ValueError('Work title must not be mistaken for person alias')
            before.append(fields['title']+'\n'+fields['text'])
            after.append(modified['title']+'\n'+modified['text'])
            audit.append({'old_pair':number,'source_document_id':doc['document_id'],
                          'required_entity_mentions':mentions,'edits':log,'legacy_prediction_changed':False})
        cases.append({'样例':f'旧构造第{number}组','问题':'全名、简称、标题或跨篇人物别名没有同步',
                      '修正前':'\n\n'.join(before),'修正后':'\n\n'.join(after),
                      '检查结论':'针对已核对的实体提及同步编辑；作品标题、出生名等不同语义角色分别处理。仅作构造回归例，不重评旧回答。'})
    rewrites={12:'Which Russian actress, born July 28, 1969, is the daughter of the director of Moscow Does Not Believe in Tears?',
              17:'What type of mollusc is an oyster, associated with the oyster bars that returned to Schultz Preserve after restoration?',
              48:'In what year did the British airship R34 make the first non-stop transatlantic crossing described in the record?'}
    for number,question in rewrites.items():
        old=records[2*number-2]['audit']['original_question']
        cases.append({'样例':f'旧构造第{number}组','问题':'题干错误关系或未明确的指代',
                      '修正前':old,'修正后':question,
                      '检查结论':'这是有来源依据的显式改写，任务表述发生变化；不把新问法回填到旧预测或旧标签。'})
    try:
        quantity_change('1979',1,role='founding_year')
    except ValueError:
        cases.append({'样例':'旧构造第60组','问题':'成立年份改为1983，但正文仍写1980年已有产品',
                      '修正前':'直接替换成立年份，未检查内部先后关系',
                      '修正后':'修正版禁止自动修改出生/死亡/成立等事件年份；本例不进入统计数量更正试点。',
                      '检查结论':'拒绝这类自动时间构造，避免把数量更正接口用于事件年份。'})
    else:raise ValueError('Event-year guard did not reject unsafe use')
    path=output/'修正前后对照.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['样例','问题','修正前','修正后','检查结论'])
        writer.writeheader();writer.writerows(cases)
    if any(file_sha256(previous/name)!=sha for name,sha in frozen.items()):
        raise ValueError('Legacy data/predictions unexpectedly changed')
    write_json(output/'alias_repair_audit.json',audit)
    write_json(output/'comparison_validation.json',{'cases':len(cases),'score_inputs_used':False,
               'legacy_files_unchanged':True,'legacy_sha256':frozen})
    print(f'Wrote {len(cases)} source-audited comparison examples; legacy predictions unchanged.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-run',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();compare(args.previous_run,args.output_dir)
