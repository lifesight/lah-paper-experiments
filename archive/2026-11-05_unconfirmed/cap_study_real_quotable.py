"""Companion to cap_study_real.py for work package L3: per read of each recorded turn, how many of its own
figures are still quotable once the whole turn has been harvested in order (the in-turn plugin's ledger at the
final model request), at the production bounds. A read whose figures are gone was evicted by the 5,000-value bound.

Usage: python cap_study_real_quotable.py <path to tests/fixtures/dashgraph/asks>
"""
from __future__ import annotations

import sys
from pathlib import Path

import harness_core.provenance as prov
from harness_core.provenance import NumberLedger, precision_of

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cap_study_real import ordered_reads, profile  # noqa: E402


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    print(f"value bound {prov._LEDGER_CAP}, eviction slab {prov._EVICTION_SLAB}, base cap {prov._BASE_CAP}")
    for ask in sorted(p for p in root.iterdir() if (p / "turn").is_dir()):
        reads = ordered_reads(ask / "turn")
        profs = [profile(n, d) for n, d in reads]
        led = NumberLedger()
        for n, d in reads:
            led.add_from(d, kind=f"result:{n}")
        cells = []
        for p in profs:
            vals = p["values"][:300]
            if not vals:
                cells.append(f"{p['name']}: no figures")
                continue
            ok = sum(led.explain(v, "amount", precision=precision_of(v)) is not None for v in vals)
            cells.append(f"{p['name']} {ok}/{len(vals)} quotable")
        print(f"{ask.name:<16} values held {len(led._exact):>5} | " + " | ".join(cells))


if __name__ == "__main__":
    main()
