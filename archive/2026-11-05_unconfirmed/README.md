# Experiments for "The Lifesight Agent Harness" (preprint, version 3, 5 November 2026)

Every number in Sections 6.1 to 6.3 of the paper, Table 6's model predictions and Figures 3 and 4 come from the
scripts in this folder. Each script writes its results beside itself as JSON and Markdown and keeps its run log, so
the tables in the paper can be checked against the files here without running anything.

## What runs from this folder alone

- `coincidence_model.py` (Section 4.4, equation 1; Table 6): reads `provenance_study_results.json` and writes
  `coincidence_model.md`. Pure Python, no dependencies. `--real <fixtures>` adds the recorded threads and needs the
  harness (below).
- `make_figures.py`, `make_figures_real.py`: Figures 3 and 4 as SVG from the results JSON. Pure Python.
- `assemble.py`, `build_paper.py`: the paper's Markdown parts to one Markdown file, a web page and a print page
  (the PDF is the print page through headless Chrome). Pure Python.

## What needs the harness

The studies drive the harness's ledger, `harness_core.provenance.NumberLedger`, which lives in the harness
repository (`lifesight-platform-mia-agents`, private at the time of writing; the paper describes it at commit
`f0602db6`). With that package importable:

- `provenance_study.py` (Section 6.1; Tables 2 to 5; about 43 s, `--quick` for a 400-claim pass) and
  `cap_probe.py` (the base-cap probe on the same generators; `--large` for 50 to 178 results) need only
  `harness_core`: the results are synthetic.
- `cap_study_real.py`, `cap_study_real_quotable.py`, `cap_study_named.py` and `fixture_census.py` (Sections 6.2
  and 6.3; Tables 7 to 10) take the path of the recorded turns, `tests/fixtures/dashgraph/asks` in the harness
  repository (reads captured from a staging build and replayed through the real tools). The fixtures carry a
  staging workspace's figures and are provided to reviewers on request. `cap_study_named.py` also needs the
  named-derivation rule applied to the harness: `l1_named_derivation.patch`, against commit `b8153f83`
  (`git apply` in the harness checkout); the rule is evaluated in the paper and not deployed.

## Files

| file | what it is |
|---|---|
| `provenance_study.py`, `provenance_study_results.{json,md}`, `provenance_study_run.log` | the synthetic study, Section 6.1 |
| `cap_probe.py`, `cap_probe_results*.{json,md}`, `cap_probe*_run.log` | the base-cap probe on the synthetic shape |
| `coincidence_model.py`, `coincidence_model.md` | the model of Section 4.4 against the measurements |
| `cap_study_real.py`, `cap_study_real_results.{json,md}`, `cap_study_real_run.log` | recorded reads at four caps, Section 6.2 |
| `cap_study_real_quotable.py`, `cap_study_real_quotable_run.log` | per-read quotability, Table 9 |
| `fixture_census.py`, `fixture_census.md` | base-eligible figures and values per captured read, Table 7 |
| `cap_study_named.py`, `cap_study_named_results.{json,md}`, `cap_study_named_run.log` | named derivation, Section 6.3 |
| `l1_named_derivation.patch` | the named-derivation rule and its tests, against harness commit `b8153f83` |
| `trace_named_rejections.py` | why the residual honest named sums of Section 6.3 are rejected (collisions and half-cent ties) |
| `companion_notes/` | the reading notes behind Sections 2 and 7: every source, quote and date read |
| `make_figures.py`, `figure_e1_false_accept.svg`, `make_figures_real.py`, `figure_real_cap.svg` | Figures 3 and 4 (Figure 3 carries 95% CI whiskers over seeds) |
| `assemble.py`, `build_paper.py` | the paper's build |

Licence: CC BY 4.0 (`LICENSE`); the harness is not part of this work.

Seeds, claim counts and sizes are in each script's header and in the `config` block of its results JSON. Paths
inside the results files that pointed at a local checkout have been replaced by `<harness repository>`.
