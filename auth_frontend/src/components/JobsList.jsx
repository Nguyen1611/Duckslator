import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import JobsApi from './JobsApi.js';

export default function JobsList() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    try {
      setLoading(true);
      const data = await JobsApi.list();
      setJobs(data.jobs || []);
    } catch (e) {
      setError(e.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleProcess(jobId) {
    try {
      await JobsApi.process(jobId);
      await load();
    } catch (e) {
      alert(e.message);
    }
  }

  async function handleDelete(jobId) {
    if (!confirm('Delete this job and its files?')) return;
    try {
      await JobsApi.remove(jobId);
      await load();
    } catch (e) {
      alert(e.message);
    }
  }

  if (loading) return <div>Loading jobs...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Your Jobs</h2>
        <Link to="/jobs/upload" className="btn">Upload new job</Link>
      </div>
      {jobs.length === 0 ? (
        <p>No jobs yet. <Link to="/jobs/upload">Create one</Link>.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>File</th>
              <th>Target</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map(j => (
              <tr key={j.job_id}>
                <td><Link to={`/jobs/${j.job_id}`}>{j.original_filename}</Link></td>
                <td>{j.target_lang}</td>
                <td>{j.status}</td>
                <td>{j.progress ?? 0}%</td>
                <td style={{ display: 'flex', gap: 8 }}>
                  {j.status === 'queued' && (
                    <button onClick={() => handleProcess(j.job_id)}>Process</button>
                  )}
                  {j.status === 'completed' && j.files_available && (
                    <button onClick={() => JobsApi.downloadResult(j.job_id, `${j.original_filename || 'result'}`)}>Download</button>
                  )}
                  <button onClick={() => handleDelete(j.job_id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


