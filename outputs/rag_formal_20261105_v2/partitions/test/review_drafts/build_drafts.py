"""Materialize the assistant's text-reviewed decisions; no detector scores are read."""
import csv,json,re,sys
from pathlib import Path
ROOT=Path('/home/yqhe/project/rgzn/RAG-HD');sys.path.insert(0,str(ROOT/'src'))
from rag_hd.io import read_jsonl,write_jsonl,write_json,fingerprint,file_sha256
from rag_hd.schema import visible_input
from rag_hd.review_packet import validate_suggestions
run=ROOT/'outputs/rag_formal_20261105_v2/partitions/test'
records=read_jsonl(run/'prepared.jsonl');gen={x['sample_id']:x for x in read_jsonl(run/'generation.jsonl')}
assert len(records)==len(gen)==120
# These row decisions were made after reading the question, answer and visible text.
# Ranges identify the inspected display order; they are not numeric-match label rules.
overrides={}
def decision(nums,label,correctness,reason):
 for n in nums:overrides[n]=(label,correctness,reason)
for n,reason in {
48:'查询2020-06-01，当前有效Pub记录为46001家；回答引用Evidence 1的46000，该证据有效期止于2019。即使正确转述旧证据，回答仍未按题目日期选版本，建议outdated。',
50:'查询2022-06-01，当前Apple审计记录为34%，回答35%来自2021旧版本。观察统计口径未变，只是受控记录版本差异，建议outdated。',
104:'查询2022-06-01，当前Upper Marlboro镇界内2010人口632，回答631仅见于2021旧版本，建议outdated。',
118:'查询2024-06-01，当前Suffolk County的2010人口1493349，回答1493350仅见于2023旧版本，建议outdated。',
}.items():decision([n],'outdated','incorrect',reason)
for n,reason in {
71:'回答先给Hank Williams的35首及11首冠军数，随后明确断言他没有录制Blue Love并以证据不足收尾；可见歌曲段落明确recorded by Hank Williams，构成直接反证。此回答已提出实质性事实，不能因为末尾拒答标记就抹掉错误，建议contradicted／incorrect。',
87:'79场属于Neil Harvey，回答错误归给Ray Harvey；可见Ray段落明确其failed to reach international standards，与79场国际Test赛的说法矛盾，建议contradicted／incorrect。',
88:'主来源79场属于Neil Harvey，回答仍错误归给Ray Harvey；Ray未达国际水平的可见叙述构成反证，不因数字恰好是主来源数就判supported。',
90:'主来源Thiruvananthapuram市区人口957730，回答957729取自次来源；不是都会区168万的混淆，依公开主来源规则建议contradicted。',
100:'主来源York River起源地Eliot的2010人口6204，回答6203取自次来源；实体链完整但统计数与主来源直接冲突，建议contradicted。',
}.items():decision([n],'contradicted','incorrect',reason)
for n,reason in {
66:'2822只属于Heber-Overgaard的2010人口；可见证据没有它与North Woodmere的关系，不能支持所问CDP的2822人口。隐藏参考用于正确性诊断，不补充可见反证，建议unsupported。',
72:'可见Some People Change的第7名属于Montgomery Gentry版本，不是Kenny Chesney单曲总数；既没有Kenny仅一首前十的完整统计，也未建立其录制Blue Love的关系，建议unsupported。',
74:'26185属于Coburg在2016年的统计，可见证据没有Bowral或Ian Hindmarsh的连接链；回答将该数归Bowral，无可见支持，建议unsupported。',
83:'主来源147是Terry Gray为Montreal、Boston、Los Angeles和St. Louis等球队效力的NHL合计；回答缩成仅为Boston打147场，原文不支持这个球队子集统计。没有分队场次表，不猜出另一精确数；建议unsupported／incorrect。',
84:'主来源147仍是Terry Gray多队生涯NHL合计，回答写成仅Boston的147场；即使选择了主来源数字，统计范围也不成立。按可见支撑缺失记unsupported，不用数字命中自动判正确。',
}.items():decision([n],'unsupported','incorrect',reason)
# Construction findings are semantic cautions, never filters for favorable scores.
approx_pairs={12,13,15,26,49}
bound_pairs={11}
with (run/'construction_review.csv').open(encoding='utf-8-sig',newline='') as f:crows=list(csv.DictReader(f))
drafts=[]
for n,r in enumerate(records,1):
 a=gen[r['sample_id']];anchors=[]
 if a['is_refusal']:
  label,correctness='undetermined','undetermined'
  reason='回答为明确拒答INSUFFICIENT_EVIDENCE，无所问事实主张，不作supported或幻觉正类；有支撑仍拒答时记漏答，保留该条。'
 elif n in overrides:label,correctness,reason=overrides[n]
 else:
  label,correctness='supported','correct'
  reason='已按问题对象、所问统计量及完整回答核对可见文本；实质性事实有支撑，且回应了所问数量。'
 # Anchors keep all relevant source passages and their public metadata. Retrieval
 # deletion/refusal cases retain all visible passages, without importing hidden gold.
 for e in r['evidence']:
  if not e.get('origin_document_id') and not (a['is_refusal'] or r['condition']=='retrieval_failure'):continue
  quote=e['text'];start=r['visible_evidence'].find(quote)
  assert start>=0
  anchors.append({'start':start,'end':start+len(quote),'quote':quote})
  header_start=r['visible_evidence'].rfind('[Evidence ',0,start)
  if header_start>=0:
   header_end=r['visible_evidence'].find('\n',header_start)
   anchors.append({'start':header_start,'end':header_end,'quote':r['visible_evidence'][header_start:header_end]})
 if not anchors:raise ValueError(n)
 if label=='supported' and n not in overrides:
  # This is an audit explanation after text review, not an automatic label rule.
  gov=[e for e in r['evidence'] if e.get('origin_document_id') and 'secondary' not in e['version'] and 'superseded_by' not in e['version'] and 'copy=current' not in e['version']]
  values=[str(v) for v in r['construction'].get('values_after',{}).values()]+[str(v) for v in r['construction'].get('values_before',{}).values()]
  excerpts=[]
  for e in gov:
   sentences=re.split(r'(?<=[.!?])\s+',e['text']);matches=[s for s in sentences if any(v in s for v in values)]
   excerpt=' '.join(matches) if matches else e['text']
   excerpts.append(e['title']+'：'+excerpt[:450])
  reason+='可见定位：'+'；'.join(excerpts)
  if 'Original question:' in r['question']:
   reason+='；采用题干规定的主来源或查询日期有效版本，未以另一版本的存在直接判幻觉。'
 draft={'display_number':n,'sample_id':r['sample_id'],'answer_sha256':fingerprint(a['answer']),'visible_input_sha256':fingerprint(visible_input(r)),'review_source':'assistant','status':'pending_user_review','evidence_label':label,'answer_correctness':correctness,'rationale':reason,'evidence_anchors':anchors,'semantic_refusal':a['is_refusal'] or n in []}
 drafts.append(draft)
