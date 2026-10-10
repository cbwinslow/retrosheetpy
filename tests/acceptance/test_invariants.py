"""Acceptance tests: one section per invariant in openspec/project.md.

``TRACE`` maps every invariant to the tests that prove it, anywhere in the suite; the last test
fails if a listed test has been renamed or removed, or if an invariant has none.
"""

import csv
import io
import json
import re
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path

import fake_season as fake
import pytest

import retrosheetpy as rs
from retrosheetpy import Kind, SeasonNotFoundError, ToolError, runner
from retrosheetpy.cache import NOTICE
from retrosheetpy.cli import main
from retrosheetpy.errors import InvalidArchiveError, RetrosheetError

TESTS = Path(__file__).resolve().parent.parent

# Invariants 2 (no Retrosheet data in the repo), 6 (minimal dependencies) and 7 (credit notice) are
# checked below against the files in the repository, not against behaviour.
TRACE: dict[int, list[str]] = {
    1: [
        "test_client.py::test_http_fetch_refuses_non_https",
        "test_client.py::test_redirect_to_http_is_refused",
        "test_client.py::test_archive_with_too_many_members_is_refused",
        "test_client.py::test_archive_that_unpacks_too_large_is_refused",
        "test_client.py::test_modified_cache_is_refetched_with_new_metadata",
        "test_client.py::test_interrupted_update_is_a_cache_miss_not_an_integrity_error",
        "acceptance/test_invariants.py::test_an_interrupted_download_caches_nothing",
    ],
    2: ["acceptance/test_invariants.py::test_no_retrosheet_data_file_is_in_the_repository"],
    3: [
        "test_kinds.py::test_postseason_uses_series_named_files_and_its_own_rosters",
        "test_kinds.py::test_allstar",
        "test_kinds.py::test_negro_leagues_year_named_files_and_no_team_list_from_retrosheet",
        "test_kinds.py::test_unknown_kind_is_refused_before_anything_downloads",
        "acceptance/test_invariants.py::test_every_kind_and_table_in_every_format_holds_the_tools_rows",
    ],
    4: [
        "test_parity_c.py::test_equals_the_c_tool",
        "test_parity_c.py::test_every_kind_equals_the_c_tool",
        "acceptance/test_invariants.py::test_every_kind_and_table_in_every_format_holds_the_tools_rows",
    ],
    5: [
        "test_cache.py::test_missing_season_is_an_error_and_leaves_no_folder",
        "test_client.py::test_corrupt_zip_rejected",
        "acceptance/test_invariants.py::test_a_failing_tool_names_the_tool_and_the_season",
        "acceptance/test_invariants.py::test_a_missing_tool_is_a_plain_error",
    ],
    6: ["acceptance/test_invariants.py::test_the_only_required_dependency_is_chadwickpy"],
    7: ["acceptance/test_invariants.py::test_the_data_use_notice_and_credit_are_kept"],
}


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


# --- 1. safe downloads ------------------------------------------------------------------------


def test_an_interrupted_download_caches_nothing(tmp_path: Path) -> None:
    def dropped(url: str) -> bytes:
        raise ConnectionResetError("connection dropped")

    cache = tmp_path / "cache"
    with pytest.raises(ConnectionResetError):
        rs.season(2010, cache=cache, fetch=dropped)
    files = [p for p in cache.rglob("*") if p.is_file() and p.name != ".notice-shown"]
    assert files == []  # no half-written archive, no record, no temp file
    # and the next attempt, with the network back, simply works
    assert rs.season(2010, cache=cache, fetch=fake.fetch).year == 2010


