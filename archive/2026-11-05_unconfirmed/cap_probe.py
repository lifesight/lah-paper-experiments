"""Probe for work package L1: what the one-source rule holds on its own once the 300-base cap is lifted.

Reuses the study's generators and claim sets (provenance_study.py, same seeds, same sizes) and runs the
production arm (each result its own source) with the pairwise base cap raised to 10**9, so every result's
bases stay in the pool for the whole session. Two readings per size: the false-accept rate of fabricated
six-figure amounts (E1) and the acceptance of honest within-result sums and differences (E2), both of which
the capped production arm reports in Tables 2 and 3 of the paper. Writes cap_probe_results.json and .md beside
this file.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import provenance_study as study  # noqa: E402
from provenance_study import CLAIMS, SEEDS, SIZES, _round_sig, aggregate, ledger_from, n_bases, rate, result  # noqa: E402

prov = study.prov
LIFTED = 10**9
#: ``--large`` runs the sizes the study did not reach: 50, 100 and 178 results, 1,400 to 4,984 bases, up to the
#: ledger's 5,000-value bound, on three seeds (the pairwise search is O(bases) per claim).
LARGE = "--large" in sys.argv
SIZES = [50, 100, 178] if LARGE else SIZES
SEEDS = [1, 2, 3] if LARGE else SEEDS
SUFFIX = "_large" if LARGE else ""


def e2_with_cap(seed: int, k: int, cap: int) -> dict:
    """E2 (same-result sums and differences at six figures) under a given base cap."""
    old = prov._BASE_CAP
    prov._BASE_CAP = cap
    try:
        rng = random.Random(seed * 7919 + k)
        results = [result(rng, i) for i in range(k)]
        led = ledger_from(results, pooled=False)
        hits = 0
        for _ in range(CLAIMS):
            r = rng.randrange(k)
            rows = results[r]["rows"]
            a, b = rng.sample(rows, 2)
            x, y = a["spend"], b["revenue"] if rng.random() < 0.5 else b["spend"]
            claim = _round_sig(x + y if rng.random() < 0.5 else abs(x - y), 6)
            hits += led.explain(claim, "amount", precision=6) is not None
            if k > 1:  # keep the study's RNG sequence identical
                r2 = (r + 1 + rng.randrange(k - 1)) % k
                rng.choice(results[r2]["rows"])
        return {"bases": n_bases(led), "same_result_accept": rate(hits, CLAIMS)}
    finally:
        prov._BASE_CAP = old


def main() -> None:
    t0 = time.perf_counter()
    out: dict = {"config": {"seeds": SEEDS, "claims_per_cell": CLAIMS, "sizes_results": SIZES,
                            "production_cap": prov._BASE_CAP, "lifted_cap": LIFTED}, "rows": []}
    for k in SIZES:
        capped = [study.e1_e4(s, k, pooled=False, cap=None) for s in SEEDS]
        lifted = [study.e1_e4(s, k, pooled=False, cap=LIFTED) for s in SEEDS]
        e2c = [e2_with_cap(s, k, prov._BASE_CAP) for s in SEEDS]
        e2l = [e2_with_cap(s, k, LIFTED) for s in SEEDS]
        row = {"results": k,
               "bases_capped": aggregate(capped, "bases"), "bases_lifted": aggregate(lifted, "bases"),
               "e1_capped": aggregate(capped, "e1_accept"), "e1_lifted": aggregate(lifted, "e1_accept"),
               "e4p2_capped": aggregate(capped, "e4_accept_p2"), "e4p2_lifted": aggregate(lifted, "e4_accept_p2"),
               "e2_capped": aggregate(e2c, "same_result_accept"), "e2_lifted": aggregate(e2l, "same_result_accept")}
        out["rows"].append(row)
        print(k, row["bases_lifted"]["mean"], "E1", row["e1_capped"]["mean"], row["e1_lifted"]["mean"],
              "E2", row["e2_capped"]["mean"], row["e2_lifted"]["mean"], flush=True)
    out["seconds"] = round(time.perf_counter() - t0, 1)
    (HERE / f"cap_probe_results{SUFFIX}.json").write_text(json.dumps(out, indent=1))
    md = ["# Cap probe: the one-source rule with the base cap lifted", "",
          f"Production arm (one source per result), seeds {SEEDS}, {CLAIMS} claims per cell, "
          f"cap {prov._BASE_CAP} versus {LIFTED}. Mean ± 95% CI over seeds, in %.", "",
          "| results | bases (lifted) | E1 fabricated 6-fig, cap 300 | E1, cap lifted | E2 honest same-result, cap 300 | E2, cap lifted | E4 2-fig, cap 300 | E4 2-fig, cap lifted |",
          "|---|---|---|---|---|---|---|---|"]
    for r in out["rows"]:
        f = lambda a: f"{a['mean']:.2f} ± {a['ci95']:.2f}"  # noqa: E731
        md.append(f"| {r['results']} | {r['bases_lifted']['mean']:.0f} | {f(r['e1_capped'])} | {f(r['e1_lifted'])} | "
                  f"{f(r['e2_capped'])} | {f(r['e2_lifted'])} | {f(r['e4p2_capped'])} | {f(r['e4p2_lifted'])} |")
    md += ["", f"Run time {out['seconds']} s."]
    (HERE / f"cap_probe_results{SUFFIX}.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
