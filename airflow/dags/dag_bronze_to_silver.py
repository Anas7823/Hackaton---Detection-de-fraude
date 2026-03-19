from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.decorators import task
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

from pipeline_helpers import (
    BRONZE_BUCKET,
    SILVER_BUCKET,
    find_unprocessed_bronze_documents,
    log_success_message,
    object_exists,
    run_ocr_on_bronze_pdf,
)


default_args = {
    "owner": "evans",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="bronze_to_silver_ingestion",
    start_date=datetime(2026, 3, 17),
    schedule="*/1 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["hackathon", "bronze", "silver", "ocr"],
) as dag:
    wait_for_bronze_pdf = S3KeySensor(
        task_id="wait_for_bronze_pdf",
        bucket_key="*",
        bucket_name=BRONZE_BUCKET,
        wildcard_match=True,
        aws_conn_id="aws_default",
        poke_interval=30,
        timeout=60 * 20,
        mode="poke",
    )

    @task
    def select_bronze_keys() -> list[str]:
        try:
            return find_unprocessed_bronze_documents()
        except ValueError as exc:
            raise AirflowSkipException(str(exc))

    @task(retries=3, retry_delay=timedelta(minutes=1), execution_timeout=timedelta(minutes=5))
    def trigger_ocr(bronze_key: str) -> str:
        return run_ocr_on_bronze_pdf(bronze_key)

    @task
    def validate_silver_output(silver_key: str) -> str:
        if not object_exists(SILVER_BUCKET, silver_key):
            raise FileNotFoundError(f"Le parquet Silver attendu est absent: {silver_key}")
        return silver_key

    @task
    def notify_success(silver_key: str) -> None:
        log_success_message(f"Document traite avec succes vers Silver: {silver_key}")

    selected_keys = select_bronze_keys()
    silver_keys = trigger_ocr.expand(bronze_key=selected_keys)
    validated_silver = validate_silver_output.expand(silver_key=silver_keys)

    wait_for_bronze_pdf >> selected_keys >> silver_keys >> validated_silver
    notify_success.expand(silver_key=validated_silver)
