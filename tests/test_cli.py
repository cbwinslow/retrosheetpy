import io
import zipfile
from pathlib import Path

from click.testing import CliRunner

from retrosheetpy.cli import main
from retrosheetpy.extract.downloader import Downloader


def test_cli_version() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "retrosheetpy" in result.output


def test_cli_ddl() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["ddl", "-s", "gamelogs", "--dialect", "postgres"])
    assert result.exit_code == 0
    assert "CREATE TABLE IF NOT EXISTS game_logs" in result.output
    assert "visiting_team VARCHAR" in result.output

    result_bq = runner.invoke(main, ["ddl", "-s", "schedules", "--dialect", "bigquery"])
    assert result_bq.exit_code == 0
    assert "vis_game_num INT64" in result_bq.output


def test_cli_cache_info(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RETROSHEETPY_CACHE_DIR", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(main, ["cache"])
    assert result.exit_code == 0
    assert "Cache Directory:" in result.output


def test_cli_export(tmp_path: Path, monkeypatch) -> None:
    buf = io.BytesIO()
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", f"{line}\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(Downloader, "_fetch_bytes", lambda self, url: fake_zip)

    out_file = tmp_path / "gamelogs_2024.parquet"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "export",
            "-s",
            "gamelogs",
            "-y",
            "2024",
            "-o",
            str(out_file),
            "-f",
            "parquet",
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()


def test_cli_download(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RETROSHEETPY_CACHE_DIR", str(tmp_path))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", "dummy\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(Downloader, "_fetch_bytes", lambda self, url: fake_zip)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["download", "-s", "gamelogs", "-y", "2024"],
    )
    assert result.exit_code == 0
    assert "gamelogs" in result.output


def test_cli_ingest_duckdb(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("RETROSHEETPY_CACHE_DIR", str(tmp_path))
    buf = io.BytesIO()
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("gl2024.txt", f"{line}\n")
    fake_zip = buf.getvalue()

    monkeypatch.setattr(Downloader, "_fetch_bytes", lambda self, url: fake_zip)

    db_path = tmp_path / "cli_test.duckdb"
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["ingest", "-d", "duckdb", "-c", str(db_path), "-s", "gamelogs", "-y", "2024"],
    )
    assert result.exit_code == 0
    assert db_path.exists()

    import duckdb

    with duckdb.connect(str(db_path)) as con:
        count = con.execute("SELECT count(*) FROM game_logs").fetchone()[0]
        assert count == 1

    # Verify idempotency on repeated run
    result_repeat = runner.invoke(
        main,
        ["ingest", "-d", "duckdb", "-c", str(db_path), "-s", "gamelogs", "-y", "2024"],
    )
    assert result_repeat.exit_code == 0
    with duckdb.connect(str(db_path)) as con:
        count = con.execute("SELECT count(*) FROM game_logs").fetchone()[0]
        assert count == 1
