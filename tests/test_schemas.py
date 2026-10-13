import pyarrow as pa

from retrosheetpy.schemas.events import EVENT_SCHEMA, cast_event_row
from retrosheetpy.schemas.gamelogs import GAMELOG_SCHEMA, parse_gamelog_line
from retrosheetpy.schemas.rosters import parse_roster_line


def test_event_schema_types() -> None:
    assert len(EVENT_SCHEMA) == 164
    assert EVENT_SCHEMA.field("GAME_ID").type == pa.string()
    assert EVENT_SCHEMA.field("INN_CT").type == pa.int16()
    assert EVENT_SCHEMA.field("OUTS_CT").type == pa.int8()
    assert EVENT_SCHEMA.field("BAT_HOME_ID").type == pa.int8()
    assert EVENT_SCHEMA.field("EVENT_CD").type == pa.int16()
    assert EVENT_SCHEMA.field("LEADOFF_FL").type == pa.bool_()


def test_cast_event_row() -> None:
    # Sample raw row as produced by cwevent (all strings)
    raw = {
        "GAME_ID": "NYA202404010",
        "AWAY_TEAM_ID": "TOR",
        "INN_CT": "1",
        "BAT_HOME_ID": "0",
        "OUTS_CT": "0",
        "BALLS_CT": "3",
        "STRIKES_CT": "2",
        "PITCH_SEQ_TX": "BBCCFB",
        "AWAY_SCORE_CT": "0",
        "HOME_SCORE_CT": "0",
        "BAT_ID": "spring01",
        "BAT_HAND_CD": "R",
        "EVENT_TX": "W",
        "LEADOFF_FL": "T",
        "EVENT_CD": "14",
    }
    typed = cast_event_row(raw)
    assert typed["GAME_ID"] == "NYA202404010"
    assert typed["INN_CT"] == 1
    assert typed["BAT_HOME_ID"] == 0
    assert typed["OUTS_CT"] == 0
    assert typed["BALLS_CT"] == 3
    assert typed["STRIKES_CT"] == 2
    assert typed["LEADOFF_FL"] is True
    assert typed["EVENT_CD"] == 14


def test_gamelog_schema_types() -> None:
    assert len(GAMELOG_SCHEMA) == 161
    assert GAMELOG_SCHEMA.field("date").type == pa.date32()
    assert GAMELOG_SCHEMA.field("visiting_score").type == pa.int16()
    assert GAMELOG_SCHEMA.field("home_score").type == pa.int16()
    assert GAMELOG_SCHEMA.field("attendance").type == pa.int32()


def test_parse_gamelog_line() -> None:
    # 2024 opening game sample line (161 comma-delimited fields)
    line = '20240328,0,Thu,LAN,NL,1,SDN,NL,1,5,2,54,D,,,,SEO01,15952,185,"000101003","000000020",37,11,1,0,0,5,0,0,0,1,0,3,1,0,0,0,8,6,2,2,0,0,27,11,1,0,0,0,31,4,0,0,0,2,0,0,1,0,0,7,2,0,0,0,9,5,5,5,1,0,27,9,2,0,0,0,hp_id,hp_name,1b_id,1b_name,2b_id,2b_name,3b_id,3b_name,lf_id,lf_name,rf_id,rf_name,v_mgr_id,v_mgr_name,h_mgr_id,h_mgr_name,w_pit_id,w_pit_name,l_pit_id,l_pit_name,s_pit_id,s_pit_name,gwrbi_id,gwrbi_name,v_sp_id,v_sp_name,h_sp_id,h_sp_name,v_b1_id,v_b1_name,8,v_b2_id,v_b2_name,6,v_b3_id,v_b3_name,7,v_b4_id,v_b4_name,3,v_b5_id,v_b5_name,9,v_b6_id,v_b6_name,4,v_b7_id,v_b7_name,5,v_b8_id,v_b8_name,2,v_b9_id,v_b9_name,1,h_b1_id,h_b1_name,8,h_b2_id,h_b2_name,6,h_b3_id,h_b3_name,7,h_b4_id,h_b4_name,3,h_b5_id,h_b5_name,9,h_b6_id,h_b6_name,4,h_b7_id,h_b7_name,5,h_b8_id,h_b8_name,2,h_b9_id,h_b9_name,1,additional_info,acquisition_info'
    record = parse_gamelog_line(line)
    assert record["visiting_team"] == "LAN"
    assert record["home_team"] == "SDN"
    assert record["visiting_score"] == 5
    assert record["home_score"] == 2
    assert record["attendance"] == 15952
    assert record["time_minutes"] == 185
    assert record["visiting_hits"] == 11


def test_parse_roster_line() -> None:
    line = "judge001,Judge,Aaron,R,R,NYA,OF"
    record = parse_roster_line(line, year=2024)
    assert record["player_id"] == "judge001"
    assert record["last_name"] == "Judge"
    assert record["first_name"] == "Aaron"
    assert record["bats"] == "R"
    assert record["throws"] == "R"
    assert record["team_id"] == "NYA"
    assert record["position"] == "OF"
    assert record["year"] == 2024
