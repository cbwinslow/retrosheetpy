"""The kinds of Retrosheet game files, and where each lives.

Retrosheet publishes them in separate archives, and each has its own rosters and team list, so each
kind is unpacked on its own (``2010`` regular season and ``2010`` postseason never share a folder).
"""

import re
from enum import StrEnum

from retrosheetpy.catalog import Product, Resource, resolve


class Kind(StrEnum):
    """Which Retrosheet files a season is read from."""

    REGULAR = "regular"  # regular-season play-by-play, 1908 on (the decade archives)
    POSTSEASON = "postseason"  # World Series, playoffs, divisional series (allpost.zip)
    ALLSTAR = "allstar"  # All-Star games (allas.zip)
    NEGRO = "negro"  # Negro Leagues play-by-play (allevr.zip)
    NEGRO_BOX = "negro_box"  # Negro Leagues games known from box scores only (allebr.zip)
    BOX = "box"  # major-league games from 1897 to 1909 known from box scores only

    @classmethod
    def parse(cls, value: "Kind | str") -> "Kind":
        try:
            return cls(value)
        except ValueError:
            raise ValueError(
                f"unknown kind {value!r}; choose from {', '.join(k.value for k in cls)}"
            ) from None

    @property
    def label(self) -> str:
        return {
            Kind.REGULAR: "regular-season",
            Kind.POSTSEASON: "postseason",
            Kind.ALLSTAR: "All-Star",
            Kind.NEGRO: "Negro Leagues",
            Kind.NEGRO_BOX: "Negro Leagues box-score",
            Kind.BOX: "box-score-only",
        }[self]


def resource_for(kind: Kind, year: int) -> Resource:
    """The Retrosheet archive that holds ``year`` of this kind."""
    if kind is Kind.REGULAR:
        return resolve(Product.EVENTS_DECADE, season=year)
    if kind is Kind.BOX:
        return resolve(Product.BOX_ARCHIVE, season=year)
    product = {
        Kind.POSTSEASON: Product.EVENTS_POSTSEASON,
        Kind.ALLSTAR: Product.EVENTS_ALLSTAR,
        Kind.NEGRO: Product.EVENTS_NEGRO_LEAGUE,
        Kind.NEGRO_BOX: Product.BOX_NEGRO_LEAGUE,
    }[kind]
    return resolve(product)


def wanted(year: int) -> re.Pattern[str]:
    """The files of one season in any archive: event files (``2010ANA.EVA``, ``2010WS.EVE``,
    ``1920.EDA``, ``1912.EBR``), rosters (``ANA2010.ROS``) and the team list (``TEAM2010``)."""
    y = str(year)
    return re.compile(
        rf"^(?:{y}[A-Z0-9]*\.E[VDB][A-Z]|[A-Z0-9]{{3}}{y}\.ROS|TEAM{y})$", re.IGNORECASE
    )


def is_event_file(name: str) -> bool:
    return bool(re.search(r"\.E[VDB][A-Z]$", name, re.IGNORECASE))
