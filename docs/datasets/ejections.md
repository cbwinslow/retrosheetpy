# Official Ejections Log

Retrosheet's official ejections database records every known ejection in Major League Baseball history (1889–present).

Each ejection entry records the game ID, date, double header flag, ejectee (player, manager, coach, trainer), ejecting umpire, inning, and the official rationale.

---

## Python API Usage

```python
import retrosheetpy as rs

# 1. Fetch ejections log into Polars
ej_df = rs.ejections(backend="polars")

# Top reasons for ejection
print(ej_df.group_by("reason").count().sort("count", descending=True).head(10))

# 2. Ingest into DuckDB
rs.to_duckdb("baseball.duckdb", datasets=["ejections"])

# 3. Export to Parquet
rs.to_parquet("ejections.parquet", dataset="ejections")
```

---

## CLI Usage

```bash
# Download and cache ejections log
retrosheetpy download -s ejections

# Export to Parquet
retrosheetpy export -s ejections -f parquet -o ejections.parquet

# Generate Postgres DDL
retrosheetpy ddl -s ejections --dialect postgres
```

---

## PyArrow Schema (`EJECTION_SCHEMA`)

| Column Name | Arrow Type | SQL Dialects | Description |
| :--- | :--- | :--- | :--- |
| `game_id` | `pa.string()` | `VARCHAR` / `STRING` | Retrosheet Game ID (e.g. `BOS202404010`). |
| `date` | `pa.date32()` | `DATE` | Date of the game (`YYYY-MM-DD`). |
| `dh` | `pa.string()` | `VARCHAR` / `STRING` | Doubleheader game index if applicable. |
| `ejectee_id` | `pa.string()` | `VARCHAR` / `STRING` | Player or personnel Retrosheet ID. |
| `ejectee_name` | `pa.string()` | `VARCHAR` / `STRING` | Full name of the ejected individual. |
| `team_id` | `pa.string()` | `VARCHAR` / `STRING` | Three-letter team abbreviation. |
| `job` | `pa.string()` | `VARCHAR` / `STRING` | Role code (`P` player, `M` manager, `C` coach, etc.). |
| `umpire_id` | `pa.string()` | `VARCHAR` / `STRING` | Retrosheet ID of the ejecting umpire. |
| `umpire_name` | `pa.string()` | `VARCHAR` / `STRING` | Name of the ejecting umpire. |
| `inning` | `pa.int8()` | `SMALLINT` / `INT64` | Inning in which the ejection occurred. |
| `reason` | `pa.string()` | `VARCHAR` / `STRING` | Documented reason (e.g. `Balls and strikes`, `Arguments`). |
