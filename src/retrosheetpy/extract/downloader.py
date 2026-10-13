"""HTTP Downloader for Retrosheet assets with caching and resilience."""

from __future__ import annotations

from pathlib import Path

import httpx

from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.manifest import Manifest


class Downloader:
    """Coordinates fetching files from retrosheet.org, verifying, and caching them."""

    def __init__(
        self,
        cache: CacheManager | None = None,
        manifest: Manifest | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.cache = cache or CacheManager()
        self.manifest = manifest or Manifest()
        self.timeout = timeout

    def _fetch_bytes(self, url: str) -> bytes:
        """Internal HTTP GET fetcher with streaming/timeout handling."""
        with httpx.Client(follow_redirects=True, timeout=self.timeout) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content

    def get_events(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts regular season event files for a given year."""
        if not force and self.cache.is_extracted("events", year):
            return self.cache.get_extracted_dir("events", year)

        url = self.manifest.event_archive_url(year)
        try:
            content = self._fetch_bytes(url)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                fallback_url = self.manifest.event_archive_fallback_url(year)
                content = self._fetch_bytes(fallback_url)
            else:
                raise
        self.cache.save_archive("events", year, content)
        return self.cache.extract_archive("events", year)

    def get_postseason(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts postseason event files for a given year."""
        if not force and self.cache.is_extracted("postseason", year):
            return self.cache.get_extracted_dir("postseason", year)

        url = self.manifest.postseason_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("postseason", year, content)
        return self.cache.extract_archive("postseason", year)

    def get_allstar(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts All-Star Game event files for a given year."""
        if not force and self.cache.is_extracted("allstar", year):
            return self.cache.get_extracted_dir("allstar", year)

        url = self.manifest.allstar_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("allstar", year, content)
        return self.cache.extract_archive("allstar", year)

    def get_gamelogs(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts game log files for a given year."""
        if not force and self.cache.is_extracted("gamelogs", year):
            return self.cache.get_extracted_dir("gamelogs", year)

        url = self.manifest.gamelog_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("gamelogs", year, content)
        return self.cache.extract_archive("gamelogs", year)

    def get_schedules(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts schedule files for a given year."""
        if not force and self.cache.is_extracted("schedules", year):
            return self.cache.get_extracted_dir("schedules", year)

        url = self.manifest.schedule_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("schedules", year, content)
        return self.cache.extract_archive("schedules", year)

    def get_parks(self, force: bool = False) -> Path:
        """Downloads ballpark encyclopedia text file."""
        target = self.cache.root / "parks" / "parkcode.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not force and target.is_file() and target.stat().st_size > 0:
            return target

        url = self.manifest.park_url()
        content = self._fetch_bytes(url)
        target.write_bytes(content)
        return target

    def get_bio(self, force: bool = False) -> Path:
        """Downloads and extracts master biographical archive, returning path to biofile0.csv."""
        target_dir = self.cache.get_extracted_dir("bio", "master")
        target_csv = target_dir / "biofile0.csv"
        if not force and target_csv.is_file() and target_csv.stat().st_size > 0:
            return target_csv

        url = self.manifest.bio_url()
        content = self._fetch_bytes(url)
        self.cache.save_archive("bio", "master", content)
        extracted = self.cache.extract_archive("bio", "master")
        csv_file = extracted / "biofile0.csv"
        if not csv_file.is_file():
            csv_file = extracted / "biofile.csv"
        if not csv_file.is_file():
            raise FileNotFoundError(f"Biofile CSV not found in extracted archive at {extracted}")
        return csv_file

    def get_ejections(self, force: bool = False) -> Path:
        """Downloads official ejections CSV file atomically."""
        target = self.cache.root / "ejections" / "ejections.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not force and target.is_file() and target.stat().st_size > 0:
            return target

        url = self.manifest.ejections_url()
        content = self._fetch_bytes(url)
        tmp_target = target.with_suffix(".csv.tmp")
        tmp_target.write_bytes(content)
        tmp_target.replace(target)
        return target

    def get_transactions(self, force: bool = False) -> Path:
        """Downloads and extracts transactions database, returning path to tran.txt."""
        target_dir = self.cache.get_extracted_dir("transactions", "master")
        target_txt = target_dir / "tran.txt"
        if not force and target_txt.is_file() and target_txt.stat().st_size > 0:
            return target_txt

        url = self.manifest.transactions_url()
        content = self._fetch_bytes(url)
        self.cache.save_archive("transactions", "master", content)
        extracted = self.cache.extract_archive("transactions", "master")
        return extracted / "tran.txt"
