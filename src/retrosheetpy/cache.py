"""Download a season's event files into the cache and unpack just that season's files.

Chadwick's tools read ``TEAMyyyy`` and the ``.ROS`` files from the current folder, so every season
gets its own flat folder holding exactly the files Chadwick needs (event files, rosters, team list).
"""

import hashlib
import json
import os
import shutil
import sys
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Unpack

from retrosheetpy.client import Client, Fetch, atomic_write, http_fetch, iter_zip_members
from retrosheetpy.errors import IntegrityError, SeasonNotFoundError
from retrosheetpy.kinds import Kind, is_event_file, resource_for, wanted
from retrosheetpy.names import home_team
from retrosheetpy.options import Options, Opts
from retrosheetpy.table import BoxScores, Table
from retrosheetpy.tools import tool

HOME_ENV = "RETROSHEETPY_HOME"
NOTICE = (
    "The information used here was obtained free of charge from and is copyrighted by "
    "Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org."
)
_NOTICE_MARK = ".notice-shown"


def print_notice(text: str) -> None:
    """Show Retrosheet's data-use notice on stderr (once per cache, the first time we download)."""
    print(text, file=sys.stderr)


_RECORD = ".season.json"
LAYOUT = 3  # bump when the set of files kept from an archive changes; old unpacks are redone
MAX_MEMBER_BYTES = 256 * 1024**2


def cache_dir(override: str | Path | None = None) -> Path:
    """The cache folder: ``override``, else ``$RETROSHEETPY_HOME``, else ``~/.retrosheetpy``."""
    if override:
        return Path(override).expanduser()
    env = os.environ.get(HOME_ENV)
    return Path(env).expanduser() if env else Path.home() / ".retrosheetpy"


_wanted = wanted  # kept for scripts that import it from here


@dataclass(frozen=True)
class Season:
    """One season unpacked in the cache: where its files are, and the tables you can ask for."""

    year: int
    folder: Path
    event_files: tuple[Path, ...]
    roster_files: tuple[Path, ...]
    team_file: Path | None
    kind: Kind = Kind.REGULAR

    @property
    def team_event_files(self) -> tuple[Path, ...]:
        """The event files named by home team. The rest (``1920.EDA``) hold deduced games of many
        teams together, so they belong to no single team."""
        return tuple(p for p in self.event_files if home_team(p.name))

    @property
    def teams(self) -> tuple[str, ...]:
        """Home-team codes with an event file this season (Retrosheet names files by home team)."""
        return tuple(sorted({t for p in self.event_files if (t := home_team(p.name))}))

    def events(self, **opts: Unpack[Opts]) -> Table:
        """Every play: one row per event (Chadwick's cwevent)."""
        return self._table("events", opts)

    def games(self, **opts: Unpack[Opts]) -> Table:
        """One row per game (cwgame)."""
        return self._table("games", opts)

    def daily(self, **opts: Unpack[Opts]) -> Table:
        """One row per player per game (cwdaily)."""
        return self._table("daily", opts)

    def subs(self, **opts: Unpack[Opts]) -> Table:
        """One row per substitution (cwsub)."""
        return self._table("subs", opts)

    def comments(self, **opts: Unpack[Opts]) -> Table:
        """One row per comment record (cwcomment)."""
        return self._table("comments", opts)

    def boxscores(self, **opts: Unpack[Opts]) -> BoxScores:
        """Box scores as text, XML or SportsML (cwbox)."""
        return BoxScores(tool("boxscores"), [self], Options.build(tool("boxscores"), opts))

    def _table(self, name: str, opts: Opts) -> Table:
        return Table(tool(name), [self], Options.build(tool(name), opts))


def season_folder(cache: Path, year: int, kind: Kind = Kind.REGULAR) -> Path:
    """Regular seasons live in ``seasons/2010``; other kinds in ``seasons/postseason/2010``."""
    base = cache / "seasons"
    return (base if kind is Kind.REGULAR else base / kind.value) / str(year)


def _scan(year: int, kind: Kind, folder: Path) -> Season:
    files = sorted(p for p in folder.iterdir() if p.is_file() and wanted(year).match(p.name))
    ev = tuple(p for p in files if is_event_file(p.name))
    ros = tuple(p for p in files if p.suffix.upper() == ".ROS")
    team = next((p for p in files if p.name.upper() == f"TEAM{year}"), None)
    return Season(year, folder, ev, ros, team, kind)


def _years_in(zip_path: Path) -> list[int]:
    """The seasons that have event files in an archive (for the "not found" message)."""
    with zipfile.ZipFile(zip_path) as zf:
        names = [PurePosixPath(n).name for n in zf.namelist()]
    return sorted({int(n[:4]) for n in names if n[:4].isdigit() and is_event_file(n)})


