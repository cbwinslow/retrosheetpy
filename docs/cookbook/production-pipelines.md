# Recipe: Production Pipelines & Orchestration

For data engineers and analytics teams maintaining a production data warehouse (PostgreSQL, Snowflake, BigQuery, or MotherDuck), Retrosheet ingestion should run as an automated, idempotent ELT pipeline.

This guide outlines an end-to-end production pipeline pattern using **`retrosheetpy`**, **SQL DDL**, and **`dlt`**.

---

## Pattern: Schema Setup -> Staging -> Load

```mermaid
sequenceDiagram
    autonumber
    participant Pipeline as Orchestrator (Airflow / Cron)
    participant RS as retrosheetpy
    participant DB as Production Database

    Pipeline->>RS: rs.get_ddl("gamelogs", dialect="postgres")
    RS-->>Pipeline: CREATE TABLE IF NOT EXISTS ...
    Pipeline->>DB: Execute DDL (Idempotent table creation)
    Pipeline->>RS: rs.to_dlt(destination, years=[2024], ...)
    RS->>DB: Stream typed Arrow RecordBatches (0.1s load)
    DB-->>Pipeline: Complete with 0 failed jobs
```

---

## Production Python Script (`sync_retrosheet.py`)

```python
import os
import dlt
import retrosheetpy as rs
from sqlalchemy import create_engine, text

# 1. Connection string from environment variable
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/retrosheet")

# 2. Pre-create strongly-typed tables using DDL generator
engine = create_engine(DB_URI)
with engine.begin() as conn:
    for dataset in ["gamelogs", "rosters", "parks"]:
        ddl = rs.get_ddl(dataset, dialect="postgres")
        conn.execute(text(ddl))

# 3. Stream data via dlt
pipeline = dlt.pipeline(
    pipeline_name="retrosheet_production_sync",
    destination=dlt.destinations.postgres(DB_URI),
    dataset_name="public",
)

# Ingest current season with replace disposition
source = rs.to_dlt(
    destination=dlt.destinations.postgres(DB_URI),
    years=[2024],
    datasets=["gamelogs", "rosters", "parks"],
    dataset_name="public",
)

print("Pipeline synchronization complete!")
```

---

## Running Headless via Cron or Docker

You can run this pipeline inside a lightweight container or scheduled GitHub Action:

```yaml
# .github/workflows/nightly-sync.yml
name: Nightly Retrosheet Sync
on:
  schedule:
    - cron: '0 4 * * *'  # 4:00 AM UTC
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run python sync_retrosheet.py
        env:
          DATABASE_URL: ${{ secrets.PROD_DB_URL }}
```
