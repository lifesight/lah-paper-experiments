"""Real-shape study for work package L1: the pairwise base cap against captured platform results.

The offline study (provenance_study.py) and the cap probe (cap_probe.py) use a synthetic result of 28 bases.
Captured platform results are far larger: an attribution report carries about 2,100 base-eligible figures and
3,700 values, a saved plan 1,300 and 1,600, a model report 20 to 400 and 120 to 1,400. This study feeds the
recorded turns under ``tests/fixtures/dashgraph/asks/<ask>/turn/`` of the mia-agents checkout (orientation and
membership first, then the reads, as the in-turn plugin harvests a session) into ``NumberLedger`` at several
values of ``_BASE_CAP`` and measures, per thread and cap:

* ``quote_first`` / ``quote_last``: a figure of the first / last result, written as it is, is grounded (the
  5,000-value bound decides this; the base cap does not).
* ``honest_first`` / ``honest_last`` / ``honest_any``: the sum or difference of two base-eligible figures of one
  result (the first, the last, a random one), written at six figures, is derived.
* ``fab_6fig``: a random amount in a random result's own magnitude band, written at six figures, is accepted.
* ``fab_2fig`` / ``fab_3fig``: the same at two and three figures (the direct class's coincidence rate).
* ``explain_ms``: mean time per ``explain`` call.

LONG is every ask's turn in sequence, the long-thread case. Usage::

    python cap_study_real.py <path to tests/fixtures/dashgraph/asks> [--quick]

Writes cap_study_real_results.json and .md beside this file.
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

import harness_core.provenance as prov
from harness_core.provenance import NumberLedger, _round_sig, precision_of

HERE = Path(__file__).resolve().parent
QUICK = "--quick" in sys.argv
CAPS = [300, 1000, 2500, 5000]
SEEDS = [1] if QUICK else [1, 2]
CLAIMS = 100 if QUICK else 400


def ordered_reads(turn_dir: Path) -> list[tuple[str, dict]]:
    """The turn's reads in harvest order: orientation, membership, then the rest by name."""
    files = sorted(turn_dir.glob("*.json"))
    rank = lambda p: (0 if p.name.startswith("orientation") else 1 if p.name.startswith("membership") else 2, p.name)  # noqa: E731
    out = []
    for p in sorted(files, key=rank):
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        if isinstance(data, dict):
            out.append((p.stem.rsplit("-", 1)[0], data))
    return out


def profile(name: str, data: dict) -> dict:
    """What one result carries on its own: its values and its base-eligible operands, before any cap."""
    led = NumberLedger()
    led.add_from(data, kind=f"result:{name}")
    src = led._sources[-1]
    values = [v for v in led._exact if math.isfinite(v) and abs(v) > prov._SMALL_VALUE_EXEMPT]
    return {"name": name, "values": values, "operands": list(src.operands), "n_values": len(led._exact)}


def build(reads: list[tuple[str, dict]], cap: int) -> NumberLedger:
    old = prov._BASE_CAP
    prov._BASE_CAP = cap
    try:
        led = NumberLedger()
        for name, data in reads:
            led.add_from(data, kind=f"result:{name}")
        return led
    finally:
        prov._BASE_CAP = old


def rate(hits: int, n: int) -> float | None:
    return round(100.0 * hits / n, 2) if n else None


def honest(led: NumberLedger, prof: dict, rng: random.Random, n: int) -> float | None:
    ops = prof["operands"]
    if len(ops) < 2:
        return None
    hits = 0
    for _ in range(n):
        a, b = rng.sample(ops, 2)
        claim = _round_sig(a + b if rng.random() < 0.5 else abs(a - b), 6)
        hits += led.explain(claim, "amount", precision=6) is not None
    return rate(hits, n)


def quote(led: NumberLedger, prof: dict, rng: random.Random, n: int) -> float | None:
    vals = prof["values"]
    if not vals:
        return None
    hits = 0
    for _ in range(n):
        v = rng.choice(vals)
        hits += led.explain(v, "amount", precision=precision_of(v)) is not None
    return rate(hits, n)


def fabricated(led: NumberLedger, profs: list[dict], rng: random.Random, n: int, sig: int) -> tuple[float | None, float]:
    bands = [(min(p["operands"]), max(p["operands"])) for p in profs if len(p["operands"]) >= 2]
    if not bands:
        return None, 0.0
    hits = 0
    t0 = time.perf_counter()
    for _ in range(n):
        lo, hi = rng.choice(bands)
        lo, hi = max(lo, prov._SMALL_VALUE_EXEMPT + 1), max(hi, lo * 1.01)
        v = _round_sig(math.exp(rng.uniform(math.log(lo), math.log(hi))), sig)
        hits += led.explain(v, "amount", precision=sig) is not None
    return rate(hits, n), 1000 * (time.perf_counter() - t0) / n


