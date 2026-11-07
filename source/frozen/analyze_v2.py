"""Descriptive family/cell tables; no universal accuracy and no claim-IID intervals.
Run only on a completed, separately authorized bundle. Output directory must be new.
"""
from collections import defaultdict
import argparse
import json
from pathlib import Path
import statistics
import random
import hashlib


def rate(n,d):
    return n/d if d else None


def percentile(values, p):
    ordered=sorted(values)
    offset=(len(ordered)-1)*p
    lo=int(offset)
    hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(offset-lo)


def seed_bootstrap(observations):
    """Paired seed-macro endpoints; identical resampled seed IDs across every contrast.
    Missing decisions excluded only from paired complete-case denominator; their counts persist.
    Undefined seed strata are never zero-filled. CI needs all 10 declared seeds defined;
    descriptive available-seed point estimates still expose eligible IDs/counts.
    """
    groups=defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
    for item in observations:
        row=item['row']
        seed=item['config']['seed']
        volume=item['config']['sources']
        for axis in ('full_fact_correct','numeric_support'):
            truth=row['gold'][axis]
            if truth not in (True,False):
                continue
            for baseline in ('direct_retained','direct_full_inventory'):
                key=(volume,row['family'],axis,str(truth),baseline)
                c=groups[key][seed]
                c['all_truth_claims']+=1
                a=row['results']['current.explained'].get('target_accepted')
                b=row['results'][baseline].get('accepted')
                if a is None or b is None:
                    c['missing_pairs']+=1
                else:
                    c['complete_pairs']+=1
                    c['current_accepts']+=int(a)
                    c['baseline_accepts']+=int(b)
    allseeds=sorted({item['config']['seed'] for item in observations})
    rng=random.Random(740031)
    draws=[[rng.choice(allseeds) for _ in allseeds] for _ in range(10000)] if allseeds else []
    seed_rows=[]
    intervals=[]
    for key,seeds in sorted(groups.items()):
        volume,family,axis,truth,baseline=key
        meta={'sources':volume,'family':family,'truth_axis':axis,'truth_class':truth,'baseline':baseline}
        rates={}
        for seed in allseeds:
            c=seeds.get(seed,{})
            n=c.get('complete_pairs',0)
            a=rate(c.get('current_accepts',0),n)
            b=rate(c.get('baseline_accepts',0),n)
            d=a-b if a is not None and b is not None else None
            seed_rows.append({**meta,'seed':seed,'counts':dict(c),'current_rate':a,'baseline_rate':b,'difference':d})
            if d is not None:
                rates[seed]=(a,b,d)
        eligible=sorted(rates)
        record={**meta,'eligible_seed_ids':eligible,'eligible_seed_count':len(eligible),
            'undefined_seed_ids':[seed for seed in allseeds if seed not in rates],
            'point_estimates':{name:statistics.mean(rates[seed][i] for seed in eligible) if eligible else None
                for i,name in enumerate(('current_rate','baseline_rate','paired_difference'))},
            'intervals':None, 'interval_kind':'descriptive 95% paired seed-cluster percentile; seed macro mean',
            'bootstrap_seed':740031,'resamples':10000}
        if len(allseeds)==10 and set(allseeds)==set(range(1001,1011)) and len(eligible)==10:
            record['intervals']={}
            for i,name in enumerate(('current_rate','baseline_rate','paired_difference')):
                values=[statistics.mean(rates[seed][i] for seed in draw) for draw in draws]
                record['intervals'][name]=[percentile(values,.025),percentile(values,.975)]
        else:
            record['interval_missing_reason']='needs all ten main seeds with nonzero complete-pair truth-class denominator; undefined rates not zero-filled'
        intervals.append(record)
    return seed_rows,intervals


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('bundle',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    completion=json.loads((args.bundle/'completion.json').read_text())
    args.output.mkdir(parents=True,exist_ok=False)
    tables=[]
    observations=[]
    integrity=[]
    costs=[]
    differences=[]
    for cell in sorted(args.bundle.glob('cell_*')):
        if not (cell/'summary.json').exists():
            tables.append({'cell':cell.name,'status':'missing_summary_retained_in_attempts'})
            continue
        summary=json.loads((cell/'summary.json').read_text())
        availability={f['fact_id']:f for f in json.loads((cell/'availability.json').read_text())}
        inputs=json.loads((cell/'inputs.json').read_text())
        gold=json.loads((cell/'gold.json').read_text())
        raw_rows=[json.loads(line) for line in (cell/'observations.jsonl').read_text().splitlines()]
        row_ids=[row['id'] for row in raw_rows]
        expected_count=12*summary['config']['per_family']
        errors=[]
        if len(row_ids)!=expected_count or len(set(row_ids))!=len(row_ids):
            errors.append('count_or_unique_ids')
        if row_ids != [x['id'] for x in inputs['claims']] or row_ids != [x['id'] for x in gold]:
            errors.append('inputs_gold_observation_alignment')
        for row,g in zip(raw_rows,gold):
            if row['gold'] != {k:v for k,v in g.items() if k!='id'}:
                errors.append('gold_mismatch')
            if set(row['results']) != {'current.explained','current.find_ungrounded','direct_retained','direct_full_inventory'}:
                errors.append('arm_inventory')
        for arm in ('current.explained','current.find_ungrounded','direct_retained','direct_full_inventory'):
            if summary['calls'].get(arm)!=expected_count:
                errors.append('call_denominator_'+arm)
        if summary['failures']:
            errors.append('checker_exceptions_present')
        integrity.append({'cell':cell.name,'expected_rows':expected_count,'actual_rows':len(row_ids),'unique_texts':len({row['text'] for row in raw_rows}),
            'unique_texts_by_family':{family:len({row['text'] for row in raw_rows if row['family']==family}) for family in sorted({row['family'] for row in raw_rows})},'errors':errors})
        counts=defaultdict(lambda:defaultdict(int))
        timers=defaultdict(list)
        paired=defaultdict(lambda:defaultdict(int))
        for row in raw_rows:
            observations.append({'cell':cell.name, 'config':summary['config'], 'row':row})
            operands=json.loads(row['text'])['operands']
            raw_support=all(availability[f]['raw_value_retained'] for f in operands)
            for arm,result in row['results'].items():
                # explained target compared only with target-only raw baselines; find_ungrounded remains whole-text.
                accepted=result.get('target_accepted') if arm=='current.explained' else result.get('accepted')
                target=counts[(row['family'],arm)]
                target['attempted']+=1
                timers[arm].append(result['elapsed_ns'])
                if result.get('error'):
                    target['failed']+=1
                if accepted is None:
                    target['no_decision']+=1
                target['accepted']+=int(accepted is True)
                target['not_parsed']+=int(result.get('not_parsed',False))
                target['exempt_tokens']+=result.get('exempt_tokens',0)
                for axis in ('full_fact_correct','numeric_support'):
                    truth=row['gold'][axis]
                    label='correct' if truth is True else 'incorrect' if truth is False else 'unjudgeable'
                    target[axis+'_'+label]+=1
                    target[axis+'_'+label+'_accepted']+=int(accepted is True)
                if row['gold']['full_fact_correct']:
                    target['correct_with_raw_support']+=int(raw_support)
                    target['correct_with_raw_support_accepted']+=int(raw_support and accepted is True)
            actual=row['results']['current.explained'].get('target_accepted')
            for baseline in ('direct_retained','direct_full_inventory'):
                other=row['results'][baseline].get('accepted')
                pair=paired[(row['family'],baseline)]
                pair['all_claims']+=1
                if actual is None or other is None:
                    pair['missing_pair']+=1
                else:
                    pair['complete_pair']+=1
                    pair['current_accepts']+=int(actual)
                    pair['baseline_accepts']+=int(other)
                    pair['current_only']+=int(actual and not other)
                    pair['baseline_only']+=int(other and not actual)
        for (family,arm),c in counts.items():
            record={'cell':cell.name,**summary['config'],'family':family,'arm':arm,'decision_scope':'whole_text' if arm=='current.find_ungrounded' else 'target','counts':dict(c)}
            record['rates']={axis+'_'+label+'_acceptance':rate(c[axis+'_'+label+'_accepted'],c[axis+'_'+label]) for axis in ('full_fact_correct','numeric_support') for label in ('correct','incorrect')}
            record['rates']['correct_acceptance_given_raw_support']=rate(c['correct_with_raw_support_accepted'],c['correct_with_raw_support'])
            tables.append(record)
        for (family,baseline),c in paired.items():
            differences.append({'cell':cell.name,**summary['config'],'family':family,'baseline':baseline,'counts':dict(c),
                'descriptive_target_acceptance_difference':rate(c['current_accepts']-c['baseline_accepts'],c['complete_pair'])})
        costs.append({'cell':cell.name,**summary['config'],'build_ns':summary['build_ns'],
            'availability_check_ns':summary['availability_check_ns'],'calls':summary['calls'],
            'all_raw_facts':len(availability),'raw_facts_retained':sum(x['raw_value_retained'] for x in availability.values()),
            'facts_quotable':sum(x['public_direct_text_quotable'] for x in availability.values()),
            'latency':{arm:{'calls':len(v),'total_ns':sum(v),'median_ns':statistics.median(v),'max_ns':max(v)} for arm,v in timers.items()}})
    seed_tables,intervals=seed_bootstrap(observations)
    declared_cells=json.loads((args.bundle/'run_manifest.json').read_text())['permit']['cells']
    main_design=all(c['seed'] in range(1001,1011) and c['per_family']==100 for c in declared_cells)
    expected_main={(seed,n) for seed in range(1001,1011) for n in (8,80,800)}
    actual_design={(c['seed'],c['sources']) for c in declared_cells}
    complete_main=main_design and actual_design==expected_main and len(declared_cells)==30 and len(observations)==36000 and all(not c['errors'] for c in integrity)
    integrity_report={'status':'complete' if completion['status']=='completed' and all(not c['errors'] for c in integrity) else 'partial',
        'declared_cells':len(declared_cells),'observed_cells':len(integrity),'observed_claims':len(observations),
        'expected_main_cells':30,'expected_main_claims':36000,'expected_main_scored_arm_calls':144000,
        'observed_scored_arm_calls':sum(len(item['row']['results']) for item in observations),
        'main_design_complete':complete_main, 'cells':integrity}
    for filename,data in [('seed_rates.json',seed_tables),('seed_cluster_bootstrap.json',intervals),('integrity.json',integrity_report),
                          ('analysis_source_manifest.json',{'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'bootstrap_seed':740031,'resamples':10000}),
                          ('family_cell_tables.json',tables),('paired_descriptive_differences.json',differences),('cost_availability.json',costs)]:
        (args.output/filename).write_text(json.dumps(data,indent=2)+'\n')
    (args.output/'analysis_manifest.json').write_text(json.dumps({'bundle':str(args.bundle.resolve()),'completion_status':completion['status'],
        'uncertainty':'descriptive 10000 paired seed-cluster percentile resamples; every seed exposed; no per-claim IID confidence intervals',
        'limits':['finite numeric-policy unsupported is not exhaustive LAH error','semantic rejection not promised by numeric checker',
                  'comparators differ in declared policy; descriptive differences only','volume cells vary age-stratified claim distributions'],
        'failed_attempts':completion['attempts']},indent=2)+'\n')


if __name__=='__main__':
    main()
