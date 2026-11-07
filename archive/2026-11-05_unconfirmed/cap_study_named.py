"""Acceptance study for work package L1 (named derivation): the recorded staging turns through the NumberLedger
with the blind pair search closed and amounts derived from the operands the answer names.

Per thread (the recorded turns under ``tests/fixtures/dashgraph/asks/<ask>/turn/`` of the mia-agents checkout, fed
in order as the in-turn plugin does; LONG is all of them in sequence), at the production constants:

* ``honest_named_last`` / ``honest_named_any``: the sum or difference of two base-eligible figures of one read (the
  last read, a random read), written with its operands in full (``A + B = C``), is derived.
* ``honest_bare_last``: the same claim written without its operands (what the blind search used to accept).
* ``fab_bare_6fig``: a random six-figure amount in a read's own band, written bare, is accepted (the direct and
  totals classes only, now).
* ``fab_named_wrong``: a random amount presented with two genuine operands of one read that do not produce it.
* ``fab_named_invented``: a random amount presented with two invented six-figure operands in the read's band.
* ``fab_named_rounded``: a sum of two operands rounded to four figures and written with two decimals
  ("1,234,000.00"), the plausible-looking fabricated operand the operand rule must reject.
* ``fab_2fig``: a random two-figure amount, bare (the direct class's coincidence, L2's surface, unchanged).
* ``honest_rejected``: why the honest named claims over the last read were rejected, by cause: the read's values
  evicted (L3), operands in two currencies, or other.

Every claim value is the value the written text parses back to, so a figure is judged as the ledger reads it.

Usage::

    python cap_study_named.py <path to tests/fixtures/dashgraph/asks>

Writes cap_study_named_results.json and .md beside this file. Run it against the harness checkout that carries the
named rule (``harness_core.provenance.NumberLedger._check_named_sums``).
"""
from __future__ import annotations

import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

from harness_core.provenance import NumberLedger, _round_sig

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cap_study_real import ordered_reads, profile  # noqa: E402

SEEDS = [1, 2]
CLAIMS = 300


def full(v: float) -> str:
    return f"{v:,.2f}"


def rate(hits: int, n: int) -> float | None:
    return round(100.0 * hits / n, 2) if n else None


def parsed(v: float) -> float:
    """The value the written form parses back to (two decimals, Western grouping)."""
    return float(full(v).replace(",", ""))


def accepted(led: NumberLedger, text: str, value: float) -> bool:
    return parsed(value) not in led.find_ungrounded(text)


def band_amount(rng: random.Random, prof: dict, sig: int) -> float:
    lo, hi = min(prof["operands"]), max(prof["operands"])
    lo, hi = max(lo, 201.0), max(hi, lo * 1.01)
    return _round_sig(math.exp(rng.uniform(math.log(lo), math.log(hi))), sig)


