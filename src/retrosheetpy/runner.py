"""Run one Chadwick tool over a season's files and stream what it prints.

Chadwick reads ``TEAMyyyy`` and the ``.ROS`` files from the current folder, so each tool runs in
the season's folder. It runs as a subprocess (``python -m chadwickpy``): that keeps the folder
change out of this process, and chadwickpy spreads the team files over the CPU cores itself.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from typing import IO, TYPE_CHECKING, Literal

from retrosheetpy.errors import ToolError
from retrosheetpy.options import MAX_JOBS, Options
from retrosheetpy.tools import Tool

if TYPE_CHECKING:
    from retrosheetpy.cache import Season

BoxFormat = Literal["text", "xml", "sportsml"]
_BOX_FLAG = {"text": None, "xml": "-X", "sportsml": "-S"}
DEFAULT_MAX_JOBS = 16


def default_jobs() -> int:
    """Workers to use when the caller does not say: the cores this process may use, leaving one
    free on bigger machines, never more than ``DEFAULT_MAX_JOBS``.

    Why a cap: more workers than free cores only makes them queue (and use more memory); past about
    16 a season gains little. Why not ``os.cpu_count()``: that ignores CPU affinity limits.
    """
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:  # not available on macOS or Windows
        cores = os.cpu_count() or 1
    return max(1, min(DEFAULT_MAX_JOBS, cores - 1 if cores > 4 else cores, MAX_JOBS))


def _fields(spec: str | None, chose: bool, highest: int) -> str:
    if spec is not None:
        return spec
    return "" if chose else f"0-{highest}"


def files_for(season: "Season", opts: Options) -> list[str]:
    """The season's event file names, narrowed to the requested home teams (in the given order)."""
    if not opts.home:
        return [p.name for p in season.event_files]
    by_team: dict[str, list[str]] = {}
    for path in season.event_files:
        by_team.setdefault(path.name[4:7].upper(), []).append(path.name)
    missing = [t for t in opts.home if t not in by_team]
    if missing:
        raise ValueError(
            f"{season.year}: no event file for home team {', '.join(missing)}; "
            f"available: {' '.join(sorted(by_team))}"
        )
    return [name for team in opts.home for name in by_team[team]]


def command(
    tool: Tool,
    season: "Season",
    opts: Options,
    *,
    box: BoxFormat = "text",
    files: list[str] | None = None,
) -> list[str]:
    cmd = [sys.executable, "-m", "chadwickpy", tool.command, "-q", "-y", str(season.year)]
    if opts.game:
        cmd += ["-i", opts.game]
    if opts.start:
        cmd += ["-s", opts.start]
    if opts.end:
        cmd += ["-e", opts.end]
    if tool.rows:
        # Choosing fields or extended means "just these": whichever you leave out is not printed.
        # Choosing neither prints everything.
        chose = opts.fields is not None or opts.extended is not None
        cmd += ["-n", "-f", _fields(opts.fields, chose, tool.max_field)]
        if tool.max_ext_field is not None:
            cmd += ["-x", _fields(opts.extended, chose, tool.max_ext_field)]
    elif _BOX_FLAG[box]:
        cmd.append(_BOX_FLAG[box] or "")
    cmd += ["-j", str(opts.jobs or default_jobs())]
    return cmd + (files if files is not None else files_for(season, opts))


@contextmanager
def stream(
    tool: Tool,
    season: "Season",
    opts: Options,
    *,
    box: BoxFormat = "text",
    files: list[str] | None = None,
) -> Iterator[IO[bytes]]:
    """Yield the tool's stdout (binary) while it runs; raise ToolError if it fails.

    If the caller stops early (leaves the block before the end), the process is stopped and no
    error is raised for that.
    """
    if not season.event_files:
        raise ToolError(f"no event files for {season.year}")
    cmd = command(tool, season, opts, box=box, files=files)
    with tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
            cmd, cwd=season.folder, stdout=subprocess.PIPE, stderr=errors
        )
        assert proc.stdout is not None  # noqa: S101 - guaranteed by stdout=PIPE
        finished = False
        try:
            yield proc.stdout
            finished = True
        finally:
            if not finished:
                proc.kill()
            proc.stdout.close()
            code = proc.wait()
        if code != 0:
            errors.seek(0)
            tail = errors.read().decode("latin-1").strip()[-500:]
            raise ToolError(f"{tool.command} failed for {season.year} ({code}): {tail}")


def run(
    tool: Tool,
    season: "Season",
    out: IO[bytes],
    opts: Options | None = None,
    *,
    box: BoxFormat = "text",
) -> None:
    """Copy the tool's raw output (Chadwick's own bytes) for one season into ``out``."""
    with stream(tool, season, opts or Options(), box=box) as src:
        shutil.copyfileobj(src, out, 1 << 20)
