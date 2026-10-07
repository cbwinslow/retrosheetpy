import json
from pathlib import Path

import fake_season as fake
import pytest

import retrosheetpy as rs
from retrosheetpy import Kind, SeasonNotFoundError
from retrosheetpy.cache import season_folder
from retrosheetpy.cli import main


@pytest.fixture
def cache(tmp_path: Path) -> Path:
    return tmp_path / "cache"


def season(kind: str, year: int, cache: Path):  # type: ignore[no-untyped-def]
    return rs.season(year, kind=kind, cache=cache, fetch=fake.fetch_any)


# --- what each kind unpacks -------------------------------------------------------------------


def test_postseason_uses_series_named_files_and_its_own_rosters(cache: Path) -> None:
    s = season("postseason", 2010, cache)
    assert [p.name for p in s.event_files] == ["2010WS.EVE"]
    assert [p.name for p in s.roster_files] == ["AAA2010.ROS", "BBB2010.ROS"]
    assert s.kind is Kind.POSTSEASON and s.teams == ()  # no single home team per file
    assert len(s.games().load()) == fake.POSTSEASON_GAMES_2010
    assert len(s.events().load()) == fake.POSTSEASON_GAMES_2010 * fake.PLAYS_PER_GAME


def test_allstar(cache: Path) -> None:
    s = season("allstar", 2010, cache)
    assert [p.name for p in s.event_files] == ["2010AS.EVE"]
    assert len(s.games().load()) == fake.ALLSTAR_GAMES_2010


def test_negro_leagues_year_named_files_and_no_team_list_from_retrosheet(cache: Path) -> None:
    s = season("negro", 1912, cache)
    assert [p.name for p in s.event_files] == ["1912.EVR"]
    assert s.team_file is not None and s.team_file.read_bytes() == b""  # we create the empty one
    assert len(s.events().load()) == fake.PLAYS_PER_GAME
    assert [r["GAME_ID"] for r in s.games()] == ["AAA191208240"]


@pytest.mark.parametrize(("kind", "year"), [("negro_box", 1912), ("box", 1901)])
def test_box_score_only_games_have_games_players_and_box_scores_but_no_events(
    cache: Path, kind: str, year: int
) -> None:
    s = season(kind, year, cache)
    assert len(s.games().load()) == 1
    assert len(s.daily().load()) == 18  # one row per player
    assert s.events().load() == []  # there are no plays to turn into events
    assert "Aville" in s.boxscores().text() or "AAA" in s.boxscores().text()


def test_a_team_list_that_retrosheet_ships_is_kept_not_replaced(cache: Path) -> None:
    s = season("box", 1901, cache)
    assert "Aville" in s.team_file.read_text()  # type: ignore[union-attr]


def test_every_kind_has_its_own_folder(cache: Path) -> None:
    regular = rs.season(2010, cache=cache, fetch=fake.fetch_any)
    post = season("postseason", 2010, cache)
    assert regular.folder != post.folder
    assert regular.folder == season_folder(cache, 2010, Kind.REGULAR)
    assert post.folder == cache / "seasons" / "postseason" / "2010"
    # the same year, but each kind keeps its own team list
    assert "Post Aces" in (post.folder / "TEAM2010").read_text()
    assert "Post Aces" not in (regular.folder / "TEAM2010").read_text()


def test_kinds_do_not_mix_in_the_results(cache: Path) -> None:
    regular = rs.games(2010, cache=cache, fetch=fake.fetch_any).load()
    post = rs.games(2010, kind="postseason", cache=cache, fetch=fake.fetch_any).load()
    assert len(regular) == fake.GAMES_2010 and len(post) == fake.POSTSEASON_GAMES_2010
    assert not {r["GAME_ID"] for r in regular} & {r["GAME_ID"] for r in post}


def test_several_years_of_one_kind(cache: Path) -> None:
    t = rs.events([2010, 2011], kind="postseason", cache=cache, fetch=fake.fetch_any)
    assert len(t.load()) == 3 * fake.PLAYS_PER_GAME


# --- errors ----------------------------------------------------------------------------------


