import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState('Processing authentication...');
  const { setAuthenticated } = useAuth();

  const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    const authStatus = searchParams.get('auth');
    const token = searchParams.get('token');
    
    if (authStatus === 'success' && token) {
      setMessage('Authentication successful! Setting up session...');
      
      // Set the cookie manually
      document.cookie = `access_token=${token}; path=/; max-age=3600; SameSite=Lax`;
      console.log('Set cookie manually:', document.cookie);
      
      // Store token in localStorage as backup
      localStorage.setItem('access_token', token);
      
      // Fetch user data using the token
      fetch(`${BASE_URL}/auth/me`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        },
      })
      .then(resp => {
        console.log('Auth me response status:', resp.status);
        if (resp.ok) {
          return resp.json();
        }
        throw new Error(`Failed to get user info: ${resp.status}`);
      })
      .then(userData => {
        console.log('User data received:', userData);
        setAuthenticated(userData);
        setMessage('Authentication successful! Redirecting...');
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 1000);
      })
      .catch(error => {
        console.error('Error fetching user data:', error);
        setMessage('Authentication successful but failed to get user info. Redirecting...');
        setAuthenticated(); // Still set as authenticated
        setTimeout(() => {
          navigate('/', { replace: true });
        }, 2000);
      });
    } else if (authStatus === 'error') {
      setMessage('Authentication failed. Please try again.');
      // Redirect back to main page after error
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 3000);
    } else {
      setMessage('Invalid authentication response. Redirecting...');
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 2000);
    }
  }, [searchParams, navigate, setAuthenticated, BASE_URL]);

  return (
    <div className="form-container">
      <h2>Authentication Status</h2>
      <div className={`result ${searchParams.get('auth') === 'success' ? 'success' : 'error'}`}>
        {message}
      </div>
    </div>
  );
};

export default OAuthCallback;
