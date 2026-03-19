from __future__ import annotations

import io
import os
from pathlib import Path
from datetime import timezone
import pandas as pd
from services.minio_client import get_minio_client, upload_parquet_with_key


GOLD_BUCKET = "gold-zone"
TARGET_PREFIXES = ("standard/", "high-risk/")


def load_project_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

    endpoint = os.getenv("MINIO_ENDPOINT", "")
    if "minio:9000" in endpoint:
        os.environ["MINIO_ENDPOINT"] = endpoint.replace("minio:9000", "localhost:9000")


def list_gold_objects() -> list[dict]:
    s3 = get_minio_client()
    paginator = s3.get_paginator("list_objects_v2")
    objects: list[dict] = []

    for page in paginator.paginate(Bucket=GOLD_BUCKET):
      for item in page.get("Contents", []):
          key = item["Key"]
          if key.endswith(".parquet") and key.startswith(TARGET_PREFIXES):
              objects.append(item)

    return sorted(objects, key=lambda item: item["Key"])


def backfill_gold_imported_at() -> tuple[int, int]:
    s3 = get_minio_client()
    scanned = 0
    updated = 0

    for obj in list_gold_objects():
        scanned += 1
        key = obj["Key"]
        last_modified = obj["LastModified"].astimezone(timezone.utc).isoformat()

        parquet_bytes = s3.get_object(Bucket=GOLD_BUCKET, Key=key)["Body"].read()
        df = pd.read_parquet(io.BytesIO(parquet_bytes))

        if "gold_imported_at" in df.columns and df["gold_imported_at"].notna().all():
            print(f"[SKIP] {key} deja renseigne")
            continue

        df["gold_imported_at"] = last_modified
        upload_parquet_with_key(df, GOLD_BUCKET, key)
        updated += 1
        print(f"[OK] {key} -> gold_imported_at={last_modified}")

    return scanned, updated


if __name__ == "__main__":
    load_project_env()
    scanned, updated = backfill_gold_imported_at()
    print(f"Migration terminee. Fichiers scannes: {scanned}, fichiers mis a jour: {updated}")
