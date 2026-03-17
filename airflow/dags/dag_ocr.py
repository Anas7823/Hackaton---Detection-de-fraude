from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def process_new_file(**kwargs):
    # Code d'extraction ici, par exemple en utilisant boto3 pour télécharger le fichier depuis MinIO et lancer l'OCR

    print("🚀 Nouveau fichier détecté dans la Bronze Zone ! Lancement de l'OCR...")

default_args = {
    'owner': 'anas_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'pipeline_ingestion_idp',
    default_args=default_args,
    schedule_interval='@continuous', # Surveille en continu
    catchup=False
) as dag:

    # 1. On attend que le fichier arrive dans MinIO
    wait_for_file = S3KeySensor(
        task_id='wait_for_bronze_file',
        bucket_name='bronze-zone',
        # Surveille tous les PDF et images
        bucket_key='**/*.{pdf,jpg,jpeg,png}', 
        wildcard_match=True,
        aws_conn_id='minio_conn', # La connexion qu'il devra créer dans l'interface Airflow
        timeout=18 * 60 * 60,
        poke_interval=30
    )

    # 2. On lance le traitement
    ocr_task = PythonOperator(
        task_id='extract_text_ocr',
        python_callable=process_new_file
    )
    
    wait_for_file >> ocr_task