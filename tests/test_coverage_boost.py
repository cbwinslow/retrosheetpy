import datetime
import io
import zipfile
from pathlib import Path

import pytest

import retrosheetpy as rs
from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.downloader import Downloader
from retrosheetpy.schemas.types import parse_bool, parse_date, parse_float, parse_int


def test_types_parsing_full() -> None:
    # parse_date
    assert parse_date(None) is None
    assert parse_date("") is None
    assert parse_date("04/01/2024") == datetime.date(2024, 4, 1)
    assert parse_date("99/99/9999") is None
    assert parse_date("20240401") == datetime.date(2024, 4, 1)
    assert parse_date("2024-04-01") == datetime.date(2024, 4, 1)
    assert parse_date("bad_date") is None
    assert parse_date("20240230") is None  # invalid leap day

    # parse_int
    assert parse_int(None, default=10) == 10
    assert parse_int("", default=5) == 5
    assert parse_int("123") == 123
    assert parse_int("abc", default=0) == 0

    # parse_float
    assert parse_float(None, default=1.5) == 1.5
    assert parse_float("", default=2.5) == 2.5
    assert parse_float("3.14") == 3.14
    assert parse_float("xyz", default=0.0) == 0.0

    # parse_bool
    assert parse_bool(None) is None
    assert parse_bool("T") is True
    assert parse_bool("true") is True
    assert parse_bool("1") is True
    assert parse_bool("Y") is True
    assert parse_bool("YES") is True
    assert parse_bool("F") is False
    assert parse_bool("FALSE") is False
    assert parse_bool("0") is False
    assert parse_bool("N") is False
    assert parse_bool("NO") is False
    assert parse_bool("unknown") is None


def test_downloader_methods_full(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("test.txt", "dummy\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_zip)

    # get_events
    p_events = downloader.get_events(2024)
    assert p_events.is_dir()

    # get_postseason
    p_post = downloader.get_postseason(2024)
    assert p_post.is_dir()

    # get_allstar
    p_as = downloader.get_allstar(2024)
    assert p_as.is_dir()

    # get_schedules
    p_sked = downloader.get_schedules(2024)
    assert p_sked.is_dir()

    # get_parks
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: b"PARKID,NAME\n")
    p_parks = downloader.get_parks()
    assert p_parks.is_file()

    # get_ejections
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: b"GAMEID,DATE\n")
    p_ej = downloader.get_ejections()
    assert p_ej.is_file()

    # get_bio
    bio_buf = io.BytesIO()
    with zipfile.ZipFile(bio_buf, "w") as zf:
        zf.writestr("biofile0.csv", "id,lastname\n")
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: bio_buf.getvalue())
    p_bio = downloader.get_bio()
    assert p_bio.is_file()

    # get_transactions
    tran_buf = io.BytesIO()
    with zipfile.ZipFile(tran_buf, "w") as zf:
        zf.writestr("tran.txt", "20240101,,,,,,\n")
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: tran_buf.getvalue())
    p_tran = downloader.get_transactions()
    assert p_tran.is_file()


