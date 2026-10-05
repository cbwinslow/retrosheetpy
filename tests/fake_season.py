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


# --- the other Retrosheet archives (postseason, all-star, Negro Leagues, box-score-only) ---------


def box_game(year: int, home: str, away: str, mmdd: str, *, gametype: str = "exhibition") -> str:
    """A made-up game known only from its box score: no ``play`` records, just ``line``/``stat``."""
    lines = [
        f"id,{home}{year}{mmdd}0",
        "version,5",
        f"info,visteam,{away}",
        f"info,hometeam,{home}",
        f"info,date,{year}/{mmdd[:2]}/{mmdd[2:]}",
        "info,number,0",
        f"info,gametype,{gametype}",
        "info,daynight,day",
        "info,timeofgame,95",
        "info,attendance,4000",
        f"info,wp,{home.lower()}p9",
        f"info,lp,{away.lower()}p9",
        "info,save,",
        "line,0,0,0,0,0,0,0,0,2,0",
        "line,1,0,0,0,0,0,0,0,0,1",
        "stat,tline,0,7,1,1,0",
        "stat,tline,1,8,2,0,0",
        *_starts(away, 0),
        *_starts(home, 1),
        'com,"At bats are deduced"',
    ]
    for team, side in ((away, 0), (home, 1)):
        for i in range(9):
            pid = f"{team.lower()}p{i + 1}"
            lines.append(f"stat,bline,{pid},{side},{i + 1},1,4,0,1,0,0,0,0,0,-1,0,0,0,-1,0,-1,-1,0")
    lines += [
        f"stat,pline,{away.lower()}p9,0,1,27,-1,36,6,1,0,0,1,1,1,-1,8,1,0,0,0,-1",
        f"stat,pline,{home.lower()}p9,1,1,27,-1,36,6,1,0,0,2,2,1,-1,4,0,0,0,2,-1",
    ]
    for team, side in ((away, 0), (home, 1)):
        for i in range(9):
            pid = f"{team.lower()}p{i + 1}"
            lines.append(f"stat,dline,{pid},{side},1,{_POS[i]},27,3,5,0,0,0,0")
    return "\n".join(lines) + "\n"


def _zip(members: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, text in members.items():
            zf.writestr(name, text)
    return buf.getvalue()


def _rosters(year: int) -> dict[str, str]:
    return {f"{t}{year}.ROS": _roster(t, year) for t in ("AAA", "BBB")}


# Postseason and All-Star files are named by series (2010WS.EVE), and have their own team lists.
POSTSEASON_GAMES_2010 = 2  # one World Series file with two games; 2011 has one game
ALLSTAR_GAMES_2010 = 1
POST_TEAMS = "AAA,A,Aville,Post Aces\nBBB,A,Bville,Post Bees\n"


def postseason_zip() -> bytes:
    return _zip(
        {
            "2010WS.EVE": game(2010, "AAA", "BBB", "1027") + game(2010, "BBB", "AAA", "1028"),
            "2011WS.EVE": game(2011, "AAA", "BBB", "1026"),
            "TEAM2010": POST_TEAMS,
            "TEAM2011": POST_TEAMS,
            **_rosters(2010),
            **_rosters(2011),
        }
    )


def allstar_zip() -> bytes:
    return _zip(
        {"2010AS.EVE": game(2010, "AAA", "BBB", "0713"), "TEAM2010": POST_TEAMS, **_rosters(2010)}
    )


def negro_zip() -> bytes:
    """Year-named files and no team list at all, like Retrosheet's Negro Leagues archive."""
    return _zip(
        {"1912.EVR": game(1912, "AAA", "BBB", "0824"), "1913.EVR": game(1913, "BBB", "AAA", "0501")}
    )


def negro_box_zip() -> bytes:
    return _zip({"1912.EBR": box_game(1912, "AAA", "BBB", "0824")})


def box_zip() -> bytes:
    """Like 1900sbox.zip: year-named box-score-only files plus rosters and a team list."""
    return _zip(
        {
            "1901.EBN": box_game(1901, "AAA", "BBB", "0426", gametype="regular"),
            "TEAM1901": "AAA,N,Aville,Aces\nBBB,N,Bville,Bees\n",
            **_rosters(1901),
        }
    )


ARCHIVES = {
    "/events/allpost.zip": postseason_zip,
    "/events/allas.zip": allstar_zip,
    "/events/allevr.zip": negro_zip,
    "/events/allebr.zip": negro_box_zip,
    "/events/1900sbox.zip": box_zip,
}


def fetch_any(url: str) -> bytes:
    """A stand-in for the network that answers for every archive retrosheetpy knows."""
    for suffix, build in ARCHIVES.items():
        if url.endswith(suffix):
            return build()
    return decade_zip()
