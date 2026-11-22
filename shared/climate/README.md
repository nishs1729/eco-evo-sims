# shared/climate

The common climate pipeline, specified in ROADMAP §2.3. Used by Paper A (plot-scale drivers and projections) and Paper B (exposure metrics).

## Planned contents

- **Historical data:** IMD gridded rainfall (0.25°) and temperature; CHELSA; plot-scale validation against station or estate rain gauges.
- **Derived variables:** PET (Penman–Monteith, or Hargreaves as a fallback), climatic water deficit, dry-season length, hot-day metrics.
- **Projections:** NEX-GDDP-CMIP6 and CHELSA-CMIP6, combined with the historical baseline by the delta-change method (1985–2014 baseline).
- **GCM selection:** exclude "hot models", then pick 5–8 models that span the projected change. Document it in `gcm_selection.md`.
- **Scenarios and horizons:** SSP1-2.6, SSP2-4.5, SSP3-7.0 (SSP5-8.5 as a high-end bound); 2041–2060 and 2071–2090.

Downloaded climate data go in a git-ignored `data/` folder here, with a `data/manifest.yaml`, following the same rules as the paper folders.
