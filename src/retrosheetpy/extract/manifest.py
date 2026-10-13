"""Manifest of canonical URLs for Retrosheet data assets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Manifest:
    """Provides authoritative URLs for Retrosheet archives and reference tables."""

    base_url: str = "https://www.retrosheet.org"

    def event_archive_url(self, year: int) -> str:
        """Play-by-play regular season archive: e.g. 2024eve.zip"""
        return f"{self.base_url}/events/{year}eve.zip"

    def event_archive_fallback_url(self, year: int) -> str:
        """Fallback archive URL: e.g. 2024seve.zip"""
        return f"{self.base_url}/events/{year}seve.zip"

    def postseason_archive_url(self, year: int) -> str:
        """Postseason play-by-play archive: e.g. 2024post.zip"""
        return f"{self.base_url}/events/{year}post.zip"

    def gamelog_archive_url(self, year: int) -> str:
        """Game log archive: e.g. gl2024.zip"""
        return f"{self.base_url}/gamelogs/gl{year}.zip"

    def schedule_archive_url(self, year: int) -> str:
        """Schedule archive: e.g. 2024sked.zip"""
        return f"{self.base_url}/schedule/{year}sked.zip"

    def park_url(self) -> str:
        """Ballpark encyclopedia table."""
        return f"{self.base_url}/parkcode.txt"

    def bio_url(self) -> str:
        """Player and personnel biographical database."""
        return f"{self.base_url}/biofile.txt"

    def ejections_url(self) -> str:
        """Official ejections log."""
        return f"{self.base_url}/ejections.csv"

    def transactions_url(self) -> str:
        """Player transactions file."""
        return f"{self.base_url}/transactions.csv"
