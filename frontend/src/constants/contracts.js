/**
 * @typedef {"VALIDE" | "FRAUDE"} DocumentStatus
 */

/**
 * @typedef {"FACTURE" | "DEVIS" | "ATTESTATION_URSSAF" | "KBIS" | "RIB" | "AUTRE"} DocumentType
 */

/**
 * @typedef {Object} UploadedDocument
 * @property {string} id
 * @property {string} filename
 * @property {string} uploadedAt
 */

/**
 * @typedef {Object} DocumentStatusItem
 * @property {string} id
 * @property {string} filename
 * @property {DocumentType} docType
 * @property {DocumentStatus} status
 * @property {string} reason
 * @property {string} createdAt
 */

/**
 * @typedef {Object} DocumentStatusResponse
 * @property {DocumentStatusItem[]} items
 * @property {{ total: number, valide: number, fraude: number }} stats
 */

export const DOCUMENT_STATUS = Object.freeze({
  VALIDE: "VALIDE",
  FRAUDE: "FRAUDE"
});

export const STATUS_UI = Object.freeze({
  [DOCUMENT_STATUS.VALIDE]: {
    label: "Validé",
    className: "bg-emerald-100 text-emerald-700 ring-1 ring-emerald-600/20"
  },
  [DOCUMENT_STATUS.FRAUDE]: {
    label: "Fraude",
    className: "bg-rose-100 text-rose-700 ring-1 ring-rose-600/20"
  }
});

export const DOCUMENT_TYPE_LABELS = Object.freeze({
  FACTURE: "Facture",
  DEVIS: "Devis",
  ATTESTATION_URSSAF: "Attestation URSSAF",
  KBIS: "Extrait Kbis",
  RIB: "RIB",
  AUTRE: "Autre"
});

export const DOCUMENT_FILTER = Object.freeze({
  TOUS: "TOUS",
  VALIDE: DOCUMENT_STATUS.VALIDE,
  FRAUDE: DOCUMENT_STATUS.FRAUDE
});

export const ALLOWED_EXTENSIONS = Object.freeze(["pdf", "png", "jpg", "jpeg"]);
export const ACCEPT_VALUE = ".pdf,.png,.jpg,.jpeg";

/**
 * @returns {DocumentStatusResponse}
 */
export function createEmptyDocumentStatusResponse() {
  return {
    items: [],
    stats: {
      total: 0,
      valide: 0,
      fraude: 0
    }
  };
}
