"""Configuration models for Retrosheet extraction and ingestion pipelines."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DownloaderConfig(BaseModel):
    """Configuration options for data fetching and caching."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: Literal["github", "retrosheet", "auto"] = Field(
        default="github",
        description="Authoritative source for downloads ('github', 'retrosheet', or 'auto' fallback).",
    )
    github_repo: str = Field(
        default="chadwickbureau/retrosheet",
        description="GitHub repository holding the Retrosheet dataset mirror.",
    )
    github_branch: str = Field(
        default="master",
        description="Branch to fetch from ('master' for augmented with errata, 'official' for upstream).",
    )
    github_raw_base: str = Field(
        default="https://raw.githubusercontent.com",
        description="Base URL for raw GitHub static file downloads (Fastly CDN).",
    )
    retrosheet_base_url: str = Field(
        default="https://www.retrosheet.org",
        description="Official upstream Retrosheet web server URL.",
    )
    custom_mirror_url: str | None = Field(
        default=None,
        description="Optional custom base URL for secondary mirror.",
    )
    cache_dir: Path | str | None = Field(
        default=None,
        description="Local cache directory override. Defaults to ~/.cache/retrosheetpy.",
    )
    timeout: float = Field(
        default=60.0,
        ge=1.0,
        description="HTTP request timeout in seconds.",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum HTTP retry attempts on transient network errors.",
    )
    github_token: str | None = Field(
        default_factory=lambda: os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"),
        description="Optional GitHub Personal Access Token for authenticated operations.",
    )


class IngestionConfig(BaseModel):
    """Configuration options for database and warehouse ingestion."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    destination: str = Field(
        default="duckdb",
        description="Target destination (duckdb, postgres, snowflake, bigquery, etc.).",
    )
    pipeline_name: str = Field(
        default="retrosheet",
        description="Name of the dlt ingestion pipeline.",
    )
    dataset_name: str = Field(
        default="retrosheet_data",
        description="Target dataset / schema name in destination.",
    )
    write_disposition: Literal["append", "replace", "merge"] = Field(
        default="replace",
        description="Strategy for writing records (replace, append, or merge).",
    )
    years: list[int] = Field(
        default_factory=lambda: [2024],
        description="List of MLB seasons to ingest.",
    )
    datasets: list[str] = Field(
        default_factory=lambda: ["events", "gamelogs", "rosters", "parks"],
        description="Datasets to ingest into destination.",
    )
    schema_contract: Literal["evolve", "freeze", "discard_row", "discard_value"] = Field(
        default="evolve",
        description="Schema evolution contract for dlt pipeline.",
    )
