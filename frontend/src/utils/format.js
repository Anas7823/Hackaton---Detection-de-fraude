import { DOCUMENT_TYPE_LABELS, STATUS_UI } from "../constants/contracts";

export function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

export function getTypeLabel(type) {
  return DOCUMENT_TYPE_LABELS[type] ?? DOCUMENT_TYPE_LABELS.AUTRE;
}

export function getStatusLabel(status) {
  return STATUS_UI[status]?.label ?? "Inconnu";
}

export function getStatusClass(status) {
  return STATUS_UI[status]?.className ?? "bg-slate-200 text-slate-700 ring-1 ring-slate-600/20";
}

