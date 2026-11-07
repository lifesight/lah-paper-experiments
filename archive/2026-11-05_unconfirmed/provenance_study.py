"""Offline study of the NumberLedger (harness-core/harness_core/provenance.py).

Measures, on synthetic tool results drawn from a marketing-amount distribution:
  E1  false-accept rate of fabricated amounts (6 significant figures) vs ledger size,
      under the production rule (pairwise operands from ONE tool result) and a
      counterfactual session-pool rule (every base combinable with every other);
  E2  acceptance of honest derived claims: a+b and a-b from the same result, and from
      two different results;
  E3  false-accept rate of fabricated multipliers (ROAS, 1x to 20x, 3 figures) with the
      blind ratio search off (production) and on (the behaviour the 2026-09-20 audit removed);
  E4  false-accept rate of fabricated rounded amounts (2 and 3 significant figures) that
      restate a ledger value by coincidence;
  E5  throughput: seconds to record results and to explain claims.

Run:  <arm64 python with harness_core importable> provenance_study.py [--quick]
Writes provenance_study_results.json and provenance_study_results.md beside itself.
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
from harness_core.provenance import NumberLedger, _round_sig

QUICK = "--quick" in sys.argv
SEEDS = [1, 2, 3, 4, 5]
CLAIMS = 400 if QUICK else 2000
ROWS_PER_RESULT = 12            # 12 rows x (spend, revenue) + 2 totals + 2 means = 28 bases per result
SIZES = [1, 2, 4, 8, 11, 18, 29]  # results -> ~28, 56, 112, 224, 308, 504, 812 bases
LO, HI = 1e3, 1e8               # log-uniform band for spend and revenue amounts


def amount(rng: random.Random) -> float:
    return round(math.exp(rng.uniform(math.log(LO), math.log(HI))), 2)


def result(rng: random.Random, i: int) -> dict:
    rows = [{"channel": f"ch{i}_{k}", "spend": amount(rng), "revenue": amount(rng)} for k in range(ROWS_PER_RESULT)]
    return {"rows": rows}


def ledger_from(results: list[dict], pooled: bool) -> NumberLedger:
    led = NumberLedger()
    if pooled:
        led.add_from({"all": [r["rows"] for r in results]}, kind="result:pool")
    else:
        for i, r in enumerate(results):
            led.add_from(r, kind=f"result:tool{i}")
    return led


def n_bases(led: NumberLedger) -> int:
    return sum(len(s.bases) for s in led._sources)


def ci95(xs: list[float]) -> tuple[float, float]:
    m = statistics.mean(xs)
    if len(xs) < 2:
        return m, 0.0
    sd = statistics.stdev(xs)
    return m, 1.96 * sd / math.sqrt(len(xs))


def rate(hits: int, n: int) -> float:
    return 100.0 * hits / n


def e1_e4(seed: int, k: int, pooled: bool, cap: int | None) -> dict:
    rng = random.Random(seed * 1000 + k)
    old_cap = prov._BASE_CAP
    if cap is not None:
        prov._BASE_CAP = cap
    try:
        results = [result(rng, i) for i in range(k)]
        led = ledger_from(results, pooled)
        bases = n_bases(led)
        out = {"bases": bases}
        # E1: fabricated amounts at 6 significant figures
        fab = [_round_sig(amount(rng), 6) for _ in range(CLAIMS)]
        why = [led.explain(v, "amount", precision=6) for v in fab]
        out["e1_accept"] = rate(sum(w is not None for w in why), CLAIMS)
        out["e1_direct"] = rate(sum(w in ("ledger",) or (w is not None and "/" not in w and "+" not in w and "-" not in w) for w in why), CLAIMS)
        out["e1_derived"] = rate(sum(w is not None and ("+" in w or " - " in w or "/" in w) for w in why), CLAIMS)
        # E4: fabricated rounded amounts at 2 and 3 figures (restatement by coincidence)
        for p in (2, 3):
            fabp = [_round_sig(amount(rng), p) for _ in range(CLAIMS)]
            hits = sum(led.explain(v, "amount", precision=p) is not None for v in fabp)
            out[f"e4_accept_p{p}"] = rate(hits, CLAIMS)
        return out
    finally:
        prov._BASE_CAP = old_cap


def e2(seed: int, k: int) -> dict:
    rng = random.Random(seed * 7919 + k)
    results = [result(rng, i) for i in range(k)]
    led = ledger_from(results, pooled=False)
    same_hits = cross_hits = 0
    n = CLAIMS
    for _ in range(n):
        r = rng.randrange(k)
        rows = results[r]["rows"]
        a, b = rng.sample(rows, 2)
        x, y = a["spend"], b["revenue"] if rng.random() < 0.5 else b["spend"]
        claim = _round_sig(x + y if rng.random() < 0.5 else abs(x - y), 6)
        same_hits += led.explain(claim, "amount", precision=6) is not None
        if k > 1:
            r2 = (r + 1 + rng.randrange(k - 1)) % k
            c = rng.choice(results[r2]["rows"])
            claim2 = _round_sig(x + c["spend"], 6)
            cross_hits += led.explain(claim2, "amount", precision=6) is not None
    return {"bases": n_bases(led), "same_result_accept": rate(same_hits, n),
            "cross_result_accept": rate(cross_hits, n) if k > 1 else None}


def e3(seed: int, k: int) -> dict:
    rng = random.Random(seed * 104729 + k)
    results = [result(rng, i) for i in range(k)]
    led = ledger_from(results, pooled=False)
    fab = [_round_sig(rng.uniform(1.0, 20.0), 3) for _ in range(CLAIMS)]
    off = sum(led.explain(v, "multiplier", precision=3) is not None for v in fab)
    on = sum(led.explain(v, "multiplier", precision=3, ratio_search=True) is not None for v in fab)
    return {"bases": n_bases(led), "ratio_search_off": rate(off, CLAIMS), "ratio_search_on": rate(on, CLAIMS)}


def e5(seed: int, k: int) -> dict:
    rng = random.Random(seed * 31 + k)
    results = [result(rng, i) for i in range(k)]
    t0 = time.perf_counter()
    led = ledger_from(results, pooled=False)
    t1 = time.perf_counter()
    fab = [_round_sig(amount(rng), 6) for _ in range(CLAIMS)]
    for v in fab:
        led.explain(v, "amount", precision=6)
    t2 = time.perf_counter()
    return {"bases": n_bases(led), "record_s": t1 - t0, "explain_ms_per_claim": 1000 * (t2 - t1) / CLAIMS}


def aggregate(rows: list[dict], key: str) -> dict:
    xs = [r[key] for r in rows if r.get(key) is not None]
    if not xs:
        return {"mean": None, "ci95": None, "n_seeds": 0}
    m, h = ci95(xs)
    return {"mean": round(m, 2), "ci95": round(h, 2), "n_seeds": len(xs)}


def main() -> None:
    out: dict = {"config": {"seeds": SEEDS, "claims_per_cell": CLAIMS, "rows_per_result": ROWS_PER_RESULT,
                            "sizes_results": SIZES, "amount_band": [LO, HI], "base_cap": prov._BASE_CAP,
                            "ledger_cap": prov._LEDGER_CAP, "quick": QUICK}}
    arms = {"production_one_result": dict(pooled=False, cap=None),
            "pool_capped_300": dict(pooled=True, cap=None),
            "pool_uncapped": dict(pooled=True, cap=10**9)}
    out["e1_e4"] = {}
    for arm, cfg in arms.items():
        out["e1_e4"][arm] = []
        for k in SIZES:
            rows = [e1_e4(s, k, cfg["pooled"], cfg["cap"]) for s in SEEDS]
            out["e1_e4"][arm].append({"results": k, "bases": aggregate(rows, "bases"),
                                      "e1_accept": aggregate(rows, "e1_accept"),
                                      "e1_derived": aggregate(rows, "e1_derived"),
                                      "e4_accept_p2": aggregate(rows, "e4_accept_p2"),
                                      "e4_accept_p3": aggregate(rows, "e4_accept_p3")})
            print(arm, k, out["e1_e4"][arm][-1]["bases"]["mean"], out["e1_e4"][arm][-1]["e1_accept"], flush=True)
    out["e2"] = []
    for k in SIZES:
        rows = [e2(s, k) for s in SEEDS]
        out["e2"].append({"results": k, "bases": aggregate(rows, "bases"),
                          "same_result_accept": aggregate(rows, "same_result_accept"),
                          "cross_result_accept": aggregate(rows, "cross_result_accept")})
    out["e3"] = []
    for k in SIZES:
        rows = [e3(s, k) for s in SEEDS]
        out["e3"].append({"results": k, "bases": aggregate(rows, "bases"),
                          "ratio_search_off": aggregate(rows, "ratio_search_off"),
                          "ratio_search_on": aggregate(rows, "ratio_search_on")})
    out["e5"] = []
    for k in SIZES:
        rows = [e5(s, k) for s in SEEDS[:3]]
        out["e5"].append({"results": k, "bases": aggregate(rows, "bases"),
                          "record_s": aggregate(rows, "record_s"),
                          "explain_ms_per_claim": aggregate(rows, "explain_ms_per_claim")})
    here = Path(__file__).resolve().parent
    (here / "provenance_study_results.json").write_text(json.dumps(out, indent=1))
    md = ["# NumberLedger study results", "",
          f"claims per cell {CLAIMS}, seeds {len(SEEDS)}, rows per result {ROWS_PER_RESULT}, "
          f"amount band {LO:g} to {HI:g}, production base cap {prov._BASE_CAP}", "",
          "## E1 fabricated amounts at 6 significant figures: accepted (%), mean and 95% CI over seeds", "",
          "| results | bases (prod) | production one-result | pool, cap 300 | pool, uncapped | bases (uncapped pool) |", "|---|---|---|---|---|---|"]
    for i, k in enumerate(SIZES):
        a, b, c = (out["e1_e4"][arm][i] for arm in arms)
        md.append(f"| {k} | {a['bases']['mean']:.0f} | {a['e1_accept']['mean']:.2f} ± {a['e1_accept']['ci95']:.2f} | "
                  f"{b['e1_accept']['mean']:.2f} ± {b['e1_accept']['ci95']:.2f} | {c['e1_accept']['mean']:.2f} ± {c['e1_accept']['ci95']:.2f} | {c['bases']['mean']:.0f} |")
    md += ["", "## E4 fabricated rounded amounts restating a ledger value by coincidence (%), production arm", "",
           "| results | bases | 2 significant figures | 3 significant figures |", "|---|---|---|---|"]
    for i, k in enumerate(SIZES):
        a = out["e1_e4"]["production_one_result"][i]
        md.append(f"| {k} | {a['bases']['mean']:.0f} | {a['e4_accept_p2']['mean']:.2f} ± {a['e4_accept_p2']['ci95']:.2f} | {a['e4_accept_p3']['mean']:.2f} ± {a['e4_accept_p3']['ci95']:.2f} |")
    md += ["", "## E2 honest derived claims accepted (%)", "", "| results | bases | same result a+b, a-b | across two results a+b |", "|---|---|---|---|"]
    for r in out["e2"]:
        x = r["cross_result_accept"]
        md.append(f"| {r['results']} | {r['bases']['mean']:.0f} | {r['same_result_accept']['mean']:.2f} ± {r['same_result_accept']['ci95']:.2f} | "
                  + (f"{x['mean']:.2f} ± {x['ci95']:.2f}" if x['n_seeds'] else "n/a") + " |")
    md += ["", "## E3 fabricated multipliers 1x to 20x at 3 figures accepted (%)", "", "| results | bases | ratio search off (production) | ratio search on |", "|---|---|---|---|"]
    for r in out["e3"]:
        md.append(f"| {r['results']} | {r['bases']['mean']:.0f} | {r['ratio_search_off']['mean']:.2f} ± {r['ratio_search_off']['ci95']:.2f} | {r['ratio_search_on']['mean']:.2f} ± {r['ratio_search_on']['ci95']:.2f} |")
    md += ["", "## E5 throughput", "", "| results | bases | record all results (s) | explain one claim (ms) |", "|---|---|---|---|"]
    for r in out["e5"]:
        md.append(f"| {r['results']} | {r['bases']['mean']:.0f} | {r['record_s']['mean']:.3f} | {r['explain_ms_per_claim']['mean']:.3f} |")
    (here / "provenance_study_results.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
