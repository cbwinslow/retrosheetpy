"""File-based destination sinks for exporting to Parquet and CSV."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq


class FileSink:
    """Exports PyArrow Tables to Parquet or CSV files."""

    def write_parquet(
        self,
        path: Path | str,
        table: pa.Table,
        compression: str = "snappy",
    ) -> Path:
        """Writes an Arrow Table to a compressed Parquet file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, p, compression=compression)
        return p

    def write_csv(
        self,
        path: Path | str,
        table: pa.Table,
    ) -> Path:
        """Writes an Arrow Table to a CSV file."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        pcsv.write_csv(table, p)
        return p
