// frontend/src/components/ForgotPassword.jsx
import { useState } from 'react';

const ForgotPassword = ({ onSuccess }) => {
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
      const url = `http://127.0.0.1:8001/auth/forgot-password?email=${encodeURIComponent(email.trim())}`;

      const response = await fetch(url, { method: 'POST' });
      const data = await response.json();

      if (response.ok) {
        setResult({ type: 'success', message: data.message || 'Password reset email sent. Check your inbox.' });
        setEmail('');
        onSuccess?.();
      } else {
        let errorMessage = 'Request failed';
        if (data?.detail) {
          if (Array.isArray(data.detail)) errorMessage = data.detail.map(e => e.msg).join(', ');
          else if (typeof data.detail === 'string') errorMessage = data.detail;
        }
        setResult({ type: 'error', message: errorMessage });
      }
    } catch (err) {
      setResult({ type: 'error', message: `Network error: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h2>Forgot Password</h2>
      <p className="form-description">Enter your email to receive a reset link.</p>

      {result && <div className={`result ${result.type}`}>{result.message}</div>}

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>Email Address:</label>
          <input
            type="email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>
      </form>
    </div>
  );
};

export default ForgotPassword;