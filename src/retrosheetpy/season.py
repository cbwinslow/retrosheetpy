"""Download a season's event files into the cache and unpack just that season's files.

Chadwick's tools read ``TEAMyyyy`` and the ``.ROS`` files from the current folder, so every season
gets its own flat folder holding exactly the files Chadwick needs (event files, rosters, team list).
"""

import hashlib
import json
import os
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from retrosheetpy.catalog import Product, resolve
from retrosheetpy.client import Client, Fetch, atomic_write, http_fetch, iter_zip_members
from retrosheetpy.errors import IntegrityError

HOME_ENV = "RETROSHEETPY_HOME"
NOTICE = (
    "The information used here was obtained free of charge from and is copyrighted by "
    "Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org."
)
_NOTICE_MARK = ".notice-shown"
_RECORD = ".season.json"
MAX_MEMBER_BYTES = 256 * 1024**2


def cache_dir(override: str | Path | None = None) -> Path:
    """The cache folder: ``override``, else ``$RETROSHEETPY_HOME``, else ``~/.retrosheetpy``."""
    if override:
        return Path(override).expanduser()
    env = os.environ.get(HOME_ENV)
    return Path(env).expanduser() if env else Path.home() / ".retrosheetpy"


def _wanted(year: int) -> re.Pattern[str]:
    y = str(year)
    return re.compile(
        rf"^(?:{y}[A-Z0-9]{{3}}\.EV[NA]|[A-Z0-9]{{3}}{y}\.ROS|TEAM{y})$", re.IGNORECASE
    )


@dataclass(frozen=True)
class Season:
    year: int
    folder: Path
    event_files: tuple[Path, ...]
    roster_files: tuple[Path, ...]
    team_file: Path | None


def season_folder(cache: Path, year: int) -> Path:
    return cache / "seasons" / str(year)


def _scan(year: int, folder: Path) -> Season:
    files = sorted(p for p in folder.iterdir() if p.is_file() and _wanted(year).match(p.name))
    ev = tuple(p for p in files if p.suffix.upper() in (".EVN", ".EVA"))
    ros = tuple(p for p in files if p.suffix.upper() == ".ROS")
    team = next((p for p in files if p.name.upper() == f"TEAM{year}"), None)
    return Season(year, folder, ev, ros, team)


def _unpack(year: int, zip_path: Path, folder: Path, sha256: str) -> None:
    """Write the season's files to ``folder`` (replacing old contents), recording the zip hash."""
    pattern = _wanted(year)
    tmp = folder.with_name(folder.name + ".part")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    try:
        found = 0
        for name, stream in iter_zip_members(zip_path):
            base = PurePosixPath(name.replace("\\", "/")).name
            if not pattern.match(base):
                continue
            data = stream.read(MAX_MEMBER_BYTES + 1)
            if len(data) > MAX_MEMBER_BYTES:
                raise IntegrityError(f"{zip_path}:{name} is larger than {MAX_MEMBER_BYTES} bytes")
            atomic_write(tmp / base, data)
            found += 1
        if not found:
            raise IntegrityError(f"{zip_path} holds no files for {year}")
        atomic_write(tmp / _RECORD, json.dumps({"year": year, "zip_sha256": sha256}).encode())
        shutil.rmtree(folder, ignore_errors=True)
        tmp.replace(folder)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def _unpacked_ok(year: int, folder: Path, sha256: str) -> bool:
    try:
        rec = json.loads((folder / _RECORD).read_text())
    except (OSError, ValueError):
        return False
    return bool(rec.get("year") == year and rec.get("zip_sha256") == sha256)


def get(
    year: int,
    *,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    force: bool = False,
    notice: Callable[[str], None] | None = None,
) -> Season:
    """Make sure ``year``'s event files are downloaded and unpacked, and describe them.

    Each decade zip is fetched once and kept. ``notice`` (if given) receives Retrosheet's
    data-use notice the first time anything is downloaded into this cache.
    """
    root = cache_dir(cache)
    mark = root / _NOTICE_MARK
    res = resolve(Product.EVENTS_DECADE, season=year)
    client = Client(root / "downloads", fetch)
    if notice is not None and not mark.exists():
        notice(NOTICE)
        root.mkdir(parents=True, exist_ok=True)
        mark.write_text(NOTICE + "\n")
    art = client.download(res, force=force)
    folder = season_folder(root, year)
    if force or not _unpacked_ok(year, folder, art.sha256):
        folder.parent.mkdir(parents=True, exist_ok=True)
        _unpack(year, art.local_path, folder, art.sha256)
    return _scan(year, folder)


def cached_seasons(cache: str | Path | None = None) -> list[int]:
    """Seasons that are unpacked in the cache, oldest first."""
    base = season_folder(cache_dir(cache), 0).parent
    if not base.is_dir():
        return []
    return sorted(int(p.name) for p in base.iterdir() if p.name.isdigit() and p.is_dir())


def verify(cache: str | Path | None = None) -> list[str]:
    """Re-check every cached download against its recorded SHA-256; return problems (empty = ok)."""
    root = cache_dir(cache)
    problems: list[str] = []
    for year in cached_seasons(root):
        folder = season_folder(root, year)
        res = resolve(Product.EVENTS_DECADE, season=year)
        data = root / "downloads" / res.product.value / res.filename
        try:
            rec = json.loads((folder / _RECORD).read_text())
            actual = hashlib.sha256(data.read_bytes()).hexdigest()
        except (OSError, ValueError):
            problems.append(f"{year}: missing or unreadable download or record")
            continue
        if actual != rec.get("zip_sha256"):
            problems.append(f"{year}: {res.filename} no longer matches what was unpacked")
    return problems


def clear(cache: str | Path | None = None) -> Path:
    """Delete the whole cache folder and return its path."""
    root = cache_dir(cache)
    shutil.rmtree(root, ignore_errors=True)
    return root
