from __future__ import annotations

import pandas as pd

from services.fraud_service import REQUIRED_FIELDS_BY_DOC_TYPE, normalize_document_type


def apply_advanced_validation(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    statuts = []
    motifs = []

    for row in result.to_dict(orient="records"):
        issues = []
        doc_type = normalize_document_type(row.get("document_type"), row.get("source_file"))
        required_fields = REQUIRED_FIELDS_BY_DOC_TYPE.get(doc_type, set())

        if "siret" in required_fields and not row.get("siret"):
            issues.append("SIRET manquant")

        if doc_type == "unknown":
            issues.append("Type document inconnu")

        if row.get("mentions_expired"):
            issues.append("Document expire")

        amount_total = row.get("amount_total")
        try:
            if "amount_total" in required_fields and amount_total in (None, ""):
                issues.append("Montant manquant")
            elif amount_total not in (None, "") and float(amount_total) > 100000:
                issues.append("Montant suspect eleve")
        except (TypeError, ValueError):
            pass

        fraud_score = float(row.get("fraud_score") or 0)
        ml_probability = float(row.get("ml_probability") or 0)

        if fraud_score >= 0.75 or ml_probability >= 0.6:
            statut = "FRAUDE"
        elif fraud_score >= 0.45 or len(issues) >= 2:
            statut = "SUSPECT"
        else:
            statut = "OK"

        statuts.append(statut)
        motifs.append(", ".join(issues))

    result["statut_fraude"] = statuts
    result["motif"] = motifs

    return result


def add_ml_detection(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ml_flag"] = result["fraud_score"].apply(lambda value: 1 if float(value) >= 0.75 else 0)
    return result
