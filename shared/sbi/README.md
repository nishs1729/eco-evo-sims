# shared/sbi

Simulation-based inference tools, written for Paper A and reused by Paper C's mechanistic forecast.

## Planned contents

- Training ensembles of NPE models (`sbi`, neural spline flows).
- Simulation-based calibration (SBC) and expected-coverage curves.
- Posterior contraction per parameter (Gate A3).
- Misspecification checks: prior-predictive envelope and a distance-to-training-set score (Gate A4).
- Helpers for the simulation registry (one row per simulation: parameters, seed, versions, outputs).

Becomes a Python package (`pyproject.toml`, `src/ecoevo_sbi/`, `tests/`) when the first code is written.
