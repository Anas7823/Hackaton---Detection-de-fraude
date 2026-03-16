from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

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
    return {"status": "healthy", "services": {"minio": "en attente de connexion"}}

