from pathlib import Path

import pyarrow as pa

from retrosheetpy.parse.events import EventParser
from retrosheetpy.parse.gamelogs import GameLogParser
from retrosheetpy.parse.parks import ParkParser
from retrosheetpy.parse.rosters import RosterParser


def test_parse_gamelogs(tmp_path: Path) -> None:
    gl_file = tmp_path / "gl2024.txt"
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    gl_file.write_text(f"{line}\n{line}\n")

    parser = GameLogParser()
    table = parser.parse_file(gl_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table.schema.field("attendance").type == pa.int32()
    assert table["attendance"].to_pylist() == [15952, 15952]
    assert table["visiting_team"].to_pylist() == ["LAN", "LAN"]


def test_parse_rosters(tmp_path: Path) -> None:
    ros_file = tmp_path / "NYA2024.ROS"
    ros_file.write_text("judge001,Judge,Aaron,R,R,NYA,OF\nsoot001,Soto,Juan,L,R,NYA,OF\n")

    parser = RosterParser()
    table = parser.parse_files([ros_file], year=2024)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table["last_name"].to_pylist() == ["Judge", "Soto"]
    assert table["bats"].to_pylist() == ["R", "L"]


def test_parse_parks(tmp_path: Path) -> None:
    park_file = tmp_path / "parkcode.txt"
    park_file.write_text(
        "PARKID,NAME,AKA,CITY,STATE,START,END,LEAGUE,NOTES\n"
        "BOS07,Fenway Park,,Boston,MA,04/20/1912,,AL,\n"
        "NYC21,Yankee Stadium,,Bronx,NY,04/16/2009,,AL,\n"
    )

    parser = ParkParser()
    table = parser.parse_file(park_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table["park_id"].to_pylist() == ["BOS07", "NYC21"]


def test_parse_events_via_chadwick(tmp_path: Path) -> None:
    # Use real test fixtures from chadwickpy if available
    fixture_dir = Path("C:/Users/blain/projects/chadwickpy/tests/fixtures/events")
    roster_dir = Path("C:/Users/blain/projects/chadwickpy/tests/reference/rosters/regular_2007")

    if fixture_dir.exists() and roster_dir.exists():
        # Copy roster and event files to tmp_path
        for r in roster_dir.iterdir():
            (tmp_path / r.name).write_bytes(r.read_bytes())
        evt_target = tmp_path / "2007BOS.EVA"
        evt_target.write_bytes((fixture_dir / "regular_2007.evt").read_bytes())

        parser = EventParser()
        table = parser.parse_files([evt_target], year=2007)
        assert isinstance(table, pa.Table)
        assert table.num_rows > 0
        assert table.schema.field("GAME_ID").type == pa.string()
        assert table.schema.field("INN_CT").type == pa.int16()
        assert table.schema.field("EVENT_CD").type == pa.int16()
