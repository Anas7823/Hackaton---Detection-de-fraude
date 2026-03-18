import os

import duckdb
import pandas as pd


def get_duckdb_connection():
    """Cree une connexion DuckDB configuree pour lire sur MinIO"""
    con = duckdb.connect(database=':memory:')

    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    endpoint = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
    con.execute(f"SET s3_endpoint='{endpoint.replace('http://', '').replace('https://', '')}';")
    con.execute(f"SET s3_access_key_id='{os.getenv('MINIO_ROOT_USER', 'admin_idp')}';")
    con.execute(f"SET s3_secret_access_key='{os.getenv('MINIO_ROOT_PASSWORD', '')}';")
    con.execute("SET s3_use_ssl=false;")
    con.execute("SET s3_url_style='path';")

    return con


def query_gold_zone():
    """Execute une requete SQL sur les sorties Gold du pipeline pour le dashboard"""
    con = get_duckdb_connection()
    try:
        query = "SELECT * FROM read_parquet('s3://gold-zone/*/*.parquet')"
        df = con.execute(query).df()
        df = df.replace([float("inf"), float("-inf")], pd.NA)
        df = df.astype(object)
        df = df.where(pd.notnull(df), None)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Erreur DuckDB: {e}")
        return []


def query_raw_documents():
    """
    Requete les documents generes par le data_generator
    (zone Gold, reference/documents_manifest.parquet).
    """
    con = get_duckdb_connection()
    try:
        query = "SELECT * FROM read_parquet('s3://gold-zone/reference/documents_manifest.parquet')"
        df = con.execute(query).df()
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Erreur DuckDB (raw_documents): {e}")
        return []


def query_raw_companies():
    """
    Requete les entreprises du data_generator
    (zone Gold, reference/companies.parquet).
    """
    con = get_duckdb_connection()
    try:
        query = "SELECT * FROM read_parquet('s3://gold-zone/reference/companies.parquet')"
        df = con.execute(query).df()
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Erreur DuckDB (raw_companies): {e}")
        return []
