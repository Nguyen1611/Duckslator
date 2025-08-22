import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import JobsApi from './JobsApi.js';

export default function JobUpload() {
  const [file, setFile] = useState(null);
  const [target, setTarget] = useState('en');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (!file) {
      setError('Please choose a file');
      return;
    }
    try {
      setSubmitting(true);
      const res = await JobsApi.create(file, target);
      navigate(`/jobs/${res.job_id}`);
    } catch (e) {
      setError(e.message || 'Upload failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Upload New Job</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <label>
          File
          <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} />
        </label>
        <label>
          Target language code
          <input type="text" value={target} onChange={e => setTarget(e.target.value)} placeholder="e.g., en, vi, fr" />
        </label>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="submit" disabled={submitting}>{submitting ? 'Uploading...' : 'Create Job'}</button>
          <button type="button" onClick={() => navigate('/jobs')}>Back to Jobs</button>
        </div>
      </form>
    </div>
  );
}


