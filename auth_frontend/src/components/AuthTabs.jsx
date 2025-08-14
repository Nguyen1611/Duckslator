// frontend/src/components/AuthTabs.jsx
import { useState } from 'react';
import LoginForm from './LoginForm.jsx';
import RegisterForm from './RegisterForm.jsx';
import GoogleAuth from './GoogleAuth.jsx';
import ForgotPassword from './ForgotPassword.jsx';
import ResendEmail from './ResendEmail.jsx';
import Profile from './Profile.jsx';

const AuthTabs = () => {
  const [activeTab, setActiveTab] = useState('login');
  const [authStatus, setAuthStatus] = useState({
    isLoggedIn: false,
    user: null,
    token: null,
  });

  const updateAuthStatus = (status) => {
    setAuthStatus(status);
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  if (authStatus.isLoggedIn) {
    return <Profile user={authStatus.user} token={authStatus.token} />;
  }

  return (
    <div className="auth-container">
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'login' ? 'active' : ''}`}
          onClick={() => handleTabChange('login')}
        >
          Login
        </button>
        <button
          className={`tab ${activeTab === 'register' ? 'active' : ''}`}
          onClick={() => handleTabChange('register')}
        >
          Register
        </button>
        <button
          className={`tab ${activeTab === 'google' ? 'active' : ''}`}
          onClick={() => handleTabChange('google')}
        >
          Google Auth
        </button>
        <button
          className={`tab ${activeTab === 'forgot-password' ? 'active' : ''}`}
          onClick={() => handleTabChange('forgot-password')}
        >
          Forgot Password
        </button>
        <button
          className={`tab ${activeTab === 'resend-email' ? 'active' : ''}`}
          onClick={() => handleTabChange('resend-email')}
        >
          Resend Email
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'login' && (
          <LoginForm
            updateAuthStatus={updateAuthStatus}
            // no onSuccess navigation here; stay or navigate as you prefer
          />
        )}

        {activeTab === 'register' && (
          <RegisterForm
            // After successful registration, switch to Login so user can sign in
            onSuccess={() => handleTabChange('login')}
          />
        )}

        {activeTab === 'google' && (
          <GoogleAuth
            updateAuthStatus={updateAuthStatus}
            // After successful Google auth, switch to Login (or keep as-is)
            onSuccess={() => handleTabChange('login')}
          />
        )}

        {activeTab === 'forgot-password' && (
          // IMPORTANT: no onSuccess passed, so we stay on this tab and show the success message
          <ForgotPassword />
        )}

        {activeTab === 'resend-email' && (
          // IMPORTANT: no onSuccess passed, so we stay on this tab and show the success message
          <ResendEmail />
        )}
      </div>
    </div>
  );
};

export default AuthTabs;