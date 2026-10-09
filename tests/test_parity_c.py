"""retrosheetpy's output must equal the real Chadwick C tools', byte for byte.

Runs only when ``CHADWICK_BIN`` names the folder holding the real ``cwevent``, ``cwgame`` ...
(CI builds them; ``CHADWICK_BIN=~/.local/bin`` locally).
"""

import io
import os
import subprocess
from pathlib import Path

import fake_season as fake
import pytest

import retrosheetpy as rs
from retrosheetpy import runner
from retrosheetpy.options import Options, Opts
from retrosheetpy.tools import TOOLS, Tool

BIN = Path(os.environ.get("CHADWICK_BIN", "/nonexistent"))
pytestmark = pytest.mark.skipif(
    not (BIN / "cwevent").exists(), reason="set CHADWICK_BIN to the real Chadwick tools"
)


def c_command(tool: Tool, year: int, o: Options, files: list[str]) -> list[str]:
    cmd = [str(BIN / tool.command), "-q", "-y", str(year)]
    for flag, value in (("-i", o.game), ("-s", o.start), ("-e", o.end)):
        if value:
            cmd += [flag, value]
    if tool.rows:
        chose = o.fields is not None or o.extended is not None
        cmd += [
            "-n",
            "-f",
            o.fields if o.fields is not None else ("" if chose else f"0-{tool.max_field}"),
        ]
        if tool.max_ext_field is not None:
            cmd += [
                "-x",
                o.extended
                if o.extended is not None
                else ("" if chose else f"0-{tool.max_ext_field}"),
            ]
    return cmd + files


CASES: list[tuple[str, Opts]] = [
    *[(name, {}) for name in TOOLS],
    ("events", {"fields": "0-5"}),
    ("events", {"fields": [0, 29], "extended": "0-3"}),
    ("events", {"extended": [5]}),
    ("events", {"home": "BBB"}),
    ("events", {"home": ["BBB", "AAA"]}),
    ("events", {"game": "AAA201004060"}),
    ("events", {"start": "0406", "end": "0406"}),
    ("games", {"start": "0406"}),
    ("games", {"end": "0405"}),
    ("games", {"fields": "0-3", "extended": "0-2"}),
    ("games", {"extended": "0-96"}),
    ("daily", {"fields": "0-3"}),
    ("daily", {"game": "BBB201004070"}),
    ("subs", {"fields": "0-5"}),
    ("comments", {"home": "AAA"}),
    ("boxscores", {"game": "AAA201004050"}),
    ("boxscores", {"start": "0406", "end": "0407"}),
]


@pytest.mark.parametrize(("name", "opts"), CASES, ids=[f"{n}-{sorted(o)}" for n, o in CASES])
def test_equals_the_c_tool(tmp_path: Path, name: str, opts: Opts) -> None:
    tool = TOOLS[name]
    season = rs.season(2010, cache=tmp_path, fetch=fake.fetch)
    options = Options.build(tool, opts)
    mine = io.BytesIO()
    runner.run(tool, season, mine, options)
    theirs = subprocess.run(  # noqa: S603
        c_command(tool, 2010, options, runner.files_for(season, options)),
        cwd=season.folder,
        capture_output=True,
        check=True,
    )
    assert mine.getvalue() == theirs.stdout
    assert mine.getvalue()


def test_box_xml_equals_the_c_tool(tmp_path: Path) -> None:
    """Plain XML equals C on this clean game. Not asserted for real seasons or SportsML, because
    the C itself is not reliable there: cwbox -X prints a ``pb`` attribute from uninitialised
    memory, and cwbox -S crashes on real data (exit 139) and prints "(null)" ids. chadwickpy's
    ``tools/cwboxxml.py`` documents both; see docs/ for what we promise."""
    tool = TOOLS["boxscores"]
    season = rs.season(2010, cache=tmp_path, fetch=fake.fetch)
    mine = io.BytesIO()
    runner.run(tool, season, mine, Options(), box="xml")
    theirs = subprocess.run(  # noqa: S603
        [str(BIN / "cwbox"), "-q", "-y", "2010", "-X", *(p.name for p in season.event_files)],
        cwd=season.folder,
        capture_output=True,
        check=True,
    )
    assert mine.getvalue() == theirs.stdout and mine.getvalue()


def test_rows_equal_the_c_output_parsed(tmp_path: Path) -> None:
    """The Table's rows are the C tool's CSV, read back (not just the raw bytes)."""
    import csv

    season = rs.season(2010, cache=tmp_path, fetch=fake.fetch)
    tool = TOOLS["games"]
    theirs = subprocess.run(  # noqa: S603
        c_command(tool, 2010, Options(), [p.name for p in season.event_files]),
        cwd=season.folder,
        capture_output=True,
        check=True,
    ).stdout.decode("latin-1")
    parsed = list(csv.DictReader(io.StringIO(theirs, newline="")))
    assert rs.games(2010, cache=tmp_path, fetch=fake.fetch).load() == parsed


KINDS = [
    ("postseason", 2010),
    ("allstar", 2010),
    ("negro", 1912),
    ("negro_box", 1912),
    ("box", 1901),
]


@pytest.mark.parametrize(("kind", "year"), KINDS)
@pytest.mark.parametrize("name", list(TOOLS))
def test_every_kind_equals_the_c_tool(tmp_path: Path, kind: str, year: int, name: str) -> None:
    """Postseason, All-Star, Negro Leagues and box-score-only files: same bytes as the C tools."""
    tool = TOOLS[name]
    season = rs.season(year, kind=kind, cache=tmp_path, fetch=fake.fetch_any)
    options = Options()
    mine = io.BytesIO()
    runner.run(tool, season, mine, options)
    theirs = subprocess.run(  # noqa: S603
        c_command(tool, year, options, runner.files_for(season, options)),
        cwd=season.folder,
        capture_output=True,
        check=True,
    )
    assert mine.getvalue() == theirs.stdout
    assert mine.getvalue()
