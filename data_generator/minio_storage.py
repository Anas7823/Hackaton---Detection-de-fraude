"""
Stockage MinIO - Connexion au Data Lake (Bronze + Gold) pour DuckDB.
Upload des PDFs vers Bronze, export Parquet vers Gold pour requetage par l'API.
"""

import io
from pathlib import Path
from typing import Optional

import pandas as pd

from config import RAW_DIR
from models import Company, DocumentRecord


def get_minio_client():
    """Retourne le client S3/MinIO ou None si indisponible."""
    try:
        import os
        import boto3
        from botocore.config import Config

        endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        if not endpoint:
            return None

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.getenv("MINIO_ROOT_USER", "admin_idp"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD", "SuperSecretPassword123!"),
            config=Config(signature_version="s3v4", region_name="us-east-1"),
        )
        # Test de connexion : list_buckets
        client.list_buckets()
        return client
    except Exception:
        return None


def upload_pdfs_to_bronze(records: list[DocumentRecord]) -> int:
    """
    Upload les PDFs generes vers la zone Bronze (MinIO).
    Chemin: bronze-zone/{siret}/{filename}
    Retourne le nombre de fichiers uploades.
    """
    client = get_minio_client()
    if not client:
        return 0

    bucket = "bronze-zone"
    count = 0

    for r in records:
        pdf_path = RAW_DIR / r.company_siret / r.filename
        if not pdf_path.exists():
            continue

        s3_key = f"{r.company_siret}/{r.filename}"
        try:
            client.upload_file(str(pdf_path), bucket, s3_key)
            count += 1
        except Exception as e:
            print(f"  [WARN] MinIO upload {r.filename}: {e}")

    return count


def upload_manifest_to_gold(records: list[DocumentRecord]) -> bool:
    """
    Convertit le manifest en Parquet et l'upload vers Gold zone.
    Chemin: gold-zone/reference/documents_manifest.parquet
    DuckDB: read_parquet('s3://gold-zone/reference/documents_manifest.parquet')
    """
    client = get_minio_client()
    if not client:
        return False

    df = pd.DataFrame([
        {
            "filename": r.filename,
            "doc_type": r.doc_type,
            "company_siret": r.company_siret,
            "company_name": r.company_name,
            "is_fraud": r.is_fraud,
            "fraud_type": r.fraud_type,
        }
        for r in records
    ])

    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    try:
        client.upload_fileobj(buffer, "gold-zone", "reference/documents_manifest.parquet")
        return True
    except Exception as e:
        print(f"  [WARN] MinIO upload manifest: {e}")
        return False


def upload_companies_to_gold(companies: list[Company]) -> bool:
    """
    Convertit les entreprises en Parquet et upload vers Gold zone.
    Chemin: gold-zone/reference/companies.parquet
    DuckDB: read_parquet('s3://gold-zone/reference/companies.parquet')
    """
    client = get_minio_client()
    if not client:
        return False

    df = pd.DataFrame([
        {
            "siren": c.siren,
            "siret": c.siret,
            "nom": c.nom,
            "adresse": c.adresse,
            "code_postal": c.code_postal,
            "ville": c.ville,
            "naf": c.naf,
            "forme_juridique": c.forme_juridique,
            "dirigeant": c.dirigeant,
            "tva_intra": c.tva_intra,
        }
        for c in companies
    ])

    buffer = io.BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    try:
        client.upload_fileobj(buffer, "gold-zone", "reference/companies.parquet")
        return True
    except Exception as e:
        print(f"  [WARN] MinIO upload companies: {e}")
        return False


def sync_to_minio(records: list[DocumentRecord], companies: list) -> dict:
    """
    Synchronise tout le dataset vers MinIO (Bronze + Gold).
    Retourne un dict avec les stats de sync.
    """
    result = {"pdfs_bronze": 0, "manifest_gold": False, "companies_gold": False}

    result["pdfs_bronze"] = upload_pdfs_to_bronze(records)
    result["manifest_gold"] = upload_manifest_to_gold(records)
    result["companies_gold"] = upload_companies_to_gold(companies)

    return result
