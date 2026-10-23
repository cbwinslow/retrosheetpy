"""Tests for transactions deprecation warning and CLI --source flag."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

import retrosheetpy as rs
from retrosheetpy.cli import main
from retrosheetpy.extract.cache import CacheManager
from retrosheetpy.extract.downloader import Downloader


def test_transactions_deprecation_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    dl = Downloader(cache=cache)

    tran_dir = cache.get_extracted_dir("transactions", "master")
    tran_dir.mkdir(parents=True, exist_ok=True)
    (tran_dir / "tran.txt").write_text("18710504,cl1,al1,f,walk001,p,signed\n")

    with pytest.warns(FutureWarning, match="Retrosheet discontinued updating transactions"):
        tbl = rs.transactions(downloader=dl)

    assert tbl.num_rows == 1


def test_transactions_missing_remote_raises_informative_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = CacheManager(cache_dir=tmp_path / "cache")
    dl = Downloader(cache=cache)

    def mock_fetch(url: str) -> bytes:
        raise ConnectionError("Connection dropped by retrosheet.org")

    monkeypatch.setattr(dl, "_fetch_bytes", mock_fetch)

    with pytest.raises(FileNotFoundError, match="handed tracking over to Baseball-Reference"):
        dl.get_transactions()


def test_cli_download_with_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    mock_dl = MagicMock()
    mock_dl.return_value = {"parks": [tmp_path / "parkcode.txt"]}
    monkeypatch.setattr("retrosheetpy.cli.api_download", mock_dl)

    result = runner.invoke(main, ["download", "-s", "parks", "--source", "github"])
    assert result.exit_code == 0
    assert "via github" in result.output
    mock_dl.assert_called_once()
    assert mock_dl.call_args[1]["source"] == "github"


def test_cli_ingest_with_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    mock_to_duckdb = MagicMock()
    monkeypatch.setattr("retrosheetpy.cli.to_duckdb", mock_to_duckdb)

    result = runner.invoke(
        main,
        [
            "ingest",
            "-d",
            "duckdb",
            "-c",
            str(tmp_path / "test.db"),
            "-s",
            "parks",
            "--source",
            "github",
        ],
    )
    assert result.exit_code == 0
    assert "source: github" in result.output
    mock_to_duckdb.assert_called_once()
    assert mock_to_duckdb.call_args[1]["source"] == "github"


def test_dlt_arrow_native_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifies that retrosheet_source yields PyArrow Tables directly into dlt pipeline."""
    import dlt

    cache = CacheManager(cache_dir=tmp_path / "cache")
    dl = Downloader(cache=cache)

    # Populate parks in cache
    parks_file = cache.root / "parks" / "parkcode.txt"
    parks_file.parent.mkdir(parents=True, exist_ok=True)
    parks_file.write_text(
        "PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES\n"
        "FEN01,Fenway Park,,Boston,MA,04/20/1912,,,Historic park\n"
    )

    from retrosheetpy.sink.dlt_sink import retrosheet_source

    source = retrosheet_source(years=2024, datasets=["parks"], downloader=dl)
    pipeline = dlt.pipeline(
        pipeline_name="test_arrow_dlt",
        destination=dlt.destinations.duckdb(str(tmp_path / "dlt_test.duckdb")),
        dataset_name="test_arrow_data",
    )
    info = pipeline.run(source)
    assert info.has_failed_jobs is False
