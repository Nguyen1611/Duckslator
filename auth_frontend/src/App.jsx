// frontend/src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthTabs from './components/AuthTabs.jsx';
import ResetPassword from './components/ResetPassword.jsx';
import VerifyEmailSuccess from './components/VerifyEmailSuccess.jsx';
import OAuthCallback from './components/OAuthCallback.jsx';

export default function App() {
  return (
    <div className="App">
      <div className="container">
        <h1 className="app-title">Duckslator</h1>
        <p className="app-subtitle">Authentication System</p>
        <Routes>
          <Route path="/" element={<AuthTabs />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/auth/verify-email/:token" element={<VerifyEmailSuccess />} />
          <Route path="/oauth-callback" element={<OAuthCallback />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}