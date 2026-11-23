# Project A: Climate sensitivity of Western Ghats wet-evergreen tree demography

Plan: [ROADMAP.md §3](../ROADMAP.md). Schedule: [planning/PROJECT_A_SCHEDULE.md](../planning/PROJECT_A_SCHEDULE.md).

| Folder | Contents | In git? |
|---|---|---|
| `data/manifest.yaml` | Source, licence, checksum and owner of every dataset | No (for now) |
| `data/raw/` | Downloads exactly as received. Never edited | No |
| `data/processed/` | Harmonised stems, plot climate, traits, guilds | No |
| `src/` | Code (flat for now) | Yes |
| `tests/` | pytest tests; run with `uv run pytest` from the repo root | Yes |
| `docs/` | Data dictionary, observation-process audit, notes | No (for now) |
| `results/` | Outputs, regenerated from code | No |
| `manuscript/` | LaTeX: `main.tex`, `supplement.tex`, `references.bib` | Yes |

To add when the schedule reaches them: `config.yaml` (A09), a Snakemake workflow (A12–A13), the `WGForest.jl` simulator package (A18), a container and HPC profile (A20), and the simulation registry (A24).