def test_a_year_the_archive_does_not_have_says_which_years_it_has(cache: Path) -> None:
    with pytest.raises(SeasonNotFoundError, match=r"postseason event files for 1999.*2010 to 2011"):
        season("postseason", 1999, cache)
    with pytest.raises(
        SeasonNotFoundError, match=r"Negro Leagues event files for 1950.*1912 to 1913"
    ):
        season("negro", 1950, cache)


def test_an_archive_with_only_a_team_list_is_not_a_season(cache: Path) -> None:
    """Retrosheet's 1871box.zip, 1872box.zip and 1874box.zip hold nothing but TEAM files."""
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("TEAM1871", "x\n")
    with pytest.raises(SeasonNotFoundError):
        rs.season(1871, kind="box", cache=cache, fetch=lambda url: buf.getvalue())


def test_unknown_kind_is_refused_before_anything_downloads(cache: Path) -> None:
    def no_network(url: str) -> bytes:
        raise AssertionError("downloaded")

    with pytest.raises(ValueError, match=r"choose from regular, postseason"):
        rs.events(2010, kind="playoffs", cache=cache, fetch=no_network)


def test_home_only_applies_to_regular_season_files(cache: Path) -> None:
    with pytest.raises(ValueError, match="home= only works on regular-season files"):
        rs.events(2010, kind="postseason", home="AAA", cache=cache, fetch=fake.fetch_any).load()


def test_game_and_dates_still_work_on_other_kinds(cache: Path) -> None:
    t = rs.games(2010, kind="postseason", start="1028", cache=cache, fetch=fake.fetch_any)
    assert [r["GAME_ID"] for r in t] == ["BBB201010280"]


# --- the cache -------------------------------------------------------------------------------


def test_second_request_for_a_kind_does_not_download_again(cache: Path) -> None:
    calls: list[str] = []

    def counting(url: str) -> bytes:
        calls.append(url)
        return fake.fetch_any(url)

    rs.season(2010, kind="postseason", cache=cache, fetch=counting)
    rs.season(2011, kind="postseason", cache=cache, fetch=counting)  # same archive
    assert len(calls) == 1


def test_cached_seasons_and_verify_cover_every_kind(cache: Path) -> None:
    season("postseason", 2010, cache)
    season("negro", 1912, cache)
    rs.season(2010, cache=cache, fetch=fake.fetch_any)
    assert rs.cached_seasons(cache) == [2010]
    assert rs.cached_seasons(cache, "postseason") == [2010]
    assert rs.cached_seasons(cache, "negro") == [1912]
    assert rs.verify_cache(cache) == []
    archive = cache / "downloads" / "events_postseason" / "allpost.zip"
    archive.write_bytes(b"changed")
    assert any("postseason 2010" in p for p in rs.verify_cache(cache))


def test_an_older_unpack_without_a_kind_is_treated_as_regular(cache: Path) -> None:
    s = rs.season(2010, cache=cache, fetch=fake.fetch_any)
    rec = s.folder / ".season.json"
    data = json.loads(rec.read_text())
    assert data["kind"] == "regular"


# --- command line ----------------------------------------------------------------------------


def test_cli_kind(cache: Path, capsys: pytest.CaptureFixture[str]) -> None:
    season("postseason", 2010, cache)
    season("negro", 1912, cache)
    assert main(["--cache-dir", str(cache), "games", "2010", "--kind", "postseason"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("GAME_ID") and len(out) == 1 + fake.POSTSEASON_GAMES_2010
    assert main(["--cache-dir", str(cache), "list"]) == 0
    assert capsys.readouterr().out.split("\n")[:-1] == ["postseason 2010", "negro 1912"]
    assert main(["--cache-dir", str(cache), "get", "1912", "--kind", "negro"]) == 0
    assert "negro 1912: 1 event files" in capsys.readouterr().out


def test_cli_unknown_kind_is_a_usage_error(cache: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--cache-dir", str(cache), "events", "2010", "--kind", "bogus"])
    assert exc.value.code == 2


def test_cli_missing_season_message(cache: Path, capsys: pytest.CaptureFixture[str]) -> None:
    season("postseason", 2010, cache)  # the archive is now cached, so nothing is downloaded
    assert main(["--cache-dir", str(cache), "events", "1999", "--kind", "postseason"]) == 1
    err = capsys.readouterr().err  # also holds the one-time Retrosheet notice from the first call
    assert "retrosheetpy: Retrosheet has no postseason event files for 1999" in err
