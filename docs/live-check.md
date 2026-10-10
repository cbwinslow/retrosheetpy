# Live check against Retrosheet (2026-10-10)

One manual run of every kind of file, from the live site into an empty cache, with retrosheetpy at
`main` plus the acceptance suite. Not automated: tests never touch the live site.

| Kind | Season | games | events | box scores |
| --- | --- | --- | --- | --- |
| regular | 2010 | 2,430 | 191,832 | 4.6M characters |
| postseason | 2010 | 32 | 2,423 | yes |
| allstar | 2010 | 1 | 72 | yes |
| negro | 1920 | 2 | 163 | yes |
| negro_box | 1920 | 5 | none (box score only) | yes |
| box | 1901 | 1,109 | none (box score only) | **fails**: the C `cwbox` crashes on 1901-1907 too (README, "Known problems") |

Cross-check against Retrosheet's own `gameinfo.csv` (`scripts/crosscheck.py`, 13 fields per game):

- 2010: 2,430 games compared, no mismatches, none only in ours.
- 1920: 1,236 games compared, no mismatches, none only in ours.
- The CSV also lists postseason, all-star and box-score-only games (33 and 12); those are not in the
  decade archives and are not compared here.

## How to repeat it

Needs network access and about 100 MB of disk. Use an empty cache so nothing is reused:

```sh
export RETROSHEETPY_HOME=$(mktemp -d)
for spec in regular:2010 postseason:2010 allstar:2010 negro:1920 negro_box:1920 box:1901; do
  kind=${spec%:*}; year=${spec#*:}
  retrosheetpy games $year --kind $kind --format csv | wc -l   # games + header
  retrosheetpy events $year --kind $kind --format csv | wc -l  # 1 (header only) for box-score kinds
  retrosheetpy boxscores $year --kind $kind | wc -c            # fails for box 1901, as in C
done
uv run python scripts/crosscheck.py 2010 1920                  # compares with gameinfo.csv
```

If a kind fails, run the same command with `--cache-dir` pointing at a fresh folder first: a stale
cache is the usual cause.
