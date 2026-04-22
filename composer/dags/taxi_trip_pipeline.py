"""
Monthly NYC TLC parquet ingestion DAG for Cloud Composer.

This DAG downloads monthly parquet files from the TLC source, lands them in
GCS, and ingests them into native BigQuery bronze tables.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup


INCLUDE_SCRIPTS_PATH = Path(__file__).resolve().parents[1] / "include" / "scripts"
if str(INCLUDE_SCRIPTS_PATH) not in sys.path:
    sys.path.append(str(INCLUDE_SCRIPTS_PATH))

from taxi_download import BRONZE_DATASET  # noqa: E402
from taxi_download import DEFAULT_ARGS  # noqa: E402
from taxi_download import GCP_REGION  # noqa: E402
from taxi_download import GOLD_DATASET  # noqa: E402
from taxi_download import RAW_BUCKET  # noqa: E402
from taxi_download import SILVER_DATASET  # noqa: E402
from taxi_download import TAXI_FILE_PREFIXES  # noqa: E402
from taxi_download import cleanup_local_file  # noqa: E402
from taxi_download import download_parquet  # noqa: E402
from taxi_download import load_gcs_parquet_to_bronze  # noqa: E402
from taxi_download import upload_to_gcs  # noqa: E402
from taxi_download import validate_runtime_config  # noqa: E402


with DAG(
    dag_id="nyc_taxi_parquet_to_bronze",
    description="Download monthly NYC TLC parquet files to GCS and load bronze BigQuery tables.",
    schedule="0 6 2 * *",
    start_date=datetime(2019, 1, 1),
    catchup=True,
    max_active_runs=2,
    default_args=DEFAULT_ARGS,
    tags=["nyc-taxi", "gcs", "bigquery", "composer", GCP_REGION or "gcp"],
) as dag:
    start = PythonOperator(
        task_id="validate_runtime_config",
        python_callable=validate_runtime_config,
    )

    raw_landing_complete = EmptyOperator(task_id="raw_landing_complete")
    bronze_complete = EmptyOperator(
        task_id="bronze_complete",
        doc_md=f"Target bronze dataset: `{BRONZE_DATASET or 'not-configured'}`",
    )
    silver_ready = EmptyOperator(
        task_id="silver_ready",
        doc_md=f"Target silver dataset: `{SILVER_DATASET or 'not-configured'}`",
    )
    gold_ready = EmptyOperator(
        task_id="gold_ready",
        doc_md=f"Target gold dataset: `{GOLD_DATASET or 'not-configured'}`",
    )

    for taxi_type in TAXI_FILE_PREFIXES:
        with TaskGroup(group_id=taxi_type) as taxi_group:
            download_task = PythonOperator(
                task_id=f"download_{taxi_type}_parquet",
                python_callable=download_parquet,
                op_kwargs={
                    "taxi_type": taxi_type,
                    "logical_date": "{{ ds }}",
                },
            )

            upload_task = PythonOperator(
                task_id=f"upload_{taxi_type}_to_gcs",
                python_callable=upload_to_gcs,
                op_kwargs={
                    "taxi_type": taxi_type,
                    "logical_date": "{{ ds }}",
                    "bucket_name": RAW_BUCKET,
                },
            )

            bronze_load_task = PythonOperator(
                task_id=f"load_{taxi_type}_bronze",
                python_callable=load_gcs_parquet_to_bronze,
                op_kwargs={
                    "taxi_type": taxi_type,
                    "logical_date": "{{ ds }}",
                    "bucket_name": RAW_BUCKET,
                },
            )

            cleanup_task = PythonOperator(
                task_id=f"cleanup_{taxi_type}_local_file",
                python_callable=cleanup_local_file,
                op_kwargs={"taxi_type": taxi_type},
                trigger_rule="all_done",
            )

            download_task >> upload_task >> bronze_load_task >> cleanup_task

        start >> taxi_group >> raw_landing_complete
        taxi_group >> bronze_complete

    raw_landing_complete >> bronze_complete >> silver_ready >> gold_ready
