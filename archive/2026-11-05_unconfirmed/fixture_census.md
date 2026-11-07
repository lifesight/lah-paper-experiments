# Census of captured platform reads

Fixtures: `<harness repository>/tests/fixtures`; one fresh ledger per read.

| read kind | fixtures | base-eligible figures (min to max) | values (min to max) |
|---|---|---|---|
| attribution report (causal read) | 14 | 118 to 2,166 | 365 to 4,066 |
| realised gain report | 2 | 2,810 to 2,947 | 4,407 to 4,618 |
| saved plan | 7 | 1,277 to 1,321 | 1,614 to 1,661 |
| attribution models list | 2 | 1,321 to 1,321 | 1,664 to 1,664 |
| model report | 18 | 2 to 393 | 63 to 1,374 |
| channel saturation curve | 5 | 119 to 255 | 285 to 1,296 |
| experiment report | 2 | 5 to 5 | 254 to 255 |
| experiment power curve | 6 | 9 to 2,854 | 351 to 5,000 |
| experiment location curve | 14 | 0 to 4,431 | 49 to 2,537 |
| experiment lift analysis | 5 | 92 to 2,197 | 281 to 4,086 |
| model diagnostics | 5 | 9 to 18 | 87 to 2,423 |
| platform report | 4 | 18 to 55 | 32 to 153 |
| orientation | 7 | 1 to 1 | 70 to 72 |

Per fixture:

