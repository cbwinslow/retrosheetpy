"""Compare our ``games`` table with Retrosheet's own per-season CSV (``gameinfo.csv``).

    uv run python scripts/crosscheck.py 1908 1914 1920 1962 2010

The two come from different pipelines (Chadwick reading the event files, and Retrosheet's own
export), so agreement is independent evidence that the tables represent Retrosheet's data. The CSV
also lists postseason, all-star and box-score-only games, which the decade event archives do not
hold; those are counted but not compared. Downloads the CSV archives with retrosheetpy's own client.
"""

import collections
import csv
import io
import sys
import zipfile

import retrosheetpy as rs
from retrosheetpy.client import Client

# (our Chadwick column, Retrosheet gameinfo.csv column)
PAIRS = [
    ("AWAY_TEAM_ID", "visteam"), ("HOME_TEAM_ID", "hometeam"), ("PARK_ID", "site"),
    ("GAME_DT", "date"), ("GAME_CT", "number"), ("ATTEND_PARK_CT", "attendance"),
    ("AWAY_SCORE_CT", "vruns"), ("HOME_SCORE_CT", "hruns"), ("WIN_PIT_ID", "wp"),
    ("LOSE_PIT_ID", "lp"), ("SAVE_PIT_ID", "save"), ("TEMP_PARK_CT", "temp"),
    ("MINUTES_GAME_CT", "timeofgame"),
]  # fmt: skip


def main() -> int:
    client = Client(rs.cache_dir() / "downloads")
    problems = 0
    for year in (int(a) for a in sys.argv[1:]):
        artifact = client.download(rs.resolve(rs.Product.YEARLY_CSV, year))
        with zipfile.ZipFile(artifact.local_path) as z, z.open(f"{year}gameinfo.csv") as f:
            theirs = {
                r["gid"]: r
                for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", newline=""))
            }
        ours = {r["GAME_ID"]: r for r in rs.games(year)}
        common = set(ours) & set(theirs)
        bad: collections.Counter[str] = collections.Counter()
        examples: dict[str, tuple[str, str, str]] = {}
        for gid in sorted(common):
            for our_col, their_col in PAIRS:
                a, b = ours[gid][our_col].strip(), theirs[gid][their_col].strip()
                if a != b and not (
                    b == "" and a in ("", "0", "-1")
                ):  # Retrosheet leaves unknown blank
                    bad[our_col] += 1
                    examples.setdefault(our_col, (gid, a, b))
        problems += sum(bad.values()) + len(set(ours) - set(theirs))
        print(
            f"{year}: compared {len(common)} games x {len(PAIRS)} fields | only in ours: "
            f"{len(set(ours) - set(theirs))} | only in Retrosheet's CSV (postseason, all-star, "
            f"box-score-only): {len(set(theirs) - set(ours))} | mismatches: {dict(bad) or 'none'}"
        )
        for col, (gid, a, b) in examples.items():
            print(f"     e.g. {gid} {col}: ours {a!r}, Retrosheet {b!r}")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
