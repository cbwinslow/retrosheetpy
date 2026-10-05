"""``Table`` (rows from a Chadwick tool) and ``BoxScores`` (text from cwbox), with their outputs.

A Table does not hold rows. Each time you loop over it, or write it, the tool runs again over the
seasons it covers and the rows stream through, so a whole era never has to fit in memory. Call
``load()`` to keep the rows in a list. Values are plain strings exactly as Chadwick prints them:
no type guessing, and a missing value is an empty string, never zero.
"""

import csv
import io
import json
import os
import re
import sqlite3
import tempfile
from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Literal

from retrosheetpy import runner
from retrosheetpy.errors import ToolError
from retrosheetpy.options import Options
from retrosheetpy.tools import Tool

if TYPE_CHECKING:
    import pandas  # type: ignore[import-untyped]

    from retrosheetpy.cache import Season

Dest = str | os.PathLike[str] | IO[str]
BATCH = 5000
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BY_SUFFIX = {
    ".csv": "csv",
    ".jsonl": "jsonl",
    ".json": "json",
    ".db": "sqlite",
    ".sqlite": "sqlite",
    ".sqlite3": "sqlite",
}


class _Stop(Exception):
    """Raised inside a stream to stop the tool early once we have what we need."""


@contextmanager
def _atomic_text(dest: Dest, encoding: str) -> Iterator[IO[str]]:
    """Open ``dest`` for text writing. A path is written whole or not at all (temp file, rename)."""
    if hasattr(dest, "write"):
        yield dest  # type: ignore[misc]
        return
    path = Path(os.fspath(dest))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".part")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="") as f:
            yield f
        tmp.chmod(0o644)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


