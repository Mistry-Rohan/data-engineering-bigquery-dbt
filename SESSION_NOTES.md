# Session Notes

## Current Project

- Project root: `C:\Users\Rohan\bigquery-dbt-project`
- Working model: single repository for Cloud Composer and dbt
- Source data: NYC TLC trip record parquet files
- Target platform: GCP

## What Has Already Been Created

- [README.md](C:/Users/Rohan/bigquery-dbt-project/README.md)
- [Architecture doc](C:/Users/Rohan/bigquery-dbt-project/docs/architecture.md)
- `composer/` scaffold for DAGs, helper scripts, config, and Composer requirements
- `dbt/` scaffold for staging, intermediate, and marts models
- `infra/terraform/` scaffold for GCS, BigQuery, IAM, and Composer provisioning
- `local_airflow/` scaffold for local Docker Airflow development

## Intended Pipeline

1. Download monthly parquet taxi files from the TLC site.
2. Upload raw files to a GCS bucket.
3. Load or register raw data into BigQuery bronze tables.
4. Transform data with dbt into silver and gold layers.
5. Orchestrate ingestion and dbt runs with Airflow.
6. Run the production workflow in Cloud Composer.

## Important Design Decisions

- Keep Composer and dbt in one monorepo.
- Keep DAG files thin and move Python business logic into shared helper modules.
- Use `staging`, `intermediate`, and `marts` inside dbt to represent bronze, silver, and gold style layers.
- Use `local_airflow/` only for development and DAG validation.

## Expected Next Step

The user plans to provide a sample Python downloader file or link. When that arrives:

1. Adapt it into `composer/include/scripts/taxi_download.py`
2. Implement a first working DAG in `composer/dags/taxi_trip_pipeline.py`
3. Wire the bronze, silver, and gold dbt flow
4. Flesh out Terraform for Composer, GCS, and BigQuery

## Helpful Files

- [README.md](C:/Users/Rohan/bigquery-dbt-project/README.md)
- [Architecture doc](C:/Users/Rohan/bigquery-dbt-project/docs/architecture.md)
- [DAG placeholder](C:/Users/Rohan/bigquery-dbt-project/composer/dags/taxi_trip_pipeline.py)
- [Downloader placeholder](C:/Users/Rohan/bigquery-dbt-project/composer/include/scripts/taxi_download.py)
- [dbt project](C:/Users/Rohan/bigquery-dbt-project/dbt/dbt_project.yml)
