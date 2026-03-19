from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

GROUND_TRUTH_PATH = Path(__file__).resolve().parents[2] / "dataset" / "metadata" / "ground_truth.csv"
MODEL_VERSION = "ground-truth-naive-bayes-v1"
DOC_TYPES = {"facture", "devis", "attestation_urssaf", "kbis", "rib"}
REQUIRED_FIELDS_BY_DOC_TYPE = {
    "facture": {"siret", "amount_total"},
    "devis": {"siret", "amount_total"},
    "attestation_urssaf": {"siret"},
    "kbis": {"siret"},
    "rib": set(),
    "unknown": set(),
}
FEATURE_COLUMNS = [
    "doc_type",
    "has_siret",
    "amount_missing",
    "mentions_expired",
    "ocr_degraded",
    "is_image",
    "amount_band",
]


def normalize_document_type(value: object, source_file: object = "") -> str:
    raw = str(value or "").strip().lower()
    filename = str(source_file or "").strip().lower()

    if raw in {"invoice", "facture"}:
        return "facture"
    if raw in {"quote", "devis"}:
        return "devis"
    if "attestation" in raw or "urssaf" in raw:
        return "attestation_urssaf"
    if "kbis" in raw:
        return "kbis"
    if "rib" in raw:
        return "rib"

    if "facture" in filename:
        return "facture"
    if "devis" in filename:
        return "devis"
    if "attestation" in filename or "urssaf" in filename:
        return "attestation_urssaf"
    if "kbis" in filename:
        return "kbis"
    if "rib" in filename:
        return "rib"

    return "unknown"


def _is_ocr_degraded(engine: object) -> bool:
    return "fallback" in str(engine or "").lower() or "error" in str(engine or "").lower()


def _resolve_siret(row: dict) -> str:
    raw_siret = str(row.get("siret") or "").strip()
    if raw_siret:
        return raw_siret

    source_file = str(row.get("source_file") or "")
    match = re.match(r"^(\d{14})", source_file)
    return match.group(1) if match else ""


def _to_amount_band(value: object, q_low: float, q_mid: float) -> str:
    try:
        if value in (None, "") or pd.isna(value):
            return "missing"
        numeric = float(value)
    except (TypeError, ValueError):
        return "missing"

    if numeric <= q_low:
        return "low"
    if numeric <= q_mid:
        return "mid"
    return "high"


def _rule_score(row: dict, amount_upper_bounds: dict[str, float], company_amount_bounds: dict[tuple[str, str], tuple[float, float]]) -> float:
    doc_type = normalize_document_type(row.get("document_type"), row.get("source_file"))
    resolved_siret = _resolve_siret(row)
    required_fields = REQUIRED_FIELDS_BY_DOC_TYPE.get(doc_type, set())
    score = 0.05

    if row.get("mentions_expired"):
        score += 0.7

    if "siret" in required_fields and not row.get("siret"):
        score += 0.25

    if "amount_total" in required_fields and row.get("amount_total") in (None, ""):
        score += 0.25

    if doc_type == "unknown":
        score += 0.15

    if _is_ocr_degraded(row.get("ocr_engine")):
        score += 0.15

    amount_limit = amount_upper_bounds.get(doc_type)
    try:
        if amount_limit is not None and float(row.get("amount_total")) > amount_limit:
            score += 0.15
    except (TypeError, ValueError):
        pass

    try:
        company_bounds = company_amount_bounds.get((resolved_siret, doc_type))
        if company_bounds and row.get("amount_total") not in (None, ""):
            amount = float(row.get("amount_total"))
            lower_bound, upper_bound = company_bounds
            if amount < lower_bound or amount > upper_bound:
                score += 0.35
    except (TypeError, ValueError):
        pass

    return min(score, 1.0)


def _extract_training_features(df: pd.DataFrame) -> pd.DataFrame:
    training = df.copy()
    training["doc_type"] = training.apply(
        lambda row: normalize_document_type(row.get("doc_type"), row.get("filename")),
        axis=1,
    )
    training["has_siret"] = training["siret_doc"].fillna("").astype(str).str.strip().ne("")
    training["amount_missing"] = pd.to_numeric(training["montant_ttc"], errors="coerce").isna()
    training["mentions_expired"] = pd.to_datetime(training["date_expiration"], errors="coerce").lt(
        pd.Timestamp.now().normalize()
    )
    training["ocr_degraded"] = training["degradation"].fillna("none").astype(str).str.lower().ne("none")
    training["is_image"] = training["filename"].fillna("").astype(str).str.lower().str.endswith((".png", ".jpg", ".jpeg"))

    amount_series = pd.to_numeric(training["montant_ttc"], errors="coerce")
    valid_amounts = amount_series.dropna()
    q_low = float(valid_amounts.quantile(0.33)) if not valid_amounts.empty else 0.0
    q_mid = float(valid_amounts.quantile(0.66)) if not valid_amounts.empty else q_low
    training["amount_band"] = amount_series.apply(lambda value: _to_amount_band(value, q_low, q_mid))

    return training, q_low, q_mid


