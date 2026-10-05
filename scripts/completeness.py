"""Do we keep every event file in every Retrosheet decade archive, and do game counts match?

    uv run python scripts/completeness.py 1908 1914 1920 1962 2010

The C-tool comparison (parity.py) runs both sides on the same file list, so it cannot notice a file
we left out. This does: it lists every member of every cached decade archive and checks that each
one belongs to a season we keep, then checks that ``games`` has exactly as many rows as there are
``id,`` records in that season's raw event files. Run ``retrosheetpy get`` first for the seasons.
"""

import glob
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

import retrosheetpy as rs
from retrosheetpy.cache import _wanted


def main() -> int:
    root = rs.cache_dir() / "downloads" / "events_decade"
    ok = True
    for archive in sorted(glob.glob(str(root / "*.zip"))):
        names = [
            PurePosixPath(n).name
            for n in zipfile.ZipFile(archive).namelist()
            if not n.endswith("/")
        ]
        decade = int(Path(archive).name[:4])
        kept: set[str] = set()
        for year in range(1908 if decade == 1910 else decade, decade + 10):
            kept |= {n for n in names if _wanted(year).match(n)}
        dropped = [n for n in names if n not in kept]
        ok &= not dropped
        print(f"{Path(archive).name}: {len(names)} members, not kept: {dropped}")
    print("every member of every archive is kept:", ok)

    bad = 0
    for year in (int(a) for a in sys.argv[1:]):
        archive = zipfile.ZipFile(root / f"{max(year // 10 * 10, 1910)}seve.zip")
        in_files = 0
        for name in archive.namelist():
            base = PurePosixPath(name).name
            if _wanted(year).match(base) and PurePosixPath(name).suffix.upper().startswith(
                (".EV", ".ED")
            ):
                in_files += len(re.findall(r"^id,", archive.read(name).decode("latin-1"), re.M))
        rows = sum(1 for _ in rs.season(year).games().rows())
        bad += rows != in_files
        print(
            f"{year}: games in the raw files {in_files}, games rows {rows}",
            "OK" if rows == in_files else "MISMATCH",
        )
    return 0 if ok and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
