"""HTTP Downloader for Retrosheet and GitHub mirror assets with caching and resilience."""

from __future__ import annotations

import tempfile
import warnings
from pathlib import Path
from typing import Literal

import httpx

from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.config import DownloaderConfig
from retrosheetpy.extract.manifest import Manifest


def _is_zip(data: bytes) -> bool:
    """Checks if a byte buffer starts with standard ZIP header magic bytes."""
    return len(data) >= 4 and data[:4] == b"PK\x03\x04"


class Downloader:
    """Coordinates fetching files from GitHub raw CDN (Chadwick Bureau mirror) or retrosheet.org."""

    def __init__(
        self,
        cache: CacheManager | None = None,
        manifest: Manifest | None = None,
        config: DownloaderConfig | None = None,
        source: Literal["github", "retrosheet", "auto"] | None = None,
        timeout: float | None = None,
    ) -> None:
        self.config = config or DownloaderConfig()
        if source is not None:
            self.config = self.config.model_copy(update={"source": source})
        if timeout is not None:
            self.config = self.config.model_copy(update={"timeout": timeout})

        self.cache = cache or CacheManager(cache_dir=self.config.cache_dir)
        self.manifest = manifest or Manifest.from_config(self.config)
        self.timeout = self.config.timeout
        self.source: Literal["github", "retrosheet", "auto"] = self.config.source

    def _fetch_bytes(self, url: str) -> bytes:
        """Internal HTTP GET fetcher with timeout and retry handling."""
        headers = {"User-Agent": "retrosheetpy/2.1 (https://github.com/cbwinslow/retrosheetpy)"}
        if self.config.github_token and "github" in url:
            headers["Authorization"] = f"Bearer {self.config.github_token}"

        last_exc: Exception | None = None
        for attempt in range(max(1, self.config.max_retries)):
            try:
                with httpx.Client(
                    follow_redirects=True, timeout=self.timeout, headers=headers
                ) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    return resp.content
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt + 1 == self.config.max_retries:
                    raise
            except httpx.HTTPStatusError:
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError(f"Failed to fetch content from {url}")

    def get_events(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts regular season event files for a given year."""
        extracted_dir = self.cache.get_extracted_dir("events", year)
        if not force and self.cache.is_extracted("events", year):
            existing_events = list(extracted_dir.glob("*.EVA")) + list(extracted_dir.glob("*.EVN"))
            if existing_events:
                return extracted_dir

        if self.source in ("github", "auto"):
            try:
                return self._get_events_github(year, extracted_dir)
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub mirror download for {year} events failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        return self._get_events_retrosheet(year)

    def _get_events_github(self, year: int, extracted_dir: Path) -> Path:
        """Downloads season events and rosters from GitHub raw CDN via TEAM{year} manifest."""
        manifest_bytes = self._fetch_bytes(self.manifest.github_team_manifest_url(year))
        if _is_zip(manifest_bytes):
            self.cache.save_archive("events", year, manifest_bytes)
            return self.cache.extract_archive("events", year)

        extracted_dir.mkdir(parents=True, exist_ok=True)
        team_manifest_file = extracted_dir / f"TEAM{year}"
        team_manifest_file.write_bytes(manifest_bytes)

        lines = manifest_bytes.decode("utf-8", errors="replace").splitlines()
        for line in lines:
            line_str = line.strip()
            if not line_str or "," not in line_str:
                continue
            parts = line_str.split(",")
            team_id = parts[0].strip()
            league = parts[1].strip().upper() if len(parts) > 1 else "A"

            event_ext = ".EVA" if league == "A" else ".EVN"
            event_filename = f"{year}{team_id}{event_ext}"
            roster_filename = f"{team_id}{year}.ROS"

            # Fetch team event file
            try:
                event_bytes = self._fetch_bytes(
                    self.manifest.github_season_file_url(year, event_filename)
                )
                (extracted_dir / event_filename).write_bytes(event_bytes)
            except Exception:
                pass

            # Fetch team roster file
            try:
                roster_bytes = self._fetch_bytes(
                    self.manifest.github_season_file_url(year, roster_filename)
                )
                (extracted_dir / roster_filename).write_bytes(roster_bytes)
            except Exception:
                pass

        # Try to fetch season schedule and league event files if available
        for extra in [f"{year}schedule.csv", f"{year}.EBA", f"{year}.EBE", f"{year}.EBN"]:
            try:
                content = self._fetch_bytes(self.manifest.github_season_file_url(year, extra))
                (extracted_dir / extra).write_bytes(content)
            except Exception:
                pass

        return extracted_dir

    def _get_events_retrosheet(self, year: int) -> Path:
        """Downloads and extracts events from retrosheet.org zip archive."""
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
        extracted_dir = self.cache.get_extracted_dir("postseason", year)
        if not force and self.cache.is_extracted("postseason", year):
            existing = list(extracted_dir.glob("*.EVE"))
            if existing:
                return extracted_dir

        if self.source in ("github", "auto"):
            try:
                postseason_rounds = [
                    "WS",
                    "ALCS",
                    "NLCS",
                    "ALD1",
                    "ALD2",
                    "NLD1",
                    "NLD2",
                    "ALW1",
                    "ALW2",
                    "NLW1",
                    "NLW2",
                    "ALDS",
                    "NLDS",
                ]
                found = 0
                for rnd in postseason_rounds:
                    fname = f"{year}{rnd}.EVE"
                    try:
                        content = self._fetch_bytes(
                            self.manifest.github_season_file_url(year, fname)
                        )
                        if _is_zip(content):
                            self.cache.save_archive("postseason", year, content)
                            return self.cache.extract_archive("postseason", year)
                        extracted_dir.mkdir(parents=True, exist_ok=True)
                        (extracted_dir / fname).write_bytes(content)
                        found += 1
                    except Exception:
                        pass
                if found > 0:
                    return extracted_dir
                if self.source == "github":
                    raise FileNotFoundError(
                        f"No postseason event files found on GitHub mirror for {year}"
                    )
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub postseason download for {year} failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        url = self.manifest.postseason_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("postseason", year, content)
        return self.cache.extract_archive("postseason", year)

    def get_allstar(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts All-Star Game event files for a given year."""
        extracted_dir = self.cache.get_extracted_dir("allstar", year)
        if not force and self.cache.is_extracted("allstar", year):
            existing = list(extracted_dir.glob("*.EVE"))
            if existing:
                return extracted_dir

        if self.source in ("github", "auto"):
            try:
                fname = f"{year}AS.EVE"
                content = self._fetch_bytes(self.manifest.github_season_file_url(year, fname))
                if _is_zip(content):
                    self.cache.save_archive("allstar", year, content)
                    return self.cache.extract_archive("allstar", year)
                extracted_dir.mkdir(parents=True, exist_ok=True)
                (extracted_dir / fname).write_bytes(content)
                return extracted_dir
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub All-Star download for {year} failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        url = self.manifest.allstar_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("allstar", year, content)
        return self.cache.extract_archive("allstar", year)

    def get_gamelogs(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts game log files for a given year."""
        extracted_dir = self.cache.get_extracted_dir("gamelogs", year)
        if not force and self.cache.is_extracted("gamelogs", year):
            existing = list(extracted_dir.glob("*.[tT][xX][tT]"))
            if existing:
                return extracted_dir

        if self.source in ("github", "auto"):
            try:
                url = self.manifest.github_gamelog_url(year)
                content = self._fetch_bytes(url)
                if _is_zip(content):
                    self.cache.save_archive("gamelogs", year, content)
                    return self.cache.extract_archive("gamelogs", year)
                extracted_dir.mkdir(parents=True, exist_ok=True)
                (extracted_dir / f"gl{year}.txt").write_bytes(content)
                return extracted_dir
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub gamelog download for {year} failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        url = self.manifest.gamelog_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("gamelogs", year, content)
        return self.cache.extract_archive("gamelogs", year)

    def get_schedules(self, year: int, force: bool = False) -> Path:
        """Downloads and extracts schedule files for a given year."""
        extracted_dir = self.cache.get_extracted_dir("schedules", year)
        if not force and self.cache.is_extracted("schedules", year):
            existing = list(extracted_dir.glob("*.csv")) + list(
                extracted_dir.glob("*.[tT][xX][tT]")
            )
            if existing:
                return extracted_dir

        if self.source in ("github", "auto"):
            try:
                url = self.manifest.github_schedule_url(year)
                content = self._fetch_bytes(url)
                if _is_zip(content):
                    self.cache.save_archive("schedules", year, content)
                    return self.cache.extract_archive("schedules", year)
                extracted_dir.mkdir(parents=True, exist_ok=True)
                (extracted_dir / f"{year}schedule.csv").write_bytes(content)
                return extracted_dir
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub schedule download for {year} failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        url = self.manifest.schedule_archive_url(year)
        content = self._fetch_bytes(url)
        self.cache.save_archive("schedules", year, content)
        return self.cache.extract_archive("schedules", year)

    def get_parks(self, force: bool = False) -> Path:
        """Downloads ballpark encyclopedia text or CSV file."""
        target = self.cache.root / "parks" / "parkcode.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not force and target.is_file() and target.stat().st_size > 0:
            return target

        if self.source in ("github", "auto"):
            try:
                url = self.manifest.github_park_url()
                content = self._fetch_bytes(url)
                if _is_zip(content):
                    self.cache.save_archive("parks", "master", content)
                    extracted = self.cache.extract_archive("parks", "master")
                    park_file = extracted / "parkcode.txt"
                    if park_file.exists():
                        target.write_bytes(park_file.read_bytes())
                        return target
                target.write_bytes(content)
                return target
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub ballpark download failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

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

        if self.source in ("github", "auto"):
            try:
                try:
                    content = self._fetch_bytes(self.manifest.github_bio_url())
                except Exception:
                    content = self._fetch_bytes(self.manifest.github_bio_fallback_url())
                if _is_zip(content):
                    self.cache.save_archive("bio", "master", content)
                    extracted = self.cache.extract_archive("bio", "master")
                    csv_file = extracted / "biofile0.csv"
                    if not csv_file.is_file():
                        csv_file = extracted / "biofile.csv"
                    return csv_file
                target_dir.mkdir(parents=True, exist_ok=True)
                target_csv.write_bytes(content)
                return target_csv
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub biofile download failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

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

        if self.source in ("github", "auto"):
            try:
                url = self.manifest.github_ejections_url()
                content = self._fetch_bytes(url)
                if _is_zip(content):
                    self.cache.save_archive("ejections", "master", content)
                    extracted = self.cache.extract_archive("ejections", "master")
                    extracted_csv = extracted / "ejections.csv"
                    if extracted_csv.is_file():
                        self._atomic_write(target, extracted_csv.read_bytes())
                        return target
                self._atomic_write(target, content)
                return target
            except Exception as e:
                if self.source == "github":
                    raise
                warnings.warn(
                    f"GitHub ejections download failed ({e}); falling back to retrosheet.org.",
                    UserWarning,
                    stacklevel=2,
                )

        url = self.manifest.ejections_url()
        content = self._fetch_bytes(url)
        self._atomic_write(target, content)
        return target

    def _atomic_write(self, target: Path, content: bytes) -> None:
        """Atomically writes bytes to a file via a temporary file."""
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False, suffix=".tmp") as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        try:
            tmp_path.replace(target)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

    def get_transactions(self, force: bool = False) -> Path:
        """Downloads and extracts transactions database, returning path to tran.txt.

        Note: Upstream Retrosheet discontinued updating transactions on November 26, 2021,
        transitioning transaction tracking to Baseball-Reference.
        """
        warnings.warn(
            "Retrosheet discontinued updating transactions on November 26, 2021. "
            "Data in this table is historical and frozen as of 2021.",
            FutureWarning,
            stacklevel=2,
        )

        target_dir = self.cache.get_extracted_dir("transactions", "master")
        target_txt = target_dir / "tran.txt"
        if not force and target_txt.is_file() and target_txt.stat().st_size > 0:
            return target_txt

        # Fallback check for user-supplied local transaction file
        local_override = self.cache.root / "transactions" / "tran.txt"
        if local_override.is_file() and local_override.stat().st_size > 0:
            return local_override

        try:
            url = self.manifest.transactions_url()
            content = self._fetch_bytes(url)
            self.cache.save_archive("transactions", "master", content)
            extracted = self.cache.extract_archive("transactions", "master")
            return extracted / "tran.txt"
        except Exception as err:
            raise FileNotFoundError(
                "Could not download tranDB.zip from retrosheet.org. Note that Retrosheet froze "
                "the transactions database in November 2021 and handed tracking over to Baseball-Reference. "
                f"You can provide a local tran.txt at '{target_txt}' to use cached historical data."
            ) from err
