import { useEffect, useMemo, useState } from "react";
import StatusBadge from "../components/StatusBadge";
import { DOCUMENT_FILTER, createEmptyDocumentStatusResponse } from "../constants/contracts";
import { getDocumentStatuses } from "../services/apiClient";
import { formatDateTime, getTypeLabel } from "../utils/format";
  

function CompliancePage() {
  const [filter, setFilter] = useState(DOCUMENT_FILTER.TOUS);
  const [response, setResponse] = useState(createEmptyDocumentStatusResponse());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDocuments() {
    setLoading(true);
    setError("");
    try {
      const payload = await getDocumentStatuses();
      setResponse(payload);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Chargement impossible.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  const filteredItems = useMemo(() => {
    if (filter === DOCUMENT_FILTER.TOUS) {
      return response.items;
    }
    return response.items.filter((item) => item.status === filter);
  }, [filter, response.items]);

  const [fileUrl, setFileUrl] = useState(null);

  // Fonction appelée lorsqu'on clique sur le bouton "Voir le document"
  const handleViewDocument = async (filename) => {
    try {
      // On demande l'URL sécurisée au backend
      const response = await fetch(`http://localhost:8000/api/v1/documents/${filename}/url`);
      const data = await response.json();
      
      // On sauvegarde l'URL pour l'afficher
      if (data.url) {
        setFileUrl(data.url);
      }
    } catch (error) {
      console.error("Erreur lors de la récupération du fichier", error);
    }
  };

  return (
    <section className="space-y-5">
      <div className="panel flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl text-slate-900">Dashboard conformite</h2>
          <p className="text-sm text-slate-600">Suivi des documents valides et fraudes detectees</p>
        </div>
        <button type="button" onClick={loadDocuments} className="btn-ghost">
          Rafraichir
        </button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <article className="panel">
          <p className="text-sm text-slate-500">Total documents</p>
          <p className="mt-1 font-display text-2xl text-slate-900">{response.stats.total}</p>
        </article>
        <article className="panel">
          <p className="text-sm text-slate-500">Valides</p>
          <p className="mt-1 font-display text-2xl text-emerald-600">{response.stats.valide}</p>
        </article>
        <article className="panel">
          <p className="text-sm text-slate-500">Fraudes</p>
          <p className="mt-1 font-display text-2xl text-rose-600">{response.stats.fraude}</p>
        </article>
      </div>

      <div className="panel flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setFilter(DOCUMENT_FILTER.TOUS)}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            filter === DOCUMENT_FILTER.TOUS ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
          }`}
        >
          Tous
        </button>
        <button
          type="button"
          onClick={() => setFilter(DOCUMENT_FILTER.VALIDE)}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            filter === DOCUMENT_FILTER.VALIDE ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
          }`}
        >
          Valides
        </button>
        <button
          type="button"
          onClick={() => setFilter(DOCUMENT_FILTER.FRAUDE)}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            filter === DOCUMENT_FILTER.FRAUDE ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
          }`}
        >
          Fraudes
        </button>
      </div>

      <div className="panel overflow-x-auto">
        {loading ? (
          <p className="text-sm text-slate-600">Chargement des donnees...</p>
        ) : error ? (
          <p className="text-sm font-medium text-rose-700">{error}</p>
        ) : filteredItems.length === 0 ? (
          <p className="text-sm text-slate-600">Aucun document pour ce filtre.</p>
        ) : (
          <table className="min-w-full table-auto border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 text-sm text-slate-500">
                <th className="py-2 pr-4 font-semibold">Nom</th>
                <th className="py-2 pr-4 font-semibold">Type</th>
                <th className="py-2 pr-4 font-semibold">Statut</th>
                <th className="py-2 pr-4 font-semibold">Motif</th>
                <th className="py-2 pr-2 font-semibold">Date</th>
                <th className="py-2 pr-2 font-semibold">Voir</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((item) => (
                <tr key={item.id} className="border-b border-slate-100 text-sm text-slate-700">
                  <td className="py-3 pr-4">{item.filename}</td>
                  <td className="py-3 pr-4">{getTypeLabel(item.docType)}</td>
                  <td className="py-3 pr-4">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="py-3 pr-4">{item.reason}</td>
                  <td className="py-3 pr-2">{formatDateTime(item.createdAt)}</td>
                  <td className="py-3 pr-2">
                    <button 
                      onClick={() => handleViewDocument(item.filename)}
                      className="text-sm font-medium text-blue-600 transition hover:text-blue-800"
                    >
                      Voir
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modale Plein Écran pour la visionneuse de document */}
      {fileUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4 sm:p-6 backdrop-blur-sm">
          <div className="flex h-full w-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <h3 className="font-display text-lg text-slate-900">Visionneuse de document</h3>
              <button
                type="button"
                onClick={() => setFileUrl(null)}
                className="rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-200 hover:text-slate-900"
              >
                Fermer
              </button>
            </div>
            <div className="flex-1 bg-slate-100">
              <iframe 
                src={fileUrl} 
                className="h-full w-full border-none" 
                title="Visionneuse de document"
              />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default CompliancePage;
