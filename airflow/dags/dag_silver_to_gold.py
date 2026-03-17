from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

from pipeline_helpers import (
    GOLD_BUCKET,
    SILVER_BUCKET,
    find_next_unprocessed_silver_parquet,
    list_bucket_keys,
    log_success_message,
    push_gold_and_route_risk,
)


default_args = {
    "owner": "evans",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="silver_to_gold_intelligence",
    start_date=datetime(2026, 3, 17),
    schedule="*/3 * * * *",
    catchup=False,
    default_args=default_args,
    tags=["hackathon", "silver", "gold", "fraud"],
) as dag:
    wait_for_silver_parquet = S3KeySensor(
        task_id="wait_for_silver_parquet",
        bucket_key="*.parquet",
        bucket_name=SILVER_BUCKET,
        wildcard_match=True,
        aws_conn_id="aws_default",
        poke_interval=30,
        timeout=60 * 20,
        mode="poke",
    )

    @task
    def select_silver_key() -> str:
        return find_next_unprocessed_silver_parquet()

    @task(retries=2, retry_delay=timedelta(minutes=1), execution_timeout=timedelta(minutes=3))
    def run_fraud_model(silver_key: str) -> dict:
        return push_gold_and_route_risk(silver_key)

    @task
    def validate_gold_output(payload: dict) -> dict:
        gold_keys = list_bucket_keys(GOLD_BUCKET, suffix=".parquet")
        if payload["gold_key"] not in gold_keys:
            raise FileNotFoundError(f"Le fichier Gold attendu est absent: {payload['gold_key']}")
        return payload

    @task
    def notify_success(payload: dict) -> None:
        log_success_message(
            f"Document traite vers Gold: {payload['gold_key']} | "
            f"risk={payload['risk_level']} | score={payload['fraud_score']}"
        )

    selected_key = select_silver_key()
    gold_payload = run_fraud_model(selected_key)
    validated_gold = validate_gold_output(gold_payload)

    wait_for_silver_parquet >> selected_key >> gold_payload >> validated_gold >> notify_success(validated_gold)
