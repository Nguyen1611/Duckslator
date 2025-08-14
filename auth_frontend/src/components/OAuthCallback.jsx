import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    const authStatus = searchParams.get('auth');
    
    if (authStatus === 'success') {
      setMessage('Authentication successful! Redirecting...');
      // Redirect to main page after successful auth
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 2000);
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
  }, [searchParams, navigate]);

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
