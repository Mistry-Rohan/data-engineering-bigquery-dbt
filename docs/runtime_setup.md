# Runtime Setup

## Configuration Pattern

This project uses three distinct configuration channels:

- code in GitHub for logic and stable defaults
- environment variables for deployment-specific settings
- runtime identity for GCP authentication

Use this rule of thumb:

- environment variables for config
- IAM or attached service accounts for auth
- Secret Manager for secrets

## Environment Variables

The recommended variables are listed in [`.env.example`](C:/Users/Rohan/bigquery-dbt-project/.env.example):

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCS_RAW_BUCKET`
- `BQ_BRONZE_DATASET`
- `BQ_SILVER_DATASET`
- `BQ_GOLD_DATASET`
- `AIRFLOW_DATA_DIR`
- `NYC_TLC_URL_PREFIX`

These values can safely vary between `dev`, `test`, and `prod`.

## Local Docker Development

For local Docker-based Airflow development:

1. Copy `.env.example` to a local `.env` file.
2. Replace placeholder values with your project-specific settings.
3. Keep `.env` out of Git.
4. Authenticate with local Application Default Credentials or a mounted local credentials file.

Recommended local auth approaches:

- `gcloud auth application-default login` on your machine, then mount ADC into the container if needed
- or mount a local service account file for development only

Avoid:

- committing service account JSON
- storing service account JSON contents directly in environment variables

## Cloud Composer

For Cloud Composer:

- set environment variables only for non-secret runtime config
- rely on the Composer environment's service account for authentication
- grant that service account access to GCS, BigQuery, and any other required services

That means the DAG should not need embedded keys or credential files in the repository.

## GitHub

This repository is safe to push to GitHub as long as you do not commit:

- `.env`
- service account key files
- secrets copied into YAML or Python files

If you later add CI or deployment automation, GitHub Actions secrets can hold deployment-time values, but the running workload in GCP should still prefer workload identity or attached service accounts where possible.

## Current DAG Expectation

The ingestion DAG at [composer/dags/taxi_trip_pipeline.py](C:/Users/Rohan/bigquery-dbt-project/composer/dags/taxi_trip_pipeline.py) expects:

- a raw GCS bucket name
- a GCP project ID
- optional BigQuery dataset names for later bronze, silver, and gold steps

Authentication is expected to come from Application Default Credentials.

## dbt Authentication

dbt also needs BigQuery authentication when it runs warehouse operations.

See [dbt_auth_setup.md](C:/Users/Rohan/bigquery-dbt-project/docs/dbt_auth_setup.md) and
[profiles.yml.example](C:/Users/Rohan/bigquery-dbt-project/dbt/profiles/profiles.yml.example)
for the recommended local and runtime setup.
