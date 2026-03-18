import { API_MODE } from "./config";
import { backendProvider } from "./providers/backendProvider";
import { mockProvider } from "./providers/mockProvider";

const providerByMode = Object.freeze({
  mock: mockProvider,
  live: backendProvider
});

export function getActiveProvider() {
  return providerByMode[API_MODE] ?? mockProvider;
}

