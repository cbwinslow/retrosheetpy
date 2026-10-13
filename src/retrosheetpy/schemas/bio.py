"""PyArrow schema definition for Retrosheet master biographical database."""

import pyarrow as pa

BIO_SCHEMA = pa.schema(
    [
        pa.field("player_id", pa.string(), nullable=False),
        pa.field("last_name", pa.string(), nullable=True),
        pa.field("use_name", pa.string(), nullable=True),
        pa.field("full_name", pa.string(), nullable=True),
        pa.field("birth_date", pa.date32(), nullable=True),
        pa.field("birth_city", pa.string(), nullable=True),
        pa.field("birth_state", pa.string(), nullable=True),
        pa.field("birth_country", pa.string(), nullable=True),
        pa.field("death_date", pa.date32(), nullable=True),
        pa.field("death_city", pa.string(), nullable=True),
        pa.field("death_state", pa.string(), nullable=True),
        pa.field("death_country", pa.string(), nullable=True),
        pa.field("cemetery", pa.string(), nullable=True),
        pa.field("cem_city", pa.string(), nullable=True),
        pa.field("cem_state", pa.string(), nullable=True),
        pa.field("cem_country", pa.string(), nullable=True),
        pa.field("cem_note", pa.string(), nullable=True),
        pa.field("birth_name", pa.string(), nullable=True),
        pa.field("alt_name", pa.string(), nullable=True),
        pa.field("debut_player", pa.date32(), nullable=True),
        pa.field("last_player", pa.date32(), nullable=True),
        pa.field("debut_coach", pa.date32(), nullable=True),
        pa.field("last_coach", pa.date32(), nullable=True),
        pa.field("debut_manager", pa.date32(), nullable=True),
        pa.field("last_manager", pa.date32(), nullable=True),
        pa.field("debut_umpire", pa.date32(), nullable=True),
        pa.field("last_umpire", pa.date32(), nullable=True),
        pa.field("bats", pa.string(), nullable=True),
        pa.field("throws", pa.string(), nullable=True),
        pa.field("height_inches", pa.int16(), nullable=True),
        pa.field("weight_lbs", pa.int16(), nullable=True),
        pa.field("hof", pa.string(), nullable=True),
    ]
)
