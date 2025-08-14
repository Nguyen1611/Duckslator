// frontend/src/components/ResetPassword.jsx
import { useEffect, useMemo, useState } from 'react';


const RULES = [
  { key: 'len', label: 'At least 8 characters', test: (p) => p.length >= 8 },
  { key: 'upper', label: 'At least 1 uppercase letter (A-Z)', test: (p) => /[A-Z]/.test(p) },
  { key: 'lower', label: 'At least 1 lowercase letter (a-z)', test: (p) => /[a-z]/.test(p) },
  { key: 'num', label: 'At least 1 number (0-9)', test: (p) => /[0-9]/.test(p) },
  { key: 'special', label: 'At least 1 special character (!@#$%^&* etc.)', test: (p) => /[^A-Za-z0-9]/.test(p) },
];


const ResetPassword = () => {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [isSuccess, setIsSuccess] = useState(false);


  useEffect(() => {
    const t = new URLSearchParams(window.location.search).get('token');
    setToken(t || '');
  }, []);


  const ruleResults = useMemo(() => {
    const res = {};
    for (const r of RULES) res[r.key] = r.test(password);
    res.match = password.length > 0 && password === confirm;
    return res;
  }, [password, confirm]);


  const allValid = useMemo(
    () => RULES.every((r) => ruleResults[r.key]) && ruleResults.match,
    [ruleResults]
  );


  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return setResult({ type: 'error', message: 'Missing token' });
    if (!allValid) return setResult({ type: 'error', message: 'Please satisfy all password rules.' });


    setLoading(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('token', token);
      fd.append('new_password', password);


      const res = await fetch('http://127.0.0.1:8001/auth/reset-password', {
        method: 'POST',
        body: fd
      });
      const data = await res.json();


      if (res.ok) {
        setResult({ type: 'success', message: 'Password reset successfully' });
        setIsSuccess(true);
        setPassword(''); 
        setConfirm('');
      } else {
        const msg = data?.detail
          ? (Array.isArray(data.detail) ? data.detail.map(e => e.msg).join(', ') : data.detail)
          : 'Reset failed';
        setResult({ type: 'error', message: msg });
      }
    } catch (e) {
      setResult({ type: 'error', message: `Network error: ${e.message}` });
    } finally {
      setLoading(false);
    }
  };


  // If success, show only the success message
  if (isSuccess) {
    return (
      <div className="form-container">
        <div className={`result ${result.type}`}>
          Password reset successfully
        </div>
      </div>
    );
  }


  return (
    <div className="form-container">
      <h2>Reset Password</h2>


      {result && <div className={`result ${result.type}`}>{result.message}</div>}


      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>New Password</label>
          <input
            type="password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            placeholder="Enter new password"
            required
          />
        </div>


        <div className="form-group">
          <label>Confirm Password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e)=>setConfirm(e.target.value)}
            placeholder="Re-enter new password"
            required
          />
        </div>


        <div className="form-group" style={{marginTop: 4}}>
          <label style={{display:'block', marginBottom: 6}}>Password must include:</label>
          <ul style={{listStyle:'none', padding:0, margin:0}}>
            {RULES.map((r) => (
              <li key={r.key} style={{display:'flex', alignItems:'center', margin:'6px 0'}}>
                <span
                  style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: ruleResults[r.key] ? '#28a745' : '#dc3545',
                    display:'inline-block', marginRight: 8
                  }}
                />
                <span style={{color: ruleResults[r.key] ? '#28a745' : '#dc3545'}}>{r.label}</span>
              </li>
            ))}
            <li style={{display:'flex', alignItems:'center', margin:'6px 0'}}>
              <span
                style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: ruleResults.match ? '#28a745' : '#dc3545',
                  display:'inline-block', marginRight: 8
                }}
              />
              <span style={{color: ruleResults.match ? '#28a745' : '#dc3545'}}>Passwords match</span>
            </li>
          </ul>
        </div>


        <button className="btn btn-primary" disabled={loading || !allValid}>
          {loading ? 'Updating...' : 'Update Password'}
        </button>
      </form>
    </div>
  );
};


export default ResetPassword;  

