# shared/

Code used by more than one paper. Write it once here instead of copying it between papers.

| Folder | What goes in it | Used by | Starts at |
|---|---|---|---|
| [climate/](climate/) | The common climate pipeline (ROADMAP §2.3) | A, B | A12 (Paper A schedule) |
| [sbi/](sbi/) | SBI tools: NPE ensembles, SBC, expected coverage, misspecification checks | A, C | A24–A27 |

Each component becomes an installable package (Python `pyproject.toml`, or a Julia/R package) when its first code is written, so papers depend on it instead of copying it.