def test_api_full_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    # Mock event zip
    event_buf = io.BytesIO()
    with zipfile.ZipFile(event_buf, "w") as zf:
        zf.writestr(
            "2024NYA.EVA",
            "id,NYA202404010\ninfo,date,2024/04/01\ninfo,visteam,TOR\ninfo,hometeam,NYA\nplay,1,0,judge001,00,FB,HR\n",
        )
        zf.writestr("2024NYA.ROS", "judge001,Judge,Aaron,R,R,NYA,OF\n")
    fake_event_zip = event_buf.getvalue()

    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: fake_event_zip)

    # Test rs.events with arrow, polars, pandas
    tbl_events = rs.events(2024, downloader=downloader, backend="arrow")
    assert tbl_events.num_rows > 0
    df_polars = rs.events(2024, downloader=downloader, backend="polars")
    assert len(df_polars) > 0
    df_pandas = rs.events(2024, downloader=downloader, backend="pandas")
    assert len(df_pandas) > 0

    with pytest.raises(ValueError, match="Unknown backend"):
        rs.events(2024, downloader=downloader, backend="invalid")

    # Test rs.postseason & rs.allstar
    tbl_post = rs.postseason(2024, downloader=downloader, backend="arrow")
    assert tbl_post.num_rows > 0
    tbl_as = rs.allstar(2024, downloader=downloader, backend="arrow")
    assert tbl_as.num_rows > 0

    # Test rs.rosters
    tbl_ros = rs.rosters(2024, downloader=downloader, backend="arrow")
    assert tbl_ros.num_rows > 0

    # Test rs.parks
    monkeypatch.setattr(
        downloader,
        "_fetch_bytes",
        lambda url: (
            b"PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES\nBOS07,Fenway Park,,Boston,MA,04/20/1912,,AL,\n"
        ),
    )
    tbl_parks = rs.parks(downloader=downloader, backend="arrow")
    assert tbl_parks.num_rows == 1

    # Test rs.bio
    bio_buf = io.BytesIO()
    with zipfile.ZipFile(bio_buf, "w") as zf:
        zf.writestr(
            "biofile0.csv",
            "id,lastname,usename,fullname,birthdate,birthcity,birthstate,birthcountry,deathdate,deathcity,deathstate,deathcountry,cemetery,cem_city,cem_state,cem_ctry,cem_note,birthname,altname,debut_p,last_p,debut_c,last_c,debut_m,last_m,debut_u,last_u,bats,throws,height,weight,HOF\n"
            "aardd001,Aardsma,David,David Allan Aardsma,19811227,Denver,Colorado,USA,,,,,,,,,,,,20040406,20150823,,,,,,,R,R,77,200,\n",
        )
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: bio_buf.getvalue())
    tbl_bio = rs.bio(downloader=downloader, backend="arrow")
    assert tbl_bio.num_rows == 1

    # Test rs.ejections
    monkeypatch.setattr(
        downloader,
        "_fetch_bytes",
        lambda url: (
            b'GAMEID,DATE,DH,EJECTEE,EJECTEENAME,TEAM,JOB,UMPIRE,UMPIRENAME,INNING,REASON\nCL6188905250,05/25/1889, ,orr-d101,"Dave Orr",CL6,P,goldf101,"Fred Goldsmith",-1,"Call at 3B"\n'
        ),
    )
    tbl_ej = rs.ejections(downloader=downloader, backend="arrow")
    assert tbl_ej.num_rows == 1

    # Test rs.transactions
    tran_buf = io.BytesIO()
    with zipfile.ZipFile(tran_buf, "w") as zf:
        zf.writestr(
            "tran.txt",
            '"20030603",,,"20030629",,1,"aardd001","Da","","","SFN","NL",,1,22,"Drafted"\n',
        )
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: tran_buf.getvalue())
    tbl_tr = rs.transactions(downloader=downloader, backend="arrow")
    assert tbl_tr.num_rows == 1

    # Test to_duckdb with all datasets
    duck_path = tmp_path / "all.duckdb"
    rs.to_duckdb(
        path=duck_path,
        years=2024,
        datasets=[
            "events",
            "postseason",
            "allstar",
            "gamelogs",
            "rosters",
            "parks",
            "schedules",
            "bio",
            "ejections",
            "transactions",
        ],
        downloader=downloader,
    )
    assert duck_path.exists()

    # Test to_parquet with all datasets
    for ds in [
        "events",
        "postseason",
        "allstar",
        "gamelogs",
        "rosters",
        "parks",
        "schedules",
        "bio",
        "ejections",
        "transactions",
    ]:
        out_p = tmp_path / f"{ds}.parquet"
        rs.to_parquet(out_p, dataset=ds, years=2024, downloader=downloader)
        assert out_p.exists()

    with pytest.raises(ValueError, match="Unsupported dataset"):
        rs.to_parquet(tmp_path / "bad.parquet", dataset="invalid", downloader=downloader)

    # Test download all
    res_all = rs.download(years=2024, datasets="all", downloader=downloader)
    assert "events" in res_all
    assert "bio" in res_all


def test_dlt_source_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    downloader = Downloader(cache=cache)

    # Mock files
    bio_buf = io.BytesIO()
    with zipfile.ZipFile(bio_buf, "w") as zf:
        zf.writestr(
            "biofile0.csv",
            "id,lastname,usename,fullname,birthdate,birthcity,birthstate,birthcountry,deathdate,deathcity,deathstate,deathcountry,cemetery,cem_city,cem_state,cem_ctry,cem_note,birthname,altname,debut_p,last_p,debut_c,last_c,debut_m,last_m,debut_u,last_u,bats,throws,height,weight,HOF\n"
            "aardd001,Aardsma,David,David Allan Aardsma,19811227,Denver,Colorado,USA,,,,,,,,,,,,20040406,20150823,,,,,,,R,R,77,200,\n",
        )
    monkeypatch.setattr(downloader, "_fetch_bytes", lambda url: bio_buf.getvalue())

    import importlib.util

    from retrosheetpy.sink.dlt_sink import retrosheet_source

    if importlib.util.find_spec("dlt") is None:
        with pytest.raises(ImportError, match="dlt is not installed"):
            retrosheet_source(2024, datasets=["bio"])
        return

    # If dlt is available, run source resources
    src = retrosheet_source(2024, datasets=["bio"], downloader=downloader)
    assert src is not None


def test_cache_clear(tmp_path: Path) -> None:
    cm = CacheManager(cache_dir=tmp_path)
    (cm.root / "events").mkdir(parents=True)
    (cm.root / "events" / "test.zip").write_text("hello")
    assert (cm.root / "events" / "test.zip").exists()

    cm.clear("events")
    assert not (cm.root / "events").exists()

    (cm.root / "parks").mkdir(parents=True)
    cm.clear()
    assert cm.root.exists()
