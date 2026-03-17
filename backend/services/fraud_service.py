from __future__ import annotations

import pandas as pd


def compute_fraud_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    scores = []

    for row in result.to_dict(orient="records"):
        score = 0.1

        if not row.get("siret"):
            score += 0.35
        if row.get("document_type") == "unknown":
            score += 0.2
        if row.get("amount_total") in (None, ""):
            score += 0.15
        if row.get("mentions_expired"):
            score += 0.4

        scores.append(min(score, 1.0))

    result["fraud_score"] = scores
    result["risk_level"] = result["fraud_score"].apply(lambda value: "high" if value > 0.8 else "normal")
    return result