class Table:
    """The output of one Chadwick tool over one or more seasons, as streaming rows."""

    def __init__(
        self,
        tool: Tool,
        seasons: "Sequence[Season]",
        opts: Options,
        keep: tuple[str, ...] | None = None,
    ) -> None:
        if not tool.rows:
            raise ValueError(f"{tool.name} is text, not a table")
        if not seasons:
            raise ValueError("no seasons given")
        self.name = tool.name
        self.years = tuple(s.year for s in seasons)
        self._tool, self._seasons, self._opts, self._keep = tool, tuple(seasons), opts, keep
        self._all_columns: tuple[str, ...] | None = None

    def __repr__(self) -> str:
        return f"Table({self.name!r}, years={list(self.years)})"

    # --- columns -------------------------------------------------------------------------------

    @property
    def all_columns(self) -> tuple[str, ...]:
        """Every column the tool prints with the current field options (before ``select``)."""
        if self._all_columns is None:
            season = self._seasons[0]
            # A run that matches no game prints just the header row, so this is quick.
            probe = replace(self._opts, home=(), game="XXX000000000", jobs=1)
            one_file = [season.event_files[0].name] if season.event_files else None
            header: list[str] = []
            with runner.stream(self._tool, season, probe, files=one_file) as src:
                text = io.TextIOWrapper(src, encoding="latin-1", newline="")
                try:
                    header = next(csv.reader(text), [])
                finally:
                    text.detach()
            if not header:
                raise ToolError(f"{self._tool.command} printed no column names")
            self._all_columns = tuple(header)
        return self._all_columns

    @property
    def columns(self) -> tuple[str, ...]:
        """The columns this Table yields, in order."""
        return self._keep if self._keep is not None else self.all_columns

    def select(self, *columns: str) -> "Table":
        """A Table with only these columns, in this order. Unknown names are an error."""
        unknown = [c for c in columns if c not in self.all_columns]
        if unknown:
            raise ValueError(f"{self.name} has no column {', '.join(unknown)}")
        if not columns or len(set(columns)) != len(columns):
            raise ValueError("select needs one or more distinct column names")
        return Table(self._tool, self._seasons, self._opts, tuple(columns))

    # --- rows ----------------------------------------------------------------------------------

    def _records(self) -> Generator[list[str], None, None]:
        """Header-stripped rows of every season, in order, with the column selection applied."""
        header: list[str] | None = None
        picks: list[int] | None = None
        for season in self._seasons:
            opts = self._opts_for(season)
            with runner.stream(self._tool, season, opts) as src:
                text = io.TextIOWrapper(src, encoding="latin-1", newline="")
                try:
                    reader = csv.reader(text)
                    got = next(reader, None)
                    if got is None:
                        raise ToolError(f"{self._tool.command} printed nothing for {season.year}")
                    if header is None:
                        header = got
                        if self._keep is not None:
                            picks = [header.index(c) for c in self._keep]
                    elif got != header:
                        raise ToolError(f"columns differ between seasons ({season.year})")
                    for row in reader:
                        yield [row[i] for i in picks] if picks is not None else row
                finally:
                    text.detach()

    def _opts_for(self, season: "Season") -> Options:
        return self._opts

    def rows(self) -> Iterator[tuple[str, ...]]:
        """The rows as tuples, in ``columns`` order. Fastest way to read."""
        records = self._records()
        try:
            for r in records:
                yield tuple(r)
        finally:
            records.close()  # stop the tool now, whether or not the garbage collector is quick

    def __iter__(self) -> Iterator[dict[str, str]]:
        cols = self.columns
        records = self._records()
        try:
            for r in records:
                yield dict(zip(cols, r, strict=True))
        finally:
            records.close()  # stop the tool now, whether or not the garbage collector is quick

    def load(self) -> list[dict[str, str]]:
        """All rows as a list of dicts (keeps everything in memory)."""
        return list(self)

    to_dicts = load

    # --- outputs -------------------------------------------------------------------------------

    def to_csv(self, dest: Dest, *, header: bool = True, encoding: str = "utf-8") -> None:
        """Write CSV to a path or text file. Chadwick's own quoting is not kept; values are
        quoted only where needed. ``encoding="latin-1"`` writes the bytes Chadwick itself uses."""
        with _atomic_text(dest, encoding) as f:
            w = csv.writer(f, lineterminator="\n")
            if header:
                w.writerow(self.columns)
            w.writerows(self._records())

    def to_jsonl(self, dest: Dest, *, encoding: str = "utf-8") -> None:
        """Write one JSON object per line."""
        with _atomic_text(dest, encoding) as f:
            for row in self:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def to_json(self, dest: Dest, *, encoding: str = "utf-8") -> None:
        """Write one JSON array of objects (streamed, so it does not build the whole list)."""
        with _atomic_text(dest, encoding) as f:
            f.write("[")
            for i, row in enumerate(self):
                f.write(("," if i else "") + "\n" + json.dumps(row, ensure_ascii=False))
            f.write("\n]\n")

    def to_sqlite(
        self,
        path: str | os.PathLike[str],
        table: str | None = None,
        *,
        if_exists: Literal["fail", "replace", "append"] = "fail",
    ) -> int:
        """Load the rows into a SQLite table (every column TEXT) and return the row count.

        All-or-nothing: one transaction. ``if_exists`` says what to do if the table is there.
        """
        name = table or self.name
        if not _IDENT.fullmatch(name):
            raise ValueError(f"{name!r} is not a plain table name")
        cols = ", ".join(f'"{c}" TEXT' for c in self.columns)
        marks = ", ".join("?" for _ in self.columns)
        # name is checked against _IDENT above and column names come from Chadwick, never the user
        insert = f'INSERT INTO "{name}" VALUES ({marks})'  # noqa: S608
        Path(os.fspath(path)).parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None: Python opens no transaction by itself, which would leave CREATE and
        # DROP outside one. We begin one ourselves so the whole load is committed or undone.
        con = sqlite3.connect(path, isolation_level=None)
        count = 0
        try:
            con.execute("BEGIN")
            try:
                exists = con.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
                ).fetchone()
                if exists and if_exists == "fail":
                    raise ValueError(f"table {name!r} already exists in {os.fspath(path)}")
                if exists and if_exists == "replace":
                    con.execute(f'DROP TABLE "{name}"')
                if not exists or if_exists == "replace":
                    con.execute(f'CREATE TABLE "{name}" ({cols})')
                batch: list[list[str]] = []
                for row in self._records():
                    batch.append(row)
                    if len(batch) >= BATCH:
                        con.executemany(insert, batch)
                        count += len(batch)
                        batch = []
                if batch:
                    con.executemany(insert, batch)
                    count += len(batch)
            except BaseException:
                con.execute("ROLLBACK")
                raise
            con.execute("COMMIT")
        finally:
            con.close()
        return count

    def to_pandas(self) -> "pandas.DataFrame":
        """A pandas DataFrame of strings. Needs pandas (``pip install retrosheetpy[pandas]``)."""
        try:
            import pandas
        except ImportError as exc:
            raise ImportError("to_pandas needs pandas: pip install retrosheetpy[pandas]") from exc
        return pandas.DataFrame(list(self.rows()), columns=list(self.columns), dtype=object)

    def write(self, path: str | os.PathLike[str], format: str | None = None, **kw: Any) -> None:
        """Write to ``path`` in ``format`` (csv, jsonl, json, sqlite), or by the file's suffix."""
        suffix = Path(os.fspath(path)).suffix.lower()
        fmt = format or _BY_SUFFIX.get(suffix, "")
        if fmt == "csv":
            self.to_csv(path, **kw)
        elif fmt == "jsonl":
            self.to_jsonl(path, **kw)
        elif fmt == "json":
            self.to_json(path, **kw)
        elif fmt == "sqlite":
            self.to_sqlite(path, **kw)
        else:
            raise ValueError(f"cannot tell the format of {os.fspath(path)!r}; pass format=")


class BoxScores:
    """Box scores for one or more seasons, as text, XML or SportsML."""

    def __init__(self, tool: Tool, seasons: "Sequence[Season]", opts: Options) -> None:
        if not seasons:
            raise ValueError("no seasons given")
        self.years = tuple(s.year for s in seasons)
        self._tool, self._seasons, self._opts = tool, tuple(seasons), opts

    def __repr__(self) -> str:
        return f"BoxScores(years={list(self.years)})"

    def _copy(self, out: IO[bytes], fmt: runner.BoxFormat) -> None:
        if fmt != "text" and len(self._seasons) > 1:
            raise ValueError(f"{fmt} box scores are one document per season; ask for one season")
        for season in self._seasons:
            runner.run(self._tool, season, out, self._opts, box=fmt)

    def _text(self, fmt: runner.BoxFormat) -> str:
        buf = io.BytesIO()
        self._copy(buf, fmt)
        return buf.getvalue().decode("latin-1")

    def text(self) -> str:
        """Plain-text box scores (what cwbox prints)."""
        return self._text("text")

    def xml(self) -> str:
        """Box scores as XML (cwbox -X). One season at a time."""
        return self._text("xml")

    def sportsml(self) -> str:
        """Box scores as SportsML (cwbox -S). One season at a time."""
        return self._text("sportsml")

    def write(
        self,
        path: str | os.PathLike[str],
        format: runner.BoxFormat = "text",
        *,
        encoding: str = "utf-8",
    ) -> None:
        """Write the box scores to ``path`` (all or nothing)."""
        with _atomic_text(path, encoding) as f:
            f.write(self._text(format))
