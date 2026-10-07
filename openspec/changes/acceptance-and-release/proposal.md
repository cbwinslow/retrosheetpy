## Why

The repo's `main` holds only the download client (#1). The working tool (tables, output formats, new CLI,
`kind=` selection) sits in stacked open PRs #5 -> #6 -> #8, and release-please PR #4 would publish 1.0.0
of a README that still says "nothing works end to end". The owner wants proof that retrosheetpy does what
it is supposed to before release.

## What Changes

- Review and land the stacked PRs in order (#5, #6, #8), each passing CI.
- Write acceptance tests for the stated job: download, cache, verify, every file kind, every output format, several seasons in one call, and clear failure on bad input (bad zip, missing season, missing tool, interrupted download).
- Exercise a real end-to-end run once locally (live site, manual, not in CI) and compare tables with Retrosheet's own gameinfo CSV (script exists).
- Fix the README status text; hold release-please #4 until chadwickpy verification (its `verify-port-completeness` change) is done.

No new features beyond what the stacked PRs contain.

## Capabilities

### New Capabilities
<!-- none: acceptance/release work (skip_specs) -->

### Modified Capabilities
<!-- none -->

## Impact

`tests/`, README status, merge order of PRs #5/#6/#8, release timing. Out of scope: parsing changes (chadwickpy), TypeScript/Rust ports.
