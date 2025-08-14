import { useState } from 'react';

const ResendEmail = ({ onSuccess }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setResult({ type: 'error', message: 'Please enter your email address' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const url = `http://127.0.0.1:8001/auth/resend-verification-email?email=${encodeURIComponent(email.trim())}`;
      
      const response = await fetch(url, {
        method: 'POST',
      });

      const data = await response.json();

      if (response.ok) {
        setResult({ type: 'success', message: 'Verification email sent successfully! Please check your inbox.' });
        setEmail('');
        onSuccess?.();
      } else {
        let errorMessage = 'Failed to send verification email';
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map(err => err.msg).join(', ');
          } else if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          }
        }
        setResult({ type: 'error', message: errorMessage });
      }
    } catch (error) {
      setResult({ type: 'error', message: 'Network error: ' + error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Resend Verification Email</h2>
      
      <p className="form-description">
        Enter your email address below and we'll send you a new verification link.
      </p>
      
      {result && (
        <div className={`result ${result.type}`}>
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>Email Address:</label>
          <input
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email address"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send Verification Email'}
        </button>
      </form>

      <div className="form-footer">
        <p>
          <a href="#" onClick={(e) => { e.preventDefault(); onSuccess?.(); }}>
            ← Back to Login
          </a>
        </p>
      </div>
    </div>
  );
};

export default ResendEmail;