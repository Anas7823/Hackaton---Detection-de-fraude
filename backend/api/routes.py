from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.minio_client import upload_to_bronze
from services.db_client import query_gold_zone, query_raw_documents, query_raw_companies

router = APIRouter()

@router.post("/api/v1/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Route pour uploader un ou plusieurs documents administratifs sensibles"""
    
    # On prépare des listes pour faire un compte-rendu propre au Front-end
    results = {"successful": [], "failed": []}
    
    for file in files:
        # 1. Vérification de sécurité pour chaque fichier
        if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
            results["failed"].append({"filename": file.filename, "reason": "Format rejeté - PDF/Image uniquement"})
            continue # On passe au fichier suivant sans bloquer le reste
        
        # 2. Upload dans le Data Lake (Zone Bronze)
        success = upload_to_bronze(file.file, file.filename)
        
        if success:
            results["successful"].append({"filename": file.filename, "zone": "bronze-zone"})
        else:
            results["failed"].append({"filename": file.filename, "reason": "Erreur d'écriture MinIO"})
    
    # Si l'utilisateur a envoyé des fichiers mais qu'ABSOLUMENT TOUT a échoué
    if not results["successful"] and files:
        raise HTTPException(status_code=500, detail="Échec de l'upload pour tous les fichiers.")
        
    # On renvoie un rapport détaillé au Front-end
    return {
        "status": "partial_success" if results["failed"] else "success",
        "message": f"{len(results['successful'])} fichier(s) sécurisé(s), {len(results['failed'])} échec(s).",
        "details": results
    }

@router.get("/api/v1/dashboard")
async def get_dashboard_data():
    """Récupère les résultats consolidés depuis la Gold Zone pour le dashboard"""
    data = query_gold_zone()
    
    if not data:
        return {
            "status": "empty",
            "message": "Aucune donnée analysée pour le moment",
            "data": []
        }
        
    return {
        "status": "success",
        "count": len(data),
        "data": data
    }


@router.get("/api/v1/documents")
async def get_raw_documents():
    """Récupère les documents générés par le data_generator (DuckDB + Parquet Gold zone)"""
    data = query_raw_documents()
    return {
        "status": "success" if data else "empty",
        "count": len(data),
        "data": data
    }


@router.get("/api/v1/companies")
async def get_raw_companies():
    """Récupère les entreprises du data_generator (DuckDB + Parquet Gold zone)"""
    data = query_raw_companies()
    return {
        "status": "success" if data else "empty",
        "count": len(data),
        "data": data
    }