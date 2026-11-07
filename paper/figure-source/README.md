# Frozen LAH figure source

Run `python3 render_figures.py` with Python3.11+, Matplotlib3.9+ and NumPy2.0+. The program reads only the two adjacent frozen plotting JSON files; no network or workspace access is needed. It writes the four existing figures as vector PDF, vector SVG and300dpi PNG at exactly6.5in wide.

This is a visual restyle of existing approved plots, not a new experiment or statistical analysis. All36 acceptance numerators and their1,000-instance denominators, all18 point estimates and18 pointwise descriptive95% seed-cluster intervals, both recorded current/history aggregate bars, all nine architecture boxes and all ten directed relations are retained. Source identifiers in these public JSON files are logical filenames rather than the author's local paths; the original source hashes are retained.

Full-fact correctness is distinct from numeric acceptance. One accepted difference target is exempt. Exemptions are not verification. The reconstructed-return exposures are repeated, include exemptions, and do not establish signed or semantic correctness; the290 sign-loss exposures include checks of future sources. Only NumberLedger is the measured component; the architecture is inspected, not validated for all-path logging, security, or end-to-end effectiveness. Exact interval endpoints remain in the frozen JSON and manuscript TableB1; narrow intervals can overlap point symbols at the shared0–100% display scale.

No copied reference-paper text, figures, institutional branding or arXiv identifiers are included. Original plotting code/data owned by the author or Lifesight are covered by the express CC BY4.0 grant in the repository license map; third-party materials retain their own notices.


## Current architecture revision

`render_figures.py` invokes `render_architecture.py` for Figure 1 before generating the three unchanged numeric figures. Run the same documented main command to regenerate all four. The architecture renderer reads `architecture_layout.original.json`, preserves the nine inspected interfaces and ten relations, and centers NumberLedger after removal of the author-requested explanatory annotation panel. It does not reproduce a HEELO illustration or add an experiment.
