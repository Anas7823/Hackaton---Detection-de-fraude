# backend/services/minio_client.py
import boto3
import os
from botocore.exceptions import ClientError

def get_minio_client():
    """Initialise et retourne le client S3 compatible MinIO"""
    return boto3.client(
        's3',
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
        aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD")
    )

def upload_to_bronze(file_obj, filename: str):
    """Upload un fichier directement dans le bucket bronze-zone"""
    s3 = get_minio_client()
    try:
        s3.upload_fileobj(file_obj, "bronze-zone", filename)
        return True
    except ClientError as e:
        print(f"Erreur d'upload MinIO: {e}")
        return False