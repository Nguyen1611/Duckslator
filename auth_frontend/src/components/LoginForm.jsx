// frontend/src/components/LoginForm.jsx
import { useState } from 'react';

const LoginForm = ({ updateAuthStatus, onSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      // Send FormData instead of JSON
      const fd = new FormData();
      fd.append('email', formData.email);
      fd.append('password', formData.password);

      const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8001';
      const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        body: fd,
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        setResult({ type: 'success', message: 'Login successful!' });
        
        updateAuthStatus({
          isLoggedIn: true,
          user: { email: formData.email },
          token: data.access_token
        });
        
        localStorage.setItem('access_token', data.access_token);
        onSuccess?.();
      } else {
        // Handle different types of error responses properly
        let errorMessage = 'Login failed';
        if (data.detail) {
          if (Array.isArray(data.detail)) {
            // Handle validation error array
            errorMessage = data.detail.map(err => err.msg).join(', ');
          } else if (typeof data.detail === 'string') {
            // Handle simple string error
            errorMessage = data.detail;
          } else {
            // Handle object error
            errorMessage = 'Validation error occurred';
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
      <h2>User Login</h2>
      
      {result && (
        <div className={`result ${result.type}`}>
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Signing In...' : 'Sign In'}
        </button>
      </form>
    </div>
  );
};

export default LoginForm;