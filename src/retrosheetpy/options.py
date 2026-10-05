"""The options every table shares, checked once and turned into Chadwick's command-line flags."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypedDict

from retrosheetpy.tools import Tool

FieldSpec = str | int | Iterable[int]


class Opts(TypedDict, total=False):
    """Keyword options accepted by ``events``, ``games``, ``daily``, ``subs``, ``comments`` and
    ``boxscores`` (everywhere in the API and as flags on the command line)."""

    home: str | Iterable[str]  # only these home teams' files (e.g. "NYA" or ["NYA", "BOS"])
    game: str  # only this game id (Chadwick -i)
    start: str  # earliest date to process, "mmdd" (Chadwick -s)
    end: str  # latest date to process, "mmdd" (Chadwick -e)
    fields: FieldSpec  # field numbers to output (Chadwick -f); with neither given: all fields
    extended: FieldSpec  # extended field numbers (Chadwick -x); leave out whichever you do not want
    jobs: int  # worker processes; 1 = one at a time; default automatic


_TEAM = re.compile(r"[A-Za-z0-9]{3}")
_MMDD = re.compile(r"(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])")
_GAME_ID = re.compile(r"[A-Za-z0-9]{3}[0-9]{9}")  # team + yyyymmdd + game number (0, 1, 2)
MAX_JOBS = 32


def _spec(value: FieldSpec, highest: int, what: str) -> str:
    """Turn 5, "0-5,9" or [0, 1, 7] into Chadwick's "-f" syntax, checking the range."""
    if isinstance(value, int):
        numbers = [value]
    elif isinstance(value, str):
        numbers = []
        for part in value.split(","):
            lo, dash, hi = part.strip().partition("-")
            if not lo.isdigit() or (dash and not hi.isdigit()):
                raise ValueError(f"{what}: cannot read {part!r}; use numbers like 0-5,9")
            numbers += range(int(lo), int(hi or lo) + 1)
    else:
        numbers = list(value)
    if not numbers:
        raise ValueError(f"{what}: no field numbers given")
    for n in numbers:
        if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= highest:
            raise ValueError(f"{what}: {n!r} is not a field number from 0 to {highest}")
    return ",".join(str(n) for n in sorted(set(numbers)))


@dataclass(frozen=True)
class Options:
    """Validated options. Build with :meth:`build`; every problem is a ValueError up front."""

    home: tuple[str, ...] = ()
    game: str | None = None
    start: str | None = None
    end: str | None = None
    fields: str | None = None
    extended: str | None = None
    jobs: int | None = None

    @classmethod
    def build(cls, tool: Tool, opts: Opts) -> "Options":
        unknown = set(opts) - set(Opts.__annotations__)
        if unknown:
            raise TypeError(f"unknown option(s): {', '.join(sorted(unknown))}")
        raw_home = opts.get("home", ())
        home = (raw_home,) if isinstance(raw_home, str) else tuple(raw_home)
        for team in home:
            if not _TEAM.fullmatch(team):
                raise ValueError(f"home: {team!r} is not a three-character team code")
        game, start, end = opts.get("game"), opts.get("start"), opts.get("end")
        if game is not None and not _GAME_ID.fullmatch(game):
            raise ValueError(f"game: {game!r} is not a game id like 'ANA201004050'")
        for name, value in (("start", start), ("end", end)):
            if value is not None and not _MMDD.fullmatch(value):
                raise ValueError(f"{name}: {value!r} is not a date like '0405' (mmdd)")
        fields = opts.get("fields")
        extended = opts.get("extended")
        if not tool.rows and (fields is not None or extended is not None):
            raise ValueError(f"{tool.name} has no fields to choose from")
        if extended is not None and tool.max_ext_field is None:
            raise ValueError(f"{tool.name} has no extended fields")
        jobs = opts.get("jobs")
        if jobs is not None and not (isinstance(jobs, int) and 1 <= jobs <= MAX_JOBS):
            raise ValueError(f"jobs: use a number from 1 to {MAX_JOBS}")
        return cls(
            home=tuple(t.upper() for t in home),
            game=game.upper() if game else None,
            start=start,
            end=end,
            fields=None if fields is None else _spec(fields, tool.max_field, "fields"),
            extended=(
                None if extended is None else _spec(extended, tool.max_ext_field or 0, "extended")
            ),
            jobs=jobs,
        )
