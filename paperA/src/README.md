# paperA/src

Code for Paper A. Kept flat until it grows; the roadmap's planned split is:

- `data/`: harmonisation, taxonomy, observation-process audit
- `stage1/`: vital-rate models (Turing.jl or brms; decided at A15)
- `WGForest.jl/`: the IBM simulator, as a Julia package (from A18)
- `inference/`: summary statistics and NPE runs, calling `shared/sbi`
- `analysis/`: validation, projections, uncertainty partition

Climate code goes in [`shared/climate/`](../../shared/climate/), not here, because Paper B reuses it.