def test_a_half_downloaded_archive_is_refused_and_not_kept(tmp_path: Path) -> None:
    whole = fake.decade_zip()
    cache = tmp_path / "cache"
    with pytest.raises(InvalidArchiveError):
        rs.season(2010, cache=cache, fetch=lambda url: whole[: len(whole) // 2])
    assert [p for p in (cache / "downloads").rglob("*") if p.is_file()] == []


# --- 2. no Retrosheet data in the repository --------------------------------------------------


def test_no_retrosheet_data_file_is_in_the_repository() -> None:
    root = TESTS.parent
    event_file = re.compile(r"\.(E[VDB][A-Z]|ROS|zip)$|^TEAM\d{4}$", re.IGNORECASE)
    skip = {".git", ".venv", "node_modules", "site", "dist"}
    found = [
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and not (skip & set(p.relative_to(root).parts)) and event_file.search(p.name)
    ]
    assert found == []


# --- 3 and 4. every kind, every format --------------------------------------------------------

KINDS = [
    (Kind.REGULAR, 2010),
    (Kind.POSTSEASON, 2010),
    (Kind.ALLSTAR, 2010),
    (Kind.NEGRO, 1912),
    (Kind.NEGRO_BOX, 1912),
    (Kind.BOX, 1901),
]
ROW_TABLES = ["events", "games", "daily", "subs", "comments"]


def table(name: str, kind: Kind, year: int, cache: Path):  # type: ignore[no-untyped-def]
    return getattr(rs, name)(year, kind=kind, cache=cache, fetch=fake.fetch_any)


@pytest.mark.parametrize("name", ROW_TABLES)
@pytest.mark.parametrize(("kind", "year"), KINDS)
def test_every_kind_and_table_in_every_format_holds_the_tools_rows(
    kind: Kind, year: int, name: str, cache: Path
) -> None:
    """Shaping adds structure, not meaning: each format reads back as exactly the tool's rows."""
    t = table(name, kind, year, cache)
    rows = [tuple(r.values()) for r in t.load()]
    base = cache.parent / f"{kind.value}-{name}"
    _csv(t, base, rows)
    _jsonl(t, base)
    _json(t, base)
    _sqlite(t, base, rows)


@pytest.mark.parametrize(("kind", "year"), KINDS)
def test_every_kind_has_games_and_box_scores(kind: Kind, year: int, cache: Path) -> None:
    assert len(table("games", kind, year, cache).load()) >= 1
    assert rs.boxscores(year, kind=kind, cache=cache, fetch=fake.fetch_any).text().strip()


def test_box_scores_in_xml(cache: Path) -> None:
    box = rs.boxscores(2010, cache=cache, fetch=fake.fetch)
    assert box.xml().lstrip().startswith("<boxscore ")
    out = cache.parent / "box.txt"
    box.write(out)
    assert out.read_text() == box.text()


def _csv(t, base: Path, rows: list[tuple[str, ...]]) -> None:  # type: ignore[no-untyped-def]
    path = base.with_suffix(".csv")
    t.to_csv(path)
    got = list(csv.reader(io.StringIO(path.read_text())))
    assert got[0] == list(t.columns) and [tuple(r) for r in got[1:]] == rows


def _jsonl(t, base: Path) -> None:  # type: ignore[no-untyped-def]
    path = base.with_suffix(".jsonl")
    t.to_jsonl(path)
    assert [json.loads(x) for x in path.read_text().splitlines()] == t.load()


def _json(t, base: Path) -> None:  # type: ignore[no-untyped-def]
    path = base.with_suffix(".json")
    t.to_json(path)
    assert json.loads(path.read_text()) == t.load()


def _sqlite(t, base: Path, rows: list[tuple[str, ...]]) -> None:  # type: ignore[no-untyped-def]
    path = base.with_suffix(".db")
    t.to_sqlite(path, table="t")
    con = sqlite3.connect(path)
    try:
        assert con.execute("select * from t").fetchall() == rows
    finally:
        con.close()


# --- 5. clear failures ------------------------------------------------------------------------


def test_a_failing_tool_names_the_tool_and_the_season(
    cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = rs.season(2010, cache=cache, fetch=fake.fetch)
    cmd = [sys.executable, "-c", "import sys; sys.stderr.write('bad option'); sys.exit(3)"]
    monkeypatch.setattr(runner, "command", lambda *a, **k: cmd)
    with pytest.raises(ToolError) as err:
        s.events().load()
    assert (
        "cwevent" in str(err.value) and "2010" in str(err.value) and "bad option" in str(err.value)
    )


def test_a_missing_tool_is_a_plain_error(
    cache: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    s = rs.season(2010, cache=cache, fetch=fake.fetch)
    monkeypatch.setattr(runner, "command", lambda *a, **k: ["no-such-chadwick-tool-anywhere"])
    with pytest.raises(RetrosheetError):
        s.events().load()
    capsys.readouterr()
    assert main(["--cache-dir", str(cache), "events", "2010"]) == 1
    assert capsys.readouterr().err.startswith("retrosheetpy: ")


def test_a_missing_season_says_what_to_do(cache: Path) -> None:
    with pytest.raises(SeasonNotFoundError) as err:
        rs.season(2012, kind="postseason", cache=cache, fetch=fake.fetch_any)
    assert "2012" in str(err.value)


# --- 6 and 7. what the repository promises ----------------------------------------------------


def test_the_only_required_dependency_is_chadwickpy() -> None:
    text = (TESTS.parent / "pyproject.toml").read_text()
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.DOTALL | re.MULTILINE)
    assert block is not None
    deps = re.findall(r'"([A-Za-z0-9_.-]+)', block.group(1))
    assert deps == ["chadwickpy"]


def test_the_data_use_notice_and_credit_are_kept() -> None:
    root = TESTS.parent
    assert "retrosheet" in (root / "NOTICE").read_text().lower()
    assert "retrosheet" in (root / "README.md").read_text().lower()
    assert NOTICE.strip()


# --- the map itself ---------------------------------------------------------------------------


def test_every_invariant_is_traced_to_tests_that_exist() -> None:
    assert sorted(TRACE) == [1, 2, 3, 4, 5, 6, 7]
    check: Callable[[str], bool] = lambda ref: _has_test(*ref.split("::"))  # noqa: E731
    missing = [ref for refs in TRACE.values() for ref in refs if not check(ref)]
    assert missing == []


def _has_test(file: str, name: str) -> bool:
    path = TESTS / file
    return (
        path.is_file()
        and re.search(rf"^def {re.escape(name)}\(", path.read_text(), re.M) is not None
    )
