# projectA/src

Code for Project A. Kept flat until it grows; the roadmap's planned split is:

- `data/`: harmonisation, taxonomy, observation-process audit
- `stage1/`: vital-rate models (Turing.jl or brms; decided at A15)
- `WGForest.jl/`: the IBM simulator, as a Julia package (from A18)
- `inference/`: summary statistics and NPE runs, calling `shared/sbi`
- `analysis/`: validation, projections, uncertainty partition

Current scripts:

- `novelty_search.py`, `novelty_search_extra.py`: A01 literature searches (closed).
- `download_data.py`: A02. Downloads the public datasets into `data/raw/` and verifies them against the publishers' checksums (`--check` to verify only).

Climate code goes in [`shared/climate/`](../../shared/climate/), not here, because Project B reuses it.
