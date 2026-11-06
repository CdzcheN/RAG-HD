"""Materialize the assistant's text-reviewed decisions; no detector scores are read."""
import csv,json,re,sys
from pathlib import Path
ROOT=Path('/home/yqhe/project/rgzn/RAG-HD');sys.path.insert(0,str(ROOT/'src'))
from rag_hd.io import read_jsonl,write_jsonl,write_json,fingerprint,file_sha256
from rag_hd.schema import visible_input
from rag_hd.review_packet import validate_suggestions
run=ROOT/'outputs/rag_formal_20261105_v2/partitions/development'
records=read_jsonl(run/'prepared.jsonl');gen={x['sample_id']:x for x in read_jsonl(run/'generation.jsonl')}
assert len(records)==len(gen)==480
# These row decisions were made after reading the question, answer and visible text.
# Ranges identify the inspected display order; they are not numeric-match label rules.
overrides={}
def decision(nums,label,correctness,reason):
 for n in nums:overrides[n]=(label,correctness,reason)
decision([75,76],'contradicted','correct','数量约35000回答到位，但额外声称Evidence 1与2均为primary；可见头明确一份secondary、一份primary。整段回答存在可见元数据反证，不能只按数值吻合判supported；正确性列仅就所问数量记correct。')
for n,reason in {
90:'主来源STEP为114个抛物面碟，回答115取自次来源，与公开优先规则及主来源明确冲突。',
98:'主来源载明1587年College最大规模70，回答69是次来源版本；这是所设上限本身的差异，不是实际人数在范围内的比较。',
114:'主来源1991年Rajasthan女性识字率20.44%，回答20.43%取自次来源。',
248:'主来源Alexandria的2010人口139966，回答139965取自次来源。',
282:'主来源Georgica Pond面积290英亩，回答291取自次来源。',
292:'主来源Olympia的2010人口46478，回答46477取自次来源。',
398:'主来源太阳红外线所占加热份额49%，回答50%取自次来源。',
444:'主来源Coney Island住宅区人口60000，回答60001取自次来源。',
452:'主来源Gilford的2010人口7126，回答7125取自次来源。',
454:'主来源College of Southern Nevada教职及非教职员工合计2900，回答2899取自次来源。',
460:'主来源Clemson于2016年秋本科生18599，回答18598取自次来源。',
463:'可见MindLeaders段落明确Element K在2011年被Skillsoft收购，9999客户也属于Skillsoft；回答误指MindLeaders，关系存在明确反证，不能因数字吻合判correct。',
467:'可见记录明确破纪录者是Pelé，1280进球属Pelé；Rosas自己也被记载在世界杯有多个进球。回答把Rosas说成破自己纪录者并仅1个生涯进球，存在明确反证。',
468:'当前有效记录仍明确Pelé打破Rosas纪录且Rosas在世界杯有多个进球。回答把1个生涯进球归Rosas，不能由首个进球叙述推出总数1，也不是简单沿用旧版1281。',
}.items():decision([n],'contradicted','incorrect',reason)
for n,reason in {
148:'查询2024版本，当前记录2011年Samoa联赛11队；回答10队仅见于2023旧版本，记outdated。',
312:'查询2020版本，当前Chanhassen的2010人口22951；回答22952仅见于2019旧版本，记outdated。',
338:'查询2022版本，当前Marquette的2010人口640；回答641仅见于2021旧版本，记outdated。',
406:'查询2024版本，当前Mueller集群为7台PS3；回答8台仅见于2023旧版本，记outdated。',
}.items():decision([n],'outdated','incorrect',reason)
for n,reason in {
184:'可见Love as a Predatory Affair的21集及演员Stephanie Ho，不能支持Stephanie Lee出演21集；人物、作品与所问SBS剧的关系没有证据。隐藏参考只用于正确性诊断，不作可见反证。',
192:'161是Heath Hill的2016人口，但可见文本没有Brummels Gallery位于Heath Hill的关系；回答添加无依据地点链。',
238:'Greg Kuzma可见段落只支持写出版30多本，未支持“since the mid-1970s”的时间范围，更未建立其为Foreigner创作者的关系；不能借另一作者数量回答。',
424:'3103属于Brightwaters的2010人口；当前可见证据没有它与2014 Cheez-It赛事举办村落的关系，所问实体链缺失。',
430:'可见Hawley人口2067明确对应2010；回答改成2011且答成其他地点。不同年份无法用2010值直接反证2011值，但2011事实没有支持，故unsupported而非contradicted。',
476:'可见Billy Ray Cyrus仅提到一张首张专辑，不能据此断言其全部录音室专辑总数为1；所问歌曲歌手实际为Alan Jackson，当前段落支持15张。故无依据且答错对象，不自动按时间挑战记outdated。',
}.items():decision([n],'unsupported','incorrect',reason)
for n,reason in {
126:'当前记录为some 97，旧记录some 98，回答some 98；近似数量仅差1且问题问about，没有误差界可排除同一真实范围，不能仅凭命中旧数字判outdated。',
166:'当前about 10001、旧about 10000，回答approximately 10000；近似范围可能重叠，不凭±1制造过时正类。',
170:'原文at least 28%是下界，回答只说28%；可能为题目要求的下界简写，也可能误当精确比例，语义不足以裁定，保留undetermined。',
386:'主来源about 30、次来源about 29，回答about 29；近似范围可能重叠，没有精度定义支持明确反证，保留undetermined。',
474:'原文为各区规定名额合计103，回答写每区up to 103又称合计已委任103；混合个别上界、总名额与实际任命数，不能明确判定其目标陈述，保留undetermined。',
}.items():decision([n],'undetermined','undetermined',reason)
for n in [131,172,179,180,375]:decision([n],'undetermined','undetermined','这是带解释文字或自然语言形式的拒答，没有给出所问事实数量；即使证据中有答案，仍作为漏答诊断，不转成幻觉正类。原始精确拒答标记未识别此写法，保留原始推理产物并另记语义拒答。')
decision([351,352],'supported','incorrect','回答所陈述的Carpenters身份有可见Sedaka’s Back段落支持，但未给出问题所求专辑数量（当前版本10）。证据支持与答题正确性分开，不能因未答数量把真实身份陈述当幻觉。')
decision([473],'supported','undetermined','原文支持may appoint/up to及总名额103，回答也保留may/up to；但题干问实际任命总数，资料只给任命限额，故事实有支持而答题正确性保留undetermined。')
# Construction findings are semantic cautions, never filters for favorable scores.
approx_pairs={38,43,46,55,62,63,70,77,82,83,84,193,204,208,223}
bound_pairs={34,40,48,52,64,85,192,202,209}
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
 draft={'display_number':n,'sample_id':r['sample_id'],'answer_sha256':fingerprint(a['answer']),'visible_input_sha256':fingerprint(visible_input(r)),'review_source':'assistant','status':'pending_user_review','evidence_label':label,'answer_correctness':correctness,'rationale':reason,'evidence_anchors':anchors,'semantic_refusal':a['is_refusal'] or n in [131,172,179,180,375]}
 drafts.append(draft)
validate_suggestions(read_jsonl(run/'review_requests.jsonl'),drafts)
constructions=[]
for n,row in enumerate(crows,1):
 a,b=records[2*n-2:2*n];da,db=drafts[2*n-2:2*n];finding='basic'
 reason='正常与挑战逐条对照，目标对象与观察时点一致，证据删除或版本标记及声明联动按规格保留。构造通过不要求模型一定回答错误。'
 if n in approx_pairs:
  finding='approximation_overlap';reason='新旧资料的近似数量仅做小幅改动，about/some等范围可能重叠；只可称报告数字扰动，不能保证形成语义互斥的事实冲突。保留整组，不能按检测分数删除或按不同数字强制正类。'
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
write_json(run/'review_drafts/decision_provenance.json',{'method':'assistant_question_answer_visible_text_review','scores_read':False,'reviewed_display_ranges':[[1,480]],'explicit_override_rows':sorted(overrides),'human_confirmation':'pending','independent_double_annotation':False,'prepared_sha256':file_sha256(run/'prepared.jsonl'),'generation_sha256':file_sha256(run/'generation.jsonl')})
print('Validated 480 score-blind answer drafts and 240 construction drafts.')
