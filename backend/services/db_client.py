import duckdb
import os

def get_duckdb_connection():
    """Crée une connexion DuckDB configurée pour lire sur MinIO"""
    con = duckdb.connect(database=':memory:') # On travaille en RAM pour la rapidité
    
    # Configuration pour accéder à MinIO (S3)
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute(f"SET s3_endpoint='{os.getenv('MINIO_ENDPOINT').replace('http://', '')}';")
    con.execute(f"SET s3_access_key_id='{os.getenv('MINIO_ROOT_USER')}';")
    con.execute(f"SET s3_secret_access_key='{os.getenv('MINIO_ROOT_PASSWORD')}';")
    con.execute("SET s3_use_ssl=false;")
    con.execute("SET s3_url_style='path';")
    
    return con

def query_gold_zone():
    """Exécute une requête SQL directement sur tous les fichiers Parquet de la zone Gold"""
    con = get_duckdb_connection()
    try:
        # On requête directement l'URL S3 avec un wildcard (*)
        query = "SELECT * FROM read_parquet('s3://gold-zone/*.parquet')"
        df = con.execute(query).df() # On récupère le résultat en DataFrame Pandas
        return df.to_dict(orient='records') # On convertit en liste JSON pour l'API
    except Exception as e:
        print(f"Erreur DuckDB: {e}")
        return []