validate_suggestions(read_jsonl(run/'review_requests.jsonl'),drafts)
constructions=[]
for n,row in enumerate(crows,1):
 a,b=records[2*n-2:2*n];da,db=drafts[2*n-2:2*n];finding='basic'
 reason='正常与挑战逐条对照，目标对象与观察时点一致，证据删除或版本标记及声明联动按规格保留。构造通过不要求模型一定回答错误。'
 if n in approx_pairs:
  finding='approximation_overlap';reason='新旧资料的近似数量仅做小幅改动，about/some/almost等范围可能重叠；只可称报告数字扰动，不能保证形成语义互斥的事实冲突。保留整组，不能按检测分数删除或按不同数字强制正类。'
 if n in bound_pairs:
  finding='bound_overlap';reason='原文是下界、上界或最大变化幅度，小幅修改后的可行范围可能重叠；只可称报告边界扰动，不保证形成相互排斥的事实。保留整组，回答依其真实语义判断。'
 if n==237:
  finding='question_scope_ambiguity';reason='来源给任命名额/上限合计103，而题干问实际任命总人数；名额不能代替实际任命。保留原始输入并标记问题范围歧义，生成后判断不补造事实。'
 initial=row['构造检查备注']
 reason=initial+'\n生成后助手检查（待用户确认）：'+reason+f" 正常回答建议{da['evidence_label']}／{da['answer_correctness']}，挑战回答建议{db['evidence_label']}／{db['answer_correctness']}。"
 constructions.append({'display_number':n,'pair_id':a['pair_id'],'review_source':'assistant','status':'pending_user_review','construction_finding':finding,'initial_note':initial,'rationale':reason})
for name,rows in [('answer_assessments.jsonl',drafts),('construction_assessments.jsonl',constructions)]:
 path=run/'review_drafts'/name
 if path.exists():raise ValueError('Refuse overwrite '+str(path))
 write_jsonl(path,rows)
write_json(run/'review_drafts/decision_provenance.json',{'method':'assistant_question_answer_visible_text_review','scores_read':False,'reviewed_display_ranges':[[1,120]],'explicit_override_rows':sorted(overrides),'human_confirmation':'pending','independent_double_annotation':False,'prepared_sha256':file_sha256(run/'prepared.jsonl'),'generation_sha256':file_sha256(run/'generation.jsonl')})
print('Validated 120 score-blind answer drafts and 60 construction drafts.')
