import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginWithMock, MOCK_CREDENTIALS } from "../services/auth";

function LoginPage({ onLogin }) {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Connectez-vous pour acceder au dashboard.");

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("loading");
    setMessage("Verification des identifiants...");

    try {
      const session = await loginWithMock(username, password);
      onLogin(session);
      setStatus("success");
      setMessage("Connexion reussie.");
      navigate("/upload", { replace: true });
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Connexion impossible.");
    }
  }

  return (
    <section className="flex min-h-screen items-center justify-center px-4 py-8 sm:px-6">
      <div className="panel w-full max-w-md">
        <div className="mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Connexion
          </p>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="label-text">Utilisateur</span>
            <input
              className="input-field"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="admin"
            />
          </label>

          <label className="block">
            <span className="label-text">Mot de passe</span>
            <input
              className="input-field"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="admin"
            />
          </label>

          <button type="submit" className="btn-primary w-full" disabled={status === "loading"}>
            {status === "loading" ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Identifiants de demo : <span className="font-semibold">{MOCK_CREDENTIALS.username}</span> /{" "}
          <span className="font-semibold">{MOCK_CREDENTIALS.password}</span>
        </div>

        <div
          className={`mt-4 rounded-2xl border px-4 py-3 text-sm font-medium ${
            status === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : status === "error"
                ? "border-rose-200 bg-rose-50 text-rose-700"
                : "border-slate-200 bg-slate-50 text-slate-600"
          }`}
        >
          {message}
        </div>
      </div>
    </section>
  );
}

export default LoginPage;
