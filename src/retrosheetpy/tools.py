"""The six Chadwick programs, and what retrosheetpy needs to know to call each one.

This and ``runner.py`` are the only modules that know about chadwickpy.
"""

from dataclasses import dataclass

from chadwickpy.tools import comment as cw_comment
from chadwickpy.tools import cwgame as cw_game
from chadwickpy.tools import daily as cw_daily
from chadwickpy.tools import events as cw_events
from chadwickpy.tools import sub as cw_sub


@dataclass(frozen=True)
class Tool:
    """One Chadwick program: its chadwickpy command and its numbered output fields."""

    name: str  # retrosheetpy's name, the same as Chadwick's without the "cw" (daily, events, ...)
    command: str  # the chadwickpy command (cwevent, ...)
    max_field: int  # highest -f field number (0 for boxscores, which have no fields)
    max_ext_field: int | None = None  # highest -x field number; None if the tool has no -x
    rows: bool = True  # False for boxscores, which are text rather than rows


TOOLS: dict[str, Tool] = {
    t.name: t
    for t in (
        Tool("events", "cwevent", cw_events.MAX_FIELD, cw_events.MAX_EXT_FIELD),
        Tool("games", "cwgame", cw_game.MAX_FIELD, cw_game.MAX_EXT_FIELD),
        Tool("daily", "cwdaily", cw_daily.MAX_FIELD),
        Tool("subs", "cwsub", cw_sub.MAX_FIELD),
        Tool("comments", "cwcomment", cw_comment.MAX_FIELD),
        Tool("boxscores", "cwbox", 0, rows=False),
    )
}


def tool(name: str) -> Tool:
    try:
        return TOOLS[name]
    except KeyError:
        raise ValueError(f"unknown table {name!r}; choose from {', '.join(TOOLS)}") from None
