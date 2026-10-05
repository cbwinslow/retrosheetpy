import csv
import io
import json
import sqlite3
import sys
import zipfile
from pathlib import Path

import fake_season as fake
import pytest

import retrosheetpy as rs
from retrosheetpy import ToolError


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


def q(name: str, years, cache: Path, **kw):  # type: ignore[no-untyped-def]
    return getattr(rs, name)(years, cache=cache, fetch=fake.fetch, **kw)


def zip_with(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in {
            **{k: v.encode("latin-1") for k, v in fake.FILES.items()},
            **files,
        }.items():
            zf.writestr(name, data)
    return buf.getvalue()


# --- the shape of a Table ---------------------------------------------------------------------


def test_every_column_is_present_and_named_as_chadwick_names_them(cache: Path) -> None:
    t = q("events", 2010, cache)
    assert len(t.columns) == 164
    assert (
        t.columns[:3] == ("GAME_ID", "AWAY_TEAM_ID", "INN_CT") and t.columns[-1] == "RUN3_AUTO_FL"
    )
    assert len(q("games", 2010, cache).columns) == 182
    assert len(q("daily", 2010, cache).columns) == 154
    assert len(q("subs", 2010, cache).columns) == 25
    assert len(q("comments", 2010, cache).columns) == 10


@pytest.mark.parametrize("name", ["events", "games", "daily", "subs", "comments"])
def test_fields_listing_agrees_with_the_columns(cache: Path, name: str) -> None:
    """Nothing is dropped: Chadwick's own field list and the columns we print are the same size."""
    assert len(rs.fields(name)) == len(q(name, 2010, cache).columns)


def test_row_counts_and_values(cache: Path) -> None:
    rows = q("events", 2010, cache).load()
    assert len(rows) == fake.GAMES_2010 * fake.PLAYS_PER_GAME
    assert rows[0]["GAME_ID"] == "AAA201004050" and rows[0]["BAT_ID"] == "bbbp1"
    assert [r["GAME_ID"] for r in q("games", 2010, cache)] == [
        "AAA201004050", "AAA201004060", "BBB201004070"
    ]  # fmt: skip
    assert len(q("daily", 2010, cache).load()) == fake.GAMES_2010 * 18
    assert len(q("comments", 2010, cache).load()) == fake.COMMENTS_2010
    assert q("subs", 2010, cache).load() == []


def test_a_table_can_be_looped_over_again_and_again(cache: Path) -> None:
    t = q("games", 2010, cache)
    assert list(t) == list(t) == t.load() == t.to_dicts()
    assert list(t.rows()) == [tuple(r.values()) for r in t]


def test_values_are_plain_strings(cache: Path) -> None:
    row = q("games", 2010, cache).load()[0]
    assert all(isinstance(v, str) for v in row.values())


def test_a_run_that_matches_nothing_still_has_its_columns(cache: Path) -> None:
    t = q("events", 2010, cache, game="AAA201009090")
    assert t.load() == [] and len(t.columns) == 164


# --- seasons ----------------------------------------------------------------------------------


def test_several_seasons_make_one_table_with_one_header(cache: Path) -> None:
    t = q("events", [2010, 2011], cache)
    rows = t.load()
    assert len(rows) == (fake.GAMES_2010 + fake.GAMES_2011) * fake.PLAYS_PER_GAME
    assert [r["GAME_ID"][3:7] for r in rows[::4]] == ["2010", "2010", "2010", "2011"]
    out = io.StringIO()
    t.to_csv(out)
    assert out.getvalue().count("GAME_ID") == 1
    assert sum(1 for _ in csv.reader(io.StringIO(out.getvalue()))) == len(rows) + 1


def test_a_range_and_a_list_are_the_same(cache: Path) -> None:
    assert q("games", range(2010, 2012), cache).load() == q("games", [2010, 2011], cache).load()
    assert q("games", 2010, cache).years == (2010,)


def test_repeated_or_missing_years_are_refused(cache: Path) -> None:
    for bad in ([2010, 2010], []):
        with pytest.raises(ValueError):
            q("events", bad, cache)


def test_a_season_with_no_data_in_the_archive_is_an_error(cache: Path) -> None:
    with pytest.raises(rs.IntegrityError):
        q("events", 2012, cache)


# --- filters ----------------------------------------------------------------------------------


def test_home_picks_that_teams_file(cache: Path) -> None:
    assert len(q("events", 2010, cache, home="AAA").load()) == 8
    assert len(q("events", 2010, cache, home="BBB").load()) == 4
    both = q("games", 2010, cache, home=["BBB", "AAA"]).load()
    assert [r["GAME_ID"][:3] for r in both] == ["BBB", "AAA", "AAA"]  # the order asked for


def test_unknown_home_team_names_the_available_ones(cache: Path) -> None:
    with pytest.raises(ValueError, match=r"no event file for home team ZZZ.*AAA BBB"):
        q("events", 2010, cache, home="ZZZ").load()
    assert rs.season(2010, cache=cache, fetch=fake.fetch).teams == ("AAA", "BBB")


def test_game_and_dates(cache: Path) -> None:
    assert len(q("events", 2010, cache, game="AAA201004060").load()) == 4
    assert len(q("games", 2010, cache, start="0406").load()) == 2
    assert len(q("games", 2010, cache, end="0405").load()) == 1
    assert len(q("games", 2010, cache, start="0406", end="0406").load()) == 1
    assert q("games", 2010, cache, start="0501").load() == []


def test_bad_options_are_refused_before_anything_is_downloaded(cache: Path) -> None:
    def no_network(url: str) -> bytes:
        raise AssertionError("downloaded before the options were checked")

    with pytest.raises(ValueError):
        rs.events(2010, cache=cache, fetch=no_network, start="13")
    with pytest.raises(ValueError):
        rs.events(2010, cache=cache, fetch=no_network, fields=999)


def test_fields_and_extended(cache: Path) -> None:
    assert q("events", 2010, cache, fields="0-2").columns == ("GAME_ID", "AWAY_TEAM_ID", "INN_CT")
    wide = q("events", 2010, cache, fields=[0], extended="0-1")
    assert wide.columns == ("GAME_ID", "HOME_TEAM_ID", "BAT_TEAM_ID")
    assert all(len(r) == 3 for r in wide.rows())
    only_ext = q("events", 2010, cache, extended=[1])  # choosing one kind drops the other
    assert only_ext.columns == ("BAT_TEAM_ID",)
    assert len(q("events", 2010, cache, fields=range(97)).columns) == 97
    assert len(q("games", 2010, cache, extended="0-96").columns) == 97


def test_select_keeps_the_order_asked_for(cache: Path) -> None:
    t = q("games", 2010, cache).select("HOME_TEAM_ID", "GAME_ID")
    assert t.columns == ("HOME_TEAM_ID", "GAME_ID")
    assert t.load()[0] == {"HOME_TEAM_ID": "AAA", "GAME_ID": "AAA201004050"}
    assert t.select("GAME_ID").columns == ("GAME_ID",)


def test_select_refuses_unknown_empty_or_repeated(cache: Path) -> None:
    t = q("games", 2010, cache)
    for args in (("NOPE",), (), ("GAME_ID", "GAME_ID")):
        with pytest.raises(ValueError):
            t.select(*args)


def test_jobs_does_not_change_the_answer(cache: Path) -> None:
    assert q("events", 2010, cache, jobs=1).load() == q("events", 2010, cache).load()
    assert q("events", 2010, cache, jobs=2).load() == q("events", 2010, cache).load()


# --- failures ---------------------------------------------------------------------------------


def test_a_failing_tool_raises_toolerror_with_its_message(cache: Path) -> None:
    broken = fake.FILES["2010AAA.EVN"].replace("info,date,2010/04/06\n", "")
    zipped = zip_with({"2010AAA.EVN": broken.encode("latin-1")})
    t = rs.events(2010, cache=cache, fetch=lambda url: zipped)
    with pytest.raises(ToolError, match="has no date"):
        t.load()


def test_stopping_early_does_not_hang_or_raise(cache: Path) -> None:
    it = iter(q("events", 2010, cache))
    assert next(it)["GAME_ID"] == "AAA201004050"
    it.close()  # the tool is stopped; no error, no leftover process


def test_text_tables_are_not_tables(cache: Path) -> None:
    from retrosheetpy.options import Options
    from retrosheetpy.table import Table
    from retrosheetpy.tools import tool

    with pytest.raises(ValueError, match="text"):
        Table(tool("boxscores"), [rs.season(2010, cache=cache, fetch=fake.fetch)], Options())


# --- outputs ----------------------------------------------------------------------------------


def test_csv_round_trips_the_rows(cache: Path, tmp_path: Path) -> None:
    t = q("games", [2010, 2011], cache)
    t.to_csv(tmp_path / "g.csv")
    with (tmp_path / "g.csv").open(newline="", encoding="utf-8") as f:
        assert list(csv.DictReader(f)) == t.load()
    t.to_csv(tmp_path / "h.csv", header=False)
    assert (tmp_path / "h.csv").read_text().count("\n") == 4


def test_csv_to_a_file_object(cache: Path) -> None:
    out = io.StringIO()
    q("subs", 2010, cache).to_csv(out)
    assert out.getvalue().startswith("GAME_ID,")


def test_jsonl_and_json(cache: Path, tmp_path: Path) -> None:
    t = q("games", 2010, cache)
    t.to_jsonl(tmp_path / "g.jsonl")
    assert [json.loads(x) for x in (tmp_path / "g.jsonl").read_text().splitlines()] == t.load()
    t.to_json(tmp_path / "g.json")
    assert json.loads((tmp_path / "g.json").read_text()) == t.load()
    q("subs", 2010, cache).to_json(tmp_path / "e.json")
    assert json.loads((tmp_path / "e.json").read_text()) == []


def test_non_ascii_text_is_kept_whole(cache: Path, tmp_path: Path) -> None:
    cafe = fake.FILES["2010AAA.EVN"].replace("a made-up game", "caf\xe9 gam\xf1")
    zipped = zip_with({"2010AAA.EVN": cafe.encode("latin-1")})
    t = rs.comments(2010, cache=cache, fetch=lambda url: zipped)
    assert t.load()[0]["COMMENT_TX"].startswith("caf\xe9 gam\xf1")
    t.to_csv(tmp_path / "u.csv")
    assert "caf\xe9 gam\xf1" in (tmp_path / "u.csv").read_text(encoding="utf-8")
    t.to_csv(tmp_path / "l.csv", encoding="latin-1")
    assert b"caf\xe9 gam\xf1" in (tmp_path / "l.csv").read_bytes()
    t.to_jsonl(tmp_path / "u.jsonl")
    assert "caf\xe9 gam\xf1" in (tmp_path / "u.jsonl").read_text(encoding="utf-8")


def test_sqlite(cache: Path, tmp_path: Path) -> None:
    db = tmp_path / "x" / "mlb.db"
    t = q("games", [2010, 2011], cache)
    assert t.to_sqlite(db) == 4
    con = sqlite3.connect(db)
    assert con.execute("select count(*) from games").fetchone() == (4,)
    assert con.execute('select "GAME_ID" from games order by 1').fetchall()[-1] == ("BBB201004070",)
    assert len(con.execute("pragma table_info(games)").fetchall()) == 182
    with pytest.raises(ValueError, match="already exists"):
        t.to_sqlite(db)
    assert t.to_sqlite(db, if_exists="append") == 4
    assert con.execute("select count(*) from games").fetchone() == (8,)
    assert t.to_sqlite(db, if_exists="replace") == 4
    assert con.execute("select count(*) from games").fetchone() == (4,)
    t.select("GAME_ID").to_sqlite(db, "ids")
    assert con.execute("select count(*) from ids").fetchone() == (4,)
    con.close()


def test_sqlite_table_name_is_checked(cache: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="plain table name"):
        q("games", 2010, cache).to_sqlite(tmp_path / "a.db", 'x"; drop table y; --')


def test_a_failed_write_leaves_nothing_behind(cache: Path, tmp_path: Path) -> None:
    broken = fake.FILES["2010AAA.EVN"].replace("info,date,2010/04/06\n", "")
    zipped = zip_with({"2010AAA.EVN": broken.encode("latin-1")})
    t = rs.events(2010, cache=cache, fetch=lambda url: zipped)
    for name, method in (("a.csv", t.to_csv), ("a.jsonl", t.to_jsonl), ("a.json", t.to_json)):
        with pytest.raises(ToolError):
            method(tmp_path / name)
    assert list(tmp_path.glob("a.*")) == []
    (tmp_path / "keep.csv").write_text("old")
    with pytest.raises(ToolError):
        t.to_csv(tmp_path / "keep.csv")
    assert (tmp_path / "keep.csv").read_text() == "old"  # the old file is untouched
    with pytest.raises(ToolError):
        t.to_sqlite(tmp_path / "a.db")
    con = sqlite3.connect(tmp_path / "a.db")
    assert con.execute("select count(*) from sqlite_master").fetchone() == (0,)  # rolled back
    con.close()


def test_write_chooses_the_format_from_the_name(cache: Path, tmp_path: Path) -> None:
    t = q("games", 2010, cache)
    for name in ("a.csv", "a.jsonl", "a.json", "a.db", "a.sqlite"):
        t.write(tmp_path / name)
        assert (tmp_path / name).stat().st_size > 0
    t.write(tmp_path / "noext", format="csv")
    with pytest.raises(ValueError, match="cannot tell the format"):
        t.write(tmp_path / "a.txt")


def test_pandas(cache: Path) -> None:
    pd = pytest.importorskip("pandas")
    df = q("games", 2010, cache).to_pandas()
    assert (
        isinstance(df, pd.DataFrame) and df.shape == (3, 182) and df["GAME_ID"][0] == "AAA201004050"
    )


def test_pandas_missing_gives_a_clear_message(cache: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pandas", None)
    with pytest.raises(ImportError, match=r"retrosheetpy\[pandas\]"):
        q("games", 2010, cache).to_pandas()


# --- box scores -------------------------------------------------------------------------------


def test_boxscores(cache: Path, tmp_path: Path) -> None:
    b = q("boxscores", 2010, cache)
    text = b.text()
    assert text.count("Game of") == fake.GAMES_2010 and "Aville" in text and "Bville" in text
    assert "<" in b.xml() and "sports-content" in b.sportsml()
    b.write(tmp_path / "b.txt")
    assert (tmp_path / "b.txt").read_text() == text
    b.write(tmp_path / "b.xml", "xml")
    assert (tmp_path / "b.xml").read_text().lstrip().startswith("<")


def test_boxscores_for_several_seasons(cache: Path) -> None:
    b = q("boxscores", [2010, 2011], cache)
    assert b.text().count("Game of") == fake.GAMES_2010 + fake.GAMES_2011
    with pytest.raises(ValueError, match="one season"):
        b.xml()
    with pytest.raises(ValueError, match="one season"):
        b.sportsml()


def test_boxscore_filters_and_refusals(cache: Path) -> None:
    assert q("boxscores", 2010, cache, game="AAA201004060").text().count("Game of") == 1
    assert q("boxscores", 2010, cache, home="BBB").text().count("Game of") == 1
    with pytest.raises(ValueError, match="no fields"):
        q("boxscores", 2010, cache, fields=0)


def _processes_running_in(folder: Path) -> list[int]:
    """Process ids whose working directory is ``folder`` (Linux). The season folder is unique to
    each test, and every tool process and worker runs inside it."""
    found = []
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            if (entry / "cwd").resolve() == folder.resolve():
                found.append(int(entry.name))
        except OSError:
            continue  # the process ended while we looked
    return found


def _describe(pid: int) -> str:
    """State, parent, process group and session of a process, for a failure message."""
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()[:70]
        state, ppid, pgrp, session = fields[0], fields[1], fields[2], fields[3]
        return f"pid {pid} state={state} ppid={ppid} pgrp={pgrp} session={session} {cmd}"
    except OSError:
        return f"pid {pid} (gone)"


def _wait_until_none_left(folder: Path, seconds: float = 10) -> list[int]:
    import time

    deadline = time.time() + seconds
    left = _processes_running_in(folder)
    while left and time.time() < deadline:
        time.sleep(0.1)
        left = _processes_running_in(folder)
    return left


needs_proc = pytest.mark.skipif(not Path("/proc/self/cwd").exists(), reason="needs Linux /proc")


@needs_proc
def test_stopping_early_leaves_no_worker_processes_behind(cache: Path) -> None:
    """chadwickpy runs team files in worker processes. Killing only its main process would leave
    them running (this leaked 36 idle processes before); the whole process group must stop."""
    # Big enough that the output cannot fit in the pipe, so the tool is still running (blocked
    # on writing) when we stop reading, and has two team files so chadwickpy starts two workers.
    big = {
        name: "".join(
            fake.game(2010, home, away, f"{m:02d}{d:02d}")
            for m in range(4, 10)
            for d in range(1, 29)
        )
        for name, home, away in (("2010AAA.EVN", "AAA", "BBB"), ("2010BBB.EVA", "BBB", "AAA"))
    }
    zipped = zip_with({k: v.encode("latin-1") for k, v in big.items()})
    t = rs.events(2010, cache=cache, fetch=lambda url: zipped, jobs=2)
    it = iter(t)
    next(it)
    folder = cache / "seasons" / "2010"
    assert _processes_running_in(folder), "the tool should be running right now"
    it.close()
    left = _wait_until_none_left(folder)
    assert left == [], "worker processes were left running: " + "; ".join(
        _describe(pid) for pid in left
    )


@needs_proc
def test_a_tool_failure_leaves_no_processes_behind(cache: Path) -> None:
    broken = fake.FILES["2010AAA.EVN"].replace("info,date,2010/04/06\n", "")
    zipped = zip_with({"2010AAA.EVN": broken.encode("latin-1")})
    t = rs.events(2010, cache=cache, fetch=lambda url: zipped, jobs=2)
    with pytest.raises(ToolError):
        t.load()
    assert _wait_until_none_left(cache / "seasons" / "2010") == []
