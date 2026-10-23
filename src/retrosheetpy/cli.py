"""Command-line interface for retrosheetpy."""

from __future__ import annotations

from typing import Literal

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from retrosheetpy.api import (
    allstar,
    bio,
    ejections,
    game_logs,
    parks,
    postseason,
    rosters,
    schedules,
    to_dlt,
    to_duckdb,
    to_parquet,
    transactions,
)
from retrosheetpy.api import download as api_download
from retrosheetpy.extract.cache import CacheManager

console = Console()

DATASET_CHOICES = [
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
    "all",
]

SOURCE_CHOICES = ["github", "retrosheet", "auto"]


def _parse_years_arg(years_str: str) -> list[int]:
    """Parses year strings like '2020-2024' or '2021,2022,2023' into a list of integers."""
    result: set[int] = set()
    for part in years_str.split(","):
        part = part.strip()
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            result.update(range(int(start_s), int(end_s) + 1))
        elif part.isdigit():
            result.add(int(part))
    return sorted(list(result))


@click.group(name="retrosheetpy")
@click.version_option(package_name="retrosheetpy")
def main() -> None:
    """retrosheetpy - Fast, strongly-typed Retrosheet downloader and database ingestor."""
    pass


@main.command()
@click.option(
    "--dataset",
    "-s",
    type=click.Choice(DATASET_CHOICES),
    default="all",
    help="Dataset to download (events, gamelogs, schedules, bio, ejections, transactions, etc.)",
)
@click.option(
    "--years",
    "-y",
    default=None,
    help="Year or range of years (e.g. '2024' or '2020-2024')",
)
@click.option(
    "--source",
    "-S",
    type=click.Choice(SOURCE_CHOICES),
    default="github",
    help="Download source mirror (default: github)",
)
@click.option("--force", is_flag=True, help="Force re-download even if already cached")
def download(
    dataset: str, years: str | None, source: Literal["github", "retrosheet", "auto"], force: bool
) -> None:
    """Download and cache Retrosheet archives locally."""
    year_list = _parse_years_arg(years) if years else None
    display_years = f" ({years})" if years else ""
    console.print(f"[bold blue]Downloading {dataset}{display_years} via {source}...[/bold blue]")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Downloading...", total=None)
        results = api_download(years=year_list, datasets=dataset, source=source, force=force)
        progress.update(task, completed=True)

    for ds, paths in results.items():
        console.print(f"[bold green]✓ {ds}:[/bold green] {len(paths)} asset(s) ready in cache")


@main.command()
@click.option(
    "--dest",
    "-d",
    type=click.Choice(["duckdb", "postgres", "snowflake", "bigquery", "sqlite"]),
    default="duckdb",
    help="Target database destination (default: duckdb)",
)
@click.option(
    "--conn",
    "-c",
    "-f",
    "conn",
    required=True,
    help="Target connection URI or file path (e.g. 'baseball.duckdb' or 'postgresql://...')",
)
@click.option(
    "--dataset",
    "-s",
    default="events,gamelogs,rosters,parks",
    help="Comma-separated datasets to ingest, or 'all'",
)
@click.option(
    "--years",
    "-y",
    default="2024",
    help="Year or range of years (e.g. '2024' or '2020-2024')",
)
@click.option(
    "--source",
    "-S",
    type=click.Choice(SOURCE_CHOICES),
    default="github",
    help="Download source mirror (default: github)",
)
@click.option("--force", is_flag=True, help="Force re-download even if cached")
def ingest(
    dest: str,
    conn: str,
    dataset: str,
    years: str,
    source: Literal["github", "retrosheet", "auto"],
    force: bool,
) -> None:
    """Ingest Retrosheet data into DuckDB or remote SQL warehouses (Postgres, Snowflake, etc.)."""
    year_list = _parse_years_arg(years)
    if dataset.lower() == "all":
        dataset_list = [
            "events",
            "gamelogs",
            "rosters",
            "parks",
            "schedules",
            "bio",
            "ejections",
            "transactions",
        ]
    else:
        dataset_list = [d.strip() for d in dataset.split(",")]

    console.print(
        f"[bold green]Starting ingestion into {dest}:[/bold green] {conn} (source: {source})"
    )
    console.print(
        f"Years: {year_list[0]}–{year_list[-1]} ({len(year_list)} seasons), Datasets: {dataset_list}"
    )

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Ingesting data...", total=None)
        if dest == "duckdb":
            to_duckdb(
                path=conn,
                years=year_list,
                datasets=dataset_list,
                source=source,
                force=force,
            )
        else:
            try:
                to_dlt(
                    destination=dest,
                    years=year_list,
                    datasets=dataset_list,
                    source=source,
                    credentials=conn,
                )
            except ImportError:
                progress.update(task, completed=True)
                console.print(
                    f"\n[bold red]Error: Destination '{dest}' requires dlt.[/bold red]\n"
                    'Install warehouse support with: [bold cyan]pip install "retrosheetpy[dlt]"[/bold cyan]'
                )
                raise SystemExit(1) from None
        progress.update(task, completed=True)

    console.print(f"[bold green]✓ Successfully ingested datasets into {conn}[/bold green]")


