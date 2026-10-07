"""The functions most people use: ``events(2010)``, ``games(range(2000, 2011), home="NYA")``, ...

Each takes one season or several (``years``), downloads and unpacks what is missing, and returns a
:class:`Table` (or :class:`BoxScores`). Several seasons give one combined Table: the rows of each
season in order, the header once. Rows already begin with the game id, which contains the year.
"""

import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Unpack

from retrosheetpy.cache import Season, print_notice
from retrosheetpy.cache import get as get_season
from retrosheetpy.client import Fetch, http_fetch
from retrosheetpy.errors import ToolError
from retrosheetpy.kinds import Kind
from retrosheetpy.options import Options, Opts
from retrosheetpy.table import BoxScores, Table
from retrosheetpy.tools import TOOLS, tool

Years = int | Iterable[int]


def _years(years: Years) -> list[int]:
    listed = [years] if isinstance(years, int) else list(years)
    if not listed:
        raise ValueError("no years given")
    if len(set(listed)) != len(listed):
        raise ValueError(f"years repeat: {listed}")
    return listed


def _seasons(
    years: Years, cache: str | Path | None, fetch: Fetch, kind: Kind | str
) -> list[Season]:
    kind = Kind.parse(kind)
    return [
        get_season(y, kind=kind, cache=cache, fetch=fetch, notice=print_notice)
        for y in _years(years)
    ]


def _table(
    name: str, years: Years, cache: str | Path | None, fetch: Fetch, kind: Kind | str, opts: Opts
) -> Table:
    t = tool(name)
    options = Options.build(t, opts)  # check the options before downloading anything
    return Table(t, _seasons(years, cache, fetch, kind), options)


def events(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> Table:
    """Every play: one row per event (Chadwick's cwevent), 164 columns."""
    return _table("events", years, cache, fetch, kind, opts)


def games(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> Table:
    """One row per game (cwgame), 182 columns."""
    return _table("games", years, cache, fetch, kind, opts)


def daily(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> Table:
    """One row per player per game (cwdaily), 154 columns."""
    return _table("daily", years, cache, fetch, kind, opts)


def subs(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> Table:
    """One row per substitution (cwsub)."""
    return _table("subs", years, cache, fetch, kind, opts)


def comments(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> Table:
    """One row per comment record (cwcomment)."""
    return _table("comments", years, cache, fetch, kind, opts)


def boxscores(
    years: Years,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    **opts: Unpack[Opts],
) -> BoxScores:
    """Box scores (cwbox) as text, XML or SportsML."""
    t = tool("boxscores")
    options = Options.build(t, opts)
    return BoxScores(t, _seasons(years, cache, fetch, kind), options)


def season(
    year: int,
    *,
    kind: Kind | str = Kind.REGULAR,
    cache: str | Path | None = None,
    fetch: Fetch = http_fetch,
    force: bool = False,
) -> Season:
    """Download (if needed) and unpack one season; returns the :class:`Season` to ask tables of.

    ``kind`` picks the Retrosheet files: ``"regular"`` (default), ``"postseason"``, ``"allstar"``,
    ``"negro"`` (Negro Leagues play-by-play), ``"negro_box"`` and ``"box"`` (games known only from
    box scores)."""
    return get_season(year, kind=kind, cache=cache, fetch=fetch, force=force, notice=print_notice)


@dataclass(frozen=True)
class Field:
    """One output column of a Chadwick tool, as Chadwick describes it."""

    number: int
    description: str
    extended: bool  # True for the -x fields, False for the -f fields
    default: bool  # printed by Chadwick when no field list is given (we print all regardless)


def fields(name: str) -> list[Field]:
    """The numbered fields of a table (what Chadwick's ``-d`` lists), in output order.

    The numbers are what ``fields=`` and ``extended=`` take. Column *names* are on
    ``table.columns``.
    """
    t = tool(name)
    if not t.rows:
        raise ValueError(f"{name} has no fields")
    done = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-m", "chadwickpy", t.command, "-d"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Chadwick prints the -d listing on stderr
        check=False,
    )
    if done.returncode != 0:
        raise ToolError(f"{t.command} -d failed: {done.stdout.decode('latin-1')[-300:]}")
    out: list[Field] = []
    extended = False
    for line in done.stdout.decode("latin-1").splitlines():
        if line.startswith("These additional fields"):
            extended = True
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            text = parts[1].rstrip()
            default = text.endswith("*")
            out.append(Field(int(parts[0]), text.rstrip("*").rstrip(), extended, default))
    return out


__all__ = [
    "TOOLS",
    "Field",
    "boxscores",
    "comments",
    "daily",
    "events",
    "fields",
    "games",
    "season",
    "subs",
]
