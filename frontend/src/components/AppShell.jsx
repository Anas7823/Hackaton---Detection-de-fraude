import { NavLink, Outlet } from "react-router-dom";
import { API_MODE } from "../services/config";

function navClassName({ isActive }) {
  if (isActive) {
    return "rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white";
  }
  return "rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900";
}

function AppShell({ session, onLogout }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col p-4 sm:p-6">
      <header className="panel mb-5 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-base-600">
            Hackathon
          </p>
          <h1 className="font-display text-2xl text-base-700">Classification de documents</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <nav className="flex rounded-xl border border-slate-200 p-1">
            <NavLink to="/upload" className={navClassName}>
              Upload
            </NavLink>
            <NavLink to="/conformite" className={navClassName}>
              Conformite
            </NavLink>
          </nav>
          {/* Verifier le mode API */}
          {/* <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase text-slate-600">
            Mode API: {API_MODE}
          </span> */}
          <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase text-white">
            Connecte: {session?.username ?? "demo"}
          </span>
          <button type="button" onClick={onLogout} className="btn-ghost">
            Deconnexion
          </button>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
