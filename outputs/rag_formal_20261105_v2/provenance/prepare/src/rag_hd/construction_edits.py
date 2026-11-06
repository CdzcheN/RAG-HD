"""Auditable span edits and explicit quantity constraints for controlled records."""
from dataclasses import dataclass, asdict
from decimal import Decimal
import re


@dataclass(frozen=True)
class Edit:
    field: str
    start: int
    end: int
    before: str
    after: str
    role: str


def locate(field, text, before, after, role, occurrence=None):
    positions = [m.start() for m in re.finditer(re.escape(before), text)]
    if not positions or (occurrence is None and len(positions) != 1):
        raise ValueError('Edit must have an unambiguous source span or explicit occurrence')
    index = 0 if occurrence is None else occurrence
    if not 0 <= index < len(positions):
        raise ValueError('Unknown occurrence')
    start = positions[index]
    return Edit(field,start,start+len(before),before,after,role)


def apply(fields, edits, required_mentions=()):
    """Only declared spans change; title, aliases and work titles are separate roles."""
    edits=list(edits)
    for field in {e.field for e in edits}:
        if field not in fields:
            raise ValueError('Unknown edit field')
        ordered=sorted((e for e in edits if e.field==field),key=lambda e:e.start)
        last=0
        for e in ordered:
            if not 0 <= e.start < e.end <= len(fields[field]) or e.start < last:
                raise ValueError('Out-of-bounds or overlapping edit')
            if fields[field][e.start:e.end] != e.before or not e.after.strip() or not e.role.strip():
                raise ValueError('Edit source mismatch or missing role')
            last=e.end
    for mention in required_mentions:
        field,start,end=mention['field'],mention['start'],mention['end']
        if fields[field][start:end]!=mention['text']:
            raise ValueError('Alias mention does not match source')
        if not any(e.field==field and e.start<=start and end<=e.end for e in edits):
            raise ValueError('Entity alias/title was not synchronized')
    result=dict(fields)
    for field in {e.field for e in edits}:
        for e in sorted((e for e in edits if e.field==field),key=lambda e:e.start,reverse=True):
            result[field]=result[field][:e.start]+e.after+result[field][e.end:]
    return result,[asdict(e) for e in edits]


def number(value):
    return Decimal(value.replace(',','').rstrip('%'))


def format_number(value, template):
    suffix='%' if template.endswith('%') else ''
    core=template.rstrip('%')
    precision=len(core.split('.')[1]) if '.' in core else 0
    grouping=',' if ',' in core else ''
    return format(value,f'{grouping}.{precision}f')+suffix


def quantity_change(old, direction, role='reported_quantity', lower=None, upper=None):
    if direction not in (-1,1):
        raise ValueError('Quantity direction must be +1 or -1')
    if role != 'reported_quantity':
        raise ValueError('Automatic temporal edits are limited to reported quantities, not event years or identities')
    if not re.fullmatch(r'[0-9][0-9,]*(?:\.[0-9]+)?%?',old):
        raise ValueError('Unsupported quantity format')
    precision=len(old.rstrip('%').split('.')[1]) if '.' in old else 0
    step=Decimal(1).scaleb(-precision)
    floor=Decimal(0) if lower is None else Decimal(str(lower))
    ceiling=Decimal(100) if old.endswith('%') and upper is None else Decimal(str(upper)) if upper is not None else None
    original=number(old)
    if original<floor or (ceiling is not None and original>ceiling):
        raise ValueError('Source quantity violates declared bounds')
    for sign in (direction,-direction):
        candidate=original+step*sign
        if candidate>=floor and (ceiling is None or candidate<=ceiling):
            return format_number(candidate,old)
    raise ValueError('No distinct quantity satisfies bounds')


def validate_constraints(values, constraints):
    """No eval: only explicitly declared sum and interval constraints are supported."""
    for constraint in constraints:
        if constraint['kind']=='sum':
            if sum(number(values[key]) for key in constraint['keys']) != Decimal(str(constraint['total'])):
                raise ValueError('Linked quantities violate the declared sum')
        elif constraint['kind']=='between':
            value=number(values[constraint['key']])
            if value<Decimal(str(constraint['lower'])) or value>Decimal(str(constraint['upper'])):
                raise ValueError('Quantity violates the declared interval')
        else:
            raise ValueError('Unknown constraint')
