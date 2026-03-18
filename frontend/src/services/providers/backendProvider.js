import { createEmptyDocumentStatusResponse } from "../../constants/contracts";
import { API_BASE_URL } from "../config";

const ENDPOINTS = Object.freeze({
  upload: ["/api/v1/upload", "/upload"],
  dashboard: ["/api/v1/dashboard", "/documents/status"]
});

function pickFirst(record, keys, fallback = "") {
  for (const key of keys) {
    if (record?.[key] !== undefined && record?.[key] !== null && record?.[key] !== "") {
      return record[key];
    }
  }
  return fallback;
}

function normalizeStatus(value) {
  const raw = String(value ?? "").toLowerCase();
  if (raw.includes("fraud") || raw.includes("anom") || raw.includes("ko") || raw === "1") {
    return "FRAUDE";
  }
  if (raw.includes("valid") || raw.includes("ok") || raw === "0") {
    return "VALIDE";
  }
  if (value === true) {
    return "FRAUDE";
  }
  if (value === false) {
    return "VALIDE";
  }
  return "VALIDE";
}

function normalizeFraudScore(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function normalizeDocType(value) {
  const raw = String(value ?? "").toLowerCase();
  if (raw.includes("facture")) {
    return "FACTURE";
  }
  if (raw.includes("invoice")) {
    return "FACTURE";
  }
  if (raw.includes("devis")) {
    return "DEVIS";
  }
  if (raw.includes("quote")) {
    return "DEVIS";
  }
  if (raw.includes("urssaf") || raw.includes("attestation")) {
    return "ATTESTATION_URSSAF";
  }
  if (raw.includes("kbis")) {
    return "KBIS";
  }
  if (raw.includes("rib")) {
    return "RIB";
  }
  return "AUTRE";
}

async function fetchJsonWithFallback(paths, init) {
  let lastError = null;

  for (const path of paths) {
    const response = await fetch(`${API_BASE_URL}${path}`, init);
    if (response.status === 404) {
      lastError = new Error(`Endpoint introuvable: ${path}`);
      continue;
    }
    if (!response.ok) {
      throw new Error(await parseError(response));
    }
    return response.json();
  }

  if (lastError) {
    throw lastError;
  }
  throw new Error("Aucun endpoint disponible.");
}

async function parseError(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
    if (typeof payload?.message === "string") {
      return payload.message;
    }
  } catch {
    // Keep generic fallback.
  }

  return `Erreur API (${response.status})`;
}

export const backendProvider = {
  async uploadDocuments(files) {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    const payload = await fetchJsonWithFallback(ENDPOINTS.upload, {
      method: "POST",
      body: formData
    });

    // Teammate contract: { details: { successful: [...], failed: [...] } }
    if (Array.isArray(payload?.details?.successful)) {
      return payload.details.successful.map((entry, index) => ({
        id:
          typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID()
            : `${Date.now()}-${index}`,
        filename: pickFirst(entry, ["filename", "name"], `document-${index + 1}`),
        uploadedAt: new Date().toISOString()
      }));
    }

    // Legacy/alternate contracts
    if (Array.isArray(payload)) {
      return payload;
    }
    if (Array.isArray(payload?.items)) {
      return payload.items;
    }

    return [];
  },

  async getDocumentStatuses() {
    const payload = await fetchJsonWithFallback(ENDPOINTS.dashboard);

    if (payload?.status === "empty") {
      return createEmptyDocumentStatusResponse();
    }

    if (Array.isArray(payload?.data)) {
      const items = payload.data.map((record, index) => {
        const filename = pickFirst(record, ["filename", "file_name", "document_name", "nom_document"], "document-inconnu");
        const rawType = pickFirst(record, ["docType", "document_type", "type", "doc_type"], filename);
        const rawStatus = pickFirst(
          record,
          ["status", "statut_fraude", "fraud_status", "is_fraud", "anomaly", "decision", "risk_level"],
          "VALIDE"
        );
        const reason = pickFirst(
          record,
          ["fraud_summary", "reason", "motif", "alert_reason", "anomaly_reason"],
          "Aucune alerte"
        );
        const createdAt = pickFirst(
          record,
          ["createdAt", "created_at", "timestamp", "date", "date_emission"],
          new Date().toISOString()
        );
        const previewUrl = pickFirst(record, ["preview_url", "previewUrl"], "");
        const fraudScore = normalizeFraudScore(pickFirst(record, ["fraud_score", "fraudScore"], 0));

        return {
          id: pickFirst(record, ["id", "_id"], `${Date.now()}-${index}`),
          filename,
          docType: normalizeDocType(rawType),
          status: normalizeStatus(rawStatus),
          reason,
          createdAt,
          previewUrl: previewUrl ? `${API_BASE_URL}${previewUrl}` : "",
          fraudSummary: reason,
          fraudScore
        };
      });

      const response = createEmptyDocumentStatusResponse();
      response.items = items;
      response.stats.total = items.length;
      response.stats.valide = items.filter((item) => item.status === "VALIDE").length;
      response.stats.fraude = items.filter((item) => item.status === "FRAUDE").length;
      return response;
    }
    if (payload?.items && payload?.stats) {
      return payload;
    }

    const empty = createEmptyDocumentStatusResponse();
    if (Array.isArray(payload)) {
      empty.items = payload;
      empty.stats.total = payload.length;
      empty.stats.valide = payload.filter((item) => item.status === "VALIDE").length;
      empty.stats.fraude = payload.filter((item) => item.status === "FRAUDE").length;
    }
    return empty;
  }
};
