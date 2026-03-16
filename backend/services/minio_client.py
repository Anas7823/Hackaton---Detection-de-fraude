# backend/services/minio_client.py
import boto3
import os
from botocore.exceptions import ClientError
import io
import pandas as pd

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

def upload_parquet_to_zone(df: pd.DataFrame, zone: str, original_filename: str):
    """
    Convertit un DataFrame Pandas en Parquet en mémoire et l'envoie dans la zone ciblée (Silver ou Gold).
    """
    s3 = get_minio_client()
    try:
        # 1. On change l'extension du fichier (ex: facture.pdf -> facture.parquet)
        base_name = original_filename.rsplit('.', 1)[0]
        parquet_filename = f"{base_name}.parquet"

        # 2. On crée un buffer en mémoire vive (RAM)
        parquet_buffer = io.BytesIO()
        
        # 3. On convertit le DataFrame en Parquet dans ce buffer
        df.to_parquet(parquet_buffer, engine='pyarrow', index=False)
        
        # 4. On remet le curseur de lecture au début du buffer
        parquet_buffer.seek(0)

        # 5. On envoie le buffer directement dans le bucket cible
        s3.upload_fileobj(parquet_buffer, zone, parquet_filename)
        
        print(f"✅ Succès : {parquet_filename} sauvegardé dans {zone}")
        return True

    except Exception as e:
        print(f"❌ Erreur d'upload Parquet vers {zone} : {e}")
        return False

# Raccourcis pour les zones Silver et Gold:
def upload_to_silver(df: pd.DataFrame, filename: str):
    return upload_parquet_to_zone(df, "silver-zone", filename)

def upload_to_gold(df: pd.DataFrame, filename: str):
    return upload_parquet_to_zone(df, "gold-zone", filename)