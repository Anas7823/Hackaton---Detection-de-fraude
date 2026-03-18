const AUTH_STORAGE_KEY = "idp_hackathon_auth_session";

export const MOCK_CREDENTIALS = Object.freeze({
  username: "admin",
  password: "admin"
});

function readSession() {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveSession(session) {
  window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function getAuthSession() {
  return readSession();
}

export function isAuthenticated() {
  return Boolean(readSession()?.username);
}

export async function loginWithMock(username, password) {
  const normalizedUsername = String(username ?? "").trim();
  const normalizedPassword = String(password ?? "");

  if (
    normalizedUsername !== MOCK_CREDENTIALS.username ||
    normalizedPassword !== MOCK_CREDENTIALS.password
  ) {
    throw new Error("Identifiants invalides. Utilisez admin / admin.");
  }

  const session = {
    username: MOCK_CREDENTIALS.username,
    loggedInAt: new Date().toISOString()
  };

  saveSession(session);
  return session;
}

export function logout() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_STORAGE_KEY);
}
