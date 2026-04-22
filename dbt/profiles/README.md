# dbt Profiles

Keep local example profiles here for development documentation only.

In CI and Composer, prefer environment variables and generated profiles rather
than committing live credentials.

Use [profiles.yml.example](C:/Users/Rohan/bigquery-dbt-project/dbt/profiles/profiles.yml.example)
as the starting point for local development.

Recommended pattern:

- local development: `method: oauth` with Application Default Credentials
- containerized or automated runtime: `method: service-account` only when a
  credentials file is mounted securely at runtime
- Cloud Composer or other GCP runtime: prefer generated profiles and runtime
  identity instead of committing a live `profiles.yml`
