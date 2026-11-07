"""Draft offline mechanism benchmark. No execution without separate frozen permit.
Python stdlib only; no production edits, network, model calls, or cloud dependencies.
"""
from __future__ import annotations
import argparse
from bisect import bisect_left, bisect_right
import dataclasses
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import platform
import random
import re
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = Path('/Users/Anil/.codex/worktrees/27da/lifesight-platform-mia-agents')
SUT = REPO / 'harness-core/harness_core/provenance.py'
HEAD = '744d96938daabb8be0c83974c78b0348b8fc2ac2'
SUT_SHA = 'c90e00fde672964e208f6e18ae415c83a4296267c9d3c4e1cfaa52e7ea081a02'
D = Decimal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


@dataclasses.dataclass(frozen=True)
class Fact:
    id: str
    source_id: str
    entity: str
    metric: str
    start: str
    end: str
    unit: str
    currency: str | None
    value: str

    def binding(self):
        return {k: getattr(self, k) for k in ('entity', 'metric', 'start', 'end', 'unit', 'currency')}


# The independent checker accepts only this declared display grammar; it never calls SUT.
DISPLAY = re.compile(r'^(?P<value>-?[0-9]+(?:\.[0-9]+)?)(?P<suffix>K|M|x|%)?(?: \((?P<a>[0-9]+(?:\.[0-9]+)?) / (?P<b>[0-9]+(?:\.[0-9]+)?)\))?$')


def read_display(text):
    m = DISPLAY.fullmatch(text)
    if not m:
        raise ValueError('unsupported canonical display')
    value = D(m['value']) * {'K': D(1000), 'M': D(1000000)}.get(m['suffix'], D(1))
    digits = len(m['value'].replace('.', '').lstrip('-0'))
    # Precision is independently defined by rendered digits, capped at six; compact display retains trailing zeros.
    p = max(2, min(6, digits))
    return value, p, 'multiplier' if m['suffix'] == 'x' else 'percent' if m['suffix'] == '%' else 'amount', m


def quantum(value, p):
    return D(1).scaleb(abs(value).adjusted() - p + 1) if value else D(1).scaleb(1-p)


def same_display(expected, value, p):
    # Decimal half-even rounding; no import or adaptation of the tested match algorithm.
    with localcontext() as ctx:
        ctx.prec = 40
        q = quantum(value, p)
        return expected.quantize(q, rounding=ROUND_HALF_EVEN) == value.quantize(q, rounding=ROUND_HALF_EVEN)


def derive(facts, operation):
    """Explicit independent semantic policy, returning expected value and binding."""
    a = facts[0]
    binding = a.binding()
    if operation == 'direct' and len(facts) == 1:
        return D(a.value), binding
    if len(facts) != 2:
        raise ValueError('two operands required')
    b = facts[1]
    if (a.start, a.end, a.currency) != (b.start, b.end, b.currency):
        raise ValueError('incomparable date/currency')
    av, bv = D(a.value), D(b.value)
    if operation in ('sum', 'difference'):
        if (a.metric, a.unit) != (b.metric, b.unit):
            raise ValueError('incomparable dimensions')
        binding['entity'] = 'all' if operation == 'sum' else 'contrast'
        return (av + bv if operation == 'sum' else av - bv), binding
    if operation in ('ratio', 'percent'):
        if (a.entity, a.metric, b.metric, a.unit, b.unit) != (b.entity, 'revenue', 'spend', 'currency', 'currency') or not bv:
            raise ValueError('ratio policy permits revenue/spend for same entity only')
        binding.update(metric='roas' if operation == 'ratio' else 'revenue_share', unit='multiplier' if operation == 'ratio' else 'percent', currency=None)
        return av / bv * (100 if operation == 'percent' else 1), binding
    raise ValueError('operation outside policy')


def semantic_check(text, fact_index):
    """Prototype source-bound reference checker; reads observable text and evidence, never labels."""
    try:
        claim = json.loads(text)
        value, p, kind, match = read_display(claim['display'])
        selected = [fact_index[x] for x in claim['operands']]
        expected, binding = derive(selected, claim['operation'])
        if kind != ('multiplier' if binding['unit'] == 'multiplier' else 'percent' if binding['unit'] == 'percent' else 'amount'):
            return False, 'unit kind mismatch'
        if binding != claim['binding']:
            return False, 'binding mismatch'
        if match['a'] is not None and (D(match['a']), D(match['b'])) != tuple(D(f.value) for f in selected):
            return False, 'displayed operands mismatch'
        return same_display(expected, value, p), 'canonical source-bound prototype'
    except (KeyError, ValueError, TypeError, ArithmeticError, json.JSONDecodeError) as exc:
        return False, 'unresolved:' + type(exc).__name__


