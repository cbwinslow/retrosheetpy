"""Retrosheet event-file names. A leaf module: nothing here imports the rest of the package."""

import re

_TEAM_FILE = re.compile(r"^\d{4}([A-Z0-9]{3})\.E[VD][A-Z]$", re.IGNORECASE)


def home_team(file_name: str) -> str | None:
    """The home-team code in a team event file name (``2010ANA.EVA`` -> ``ANA``), or None for the
    deduced-game files named by year alone (``1920.EDA``), which hold many teams' games."""
    m = _TEAM_FILE.match(file_name)
    return m.group(1).upper() if m else None
