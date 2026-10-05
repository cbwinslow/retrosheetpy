import csv
import io
import json
import sqlite3
from pathlib import Path

import fake_season as fake
import pytest

import retrosheetpy as rs
from retrosheetpy import cli
from retrosheetpy.cli import main, parse_years


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    """A cache that already holds the made-up 2010 and 2011 seasons, so the CLI never downloads."""
    c = tmp_path / "cache"
    for year in (2010, 2011):
        rs.season(year, cache=c, fetch=fake.fetch)
    return c


def run(cache: Path, *args: str) -> int:
    return main(["--cache-dir", str(cache), *args])


# --- years ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tokens", "want"),
    [
        (["2010"], [2010]),
        (["2008-2010"], [2008, 2009, 2010]),
        (["2001,2005"], [2001, 2005]),
        (["1999", "2003-2004", "2010"], [1999, 2003, 2004, 2010]),
    ],
)
def test_parse_years(tokens: list[str], want: list[int]) -> None:
    assert parse_years(tokens) == want


@pytest.mark.parametrize("bad", ["abc", "2010-", "-2010", "2010-2008", "20x0", ""])
def test_parse_years_refuses_nonsense(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_years([bad])


# --- commands ---------------------------------------------------------------------------------


def test_version_and_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--version"]) == 0 and "retrosheetpy" in capsys.readouterr().out
    assert main([]) == 2


def test_csv_to_stdout(cache: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(cache, "games", "2010") == 0
    rows = list(csv.DictReader(io.StringIO(capsys.readouterr().out)))
    assert [r["GAME_ID"] for r in rows] == ["AAA201004050", "AAA201004060", "BBB201004070"]


def test_each_format_to_stdout(cache: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(cache, "games", "2010", "--format", "jsonl") == 0
    assert len([json.loads(x) for x in capsys.readouterr().out.splitlines()]) == 3
    assert run(cache, "games", "2010", "--format", "json") == 0
    assert len(json.loads(capsys.readouterr().out)) == 3


def test_out_file_and_out_folder(
    cache: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(cache, "events", "2010", "--out", str(tmp_path / "e.csv")) == 0
    assert capsys.readouterr().out.strip() == str(tmp_path / "e.csv")
    assert (tmp_path / "e.csv").read_text().startswith("GAME_ID,")
    folder = tmp_path / "out"
    folder.mkdir()
    assert run(cache, "events", "2010-2011", "--out", str(folder)) == 0
    assert (folder / "2010-2011-events.csv").is_file()
    assert run(cache, "games", "2010", "--format", "jsonl", "--out", str(folder) + "/") == 0
    assert (folder / "2010-games.jsonl").is_file()
    assert run(cache, "events", "2010", "--out", str(tmp_path / "new") + "/") == 0
    assert (tmp_path / "new" / "2010-events.csv").is_file()


def test_sqlite(cache: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "m.db"
    assert run(cache, "games", "2010-2011", "--format", "sqlite", "--out", str(db)) == 0
    assert "4 rows" in capsys.readouterr().out
    assert sqlite3.connect(db).execute("select count(*) from games").fetchone() == (4,)
    assert run(cache, "games", "2010", "--format", "sqlite", "--out", str(db)) == 1  # table exists
    assert "already exists" in capsys.readouterr().err
    assert (
        run(
            cache,
            "games",
            "2010",
            "--format",
            "sqlite",
            "--out",
            str(db),
            "--if-exists",
            "replace",
            "--table",
            "g",
        )
        == 0
    )
    assert sqlite3.connect(db).execute("select count(*) from g").fetchone() == (3,)
    assert run(cache, "games", "2010", "--format", "sqlite") == 1
    assert "needs --out" in capsys.readouterr().err


def test_filters_and_fields_reach_the_table(
    cache: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        run(
            cache,
            "events",
            "2010",
            "--home",
            "BBB",
            "--fields",
            "0-1",
            "--start",
            "0407",
            "-j",
            "1",
        )
        == 0
    )
    rows = list(csv.reader(io.StringIO(capsys.readouterr().out)))
    assert rows[0] == ["GAME_ID", "AWAY_TEAM_ID"] and len(rows) == 5
    assert (
        run(cache, "events", "2010", "--home", "AAA,BBB", "--game", "BBB201004070", "--fields", "0")
        == 0
    )
    assert len(capsys.readouterr().out.splitlines()) == 5
    assert run(cache, "games", "2010", "--fields", "0", "--extended", "0") == 0
    assert capsys.readouterr().out.splitlines()[0] == "GAME_ID,AWAY_TEAM_LEAGUE_ID"


def test_boxscores_formats(cache: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(cache, "boxscores", "2010", "--game", "AAA201004050") == 0
    assert "Aville" in capsys.readouterr().out
    assert run(cache, "boxscores", "2010", "--format", "xml") == 0
    assert capsys.readouterr().out.lstrip().startswith("<")
    assert (
        run(cache, "boxscores", "2010", "--format", "sportsml", "--out", str(tmp_path / "b.xml"))
        == 0
    )
    assert "sports-content" in (tmp_path / "b.xml").read_text()
    assert run(cache, "boxscores", "2010-2011", "--format", "xml") == 1
    assert "one season" in capsys.readouterr().err


def test_fields_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fields", "comments"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert (len(lines) == 10 and lines[0].split(None, 1) == ["f", "0"]) or "game id" in lines[0]
    assert main(["fields", "events"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 164 and out[97].startswith("x")


def test_get_list_cache(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    c = tmp_path / "c"
    assert run(c, "list") == 0 and capsys.readouterr().out == ""
    for y in (2010, 2011):
        rs.season(y, cache=c, fetch=fake.fetch)
    assert run(c, "get", "2010-2011") == 0
    out = capsys.readouterr().out
    assert (
        "regular 2010: 2 event files (AAA, BBB)" in out
        and "regular 2011: 1 event files (AAA)" in out
    )
    assert run(c, "list") == 0 and capsys.readouterr().out.split() == ["2010", "2011"]
    assert run(c, "cache", "path") == 0 and str(c) in capsys.readouterr().out
    assert run(c, "cache", "verify") == 0
    assert run(c, "cache", "clear") == 0 and not c.exists()


def test_errors_are_plain_and_exit_1(cache: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for args in (
        ("events", "2010", "--home", "ZZZ"),
        ("events", "2010", "--start", "99"),
        ("events", "2010", "--fields", "500"),
        ("events", "abc"),
        ("games", "2010", "--game", "bad"),
    ):
        capsys.readouterr()
        assert run(cache, *args) == 1, args
        assert capsys.readouterr().err.startswith("retrosheetpy: "), args


def test_a_closed_pipe_is_not_an_error(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(self, dest):  # type: ignore[no-untyped-def]
        raise BrokenPipeError

    monkeypatch.setattr(rs.Table, "to_csv", broken)
    assert run(cache, "games", "2010") == 0


def test_parser_covers_every_table() -> None:
    parser = cli._parser()
    for name in ("events", "games", "daily", "subs", "comments", "boxscores"):
        assert parser.parse_args([name, "2010"]).command == name


def test_a_flag_a_table_does_not_have_is_a_usage_error(cache: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run(cache, "daily", "2010", "--extended", "0")
    assert exc.value.code == 2


def test_a_closed_pipe_is_silent_for_real(cache: Path) -> None:
    """`retrosheetpy events 2010 | head` must end quietly: no traceback, exit status 0."""
    import subprocess
    import sys

    proc = subprocess.Popen(  # noqa: S603
        [sys.executable, "-m", "retrosheetpy.cli", "--cache-dir", str(cache), "events", "2010"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    proc.stdout.close()  # the reader goes away before the first byte is written
    _, err = proc.communicate(timeout=60)
    assert proc.returncode == 0
    assert err == b""
