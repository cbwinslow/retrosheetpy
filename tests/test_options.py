import pytest

from retrosheetpy import runner
from retrosheetpy.options import MAX_JOBS, Options
from retrosheetpy.tools import TOOLS, tool

EVENTS, GAMES, DAILY, BOX = tool("events"), tool("games"), tool("daily"), tool("boxscores")


def build(t=EVENTS, **kw):  # type: ignore[no-untyped-def]
    return Options.build(t, kw)


def test_defaults_are_empty() -> None:
    assert build() == Options()


def test_home_accepts_one_or_many_and_uppercases() -> None:
    assert build(home="nya").home == ("NYA",)
    assert build(home=["nya", "bos"]).home == ("NYA", "BOS")


@pytest.mark.parametrize("bad", ["NY", "NYAA", "N A", ""])
def test_home_must_be_three_characters(bad: str) -> None:
    with pytest.raises(ValueError, match="home"):
        build(home=bad)


def test_game_id_checked_and_uppercased() -> None:
    assert build(game="ana201004050").game == "ANA201004050"
    for bad in ("ANA20100405", "ANA2010040500", "20100405ANA0", ""):
        with pytest.raises(ValueError, match="game"):
            build(game=bad)


@pytest.mark.parametrize("bad", ["0001", "1301", "0432", "405", "04-05", "abcd", "00405"])
def test_dates_must_be_mmdd(bad: str) -> None:
    with pytest.raises(ValueError, match="start"):
        build(start=bad)
    with pytest.raises(ValueError, match="end"):
        build(end=bad)


def test_valid_dates_pass() -> None:
    assert build(start="0101", end="1231").end == "1231"


@pytest.mark.parametrize(
    ("given", "want"),
    [(5, "5"), ("0-3,7", "0,1,2,3,7"), ([9, 2, 2], "2,9"), (range(3), "0,1,2"), ("4", "4")],
)
def test_field_lists_are_normalised(given, want: str) -> None:  # type: ignore[no-untyped-def]
    assert build(fields=given).fields == want


@pytest.mark.parametrize("bad", [-1, 97, "0-97", "a", "1-", "-3", [], "", True, [1.5]])
def test_bad_field_lists_are_refused(bad) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="fields"):
        build(fields=bad)


def test_field_limits_follow_the_table() -> None:
    assert build(DAILY, fields=153).fields == "153"
    with pytest.raises(ValueError):
        build(DAILY, fields=154)
    assert build(EVENTS, extended=66).extended == "66"
    with pytest.raises(ValueError):
        build(EVENTS, extended=67)


def test_tables_without_extended_fields_refuse_them() -> None:
    with pytest.raises(ValueError, match="extended"):
        build(DAILY, extended=0)


def test_boxscores_have_no_fields() -> None:
    with pytest.raises(ValueError, match="no fields"):
        build(BOX, fields=0)


def test_jobs_range() -> None:
    assert build(jobs=1).jobs == 1 and build(jobs=MAX_JOBS).jobs == MAX_JOBS
    for bad in (0, -1, MAX_JOBS + 1, 2.5, "4"):
        with pytest.raises(ValueError, match="jobs"):
            build(jobs=bad)


def test_unknown_option_is_a_type_error() -> None:
    with pytest.raises(TypeError, match="unknown option"):
        Options.build(EVENTS, {"hom": "NYA"})  # type: ignore[typeddict-unknown-key]


def test_every_table_is_registered() -> None:
    assert list(TOOLS) == ["events", "games", "daily", "subs", "comments", "boxscores"]
    with pytest.raises(ValueError, match="choose from"):
        tool("nope")


def test_default_jobs_is_capped_and_leaves_a_core(monkeypatch: pytest.MonkeyPatch) -> None:
    for cores, want in [(1, 1), (2, 2), (4, 4), (5, 4), (8, 7), (17, 16), (40, 16), (512, 16)]:
        monkeypatch.setattr(runner.os, "sched_getaffinity", lambda _pid, n=cores: set(range(n)))
        assert runner.default_jobs() == want, cores


def test_default_jobs_without_affinity_support(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delattr(runner.os, "sched_getaffinity", raising=False)
    monkeypatch.setattr(runner.os, "cpu_count", lambda: 8)
    assert runner.default_jobs() == 7
    monkeypatch.setattr(runner.os, "cpu_count", lambda: None)
    assert runner.default_jobs() == 1