@lru_cache(maxsize=1)
def _train_fraud_model() -> dict:
    if not GROUND_TRUTH_PATH.exists():
        return {
            "available": False,
            "q_low": 0.0,
            "q_mid": 0.0,
            "class_counts": {0: 1, 1: 1},
            "feature_counts": {column: {0: {}, 1: {}} for column in FEATURE_COLUMNS},
            "feature_values": {column: set() for column in FEATURE_COLUMNS},
            "amount_upper_bounds": {},
            "company_amount_bounds": {},
            "doc_type_fraud_rates": {},
        }

    df = pd.read_csv(GROUND_TRUTH_PATH)
    training, q_low, q_mid = _extract_training_features(df)

    class_counts = {0: 0, 1: 0}
    feature_counts = {column: {0: {}, 1: {}} for column in FEATURE_COLUMNS}
    feature_values = {column: set() for column in FEATURE_COLUMNS}

    for row in training.to_dict(orient="records"):
        label = int(row["is_fraud"])
        class_counts[label] += 1

        for column in FEATURE_COLUMNS:
            value = str(row[column])
            feature_values[column].add(value)
            feature_counts[column][label][value] = feature_counts[column][label].get(value, 0) + 1

    legit_rows = training[training["is_fraud"] == 0].copy()
    legit_rows["montant_ttc"] = pd.to_numeric(legit_rows["montant_ttc"], errors="coerce")
    amount_upper_bounds = {}
    for doc_type, group in legit_rows.groupby("doc_type"):
        amounts = group["montant_ttc"].dropna()
        if not amounts.empty:
            amount_upper_bounds[doc_type] = float(amounts.quantile(0.95))

    company_amount_bounds = {}
    grouped_company = legit_rows.groupby(["siret_doc", "doc_type"])
    for (siret_doc, doc_type), group in grouped_company:
        amounts = group["montant_ttc"].dropna()
        if len(amounts) >= 2:
            company_amount_bounds[(str(siret_doc), doc_type)] = (
                float(amounts.quantile(0.05)),
                float(amounts.quantile(0.95)),
            )

    doc_type_fraud_rates = (
        training.groupby("doc_type")["is_fraud"].mean().to_dict()
        if not training.empty
        else {}
    )

    return {
        "available": True,
        "q_low": q_low,
        "q_mid": q_mid,
        "class_counts": class_counts,
        "feature_counts": feature_counts,
        "feature_values": feature_values,
        "amount_upper_bounds": amount_upper_bounds,
        "company_amount_bounds": company_amount_bounds,
        "doc_type_fraud_rates": doc_type_fraud_rates,
    }


def _row_to_model_features(row: dict, model: dict) -> dict:
    doc_type = normalize_document_type(row.get("document_type"), row.get("source_file"))
    return {
        "doc_type": doc_type,
        "has_siret": bool(row.get("siret")),
        "amount_missing": row.get("amount_total") in (None, ""),
        "mentions_expired": bool(row.get("mentions_expired")),
        "ocr_degraded": _is_ocr_degraded(row.get("ocr_engine")),
        "is_image": str(row.get("source_file", "")).lower().endswith((".png", ".jpg", ".jpeg")),
        "amount_band": _to_amount_band(row.get("amount_total"), model["q_low"], model["q_mid"]),
    }


def _predict_ml_probability(row: dict, model: dict) -> float:
    if not model["available"]:
        return 0.0

    features = _row_to_model_features(row, model)
    total = sum(model["class_counts"].values())
    log_probabilities = {}

    for label in (0, 1):
        prior = (model["class_counts"][label] + 1) / (total + 2)
        log_probability = math.log(prior)

        for column in FEATURE_COLUMNS:
            value = str(features[column])
            domain_size = len(model["feature_values"][column]) + 1
            count = model["feature_counts"][column][label].get(value, 0)
            conditional = (count + 1) / (model["class_counts"][label] + domain_size)
            log_probability += math.log(conditional)

        log_probabilities[label] = log_probability

    max_log = max(log_probabilities.values())
    fraud_exp = math.exp(log_probabilities[1] - max_log)
    legit_exp = math.exp(log_probabilities[0] - max_log)
    return fraud_exp / (fraud_exp + legit_exp)


def compute_fraud_scores(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    model = _train_fraud_model()

    fraud_scores = []
    ml_probabilities = []
    model_versions = []
    risk_levels = []

    for row in result.to_dict(orient="records"):
        ml_probability = _predict_ml_probability(row, model)
        rule_score = _rule_score(row, model["amount_upper_bounds"], model["company_amount_bounds"])
        doc_type = normalize_document_type(row.get("document_type"), row.get("source_file"))
        prior = float(model["doc_type_fraud_rates"].get(doc_type, 0.18))

        blended_score = max(rule_score, (ml_probability * 0.45) + (rule_score * 0.45) + (prior * 0.10))
        if row.get("mentions_expired"):
            blended_score = max(blended_score, 0.9)

        blended_score = min(blended_score, 1.0)
        fraud_scores.append(round(blended_score, 4))
        ml_probabilities.append(round(ml_probability, 4))
        model_versions.append(MODEL_VERSION if model["available"] else "rules-only")
        risk_levels.append("high" if blended_score >= 0.75 else "normal")

    result["fraud_score"] = fraud_scores
    result["ml_probability"] = ml_probabilities
    result["model_version"] = model_versions
    result["risk_level"] = risk_levels
    return result
