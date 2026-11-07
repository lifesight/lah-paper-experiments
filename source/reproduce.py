#!/usr/bin/env python3
"""New stdlib portability adapter. Frozen sources and original outputs stay unchanged."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path): return json.loads(path.read_text())
def dump(path, value): path.write_text(json.dumps(value, indent=2) + '\n')

def verify():
    manifest = read(ROOT / 'FILE_MANIFEST.json')
    expected = {item['path'] for item in manifest['files']}
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name != 'FILE_MANIFEST.json'}
    if actual != expected:
        raise RuntimeError('Package allowlist differs: ' + repr(sorted(actual ^ expected)))
    for item in manifest['files']:
        path = ROOT / item['path']
        if path.is_symlink() or path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise RuntimeError('Integrity mismatch: ' + item['path'])
    permit = read(ROOT / 'frozen/MAIN001_PERMIT.json')
    pinned = [(ROOT/'frozen/runner.py', 'runner_sha256'),
              (ROOT/'frozen/analyze_v2.py', 'analysis_sha256'),
              (ROOT/'original/main001/sut_provenance.py', 'sut_sha256'),
              (ROOT/'frozen/FINAL_PROTOCOL.json', 'final_protocol_sha256'),
              (ROOT/'frozen/FINAL_MAIN_GATE.json', 'review_gate_sha256')]
    for path, key in pinned:
        if digest(path) != permit[key]: raise RuntimeError('Frozen identity: ' + key)
    return {'files_verified': len(expected), 'frozen_identities_verified': len(pinned)}

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def no_timing(obj):
    if isinstance(obj, list): return [no_timing(x) for x in obj]
    if isinstance(obj, dict):
        return {k: no_timing(v) for k, v in obj.items() if k not in ('elapsed_ns','build_ns','availability_check_ns')}
    return obj

def smoke(out):
    runner = load(ROOT/'frozen/runner.py', 'frozen_lah_runner')
    module = runner.load_sut(ROOT/'original/main001/sut_provenance.py')
    config = read(ROOT/'frozen/MAIN001_PERMIT.json')['cells'][0]
    assert config == {'seed':1001,'sources':8,'per_family':100}
    out.mkdir()
    validation = runner.validate_cases()
    actual_constants = {k:getattr(module,k) for k in ('_LEDGER_CAP','_BASE_CAP','_EVICTION_SLAB','_GROUP_CAP')}
    assert actual_constants == read(ROOT/'original/main001/sut_constants.json')
    runner.run_cell(config, out/'cell_000', module)
    compared = []
    for name in ('inputs.json','gold.json','retained_state.json','availability.json','summary.json','observations.jsonl'):
        old, new = ROOT/'original/main001/cell_000'/name, out/'cell_000'/name
        if name.endswith('.jsonl'):
            with old.open() as a, new.open() as b:
                count = 0
                for left,right in __import__('itertools').zip_longest(a,b):
                    assert left is not None and right is not None
                    assert no_timing(json.loads(left)) == no_timing(json.loads(right)), (name,count)
                    count += 1
        else:
            assert no_timing(read(old)) == no_timing(read(new)), name
        compared.append(name)
    result = {'status':'passed','kind':'same-component synthetic replay; not independent replication',
              'cell':'cell_000','config':config,'runner_hand_checks':validation,
              'unchanged_constants':actual_constants,'files_compared':compared,
              'excluded_fields':['elapsed_ns','build_ns','availability_check_ns'],
              'timing':'New timing values remain only in this new replay output; original timing retained unchanged in original/. No timing equality or performance claim.'}
    dump(out/'comparison.json',result)
    return result

def analysis(out):
    analyzer = load(ROOT/'frozen/analyze_v2.py', 'frozen_lah_analyzer')
    previous = sys.argv
    try:
        sys.argv = [str(ROOT/'frozen/analyze_v2.py'),str(ROOT/'original/main001'),str(out)]
        analyzer.main()
    finally: sys.argv = previous
    compared=[]
    for old in sorted((ROOT/'original/main001_analysis').glob('*.json')):
        actual = read(out/old.name)
        expected = read(old)
        if old.name == 'analysis_manifest.json':
            # Only an origin path changes. All other content, including original times, is compared exactly.
            actual.pop('bundle'); expected.pop('bundle')
        assert actual == expected, old.name
        compared.append(old.name)
    result = {'status':'passed','files_compared':compared,'only_excluded_field':'analysis_manifest.json /bundle',
              'timing':'Reanalysis uses original observations, including their immutable historical timings. It measures no new benchmark performance.'}
    dump(out/'comparison.json',result)
    return result

def aggregate_check():
    data = read(ROOT/'aggregate/table4_counts.json')
    keys = ('source_occurrences','prefixes','ingested_exposures','exempt','supported')
    assert len(data['rows']) == 7
    totals = {k:sum(row[k] for row in data['rows']) for k in keys}
    assert totals == data['total']
    assert totals == dict(zip(keys,(8187,17,14675,11395,3280)))
    assert all(row['exempt']+row['supported']==row['ingested_exposures'] for row in data['rows'])
    return {'status':'passed','totals':totals,'scope':'aggregate accounting only; raw cohort unavailable'}

def main():
    if sys.version_info < (3,11): raise SystemExit('Python 3.11+ is required by the unchanged source snapshot.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('all','smoke','analysis','verify'),default='all')
    parser.add_argument('--output',type=Path,help='New external directory; never inside this immutable package')
    args=parser.parse_args()
    integrity=verify()
    if args.mode=='verify':
        print(json.dumps({'integrity':integrity,'table4':aggregate_check()},indent=2));return
    if args.output is None: parser.error('--output is required except for --mode verify')
    output=args.output.resolve()
    if output==ROOT or ROOT in output.parents: parser.error('--output must be outside the package')
    output.mkdir(parents=True,exist_ok=False)
    report={'kind':'new portability-adapter verification, not original MAIN001 execution',
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'python':sys.version,'platform':platform.platform(),'integrity':integrity,
            'adapter_sha256':digest(Path(__file__).resolve()),'mode':args.mode,'table4':aggregate_check(),
            'network':'none; no model/cloud/platform access','original_permit':'frozen/MAIN001_PERMIT.json is an immutable historical receipt; it is not a permit minted for this adapter run'}
    started=time.monotonic()
    dump(output/'adapter_receipt.json',report)
    if args.mode in ('all','smoke'): report['smoke']=smoke(output/'smoke')
    if args.mode in ('all','analysis'): report['analysis']=analysis(output/'analysis')
    report['status']='passed'
    report['adapter_wall_seconds']=time.monotonic()-started
    dump(output/'adapter_receipt.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
