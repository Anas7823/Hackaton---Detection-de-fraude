"""
Script principal : orchestre la generation du dataset.
- Recupere des entreprises reelles (API Sirene) + fallback Faker
- Genere des documents PDF legitimes
- Applique des degradations simulant des scans
- Produit un manifest des documents generes (Personne B consolide le ground_truth)
"""

import os
import random
import sys
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd

from config import (
    RAW_DIR, SCANS_DIR, OUTPUT_DIR,
    NUM_COMPANIES, NUM_DOCUMENTS_PER_COMPANY,
    RATIO_SANS_INTITULE,
)
from fetch_sirene import fetch_companies_from_api
from document_generator import (
    generate_invoice, generate_devis,
    generate_attestation_urssaf, generate_kbis, generate_rib,
    render_pdf,
)
from degrade_scans import degrade_image, pdf_to_image
from models import DocumentRecord


def main():
    print("=" * 60)
    print("  GÉNÉRATEUR DE DATASET - Détection de Fraude Documentaire")
    print("=" * 60)

    # --- Étape 1 : Récupérer les entreprises ---
    print(f"\n[1/5] Récupération de {NUM_COMPANIES} entreprises (API Sirene)...")
    companies = fetch_companies_from_api(NUM_COMPANIES)
    print(f"       -> {len(companies)} entreprises chargees.")

    # --- Étape 2 : Générer les documents ---
    print(f"\n[2/5] Génération des documents PDF...")
    records: list[DocumentRecord] = []
    doc_count = 0

    for i, company in enumerate(companies):
        client = random.choice([c for c in companies if c.siret != company.siret])
        company_dir_raw = RAW_DIR / company.siret
        company_dir_raw.mkdir(parents=True, exist_ok=True)

        doc_types_for_company = _pick_document_types(NUM_DOCUMENTS_PER_COMPANY)

        for doc_type in doc_types_for_company:
            show_titre = random.random() >= RATIO_SANS_INTITULE if doc_type in ("facture", "devis") else True

            try:
                doc, html = _generate_document(doc_type, company, client, show_titre)
            except Exception as e:
                print(f"  [WARN] Erreur generation {doc_type} pour {company.nom}: {e}")
                continue

            filename = f"{company.siret}_{doc_type}_{doc_count:04d}.pdf"
            pdf_path = company_dir_raw / filename

            try:
                render_pdf(html, pdf_path)
            except Exception as e:
                print(f"  [WARN] Erreur PDF {filename}: {e}")
                continue

            records.append(DocumentRecord(
                filename=filename,
                doc_type=doc_type,
                company_siret=company.siret,
                company_name=company.nom,
            ))
            doc_count += 1

        progress = (i + 1) / len(companies) * 100
        print(f"       [{progress:5.1f}%] {company.nom} -> {len(doc_types_for_company)} docs")

    print(f"       -> {doc_count} documents PDF generes.")

    # --- Étape 3 : Générer des scans dégradés ---
    print(f"\n[3/5] Génération des scans dégradés...")
    scan_count = 0
    pdf_files = list(RAW_DIR.rglob("*.pdf"))

    scan_ratio = 0.6
    pdfs_to_scan = random.sample(pdf_files, int(len(pdf_files) * scan_ratio))

    for pdf_path in pdfs_to_scan:
        try:
            img_path = pdf_to_image(pdf_path)
            scan_output = SCANS_DIR / pdf_path.relative_to(RAW_DIR).with_suffix(".png")
            scan_output.parent.mkdir(parents=True, exist_ok=True)
            degradation_info = degrade_image(img_path, scan_output)

            if img_path.exists() and img_path.suffix == ".png":
                img_path.unlink()

            scan_count += 1
        except Exception as e:
            print(f"  [WARN] Erreur scan {pdf_path.name}: {e}")

    print(f"       -> {scan_count} scans degrades generes.")

    # --- Étape 4 : Manifest des documents (Personne B consolide le ground_truth) ---
    print(f"\n[4/5] Generation du manifest documents.csv...")
    df = pd.DataFrame([
        {
            "filename": r.filename,
            "doc_type": r.doc_type,
            "company_siret": r.company_siret,
            "company_name": r.company_name,
        }
        for r in records
    ])

    csv_path = OUTPUT_DIR / "documents_manifest.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"       -> {csv_path}")

    # --- Étape 5 : Résumé ---
    print(f"\n[5/5] Resume du dataset")
    print("=" * 60)
    print(f"  Documents totaux   : {len(records)}")
    print(f"  Scans degrades    : {scan_count}")
    print(f"  Entreprises       : {len(companies)}")
    print()
    print("  Repartition par type de document :")
    for doc_type in df["doc_type"].unique():
        count = len(df[df["doc_type"] == doc_type])
        print(f"    {doc_type:<25s} : {count:3d} docs")

    print("\n" + "=" * 60)
    print(f"  Dataset sauvegardé dans : {OUTPUT_DIR.resolve()}")
    print("=" * 60)


def _pick_document_types(n: int) -> list[str]:
    """Sélectionne un mix réaliste de types de documents pour une entreprise."""
    must_have = ["facture", "attestation_urssaf"]
    optional = ["devis", "kbis", "rib"]
    remaining = max(0, n - len(must_have))
    extras = random.choices(optional + ["facture", "devis"], k=remaining)
    return must_have + extras


def _generate_document(doc_type, emetteur, client, show_titre: bool = True):
    if doc_type == "facture":
        return generate_invoice(emetteur, client, show_titre)
    elif doc_type == "devis":
        return generate_devis(emetteur, client, show_titre)
    elif doc_type == "attestation_urssaf":
        return generate_attestation_urssaf(emetteur)
    elif doc_type == "kbis":
        return generate_kbis(emetteur)
    elif doc_type == "rib":
        return generate_rib(emetteur)
    else:
        raise ValueError(f"Type de document inconnu: {doc_type}")


if __name__ == "__main__":
    main()
