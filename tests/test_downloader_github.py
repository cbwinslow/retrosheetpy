"""Unit tests for GitHub mirror and multi-source Downloader features."""

from pathlib import Path

import pytest

from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.config import DownloaderConfig
from retrosheetpy.extract.downloader import Downloader


def test_downloader_github_gamelog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    config = DownloaderConfig(source="github")
    dl = Downloader(cache=cache, config=config)

    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info\n'

    def mock_fetch(url: str) -> bytes:
        assert "raw.githubusercontent.com" in url
        assert "seasons/2024/GL2024.TXT" in url
        return line.encode("utf-8")

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    gamelog_dir = dl.get_gamelogs(2024)
    assert (gamelog_dir / "gl2024.txt").exists()
    assert (gamelog_dir / "gl2024.txt").read_text() == line


def test_downloader_github_events_with_team_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    config = DownloaderConfig(source="github")
    dl = Downloader(cache=cache, config=config)

    team_manifest = "BOS,A,Boston,Red Sox\nNYN,N,New York,Mets\n"
    bos_events = "id,BOS202404010\nplay,1,0,deve001,00,FB,HR\n"
    nyn_events = "id,NYN202404010\nplay,1,0,alons001,00,FB,HR\n"
    bos_roster = "deve001,Devers,Rafael,L,R,BOS,3B\n"
    nyn_roster = "alons001,Alonso,Pete,R,R,NYN,1B\n"

    def mock_fetch(url: str) -> bytes:
        if "TEAM2024" in url:
            return team_manifest.encode("utf-8")
        if "2024BOS.EVA" in url:
            return bos_events.encode("utf-8")
        if "2024NYN.EVN" in url:
            return nyn_events.encode("utf-8")
        if "BOS2024.ROS" in url:
            return bos_roster.encode("utf-8")
        if "NYN2024.ROS" in url:
            return nyn_roster.encode("utf-8")
        raise FileNotFoundError(f"Not found: {url}")

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    events_dir = dl.get_events(2024)
    assert (events_dir / "TEAM2024").exists()
    assert (events_dir / "2024BOS.EVA").exists()
    assert (events_dir / "2024NYN.EVN").exists()
    assert (events_dir / "BOS2024.ROS").exists()
    assert (events_dir / "NYN2024.ROS").exists()


def test_downloader_auto_fallback_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    config = DownloaderConfig(source="auto")
    dl = Downloader(cache=cache, config=config)

    # Let GitHub URL fail and retrosheet URL succeed
    csv_data = (
        b"PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES\nFEN01,Fenway Park,,Boston,MA,,,,,\n"
    )

    def mock_fetch(url: str) -> bytes:
        if "raw.githubusercontent.com" in url:
            raise RuntimeError("GitHub raw CDN timeout")
        if "parkcode.txt" in url:
            return csv_data
        raise RuntimeError(f"Unexpected URL: {url}")

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    with pytest.warns(UserWarning, match="GitHub ballpark download failed"):
        path = dl.get_parks()

    assert path.exists()
    assert "Fenway" in path.read_text()


def test_downloader_context_manager_and_session_reuse(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    with Downloader(cache=cache) as dl:
        client1 = dl._get_client()
        client2 = dl._get_client()
        assert client1 is client2
        assert not client1.is_closed

    assert client1.is_closed


def test_downloader_github_events_network_error_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    cache = CacheManager(cache_dir=tmp_path / "cache")
    config = DownloaderConfig(source="github")
    dl = Downloader(cache=cache, config=config)

    team_manifest = "BOS,A,Boston,Red Sox\nNYN,N,New York,Mets\n"

    def mock_fetch(url: str) -> bytes:
        if "TEAM2024" in url:
            return team_manifest.encode("utf-8")
        if "2024BOS.EVA" in url:
            # Simulate network timeout mid-download
            raise httpx.ConnectTimeout("Connection timed out to raw CDN")
        return b""

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    with pytest.raises(httpx.ConnectTimeout):
        dl.get_events(2024)

    # Verify partial directory was wiped cleanly
    extracted_dir = cache.get_extracted_dir("events", 2024)
    assert not extracted_dir.exists()


def test_downloader_github_events_tolerates_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import httpx

    cache = CacheManager(cache_dir=tmp_path / "cache")
    config = DownloaderConfig(source="github")
    dl = Downloader(cache=cache, config=config)

    team_manifest = "BOS,A,Boston,Red Sox\nOLD,N,Old Team,Nonexistent\n"
    bos_events = "id,BOS202404010\nplay,1,0,deve001,00,FB,HR\n"

    def mock_fetch(url: str) -> bytes:
        if "TEAM2024" in url:
            return team_manifest.encode("utf-8")
        if "2024BOS.EVA" in url:
            return bos_events.encode("utf-8")
        # 404 for OLD team
        req = httpx.Request("GET", url)
        resp = httpx.Response(status_code=404, request=req)
        raise httpx.HTTPStatusError("Not found", request=req, response=resp)

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    events_dir = dl.get_events(2024)
    assert events_dir.exists()
    assert (events_dir / "2024BOS.EVA").exists()
    assert not (events_dir / "2024OLD.EVN").exists()
