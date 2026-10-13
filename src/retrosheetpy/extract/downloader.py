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
        """Downloads player biographical database text file."""
        target = self.cache.root / "bio" / "biofile.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not force and target.is_file() and target.stat().st_size > 0:
            return target

        url = self.manifest.bio_url()
        content = self._fetch_bytes(url)
        target.write_bytes(content)
        return target