def numerical_universe(facts):
    """Finite, explicit numeric oracle: raw values and within-source pair arithmetic.
    It intentionally ignores entity/metric/date/unit. Includes signed values, never abs-folding.
    No totals of arbitrary subsets and no undeclared cross-source operations.
    """
    by_source = {}
    values = {D(f.value) for f in facts}
    for f in facts:
        by_source.setdefault(f.source_id, []).append(D(f.value))
    for operands in by_source.values():
        for a, b in itertools.combinations(operands, 2):
            values.update((a+b, a-b, b-a))
            if a and b:
                values.update((a/b, b/a, 100*a/b, 100*b/a, 100*(a-b)/b, 100*(b-a)/a))
    return sorted(values)


def numeric_supported(universe, value, p):
    q = quantum(value, p)
    half = q/2
    center = value.quantize(q, rounding=ROUND_HALF_EVEN)
    left, right = bisect_left(universe, center-half), bisect_right(universe, center+half)
    return any(same_display(x, value, p) for x in universe[left:right])


def label_claim(claim, facts, universe):
    # Semantic label is reconstructed from source data; the generator family is not the label.
    value, p, kind, _ = read_display(claim['display'])
    full, reason = semantic_check(encoded(claim), {f.id: f for f in facts})
    return {'full_fact_correct': full, 'numeric_support': numeric_supported(universe, value, p),
            'numeric_policy': 'finite-raw/signed-within-source-pairs-v1-not-all-LAH-support', 'rationale': reason,
            'target_value': str(value), 'precision': p, 'kind': kind}


def fmt(value, p):
    return format(value.quantize(quantum(value, p), rounding=ROUND_HALF_EVEN), 'f')


