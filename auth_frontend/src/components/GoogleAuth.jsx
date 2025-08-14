import { useState } from 'react';

const GoogleAuth = ({ updateAuthStatus, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleGoogleAuth = async () => {
    setLoading(true);
    setResult(null);

    try {
      // Get Google OAuth URL from backend
      const response = await fetch('http://127.0.0.1:8001/auth/google/start');
      const data = await response.json();

      if (response.ok && data.auth_url) {
        // Redirect to Google OAuth
        window.location.href = data.auth_url;
      } else {
        setResult({ type: 'error', message: 'Failed to start Google authentication' });
      }
    } catch (error) {
      setResult({ type: 'error', message: 'Google authentication failed: ' + error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Google Authentication</h2>
      
      {result && (
        <div className={`result ${result.type}`}>
          {result.message}
        </div>
      )}

      <div className="google-auth-section">
        <p>Sign in with your Google account</p>
        
        <button 
          onClick={handleGoogleAuth} 
          className="btn btn-google"
          disabled={loading}
        >
          {loading ? 'Connecting...' : 'Sign in with Google'}
        </button>
      </div>
    </div>
  );
};

export default GoogleAuth;