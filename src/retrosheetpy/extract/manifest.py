"""Manifest of canonical URLs for Retrosheet and GitHub mirror data assets."""

from __future__ import annotations

from dataclasses import dataclass

from retrosheetpy.extract.config import DownloaderConfig


@dataclass(frozen=True)
class Manifest:
    """Provides authoritative URLs for Retrosheet archives and GitHub mirror reference tables."""

    base_url: str = "https://www.retrosheet.org"
    github_raw_base: str = "https://raw.githubusercontent.com"
    github_repo: str = "chadwickbureau/retrosheet"
    github_branch: str = "master"

    @classmethod
    def from_config(cls, config: DownloaderConfig) -> Manifest:
        """Constructs a Manifest from a DownloaderConfig instance."""
        return cls(
            base_url=config.custom_mirror_url or config.retrosheet_base_url,
            github_raw_base=config.github_raw_base,
            github_repo=config.github_repo,
            github_branch=config.github_branch,
        )

    # --- Official Retrosheet URLs ---

    def event_archive_url(self, year: int) -> str:
        """Play-by-play regular season archive: e.g. 2024eve.zip"""
        return f"{self.base_url}/events/{year}eve.zip"

    def event_archive_fallback_url(self, year: int) -> str:
        """Fallback archive URL: e.g. 2024seve.zip"""
        return f"{self.base_url}/events/{year}seve.zip"

    def postseason_archive_url(self, year: int) -> str:
        """Postseason play-by-play archive: e.g. 2024post.zip"""
        return f"{self.base_url}/events/{year}post.zip"

    def allstar_archive_url(self, year: int) -> str:
        """All-Star Game play-by-play archive: e.g. 2024as.zip"""
        return f"{self.base_url}/events/{year}as.zip"

    def gamelog_archive_url(self, year: int) -> str:
        """Game log archive: e.g. gl2024.zip"""
        return f"{self.base_url}/gamelogs/gl{year}.zip"

    def schedule_archive_url(self, year: int) -> str:
        """Schedule archive: e.g. 2024SKED.zip"""
        return f"{self.base_url}/schedule/{year}SKED.zip"

    def park_url(self) -> str:
        """Ballpark encyclopedia table: parkcode.txt"""
        return f"{self.base_url}/parkcode.txt"

    def bio_url(self) -> str:
        """Master biographical database archive: biofile.zip"""
        return f"{self.base_url}/biofile.zip"

    def ejections_url(self) -> str:
        """Official ejections log: ejections.csv"""
        return f"{self.base_url}/ejections.csv"

    def transactions_url(self) -> str:
        """Player transactions archive: tranDB.zip (frozen November 2021)."""
        return f"{self.base_url}/transactions/tranDB.zip"

    # --- GitHub Raw CDN URLs (Chadwick Bureau Mirror) ---

    @property
    def github_base(self) -> str:
        """Base CDN URL for the configured GitHub repository and branch."""
        return f"{self.github_raw_base}/{self.github_repo}/{self.github_branch}"

    def github_park_url(self) -> str:
        """GitHub raw reference URL for ballparks CSV."""
        return f"{self.github_base}/reference/ballparks.csv"

    def github_bio_url(self) -> str:
        """GitHub raw reference URL for primary biofile0.csv."""
        return f"{self.github_base}/reference/biofile0.csv"

    def github_bio_fallback_url(self) -> str:
        """GitHub raw reference URL for fallback biofile.csv."""
        return f"{self.github_base}/reference/biofile.csv"

    def github_ejections_url(self) -> str:
        """GitHub raw reference URL for ejections.csv."""
        return f"{self.github_base}/reference/ejections.csv"

    def github_gamelog_url(self, year: int) -> str:
        """GitHub raw season game log: seasons/{year}/GL{year}.TXT"""
        return f"{self.github_base}/seasons/{year}/GL{year}.TXT"

    def github_schedule_url(self, year: int) -> str:
        """GitHub raw season schedule: seasons/{year}/{year}schedule.csv"""
        return f"{self.github_base}/seasons/{year}/{year}schedule.csv"

    def github_team_manifest_url(self, year: int) -> str:
        """GitHub raw team manifest listing active teams: seasons/{year}/TEAM{year}"""
        return f"{self.github_base}/seasons/{year}/TEAM{year}"

    def github_season_file_url(self, year: int, filename: str) -> str:
        """GitHub raw file inside a season directory: seasons/{year}/{filename}"""
        return f"{self.github_base}/seasons/{year}/{filename}"
