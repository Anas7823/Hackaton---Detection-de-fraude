import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import CompliancePage from "./pages/CompliancePage";
import LoginPage from "./pages/LoginPage";
import UploadPage from "./pages/UploadPage";
import { getAuthSession, logout } from "./services/auth";

function App() {
  const [session, setSession] = useState(() => getAuthSession());
  const authenticated = Boolean(session?.username);

  function handleLogin(nextSession) {
    setSession(nextSession);
  }

  function handleLogout() {
    logout();
    setSession(null);
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            authenticated ? <Navigate to="/upload" replace /> : <LoginPage onLogin={handleLogin} />
          }
        />
        <Route
          element={
            authenticated ? <AppShell session={session} onLogout={handleLogout} /> : <Navigate to="/login" replace />
          }
        >
          <Route path="/" element={<Navigate to="/upload" replace />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/conformite" element={<CompliancePage />} />
        </Route>
        <Route path="*" element={<Navigate to={authenticated ? "/upload" : "/login"} replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

