# Named derivation (L1): recorded turns through the NumberLedger with the pair search closed

Fixtures: `<harness repository>/tests/fixtures/dashgraph/asks`. Seeds [1, 2], 300 claims per cell, production constants. Percentages.

| thread | honest named, last read | honest named, any read | honest bare, last read | fabricated bare 6-fig | fabricated, genuine operands, wrong sum | fabricated, invented operands | fabricated, 4-figure operands | fabricated bare 2-fig | values kept | ms per check | honest rejections, last read |
|---|---|---|---|---|---|---|---|---|---|---|---|
| causal | 99.0 | 51.0 | 20.33 | 0.67 | 0.67 | 0.0 | 0.0 | 52.66 | 3730 | 0.81 | other 1.67% |
| cmo | 99.34 | 100.0 | 1.67 | 0.17 | 0.17 | 0.0 | 0.67 | 62.0 | 2138 | 0.53 | other 0.33% |
| geo-experiment | 100.0 | 100.0 | 17.84 | 0.17 | 0.17 | 0.0 | 1.0 | 10.5 | 309 | 0.06 |  |
| model | 100.0 | 100.0 | 5.83 | 0.17 | 0.17 | 0.0 | 0.17 | 40.34 | 1346 | 0.4 |  |
| promoted-plan | 99.34 | 73.16 | 1.67 | 0.34 | 0.34 | 0.17 | 1.0 | 46.84 | 1661 | 0.68 | other 0.33% |
| q4-leads | 100.0 | 100.0 | 50.5 | 0.0 | 0.0 | 0.0 | 0.0 | 4.0 | 106 | 0.05 |  |
| q4-performance | 100.0 | 100.0 | 7.0 | 0.0 | 0.0 | 0.0 | 1.0 | 32.84 | 503 | 0.14 |  |
| LONG (all asks in sequence) | 100.0 | 54.17 | 7.0 | 0.0 | 0.0 | 0.0 | 2.33 | 58.84 | 2182 | 1.2 |  |

Run time 22.3 s.
