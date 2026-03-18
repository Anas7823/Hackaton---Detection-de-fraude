/**
 * Template pour connecter le backend
 *
 * How to use:
 * 1) Keep page code untouched (Upload/Compliance already call apiClient only).
 * 2) Implement real fetch logic in this file.
 * 3) Ensure VITE_API_MODE=live.
 * 4) Ignore mockProvider.js entirely during integration.
 */
export const backendProviderTemplate = {
  /**
   * @param {File[]} files
   * @returns {Promise<Array<{id: string, filename: string, uploadedAt: string}>>}
   */
  async uploadDocuments(files) {
    // TODO: replace with real POST /upload (multipart files[])
    // Example:
    // const formData = new FormData();
    // files.forEach((file) => formData.append("files", file));
    // const response = await fetch(`${API_BASE_URL}/upload`, { method: "POST", body: formData });
    // return await response.json();
    throw new Error("Template only: implement uploadDocuments in backendProvider.js");
  },

  /**
   * @returns {Promise<{items: Array<{id: string, filename: string, docType: string, status: string, reason: string, createdAt: string}>, stats: {total: number, valide: number, fraude: number}}>}
   */
  async getDocumentStatuses() {
    // TODO: replace with real GET /documents/status
    // Example:
    // const response = await fetch(`${API_BASE_URL}/documents/status`);
    // return await response.json();
    throw new Error("Template only: implement getDocumentStatuses in backendProvider.js");
  }
};

