"""A coincidence model for the NumberLedger's classes, compared with the measured rates.

The model. A claim written with p significant figures names a *key*: its rounding to p figures. A class accepts the
claim when some candidate of the class (a value, for the direct class; a sum or difference of two bases of one
source, for the pairwise class) rounds to the same key. Keys in one decade number K_p = 9 * 10^(p-1) (the mantissas
10^(p-1) .. 10^p - 1); over the band of D decades the ledger's figures occupy, K_p * D keys. If M candidates fall on
keys with the claim's weight, the chance that the claim's key is occupied is

    P(accept) = 1 - exp(-M / (K_p * D))                                                     (1)

with one correction: log-uniform magnitudes put more candidates and more claims on low mantissas (Benford's law),
so a claim's key is occupied more often than a uniform key; the factor is K_p times the sum over the decade's keys of
the squared log-uniform mass of each key, about 1.53 at every precision (computed below).

With ``--real <path to tests/fixtures/dashgraph/asks>`` the model is also applied to the recorded threads of
cap_study_real.py: the bases each cap keeps are allocated to sources as the ledger does (a new result evicts the
oldest result's bases when the pool is full), M is summed over sources, and the band is each thread's own.

Three consequences the measurements test. (i) Precision: each written figure divides the surface by ten (K_p), so
the direct class at two figures saturates at a few hundred values while at six figures it is negligible. (ii) The
one-source rule: the pairwise candidate set is sum over sources of n_S (n_S - 1) instead of n (n - 1), a factor
of about k for k equal sources, and no factor at all when one source holds the bases, which is the real-read
regime. (iii) Named derivation: the candidate set is the pairs the answer names, so a claim can only coincide
through the direct class.

Usage: python coincidence_model.py   (reads the three results files beside it; writes coincidence_model.md)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LO, HI = 1e3, 1e8  # the synthetic band
D = math.log10(HI / LO)  # decades


def keys_per_decade(p: int) -> int:
    return 9 * 10 ** (p - 1)


def benford_factor(p: int) -> float:
    """How much more often a log-uniform claim lands on a key that log-uniform candidates occupy, relative to
    uniform keys: sum over mantissa keys of w(key)^2 * K where w is the log-uniform mass of the key."""
    K = keys_per_decade(p)
    lo = 10 ** (p - 1)
    masses = [math.log10((k + 1) / k) for k in range(lo, lo * 10)]  # log-uniform mass of each key
    return K * sum(w * w for w in masses)


def predict(M: float, p: int, band: float = D) -> float:
    """Equation (1): the first-order occupancy."""
    lam = M * benford_factor(p) / (keys_per_decade(p) * band)
    return 100.0 * (1.0 - math.exp(-lam))


def predict_exact(M: float, p: int, band: float = D) -> float:
    """The exact occupancy for log-uniform claims and candidates over the band: sum over keys of the claim's mass
    on the key times the chance the key holds at least one of M candidates. Below (1) by Jensen's inequality; the
    two agree while M is small against the key count."""
    K = keys_per_decade(p)
    lo = 10 ** (p - 1)
    masses = [math.log10((k + 1) / k) / band for k in range(lo, lo * 10)]  # one decade's keys, mass over the band
    per_decade = sum(q * (1.0 - math.exp(-M * q)) for q in masses)
    return 100.0 * per_decade * band


def predict_direct(M: float, p: int, band: float = D, exact: bool = False) -> float:
    """The direct class at a written precision p, with rule 2's loose precision: a p-figure claim whose last
    written figure is zero is matched at p - 1 figures (one claim in ten), so the rate is a mixture."""
    f = predict_exact if exact else predict
    if p <= 2:
        return f(M, p, band)
    return 0.1 * f(M, p - 1, band) + 0.9 * f(M, p, band)


def main() -> None:
    syn = json.loads((HERE / "provenance_study_results.json").read_text())
    rows = []
    # Direct class, rounded claims (E4): M = ledger values (the production arm's values column)
    for p in (2, 3):
        for cell in syn["e1_e4"]["production_one_result"]:
            k = cell["results"]
            values = 28 * k  # 24 cells + 2 totals + 2 means per synthetic result
            meas = cell[f"e4_accept_p{p}"]["mean"]
            rows.append(("direct, %d-figure claims" % p, k, values, round(predict_direct(values, p), 1),
                         round(predict_direct(values, p, exact=True), 1), meas))
    # Pairwise class at six figures: candidates = ordered pairs' sums and differences of one source
    # production arm: k sources of 28 bases up to the cap (then 300 bases over the newest sources)
    pw = []
    for arm, label in (("production_one_result", "pairwise, one source"), ("pool_capped_300", "pairwise, pooled")):
        for cell in syn["e1_e4"][arm]:
            k, bases = cell["results"], cell["bases"]["mean"]
            if arm == "production_one_result":
                n_src = min(k, int(bases // 28)); M = n_src * 28 * 27 + (bases - n_src * 28) * max(bases - n_src * 28 - 1, 0)
            else:
                M = bases * (bases - 1)
            pw.append((label, k, int(bases), int(M), round(predict(M, 6), 2), cell["e1_accept"]["mean"]))
    # discrete versus continuous Benford factor, for the record
    cont = 9 * 0.9 / math.log(10) ** 2
    out = ["# Coincidence model against the measured rates", "",
           "Direct class (Table 5 of the paper, synthetic, production arm). M = ledger values. 'Eq. (1)' is the",
           "first-order occupancy with rule 2's loose-precision mixture for three-figure claims; 'exact' the full",
           "occupancy sum with the same mixture.", "",
           "| class | results | M | eq. (1) % | exact % | measured % |", "|---|---|---|---|---|---|"]
    out += [f"| {c} | {k} | {M} | {pr} | {ex} | {me} |" for c, k, M, pr, ex, me in rows]
    out += ["", "Pairwise class at six figures (Table 2). M = ordered pairs (sums and differences) of one source,",
            "summed over sources.", "",
            "| class | results | bases | M | predicted % | measured % |", "|---|---|---|---|---|---|"]
    out += [f"| {c} | {k} | {b} | {M} | {pr} | {me} |" for c, k, b, M, pr, me in pw]
    ratios = []
    for a, b in zip([r for r in pw if r[0].endswith("one source")], [r for r in pw if r[0].endswith("pooled")]):
        if a[5] and b[5]:
            k_src = min(a[1], 300 // 28)
            ratios.append((a[1], a[2], round(b[5] / a[5], 1), k_src, round(b[3] / a[3], 1)))
    out += ["", "The one-source rule's factor: measured pooled / one-source against the model's n(n-1) / sum n_S(n_S-1).", "",
            "| results | bases | measured ratio | sources holding bases | model ratio |", "|---|---|---|---|---|"]
    out += [f"| {k} | {b} | {r} | {s} | {m} |" for k, b, r, s, m in ratios]
    out += ["", f"Benford factors from the discrete key masses: p=2 {benford_factor(2):.3f}, p=3 {benford_factor(3):.3f}, "
            f"p=6 {benford_factor(6):.3f}; continuous limit 9 * 0.9 / ln(10)^2 = {cont:.3f}; "
            f"keys per decade 90, 900, 900,000; band {D:.0f} decades."]
    import sys
    if "--real" in sys.argv:
        out += ["", "## Recorded threads (cap_study_real.py), pairwise class at six figures", "",
                "Bases allocated to sources as the ledger does; M summed over sources; band = the thread's operands.", "",
                "| thread | cap | bases kept | sources holding bases | M | band (decades) | predicted % | measured % |",
                "|---|---|---|---|---|---|---|---|"]
        sys.path.insert(0, str(HERE))
        from cap_study_real import ordered_reads, profile
        real = json.loads((HERE / "cap_study_real_results.json").read_text())
        root = Path(sys.argv[sys.argv.index("--real") + 1])
        for tname, t in real["threads"].items():
            if tname.startswith("LONG"):
                asks = sorted(p for p in root.iterdir() if (p / "turn").is_dir())
                reads = [r for a in asks for r in ordered_reads(a / "turn")]
            else:
                reads = ordered_reads(root / tname / "turn")
            profs = [profile(n, d) for n, d in reads]
            ops = [v for p_ in profs for v in p_["operands"]]
            band = math.log10(max(ops) / min(ops)) if ops else D
            for c in t["cells"]:
                cap = c["cap"]
                held: list[int] = []  # bases per source, in order, under the cap with oldest-first eviction
                for p_ in profs:
                    n = len(p_["operands"])
                    if n == 0:
                        held.append(0); continue
                    take = 0
                    for _ in range(n):
                        if sum(held) + take >= cap:
                            victim = next((i for i, h in enumerate(held) if h > 0), None)
                            if victim is None:
                                break
                            held[victim] = 0
                        take += 1
                    held.append(take)
                M = sum(h * (h - 1) for h in held)
                lam = M * benford_factor(6) / (keys_per_decade(6) * band)
                pred = 100.0 * (1.0 - math.exp(-lam))
                out.append(f"| {tname} | {cap} | {sum(held)} | {sum(1 for h in held if h)} | {M} | {band:.1f} | "
                           f"{pred:.1f} | {c['fab_6fig']} |")
    (HERE / "coincidence_model.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
