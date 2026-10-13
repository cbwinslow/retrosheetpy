import io
import zipfile
from pathlib import Path

import pyarrow as pa
import pytest

import retrosheetpy as rs
from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.downloader import Downloader


def test_api_gamelogs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path)
    downloader = Downloader(cache=cache)

    buf = io.BytesIO()
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", f"{line}\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_zip)

    table = rs.game_logs(year=2024, downloader=downloader, backend="arrow")
    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table["visiting_team"].to_pylist() == ["LAN"]
    assert table["visiting_score"].to_pylist() == [5]


def test_api_to_duckdb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    buf = io.BytesIO()
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", f"{line}\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_zip)

    db_path = tmp_path / "test.duckdb"
    rs.to_duckdb(
        path=db_path,
        years=[2024],
        datasets=["gamelogs"],
        downloader=downloader,
    )
    assert db_path.exists()


def test_api_download(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", "dummy\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_zip)

    res = rs.download(years=[2024], datasets="gamelogs", downloader=downloader)
    assert "gamelogs" in res
    assert len(res["gamelogs"]) == 1
    assert res["gamelogs"][0].exists()


def test_api_schedules_and_specialty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    # Mock schedules zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "2024schedule.csv",
            "Date,Num,Day,Visitor,League,Game,Home,League,Game,Day/Night,Location,Postponed,Makeup\n"
            "20240320,0,Wednesday,LAN,NL,1,SDN,NL,1,n,SEO01,,\n",
        )
    fake_zip = buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_zip)

    tbl = rs.schedules(year=2024, downloader=downloader, backend="arrow")
    assert tbl.num_rows == 1
    assert tbl["vis_team"].to_pylist() == ["LAN"]

    parquet_file = tmp_path / "schedules.parquet"
    rs.to_parquet(parquet_file, dataset="schedules", years=2024, downloader=downloader)
    assert parquet_file.exists()
