from __future__ import annotations

import os
from typing import Any

import boto3
import httpx
from botocore.exceptions import ClientError


MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123")
BRONZE_BUCKET = os.getenv("BRONZE_BUCKET", "bronze-zone")
SILVER_BUCKET = os.getenv("SILVER_BUCKET", "silver-zone")
GOLD_BUCKET = os.getenv("GOLD_BUCKET", "gold-zone")
HIGH_RISK_PREFIX = os.getenv("HIGH_RISK_PREFIX", "high-risk/")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://backend:8000")


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ROOT_USER,
        aws_secret_access_key=MINIO_ROOT_PASSWORD,
    )


def list_bucket_keys(bucket_name: str, suffix: str | None = None) -> list[str]:
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=bucket_name)
    keys = [item["Key"] for item in response.get("Contents", [])]
    if suffix:
        keys = [key for key in keys if key.lower().endswith(suffix.lower())]
    return sorted(keys)


def object_exists(bucket_name: str, key: str) -> bool:
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError:
        return False


def find_next_unprocessed_bronze_pdf() -> str:
    bronze_keys = list_bucket_keys(BRONZE_BUCKET, suffix=".pdf")
    silver_keys = set(list_bucket_keys(SILVER_BUCKET, suffix=".parquet"))

    for bronze_key in bronze_keys:
        expected_silver_key = f"{bronze_key.rsplit('.', 1)[0]}.parquet"
        if expected_silver_key not in silver_keys:
            return bronze_key

    raise ValueError("Aucun nouveau PDF Bronze a traiter.")


def find_next_unprocessed_silver_parquet() -> str:
    silver_keys = list_bucket_keys(SILVER_BUCKET, suffix=".parquet")
    gold_keys = set(list_bucket_keys(GOLD_BUCKET, suffix=".parquet"))

    for silver_key in silver_keys:
        standard_key = f"standard/{silver_key}"
        risk_key = f"{HIGH_RISK_PREFIX}{silver_key}"
        if standard_key not in gold_keys and risk_key not in gold_keys:
            return silver_key

    raise ValueError("Aucun nouveau fichier Silver a traiter.")


def run_ocr_on_bronze_pdf(bronze_key: str) -> str:
    response = httpx.post(
        f"{BACKEND_BASE_URL}/api/v1/internal/process/bronze-to-silver",
        json={"bronze_key": bronze_key},
        timeout=300.0,
    )
    response.raise_for_status()
    return response.json()["silver_key"]


def push_gold_and_route_risk(silver_key: str) -> dict[str, Any]:
    response = httpx.post(
        f"{BACKEND_BASE_URL}/api/v1/internal/process/silver-to-gold",
        json={"silver_key": silver_key},
        timeout=180.0,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "gold_key": payload["gold_key"],
        "risk_level": payload["risk_level"],
        "fraud_score": payload["fraud_score"],
    }


def log_success_message(message: str) -> None:
    print(f"[AIRFLOW SUCCESS] {message}")
