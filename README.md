# retrosheetpy

Ask for a Retrosheet season, get data tables. `retrosheetpy` downloads a season from
[Retrosheet](https://www.retrosheet.org), keeps it in a cache folder, runs the Chadwick tools
(through [chadwickpy](https://pypi.org/project/chadwickpy/)) on it, and writes CSV ready for a database.

> **Status: under construction (not yet released).** Nothing here works end to end yet.

```
retrosheetpy get 2010      # download and cache the 2010 season
retrosheetpy events 2010   # play-by-play CSV
```

## Data and credit

No Retrosheet data is included. The information used was obtained free of charge from, and is
copyrighted by, [Retrosheet](https://www.retrosheet.org). Follow Retrosheet's data-use notice
when you publish anything made from its files.

retrosheetpy is independent: not written, endorsed or sponsored by Retrosheet or the Chadwick
Baseball Bureau. It is unrelated to any other project that uses the name `retrosheetpy`.

## Licence

GPL-3.0-or-later. See `LICENSE` and `NOTICE`.
