/**
 * - mock: sans le back
 * - live: Avec 
 */
export const API_MODE = import.meta.env.VITE_API_MODE === "live" ? "live" : "mock";

/**
 * Url pour les appels api
 */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(
  /\/$/,
  ""
);

