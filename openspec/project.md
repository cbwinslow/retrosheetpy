# retrosheetpy constitution

## What it is
Ask for a Retrosheet season, get data tables. retrosheetpy downloads Retrosheet files, caches them,
runs the Chadwick tools through `chadwickpy`, and writes CSV/JSON/SQLite/pandas ready for a database.

## Boundaries
```text
chadwickpy   = port of the Chadwick C tools. No network.
retrosheetpy = download + cache + verify + parse via chadwickpy + table shaping (this repo).
mlb-baseball = PostgreSQL ingestion; uses the original C tools until ADR-299 there is superseded.
```
Dependency direction: `mlb-baseball` -> `retrosheetpy` -> `chadwickpy`. retrosheetpy never reimplements parsing.

## Invariants
1. **Safe downloads:** https only, no redirects off https, size and member caps on zips, checksum/verify, atomic cache writes.
2. **Never a Retrosheet data file in the repo;** tests use fakes and tiny captured fixtures, never the live site.
3. **Every kind of Retrosheet file is handled or explicitly refused:** regular, postseason, all-star, Negro Leagues, deduced, box-score-only.
4. **Output is faithful to Chadwick's output;** shaping adds structure, not meaning.
5. **Failures are clear:** a bad archive, missing season or tool error names what failed and what to do.
6. **Minimal dependencies** (today `chadwickpy` only; pandas optional).
7. Credit and data-use notice stay in README/NOTICE.

## Workflow
OpenSpec: `/opsx:propose` -> `/opsx:apply` -> `/opsx:archive`. ADRs in `docs/DECISIONS.md`. Test first. Conventional Commits; PRs only.

## Phases
- **Now:** land the stacked PRs (#5, #6, #8) and prove acceptance (`acceptance-and-release`).
- **Then:** release 1.0 once chadwickpy verification completes.
