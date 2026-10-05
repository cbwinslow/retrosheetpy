import io
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fake_season import decade_zip

import retrosheetpy as rs
from retrosheetpy import ToolError, season, tables
from retrosheetpy.cli import main


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    season.get(2010, cache=tmp_path, fetch=lambda url: decade_zip())
    return tmp_path


def by_hand(tool: str, folder: Path, *args: str) -> bytes:
    """Run chadwickpy directly, the way a person would, from the season folder."""
    done = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "chadwickpy", tool, "-q", "-y", "2010", *args, "2010AAA.EVN"],
        cwd=folder,
        capture_output=True,
        check=True,
    )
    return done.stdout


@pytest.mark.parametrize("name", list(tables.TABLES))
def test_output_equals_running_chadwickpy_by_hand(cache: Path, name: str) -> None:
    table = tables.TABLES[name]
    s = season.get(2010, cache=cache)
    out = io.BytesIO()
    tables.run(table, s, out, jobs=1)
    extra: list[str] = []
    if table.csv_output:
        extra = ["-n", "-f", f"0-{table.max_field}"]
        if table.max_ext_field is not None:
            extra += ["-x", f"0-{table.max_ext_field}"]
    assert out.getvalue() == by_hand(table.tool, s.folder, *extra)
    assert out.getvalue()


def test_events_rows_are_dicts_with_field_names(cache: Path) -> None:
    rows = rs.events(2010, cache=cache)
    assert len(rows) == 4  # the four plays in the made-up game
    assert rows[0]["GAME_ID"] == "AAA201004050"
    assert rows[0]["BAT_ID"] == "bbbp1"


def test_games_comments_daily_subs_rows(cache: Path) -> None:
    assert [r["GAME_ID"] for r in rs.games(2010, cache=cache)] == ["AAA201004050"]
    assert rs.comments(2010, cache=cache)[0]["COMMENT_TX"] == "a made-up game"
    assert len(rs.daily(2010, cache=cache)) == 18
    assert rs.subs(2010, cache=cache) == []


def test_boxscores_is_text(cache: Path) -> None:
    text = rs.boxscores(2010, cache=cache)
    assert "Bville" in text and "Aville" in text


def test_rows_refuses_a_text_table(cache: Path) -> None:
    with pytest.raises(ValueError, match="text"):
        tables.rows(tables.TABLES["boxscores"], season.get(2010, cache=cache))


def test_a_season_with_no_event_files_is_a_tool_error(tmp_path: Path) -> None:
    empty = season.Season(2010, tmp_path, (), (), None)
    with pytest.raises(ToolError, match="no event files"):
        tables.run(tables.TABLES["events"], empty, io.BytesIO())


def test_a_tool_failure_reports_its_message(cache: Path) -> None:
    s = season.get(2010, cache=cache)
    (s.folder / "2010AAA.EVN").write_text("id,BAD\nthis is not a game\n")
    with pytest.raises(ToolError, match="cwevent failed"):
        tables.run(tables.TABLES["events"], s, io.BytesIO())


def test_write_is_all_or_nothing(cache: Path, tmp_path: Path) -> None:
    s = season.get(2010, cache=cache)
    (s.folder / "2010AAA.EVN").write_text("id,BAD\nthis is not a game\n")
    dest = tmp_path / "out" / "x.csv"
    with pytest.raises(ToolError):
        tables.write(tables.TABLES["events"], s, dest)
    assert not dest.exists() and not dest.with_name("x.csv.part").exists()


def test_cli_writes_a_file(cache: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "o"
    assert main(["--cache-dir", str(cache), "events", "2010", "--out", str(out)]) == 0
    assert (out / "2010-events.csv").read_text().startswith('"GAME_ID"')
    assert str(out / "2010-events.csv") in capsys.readouterr().out


@pytest.mark.skipif(
    not (
        os.environ.get("CHADWICK_BIN")
        and (Path(os.environ.get("CHADWICK_BIN", "")) / "cwevent").exists()
    ),
    reason="set CHADWICK_BIN to the folder holding the real Chadwick tools",
)
@pytest.mark.parametrize("name", list(tables.TABLES))
def test_output_equals_the_real_chadwick_c_tools(cache: Path, name: str) -> None:
    table = tables.TABLES[name]
    s = season.get(2010, cache=cache)
    mine = io.BytesIO()
    tables.run(table, s, mine)
    cmd = [str(Path(os.environ["CHADWICK_BIN"]) / table.tool), "-q", "-y", "2010"]
    if table.csv_output:
        cmd += ["-n", "-f", f"0-{table.max_field}"]
        if table.max_ext_field is not None:
            cmd += ["-x", f"0-{table.max_ext_field}"]
    done = subprocess.run([*cmd, "2010AAA.EVN"], cwd=s.folder, capture_output=True, check=True)  # noqa: S603
    assert mine.getvalue() == done.stdout
