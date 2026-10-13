"""Protocols and interfaces for Retrosheet parsers."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pyarrow as pa


class DatasetParser(Protocol):
    """Protocol implemented by all dataset parsing modules."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses a single file into a typed PyArrow Table."""
        ...
