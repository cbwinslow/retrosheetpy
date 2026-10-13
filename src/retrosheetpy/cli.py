"""Command-line interface for retrosheetpy."""

from __future__ import annotations

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from retrosheetpy.api import game_logs, parks, rosters, to_duckdb, to_parquet
from retrosheetpy.extract.cache import CacheManager

console = Console()


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
    type=click.Choice(["events", "gamelogs", "rosters", "parks"]),
    required=True,
    help="Dataset name",
)
@click.option(
    "--dialect",
    type=click.Choice(["postgres", "duckdb", "sqlite"]),
    default="postgres",
    help="Target SQL dialect",
)
def ddl(dataset: str, dialect: str) -> None:
    """Print SQL DDL CREATE TABLE statement for a dataset."""
    from retrosheetpy.api import get_ddl

    sql = get_ddl(dataset, dialect=dialect)
    console.print(sql)


@main.command()
@click.option(
    "--years", "-y", required=True, help="Year or range of years (e.g. '2024' or '2020-2024')"
)
@click.option(
    "--dest",
    "-d",
    type=click.Choice(["duckdb"]),
    default="duckdb",
    help="Target destination database",
)
@click.option(
    "--file",
    "-f",
    "output_file",
    required=True,
    help="Output database file path (e.g. retrosheet.duckdb)",
)
@click.option(
    "--datasets",
    "-s",
    default="events,gamelogs,rosters,parks",
    help="Comma-separated datasets to ingest",
)
@click.option("--force", is_flag=True, help="Force re-download even if cached")
def ingest(years: str, dest: str, output_file: str, datasets: str, force: bool) -> None:
    """Ingest Retrosheet data into an embedded database (DuckDB)."""
    year_list = _parse_years_arg(years)
    dataset_list = [d.strip() for d in datasets.split(",")]

    console.print(f"[bold green]Starting ingestion into {dest}:[/bold green] {output_file}")
    console.print(
        f"Years: {year_list[0]}–{year_list[-1]} ({len(year_list)} seasons), Datasets: {dataset_list}"
    )

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True
    ) as progress:
        task = progress.add_task("Ingesting data...", total=None)
        to_duckdb(
            path=output_file,
            years=year_list,
            datasets=dataset_list,
            force=force,
        )
        progress.update(task, completed=True)

    console.print(f"[bold green]✓ Successfully ingested datasets into {output_file}[/bold green]")


@main.command()
@click.option(
    "--dataset", "-s", type=click.Choice(["events", "gamelogs", "rosters", "parks"]), required=True
)
@click.option(
    "--years", "-y", default="2024", help="Year or range of years (e.g. '2024' or '2020-2024')"
)
@click.option("--format", "-fmt", type=click.Choice(["parquet", "csv"]), default="parquet")
@click.option("--output", "-o", required=True, help="Output file path (e.g. gamelogs_2024.parquet)")
@click.option("--force", is_flag=True, help="Force re-download even if cached")
def export(dataset: str, years: str, format: str, output: str, force: bool) -> None:
    """Export Retrosheet data to Parquet or CSV format."""
    year_list = _parse_years_arg(years)
    console.print(f"[bold blue]Exporting {dataset} ({years}) to {output} ({format})...[/bold blue]")

    if format == "parquet":
        to_parquet(path=output, dataset=dataset, years=year_list, force=force)
    else:
        # CSV export
        from retrosheetpy.sink.file_sink import FileSink

        sink = FileSink()
        if dataset == "parks":
            tbl = parks(backend="arrow", force=force)
        elif dataset == "rosters":
            tbl = rosters(year=year_list, backend="arrow", force=force)
        elif dataset in ("gamelogs", "game_logs"):
            tbl = game_logs(year=year_list, backend="arrow", force=force)
        else:
            from retrosheetpy.api import events

            tbl = events(year=year_list, backend="arrow", force=force)
        sink.write_csv(output, tbl)

    console.print(f"[bold green]✓ Export complete: {output}[/bold green]")


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
