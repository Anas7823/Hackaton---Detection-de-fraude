from typing import List

import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.db_client import query_gold_zone, query_raw_documents, query_raw_companies
from services.validation_service import apply_advanced_validation, add_ml_detection 
from services.fraud_service import compute_fraud_scores
from services.minio_client import (
    object_exists,
    read_bytes_from_zone,
    upload_parquet_with_key,
    upload_to_bronze,
    get_file_url
)
from services.ocr_service import analyze_document_with_ocr

router = APIRouter()

@router.get("/api/v1/documents/{filename}/url")
async def get_document_url(filename: str):
    """Génère une URL temporaire pour visualiser le document brut (PDF/Image) depuis la Bronze Zone"""
    url = get_file_url("bronze-zone", filename)
    
    if not url:
        raise HTTPException(status_code=404, detail="Fichier introuvable ou erreur MinIO")
        
    return {"url": url}


@router.post("/api/v1/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Route pour uploader un ou plusieurs documents administratifs sensibles"""
    results = {"successful": [], "failed": []}

    for file in files:
        if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            results["failed"].append({"filename": file.filename, "reason": "Format rejete - PDF/Image uniquement"})
            continue

        success = upload_to_bronze(file.file, file.filename)

        if success:
            results["successful"].append({"filename": file.filename, "zone": "bronze-zone"})
        else:
            results["failed"].append({"filename": file.filename, "reason": "Erreur d'ecriture MinIO"})

    if not results["successful"] and files:
        raise HTTPException(status_code=500, detail="Echec de l'upload pour tous les fichiers.")

    return {
        "status": "partial_success" if results["failed"] else "success",
        "message": f"{len(results['successful'])} fichier(s) securise(s), {len(results['failed'])} echec(s).",
        "details": results,
    }


@router.get("/api/v1/dashboard")
async def get_dashboard_data():
    """Recupere les resultats consolides depuis la Gold Zone pour le dashboard"""
    data = query_gold_zone()

    if not data:
        return {
            "status": "empty",
            "message": "Aucune donnee analysee pour le moment",
            "data": [],
        }

    return {
        "status": "success",
        "count": len(data),
        "data": data,
    }


@router.get("/api/v1/documents")
async def get_raw_documents():
    """Recupere les documents generes par le data_generator"""
    data = query_raw_documents()
    return {
        "status": "success" if data else "empty",
        "count": len(data),
        "data": data,
    }


@router.get("/api/v1/companies")
async def get_raw_companies():
    """Recupere les entreprises du data_generator"""
    data = query_raw_companies()
    return {
        "status": "success" if data else "empty",
        "count": len(data),
        "data": data,
    }


@router.post("/api/v1/internal/process/bronze-to-silver")
async def process_bronze_to_silver(payload: dict):
    bronze_key = payload.get("bronze_key")
    if not bronze_key:
        raise HTTPException(status_code=400, detail="bronze_key is required")

    if not object_exists("bronze-zone", bronze_key):
        raise HTTPException(status_code=404, detail="Bronze file not found")

    file_bytes = read_bytes_from_zone("bronze-zone", bronze_key)
    extraction = analyze_document_with_ocr(bronze_key, file_bytes)
    fields = extraction["fields"]

    df = pd.DataFrame(
        [
            {
                "source_file": bronze_key,
                "ocr_engine": extraction["engine"],
                "document_type": fields["document_type"],
                "siret": fields["siret"],
                "amount_total": fields["amount_total"],
                "mentions_expired": fields["mentions_expired"],
                "ocr_text": fields["ocr_text"],
            }
        ]
    )

    silver_key = f"{bronze_key.rsplit('.', 1)[0]}.parquet"
    upload_parquet_with_key(df, "silver-zone", silver_key)

    return {
        "status": "success",
        "bronze_key": bronze_key,
        "silver_key": silver_key,
        "ocr_engine": extraction["engine"],
    }


@router.post("/api/v1/internal/process/silver-to-gold")
async def process_silver_to_gold(payload: dict):
    silver_key = payload.get("silver_key")
    if not silver_key:
        raise HTTPException(status_code=400, detail="silver_key is required")

    if not object_exists("silver-zone", silver_key):
        raise HTTPException(status_code=404, detail="Silver file not found")

    parquet_bytes = read_bytes_from_zone("silver-zone", silver_key)
    df = pd.read_parquet(io.BytesIO(parquet_bytes))
    scored_df = compute_fraud_scores(df)
    scored_df = apply_advanced_validation(scored_df)
    scored_df = add_ml_detection(scored_df)

    prefix = "high-risk/" if float(scored_df["fraud_score"].max()) > 0.8 else "standard/"
    gold_key = f"{prefix}{silver_key}"
    upload_parquet_with_key(scored_df, "gold-zone", gold_key)

    return {
        "status": "success",
        "silver_key": silver_key,
        "gold_key": gold_key,
        "fraud_score": float(scored_df["fraud_score"].iloc[0]),
        "risk_level": scored_df["risk_level"].iloc[0],
    }
