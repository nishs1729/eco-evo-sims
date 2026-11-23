# eco-evo-sims

A research programme of three connected projects on forecasting climate vulnerability under explicit uncertainty, from forest stands to genomes. The full plan is in [ROADMAP.md](ROADMAP.md).

| Project | Question | Status |
|---|---|---|
| A | How sensitive is Western Ghats wet-evergreen tree demography to dry-season water deficit and heat, and what does that imply under CMIP6? | Active |
| B | India's KMGBF genetic-diversity indicators, genetic-data coverage and climate exposure | Not started |
| C | When does genomic data predict persistence under climate change? | Not started |

## Layout

```
.
├── ROADMAP.md          # the plan: questions, hypotheses, gates, timelines
├── planning/           # schedule network for Project A + the script that generates it
├── docs/               # programme-level records: governance, verification, decisions (git-ignored for now)
├── shared/             # code used by more than one project (climate pipeline, SBI tools)
└── projectA/
    ├── data/           # manifest.yaml, raw/, processed/ (all git-ignored for now)
    ├── src/            # code
    ├── docs/           # data dictionary, observation-process audit, notes (git-ignored for now)
    ├── results/        # git-ignored; regenerated
    └── manuscript/     # LaTeX
```

`projectB/` and `projectC/` will be created when those projects start. More structure (a Snakemake workflow, containers, a simulation registry) is added when an activity needs it; [planning/PROJECT_A_SCHEDULE.md](planning/PROJECT_A_SCHEDULE.md) says when.

## Setup

Python environment (uv; Python 3.13; versions locked in `uv.lock`):

```bash
uv sync                                         # create .venv/ from uv.lock
uv run python projectA/src/download_data.py     # fetch and verify Project A's public data
uv run pytest                                   # tests (data-integrity tests skip if data/raw/ is absent)
uv run ruff check .                             # lint
```

The Global Wood Density Database has to be downloaded by hand (Dryad blocks scripts); `download_data.py` says how and then verifies it. Julia and R environments, the Snakemake workflow and the container are added when the schedule first needs them. Dependencies and their maintenance checks are recorded in `docs/dependencies.md`.

## Rules

1. **Raw data are read-only.** Record every download in the project's `data/manifest.yaml` (source, licence, checksum, date) at the time of download.
2. **Data and results stay out of git.** For now, all `docs/` folders and data manifests are also kept local only. See `.gitignore`.
3. **Every result is regenerable from code.** Notebooks are for exploration only.
4. **Decisions are logged** in [docs/decisions.md](docs/decisions.md), gate outcomes included.
5. **Code reused by more than one project lives in `shared/`.**
