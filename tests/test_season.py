import io
import zipfile
from pathlib import Path

import pytest

from retrosheetpy import IntegrityError, Season, cache_dir, get
from retrosheetpy import season as season_module
from retrosheetpy.cli import main


def decade_zip(extra: dict[str, bytes] | None = None) -> bytes:
    members = {
        "2010ANA.EVA": b"id,A\n",
        "2010BOS.EVN": b"id,B\n",
        "2011ANA.EVA": b"other season\n",
        "ANA2010.ROS": b"r\n",
        "ANA2011.ROS": b"r11\n",
        "TEAM2010": b"ANA,A,Anaheim,Angels\n",
        "TEAM2011": b"x\n",
        "readme.txt": b"ignore me\n",
        **(extra or {}),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


class Fetch:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.calls.append(url)
        return self.payload


def test_get_unpacks_only_that_season(tmp_path: Path) -> None:
    s = get(2010, cache=tmp_path, fetch=Fetch(decade_zip()))
    assert isinstance(s, Season)
    assert [p.name for p in s.event_files] == ["2010ANA.EVA", "2010BOS.EVN"]
    assert [p.name for p in s.roster_files] == ["ANA2010.ROS"]
    assert s.team_file is not None and s.team_file.name == "TEAM2010"
    assert sorted(p.name for p in s.folder.iterdir() if not p.name.startswith(".")) == [
        "2010ANA.EVA",
        "2010BOS.EVN",
        "ANA2010.ROS",
        "TEAM2010",
    ]


def test_second_get_does_not_download_again(tmp_path: Path) -> None:
    fetch = Fetch(decade_zip())
    get(2010, cache=tmp_path, fetch=fetch)
    get(2010, cache=tmp_path, fetch=fetch)
    assert len(fetch.calls) == 1


def test_two_seasons_share_one_decade_download(tmp_path: Path) -> None:
    fetch = Fetch(decade_zip())
    get(2010, cache=tmp_path, fetch=fetch)
    s = get(2011, cache=tmp_path, fetch=fetch)
    assert len(fetch.calls) == 1
    assert [p.name for p in s.event_files] == ["2011ANA.EVA"]


def test_missing_season_is_an_error_and_leaves_no_folder(tmp_path: Path) -> None:
    with pytest.raises(IntegrityError):
        get(2012, cache=tmp_path, fetch=Fetch(decade_zip()))
    assert not (tmp_path / "seasons" / "2012").exists()
    assert not (tmp_path / "seasons" / "2012.part").exists()


def test_unsafe_member_name_is_refused(tmp_path: Path) -> None:
    from retrosheetpy import UnsafeArchiveMemberError

    with pytest.raises(UnsafeArchiveMemberError):
        get(2010, cache=tmp_path, fetch=Fetch(decade_zip({"../2010EVL.EVN": b"x"})))


def test_notice_shown_once(tmp_path: Path) -> None:
    seen: list[str] = []
    fetch = Fetch(decade_zip())
    get(2010, cache=tmp_path, fetch=fetch, notice=seen.append)
    get(2011, cache=tmp_path, fetch=fetch, notice=seen.append)
    assert len(seen) == 1 and "Retrosheet" in seen[0]


def test_cache_dir_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RETROSHEETPY_HOME", str(tmp_path / "env"))
    assert cache_dir() == tmp_path / "env"
    assert cache_dir(tmp_path / "arg") == tmp_path / "arg"
    monkeypatch.delenv("RETROSHEETPY_HOME")
    assert cache_dir() == Path.home() / ".retrosheetpy"


def test_verify_detects_changed_download(tmp_path: Path) -> None:
    get(2010, cache=tmp_path, fetch=Fetch(decade_zip()))
    assert season_module.verify(tmp_path) == []
    zip_path = tmp_path / "downloads" / "events_decade" / "2010seve.zip"
    zip_path.write_bytes(b"tampered")
    assert season_module.verify(tmp_path) != []


def test_tampered_download_is_refetched(tmp_path: Path) -> None:
    fetch = Fetch(decade_zip())
    get(2010, cache=tmp_path, fetch=fetch)
    (tmp_path / "downloads" / "events_decade" / "2010seve.zip").write_bytes(b"tampered")
    s = get(2010, cache=tmp_path, fetch=fetch)
    assert len(fetch.calls) == 2 and len(s.event_files) == 2


def test_list_and_clear(tmp_path: Path) -> None:
    get(2010, cache=tmp_path, fetch=Fetch(decade_zip()))
    assert season_module.cached_seasons(tmp_path) == [2010]
    season_module.clear(tmp_path)
    assert season_module.cached_seasons(tmp_path) == []


def test_cli_list_path_and_verify(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    get(2010, cache=tmp_path, fetch=Fetch(decade_zip()))
    assert main(["--cache-dir", str(tmp_path), "list"]) == 0
    assert capsys.readouterr().out.split() == ["2010"]
    assert main(["--cache-dir", str(tmp_path), "cache", "path"]) == 0
    assert str(tmp_path) in capsys.readouterr().out
    assert main(["--cache-dir", str(tmp_path), "cache", "verify"]) == 0


def test_cli_get_reports_errors_plainly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--cache-dir", str(tmp_path), "get", "1850"]) == 1
    assert "no event decade archive" in capsys.readouterr().err
