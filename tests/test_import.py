import retrosheetpy
from retrosheetpy.cli import main


def test_version_is_a_string() -> None:
    assert isinstance(retrosheetpy.__version__, str)


def test_cli_version(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["--version"]) == 0
    assert "retrosheetpy" in capsys.readouterr().out