def cell(reads: list[tuple[str, dict]], profs: list[dict], seed: int) -> dict:
    rng = random.Random(seed * 7919)
    led = NumberLedger()
    for name, data in reads:
        led.add_from(data, kind=f"result:{name}")
    rich = [p for p in profs if len(p["operands"]) >= 2]
    sources = {id(p): s for p, s in zip(profs, [s for s in led._sources if s.kind])}
    out: dict = {}
    t0 = time.perf_counter()
    for label, pick in (("last", lambda: rich[-1]), ("any", lambda: rng.choice(rich))):
        named = bare = 0
        why = {"evicted": 0, "currency": 0, "other": 0}
        for _ in range(CLAIMS):
            p = pick()
            a, b = rng.sample(p["operands"], 2)
            plus = rng.random() < 0.5
            c = parsed(a + b if plus else abs(a - b))
            big, small = max(a, b), min(a, b)
            text = f"Together {full(big)} {'+' if plus else '-'} {full(small)} = {full(c)}."
            ok = accepted(led, text, c)
            named += ok
            bare += accepted(led, f"Together that is {full(c)}.", c)
            if not ok and label == "last":
                src = sources[id(p)]
                ca, cb = src.value_currencies.get(a, {None}), src.value_currencies.get(b, {None})
                if not src.values:
                    why["evicted"] += 1
                elif (ca - {None}) and (cb - {None}) and not ((ca - {None}) & (cb - {None})):
                    why["currency"] += 1
                else:
                    why["other"] += 1
        out[f"honest_named_{label}"] = rate(named, CLAIMS)
        if label == "last":
            out["honest_bare_last"] = rate(bare, CLAIMS)
            out["honest_rejected"] = ", ".join(f"{k} {rate(n, CLAIMS)}%" for k, n in why.items() if n)
    fab_bare = fab_wrong = fab_invented = fab_rounded = fab_2 = 0
    for _ in range(CLAIMS):
        p = rng.choice(rich)
        c = band_amount(rng, p, 6)
        fab_bare += accepted(led, f"Together that is {full(c)}.", c)
        a, b = rng.sample(p["operands"], 2)
        fab_wrong += accepted(led, f"Together {full(max(a, b))} + {full(min(a, b))} = {full(c)}.", c)
        x, y = band_amount(rng, p, 6), band_amount(rng, p, 6)
        s = round(x + y, 2)
        fab_invented += accepted(led, f"Together {full(x)} + {full(y)} = {full(s)}.", s)
        x2, y2 = _round_sig(x, 4), _round_sig(y, 4)
        s2 = parsed(x2 + y2)
        fab_rounded += accepted(led, f"Together {full(x2)} + {full(y2)} = {full(s2)}.", s2)
        c2 = band_amount(rng, p, 2)
        fab_2 += accepted(led, f"About {full(c2)}.", c2)
    out.update({"fab_bare_6fig": rate(fab_bare, CLAIMS), "fab_named_wrong": rate(fab_wrong, CLAIMS),
                "fab_named_invented": rate(fab_invented, CLAIMS), "fab_named_rounded": rate(fab_rounded, CLAIMS),
                "fab_2fig": rate(fab_2, CLAIMS), "values_kept": len(led._exact),
                "ms_per_check": round(1000 * (time.perf_counter() - t0) / (CLAIMS * 8), 3)})
    return out


def mean(rows: list[dict], key: str) -> float | str | None:
    xs = [r[key] for r in rows if r.get(key) is not None]
    if xs and isinstance(xs[0], str):
        return xs[0]
    return round(statistics.mean(xs), 2) if xs else None


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    threads: dict[str, list[tuple[str, dict]]] = {}
    for ask in sorted(p for p in root.iterdir() if (p / "turn").is_dir()):
        reads = ordered_reads(ask / "turn")
        if reads:
            threads[ask.name] = reads
    threads["LONG (all asks in sequence)"] = [r for reads in threads.values() for r in reads]
    out: dict = {"config": {"seeds": SEEDS, "claims_per_cell": CLAIMS, "fixtures": str(root)}, "threads": {}}
    keys = ["honest_named_last", "honest_named_any", "honest_bare_last", "fab_bare_6fig", "fab_named_wrong",
            "fab_named_invented", "fab_named_rounded", "fab_2fig", "values_kept", "ms_per_check", "honest_rejected"]
    t_all = time.perf_counter()
    for tname, reads in threads.items():
        profs = [profile(n, d) for n, d in reads]
        if not any(len(p["operands"]) >= 2 for p in profs):
            continue
        rows = [cell(reads, profs, s) for s in SEEDS]
        agg = {k: mean(rows, k) for k in keys}
        out["threads"][tname] = agg
        print(f"{tname:<30} " + " ".join(f"{k}={agg[k]}" for k in keys), flush=True)
    out["seconds"] = round(time.perf_counter() - t_all, 1)
    (HERE / "cap_study_named_results.json").write_text(json.dumps(out, indent=1))
    md = ["# Named derivation (L1): recorded turns through the NumberLedger with the pair search closed", "",
          f"Fixtures: `{root}`. Seeds {SEEDS}, {CLAIMS} claims per cell, production constants. Percentages.", "",
          "| thread | honest named, last read | honest named, any read | honest bare, last read | fabricated bare 6-fig | fabricated, genuine operands, wrong sum | fabricated, invented operands | fabricated, 4-figure operands | fabricated bare 2-fig | values kept | ms per check | honest rejections, last read |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for tname, a in out["threads"].items():
        md.append(f"| {tname} | " + " | ".join(str(a[k]) for k in keys) + " |")
    md += ["", f"Run time {out['seconds']} s."]
    (HERE / "cap_study_named_results.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
