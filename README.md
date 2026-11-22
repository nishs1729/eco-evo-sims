# eco-evo-sims

A research programme of three connected papers on forecasting climate vulnerability under explicit uncertainty, from forest stands to genomes. The full plan is in [ROADMAP.md](ROADMAP.md).

| Paper | Question | Status |
|---|---|---|
| A | How sensitive is Western Ghats wet-evergreen tree demography to dry-season water deficit and heat, and what does that imply under CMIP6? | Active |
| B | India's KMGBF genetic-diversity indicators, genetic-data coverage and climate exposure | Not started |
| C | When does genomic data predict persistence under climate change? | Not started |

## Layout

```
.
├── ROADMAP.md          # the plan: questions, hypotheses, gates, timelines
├── planning/           # schedule network for Paper A + the script that generates it
├── docs/               # programme-level records: governance, verification, decisions (git-ignored for now)
├── shared/             # code used by more than one paper (climate pipeline, SBI tools)
└── paperA/
    ├── data/           # manifest.yaml, raw/, processed/ (all git-ignored for now)
    ├── src/            # code
    ├── docs/           # data dictionary, observation-process audit, notes (git-ignored for now)
    ├── results/        # git-ignored; regenerated
    └── manuscript/     # LaTeX
```

`paperB/` and `paperC/` will be created when those papers start. More structure (a Snakemake workflow, containers, a simulation registry) is added when an activity needs it; [planning/PAPER_A_SCHEDULE.md](planning/PAPER_A_SCHEDULE.md) says when.

## Rules

1. **Raw data are read-only.** Record every download in the paper's `data/manifest.yaml` (source, licence, checksum, date) at the time of download.
2. **Data and results stay out of git.** For now, all `docs/` folders and data manifests are also kept local only. See `.gitignore`.
3. **Every result is regenerable from code.** Notebooks are for exploration only.
4. **Decisions are logged** in [docs/decisions.md](docs/decisions.md), gate outcomes included.
5. **Code reused by more than one paper lives in `shared/`.**