def synthetic(seed, n_sources, per_family):
    rng = random.Random(seed)
    facts, sources = [], []
    for i in range(n_sources):
        sid = 'source_' + chr(97 + i % 26) + '_' + str(i).zfill(6) + '_data'
        rows = []
        for entity in ('alpha', 'beta'):
            spend = D(rng.randrange(10000001, 90000000)) / 100
            revenue = spend * D(rng.randrange(301, 899)) / 100
            for metric, value in (('spend', spend), ('revenue', revenue), ('cost', D(rng.randrange(10000001, 90000000))/100), ('margin', D(rng.randrange(10000001, 90000000))/100)):
                fid = 'fact_' + chr(97 + len(facts) % 26) + '_' + str(len(facts)).zfill(7) + '_data'
                fact = Fact(fid, sid, entity, metric, '2026-01-01', '2026-01-31', 'currency', 'USD', str(value))
                facts.append(fact)
                rows.append(dict(fact.binding(), fact_id=fid, **{metric: float(value)}))
        sources.append({'id': sid, 'kind': 'result:synthetic', 'payload': {'rows': rows}})
    families = ('direct_exact', 'direct_compact', 'sum', 'difference', 'ratio_named', 'percent',
                'random_value', 'near_value', 'wrong_entity', 'wrong_date', 'wrong_currency', 'wrong_sign')
    claims = []
    for family in families:
        for j in range(per_family):
            offset = (j * (n_sources-1) // max(1, per_family-1)) * 8
            a, b = facts[offset], facts[offset+4]
            operation = {'sum':'sum','difference':'difference','ratio_named':'ratio','percent':'percent'}.get(family, 'direct')
            selected = [facts[offset+1], a] if operation in ('ratio', 'percent') else [a,b] if operation in ('sum','difference') else [a]
            value, binding = derive(selected, operation)
            if family == 'direct_compact':
                display = fmt(value / 1000, 4) + 'K'
            elif operation == 'ratio':
                display = fmt(value, 3) + 'x (' + selected[0].value + ' / ' + selected[1].value + ')'
            elif operation == 'percent':
                display = fmt(value, 6) + '%'
            else:
                display = format(value, 'f')
            if family == 'random_value':
                display = str(D(rng.randrange(10000001, 90000000))/100)
            elif family == 'near_value':
                display = str(value + D('1234.57'))
            elif family == 'wrong_entity':
                binding['entity'] = 'absent_entity'
            elif family == 'wrong_date':
                binding['start'], binding['end'] = '2025-01-01', '2025-01-31'
            elif family == 'wrong_currency':
                binding['currency'] = 'EUR'
            elif family == 'wrong_sign':
                display = '-' + format(value, 'f')
            claims.append({'id': family+'_'+str(j), 'family': family, 'claim': {'display': display, 'operation': operation, 'operands':[f.id for f in selected], 'binding': binding}})
    return sources, facts, claims


def load_sut(snapshot):
    spec = importlib.util.spec_from_file_location('lah_benchmark_pinned_sut', snapshot)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def state(ledger):
    # Observational private-state reads only. Complete bands avoid conflating cap with support.
    return {'held': ledger._held, 'exact_values': sorted(ledger._exact), 'n_bases': ledger._n_bases,
            'totals': ledger._totals, 'groups': ledger._groups,
            'sources': [{'kind':s.kind, 'values':s.values, 'bases':s.bases, 'operands':s.operands,
                         'counts':sorted(s.counts), 'named':s.named, 'named_currency':s.named_currency,
                         'group_families':repr(s.group_families)} for s in ledger._sources]}


def direct_baseline(text, raw_values):
    try:
        value, p, _kind, _ = read_display(json.loads(text)['display'])
        return any(same_display(v, value, p) for v in raw_values), 'independent raw direct-only Decimal baseline'
    except (ValueError, KeyError, json.JSONDecodeError):
        return False, 'unsupported'


def run_cell(config, out, module):
    sources, facts, claims = synthetic(config['seed'], config['sources'], config['per_family'])
    universe = numerical_universe(facts)
    # Immutable evidence/labels first, then evaluate. Existing output directories are forbidden.
    out.mkdir(parents=True, exist_ok=False)
    dump(out/'inputs.json', {'sources':sources, 'facts':[dataclasses.asdict(f) for f in facts], 'claims':claims})
    labeled = [(c, label_claim(c['claim'], facts, universe)) for c in claims]
    dump(out/'gold.json', [{'id':c['id'], **gold} for c,gold in labeled])
    ledger = module.NumberLedger()
    start = time.perf_counter_ns()
    for source in sources:
        ledger.add_from(source['payload'], kind=source['kind'])
    build_ns = time.perf_counter_ns() - start
    retained = state(ledger)
    retained['source_identity_by_position'] = ['constructor']+[source['id'] for source in sources]
    dump(out/'retained_state.json', retained)
    raw_full = [D(f.value) for f in facts]
    # Fair retained-state baseline: actual raw fact values present in per-source retained values.
    raw_retained = [D(f.value) for f in facts if any(s.kind and float(f.value) in s.values for s in ledger._sources)]
    source_positions = {source['id']:i+1 for i,source in enumerate(sources)}
    idx = {f.id:f for f in facts}
    calls = {'current.explained':0, 'current.find_ungrounded':0, 'direct_retained':0, 'direct_full_inventory':0}
    errors = []
    rows = []
    for c,gold in labeled:
        text = encoded(c['claim'])
        row = {'id':c['id'], 'family':c['family'], 'text':text, 'gold':gold, 'results':{}}
        for arm in calls:
            calls[arm] += 1
            start = time.perf_counter_ns()
            try:
                if arm == 'current.explained':
                    outputs = ledger.explained(text)
                    accepted = bool(outputs) and all(why is not None for _,why in outputs)
                    detail = [{'value':f.value,'kind':f.kind,'raw':f.raw,'precision':f.precision,'why':why} for f,why in outputs]
                    result = {'accepted':accepted, 'target_accepted':outputs[0][1] is not None if outputs else None, 'not_parsed':not outputs, 'exempt_tokens':sum(why=='exempt' for _,why in outputs), 'tokens':detail}
                elif arm == 'current.find_ungrounded':
                    result = {'accepted':not ledger.find_ungrounded(text), 'note':'empty parse accepts vacuously; explained records coverage'}
                elif arm.startswith('direct_'):
                    accepted, why = direct_baseline(text, raw_retained if arm=='direct_retained' else raw_full)
                    result = {'accepted':accepted, 'why':why}
                result['elapsed_ns'] = time.perf_counter_ns()-start
            except Exception:
                result = {'accepted':None, 'elapsed_ns':time.perf_counter_ns()-start, 'error':traceback.format_exc()}
                errors.append({'id':c['id'],'arm':arm,'trace':result['error']})
            row['results'][arm] = result
        rows.append(row)
    with (out/'observations.jsonl').open('w') as stream:
        for row in rows:
            stream.write(encoded(row)+'\n')
    availability = []
    availability_ns = 0
    for f in facts:
        begin = time.perf_counter_ns()
        result = ledger.explained(f.value)
        availability_ns += time.perf_counter_ns()-begin
        availability.append({'fact_id':f.id, 'raw_value_retained':float(f.value) in ledger._sources[source_positions[f.source_id]].values,
            'public_direct_text_quotable':bool(result) and all(why is not None for _,why in result),
            'explanation':[why for _,why in result], 'value':f.value})
    calls['availability.explained'] = len(facts)
    dump(out/'availability.json', availability)
    dump(out/'summary.json', {'config':config,'build_ns':build_ns,'availability_check_ns':availability_ns,'calls':calls,'claims':len(claims), 'failures':errors,
                              'retries':0, 'note':'all attempts preserved; no automatic retry; analysis must use seed clusters'})


def validate_cases():
    a = Fact('fact_alpha_data','source_alpha_data','alpha','spend','2026-01-01','2026-01-31','currency','USD','120000')
    b = dataclasses.replace(a,id='fact_beta_data',entity='beta',value='230000')
    r = dataclasses.replace(a,id='fact_revenue_data',metric='revenue',value='360000')
    facts = {f.id:f for f in (a,b,r)}
    cases = [({'display':'120000','operation':'direct','operands':[a.id],'binding':a.binding()},True),
             ({'display':'-120000','operation':'direct','operands':[a.id],'binding':a.binding()},False),
             ({'display':'120000','operation':'direct','operands':[a.id],'binding':dict(a.binding(),entity='beta')},False),
             ({'display':'350000','operation':'sum','operands':[a.id,b.id],'binding':dict(a.binding(),entity='all')},True),
             ({'display':'3.00x (360000 / 120000)','operation':'ratio','operands':[r.id,a.id],'binding':dict(a.binding(),metric='roas',unit='multiplier',currency=None)},True)]
    for claim, expected in cases:
        assert semantic_check(encoded(claim),facts)[0] is expected, (claim,expected)
    assert same_display(D('123456'),D('123500'),4)
    assert not same_display(D('123456'),D('123600'),4)
    u = numerical_universe([a,b])
    assert numeric_supported(u,D('350000'),6)
    assert numeric_supported(u,D('230000'),6)
    assert not numeric_supported(u,D('999999'),6)
    assert numeric_supported([D('123457.4')],D('123456.78'),6)
    split = numerical_universe([a,dataclasses.replace(b,source_id='other_source_data')])
    assert not numeric_supported(split,D('350000'),6)
    invalid = dict(cases[-1][0], display='3.00x (360000 / 0)')
    assert not semantic_check(encoded(invalid),facts)[0]
    bad_date = dataclasses.replace(b,start='2025-01-01')
    try:
        derive([a,bad_date],'sum')
    except ValueError:
        pass
    else:
        raise AssertionError('incomparable dates accepted by oracle')
    return {'semantic_hand_checked_cases':len(cases)+2, 'numeric_hand_checked_cases':7, 'result':'passed'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--permit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    permit = json.loads(args.permit.read_text())
    # Hash-bound root-issued freeze, never inferred from elapsed time or file presence alone.
    assert permit['authorized_by_root'] is True
    assert permit['runner_sha256'] == sha(__file__)
    assert permit['sut_sha256'] == SUT_SHA == sha(SUT)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()==HEAD
    assert permit['phase'] in ('pilot','heldout')
    if permit['phase']=='pilot':
        assert all(c['seed'] in (9001,9002) for c in permit['cells'])
    else:
        assert all(c['seed'] in range(1001,1011) for c in permit['cells'])
    args.output.mkdir(parents=True,exist_ok=False)
    snapshot = args.output/'sut_provenance.py'
    snapshot.write_bytes(SUT.read_bytes())
    dump(args.output/'run_manifest.json', {'status':'started','permit':permit, 'python':sys.version,
          'platform':platform.platform(), 'head':HEAD,'runner_sha256':sha(__file__), 'sut_sha256':sha(snapshot),
          'validation':validate_cases(), 'clock':'perf_counter_ns', 'network':'none','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    module = load_sut(snapshot)
    # Default constants are observed, never changed.
    dump(args.output/'sut_constants.json',{k:getattr(module,k) for k in ('_LEDGER_CAP','_BASE_CAP','_EVICTION_SLAB','_GROUP_CAP')})
    attempts=[]
    for i,cell in enumerate(permit['cells']):
        try:
            run_cell(cell,args.output/('cell_'+str(i).zfill(3)),module)
            attempts.append({'cell':cell,'status':'completed'})
        except Exception:
            attempts.append({'cell':cell,'status':'failed','trace':traceback.format_exc()})
        dump(args.output/'attempts.json',attempts)
    dump(args.output/'completion.json',{'status':'completed' if all(a['status']=='completed' for a in attempts) else 'partial','attempts':attempts})


if __name__=='__main__':
    main()
