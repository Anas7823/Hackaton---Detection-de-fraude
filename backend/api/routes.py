from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.minio_client import upload_to_bronze

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