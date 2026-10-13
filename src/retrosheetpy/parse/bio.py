"""Parser for Retrosheet Master Biographical Database (biofile0.csv)."""

from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa

from retrosheetpy.schemas.bio import BIO_SCHEMA
from retrosheetpy.schemas.types import parse_date, parse_int


class BioParser:
    """Parses Retrosheet biographical files into a strongly-typed PyArrow Table."""

    def parse_file(self, path: Path) -> pa.Table:
        """Parses biofile0.csv into an Arrow Table conforming to BIO_SCHEMA."""
        records: list[dict[str, object]] = []

        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = None
            for row in reader:
                if not row:
                    continue
                if header is None:
                    header = [c.strip().lower() for c in row]
                    continue

                row_dict = dict(zip(header, row, strict=False))
                # Map fields to BIO_SCHEMA
                records.append(
                    {
                        "player_id": row_dict.get("id") or row_dict.get("playerid") or "",
                        "last_name": row_dict.get("lastname") or row_dict.get("last") or None,
                        "use_name": row_dict.get("usename") or row_dict.get("first") or None,
                        "full_name": row_dict.get("fullname") or row_dict.get("birth.name") or None,
                        "birth_date": parse_date(row_dict.get("birthdate")),
                        "birth_city": row_dict.get("birthcity")
                        or row_dict.get("birth.city")
                        or None,
                        "birth_state": row_dict.get("birthstate")
                        or row_dict.get("birth.state")
                        or None,
                        "birth_country": row_dict.get("birthcountry")
                        or row_dict.get("birth.country")
                        or None,
                        "death_date": parse_date(row_dict.get("deathdate")),
                        "death_city": row_dict.get("deathcity")
                        or row_dict.get("death.city")
                        or None,
                        "death_state": row_dict.get("deathstate")
                        or row_dict.get("death.state")
                        or None,
                        "death_country": row_dict.get("deathcountry")
                        or row_dict.get("death.country")
                        or None,
                        "cemetery": row_dict.get("cemetery") or None,
                        "cem_city": row_dict.get("cem_city") or row_dict.get("ceme.city") or None,
                        "cem_state": row_dict.get("cem_state")
                        or row_dict.get("ceme.state")
                        or None,
                        "cem_country": row_dict.get("cem_ctry")
                        or row_dict.get("ceme.country")
                        or None,
                        "cem_note": row_dict.get("cem_note") or row_dict.get("ceme.note") or None,
                        "birth_name": row_dict.get("birthname")
                        or row_dict.get("birth.name")
                        or None,
                        "alt_name": row_dict.get("altname") or row_dict.get("nickname") or None,
                        "debut_player": parse_date(
                            row_dict.get("debut_p") or row_dict.get("play.debut")
                        ),
                        "last_player": parse_date(
                            row_dict.get("last_p") or row_dict.get("play.lastgame")
                        ),
                        "debut_coach": parse_date(
                            row_dict.get("debut_c") or row_dict.get("coach.debut")
                        ),
                        "last_coach": parse_date(
                            row_dict.get("last_c") or row_dict.get("coach.lastgame")
                        ),
                        "debut_manager": parse_date(
                            row_dict.get("debut_m") or row_dict.get("mgr.debut")
                        ),
                        "last_manager": parse_date(
                            row_dict.get("last_m") or row_dict.get("mgr.lastgame")
                        ),
                        "debut_umpire": parse_date(
                            row_dict.get("debut_u") or row_dict.get("ump.debut")
                        ),
                        "last_umpire": parse_date(
                            row_dict.get("last_u") or row_dict.get("ump.lastgame")
                        ),
                        "bats": row_dict.get("bats") or None,
                        "throws": row_dict.get("throws") or None,
                        "height_inches": parse_int(row_dict.get("height")),
                        "weight_lbs": parse_int(row_dict.get("weight")),
                        "hof": row_dict.get("hof") or None,
                    }
                )

        if not records:
            return pa.Table.from_batches([], schema=BIO_SCHEMA)

        arrays = []
        for field in BIO_SCHEMA:
            col_vals = [r.get(field.name) for r in records]
            arrays.append(pa.array(col_vals, type=field.type))

        return pa.Table.from_arrays(arrays, schema=BIO_SCHEMA)
