# Real-shape cap study (L1): recorded turns through the NumberLedger at four base caps

Fixtures: `<harness repository>/tests/fixtures/dashgraph/asks`. Seeds [1, 2], 400 claims per cell, value bound 5000. Percentages.

## causal

Reads in order (values / base-eligible operands): orientation (72/1), membership (1/0), attribution_models (1664/1321), attribution_report (3730/2081)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 300 | 3730 | 3 | 100.0 | 100.0 | None | 27.88 | 16.59 | 3.75 | 26.62 | 49.88 | 0.31 |
| 1000 | 1000 | 3730 | 3 | 100.0 | 100.0 | None | 86.38 | 49.27 | 19.0 | 22.62 | 50.38 | 0.61 |
| 2500 | 2458 | 3730 | 3 | 100.0 | 100.0 | None | 100.0 | 100.0 | 51.88 | 22.75 | 50.25 | 0.86 |
| 5000 | 2458 | 3730 | 3 | 100.0 | 100.0 | None | 100.0 | 100.0 | 52.25 | 24.88 | 46.75 | 0.87 |

## cmo

Reads in order (values / base-eligible operands): orientation (72/1), membership (1/0), model_report (484/272), plans_get (1661/1321)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 300 | 2138 | 0 | 100.0 | 100.0 | None | 18.88 | 16.23 | 6.25 | 26.25 | 62.5 | 0.20 |
| 1000 | 1000 | 2138 | 0 | 100.0 | 100.0 | None | 73.0 | 56.58 | 30.62 | 24.88 | 64.75 | 0.46 |
| 2500 | 1592 | 2138 | 0 | 100.0 | 100.0 | None | 100.0 | 99.74 | 38.0 | 24.12 | 66.25 | 0.68 |
| 5000 | 1592 | 2138 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 36.5 | 26.62 | 63.75 | 0.67 |

## geo-experiment

Reads in order (values / base-eligible operands): orientation (72/1), membership (1/0), experiment_report (254/5), list_experiments (7/0)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 6 | 309 | 0 | 100.0 | None | None | None | 100.0 | 0.0 | 1.38 | 9.0 | 0.04 |
| 1000 | 6 | 309 | 0 | 100.0 | None | None | None | 100.0 | 0.0 | 1.75 | 10.25 | 0.04 |
| 2500 | 6 | 309 | 0 | 100.0 | None | None | None | 100.0 | 0.0 | 1.88 | 11.38 | 0.04 |
| 5000 | 6 | 309 | 0 | 100.0 | None | None | None | 100.0 | 0.0 | 2.5 | 13.12 | 0.04 |

## model

Reads in order (values / base-eligible operands): orientation (71/1), membership (1/0), channel_saturation (1296/255), channel_saturation (1296/255), model_diagnostics (87/18), model_report (1326/265), model_report (77/9)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 292 | 1346 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 3.75 | 13.5 | 43.38 | 0.35 |
| 1000 | 803 | 1346 | 0 | 100.0 | 100.0 | None | 100.0 | 99.65 | 4.25 | 12.12 | 43.88 | 0.60 |
| 2500 | 803 | 1346 | 0 | 100.0 | 100.0 | None | 100.0 | 99.82 | 3.88 | 12.0 | 46.12 | 0.60 |
| 5000 | 803 | 1346 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 4.5 | 13.0 | 45.38 | 0.59 |

## promoted-plan

Reads in order (values / base-eligible operands): orientation (70/1), membership (1/0), attribution_models (1664/1321), attribution_report (3734/2166), plans_get (1661/1321)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 300 | 1661 | 4 | 0.0 | 100.0 | None | 18.75 | 20.33 | 6.75 | 19.38 | 45.25 | 0.16 |
| 1000 | 1000 | 1661 | 4 | 0.0 | 100.0 | None | 73.0 | 71.38 | 35.25 | 18.88 | 44.88 | 0.40 |
| 2500 | 1319 | 1661 | 4 | 0.0 | 100.0 | None | 100.0 | 87.15 | 38.0 | 19.75 | 45.62 | 0.51 |
| 5000 | 3839 | 1661 | 4 | 0.0 | 100.0 | None | 100.0 | 100.0 | 52.12 | 20.25 | 42.38 | 1.15 |

## q4-leads

Reads in order (values / base-eligible operands): orientation (71/1), membership (1/0), model_report (64/2)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 3 | 106 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.0 | 0.5 | 4.38 | 0.03 |
| 1000 | 3 | 106 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.0 | 0.0 | 5.38 | 0.03 |
| 2500 | 3 | 106 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.0 | 0.62 | 3.0 | 0.03 |
| 5000 | 3 | 106 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.0 | 1.0 | 4.75 | 0.03 |

## q4-performance

Reads in order (values / base-eligible operands): orientation (71/1), membership (1/0), attribution_report (365/118), model_report (103/17), model_report (126/11)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 147 | 503 | 0 | 100.0 | 100.0 | None | 100.0 | 99.55 | 0.38 | 9.12 | 30.75 | 0.20 |
| 1000 | 147 | 503 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.62 | 7.0 | 27.75 | 0.20 |
| 2500 | 147 | 503 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 0.38 | 7.62 | 31.88 | 0.20 |
| 5000 | 147 | 503 | 0 | 100.0 | 100.0 | None | 100.0 | 100.0 | 1.0 | 8.75 | 29.88 | 0.20 |

## LONG (all asks in sequence)

Reads in order (values / base-eligible operands): orientation (72/1), membership (1/0), attribution_models (1664/1321), attribution_report (3730/2081), orientation (72/1), membership (1/0), model_report (484/272), plans_get (1661/1321), orientation (72/1), membership (1/0), experiment_report (254/5), list_experiments (7/0), orientation (71/1), membership (1/0), channel_saturation (1296/255), channel_saturation (1296/255), model_diagnostics (87/18), model_report (1326/265), model_report (77/9), orientation (70/1), membership (1/0), attribution_models (1664/1321), attribution_report (3734/2166), plans_get (1661/1321), orientation (71/1), membership (1/0), model_report (64/2), orientation (71/1), membership (1/0), attribution_report (365/118), model_report (103/17), model_report (126/11)

| cap | bases kept | values kept | results whose values were evicted | quote first | quote last | honest first | honest last | honest any | fabricated 6-fig | 3-fig | 2-fig | explain ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 | 150 | 2182 | 23 | 100.0 | 100.0 | None | 100.0 | 27.21 | 0.12 | 22.12 | 59.0 | 0.26 |
| 1000 | 150 | 2182 | 23 | 100.0 | 100.0 | None | 100.0 | 30.0 | 0.38 | 24.38 | 59.25 | 0.26 |
| 2500 | 1469 | 2182 | 23 | 100.0 | 100.0 | None | 100.0 | 71.95 | 41.12 | 24.88 | 58.0 | 0.62 |
| 5000 | 4798 | 2182 | 23 | 100.0 | 100.0 | None | 100.0 | 98.65 | 55.38 | 21.12 | 57.25 | 1.59 |

Run time 49.2 s.
