import duckdb
import os

def get_duckdb_connection():
    """Crée une connexion DuckDB configurée pour lire sur MinIO"""
    con = duckdb.connect(database=':memory:') # On travaille en RAM pour la rapidité
    
    # Configuration pour accéder à MinIO (S3)
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
    """Exécute une requête SQL sur les données validées (gold-zone/validated/) pour le dashboard"""
    con = get_duckdb_connection()
    try:
        # Données validées par le pipeline OCR + détection fraude
        query = "SELECT * FROM read_parquet('s3://gold-zone/validated/*.parquet')"
        df = con.execute(query).df() # On récupère le résultat en DataFrame Pandas
        return df.to_dict(orient='records') # On convertit en liste JSON pour l'API
    except Exception as e:
        print(f"Erreur DuckDB: {e}")
        return []


def query_raw_documents():
    """
    Requête les documents générés par le data_generator (zone Gold, reference/documents_manifest.parquet).
    Retourne la liste des documents avec filename, doc_type, company_siret, company_name.
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
    Requête les entreprises du data_generator (zone Gold, reference/companies.parquet).
    Retourne la liste des entreprises (SIRET, nom, adresse, etc.).
    """
    con = get_duckdb_connection()
    try:
        query = "SELECT * FROM read_parquet('s3://gold-zone/reference/companies.parquet')"
        df = con.execute(query).df()
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Erreur DuckDB (raw_companies): {e}")
        return []