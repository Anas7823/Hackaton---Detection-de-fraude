import pandas as pd
import io
import os
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path
import boto3
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env à la racine
load_dotenv(Path(__file__).parent.parent / ".env")

def train_fraud_model():
    print("🚀 Démarrage de l'entraînement du modèle de détection de fraude...")
    
    # 1. Connexion au Data Lake (MinIO)
    # Adaptation dynamique pour l'exécution locale (remplace le réseau interne Docker par localhost)
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    if "http://minio:" in minio_endpoint:
        minio_endpoint = minio_endpoint.replace("http://minio:", "http://localhost:")

    try:
        s3 = boto3.client(
            's3',
            endpoint_url=minio_endpoint,
            aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD"),
        )
    except Exception as e:
        print(f"❌ Erreur de connexion à MinIO: {e}")
        return
        
    print("📥 Récupération des données depuis MinIO...")
    
    # 2. Récupérer le Manifest (Gold Zone) qui contient la variable cible (is_fraud)
    try:
        obj = s3.get_object(Bucket="gold-zone", Key="reference/documents_manifest.parquet")
        df_manifest = pd.read_parquet(io.BytesIO(obj['Body'].read()))
        print("✅ Manifest chargé depuis MinIO (Gold Zone).")
    except Exception as e:
        print(f"⚠️ Manifest introuvable sur MinIO. Tentative de lecture en local...")
        local_manifest_path = Path(__file__).parent.parent / "data_generator" / "output" / "documents_manifest.csv"
        if local_manifest_path.exists():
            df_manifest = pd.read_csv(local_manifest_path)
            print("✅ Manifest local chargé avec succès.")
        else:
            print(f"❌ Erreur critique : Manifest introuvable en local ({local_manifest_path}).")
            return

    # 3. Récupérer toutes les extractions OCR (Silver Zone)
    silver_objects = s3.list_objects_v2(Bucket="silver-zone")
    df_silver_list = []
    
    if 'Contents' in silver_objects:
        for item in silver_objects['Contents']:
            if item['Key'].endswith('.parquet'):
                obj = s3.get_object(Bucket="silver-zone", Key=item['Key'])
                df_silver_list.append(pd.read_parquet(io.BytesIO(obj['Body'].read())))
                
    if not df_silver_list:
        print("❌ Aucun fichier trouvé dans la Silver Zone. Lancez l'API et Airflow en premier !")
        return
        
    df_silver = pd.concat(df_silver_list, ignore_index=True)
    print(f"📂 {len(df_silver)} extractions OCR chargées depuis la Silver Zone.")

    # 4. Jointure des Features (Silver) et des Labels (Gold)
    # source_file ressemble à "siret/monfichier.pdf" ou "monfichier.pdf"
    df_silver['filename'] = df_silver['source_file'].apply(lambda x: str(x).split('/')[-1])
    df = pd.merge(df_silver, df_manifest[['filename', 'is_fraud']], on='filename', how='left')
    df['is_fraud'] = df['is_fraud'].fillna(0).astype(int)
    
    # 🎯 CORRECTION CRITIQUE : Filtrer pour le ML
    # On ne garde que les factures et devis car les autres types de fraudes (RIB invalide, Attestation expirée)
    # sont gérés par le moteur de règles. Le ML ne doit apprendre que sur les anomalies de montants !
    df = df[df['document_type'].isin(['facture', 'devis', 'unknown'])].copy()

    # 5. Extraction via Regex depuis l'ocr_text
    def extract_ht(text):
        if not isinstance(text, str): return 0.0
        match = re.search(r'(?:HT|Total HT|Montant HT)\s*[:\-]?\s*([\d\s]+[.,]\d{2})', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(' ', '').replace(',', '.'))
        return 0.0
        
    def extract_total(text):
        if not isinstance(text, str): return 0.0
        match = re.search(r'(?:TTC|Total TTC|Montant total|Montant TTC)\s*[:\-]?\s*([\d\s]+[.,]\d{2})', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(' ', '').replace(',', '.'))
        return 0.0

    df['montant_ht_extrait'] = df['ocr_text'].apply(extract_ht)
    df['montant_total_regex'] = df['ocr_text'].apply(extract_total)
    
    # Consolidation du TTC (Privilégie 'amount_total' de l'OCR, comble avec le Regex)
    df['amount_total_clean'] = pd.to_numeric(df['amount_total'], errors='coerce').fillna(df['montant_total_regex'])
    
    # Feature Engineering intelligent : Tolérance multi-TVA
    def compute_ecart(row):
        ttc = row['amount_total_clean']
        ht = row['montant_ht_extrait']
        if pd.isna(ttc) or pd.isna(ht) or ht == 0:
            return 0.0
        # Teste les taux de TVA officiels (0%, 5.5%, 10%, 20%) et garde l'écart minimum
        ecart = min([abs(ttc - (ht * (1 + rate))) for rate in [0.0, 0.055, 0.10, 0.20]])
        return round(ecart, 2)

    df['ecart_montant'] = df.apply(compute_ecart, axis=1)
    df['montant_manquant'] = ((df['amount_total_clean'] == 0) | (df['montant_ht_extrait'] == 0)).astype(int)

    # Création d'une variable binaire pour aider le modèle à ignorer le bruit de l'OCR (tolérance 1 euro)
    df['ecart_suspect'] = (df['ecart_montant'] > 1.0).astype(int)

    
    # Préparation Finale des Variables
    df['document_type'] = df['document_type'].fillna('unknown')
    df['ecart_montant'] = df['ecart_montant'].fillna(0)
    
    X = df[['document_type', 'ecart_montant', 'montant_manquant', 'ecart_suspect']]

    y = df['is_fraud']
    
    # 6. Pipeline Machine Learning (Évite les crashs en production)
    preprocessor = ColumnTransformer(
        transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), ['document_type'])],
        remainder='passthrough'
    )
    
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'))
    ])
    
    # 7. Entraînement et Évaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)
    
    print("\n📊 Rapport de classification :")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # 8. Sauvegarde
    model_dir = Path(__file__).parent / "saved_models"
    model_dir.mkdir(exist_ok=True, parents=True)
    model_path = model_dir / "fraud_model.joblib"
    
    joblib.dump(model, model_path)

if __name__ == "__main__":
    train_fraud_model()
