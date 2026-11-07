"""Census of captured platform reads (Table 7 of the paper): for every JSON fixture of 2 KB or more under the
harness checkout's tests/fixtures, the values and base-eligible figures (``operands``) one read puts into a fresh
NumberLedger, grouped by the read's kind as named in the fixture's file name. Ranges are over every fixture of a
kind, including small or partial captures, so they are wide by construction.

Usage: python fixture_census.py <path to tests/fixtures>   (writes fixture_census.md beside this file)
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from harness_core.provenance import NumberLedger

HERE = Path(__file__).resolve().parent
KINDS = [("attribution_report", "attribution report (causal read)"), ("realized_gain", "realised gain report"),
         ("plans_get", "saved plan"), ("attribution_models", "attribution models list"), ("model_report", "model report"),
         ("channel_saturation", "channel saturation curve"), ("experiment_report", "experiment report"),
         ("power_curve", "experiment power curve"), ("location_curve", "experiment location curve"),
         ("lift_analysis", "experiment lift analysis"), ("model_diagnostics", "model diagnostics"),
         ("platform_report", "platform report"), ("orientation", "orientation")]


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    per_kind: dict[str, list[tuple[int, int, str]]] = defaultdict(list)
    for p in sorted(root.rglob("*.json")):
        if p.stat().st_size < 2000:
            continue
        kind = next((k for k, _ in KINDS if k in p.stem), None)
        if kind is None:
            continue
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        led = NumberLedger()
        try:
            led.add_from(data, kind=f"result:{kind}")
        except Exception:
            continue
        per_kind[kind].append((len(led._exact), len(led._sources[-1].operands), str(p.relative_to(root))))
    out = ["# Census of captured platform reads", "", f"Fixtures: `{root}`; one fresh ledger per read.", "",
           "| read kind | fixtures | base-eligible figures (min to max) | values (min to max) |", "|---|---|---|---|"]
    for k, label in KINDS:
        rows = per_kind.get(k)
        if not rows:
            continue
        ops = [r[1] for r in rows]; vals = [r[0] for r in rows]
        out.append(f"| {label} | {len(rows)} | {min(ops):,} to {max(ops):,} | {min(vals):,} to {max(vals):,} |")
    out += ["", "Per fixture:", ""] + [f"- {k}: {path} values {v} operands {o}" for k in per_kind for v, o, path in per_kind[k]]
    (HERE / "fixture_census.md").write_text("\n".join(out) + "\n")
    print("\n".join(out[:20]))


if __name__ == "__main__":
    main()
