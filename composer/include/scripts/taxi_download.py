"""
Helpers for the NYC TLC raw-to-bronze ingestion pipeline.

This module keeps the business logic out of the DAG file so the Composer DAG
can focus on orchestration.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import requests
import yaml
from airflow.exceptions import AirflowFailException, AirflowSkipException
from google.cloud import bigquery
from google.cloud import storage


TAXI_FILE_PREFIXES = {
    "yellow": "yellow_tripdata",
    "green": "green_tripdata",
    "fhv": "fhv_tripdata",
    "hvfhv": "hvfhv_tripdata",
}

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "pipeline_config.yaml"
)


def load_pipeline_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}

    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


PIPELINE_CONFIG = load_pipeline_config()


def get_config_value(
    env_var_names: list[str],
    default: str | None = None,
) -> str | None:
    for env_var_name in env_var_names:
        env_value = os.environ.get(env_var_name)
        if env_value:
            return env_value
    return default


PROJECT_ID = get_config_value(
    ["GCP_PROJECT_ID"],
    default=PIPELINE_CONFIG.get("project_id"),
)
GCP_REGION = get_config_value(
    ["GCP_REGION", "GCP_LOCATION"],
    default=PIPELINE_CONFIG.get("location", "us-central1"),
)
RAW_BUCKET = get_config_value(
    ["GCS_RAW_BUCKET", "GCP_GCS_BUCKET"],
    default=PIPELINE_CONFIG.get("gcs", {}).get("raw_bucket"),
)
BRONZE_DATASET = get_config_value(
    ["BQ_BRONZE_DATASET"],
    default=PIPELINE_CONFIG.get("bigquery", {}).get("bronze_dataset"),
)
SILVER_DATASET = get_config_value(
    ["BQ_SILVER_DATASET"],
    default=PIPELINE_CONFIG.get("bigquery", {}).get("silver_dataset"),
)
GOLD_DATASET = get_config_value(
    ["BQ_GOLD_DATASET"],
    default=PIPELINE_CONFIG.get("bigquery", {}).get("gold_dataset"),
)
AIRFLOW_DATA_DIR = get_config_value(
    ["AIRFLOW_DATA_DIR"],
    default="/tmp/nyc_taxi_pipeline",
)
URL_PREFIX = get_config_value(
    ["NYC_TLC_URL_PREFIX"],
    default="https://d37ci6vzurychx.cloudfront.net/trip-data",
)


def build_month_key(logical_date: str) -> str:
    return datetime.fromisoformat(logical_date).strftime("%Y-%m")


def build_source_url(taxi_type: str, logical_date: str) -> str:
    file_prefix = TAXI_FILE_PREFIXES[taxi_type]
    month_key = build_month_key(logical_date)
    return f"{URL_PREFIX}/{file_prefix}_{month_key}.parquet"


def build_local_path(taxi_type: str, logical_date: str) -> str:
    file_prefix = TAXI_FILE_PREFIXES[taxi_type]
    month_key = build_month_key(logical_date)
    local_dir = Path(AIRFLOW_DATA_DIR) / taxi_type
    local_dir.mkdir(parents=True, exist_ok=True)
    return str(local_dir / f"{file_prefix}_{month_key}.parquet")


def build_gcs_object_name(taxi_type: str, logical_date: str) -> str:
    file_prefix = TAXI_FILE_PREFIXES[taxi_type]
    date_value = datetime.fromisoformat(logical_date)
    month_key = date_value.strftime("%Y-%m")
    return (
        f"raw/{taxi_type}/year={date_value:%Y}/month={date_value:%m}/"
        f"{file_prefix}_{month_key}.parquet"
    )


def build_bronze_table_id(taxi_type: str) -> str:
    file_prefix = TAXI_FILE_PREFIXES[taxi_type]
    return f"{PROJECT_ID}.{BRONZE_DATASET}.{file_prefix}"


def validate_runtime_config() -> None:
    if not RAW_BUCKET:
        raise AirflowFailException(
            "Missing raw bucket configuration. Set GCS_RAW_BUCKET or define "
            "gcs.raw_bucket in pipeline_config.yaml."
        )

    if not PROJECT_ID:
        raise AirflowFailException(
            "Missing GCP project configuration. Set GCP_PROJECT_ID or define "
            "project_id in pipeline_config.yaml."
        )

    if not BRONZE_DATASET:
        raise AirflowFailException(
            "Missing bronze dataset configuration. Set BQ_BRONZE_DATASET or "
            "define bigquery.bronze_dataset in pipeline_config.yaml."
        )


def download_parquet(taxi_type: str, logical_date: str, **_: object) -> str:
    source_url = build_source_url(taxi_type=taxi_type, logical_date=logical_date)
    local_path = build_local_path(taxi_type=taxi_type, logical_date=logical_date)

    response = requests.get(source_url, stream=True, timeout=600)
    if response.status_code == 404:
        raise AirflowSkipException(
            f"No source file published for {taxi_type} at {source_url}"
        )
    response.raise_for_status()

    with open(local_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                output_file.write(chunk)

    return local_path


def upload_to_gcs(
    taxi_type: str,
    logical_date: str,
    bucket_name: str,
    ti,
    **_: object,
) -> str:
    local_path = ti.xcom_pull(task_ids=f"{taxi_type}.download_{taxi_type}_parquet")
    if not local_path:
        raise AirflowSkipException(
            f"Download step did not produce a local file for {taxi_type}."
        )

    object_name = build_gcs_object_name(taxi_type=taxi_type, logical_date=logical_date)

    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_path)

    return object_name


def load_gcs_parquet_to_bronze(
    taxi_type: str,
    logical_date: str,
    bucket_name: str,
    ti,
    **_: object,
) -> str:
    gcs_object_name = ti.xcom_pull(task_ids=f"{taxi_type}.upload_{taxi_type}_to_gcs")
    if not gcs_object_name:
        raise AirflowSkipException(
            f"GCS upload step did not produce an object path for {taxi_type}."
        )

    source_uri = f"gs://{bucket_name}/{gcs_object_name}"
    table_id = build_bronze_table_id(taxi_type=taxi_type)

    client = bigquery.Client(project=PROJECT_ID)
    dataset_id = f"{PROJECT_ID}.{BRONZE_DATASET}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = GCP_REGION
    client.create_dataset(dataset, exists_ok=True)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        autodetect=True,
        schema_update_options=[
            bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            bigquery.SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
        ],
    )

    load_job = client.load_table_from_uri(
        source_uris=source_uri,
        destination=table_id,
        job_config=job_config,
        location=GCP_REGION,
    )
    load_job.result()

    return table_id


def cleanup_local_file(taxi_type: str, ti, **_: object) -> None:
    local_path = ti.xcom_pull(task_ids=f"{taxi_type}.download_{taxi_type}_parquet")
    if local_path and os.path.exists(local_path):
        os.remove(local_path)
