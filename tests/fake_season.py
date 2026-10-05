"""A made-up one-game 2010 season (fictional teams) for offline tests. Not Retrosheet data."""

import io
import zipfile

_NAMES = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
_POS = [8, 4, 3, 7, 9, 5, 6, 2, 1]


def _starts(team: str, home: int) -> list[str]:
    return [
        f'start,{team.lower()}p{i + 1},"{team} {n}",{home},{i + 1},{_POS[i]}'
        for i, n in enumerate(_NAMES)
    ]


def _roster(team: str) -> str:
    rows = [
        f"{team.lower()}p{i + 1},{n},{team[0]},R,R,{team},{_POS[i]}" for i, n in enumerate(_NAMES)
    ]
    return "\n".join(rows) + "\n"


GAME = (
    "\n".join(
        [
            "id,AAA201004050",
            "version,2",
            "info,visteam,BBB",
            "info,hometeam,AAA",
            "info,date,2010/04/05",
            "info,number,0",
            "info,starttime,1:05PM",
            "info,daynight,day",
            "info,usedh,false",
            "info,innings,9",
            *_starts("BBB", 0),
            *_starts("AAA", 1),
            "play,1,0,bbbp1,22,CFBX,8",
            "play,1,0,bbbp2,00,X,63",
            "play,1,0,bbbp3,11,CBX,S7",
            "play,1,0,bbbp4,00,X,K",
            'com,"a made-up game"',
            "data,er,aaap9,0",
        ]
    )
    + "\n"
)
TEAMS = "AAA,A,Aville,Aces\nBBB,A,Bville,Bees\n"


def decade_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("2010AAA.EVN", GAME)
        zf.writestr("TEAM2010", TEAMS)
        zf.writestr("AAA2010.ROS", _roster("AAA"))
        zf.writestr("BBB2010.ROS", _roster("BBB"))
    return buf.getvalue()
