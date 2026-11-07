#!/usr/bin/env python3
"""Verify/replay the exact review-era LAH synthetic archive, offline."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess, sys, tempfile, zipfile

ARCHIVE_SHA256 = '04630a37ffe19b8c5c20bc48df93c63c299cc59f7b2d8d8b4eb44c60dcc5170f'
ROOT = pathlib.Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=pathlib.Path, help='New output directory; required except in verify mode')
    ap.add_argument('--mode', choices=['all', 'verify', 'smoke', 'analysis'], default='all')
    args = ap.parse_args()
    if sys.version_info < (3, 11): ap.error('Python 3.11+ is required')
    if args.mode != 'verify' and args.output is None: ap.error('--output must name a new output directory')
    output = args.output.resolve() if args.output else None
    if output and output.exists(): ap.error('Output directory already exists; choose a new directory')
    archive = ROOT / 'reproduction/lah-reproduction-candidate-v2.zip'
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != ARCHIVE_SHA256: raise SystemExit('Archive SHA-256 mismatch; refusing to run')
    with tempfile.TemporaryDirectory(prefix='lah-reproduction-') as tmp:
        target = pathlib.Path(tmp).resolve()
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None: raise SystemExit('Archive CRC mismatch')
            for name in z.namelist():
                dest = (target / name).resolve()
                if not dest.is_relative_to(target): raise SystemExit('Unsafe archive path')
            z.extractall(target)
        cmd = [sys.executable, str(target/'lah-reproduction-candidate/reproduce.py'), '--mode', args.mode]
        if output: cmd += ['--output', str(output)]
        proc = subprocess.run(cmd, check=False)
        if proc.returncode: return proc.returncode
    print(json.dumps({'archive_sha256':digest,'status':'passed','mode':args.mode,'output':str(output) if output else None,'scope':{'all':'all stored-cell reanalysis plus one-cell fresh replay; not a new all-cell study or independent replication','verify':'archive and frozen-file identity verification only; no replay or analysis','smoke':'fresh replay of original cell_000 plus aggregate accounting; no full stored-cell reanalysis','analysis':'reanalysis of all thirty stored cells plus aggregate accounting; no fresh cell replay'}[args.mode]}))
    return 0
if __name__ == '__main__': raise SystemExit(main())
