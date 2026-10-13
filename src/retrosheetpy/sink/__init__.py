"""Sinks module for exporting typed Retrosheet tables to DuckDB, Parquet, CSV, and DataFrames."""

from retrosheetpy.sink.dataframe import to_arrow, to_pandas, to_polars
from retrosheetpy.sink.dlt_sink import retrosheet_source
from retrosheetpy.sink.duckdb_sink import DuckDBSink
from retrosheetpy.sink.file_sink import FileSink

__all__ = [
    "DuckDBSink",
    "FileSink",
    "retrosheet_source",
    "to_arrow",
    "to_pandas",
    "to_polars",
]