- attribution_report: dashgraph/asks/causal/attribution_report-1.json values 3730 operands 2081
- attribution_report: dashgraph/asks/causal/attribution_report-2.json values 3730 operands 2081
- attribution_report: dashgraph/asks/causal/attribution_report-3.json values 3730 operands 2081
- attribution_report: dashgraph/asks/causal/attribution_report-4.json values 3730 operands 2081
- attribution_report: dashgraph/asks/causal/attribution_report-5.json values 3729 operands 2081
- attribution_report: dashgraph/asks/causal/turn/attribution_report-1.json values 3730 operands 2081
- attribution_report: dashgraph/asks/promoted-plan/attribution_report-1.json values 3737 operands 2166
- attribution_report: dashgraph/asks/promoted-plan/turn/attribution_report-1.json values 3734 operands 2166
- attribution_report: dashgraph/asks/q4-performance/attribution_report-1.json values 367 operands 118
- attribution_report: dashgraph/asks/q4-performance/turn/attribution_report-1.json values 365 operands 118
- attribution_report: templates/attribution_report-1.json values 3978 operands 2152
- attribution_report: templates/attribution_report-2.json values 3098 operands 1660
- attribution_report: templates_usd/attribution_report-1.json values 4066 operands 2104
- attribution_report: templates_usd/attribution_report-2.json values 2888 operands 1535
- attribution_models: dashgraph/asks/causal/turn/attribution_models-1.json values 1664 operands 1321
- attribution_models: dashgraph/asks/promoted-plan/turn/attribution_models-1.json values 1664 operands 1321
- orientation: dashgraph/asks/causal/turn/orientation-1.json values 72 operands 1
- orientation: dashgraph/asks/cmo/turn/orientation-1.json values 72 operands 1
- orientation: dashgraph/asks/geo-experiment/turn/orientation-1.json values 72 operands 1
- orientation: dashgraph/asks/model/turn/orientation-1.json values 71 operands 1
- orientation: dashgraph/asks/promoted-plan/turn/orientation-1.json values 70 operands 1
- orientation: dashgraph/asks/q4-leads/turn/orientation-1.json values 71 operands 1
- orientation: dashgraph/asks/q4-performance/turn/orientation-1.json values 71 operands 1
- model_report: dashgraph/asks/cmo/model_report-1.json values 484 operands 272
- model_report: dashgraph/asks/cmo/model_report-2.json values 484 operands 272
- model_report: dashgraph/asks/cmo/turn/model_report-1.json values 484 operands 272
- model_report: dashgraph/asks/model/model_report-1.json values 68 operands 3
- model_report: dashgraph/asks/model/model_report-2.json values 77 operands 9
- model_report: dashgraph/asks/model/model_report-3.json values 1310 operands 256
- model_report: dashgraph/asks/model/turn/model_report-1.json values 1326 operands 265
- model_report: dashgraph/asks/model/turn/model_report-2.json values 77 operands 9
- model_report: dashgraph/asks/q4-leads/model_report-1.json values 63 operands 2
- model_report: dashgraph/asks/q4-leads/turn/model_report-1.json values 64 operands 2
- model_report: dashgraph/asks/q4-performance/model_report-1.json values 105 operands 17
- model_report: dashgraph/asks/q4-performance/model_report-2.json values 128 operands 11
- model_report: dashgraph/asks/q4-performance/turn/model_report-1.json values 103 operands 17
- model_report: dashgraph/asks/q4-performance/turn/model_report-2.json values 126 operands 11
- model_report: dashgraph/builds/marginal-headroom/model_report.json values 1161 operands 393
- model_report: templates/model_report-1.json values 125 operands 21
- model_report: templates_usd/model_report-1.json values 123 operands 21
- model_report: templates_usd/model_report-2.json values 1374 operands 259
- plans_get: dashgraph/asks/cmo/plans_get-1.json values 1661 operands 1321
- plans_get: dashgraph/asks/cmo/plans_get-2.json values 1661 operands 1321
- plans_get: dashgraph/asks/cmo/turn/plans_get-1.json values 1661 operands 1321
- plans_get: dashgraph/asks/promoted-plan/plans_get-1.json values 1660 operands 1321
- plans_get: dashgraph/asks/promoted-plan/turn/plans_get-1.json values 1661 operands 1321
- plans_get: templates/plans_get-1.json values 1616 operands 1277
- plans_get: templates_usd/plans_get-1.json values 1614 operands 1277
- experiment_report: dashgraph/asks/geo-experiment/experiment_report-1.json values 255 operands 5
- experiment_report: dashgraph/asks/geo-experiment/turn/experiment_report-1.json values 254 operands 5
- channel_saturation: dashgraph/asks/model/turn/channel_saturation-1.json values 1296 operands 255
- channel_saturation: dashgraph/asks/model/turn/channel_saturation-2.json values 1296 operands 255
- channel_saturation: dashgraph/builds/marginal-headroom/channel_saturation_facebook_bof.json values 359 operands 160
- channel_saturation: dashgraph/builds/marginal-headroom/channel_saturation_facebook_others.json values 285 operands 119
- channel_saturation: dashgraph/builds/marginal-headroom/channel_saturation_linkedin_all.json values 462 operands 165
- model_diagnostics: dashgraph/asks/model/turn/model_diagnostics-1.json values 87 operands 18
- model_diagnostics: templates/model_diagnostics-1.json values 2423 operands 9
- model_diagnostics: templates/model_diagnostics-2.json values 95 operands 18
- model_diagnostics: templates_usd/model_diagnostics-1.json values 2421 operands 9
- model_diagnostics: templates_usd/model_diagnostics-2.json values 93 operands 18
- lift_analysis: newapi/experiments/lift_floor__lift_analysis.json values 4086 operands 1933
- lift_analysis: newapi/experiments/multicell_multikpi__lift_analysis.json values 3320 operands 149
- lift_analysis: newapi/experiments/running_one_cell__lift_analysis.json values 281 operands 92
- lift_analysis: newapi/experiments/running_two_cells__lift_analysis.json values 510 operands 203
- lift_analysis: newapi/experiments/two_measurements__lift_analysis.json values 1878 operands 2197
- location_curve: newapi/experiments/lift_floor__location_curve.json values 1379 operands 4
- location_curve: newapi/experiments/lift_floor__location_curve_completed.json values 1233 operands 4
- location_curve: newapi/experiments/lift_floor__location_curve_market_selection.json values 161 operands 0
- location_curve: newapi/experiments/multicell_multikpi__location_curve.json values 2537 operands 4431
- location_curve: newapi/experiments/multicell_multikpi__location_curve_completed.json values 1550 operands 1544
- location_curve: newapi/experiments/multicell_multikpi__location_curve_market_selection.json values 1463 operands 1457
- location_curve: newapi/experiments/multicell_multikpi__location_curve_post_completed.json values 1714 operands 1708
- location_curve: newapi/experiments/running_one_cell__location_curve.json values 196 operands 140
- location_curve: newapi/experiments/running_one_cell__location_curve_interim_5.json values 166 operands 112
- location_curve: newapi/experiments/running_one_cell__location_curve_market_selection.json values 84 operands 56
- location_curve: newapi/experiments/two_measurements__location_curve.json values 560 operands 2
- location_curve: newapi/experiments/two_measurements__location_curve_completed.json values 538 operands 2
- location_curve: newapi/experiments/two_measurements__location_curve_market_selection.json values 49 operands 0
- location_curve: newapi/experiments/two_measurements__location_curve_post_completed.json values 538 operands 2
- power_curve: newapi/experiments/lift_floor__power_curve.json values 1604 operands 47
- power_curve: newapi/experiments/markets_ready__power_curve.json values 2673 operands 1553
- power_curve: newapi/experiments/multicell_multikpi__power_curve.json values 5000 operands 2854
- power_curve: newapi/experiments/running_one_cell__power_curve.json values 1511 operands 731
- power_curve: newapi/experiments/running_two_cells__power_curve.json values 2890 operands 1557
- power_curve: newapi/experiments/two_measurements__power_curve.json values 351 operands 9
- platform_report: templates/platform_report-1.json values 153 operands 55
- platform_report: templates/platform_report-2.json values 37 operands 21
- platform_report: templates_usd/platform_report-1.json values 151 operands 52
- platform_report: templates_usd/platform_report-2.json values 32 operands 18
- realized_gain: templates/realized_gain-1.json values 4618 operands 2947
- realized_gain: templates_usd/realized_gain-1.json values 4407 operands 2810
