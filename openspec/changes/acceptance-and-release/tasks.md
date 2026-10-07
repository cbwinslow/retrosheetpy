## 1. Land the stack

- [ ] 1.1 Review PR #5 (hardening), run its checks, merge
- [ ] 1.2 Rebase and merge #6 (tables, options, CLI), then #8 (kind=)
- [ ] 1.3 Confirm `main` passes the parity job and mypy/ruff

## 2. Acceptance tests (test first)

- [ ] 2.1 Map invariants 1-5 to tests in `tests/acceptance/`; verify each invariant has at least one test
- [ ] 2.2 Failure-path tests: bad zip, oversize zip, redirect off https, missing season, missing tool, interrupted download
- [ ] 2.3 Every file kind and every output format on tiny fixtures

## 3. Real-world check and release

- [ ] 3.1 One manual live run per file kind, recorded in `docs/` with the gameinfo cross-check result
- [ ] 3.2 Fix README status text; hold release-please #4 until chadwickpy verification is done
- [ ] 3.3 Run the full suite, ruff, mypy; inspect the diff; open PR
