# Player Transactions Database

Retrosheet's transactions database (`tranDB.zip` containing `tran.txt`) tracks player trades, free agent signings, waivers, releases, purchases, and draft picks spanning baseball history.

Each transaction record captures dates, chronological ordering, transaction type codes, trading clubs, draft round, pick numbers, and supplemental terms.

---

## Python API Usage

```python
import retrosheetpy as rs

# 1. Fetch transactions into Polars
tran_df = rs.transactions(backend="polars")

# Trades involving a specific player
ohtani_moves = tran_df.filter(tran_df["player_id"] == "ohtas001")
print(ohtani_moves.select(["primary_date", "type", "from_team", "to_team", "info"]))

# 2. Ingest into DuckDB
rs.to_duckdb("baseball.duckdb", datasets=["transactions"])

# 3. Export to Parquet
rs.to_parquet("transactions.parquet", dataset="transactions")
```

---

## CLI Usage

```bash
# Download and cache transactions archive
retrosheetpy download -s transactions

# Export to Parquet
retrosheetpy export -s transactions -f parquet -o transactions.parquet

# Generate DDL
retrosheetpy ddl -s transactions --dialect postgres
```

---

## PyArrow Schema (`TRANSACTION_SCHEMA`)

| Column Name | Arrow Type | SQL Dialects | Description |
| :--- | :--- | :--- | :--- |
| `primary_date` | `pa.date32()` | `DATE` | Effective transaction date (`YYYY-MM-DD`). |
| `time` | `pa.string()` | `VARCHAR` / `STRING` | Chronological ordering flag (`1` between games, `2` after games). |
| `approx_indicator` | `pa.string()` | `VARCHAR` / `STRING` | `@` if primary date is approximate. |
| `secondary_date` | `pa.date32()` | `DATE` | Associated secondary date (e.g. trade completion date). |
| `approx_indicator_sec` | `pa.string()` | `VARCHAR` / `STRING` | `@` if secondary date is approximate. |
| `transaction_id` | `pa.string()` | `VARCHAR` / `STRING` | Unique transaction record identifier. |
| `player_id` | `pa.string()` | `VARCHAR` / `STRING` | Retrosheet player identifier. |
| `type` | `pa.string()` | `VARCHAR` / `STRING` | Transaction type code (`T` trade, `F` free agent, `D` draft, etc.). |
| `from_team` | `pa.string()` | `VARCHAR` / `STRING` | Relinquishing team abbreviation. |
| `from_league` | `pa.string()` | `VARCHAR` / `STRING` | Relinquishing league. |
| `to_team` | `pa.string()` | `VARCHAR` / `STRING` | Acquiring team abbreviation. |
| `to_league` | `pa.string()` | `VARCHAR` / `STRING` | Acquiring league. |
| `draft_type` | `pa.string()` | `VARCHAR` / `STRING` | Amateur, rule 5, or expansion draft code. |
| `draft_round` | `pa.int16()` | `SMALLINT` / `INT64` | Draft round number. |
| `pick_number` | `pa.int16()` | `SMALLINT` / `INT64` | Overall draft pick number. |
| `info` | `pa.string()` | `VARCHAR` / `STRING` | Supplemental trade notes and conditions. |
