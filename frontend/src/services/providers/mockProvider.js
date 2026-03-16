import {
  DOCUMENT_STATUS,
  createEmptyDocumentStatusResponse
} from "../../constants/contracts";

const STORAGE_KEY = "idp_hackathon_documents";
const NETWORK_DELAY_MS = 550;

function delay(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function randomStatus(filename) {
  const normalized = filename.toLowerCase();
  if (
    normalized.includes("fraude") ||
    normalized.includes("faux") ||
    normalized.includes("fake") ||
    normalized.includes("expire")
  ) {
    return DOCUMENT_STATUS.FRAUDE;
  }

  return Math.random() > 0.22 ? DOCUMENT_STATUS.VALIDE : DOCUMENT_STATUS.FRAUDE;
}

function inferType(filename) {
  const value = filename.toLowerCase();

  if (value.includes("facture")) {
    return "FACTURE";
  }
  if (value.includes("devis")) {
    return "DEVIS";
  }
  if (value.includes("urssaf") || value.includes("attestation")) {
    return "ATTESTATION_URSSAF";
  }
  if (value.includes("kbis")) {
    return "KBIS";
  }
  if (value.includes("rib")) {
    return "RIB";
  }

  return "AUTRE";
}

function buildReason(status) {
  if (status === DOCUMENT_STATUS.VALIDE) {
    return "Aucune incoherence detectee";
  }

  const reasons = [
    "SIRET incoherent avec les pieces associees",
    "Date d'attestation depassee",
    "Montant HT/TVA/TTC non coherent",
    "Confiance OCR trop faible"
  ];
  return reasons[Math.floor(Math.random() * reasons.length)];
}

/**
 * @returns {import("../../constants/contracts").DocumentStatusItem[]}
 */
function readRecords() {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * @param {import("../../constants/contracts").DocumentStatusItem[]} records
 */
function saveRecords(records) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
}

function createSeedRecords() {
  const now = Date.now();
  const seed = [
    {
      id: "seed-1",
      filename: "facture_alpha_2026.pdf",
      docType: "FACTURE",
      status: DOCUMENT_STATUS.VALIDE,
      reason: "Aucune incoherence detectee",
      createdAt: new Date(now - 3600_000 * 18).toISOString()
    },
    {
      id: "seed-2",
      filename: "attestation_urssaf_expiree.pdf",
      docType: "ATTESTATION_URSSAF",
      status: DOCUMENT_STATUS.FRAUDE,
      reason: "Date d'attestation depassee",
      createdAt: new Date(now - 3600_000 * 7).toISOString()
    },
    {
      id: "seed-3",
      filename: "devis_beta_2026.pdf",
      docType: "DEVIS",
      status: DOCUMENT_STATUS.VALIDE,
      reason: "Aucune incoherence detectee",
      createdAt: new Date(now - 3600_000 * 2).toISOString()
    }
  ];

  saveRecords(seed);
  return seed;
}

function ensureRecords() {
  const current = readRecords();
  if (current.length > 0) {
    return current;
  }

  return createSeedRecords();
}

export const mockProvider = {
  /**
   * @param {File[]} files
   * @returns {Promise<import("../../constants/contracts").UploadedDocument[]>}
   */
  async uploadDocuments(files) {
    await delay(NETWORK_DELAY_MS);

    if (!Array.isArray(files) || files.length === 0) {
      throw new Error("Aucun fichier a envoyer.");
    }

    const existing = ensureRecords();
    const now = Date.now();

    const newRecords = files.map((file, index) => {
      const status = randomStatus(file.name);
      const createdAt = new Date(now + index * 1000).toISOString();
      return {
        id:
          typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID()
            : `${Date.now()}-${index}`,
        filename: file.name,
        docType: inferType(file.name),
        status,
        reason: buildReason(status),
        createdAt
      };
    });

    saveRecords([...newRecords, ...existing]);

    return newRecords.map((record) => ({
      id: record.id,
      filename: record.filename,
      uploadedAt: record.createdAt
    }));
  },

  /**
   * @returns {Promise<import("../../constants/contracts").DocumentStatusResponse>}
   */
  async getDocumentStatuses() {
    await delay(NETWORK_DELAY_MS);

    const response = createEmptyDocumentStatusResponse();
    const items = ensureRecords();

    const valide = items.filter((item) => item.status === DOCUMENT_STATUS.VALIDE).length;
    const fraude = items.filter((item) => item.status === DOCUMENT_STATUS.FRAUDE).length;

    response.items = items;
    response.stats = {
      total: items.length,
      valide,
      fraude
    };
    return response;
  }
};
