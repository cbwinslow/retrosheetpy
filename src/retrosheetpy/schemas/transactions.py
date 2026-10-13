"""PyArrow schema definition for Retrosheet player transactions database."""

import pyarrow as pa

TRANSACTION_SCHEMA = pa.schema(
    [
        pa.field("primary_date", pa.date32(), nullable=True),
        pa.field("time", pa.string(), nullable=True),
        pa.field("approx_indicator", pa.string(), nullable=True),
        pa.field("secondary_date", pa.date32(), nullable=True),
        pa.field("approx_indicator_sec", pa.string(), nullable=True),
        pa.field("transaction_id", pa.string(), nullable=False),
        pa.field("player_id", pa.string(), nullable=False),
        pa.field("type", pa.string(), nullable=True),
        pa.field("from_team", pa.string(), nullable=True),
        pa.field("from_league", pa.string(), nullable=True),
        pa.field("to_team", pa.string(), nullable=True),
        pa.field("to_league", pa.string(), nullable=True),
        pa.field("draft_type", pa.string(), nullable=True),
        pa.field("draft_round", pa.int16(), nullable=True),
        pa.field("pick_number", pa.int16(), nullable=True),
        pa.field("info", pa.string(), nullable=True),
    ]
)
