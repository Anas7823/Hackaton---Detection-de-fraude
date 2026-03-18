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
  const [selectedDocument, setSelectedDocument] = useState(null);

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
                <th className="py-2 pr-4 font-semibold">Resume fraude</th>
                <th className="py-2 pr-2 font-semibold">Date</th>
                <th className="py-2 font-semibold text-right">Voir</th>
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
                  <td className="py-3 pr-4">
                    <div className="max-w-md">
                      <p className="font-medium text-slate-700">{item.fraudSummary}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Score fraude : {(item.fraudScore ?? 0).toFixed(2)}
                      </p>
                    </div>
                  </td>
                  <td className="py-3 pr-2">{formatDateTime(item.createdAt)}</td>
                  <td className="py-3 text-right">
                    <button
                      type="button"
                      className="btn-ghost"
                      disabled={!item.previewUrl}
                      onClick={() => setSelectedDocument(item)}
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

      {selectedDocument ? (
        <div className="fixed inset-0 z-50 bg-slate-950/40 p-4 backdrop-blur-sm">
          <div className="mx-auto grid h-full max-w-6xl gap-4 overflow-hidden rounded-3xl bg-white p-4 shadow-2xl lg:grid-cols-[minmax(0,2fr)_360px]">
            <div className="flex min-h-[60vh] flex-col overflow-hidden rounded-2xl border border-slate-200">
              <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                <div>
                  <h3 className="font-display text-lg text-slate-900">{selectedDocument.filename}</h3>
                  <p className="text-sm text-slate-500">Previsualisation du document source</p>
                </div>
                <button type="button" className="btn-ghost" onClick={() => setSelectedDocument(null)}>
                  Fermer
                </button>
              </div>
              <iframe
                title={`Apercu de ${selectedDocument.filename}`}
                src={selectedDocument.previewUrl}
                className="h-full min-h-[55vh] w-full bg-slate-50"
              />
            </div>

            <aside className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Analyse fraude</p>
              <h4 className="mt-2 font-display text-xl text-slate-900">{selectedDocument.filename}</h4>
              <div className="mt-4">
                <StatusBadge status={selectedDocument.status} />
              </div>
              <div className="mt-5 space-y-4 text-sm text-slate-700">
                <div>
                  <p className="font-semibold text-slate-900">Resume</p>
                  <p className="mt-1 leading-6">{selectedDocument.fraudSummary}</p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Score de fraude</p>
                  <p className="mt-1 text-lg font-semibold text-slate-900">
                    {(selectedDocument.fraudScore ?? 0).toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Date de traitement</p>
                  <p className="mt-1">{formatDateTime(selectedDocument.createdAt)}</p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export default CompliancePage;

