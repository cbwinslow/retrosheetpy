# Cloud Warehouses via dlt

[dlt (Data Load Tool)](https://dlthub.com) is an open-source library that automates schema extraction, typing, and resilient data loading into enterprise data warehouses and relational databases.

`retrosheetpy` exposes a dedicated `@dlt.source` generator and the top-level helper `rs.to_dlt()` to stream Retrosheet datasets directly into **PostgreSQL, Snowflake, Google BigQuery, Databricks, Redshift, and DuckDB**.

---

## Out-of-the-Box Ingestion

`dlt` is included directly in `retrosheetpy`'s core dependencies. `retrosheetpy`'s dlt sources yield native PyArrow Tables (`pyarrow.Table`) directly into `dlt` without converting rows to Python dictionaries, ensuring zero-copy throughput and strict type preservation into destination databases.

```bash
pip install retrosheetpy
```

---

## Direct Pipeline Execution (`to_dlt`)

To load multiple seasons directly into a database with a single call:

```python
import retrosheetpy as rs

# Stream 2023-2024 rosters, ballparks, and game logs into PostgreSQL
info = rs.to_dlt(
    destination="postgresql://postgres:postgres@localhost:5432/retrosheet",
    years=[2023, 2024],
    datasets=["rosters", "parks", "gamelogs"],
    dataset_name="public",
)

print(info)
```

---

## Custom dlt Pipelines & Sources

For fine-grained control over incremental loading, staging credentials, and write dispositions (e.g. `append` vs `replace`):

```python
import dlt
from retrosheetpy.sink.dlt_sink import retrosheet_source

# 1. Initialize custom dlt pipeline
pipeline = dlt.pipeline(
    pipeline_name="mlb_production_warehouse",
    destination=dlt.destinations.snowflake(),
    dataset_name="retrosheet_raw",
)

# 2. Instantiate retrosheet source for specific datasets
source = retrosheet_source(
    years=[2024],
    datasets=["events", "gamelogs", "rosters", "parks"],
)

# 3. Run pipeline with replace or append disposition
load_info = pipeline.run(source, write_disposition="replace")
print(load_info)
```

---

## Handling PostgreSQL Schemas

> [!TIP]
> PostgreSQL prohibits custom schemas starting with `pg_`. When configuring `dlt`, explicitly pass `dataset_name="public"` or a custom schema name such as `dataset_name="retrosheet"` to avoid schema naming conflicts.
