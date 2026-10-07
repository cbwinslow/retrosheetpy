## Context

See proposal.md. Existing tests: `tests/test_client.py`, `test_resolve.py`, `test_import.py` on main; more on the stacked branches (parity job with real Chadwick, completeness and gameinfo cross-check scripts).

## Goals / Non-Goals

**Goals:** a written acceptance suite mapped to invariants 1-5 in project.md; stack landed in order; accurate README; release only after chadwickpy is verified.
**Non-Goals:** new file kinds; other-language ports; parser changes.

## Decisions

- **Land in stack order** (#5 -> #6 -> #8) rather than squashing the branches together, so each CI run is meaningful; rebase each onto main after the one below merges.
- **Acceptance tests use fakes and tiny fixtures;** one manual live run is recorded as evidence, not automated.
- **Do not merge release-please #4** until the owner confirms chadwickpy verification is complete.

## Risks / Trade-offs

- Stacked PRs may conflict after rebases; keep each merge small and re-run CI.
- Retrosheet's box-score-only files have known problems (documented in README); the suite pins current behavior, not a fix.
