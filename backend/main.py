from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from services.minio_client import get_minio_client

app = FastAPI(
    title="API IDP - Traitement de Documents Administratifs",
    description="API permettant l'ingestion et l'orchestration de l'OCR.",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod, remplacer "*" par "http://localhost:3000"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/")
def read_root():
    return {"status": "success", "message": "Le Backend FastAPI est opérationnel.", "message" : "Bienvenue sur l'API IDP. L'architecture est opérationnelle."}

@app.get("/health")
def health_check():
    """Vérifie la santé de l'API et la connexion réelle au Data Lake"""
    health_status = {
        "status": "up",
        "database": "duckdb_in_memory",
        "storage": {"status": "down", "buckets": []}
    }
    
    try:
        # On tente de lister les buckets pour vérifier la connexion réelle
        s3 = get_minio_client()
        response = s3.list_buckets()
        buckets = [b['Name'] for b in response['Buckets']]
        
        health_status["storage"]["status"] = "connected"
        health_status["storage"]["buckets"] = buckets
        
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["storage"]["status"] = f"error: {str(e)}"
    
    return health_status
