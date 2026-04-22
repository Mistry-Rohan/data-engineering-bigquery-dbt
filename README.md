# NYC Taxi Data Pipeline On GCP

End-to-end data pipeline for NYC TLC taxi trip data built with Cloud Composer,
GCS, BigQuery, and dbt.

The project ingests monthly parquet files published by the NYC Taxi and
Limousine Commission, lands them in Google Cloud Storage, loads them into native
BigQuery bronze tables, and then uses dbt to build silver and gold analytics
models.

## What The Project Does

- downloads monthly NYC TLC parquet trip files
- stores raw source files in GCS
- loads native BigQuery bronze tables from parquet files in GCS
- standardizes and cleans taxi trip data into silver models with dbt
- publishes gold marts for reporting and analytics
- keeps orchestration, transformations, and infrastructure code in one repo

## Source Data

- Official NYC TLC trip record data:
  [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

Each file contains one month of trip data. The source is already in parquet
format, so the ingestion path does not include CSV-to-parquet conversion.

## Architecture

This project uses a medallion-style layout with clear ownership per layer:

- `raw` in GCS: landed source parquet files
- `bronze` in BigQuery: native ingestion tables loaded by Airflow
- `silver` in BigQuery: cleaned and standardized dbt models
- `gold` in BigQuery: analytics-ready marts and facts built by dbt

High-level flow:

1. Cloud Composer runs a monthly ingestion DAG.
2. Airflow downloads monthly parquet files from the TLC source.
3. Airflow uploads those files to GCS raw storage.
4. Airflow loads each file into a native BigQuery bronze table.
5. dbt reads bronze tables and builds silver models.
6. dbt builds gold marts for consumption.

The detailed architecture is documented in
[architecture.md](C:/Users/Rohan/bigquery-dbt-project/docs/architecture.md).

## Repository Structure

```text
bigquery-dbt-project/
|-- composer/
|-- dbt/
|-- docs/
|-- infra/
|-- local_airflow/
`-- scripts/
```

Main areas:

- [composer](C:/Users/Rohan/bigquery-dbt-project/composer): Cloud Composer DAGs, helper scripts, and Composer config
- [dbt](C:/Users/Rohan/bigquery-dbt-project/dbt): bronze sources, silver models, gold marts, macros, and tests
- [infra](C:/Users/Rohan/bigquery-dbt-project/infra): planned Terraform scaffolding for GCP resources, not yet fully implemented
- [local_airflow](C:/Users/Rohan/bigquery-dbt-project/local_airflow): local Docker-based Airflow development
- [docs](C:/Users/Rohan/bigquery-dbt-project/docs): architecture, runtime, and dbt auth documentation

## Current Pipeline Scope

### Airflow

The current DAG is:

- [taxi_trip_pipeline.py](C:/Users/Rohan/bigquery-dbt-project/composer/dags/taxi_trip_pipeline.py)

It currently:

- downloads monthly parquet files for `yellow`, `green`, `fhv`, and `hvfhv`
- uploads them to a raw GCS bucket
- loads them into native BigQuery bronze tables

Shared ingestion logic lives in:

- [taxi_download.py](C:/Users/Rohan/bigquery-dbt-project/composer/include/scripts/taxi_download.py)

### dbt

The current dbt project:

- treats bronze as a source layer in BigQuery
- builds silver models for yellow and green trips
- builds gold fact and aggregate models for analytics

Current model layout:

- bronze sources: [dbt/models/bronze](C:/Users/Rohan/bigquery-dbt-project/dbt/models/bronze)
- silver models: [dbt/models/silver](C:/Users/Rohan/bigquery-dbt-project/dbt/models/silver)
- gold models: [dbt/models/gold](C:/Users/Rohan/bigquery-dbt-project/dbt/models/gold)

## Configuration

Runtime configuration is driven by environment variables, while authentication
is expected to come from runtime identity.

Example variables are provided in:

- [.env.example](C:/Users/Rohan/bigquery-dbt-project/.env.example)

Primary variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCS_RAW_BUCKET`
- `BQ_BRONZE_DATASET`
- `BQ_SILVER_DATASET`
- `BQ_GOLD_DATASET`
- `AIRFLOW_DATA_DIR`
- `NYC_TLC_URL_PREFIX`

## Authentication

This repository does not store live credentials.

Recommended pattern:

- local development: ADC with `gcloud auth application-default login`
- CI/CD: GitHub Actions authenticates to GCP using workload identity federation or a securely injected service account credential
- Cloud Composer runtime: the Composer environment service account authenticates to GCP

More detail:

- [runtime_setup.md](C:/Users/Rohan/bigquery-dbt-project/docs/runtime_setup.md)
- [dbt_auth_setup.md](C:/Users/Rohan/bigquery-dbt-project/docs/dbt_auth_setup.md)
- [profiles.yml.example](C:/Users/Rohan/bigquery-dbt-project/dbt/profiles/profiles.yml.example)

## CI/CD

GitHub Actions workflow:

- [.github/workflows/ci-cd.yml](C:/Users/Rohan/bigquery-dbt-project/.github/workflows/ci-cd.yml)

The workflow is split into:

- repository validation: Python syntax checks, YAML validation, and dbt parse
- optional BigQuery integration validation: `dbt debug` and `dbt build` when GCP authentication and dataset variables are configured in GitHub

Recommended GitHub configuration:

Repository variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `BQ_BRONZE_DATASET`
- `BQ_SILVER_DATASET`
- `BQ_GOLD_DATASET`

Preferred repository secrets for GCP auth:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

Fallback secret if workload identity is not set up:

- `GCP_CREDENTIALS`

## Local Development

### Airflow

Use the Docker-based local Airflow area in:

- [local_airflow](C:/Users/Rohan/bigquery-dbt-project/local_airflow)

### dbt

1. Copy [profiles.yml.example](C:/Users/Rohan/bigquery-dbt-project/dbt/profiles/profiles.yml.example) to `dbt/profiles/profiles.yml`
2. Set `DBT_PROFILES_DIR`
3. Authenticate locally with ADC
4. Run dbt commands against the `dev` target

## Testing

Current checks include:

- Python compilation for Composer DAG and helper files
- dbt project parsing
- dbt generic and singular tests when run against BigQuery

## Documentation

- [architecture.md](C:/Users/Rohan/bigquery-dbt-project/docs/architecture.md)
- [runtime_setup.md](C:/Users/Rohan/bigquery-dbt-project/docs/runtime_setup.md)
- [dbt_auth_setup.md](C:/Users/Rohan/bigquery-dbt-project/docs/dbt_auth_setup.md)
- [SESSION_NOTES.md](C:/Users/Rohan/bigquery-dbt-project/SESSION_NOTES.md)

## Current Status

This repository currently contains:

- Composer ingestion code for raw landing in GCS and native bronze loading in BigQuery
- dbt sources plus silver and gold transformation models
- placeholder Terraform scaffolding for future infrastructure provisioning
- auth and runtime documentation
- a CI/CD workflow for repository validation and optional BigQuery integration checks

The next major implementation step is to wire dbt execution into Composer so the
full orchestration path runs end to end after bronze ingestion completes.
