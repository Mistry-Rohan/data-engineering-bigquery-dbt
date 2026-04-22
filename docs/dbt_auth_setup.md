# dbt Authentication Setup

This project uses dbt with BigQuery, so dbt needs authentication whenever it runs warehouse operations such as:

- `dbt run`
- `dbt test`
- `dbt build`
- `dbt seed`
- `dbt source freshness`

## Recommended Pattern

Use the same authentication philosophy as the Airflow side of the project:

- environment variables for configuration
- runtime identity for GCP authentication
- no committed credentials in GitHub

## Local Development

For local development, use the `oauth` target in
[profiles.yml.example](C:/Users/Rohan/bigquery-dbt-project/dbt/profiles/profiles.yml.example).

Suggested setup:

1. Copy `dbt/profiles/profiles.yml.example` to `dbt/profiles/profiles.yml`
2. Set `DBT_PROFILES_DIR` to `C:\Users\Rohan\bigquery-dbt-project\dbt\profiles`
3. Run `gcloud auth application-default login`
4. Use the `dev` target for local runs

This keeps local auth tied to your Google account or local ADC rather than a committed key.

## Runtime / Container Use

For automated runtime use, the example profile includes a `runtime` target.

Use this only when a credentials file is mounted securely at runtime and passed through:

- `DBT_GOOGLE_APPLICATION_CREDENTIALS`

Do not commit that file into the repository.

## Cloud Composer Note

If you later run dbt from Cloud Composer, the cleanest pattern is usually:

- generate or mount a runtime `profiles.yml`
- inject non-secret config through environment variables
- rely on the Composer environment's service account or securely mounted credentials

In other words, the repository should contain only the template, not the live profile.

## Related Variables

The current dbt profile expects these environment variables:

- `GCP_PROJECT_ID`
- `GCP_REGION`
- `BQ_SILVER_DATASET`
- `DBT_GOOGLE_APPLICATION_CREDENTIALS` for the `runtime` target only

## Official References

These patterns are based on the official dbt docs for BigQuery connection setup and profile configuration:

- [dbt BigQuery setup](https://docs.getdbt.com/docs/local/connect-data-platform/bigquery-setup)
- [About profiles.yml](https://docs.getdbt.com/docs/fusion/connect-data-platform-fusion/connection-profiles)
