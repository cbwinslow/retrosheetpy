"""Parser for Retrosheet Player Transactions (tran.txt)."""

from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.transactions import TRANSACTION_SCHEMA
from retrosheetpy.schemas.types import parse_date, parse_int


class TransactionParser:
    """Parses Retrosheet tran.txt into a strongly-typed PyArrow Table."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses tran.txt into an Arrow Table conforming to TRANSACTION_SCHEMA."""
        records: list[dict[str, object]] = []

        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 7:
                    continue

                primary_date = parse_date(row[0]) if len(row) > 0 else None
                time_val = row[1].strip() if len(row) > 1 and row[1].strip() else None
                approx_ind = row[2].strip() if len(row) > 2 and row[2].strip() else None
                sec_date = parse_date(row[3]) if len(row) > 3 else None
                approx_sec = row[4].strip() if len(row) > 4 and row[4].strip() else None
                tran_id = row[5].strip() if len(row) > 5 else ""
                player_id = row[6].strip() if len(row) > 6 else ""
                tran_type = row[7].strip() if len(row) > 7 and row[7].strip() else None
                from_team = row[8].strip() if len(row) > 8 and row[8].strip() else None
                from_lg = row[9].strip() if len(row) > 9 and row[9].strip() else None
                to_team = row[10].strip() if len(row) > 10 and row[10].strip() else None
                to_lg = row[11].strip() if len(row) > 11 and row[11].strip() else None
                draft_type = row[12].strip() if len(row) > 12 and row[12].strip() else None
                draft_round = parse_int(row[13]) if len(row) > 13 else None
                pick_num = parse_int(row[14]) if len(row) > 14 else None
                info = row[15].strip() if len(row) > 15 and row[15].strip() else None

                records.append(
                    {
                        "primary_date": primary_date,
                        "time": time_val,
                        "approx_indicator": approx_ind,
                        "secondary_date": sec_date,
                        "approx_indicator_sec": approx_sec,
                        "transaction_id": tran_id,
                        "player_id": player_id,
                        "type": tran_type,
                        "from_team": from_team,
                        "from_league": from_lg,
                        "to_team": to_team,
                        "to_league": to_lg,
                        "draft_type": draft_type,
                        "draft_round": draft_round,
                        "pick_number": pick_num,
                        "info": info,
                    }
                )

        if not records:
            return pa.Table.from_batches([], schema=TRANSACTION_SCHEMA)

        arrays = []
        for field in TRANSACTION_SCHEMA:
            col_vals = [r.get(field.name) for r in records]
            arrays.append(pa.array(col_vals, type=field.type))

        return pa.Table.from_arrays(arrays, schema=TRANSACTION_SCHEMA)
