"""PyArrow schema definition for Retrosheet schedule tables."""

import pyarrow as pa

SCHEDULE_SCHEMA = pa.schema(
    [
        pa.field("date", pa.date32(), nullable=True),
        pa.field("game_num", pa.int8(), nullable=True),
        pa.field("day_of_week", pa.string(), nullable=True),
        pa.field("vis_team", pa.string(), nullable=True),
        pa.field("vis_league", pa.string(), nullable=True),
        pa.field("vis_game_num", pa.int16(), nullable=True),
        pa.field("home_team", pa.string(), nullable=True),
        pa.field("home_league", pa.string(), nullable=True),
        pa.field("home_game_num", pa.int16(), nullable=True),
        pa.field("day_night", pa.string(), nullable=True),
        pa.field("park_id", pa.string(), nullable=True),
        pa.field("postponed", pa.string(), nullable=True),
        pa.field("makeup_date", pa.date32(), nullable=True),
    ]
)
