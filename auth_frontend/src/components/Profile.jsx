import { useState } from 'react';

const Profile = ({ user, token }) => {
  const [loading, setLoading] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    window.location.reload();
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
        <button onClick={handleLogout} className="btn btn-secondary">
          Logout
        </button>
      </div>
    </div>
  );
};

export default Profile;