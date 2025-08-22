// frontend/src/App.jsx
import { Routes, Route, Navigate, Link } from 'react-router-dom';
import AuthTabs from './components/AuthTabs.jsx';
import ResetPassword from './components/ResetPassword.jsx';
import VerifyEmailSuccess from './components/VerifyEmailSuccess.jsx';
import OAuthCallback from './components/OAuthCallback.jsx';
import JobsList from './components/JobsList.jsx';
import JobUpload from './components/JobUpload.jsx';
import JobDetail from './components/JobDetail.jsx';
import { useAuth } from './components/AuthContext.jsx';

export default function App() {
  const { isLoggedIn } = useAuth();
  return (
    <div className="App">
      <div className="container">
        <h1 className="app-title">Duckslator</h1>
        <p className="app-subtitle">Authentication & Jobs</p>
        <nav style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <Link to="/">Auth</Link>
          {isLoggedIn && <Link to="/jobs">Jobs</Link>}
        </nav>
        <Routes>
          <Route path="/" element={<AuthTabs />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/auth/verify-email/:token" element={<VerifyEmailSuccess />} />
          <Route path="/oauth-callback" element={<OAuthCallback />} />
          <Route path="/jobs" element={isLoggedIn ? <JobsList /> : <Navigate to="/" replace />} />
          <Route path="/jobs/upload" element={isLoggedIn ? <JobUpload /> : <Navigate to="/" replace />} />
          <Route path="/jobs/:jobId" element={isLoggedIn ? <JobDetail /> : <Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}