from __future__ import annotations

import csv
import re
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data_generator" / "output" / "documents_manifest.csv"
RAW_DIR = REPO_ROOT / "data_generator" / "output" / "raw"
RAW_FRAUD_DIR = REPO_ROOT / "data_generator" / "output" / "raw_fraud"
SCANS_DIR = REPO_ROOT / "data_generator" / "output" / "scans"
SCANS_FRAUD_DIR = REPO_ROOT / "data_generator" / "output" / "scans_fraud"
GROUND_TRUTH_PATH = REPO_ROOT / "dataset" / "metadata" / "ground_truth.csv"

HEADERS = [
    "filename",
    "doc_type",
    "is_fraud",
    "fraud_type",
    "siret_doc",
    "date_expiration",
    "montant_ht",
    "montant_ttc",
    "degradation",
    "linked_group_id",
    "source_dataset_path",
]

SUPPORTED_DOC_TYPES = {"facture", "attestation_urssaf", "devis", "kbis", "rib"}

AMOUNT_RE = r"([0-9][0-9\s]*[.,][0-9]{2})"


def parse_bool(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y"}


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def normalize_amount(value: str | None) -> str:
    if not value:
        return ""
    return value.replace(" ", "").replace(",", ".").strip()


def normalize_date(value: str | None) -> str:
    if not value:
        return ""
    day, month, year = value.split("/")
    return f"{year}-{month}-{day}"


def extract_siret(text: str, fallback_siret: str) -> str:
    sirets = re.findall(r"SIRET\s*[:\(]?\s*(\d{14})", text, re.IGNORECASE)
    if fallback_siret in sirets:
        return fallback_siret
    return sirets[0] if sirets else fallback_siret


def extract_invoice_fields(text: str, fallback_siret: str) -> tuple[str, str, str]:
    siret_doc = extract_siret(text, fallback_siret)

    total_ht_match = re.search(rf"Total HT\s+{AMOUNT_RE}\s*€", text, re.IGNORECASE)
    total_ttc_match = re.search(rf"Total TTC\s+{AMOUNT_RE}\s*€", text, re.IGNORECASE)

    montant_ht = normalize_amount(total_ht_match.group(1) if total_ht_match else None)
    montant_ttc = normalize_amount(total_ttc_match.group(1) if total_ttc_match else None)
    return siret_doc, montant_ht, montant_ttc


def extract_quote_fields(text: str, fallback_siret: str) -> tuple[str, str, str]:
    siret_doc = extract_siret(text, fallback_siret)

    total_ht_match = re.search(rf"Total HT\s+{AMOUNT_RE}\s*€", text, re.IGNORECASE)
    total_ttc_match = re.search(rf"Total TTC\s+{AMOUNT_RE}\s*€", text, re.IGNORECASE)

    montant_ht = normalize_amount(total_ht_match.group(1) if total_ht_match else None)
    montant_ttc = normalize_amount(total_ttc_match.group(1) if total_ttc_match else None)
    return siret_doc, montant_ht, montant_ttc


def extract_attestation_fields(text: str, fallback_siret: str) -> tuple[str, str]:
    siret_doc = extract_siret(text, fallback_siret)
    validity_match = re.search(r"Du\s+(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})", text)
    expiration_date = normalize_date(validity_match.group(2) if validity_match else None)
    return siret_doc, expiration_date


def extract_kbis_fields(text: str, fallback_siret: str) -> str:
    match = re.search(r"SIRET\s*\(siège\)\s*:\s*(\d{14})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return extract_siret(text, fallback_siret)


def extract_rib_fields(text: str, fallback_siret: str) -> str:
    return extract_siret(text, fallback_siret)


def source_relative_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def resolve_pdf_path(company_siret: str, filename: str, is_fraud: bool, folder_hint: str) -> Path:
    candidates: list[Path] = []
    if folder_hint == "raw_fraud":
        candidates.append(RAW_FRAUD_DIR / company_siret / filename)
    elif folder_hint == "raw":
        candidates.append(RAW_DIR / company_siret / filename)
    else:
        preferred = RAW_FRAUD_DIR if is_fraud else RAW_DIR
        secondary = RAW_DIR if is_fraud else RAW_FRAUD_DIR
        candidates.extend([preferred / company_siret / filename, secondary / company_siret / filename])

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(f"Document introuvable (candidats: {candidates})")


def resolve_scan_path(company_siret: str, filename: str, is_fraud: bool, folder_hint: str) -> Path | None:
    scan_filename = Path(filename).with_suffix(".png")

    candidates: list[Path] = []
    if folder_hint == "raw_fraud":
        candidates.append(SCANS_FRAUD_DIR / company_siret / scan_filename)
    elif folder_hint == "raw":
        candidates.append(SCANS_DIR / company_siret / scan_filename)
    else:
        preferred = SCANS_FRAUD_DIR if is_fraud else SCANS_DIR
        secondary = SCANS_DIR if is_fraud else SCANS_FRAUD_DIR
        candidates.extend([preferred / company_siret / scan_filename, secondary / company_siret / scan_filename])

    for path in candidates:
        if path.exists():
            return path
    return None


def build_rows_from_manifest() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as manifest_file:
        reader = csv.DictReader(manifest_file)
        for entry in reader:
            raw_doc_type = entry["doc_type"]
            if raw_doc_type not in SUPPORTED_DOC_TYPES:
                continue

            filename = entry["filename"]
            company_siret = entry["company_siret"]
            is_fraud = parse_bool(entry.get("is_fraud"))
            type_fraud = (entry.get("fraud_type") or "").strip()
            folder_hint = (entry.get("folder") or "").strip().lower()
            pdf_path = resolve_pdf_path(company_siret, filename, is_fraud, folder_hint)

            pdf_text = extract_pdf_text(pdf_path)

            siret_doc = company_siret
            montant_ht = ""
            montant_ttc = ""
            date_expiration = ""

            if raw_doc_type == "facture":
                siret_doc, montant_ht, montant_ttc = extract_invoice_fields(pdf_text, company_siret)
            elif raw_doc_type == "devis":
                siret_doc, montant_ht, montant_ttc = extract_quote_fields(pdf_text, company_siret)
            elif raw_doc_type == "attestation_urssaf":
                siret_doc, date_expiration = extract_attestation_fields(pdf_text, company_siret)
            elif raw_doc_type == "kbis":
                siret_doc = extract_kbis_fields(pdf_text, company_siret)
            elif raw_doc_type == "rib":
                siret_doc = extract_rib_fields(pdf_text, company_siret)

            rows.append(
                {
                    "filename": filename,
                    "doc_type": raw_doc_type,
                    "is_fraud": "1" if is_fraud else "0",
                    "fraud_type": type_fraud,
                    "siret_doc": siret_doc,
                    "date_expiration": date_expiration,
                    "montant_ht": montant_ht,
                    "montant_ttc": montant_ttc,
                    "degradation": "none",
                    "linked_group_id": f"grp_{company_siret}",
                    "source_dataset_path": source_relative_path(pdf_path),
                }
            )

            scan_path = resolve_scan_path(company_siret, filename, is_fraud, folder_hint)
            if scan_path is not None:
                scan_filename = scan_path.name

                rows.append(
                    {
                        "filename": scan_filename,
                        "doc_type": raw_doc_type,
                        "is_fraud": "1" if is_fraud else "0",
                        "fraud_type": type_fraud,
                        "siret_doc": siret_doc,
                        "date_expiration": date_expiration,
                        "montant_ht": montant_ht,
                        "montant_ttc": montant_ttc,
                        "degradation": "scan_degraded",
                        "linked_group_id": f"grp_{company_siret}",
                        "source_dataset_path": source_relative_path(scan_path),
                    }
                )

    return rows


def write_ground_truth(rows: list[dict[str, str]], output_path: Path = GROUND_TRUTH_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows_from_manifest()
    write_ground_truth(rows)
    print(f"Ground truth généré: {GROUND_TRUTH_PATH}")
    print("Matérialisation locale: inactive")
    print(f"Nombre de lignes écrites: {len(rows)}")


if __name__ == "__main__":
    main()