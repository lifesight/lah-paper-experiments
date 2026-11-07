"""Why are the residual honest named sums over the last read rejected (Section 6.3's 0.3% to 1.7%)?
Replays cap_study_named's honest 'last' cell for each turn with the same seeds and classifies every rejection."""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

EXP = Path(__file__).resolve().parent
sys.path.insert(0, str(EXP))
from cap_study_named import CLAIMS, SEEDS, accepted, full, parsed  # noqa: E402
from cap_study_real import ordered_reads, profile  # noqa: E402
from harness_core.provenance import (  # noqa: E402
    NumberLedger, _half_unit, _is_exempt, _named_sum_operands, _operand_of, _round_sig, _written_digits,
    extract_figures,
)

root = Path(sys.argv[1]).resolve()
for ask in sorted(p for p in root.iterdir() if (p / "turn").is_dir()):
    reads = ordered_reads(ask / "turn")
    if not reads:
        continue
    profs = [profile(n, d) for n, d in reads]
    rich = [p for p in profs if len(p["operands"]) >= 2]
    if not rich:
        continue
    causes: Counter = Counter()
    samples: list[str] = []
    for seed in SEEDS:
        rng = random.Random(seed * 7919)
        led = NumberLedger()
        for name, data in reads:
            led.add_from(data, kind=f"result:{name}")
        sources = {id(p): s for p, s in zip(profs, [s for s in led._sources if s.kind])}
        p = rich[-1]
        src = sources[id(p)]
        for _ in range(CLAIMS):
            a, b = rng.sample(p["operands"], 2)
            plus = rng.random() < 0.5
            c = parsed(a + b if plus else abs(a - b))
            big, small = max(a, b), min(a, b)
            text = f"Together {full(big)} {'+' if plus else '-'} {full(small)} = {full(c)}."
            if accepted(led, text, c):
                continue
            # diagnose
            figs = extract_figures(text)
            byval = {parsed(f.value): f for f in figs}
            fa, fb, fc = byval.get(parsed(big)), byval.get(parsed(small)), byval.get(c)
            if fc is None:
                causes["claim not extracted as a figure"] += 1; samples.append(text); continue
            if fa is None or fb is None:
                causes["an operand not extracted as a figure"] += 1; samples.append(text); continue
            if _is_exempt(big) or _is_exempt(small):
                causes["an operand is at or below the 200 exemption"] += 1; samples.append(text); continue
            xa, xb = _operand_of(src, fa), _operand_of(src, fb)
            if xa is None or xb is None:
                which = "a" if xa is None else "b"
                val = big if xa is None else small
                causes[f"operand not found by _operand_of (written {full(val)}, platform {val!r}, digits {_written_digits(fa if xa is None else fb)})"] += 1
                samples.append(text); continue
            if abs(parsed(big) - big) > 1e-9 or abs(parsed(small) - small) > 1e-9:
                tag = "operand has more than two decimals"
            else:
                tag = "operands exact"
            computed = xa + xb if plus else abs(xa - xb)
            if abs(computed - c) > _half_unit(c, _written_digits(fc)):
                causes[f"arithmetic outside half unit ({tag}: computed {computed!r} vs claim {c!r}, tol {_half_unit(c, _written_digits(fc))})"] += 1
                samples.append(text); continue
            pairs = _named_sum_operands(text, fc)
            if not pairs:
                causes["grammar: no operand pair found for the claim"] += 1; samples.append(text); continue
            causes["other (operands found, arithmetic holds, pair found)"] += 1; samples.append(text)
    n = CLAIMS * len(SEEDS)
    print(f"{ask.name}: {sum(causes.values())} of {n} rejected")
    for k, v in causes.most_common():
        print(f"   {v:3d}  {k}")
    for s in samples[:3]:
        print("      e.g.", s)