@main.command()
@click.option(
    "--dataset",
    "-s",
    type=click.Choice([d for d in DATASET_CHOICES if d != "all"]),
    required=True,
    help="Dataset name to export",
)
@click.option(
    "--years", "-y", default="2024", help="Year or range of years (e.g. '2024' or '2020-2024')"
)
@click.option("--format", "-f", "-fmt", type=click.Choice(["parquet", "csv"]), default="parquet")
@click.option("--output", "-o", required=True, help="Output file path (e.g. gamelogs_2024.parquet)")
@click.option(
    "--source",
    "-S",
    type=click.Choice(SOURCE_CHOICES),
    default="github",
    help="Download source mirror (default: github)",
)
@click.option("--force", is_flag=True, help="Force re-download even if cached")
def export(
    dataset: str,
    years: str,
    format: str,
    output: str,
    source: Literal["github", "retrosheet", "auto"],
    force: bool,
) -> None:
    """Export Retrosheet data to Parquet or CSV format."""
    year_list = _parse_years_arg(years)
    console.print(
        f"[bold blue]Exporting {dataset} ({years}) to {output} ({format}, source: {source})...[/bold blue]"
    )

    if format == "parquet":
        to_parquet(path=output, dataset=dataset, years=year_list, source=source, force=force)
    else:
        from retrosheetpy.sink.file_sink import FileSink

        sink = FileSink()
        d = dataset.lower()
        if d == "parks":
            tbl = parks(backend="arrow", source=source, force=force)
        elif d == "bio":
            tbl = bio(backend="arrow", source=source, force=force)
        elif d == "ejections":
            tbl = ejections(backend="arrow", source=source, force=force)
        elif d == "transactions":
            tbl = transactions(backend="arrow", source=source, force=force)
        elif d == "rosters":
            tbl = rosters(year=year_list, backend="arrow", source=source, force=force)
        elif d == "schedules":
            tbl = schedules(year=year_list, backend="arrow", source=source, force=force)
        elif d in ("gamelogs", "game_logs"):
            tbl = game_logs(year=year_list, backend="arrow", source=source, force=force)
        elif d == "postseason":
            tbl = postseason(year=year_list, backend="arrow", source=source, force=force)
        elif d == "allstar":
            tbl = allstar(year=year_list, backend="arrow", source=source, force=force)
        else:
            from retrosheetpy.api import events

            tbl = events(year=year_list, backend="arrow", source=source, force=force)
        sink.write_csv(output, tbl)

    console.print(f"[bold green]✓ Export complete: {output}[/bold green]")


@main.command()
@click.option(
    "--dataset",
    "-s",
    type=click.Choice([d for d in DATASET_CHOICES if d != "all"]),
    required=True,
    help="Dataset name",
)
@click.option(
    "--dialect",
    type=click.Choice(["postgres", "duckdb", "sqlite", "snowflake", "bigquery"]),
    default="postgres",
    help="Target SQL dialect",
)
def ddl(dataset: str, dialect: str) -> None:
    """Print SQL DDL CREATE TABLE statement for a dataset."""
    from retrosheetpy.api import get_ddl

    sql = get_ddl(dataset, dialect=dialect)
    console.print(sql)


@main.command()
@click.option("--clear", is_flag=True, help="Clear local cache")
def cache(clear: bool) -> None:
    """Inspect or clear the local download cache."""
    cm = CacheManager()
    if clear:
        cm.clear()
        console.print("[bold yellow]✓ Cache cleared successfully.[/bold yellow]")
    else:
        console.print(f"[bold]Cache Directory:[/bold] {cm.root}")
        size = sum(f.stat().st_size for f in cm.root.glob("**/*") if f.is_file())
        console.print(f"[bold]Total Cached Size:[/bold] {size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
