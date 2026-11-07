# Coincidence model against the measured rates

Direct class (Table 5 of the paper, synthetic, production arm). M = ledger values. 'Eq. (1)' is the
first-order occupancy with rule 2's loose-precision mixture for three-figure claims; 'exact' the full
occupancy sum with the same mixture.

| class | results | M | eq. (1) % | exact % | measured % |
|---|---|---|---|---|---|
| direct, 2-figure claims | 1 | 28 | 9.1 | 8.9 | 9.14 |
| direct, 2-figure claims | 2 | 56 | 17.3 | 16.7 | 17.87 |
| direct, 2-figure claims | 4 | 112 | 31.6 | 29.7 | 30.67 |
| direct, 2-figure claims | 8 | 224 | 53.2 | 48.2 | 46.69 |
| direct, 2-figure claims | 11 | 308 | 64.8 | 57.8 | 58.37 |
| direct, 2-figure claims | 18 | 504 | 81.9 | 72.2 | 71.38 |
| direct, 2-figure claims | 29 | 812 | 93.6 | 83.9 | 81.97 |
| direct, 3-figure claims | 1 | 28 | 1.8 | 1.7 | 2.48 |
| direct, 3-figure claims | 2 | 56 | 3.4 | 3.4 | 4.57 |
| direct, 3-figure claims | 4 | 112 | 6.5 | 6.3 | 6.88 |
| direct, 3-figure claims | 8 | 224 | 11.9 | 11.3 | 11.56 |
| direct, 3-figure claims | 11 | 308 | 15.4 | 14.5 | 14.76 |
| direct, 3-figure claims | 18 | 504 | 22.3 | 20.9 | 21.04 |
| direct, 3-figure claims | 29 | 812 | 31.0 | 29.1 | 29.42 |

Pairwise class at six figures (Table 2). M = ordered pairs (sums and differences) of one source,
summed over sources.

| class | results | bases | M | predicted % | measured % |
|---|---|---|---|---|---|
| pairwise, one source | 1 | 28 | 756 | 0.03 | 0.05 |
| pairwise, one source | 2 | 55 | 1501 | 0.05 | 0.08 |
| pairwise, one source | 4 | 112 | 3024 | 0.1 | 0.12 |
| pairwise, one source | 8 | 224 | 6048 | 0.21 | 0.23 |
| pairwise, one source | 11 | 280 | 7560 | 0.26 | 0.34 |
| pairwise, one source | 18 | 280 | 7560 | 0.26 | 0.3 |
| pairwise, one source | 29 | 280 | 7560 | 0.26 | 0.51 |
| pairwise, pooled | 1 | 28 | 756 | 0.03 | 0.05 |
| pairwise, pooled | 2 | 55 | 3057 | 0.1 | 0.13 |
| pairwise, pooled | 4 | 112 | 12432 | 0.42 | 0.44 |
| pairwise, pooled | 8 | 224 | 49952 | 1.68 | 1.88 |
| pairwise, pooled | 11 | 300 | 89700 | 3.0 | 3.04 |
| pairwise, pooled | 18 | 300 | 89700 | 3.0 | 3.2 |
| pairwise, pooled | 29 | 300 | 89700 | 3.0 | 2.71 |

The one-source rule's factor: measured pooled / one-source against the model's n(n-1) / sum n_S(n_S-1).

| results | bases | measured ratio | sources holding bases | model ratio |
|---|---|---|---|---|
| 1 | 28 | 1.0 | 1 | 1.0 |
| 2 | 55 | 1.6 | 2 | 2.0 |
| 4 | 112 | 3.7 | 4 | 4.1 |
| 8 | 224 | 8.2 | 8 | 8.3 |
| 11 | 280 | 8.9 | 10 | 11.9 |
| 18 | 280 | 10.7 | 10 | 11.9 |
| 29 | 280 | 5.3 | 10 | 11.9 |