def cell(reads: list[tuple[str, dict]], profs: list[dict], cap: int, seed: int) -> dict:
    rng = random.Random(seed * 10007 + cap)
    led = build(reads, cap)
    survivors = [s for s in led._sources if s.kind]
    evicted = sum(1 for s, p in zip(survivors, profs) if p["n_values"] and not s.values)
    out = {"bases_kept": led._n_bases, "values_kept": len(led._exact), "results_values_evicted": evicted,
           "quote_first": quote(led, profs[0], rng, CLAIMS), "quote_last": quote(led, profs[-1], rng, CLAIMS),
           "honest_first": honest(led, profs[0], rng, CLAIMS), "honest_last": honest(led, profs[-1], rng, CLAIMS)}
    hits = n = 0
    for _ in range(CLAIMS):
        p = rng.choice(profs)
        if len(p["operands"]) < 2:
            continue
        a, b = rng.sample(p["operands"], 2)
        claim = _round_sig(a + b if rng.random() < 0.5 else abs(a - b), 6)
        hits += led.explain(claim, "amount", precision=6) is not None
        n += 1
    out["honest_any"] = rate(hits, n)
    out["fab_6fig"], out["explain_ms"] = fabricated(led, profs, rng, CLAIMS, 6)
    out["fab_3fig"], _ = fabricated(led, profs, rng, CLAIMS, 3)
    out["fab_2fig"], _ = fabricated(led, profs, rng, CLAIMS, 2)
    return out


def mean(rows: list[dict], key: str) -> float | None:
    xs = [r[key] for r in rows if r.get(key) is not None]
    return round(statistics.mean(xs), 2) if xs else None


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    threads: dict[str, list[tuple[str, dict]]] = {}
    for ask in sorted(p for p in root.iterdir() if (p / "turn").is_dir()):
        reads = ordered_reads(ask / "turn")
        if reads:
            threads[ask.name] = reads
    threads["LONG (all asks in sequence)"] = [r for reads in threads.values() for r in reads]
    out: dict = {"config": {"caps": CAPS, "seeds": SEEDS, "claims_per_cell": CLAIMS, "fixtures": str(root),
                            "ledger_cap": prov._LEDGER_CAP}, "threads": {}}
    t_all = time.perf_counter()
    for tname, reads in threads.items():
        profs = [profile(n, d) for n, d in reads]
        profs = [p for p in profs]  # keep alignment with reads (one source per read)
        shape = [{"read": p["name"], "values": p["n_values"], "operands": len(p["operands"])} for p in profs]
        out["threads"][tname] = {"reads": len(reads), "shape": shape, "cells": []}
        print(f"== {tname}: {len(reads)} reads, operands per read {[len(p['operands']) for p in profs]}", flush=True)
        for cap in CAPS:
            rows = [cell(reads, profs, cap, s) for s in SEEDS]
            agg = {k: mean(rows, k) for k in rows[0]}
            agg["cap"] = cap
            out["threads"][tname]["cells"].append(agg)
            print(f"   cap {cap:>5}: bases {agg['bases_kept']:.0f} values {agg['values_kept']:.0f} evicted {agg['results_values_evicted']:.0f} | "
                  f"quote first/last {agg['quote_first']}/{agg['quote_last']} | honest first/last/any "
                  f"{agg['honest_first']}/{agg['honest_last']}/{agg['honest_any']} | fab 6/3/2 "
                  f"{agg['fab_6fig']}/{agg['fab_3fig']}/{agg['fab_2fig']} | {agg['explain_ms']:.2f} ms", flush=True)
    out["seconds"] = round(time.perf_counter() - t_all, 1)
    (HERE / "cap_study_real_results.json").write_text(json.dumps(out, indent=1))
    md = ["# Real-shape cap study (L1): recorded turns through the NumberLedger at four base caps", "",
          f"Fixtures: `{root}`. Seeds {SEEDS}, {CLAIMS} claims per cell, value bound {prov._LEDGER_CAP}. Percentages.", ""]
    for tname, t in out["threads"].items():
        md += [f"## {tname}", "", "Reads in order (values / base-eligible operands): " +
               ", ".join(f"{s['read']} ({s['values']}/{s['operands']})" for s in t["shape"]), "",
               "| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for c in t["cells"]:
            md.append(f"| {c['cap']} | {c['bases_kept']:.0f} | {c['values_kept']:.0f} | {c['results_values_evicted']:.0f} | "
                      f"{c['quote_first']} | {c['quote_last']} | {c['honest_first']} | {c['honest_last']} | {c['honest_any']} | "
                      f"{c['fab_6fig']} | {c['fab_3fig']} | {c['fab_2fig']} | {c['explain_ms']:.2f} |")
        md.append("")
    md.append(f"Run time {out['seconds']} s.")
    (HERE / "cap_study_real_results.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
