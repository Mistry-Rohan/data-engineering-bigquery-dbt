# Architecture And Repo Structure

## Overview

This project builds an end-to-end NYC taxi data pipeline on GCP using:

- NYC TLC parquet files as the source
- Google Cloud Storage as the raw landing zone
- Cloud Composer as the managed Airflow orchestrator
- BigQuery as the warehouse
- dbt as the transformation layer for silver and gold models

The repository is a single monorepo that keeps orchestration, transformation,
and infrastructure code together while still separating concerns cleanly.

## End-To-End Flow

1. A monthly Airflow DAG resolves the taxi type and logical month to ingest.
2. The DAG downloads the monthly parquet file directly from the TLC source.
3. The file is uploaded to a raw GCS path partitioned by taxi type, year, and month.
4. Airflow loads that parquet file from GCS into a native BigQuery bronze table.
5. dbt reads the bronze tables and builds silver cleanup models.
6. dbt builds gold marts for reporting and downstream analytics.

## Layer Ownership

### Raw

- Storage: GCS
- Purpose: exact landed copies of source parquet files
- Owner: Airflow ingestion

Example path:

```text
raw/yellow/year=2026/month=01/yellow_tripdata_2026-01.parquet
```

### Bronze

- Storage: BigQuery
- Purpose: native landed tables loaded from raw parquet files
- Owner: Airflow ingestion

Example tables:

- `taxi_bronze.yellow_tripdata`
- `taxi_bronze.green_tripdata`
- `taxi_bronze.fhv_tripdata`
- `taxi_bronze.hvfhv_tripdata`

### Silver

- Storage: BigQuery
- Purpose: cleaned and standardized warehouse models
- Owner: dbt

Current silver models:

- `stg_yellow_tripdata`
- `stg_green_tripdata`
- `int_trips_unioned`

### Gold

- Storage: BigQuery
- Purpose: analytics-ready marts and facts
- Owner: dbt

Current gold models:

- `fct_taxi_trips`
- `fct_monthly_taxi_metrics`

## Current Repository Tree

```text
bigquery-dbt-project/
|-- .github/
|   `-- workflows/
|       `-- ci-cd.yml
|-- README.md
|-- .env.example
|-- docs/
|   |-- architecture.md
|   |-- runtime_setup.md
|   `-- dbt_auth_setup.md
|-- composer/
|   |-- dags/
|   |   `-- taxi_trip_pipeline.py
|   |-- include/
|   |   |-- config/
|   |   |   `-- pipeline_config.yaml
|   |   `-- scripts/
|   |       `-- taxi_download.py
|   |-- plugins/
|   |   `-- .gitkeep
|   `-- requirements.txt
|-- dbt/
|   |-- dbt_project.yml
|   |-- macros/
|   |   |-- build_trip_id.sql
|   |   |-- generate_schema_name.sql
|   |   `-- get_payment_type_description.sql
|   |-- models/
|   |   |-- bronze/
|   |   |   `-- _sources.yml
|   |   |-- silver/
|   |   |   |-- staging/
|   |   |   |   |-- schema.yml
|   |   |   |   |-- stg_green_tripdata.sql
|   |   |   |   `-- stg_yellow_tripdata.sql
|   |   |   `-- intermediate/
|   |   |       `-- int_trips_unioned.sql
|   |   `-- gold/
|   |       |-- schema.yml
|   |       |-- fct_taxi_trips.sql
|   |       `-- fct_monthly_taxi_metrics.sql
|   |-- profiles/
|   |   |-- README.md
|   |   `-- profiles.yml.example
|   |-- seeds/
|   |   `-- taxi_zone_lookup.csv
|   `-- tests/
|       |-- assert_valid_trip_durations.sql
|       `-- generic/
|           `-- test_positive_values.sql
|-- infra/
|   `-- terraform/
|       |-- main.tf
|       |-- variables.tf
|       `-- outputs.tf
|-- local_airflow/
|   |-- docker-compose.yml
|   `-- .env.example
`-- scripts/
    |-- deploy_composer.ps1
    `-- run_dbt_local.ps1
```

## What Goes Where

### `composer/`

Contains code that must be available to the Cloud Composer environment.

- `dags/`: DAG entrypoints only
- `include/scripts/`: shared ingestion helpers
- `include/config/`: static pipeline defaults
- `requirements.txt`: Composer Python package dependencies

The DAG should stay orchestration-focused and import helper logic from
`include/scripts/`.

### `dbt/`

Contains the analytics engineering layer.

- `models/bronze/`: source declarations for native bronze tables
- `models/silver/`: cleanup, standardization, and integration models
- `models/gold/`: final marts and facts
- `macros/`: reusable SQL helpers
- `tests/`: singular and generic dbt tests

### `infra/terraform/`

Intended to provision:

- raw GCS bucket
- BigQuery bronze, silver, and gold datasets
- Composer environment
- service accounts and IAM bindings

### `local_airflow/`

For local DAG validation and development before deploying to Composer.

## Why Bronze Is Not A dbt Layer Here

This project intentionally keeps bronze ingestion outside dbt.

- Airflow owns raw file movement and native BigQuery loads
- dbt starts at bronze as a source layer
- dbt then builds silver and gold

That split keeps ingestion operational concerns in Airflow and warehouse
transformations in dbt.

## Orchestration Model

The current Composer DAG is designed around monthly catchup.

For each taxi type and month it:

1. downloads the parquet file
2. uploads it to raw GCS
3. loads it into the matching native bronze table
4. cleans up the local worker file

The next orchestration step is to add dbt execution for silver and gold after
bronze completion.
