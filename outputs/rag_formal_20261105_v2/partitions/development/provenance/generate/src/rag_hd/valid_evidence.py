"""Select evidence using only explicitly visible source/date policies."""
from datetime import date
import re

from .io import fingerprint
from .retrieval import tokenize

HEADER = re.compile(r'^\[Evidence (\d+); title: (.*?); version: ([^\n]*)\]\n', re.M)
STOP = set('a an the is are was were be been being of in on at to for from by with and or as its it that this which what who when where how did does do has have had s'.split())


def select(public):
    question, text = public['question'], public['evidence']
    matches = list(HEADER.finditer(text))
    # Unknown rendering or ambiguous rule: preserve the baseline input, do not invent a policy.
    if not matches or matches[0].start() != 0:
        return {'mode':'none','evidence':text,'selected_body':text,'excluded_body':'',
                'kept':[], 'dropped':[], 'drop_fraction':0.0, 'reason':'unrecognized_rendering'}
    entries = []
    for index, match in enumerate(matches):
        end = matches[index+1].start() if index+1 < len(matches) else len(text)
        entries.append({'rank':int(match[1]),'version':match[3],
                        'body':text[match.end():end].strip(), 'full':text[match.start():end].strip()})
    lower = question.casefold()
    authority = ('record policy:' in lower and 'source_tier=primary' in lower and
                 'source_tier=secondary cannot override' in lower)
    dates = re.findall(r'Query date:\s*(\d{4}-\d{2}-\d{2})',question)
    temporal = len(dates)==1 and 'record policy:' in lower and 'validity interval' in lower
    mask = [True]*len(entries)
    mode, reason = 'none', 'no_explicit_supported_policy'
    if temporal:
        try:
            query = date.fromisoformat(dates[0])
            intervals = []
            for entry in entries:
                starts = re.findall(r'(?<!\w)valid_from=(\d{4}-\d{2}-\d{2})(?!\d)', entry['version'])
                ends = re.findall(r'(?<!\w)valid_until=(\d{4}-\d{2}-\d{2})(?!\d)', entry['version'])
                if len(starts)>1 or len(ends)>1 or bool(starts)!=bool(ends):
                    raise ValueError('Ambiguous/incomplete interval')
                if starts:
                    start,end = date.fromisoformat(starts[0]),date.fromisoformat(ends[0])
                    if start>end:
                        raise ValueError('Reversed interval')
                    intervals.append(start<=query<=end)
                else:
                    intervals.append(False)
            mask, mode, reason = intervals, 'time', 'explicit_query_date_and_validity_intervals'
        except ValueError:
            temporal = False
            reason = 'invalid_date_policy_fallback_to_all'
    if authority:
        tier_masks = [bool(re.search(r'(?:^|;\s*)source_tier=primary(?:;|$)',e['version'])) for e in entries]
        # If the policy names primary but none exists, insufficient effective evidence is observable.
        mask = [a and b for a,b in zip(mask,tier_masks)]
        mode, reason = ('authority_time' if temporal else 'authority'), 'explicit_primary_priority'
    selected = [e for e,keep in zip(entries,mask) if keep]
    excluded = [e for e,keep in zip(entries,mask) if not keep]
    return {'mode':mode,'evidence':'\n\n'.join(e['full'] for e in selected),
            'selected_body':'\n'.join(e['body'] for e in selected),
            'excluded_body':'\n'.join(e['body'] for e in excluded),
            'kept':[e['rank'] for e in selected], 'dropped':[e['rank'] for e in excluded],
            'drop_fraction':len(excluded)/len(entries),'reason':reason}


def words(text):
    return set(tokenize(text))-STOP


def coverage(values, evidence):
    return len(values & evidence)/len(values) if values else 1.0


def features(public, answer, original_risk, filtered_risk, selection):
    """Inputs intentionally have no labels, audit, condition, references or gold supports."""
    original_body = HEADER.sub('',public['evidence'])
    original_words = words(original_body)
    question_words = words(public['question'].rsplit('Original question:',1)[-1])
    answer_words = words(answer)
    kept, dropped = words(selection['selected_body']),words(selection['excluded_body'])
    numbers = set(re.findall(r'\b\d+(?:[,.]\d+)*\b',answer))
    kept_numbers = set(re.findall(r'\b\d+(?:[,.]\d+)*\b',selection['selected_body']))
    dropped_numbers = set(re.findall(r'\b\d+(?:[,.]\d+)*\b',selection['excluded_body']))
    missing_words = len(answer_words & (dropped-kept))/len(answer_words) if answer_words else 0.0
    missing_numbers = len(numbers & (dropped_numbers-kept_numbers))/len(numbers) if numbers else 0.0
    authority = selection['mode'] in ('authority','authority_time')
    temporal = selection['mode'] in ('time','authority_time')
    delta = filtered_risk-original_risk
    return {'minicheck_risk':original_risk,
            'question_coverage':coverage(question_words,original_words),
            'answer_coverage':coverage(answer_words,original_words),
            'answer_number_coverage':coverage(numbers,set(re.findall(r'\b\d+(?:[,.]\d+)*\b',original_body))),
            'authority_risk_delta':delta if authority else 0.0,
            'authority_excluded_token_fraction':missing_words if authority else 0.0,
            'authority_drop_fraction':selection['drop_fraction'] if authority else 0.0,
            'time_risk_delta':delta if temporal else 0.0,
            'time_excluded_token_fraction':missing_words if temporal else 0.0,
            'time_excluded_number_fraction':missing_numbers if temporal else 0.0,
            'time_drop_fraction':selection['drop_fraction'] if temporal else 0.0}


GROUPS = {'base':['minicheck_risk'],
          'lexical':['question_coverage','answer_coverage','answer_number_coverage'],
          'authority':['authority_risk_delta','authority_excluded_token_fraction','authority_drop_fraction'],
          'time':['time_risk_delta','time_excluded_token_fraction','time_excluded_number_fraction','time_drop_fraction']}
