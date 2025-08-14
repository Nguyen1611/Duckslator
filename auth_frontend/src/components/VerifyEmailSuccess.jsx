import React from 'react';

const VerifyEmailSuccess = () => {
  return (
    <div className="form-container">
      <h2>Email Verification Complete</h2>
      
      <div className={`result success`} style={{ 
        textAlign: 'center', 
        padding: '20px',
        fontSize: '1.1rem',
        fontWeight: '500'
      }}>
        ✅ Email verified successfully. You can now log in.
      </div>
      
      <div style={{ textAlign: 'center', marginTop: '30px' }}>
        <p style={{ color: '#666', marginBottom: '20px', fontSize: '1rem' }}>
          Your email address has been successfully verified.
        </p>
        <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '25px' }}>
          You can now log in to your Duckslator account and start using our services.
        </p>
        
        <div style={{ 
          background: '#f8f9fa', 
          padding: '20px', 
          borderRadius: '8px',
          border: '1px solid #e9ecef',
          marginTop: '20px'
        }}>
          <p style={{ color: '#495057', margin: '0', fontSize: '0.9rem' }}>
            <strong>Next Steps:</strong>
          </p>
          <ul style={{ 
            textAlign: 'left', 
            color: '#495057', 
            fontSize: '0.9rem',
            margin: '10px 0 0 0',
            paddingLeft: '20px'
          }}>
            <li>Go back to the login page</li>
            <li>Enter your email and password</li>
            <li>Start using Duckslator!</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailSuccess;
