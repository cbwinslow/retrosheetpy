"""Run chadwickpy's tools on a cached season. The only module that knows about chadwickpy.

Chadwick reads ``TEAMyyyy`` and the ``.ROS`` files from the current folder, so each tool runs in
the season's folder. It runs as a subprocess (``python -m chadwickpy``): that keeps the folder
change out of this process, and chadwickpy spreads the team files over the CPU cores itself.
"""

import csv
import io
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from chadwickpy.tools import comment as cw_comment
from chadwickpy.tools import cwgame as cw_game
from chadwickpy.tools import daily as cw_daily
from chadwickpy.tools import events as cw_events
from chadwickpy.tools import sub as cw_sub

from retrosheetpy.errors import ToolError
from retrosheetpy.season import Season, get


@dataclass(frozen=True)
class Table:
    """One chadwickpy tool and how retrosheetpy calls it."""

    name: str  # retrosheetpy's name for it
    tool: str  # the chadwickpy command
    max_field: int
    max_ext_field: int | None = None
    csv_output: bool = True

    @property
    def suffix(self) -> str:
        return "csv" if self.csv_output else "txt"


TABLES: dict[str, Table] = {
    t.name: t
    for t in (
        Table("events", "cwevent", cw_events.MAX_FIELD, cw_events.MAX_EXT_FIELD),
        Table("games", "cwgame", cw_game.MAX_FIELD, cw_game.MAX_EXT_FIELD),
        Table("daily", "cwdaily", cw_daily.MAX_FIELD),
        Table("subs", "cwsub", cw_sub.MAX_FIELD),
        Table("comments", "cwcomment", cw_comment.MAX_FIELD),
        Table("boxscores", "cwbox", 0, csv_output=False),
    )
}


def _command(table: Table, season: Season, jobs: int | None) -> list[str]:
    cmd = [sys.executable, "-m", "chadwickpy", table.tool, "-q", "-y", str(season.year)]
    if table.csv_output:
        cmd += ["-n", "-f", f"0-{table.max_field}"]
        if table.max_ext_field is not None:
            cmd += ["-x", f"0-{table.max_ext_field}"]
    if jobs is not None:
        cmd += ["-j", str(jobs)]
    return cmd + [p.name for p in season.event_files]


def run(table: Table, season: Season, out: IO[bytes], *, jobs: int | None = None) -> None:
    """Write the tool's output for every team file of ``season`` to ``out`` (raw bytes)."""
    if not season.event_files:
        raise ToolError(f"no event files for {season.year}")
    with tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            _command(table, season, jobs),
            cwd=season.folder,
            stdout=subprocess.PIPE,
            stderr=errors,
        )
        assert proc.stdout is not None  # noqa: S101 - set by stdout=PIPE
        with proc.stdout:
            shutil.copyfileobj(proc.stdout, out, 1 << 20)
        code = proc.wait()
        if code != 0:
            errors.seek(0)
            tail = errors.read().decode("latin-1").strip()[-500:]
            raise ToolError(f"{table.tool} failed ({code}): {tail}")


def write(table: Table, season: Season, path: Path, *, jobs: int | None = None) -> Path:
    """Run the tool and write its output to ``path`` (written whole or not at all)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    try:
        with tmp.open("wb") as f:
            run(table, season, f, jobs=jobs)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def rows(table: Table, season: Season, *, jobs: int | None = None) -> list[dict[str, str]]:
    """The tool's output as a list of dicts keyed by field name (CSV tables only)."""
    if not table.csv_output:
        raise ValueError(f"{table.name} is text, not rows")
    buf = io.BytesIO()
    run(table, season, buf, jobs=jobs)
    return list(csv.DictReader(io.StringIO(buf.getvalue().decode("latin-1"))))


def _season(year: int, cache: str | Path | None) -> Season:
    return get(year, cache=cache)


def events(
    year: int, *, cache: str | Path | None = None, jobs: int | None = None
) -> list[dict[str, str]]:
    """Every play of ``year`` as dicts (downloads the season first if needed)."""
    return rows(TABLES["events"], _season(year, cache), jobs=jobs)


def games(
    year: int, *, cache: str | Path | None = None, jobs: int | None = None
) -> list[dict[str, str]]:
    """One row per game."""
    return rows(TABLES["games"], _season(year, cache), jobs=jobs)


def daily(
    year: int, *, cache: str | Path | None = None, jobs: int | None = None
) -> list[dict[str, str]]:
    """One row per player per game."""
    return rows(TABLES["daily"], _season(year, cache), jobs=jobs)


def subs(
    year: int, *, cache: str | Path | None = None, jobs: int | None = None
) -> list[dict[str, str]]:
    """One row per substitution."""
    return rows(TABLES["subs"], _season(year, cache), jobs=jobs)


def comments(
    year: int, *, cache: str | Path | None = None, jobs: int | None = None
) -> list[dict[str, str]]:
    """One row per comment in the event files."""
    return rows(TABLES["comments"], _season(year, cache), jobs=jobs)


def boxscores(year: int, *, cache: str | Path | None = None, jobs: int | None = None) -> str:
    """Box scores for every game, as text."""
    buf = io.BytesIO()
    run(TABLES["boxscores"], _season(year, cache), buf, jobs=jobs)
    return buf.getvalue().decode("latin-1")
