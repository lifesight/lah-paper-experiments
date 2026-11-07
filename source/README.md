# Browsable frozen study sources

These four Python files are exact copies of the already distributed immutable reproduction archive. `SOURCE_MANIFEST.json` binds each file to its archive member and checksum. No workspace data or full private harness is included.

- `frozen/runner.py`: synthetic component-study runner.
- `frozen/analyze_v2.py`: stored-result analysis.
- `original/main001/sut_provenance.py`: frozen NumberLedger component under test.
- `reproduce.py`: archive-level reproduction driver.

Use the repository-root `python3 reproduce.py --output ../lah-verification` command for the complete, versioned reproduction context. These standalone browse copies deliberately do not duplicate the archive's large observation files. The author expressly licensed owned study code and synthetic data under CC BY4.0; see the root LICENSE and NOTICE. Third-party notices and excluded private material retain their separate status.

Published versioned study materials: https://doi.org/10.5281/zenodo.24036084. The immutable scientific archive and reported numbers are unchanged by the current DOI/documentation update. Owned study code and synthetic data are CC BY4.0 under the express grant in root LICENSE/NOTICE; third-party materials retain their separate licenses.
