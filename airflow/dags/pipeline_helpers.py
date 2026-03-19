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
AIRFLOW_BATCH_SIZE = max(int(os.getenv("AIRFLOW_BATCH_SIZE", "5")), 1)
SUPPORTED_BRONZE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg")


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


def list_bucket_keys_by_suffixes(bucket_name: str, suffixes: tuple[str, ...]) -> list[str]:
    keys = list_bucket_keys(bucket_name)
    normalized_suffixes = tuple(suffix.lower() for suffix in suffixes)
    return [key for key in keys if key.lower().endswith(normalized_suffixes)]


def object_exists(bucket_name: str, key: str) -> bool:
    s3 = get_s3_client()
    try:
        s3.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError:
        return False


def find_unprocessed_bronze_documents(limit: int = AIRFLOW_BATCH_SIZE) -> list[str]:
    bronze_keys = list_bucket_keys_by_suffixes(BRONZE_BUCKET, SUPPORTED_BRONZE_EXTENSIONS)
    silver_keys = set(list_bucket_keys(SILVER_BUCKET, suffix=".parquet"))
    pending_keys: list[str] = []

    for bronze_key in bronze_keys:
        expected_silver_key = f"{bronze_key.rsplit('.', 1)[0]}.parquet"
        if expected_silver_key not in silver_keys:
            pending_keys.append(bronze_key)
        if len(pending_keys) >= limit:
            break

    if not pending_keys:
        raise ValueError("Aucun nouveau document Bronze a traiter.")

    return pending_keys


def find_unprocessed_silver_parquets(limit: int = AIRFLOW_BATCH_SIZE) -> list[str]:
    silver_keys = list_bucket_keys(SILVER_BUCKET, suffix=".parquet")
    gold_keys = set(list_bucket_keys(GOLD_BUCKET, suffix=".parquet"))
    pending_keys: list[str] = []

    for silver_key in silver_keys:
        standard_key = f"standard/{silver_key}"
        risk_key = f"{HIGH_RISK_PREFIX}{silver_key}"
        if standard_key not in gold_keys and risk_key not in gold_keys:
            pending_keys.append(silver_key)
        if len(pending_keys) >= limit:
            break

    if not pending_keys:
        raise ValueError("Aucun nouveau fichier Silver a traiter.")

    return pending_keys


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
