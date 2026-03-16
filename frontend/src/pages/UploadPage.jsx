import { useMemo, useRef, useState } from "react";
import { ACCEPT_VALUE, ALLOWED_EXTENSIONS } from "../constants/contracts";
import { uploadDocuments } from "../services/apiClient";

// verif de l'extension du fichier
function isFileAllowed(file) {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return ALLOWED_EXTENSIONS.includes(extension);
}

// cree une signature pour eviter les doublons cote ui
function fileSignature(file) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const [uploadState, setUploadState] = useState("idle");
  const [message, setMessage] = useState("Selectionnez un ou plusieurs documents a uploader.");
  const inputRef = useRef(null);
  const totalCount = selectedFiles.length;
  const hasFiles = totalCount > 0;

  const acceptedListText = useMemo(() => ALLOWED_EXTENSIONS.map((ext) => `.${ext}`).join(", "), []);

  function pushFiles(fileList) {
    const incoming = Array.from(fileList ?? []);
    if (!incoming.length) {
      return;
    }

    const invalid = incoming.filter((file) => !isFileAllowed(file));
    const valid = incoming.filter((file) => isFileAllowed(file));

    setSelectedFiles((current) => {
      const signatures = new Set(current.map((item) => fileSignature(item.file)));
      const additions = valid
        .filter((file) => !signatures.has(fileSignature(file)))
        .map((file) => ({
          id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : fileSignature(file),
          file
        }));
      return [...current, ...additions];
    });

    if (invalid.length > 0) {
      setUploadState("error");
      setMessage(`Formats non autorises: ${invalid.map((file) => file.name).join(", ")}`);
      return;
    }

    setUploadState("idle");
    setMessage("Fichiers prets. Cliquez sur Envoyer.");
  }

  function handleInputChange(event) {
    pushFiles(event.target.files);
  }

  function removeFile(id) {
    setSelectedFiles((current) => current.filter((entry) => entry.id !== id));
    setUploadState("idle");
    setMessage("Selection mise a jour.");
  }

  function handleDragOver(event) {
    event.preventDefault();
    setIsDragActive(true);
  }

  function handleDragLeave(event) {
    event.preventDefault();
    setIsDragActive(false);
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragActive(false);
    pushFiles(event.dataTransfer.files);
  }

  async function handleSubmit() {
    if (!hasFiles) {
      setUploadState("error");
      setMessage("Ajoutez au moins un fichier avant l'envoi.");
      return;
    }

    setUploadState("loading");
    setMessage("Envoi en cours...");

    try {
      const files = selectedFiles.map((entry) => entry.file);
      const uploaded = await uploadDocuments(files);
      setUploadState("success");
      setMessage(`${uploaded.length} document(s) envoye(s) avec succes.`);
      setSelectedFiles([]);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (error) {
      setUploadState("error");
      setMessage(error instanceof Error ? error.message : "Echec de l'envoi.");
    }
  }

  return (
    <section className="space-y-5">
      <div className="panel">
        <h2 className="font-display text-xl text-slate-900">Upload  de documents</h2>
        <p className="mt-1 text-sm text-slate-600">Formats acceptes: {acceptedListText}</p>
      </div> 
      <div
        className={`panel border-2 border-dashed transition ${
          isDragActive ? "border-slate-900 bg-slate-50" : "border-slate-300"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <p className="font-medium text-slate-800">Glissez-deposez vos PDF ou images ici</p>
          <p className="mt-2 text-sm text-slate-500">ou selectionnez les fichiers manuellement</p>
          <label className="btn-ghost mt-4 cursor-pointer">
            Choisir des fichiers
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              accept={ACCEPT_VALUE}
              multiple
              onChange={handleInputChange}
            />
          </label>
        </div>
      </div>
      <div className="panel">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-display text-lg text-slate-900">Fichiers selectionnes ({totalCount})</h3>
          <button
            type="button"
            className="btn-primary"
            disabled={uploadState === "loading"}
            onClick={handleSubmit}
          >
            {uploadState === "loading" ? "Envoi..." : "Envoyer"}
          </button>
        </div>
        {hasFiles ? (
          <ul className="space-y-2">
            {selectedFiles.map((entry) => (
              <li
                key={entry.id}
                className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2"
              >
                <span className="truncate text-sm text-slate-700">{entry.file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(entry.id)}
                  className="text-sm font-medium text-rose-600 transition hover:text-rose-800"
                >
                  Retirer
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Aucun fichier selectionne.</p>
        )}
      </div>
      <div
        className={`panel ${
          uploadState === "success"
            ? "border-emerald-300 bg-emerald-50"
            : uploadState === "error"
              ? "border-rose-300 bg-rose-50"
              : "border-slate-200"
        }`}
      >
        <p className="text-sm font-medium text-slate-700">{message}</p>
      </div>
    </section>
  );
}
export default UploadPage;
