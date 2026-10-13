# Biographical Encyclopedia

Retrosheet maintains the authoritative biographical encyclopedia of all players, managers, coaches, and umpires who have appeared in Major League Baseball, including historical Negro Leagues participants.

The master dataset (`biofile.zip` containing `biofile0.csv`) provides 32 standardized, strongly-typed fields including vital records, debut and final appearance dates, physical attributes, cemetery records, and Hall of Fame status.

---

## Python API Usage

```python
import retrosheetpy as rs

# 1. Fetch biographical master into Polars
bio_df = rs.bio(backend="polars")

# Filter Hall of Fame players
hof_players = bio_df.filter(bio_df["hof"].is_not_null())
print(hof_players.select(["player_id", "use_name", "last_name", "debut_player", "hof"]))

# 2. Ingest into DuckDB
rs.to_duckdb("baseball.duckdb", datasets=["bio"])

# 3. Export to Parquet
rs.to_parquet("biofile.parquet", dataset="bio")
```

---

## CLI Usage

```bash
# Download and cache biographical master
retrosheetpy download -s bio

# Export to Parquet or CSV
retrosheetpy export -s bio -f parquet -o biofile.parquet
retrosheetpy export -s bio -f csv -o biofile.csv

# Generate Snowflake SQL DDL
retrosheetpy ddl -s bio --dialect snowflake
```

---

## PyArrow Schema (`BIO_SCHEMA`)

| Column Name | Arrow Type | SQL Dialects | Description |
| :--- | :--- | :--- | :--- |
| `player_id` | `pa.string()` | `VARCHAR` / `STRING` | Primary Retrosheet identifier (e.g. `aaroh101`). |
| `last_name` | `pa.string()` | `VARCHAR` / `STRING` | Legal last name. |
| `use_name` | `pa.string()` | `VARCHAR` / `STRING` | Commonly known first name (e.g. `Hank`). |
| `full_name` | `pa.string()` | `VARCHAR` / `STRING` | Complete legal full name. |
| `birth_date` | `pa.date32()` | `DATE` | Birth date (`YYYY-MM-DD`). |
| `birth_city` | `pa.string()` | `VARCHAR` / `STRING` | City of birth. |
| `birth_state` | `pa.string()` | `VARCHAR` / `STRING` | State/province of birth. |
| `birth_country` | `pa.string()` | `VARCHAR` / `STRING` | Country of birth. |
| `death_date` | `pa.date32()` | `DATE` | Date of death (`YYYY-MM-DD`) if deceased. |
| `death_city` | `pa.string()` | `VARCHAR` / `STRING` | City of death. |
| `death_state` | `pa.string()` | `VARCHAR` / `STRING` | State/province of death. |
| `death_country` | `pa.string()` | `VARCHAR` / `STRING` | Country of death. |
| `cemetery` | `pa.string()` | `VARCHAR` / `STRING` | Cemetery or internment facility name. |
| `cem_city` | `pa.string()` | `VARCHAR` / `STRING` | Cemetery city location. |
| `cem_state` | `pa.string()` | `VARCHAR` / `STRING` | Cemetery state/province. |
| `cem_country` | `pa.string()` | `VARCHAR` / `STRING` | Cemetery country. |
| `cem_note` | `pa.string()` | `VARCHAR` / `STRING` | Grave location or internment notes. |
| `birth_name` | `pa.string()` | `VARCHAR` / `STRING` | Name given at birth if different. |
| `alt_name` | `pa.string()` | `VARCHAR` / `STRING` | Nicknames or alternative spellings. |
| `debut_player` | `pa.date32()` | `DATE` | First Major League appearance as a player. |
| `last_player` | `pa.date32()` | `DATE` | Final Major League appearance as a player. |
| `debut_coach` | `pa.date32()` | `DATE` | First appearance as an MLB coach. |
| `last_coach` | `pa.date32()` | `DATE` | Final appearance as an MLB coach. |
| `debut_manager` | `pa.date32()` | `DATE` | First appearance as an MLB manager. |
| `last_manager` | `pa.date32()` | `DATE` | Final appearance as an MLB manager. |
| `debut_umpire` | `pa.date32()` | `DATE` | First appearance as an MLB umpire. |
| `last_umpire` | `pa.date32()` | `DATE` | Final appearance as an MLB umpire. |
| `bats` | `pa.string()` | `VARCHAR` / `STRING` | Batting hand (`R`, `L`, `B`). |
| `throws` | `pa.string()` | `VARCHAR` / `STRING` | Throwing hand (`R`, `L`). |
| `height_inches` | `pa.int16()` | `SMALLINT` / `INT64` | Player height in inches (e.g. `74` for 6'2"). |
| `weight_lbs` | `pa.int16()` | `SMALLINT` / `INT64` | Weight in pounds (e.g. `205`). |
| `hof` | `pa.string()` | `VARCHAR` / `STRING` | Hall of Fame induction year or indicator. |
