"""In-memory DataFrame converters for PyArrow Tables."""

from __future__ import annotations

from typing import Any

import pyarrow as pa


def to_arrow(table: pa.Table) -> pa.Table:
    """Returns the PyArrow Table directly."""
    return table


def to_polars(table: pa.Table) -> Any:
    """Converts PyArrow Table to a Polars DataFrame (zero-copy when supported)."""
    try:
        import polars as pl

        return pl.from_arrow(table)
    except ImportError as err:
        raise ImportError(
            "Polars is not installed. Install via 'pip install retrosheetpy[polars]'."
        ) from err


def to_pandas(table: pa.Table) -> Any:
    """Converts PyArrow Table to a pandas DataFrame."""
    try:
        import pandas as pd  # noqa: F401

        return table.to_pandas()
    except ImportError as err:
        raise ImportError(
            "pandas is not installed. Install via 'pip install retrosheetpy[pandas]'."
        ) from err