def _unpack(year: int, kind: Kind, zip_path: Path, folder: Path, sha256: str) -> None:
    """Write the season's files to ``folder`` (replacing old contents), recording the zip hash."""
    pattern = wanted(year)
    tmp = folder.with_name(folder.name + ".part")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        events = 0
        have_team_file = False
        for name, stream in iter_zip_members(zip_path):
            base = PurePosixPath(name.replace("\\", "/")).name
            if not pattern.match(base):
                continue
            data = stream.read(MAX_MEMBER_BYTES + 1)
            if len(data) > MAX_MEMBER_BYTES:
                raise IntegrityError(f"{zip_path}:{name} is larger than {MAX_MEMBER_BYTES} bytes")
            # No per-file fsync: the unpacked folder can always be rebuilt from the saved zip, and
            # flushing ~600 small files one by one is very slow on a busy disk. The folder only
            # appears under its real name (rename) after every file is written.
            (tmp / base).write_bytes(data)
            events += is_event_file(base)
            have_team_file |= base.upper() == f"TEAM{year}"
        if not events:
            years = _years_in(zip_path)
            have = f"{years[0]} to {years[-1]}" if years else "none"
            raise SeasonNotFoundError(
                f"Retrosheet has no {kind.label} event files for {year} ({zip_path.name}); "
                f"it has seasons {have}"
            )
        if not have_team_file:
            # The Chadwick tools refuse to run without TEAMyyyy in the folder; some archives (Negro
            # Leagues, early box scores) do not ship one, and an empty file is what they accept.
            (tmp / f"TEAM{year}").write_bytes(b"")
        atomic_write(
            tmp / _RECORD,
            json.dumps(
                {"year": year, "kind": kind.value, "zip_sha256": sha256, "layout": LAYOUT}
            ).encode(),
        )
        shutil.rmtree(folder, ignore_errors=True)
        tmp.replace(folder)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def _unpacked_ok(year: int, kind: Kind, folder: Path, sha256: str) -> bool:
    try:
        rec = json.loads((folder / _RECORD).read_text())
    except (OSError, ValueError):
        return False
    return bool(
        rec.get("year") == year
        and rec.get("kind", Kind.REGULAR.value) == kind.value
        and rec.get("zip_sha256") == sha256
        and rec.get("layout") == LAYOUT
    )


def get(
    year: int,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    force: bool = False,
    notice: Callable[[str], None] | None = None,
) -> Season:
    """Make sure ``year``'s event files of this ``kind`` are downloaded and unpacked, and say where.

    Each archive is fetched once and kept. ``notice`` (if given) receives Retrosheet's data-use
    notice the first time anything is downloaded into this cache.
    """
    kind = Kind.parse(kind)
    root = cache_dir(cache)
    mark = root / _NOTICE_MARK
    res = resource_for(kind, year)
    client = Client(root / "downloads", fetch)
    if notice is not None and not mark.exists():
        notice(NOTICE)
        root.mkdir(parents=True, exist_ok=True)
        mark.write_text(NOTICE + "\n")
    art = client.download(res, force=force)
    folder = season_folder(root, year, kind)
    if force or not _unpacked_ok(year, kind, folder, art.sha256):
        folder.parent.mkdir(parents=True, exist_ok=True)
        _unpack(year, kind, art.local_path, folder, art.sha256)
    return _scan(year, kind, folder)


def cached_seasons(cache: str | Path | None = None, kind: Kind | str = Kind.REGULAR) -> list[int]:
    """Seasons of this kind that are unpacked in the cache, oldest first."""
    kind = Kind.parse(kind)
    base = season_folder(cache_dir(cache), 0, kind).parent
    if not base.is_dir():
        return []
    return sorted(int(p.name) for p in base.iterdir() if p.name.isdigit() and p.is_dir())


def verify(cache: str | Path | None = None) -> list[str]:
    """Re-check every cached download against its recorded SHA-256; return problems (empty = ok)."""
    root = cache_dir(cache)
    problems: list[str] = []
    for kind in Kind:
        for year in cached_seasons(root, kind):
            label = f"{kind.value} {year}"
            folder = season_folder(root, year, kind)
            res = resource_for(kind, year)
            data = root / "downloads" / res.product.value / res.filename
            try:
                rec = json.loads((folder / _RECORD).read_text())
                actual = hashlib.sha256(data.read_bytes()).hexdigest()
            except (OSError, ValueError):
                problems.append(f"{label}: missing or unreadable download or record")
                continue
            if actual != rec.get("zip_sha256"):
                problems.append(f"{label}: {res.filename} no longer matches what was unpacked")
    return problems


def clear(cache: str | Path | None = None) -> Path:
    """Delete the whole cache folder and return its path."""
    root = cache_dir(cache)
    shutil.rmtree(root, ignore_errors=True)
    return root
