"""Unit tests for configuration models."""

import pytest
from pydantic import ValidationError

from retrosheetpy.extract.config import DownloaderConfig, IngestionConfig


def test_downloader_config_defaults() -> None:
    cfg = DownloaderConfig()
    assert cfg.source == "github"
    assert cfg.github_repo == "chadwickbureau/retrosheet"
    assert cfg.github_branch == "master"
    assert cfg.github_raw_base == "https://raw.githubusercontent.com"
    assert cfg.timeout == 60.0
    assert cfg.max_retries == 3


def test_downloader_config_custom() -> None:
    cfg = DownloaderConfig(
        source="retrosheet",
        timeout=120.0,
        max_retries=5,
        custom_mirror_url="https://mirror.example.com",
    )
    assert cfg.source == "retrosheet"
    assert cfg.timeout == 120.0
    assert cfg.max_retries == 5
    assert cfg.custom_mirror_url == "https://mirror.example.com"


def test_downloader_config_validation() -> None:
    with pytest.raises(ValidationError):
        DownloaderConfig(source="invalid_source")  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        DownloaderConfig(timeout=0.5)

    with pytest.raises(ValidationError):
        DownloaderConfig(extra_param="not_allowed")  # type: ignore[call-arg]


def test_ingestion_config_defaults() -> None:
    cfg = IngestionConfig()
    assert cfg.destination == "duckdb"
    assert cfg.pipeline_name == "retrosheet"
    assert cfg.write_disposition == "replace"
    assert cfg.years == [2024]
    assert "events" in cfg.datasets
    assert cfg.schema_contract == "evolve"


def test_ingestion_config_custom() -> None:
    cfg = IngestionConfig(
        destination="postgres",
        years=[2022, 2023, 2024],
        write_disposition="append",
        schema_contract="freeze",
    )
    assert cfg.destination == "postgres"
    assert cfg.years == [2022, 2023, 2024]
    assert cfg.write_disposition == "append"
    assert cfg.schema_contract == "freeze"
