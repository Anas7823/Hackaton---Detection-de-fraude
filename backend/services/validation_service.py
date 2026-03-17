from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest


def apply_advanced_validation(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    statuts = []
    motifs = []

    for row in result.to_dict(orient="records"):

        issues = []

        if not row.get("siret"):
            issues.append("SIRET manquant")

        if row.get("document_type") == "unknown":
            issues.append("Type document inconnu")

        if row.get("mentions_expired"):
            issues.append("Document expiré")

        if row.get("amount_total") and row["amount_total"] > 100000:
            issues.append("Montant suspect élevé !! ")

        # classification
        if len(issues) >= 3:
            statut = "FRAUDE"
        elif len(issues) == 2:
            statut = "SUSPECT"
        else:
            statut = "OK"

        statuts.append(statut)
        motifs.append(", ".join(issues))

    result["statut_fraude"] = statuts
    result["motif"] = motifs

    return result


def add_ml_detection(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    try:
        model = IsolationForest(contamination=0.1)

        features = df[["amount_total"]].fillna(0)

        df["ml_flag"] = model.fit_predict(features)

    except Exception:
        df["ml_flag"] = 0 

    return df