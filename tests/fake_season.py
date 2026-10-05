"""Made-up 2010 and 2011 seasons (fictional teams AAA and BBB) for offline tests.

Not Retrosheet data. What is in it, so tests can state exact expectations:

* 2010: ``2010AAA.EVN`` holds AAA's home games on 0405 and 0406; ``2010BBB.EVA`` holds BBB's home
  game on 0407. 3 games, 4 plays each (12 events), one comment in each AAA game.
* 2011: ``2011AAA.EVN`` holds one AAA home game on 0410 (1 game, 4 events, no comment).
"""

import io
import zipfile

_NAMES = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
_POS = [8, 4, 3, 7, 9, 5, 6, 2, 1]

GAMES_2010 = 3
GAMES_2011 = 1
PLAYS_PER_GAME = 4
COMMENTS_2010 = 2


def _starts(team: str, home: int) -> list[str]:
    return [
        f'start,{team.lower()}p{i + 1},"{team} {n}",{home},{i + 1},{_POS[i]}'
        for i, n in enumerate(_NAMES)
    ]


def _roster(team: str, year: int) -> str:
    rows = [
        f"{team.lower()}p{i + 1},{n},{team[0]},R,R,{team},{_POS[i]}" for i, n in enumerate(_NAMES)
    ]
    del year  # rosters are per season by file name; the content is the same here
    return "\n".join(rows) + "\n"


def game(year: int, home: str, away: str, mmdd: str, *, comment: bool = False) -> str:
    """One complete, valid game in Retrosheet's event-file format (home bats second)."""
    ap = away.lower()
    lines = [
        f"id,{home}{year}{mmdd}0",
        "version,2",
        f"info,visteam,{away}",
        f"info,hometeam,{home}",
        f"info,date,{year}/{mmdd[:2]}/{mmdd[2:]}",
        "info,number,0",
        "info,starttime,1:05PM",
        "info,daynight,day",
        "info,usedh,false",
        "info,innings,9",
        *_starts(away, 0),
        *_starts(home, 1),
        f"play,1,0,{ap}p1,22,CFBX,8",
        f"play,1,0,{ap}p2,00,X,63",
        f"play,1,0,{ap}p3,11,CBX,S7",
        f"play,1,0,{ap}p4,00,X,K",
    ]
    if comment:
        lines.append('com,"a made-up game"')
    lines.append(f"data,er,{home.lower()}p9,0")
    return "\n".join(lines) + "\n"


FILES: dict[str, str] = {
    "2010AAA.EVN": game(2010, "AAA", "BBB", "0405", comment=True)
    + game(2010, "AAA", "BBB", "0406", comment=True),
    "2010BBB.EVA": game(2010, "BBB", "AAA", "0407"),
    "2011AAA.EVN": game(2011, "AAA", "BBB", "0410"),
    "TEAM2010": "AAA,A,Aville,Aces\nBBB,A,Bville,Bees\n",
    "TEAM2011": "AAA,A,Aville,Aces\nBBB,A,Bville,Bees\n",
    **{f"{t}{y}.ROS": _roster(t, y) for t in ("AAA", "BBB") for y in (2010, 2011)},
}


def decade_zip(extra: dict[str, bytes] | None = None) -> bytes:
    """The made-up 2010s decade archive (the file the downloader would fetch)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, text in FILES.items():
            zf.writestr(name, text)
        for name, data in (extra or {}).items():
            zf.writestr(name, data)
    return buf.getvalue()


def fetch(url: str) -> bytes:
    """A stand-in for the network: every download is the made-up decade archive."""
    return decade_zip()
