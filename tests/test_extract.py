import io
import zipfile
from pathlib import Path

import pytest

from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.downloader import Downloader
from retrosheetpy.extract.manifest import Manifest


def test_manifest_urls() -> None:
    manifest = Manifest()
    assert manifest.event_archive_url(2024) == "https://www.retrosheet.org/events/2024eve.zip"
    assert (
        manifest.event_archive_fallback_url(2024)
        == "https://www.retrosheet.org/events/2024seve.zip"
    )
    assert manifest.gamelog_archive_url(2023) == "https://www.retrosheet.org/gamelogs/gl2023.zip"
    assert manifest.schedule_archive_url(2022) == "https://www.retrosheet.org/schedule/2022sked.zip"
    assert manifest.park_url() == "https://www.retrosheet.org/parkcode.txt"
    assert manifest.bio_url() == "https://www.retrosheet.org/biofile.txt"


def test_cache_manager(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path)
    assert not cache.has_archive("events", 2024)

    # Save a fake zip archive
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("2024NYA.EVA", "id,NYA202404010\nplay,1,0,judge001,00,FB,HR\n")
    zip_bytes = buf.getvalue()

    archive_path = cache.save_archive("events", 2024, zip_bytes)
    assert cache.has_archive("events", 2024)
    assert archive_path.exists()

    # Extract archive
    extracted_dir = cache.extract_archive("events", 2024)
    assert extracted_dir.is_dir()
    event_file = extracted_dir / "2024NYA.EVA"
    assert event_file.exists()
    assert "judge001" in event_file.read_text()


def test_downloader_with_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path)
    downloader = Downloader(cache=cache)

    # Mock the HTTP download
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", "20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,\n")
    fake_zip_bytes = buf.getvalue()

    called = 0

    def mock_fetch(url: str) -> bytes:
        nonlocal called
        called += 1
        return fake_zip_bytes

    monkeypatch.setattr(downloader, "_fetch_bytes", mock_fetch)

    # First fetch should download and cache
    extracted_dir = downloader.get_gamelogs(2024)
    assert called == 1
    assert (extracted_dir / "gl2024.txt").exists()

    # Second fetch should use cache without hitting network
    extracted_dir_2 = downloader.get_gamelogs(2024)
    assert called == 1
    assert extracted_dir_2 == extracted_dir