Benford factors from the discrete key masses: p=2 1.527, p=3 1.528, p=6 1.528; continuous limit 9 * 0.9 / ln(10)^2 = 1.528; keys per decade 90, 900, 900,000; band 5 decades.

## Recorded threads (cap_study_real.py), pairwise class at six figures

Bases allocated to sources as the ledger does; M summed over sources; band = the thread's operands.

| thread | cap | bases kept | sources holding bases | M | band (decades) | predicted % | measured % |
|---|---|---|---|---|---|---|---|
| causal | 300 | 300 | 1 | 89700 | 5.2 | 2.9 | 3.75 |
| causal | 1000 | 1000 | 1 | 999000 | 5.2 | 27.9 | 19.0 |
| causal | 2500 | 2081 | 1 | 4328480 | 5.2 | 75.8 | 51.88 |
| causal | 5000 | 3403 | 3 | 6072200 | 5.2 | 86.3 | 52.25 |
| cmo | 300 | 300 | 1 | 89700 | 5.5 | 2.8 | 6.25 |
| cmo | 1000 | 1000 | 1 | 999000 | 5.5 | 26.7 | 30.62 |
| cmo | 2500 | 1594 | 3 | 1817432 | 5.5 | 43.2 | 38.0 |
| cmo | 5000 | 1594 | 3 | 1817432 | 5.5 | 43.2 | 36.5 |
| geo-experiment | 300 | 6 | 2 | 20 | 0.9 | 0.0 | 0.0 |
| geo-experiment | 1000 | 6 | 2 | 20 | 0.9 | 0.0 | 0.0 |
| geo-experiment | 2500 | 6 | 2 | 20 | 0.9 | 0.0 | 0.0 |
| geo-experiment | 5000 | 6 | 2 | 20 | 0.9 | 0.0 | 0.0 |
| model | 300 | 292 | 3 | 70338 | 5.4 | 2.2 | 3.75 |
| model | 1000 | 803 | 6 | 199878 | 5.4 | 6.1 | 4.25 |
| model | 2500 | 803 | 6 | 199878 | 5.4 | 6.1 | 3.88 |
| model | 5000 | 803 | 6 | 199878 | 5.4 | 6.1 | 4.5 |
| promoted-plan | 300 | 300 | 1 | 89700 | 5.2 | 2.9 | 6.75 |
| promoted-plan | 1000 | 1000 | 1 | 999000 | 5.2 | 27.9 | 35.25 |
| promoted-plan | 2500 | 1321 | 1 | 1743720 | 5.2 | 43.5 | 38.0 |
| promoted-plan | 5000 | 4809 | 4 | 8176830 | 5.2 | 93.1 | 52.12 |
| q4-leads | 300 | 3 | 2 | 2 | 0.4 | 0.0 | 0.0 |
| q4-leads | 1000 | 3 | 2 | 2 | 0.4 | 0.0 | 0.0 |
| q4-leads | 2500 | 3 | 2 | 2 | 0.4 | 0.0 | 0.0 |
| q4-leads | 5000 | 3 | 2 | 2 | 0.4 | 0.0 | 0.0 |
| q4-performance | 300 | 147 | 4 | 14188 | 4.6 | 0.5 | 0.38 |
| q4-performance | 1000 | 147 | 4 | 14188 | 4.6 | 0.5 | 0.62 |
| q4-performance | 2500 | 147 | 4 | 14188 | 4.6 | 0.5 | 0.38 |
| q4-performance | 5000 | 147 | 4 | 14188 | 4.6 | 0.5 | 1.0 |
| LONG (all asks in sequence) | 300 | 150 | 6 | 14190 | 5.5 | 0.4 | 0.12 |
| LONG (all asks in sequence) | 1000 | 150 | 6 | 14190 | 5.5 | 0.4 | 0.38 |
| LONG (all asks in sequence) | 2500 | 1471 | 7 | 1757910 | 5.5 | 42.0 | 41.12 |
| LONG (all asks in sequence) | 5000 | 4968 | 11 | 8191092 | 5.5 | 92.1 | 55.38 |
