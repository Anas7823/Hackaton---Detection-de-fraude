from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    # Override avec .env local pour exécution sur l'hôte (localhost au lieu de minio)
    load_dotenv(Path(__file__).parent / ".env", override=True)
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
RAW_DIR = OUTPUT_DIR / "raw"
SCANS_DIR = OUTPUT_DIR / "scans"

SIRENE_API_URL = "https://recherche-entreprises.api.gouv.fr/search"

DOCUMENT_TYPES = ["facture", "devis", "attestation_urssaf", "kbis", "rib"]

TVA_RATES = [0.055, 0.10, 0.20]

NUM_COMPANIES = 50
NUM_DOCUMENTS_PER_COMPANY = 10
# Nombre de documents variable par entreprise (min, max)
DOCS_PER_COMPANY_MIN = 8
DOCS_PER_COMPANY_MAX = 12

# Ratio de documents SANS intitulé explicite (FACTURE/DEVIS) - plus réaliste pour la classification
RATIO_SANS_INTITULE = 0.25

# Ratio de documents frauduleux (faux) dans le dataset
RATIO_FRAUDE = 0.20

TEAM_MEMBERS = [
    "Ismaël Cerezo",
    "Anas El Khiat",
    "Julien Hanslik",
    "Evans Kouassi",
    "Chaimae Hmamed",
    "Frederick Toufik"
    "Romain Liénard",
]
