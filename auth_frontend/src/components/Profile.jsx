import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';

const Profile = ({ user, token }) => {
  const [loading, setLoading] = useState(false);

  const { setLoggedOut } = useAuth();

  const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

  const handleLogout = async () => {
    setLoading(true);
    try {
      // Call backend logout endpoint to clear server-side session
      await fetch(`${BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear frontend storage and cookies
      localStorage.removeItem('access_token');
      
      // Clear the cookie manually
      document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      
      // Update auth context
      setLoggedOut();
      
      setLoading(false);
    }
  };

  return (
    <div className="profile-container">
      <h2>Welcome, {user?.email}!</h2>
      
      <div className="profile-info">
        <p><strong>Email:</strong> {user?.email}</p>
        <p><strong>Status:</strong> Logged In</p>
        <p><strong>Token:</strong> {token ? 'Present' : 'Missing'}</p>
      </div>

      <div className="profile-actions">
        <div style={{ marginBottom: 12 }}>
          <Link to="/jobs">Go to Jobs</Link>
        </div>
        <button 
          onClick={handleLogout} 
          className="btn btn-secondary"
          disabled={loading}
        >
          {loading ? 'Logging out...' : 'Logout'}
        </button>
      </div>
    </div>
  );
};

export default Profile;