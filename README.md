# retrosheetpy

Ask for a Retrosheet season, get data tables. `retrosheetpy` downloads seasons from
[Retrosheet](https://www.retrosheet.org), keeps them in a cache folder, runs the Chadwick tools on
them (through the pure-Python port [chadwickpy](https://pypi.org/project/chadwickpy/)), and gives you
the result as rows, CSV, JSON lines, SQLite or pandas.

> **Status: not released yet.** The code works and is tested; the name is not on PyPI yet.

```python
import retrosheetpy as rs

rs.events(2010)  # every play of 2010: a Table with 164 columns
rs.games(range(2000, 2011))  # eleven seasons, one combined Table
rs.events(2010, home="NYA", start="0601", end="0630")  # one team's home games in June
rs.season(2010).daily().to_csv("daily.csv")
rs.games([2008, 2009]).to_sqlite("mlb.db")
```

```
retrosheetpy events 2010 --out events.csv
retrosheetpy games 2000-2010 --format sqlite --out mlb.db
retrosheetpy events 2010 --home NYA --fields 0-5 --format jsonl
retrosheetpy boxscores 2010 --game ANA201004050
retrosheetpy fields events            # the numbered fields Chadwick lists
```

## The six tables

They are Chadwick's six programs, with Chadwick's names and Chadwick's column names.

| Table | One row per | Columns | Chadwick |
| --- | --- | --- | --- |
| `events` | play | 164 | `cwevent` |
| `games` | game | 183 | `cwgame` |
| `daily` | player per game | 154 | `cwdaily` |
| `subs` | substitution | 26 | `cwsub` |
| `comments` | comment record | 10 | `cwcomment` |
| `boxscores` | (text) | | `cwbox` (text, XML, SportsML) |

Every column Chadwick can print is printed by default. Values are the strings Chadwick prints; a
missing value is an empty string, never zero. Nothing is typed or guessed.

## What is covered

Regular-season games from Retrosheet's decade event archives, seasons **1908 to the latest**
(Retrosheet's 1910s archive also holds 1908 and 1909). All event files in an archive are used:
team files (`2010ANA.EVA`, the Federal League's `.EVF`, `.EVR`) and the deduced-game files
(`.EDN`, `.EDA`, `.EDF`, including those named by year alone, such as `1920.EDA`).

Games from Retrosheet's other archives are one option away, with `kind=` (or `--kind`):

| `kind=` | Retrosheet files | Seasons | Notes |
| --- | --- | --- | --- |
| `"regular"` (default) | decade event archives | 1908 on | |
| `"postseason"` | `allpost.zip` | 1900 on | World Series, playoffs, division series |
| `"allstar"` | `allas.zip` | 1933 on | |
| `"negro"` | `allevr.zip` | 1903 to 1961 | Negro Leagues play-by-play |
| `"negro_box"` | `allebr.zip` | 1903 to 1961 | games known from box scores only: no events |
| `"box"` | `1890sbox.zip`, `1900sbox.zip` | 1897 to 1909 | major-league games known from box scores only: no events |

Each kind is kept apart in the cache (a season's postseason and regular files have different team
lists). `home=` works on the regular season only, since the other files are not named by home team.
Retrosheet ships no team list for the Negro Leagues archives and the Chadwick tools will not run
without one, so retrosheetpy creates an empty one. Games known only from box scores have no plays, so
`events` is empty for them; `games`, `daily` and `boxscores` have the data.

Checked against the real C tools (6,000-odd comparisons): every season of `postseason`, `allstar`,
`negro` and `box` 1897-1899, all six tables, byte-identical.

**Known problems in Retrosheet's box-score-only files, not in this package.** The C tools themselves
fail on these, and chadwickpy stops where the C would crash or read uninitialised memory, so you get
an error (`ToolError`) instead of output:

* `boxscores` for `kind="box"` 1901 to 1907: the C `cwbox` crashes on these files. Single games work
  (`game=`).
* `kind="negro_box"` 1921, 1933 to 1939, 1946, 1947 and 1949: some games are damaged (players listed
  in a statistics line but missing from the lineup, `NA` where a number belongs, a start time written
  as `6.25E-2`). `games`, `daily` and `boxscores` fail for those seasons; asking for one game or a date
  range that avoids the damaged games works.

The 1871, 1872 and 1874 archives Retrosheet lists as box scores hold only a team list, so there is
nothing to read; the package says so. Seasons before 1897 are not available from these archives.

## Options (the same for every table)

| Option | Meaning |
| --- | --- |
| `home="NYA"` or `["NYA", "BOS"]` | only those home teams' files (Retrosheet files are named by home team). Games Retrosheet deduced from box scores sit in files named by year (`1920.EDA`) that mix teams, so `home=` leaves those out. |
| `game="ANA201004050"` | only that game |
| `start="0405"`, `end="0430"` | date range, `mmdd` |
| `fields=...`, `extended=...` | choose columns by Chadwick's field numbers (`"0-5,9"`, `[0, 7]`). Choose one and the other is left out. |
| `jobs=4` | worker processes (default: automatic, at most 16, leaving a core free) |

`table.select("GAME_ID", "BAT_ID")` picks columns by name afterwards.

Asking for several seasons (a list or a range) gives one Table: the seasons' rows in order, the
header once. Every row starts with the game id, which contains the year, so no extra column is added.
XML and SportsML box scores are one document per season, so they take one season at a time.

## Getting the data out

A `Table` streams: it runs the tool each time you loop over it, so a whole era does not have to fit in
memory. `.load()` keeps the rows in a list.

```python
for row in rs.events(2010):
    ...  # dicts
rs.events(2010).rows()  # tuples, faster
t.to_csv("a.csv")
t.to_jsonl("a.jsonl")
t.to_json("a.json")
t.to_sqlite("a.db", if_exists="replace")  # every column TEXT; all-or-nothing
t.to_pandas()  # pip install "retrosheetpy[pandas]"
t.write("a.csv")  # the format follows the file name
```

Files are written whole or not at all. A tool failure raises `ToolError` with Chadwick's message and
leaves nothing behind.

## The cache

`~/.retrosheetpy` (or `$RETROSHEETPY_HOME`, or `--cache-dir`). Each decade's event archive is
downloaded once, with its SHA-256 recorded, and each season is unpacked beside it.
`retrosheetpy cache verify` re-checks the files; `retrosheetpy cache clear` removes them.

## How it was checked

The output is compared byte for byte with the real Chadwick C tools by `scripts/parity.py`: 24
seasons between 1910 and 2025 (including the Federal League and deduced-game files), all tables, plus
option variants: 288 of 288 identical. Those 24 seasons asked for as one Table give 3,441,587 `events`
rows and 43,566 `games` rows, equal to the C outputs joined. The unit tests (`pytest`) use a made-up
two-season fixture and need no network; with `CHADWICK_BIN` set they also compare against the C tools.

That comparison runs the C tools on the same file list, so it cannot notice a file we left out. A
separate check does: every file in all twelve decade archives is kept, and for 1908, 1909, 1914, 1920,
1962 and 2010 the number of `games` rows equals the number of games in the raw event files.

Two things are *not* compared with C, on purpose: the C `cwbox -S` (SportsML) crashes on real data,
and the C `cwbox -X` (XML) prints one attribute (`pb`) from uninitialised memory. chadwickpy
documents both. The text box scores are identical.

## Speed

Measured on a 40-core machine, 2010 `events` (191,832 rows, 30 team files): about 5 to 8 seconds with
the default workers, about 90 seconds on one core. The C tools take about 8.7 seconds on one core.
Python is not faster than C per core; chadwickpy runs the team files on several cores.

## Data and credit

No Retrosheet data is included. The information used was obtained free of charge from, and is
copyrighted by, [Retrosheet](https://www.retrosheet.org). Follow Retrosheet's data-use notice when you
publish anything made from its files. The notice is printed the first time a season is downloaded.

retrosheetpy is independent: not written, endorsed or sponsored by Retrosheet or the Chadwick
Baseball Bureau. It is unrelated to any other project that uses the name `retrosheetpy`.

## Licence

GPL-3.0-or-later. See `LICENSE` and `NOTICE`.
