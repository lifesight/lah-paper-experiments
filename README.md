# LAH: An Evidence-Aware Agent Harness for Marketing Measurement

Companion materials for Anil Kumar Singh (Lifesight), 7 November 2026. This repository separates the current paper's verified component studies from historical draft artifacts. The reproducibility materials are published at [Zenodo DOI10.5281/zenodo.24036084](https://doi.org/10.5281/zenodo.24036084). An arXiv identifier will be added only after one is assigned; archival publication is not peer-review or arXiv acceptance.

## Start here

- [Paper and bibliography](paper/)
- [What was measured, and what was not](docs/CLAIMS_AND_LIMITS.md)
- [Study provenance and historical-artifact status](docs/STUDY_PROVENANCE.md)
- [Reproduction archive](reproduction/lah-reproduction-candidate-v2.zip) and [checksum](reproduction/lah-reproduction-candidate-v2.zip.sha256)
- [Results](results/) and [figures](figures/)
- [Browsable study source code](source/)
- [Release and Zenodo handoff](docs/RELEASE_AND_ZENODO.md)
- [License and distribution boundaries](NOTICE.md)

## Reproduce

Python 3.11 or newer, standard library only; no installation, network, model endpoint, credentials, Google ADK or platform account required:

```sh
python3 reproduce.py --output ../lah-verification
```

Choose a new output directory. The command validates the archive, checks 204 files and five frozen identities, reanalyzes all thirty stored synthetic cells, freshly replays one original cell, and reconciles aggregate Table 4 arithmetic. It does **not** freshly rerun all thirty cells, reproduce private customer data, or independently replicate the study. Approximately 139 MB of immutable observations are compressed in the archive; analysis needs additional memory and may take minutes. See `python3 reproduce.py --help` and the archive's README for scope/modes.

## Current evidence

| Study | Scope | Completed accounting |
|---|---|---|
| Synthetic NumberLedger component study | 10 seeds x 3 source conditions x 12 families x 100 instances | 30 cells; 36,000 repeated claim instances; 144,000 scored-arm calls; 71,040 availability checks |
| Exploratory reconstructed-return quotability | Seven development groups, one workspace, 17 successful-return prefixes | 26,028 temporal checks; 14,675 ingested exposures = 11,395 exempt + 3,280 supported nonexempt |

These are completed AI-assisted offline engineering measurements. They do not establish whole-harness efficacy, semantic correctness, causal validity, independent replication or improved marketing outcomes. Query identities vary across source conditions and instances are repeated; intervals are pointwise descriptive seed-cluster summaries.

## Historical artifacts

Previously active research files and the original license are preserved byte for byte under [archive/2026-11-05_unconfirmed](archive/2026-11-05_unconfirmed/). Their old table/section identifiers, completed-study assertions and numerical claims are **not evidence for the current paper**. Their presence does not establish that the six earlier proposed studies were completed or author-confirmed. Use only the current paper, archive and claim map above for current results.

## Reproducibility and release status

The v2 ZIP is the exact immutable review-era reproduction candidate (SHA-256 `04630a37ffe19b8c5c20bc48df93c63c299cc59f7b2d8d8b4eb44c60dcc5170f`). Its internal README and LICENSE_STATUS.json record its **creation-time** private/preparation state. The current root LICENSE and NOTICE document the author's later CC BY4.0 grant for owned study code and synthetic data without altering frozen files or claiming retroactive preregistration. Publishing this repository is distinct from submitting or acceptance by arXiv.

Raw workspace tool arguments/results, identities, customer-source leaves and reconstruction inputs are not distributed. Only pseudonymous aggregate accounting for the recorded cohort is included. Four preserved historical files contain author-local provenance paths; the reproduction code does not follow those paths or require the private source repository.

The published Zenodo release contains the exact pre-link archive. This working update adds its DOI to the paper/citation resources and updates owned-materials license notices; it has not replaced the published Zenodo file. See [release status](docs/RELEASE_AND_ZENODO.md) and [citation metadata](CITATION.cff).
