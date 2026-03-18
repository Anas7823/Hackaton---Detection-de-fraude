from __future__ import annotations

import io
import re
from typing import Any


def _extract_text_with_doctr(file_name: str, file_bytes: bytes) -> tuple[str, str]:
    from doctr.io import DocumentFile
    from doctr.models import ocr_predictor
    from doctr.models.preprocessor import pytorch as doctr_preprocessor_module
    from doctr.utils import multithreading as doctr_multithreading_module

    def _sequential_exec(func, seq, threads=None):
        return map(func, seq)

    doctr_multithreading_module.multithread_exec = _sequential_exec
    doctr_preprocessor_module.multithread_exec = _sequential_exec

    lower_name = file_name.lower()
    if lower_name.endswith(".pdf"):
        document = DocumentFile.from_pdf(io.BytesIO(file_bytes).read())
    else:
        document = DocumentFile.from_images([io.BytesIO(file_bytes).read()])

    predictor = ocr_predictor(pretrained=True)
    result = predictor(document)
    exported = result.export()

    words: list[str] = []
    for page in exported.get("pages", []):
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                for word in line.get("words", []):
                    value = word.get("value")
                    if value:
                        words.append(value)

    return " ".join(words), "doctr"


def _extract_text_fallback(file_bytes: bytes) -> tuple[str, str]:
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    return text, "fallback_text_reader"


def extract_document_fields(raw_text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", raw_text).strip()

    siret_match = re.search(r"(?:siret\D*)?(\d{14})", normalized, re.IGNORECASE)
    amount_match = re.search(r"(?:montant|total|ttc)[^\d]{0,20}(\d[\d\s]*[.,]\d{2})", normalized, re.IGNORECASE)
    invoice_match = re.search(r"\b(facture|invoice)\b", normalized, re.IGNORECASE)
    quote_match = re.search(r"\b(devis|quotation|quote)\b", normalized, re.IGNORECASE)
    expired_match = re.search(r"\b(expire|expired|invalide)\b", normalized, re.IGNORECASE)

    amount_value = None
    if amount_match:
        amount_value = float(amount_match.group(1).replace(" ", "").replace(",", "."))

    return {
        "document_type": "invoice" if invoice_match else "quote" if quote_match else "unknown",
        "siret": siret_match.group(1) if siret_match else None,
        "amount_total": amount_value,
        "mentions_expired": bool(expired_match),
        "ocr_text": raw_text[:5000],
    }


def analyze_document_with_ocr(file_name: str, file_bytes: bytes) -> dict[str, Any]:
    lower_name = file_name.lower()
    if lower_name.endswith(".txt"):
        raw_text, engine = _extract_text_fallback(file_bytes)
        return {
            "engine": engine,
            "raw_text": raw_text[:5000],
            "fields": extract_document_fields(raw_text),
        }

    try:
        raw_text, engine = _extract_text_with_doctr(file_name, file_bytes)
    except Exception as exc:
        raw_text, engine = _extract_text_fallback(file_bytes)
        engine = f"{engine} ({exc.__class__.__name__})"

    enriched_text = raw_text
    if "facture" in lower_name and "facture" not in raw_text.lower():
        enriched_text = f"facture {enriched_text}"
    if "devis" in lower_name and "devis" not in raw_text.lower():
        enriched_text = f"devis {enriched_text}"

    return {
        "engine": engine,
        "raw_text": enriched_text[:5000],
        "fields": extract_document_fields(enriched_text),
    }
