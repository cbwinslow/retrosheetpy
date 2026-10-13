from pathlib import Path

import pyarrow as pa

from retrosheetpy.parse.bio import BioParser
from retrosheetpy.parse.ejections import EjectionParser
from retrosheetpy.parse.events import EventParser
from retrosheetpy.parse.gamelogs import GameLogParser
from retrosheetpy.parse.parks import ParkParser
from retrosheetpy.parse.rosters import RosterParser
from retrosheetpy.parse.schedules import ScheduleParser
from retrosheetpy.parse.transactions import TransactionParser


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


def test_parse_schedules(tmp_path: Path) -> None:
    sked_file = tmp_path / "2024schedule.csv"
    sked_file.write_text(
        "Date,Num,Day,Visitor,League,Game,Home,League,Game,Day/Night,Location,Postponed,Makeup\n"
        "20240320,0,Wednesday,LAN,NL,1,SDN,NL,1,n,SEO01,,\n"
        "20240321,0,Thursday,SDN,NL,2,LAN,NL,2,n,SEO01,,\n"
    )
    parser = ScheduleParser()
    table = parser.parse_file(sked_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert table["vis_team"].to_pylist() == ["LAN", "SDN"]
    assert table["home_team"].to_pylist() == ["SDN", "LAN"]


def test_parse_bio(tmp_path: Path) -> None:
    bio_file = tmp_path / "biofile0.csv"
    bio_file.write_text(
        "id,lastname,usename,fullname,birthdate,birthcity,birthstate,birthcountry,deathdate,deathcity,deathstate,deathcountry,cemetery,cem_city,cem_state,cem_ctry,cem_note,birthname,altname,debut_p,last_p,debut_c,last_c,debut_m,last_m,debut_u,last_u,bats,throws,height,weight,HOF\n"
        "aardd001,Aardsma,David,David Allan Aardsma,19811227,Denver,Colorado,USA,,,,,,,,,,,,20040406,20150823,,,,,,,R,R,77,200,\n"
    )
    parser = BioParser()
    table = parser.parse_file(bio_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table["player_id"].to_pylist() == ["aardd001"]
    assert table["height_inches"].to_pylist() == [77]
    assert table["weight_lbs"].to_pylist() == [200]


def test_parse_ejections(tmp_path: Path) -> None:
    ej_file = tmp_path / "ejections.csv"
    ej_file.write_text(
        "GAMEID,DATE,DH,EJECTEE,EJECTEENAME,TEAM,JOB,UMPIRE,UMPIRENAME,INNING,REASON\n"
        'CL6188905250,05/25/1889, ,orr-d101,"Dave Orr",CL6,P,goldf101,"Fred Goldsmith",-1,"Call at 3B"\n'
    )
    parser = EjectionParser()
    table = parser.parse_file(ej_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table["ejectee_id"].to_pylist() == ["orr-d101"]
    assert table["umpire_name"].to_pylist() == ["Fred Goldsmith"]


def test_parse_transactions(tmp_path: Path) -> None:
    tr_file = tmp_path / "tran.txt"
    tr_file.write_text(
        '"20030603",,,"20030629",,1,"aardd001","Da","","","SFN","NL",,1,22,"Drafted"\n'
    )
    parser = TransactionParser()
    table = parser.parse_file(tr_file)
    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table["player_id"].to_pylist() == ["aardd001"]
    assert table["to_team"].to_pylist() == ["SFN"]


def test_parse_events_via_chadwick(tmp_path: Path) -> None:
    fake_eva = (
        b"id,BOS202404010\n"
        b"info,date,2024/04/01\n"
        b"info,hometeam,BOS\n"
        b"info,visteam,BAL\n"
        b"start,play01,Batter One,0,1,4\n"
        b"start,pitch01,Pitcher One,1,1,1\n"
        b"play,1,0,play01,00,,S\n"
        b"data,er,pitch01,0\n"
    )
    target_eva = tmp_path / "2024BOS.EVA"
    target_eva.write_bytes(fake_eva)

    parser = EventParser()
    table = parser.parse_files([target_eva], year=2024)

    assert isinstance(table, pa.Table)
    assert table.num_rows == 1
    assert table["GAME_ID"].to_pylist() == ["BOS202404010"]
    assert table["INN_CT"].to_pylist() == [1]
    assert table["EVENT_CD"].to_pylist() == [20]  # Single (S) -> EVENT_CD 20
    assert pa.types.is_string(table.schema.field("GAME_ID").type)
    assert pa.types.is_int16(table.schema.field("INN_CT").type)
    assert pa.types.is_int16(table.schema.field("EVENT_CD").type)
