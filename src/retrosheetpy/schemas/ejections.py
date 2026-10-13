"""PyArrow schema definition for Retrosheet official ejections log."""

import pyarrow as pa

EJECTION_SCHEMA = pa.schema(
    [
        pa.field("game_id", pa.string(), nullable=True),
        pa.field("date", pa.date32(), nullable=True),
        pa.field("dh", pa.string(), nullable=True),
        pa.field("ejectee_id", pa.string(), nullable=False),
        pa.field("ejectee_name", pa.string(), nullable=True),
        pa.field("team_id", pa.string(), nullable=True),
        pa.field("job", pa.string(), nullable=True),
        pa.field("umpire_id", pa.string(), nullable=True),
        pa.field("umpire_name", pa.string(), nullable=True),
        pa.field("inning", pa.int8(), nullable=True),
        pa.field("reason", pa.string(), nullable=True),
    ]
)
