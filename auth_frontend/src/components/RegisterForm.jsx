import { useState } from 'react';

const RegisterForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    age: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      setResult({ type: 'error', message: 'Passwords do not match' });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const userData = {
        firstName: formData.firstName,
        lastName: formData.lastName,
        age: parseInt(formData.age),
        email: formData.email,
        password: formData.password
      };

      const response = await fetch('http://127.0.0.1:8001/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      });

      const data = await response.json();

      if (response.ok) {
        setResult({ type: 'success', message: 'Registration successful! Please check your email to verify your account.' });
        setIsSuccess(true);
        setFormData({
          firstName: '', lastName: '', age: '', email: '', password: '', confirmPassword: ''
        });
        // Don't call onSuccess() - stay on register tab with success message
      } else {
        let errorMessage = 'Registration failed';
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

  // If success, show only success message
  if (isSuccess) {
    return (
      <div className="form-container">
        <h2>Registration Complete</h2>
        <div className={`result success`}>
          Registration successful! Please check your email to verify your account.
        </div>
        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <p style={{ color: '#666', marginBottom: '15px' }}>
            We've sent a verification link to your email address.
          </p>
          <p style={{ color: '#666', fontSize: '0.9rem' }}>
            Didn't receive the email? Check your spam folder or use the "Resend Email" tab.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="form-container">
      <h2>User Registration</h2>
      
      {result && (
        <div className={`result ${result.type}`}>
          {result.message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="form">
        <div className="form-row">
          <div className="form-group">
            <label>First Name:</label>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>Last Name:</label>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <div className="form-group">
          <label>Age:</label>
          <input
            type="number"
            name="age"
            min="13"
            max="120"
            value={formData.age}
            onChange={handleChange}
            required
          />
        </div>

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

        <div className="form-group">
          <label>Confirm Password:</label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;