import { createEmptyDocumentStatusResponse } from "../constants/contracts";
import { API_MODE } from "./config";
import { getActiveProvider } from "./providerFactory";

const activeProvider = getActiveProvider();

function asString(value, fallback = "") {
  return typeof value === "string" ? value : fallback;
}

function normalizeUploadedDocument(item, index) {
  return {
    id: asString(item?.id, `${Date.now()}-${index}`),
    filename: asString(item?.filename, "document-inconnu"),
    uploadedAt: asString(item?.uploadedAt, new Date().toISOString())
  };
}

function normalizeStatusItem(item, index) {
  return {
    id: asString(item?.id, `${Date.now()}-${index}`),
    filename: asString(item?.filename, "document-inconnu"),
    docType: asString(item?.docType, "AUTRE"),
    status: asString(item?.status, "FRAUDE"),
    reason: asString(item?.reason, "Motif indisponible"),
    createdAt: asString(item?.createdAt, new Date().toISOString()),
    previewUrl: asString(item?.previewUrl),
    fraudSummary: asString(item?.fraudSummary, "Resume indisponible"),
    fraudScore: typeof item?.fraudScore === "number" ? item.fraudScore : 0
  };
}

/**
 * @param {File[]} files
 * @returns {Promise<import("../constants/contracts").UploadedDocument[]>}
 */
export async function uploadDocuments(files) {
  const payload = await activeProvider.uploadDocuments(files);
  const list = Array.isArray(payload) ? payload : [];
  return list.map(normalizeUploadedDocument);
}

/**
 * @returns {Promise<import("../constants/contracts").DocumentStatusResponse>}
 */
export async function getDocumentStatuses() {
  const payload = await activeProvider.getDocumentStatuses();
  const safePayload = payload ?? createEmptyDocumentStatusResponse();
  const items = Array.isArray(safePayload.items) ? safePayload.items : [];
  const normalizedItems = items.map(normalizeStatusItem);

  const validCount = normalizedItems.filter((item) => item.status === "VALIDE").length;
  const fraudCount = normalizedItems.filter((item) => item.status === "FRAUDE").length;

  return {
    items: normalizedItems,
    stats: {
      total: normalizedItems.length,
      valide: validCount,
      fraude: fraudCount
    }
  };
}
