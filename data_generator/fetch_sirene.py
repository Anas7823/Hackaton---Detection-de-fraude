"""
Récupération d'entreprises réelles via l'API Recherche Entreprises (data.gouv.fr).
API publique, sans clé d'authentification.
"""

import random
import requests
from models import Company
from config import SIRENE_API_URL, TEAM_MEMBERS

SEARCH_TERMS = [
    "boulangerie", "plomberie", "informatique", "restaurant",
    "consulting", "transport", "construction", "pharmacie",
    "architecte", "menuiserie", "electricien", "coiffure",
    "garage", "imprimerie", "librairie",
]


def fetch_companies_from_api(n: int = 15) -> list[Company]:
    """Récupère n entreprises réelles depuis l'API Sirene publique."""
    companies = []
    seen_sirets = set()

    for term in random.sample(SEARCH_TERMS, min(n, len(SEARCH_TERMS))):
        if len(companies) >= n:
            break

        try:
            resp = requests.get(
                SIRENE_API_URL,
                params={"q": term, "page": 1, "per_page": 5},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            for result in data.get("results", []):
                if len(companies) >= n:
                    break

                siege = result.get("siege", {})
                siret = siege.get("siret", "")
                siren = result.get("siren", "")

                if not siret or siret in seen_sirets:
                    continue

                adresse_parts = [
                    siege.get("numero_voie", ""),
                    siege.get("type_voie", ""),
                    siege.get("libelle_voie", ""),
                ]
                adresse = " ".join(p for p in adresse_parts if p).strip()
                if not adresse:
                    adresse = "1 rue de la Paix"

                dirigeant_name = ""
                dirigeants = result.get("dirigeants", [])
                if dirigeants:
                    d = dirigeants[0]
                    dirigeant_name = f"{d.get('prenom', '')} {d.get('nom', '')}".strip()

                if not dirigeant_name:
                    dirigeant_name = random.choice(TEAM_MEMBERS)

                company = Company(
                    siren=siren,
                    siret=siret,
                    nom=result.get("nom_complet", "Entreprise Inconnue"),
                    adresse=adresse,
                    code_postal=siege.get("code_postal", "75001"),
                    ville=siege.get("libelle_commune", "Paris"),
                    naf=result.get("activite_principale", "62.01Z"),
                    forme_juridique=result.get("nature_juridique", "SAS"),
                    date_creation=result.get("date_creation", "2020-01-01"),
                    dirigeant=dirigeant_name,
                    capital_social=random.choice([1000, 5000, 10000, 50000, 100000]),
                )
                companies.append(company)
                seen_sirets.add(siret)

        except requests.RequestException as e:
            print(f"[WARN] Erreur API pour '{term}': {e}")
            continue

    if len(companies) < n:
        print(f"[INFO] API: {len(companies)}/{n} entreprises. Complétion avec données Faker.")
        companies.extend(_generate_fallback_companies(n - len(companies), seen_sirets))

    return companies


def _generate_fallback_companies(n: int, seen_sirets: set) -> list[Company]:
    """Génère des entreprises fictives crédibles en cas d'échec API."""
    from faker import Faker

    fake = Faker("fr_FR")
    companies = []

    formes = ["SAS", "SARL", "EURL", "SA", "SCI"]
    activites = {
        "62.01Z": "Programmation informatique",
        "43.21A": "Travaux d'installation électrique",
        "56.10A": "Restauration traditionnelle",
        "47.11B": "Commerce d'alimentation générale",
        "71.12B": "Ingénierie, études techniques",
    }

    for _ in range(n):
        siren = "".join([str(random.randint(0, 9)) for _ in range(9)])
        nic = "".join([str(random.randint(0, 9)) for _ in range(5)])
        siret = siren + nic

        if siret in seen_sirets:
            continue

        naf = random.choice(list(activites.keys()))

        company = Company(
            siren=siren,
            siret=siret,
            nom=fake.company(),
            adresse=fake.street_address(),
            code_postal=fake.postcode(),
            ville=fake.city(),
            naf=naf,
            forme_juridique=random.choice(formes),
            date_creation=fake.date_between(start_date="-15y", end_date="-1y").isoformat(),
            dirigeant=random.choice(TEAM_MEMBERS),
            capital_social=random.choice([1000, 5000, 10000, 50000, 100000]),
        )
        companies.append(company)
        seen_sirets.add(siret)

    return companies


if __name__ == "__main__":
    print("Récupération des entreprises...")
    companies = fetch_companies_from_api(10)
    for c in companies:
        print(f"  {c.nom} | SIRET: {c.siret} | {c.ville}")
    print(f"\nTotal: {len(companies)} entreprises récupérées.")
