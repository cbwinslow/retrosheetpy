# Decisions

Newest first.

## ADR-001: retrosheetpy downloads and shapes; chadwickpy parses

**Decision (2026-10-07, owner direction).** retrosheetpy owns download, cache, verification and table
shaping, and calls `chadwickpy` for all parsing. **Why.** One reason to change per package; the
parser is verified separately against the C tools. **Revisit if:** a second consumer needs the
parsing without the download layer (then it uses chadwickpy directly).
