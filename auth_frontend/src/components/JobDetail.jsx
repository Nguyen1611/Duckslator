import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import JobsApi from './JobsApi.js';

export default function JobDetail() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [working, setWorking] = useState(false);

  async function load() {
    try {
      setLoading(true);
      const data = await JobsApi.get(jobId);
      setJob(data);
    } catch (e) {
      setError(e.message || 'Failed to load job');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [jobId]);

  async function handleProcess() {
    try {
      setWorking(true);
      await JobsApi.process(jobId);
      await load();
    } catch (e) {
      alert(e.message);
    } finally {
      setWorking(false);
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this job and its files?')) return;
    try {
      setWorking(true);
      await JobsApi.remove(jobId);
      navigate('/jobs');
    } catch (e) {
      alert(e.message);
    } finally {
      setWorking(false);
    }
  }

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!job) return <div>Not found</div>;

  const canDownload = job.status === 'completed' && job.files_available;

  return (
    <div>
      <h2>Job Detail</h2>
      <p><strong>Original file:</strong> {job.original_filename}</p>
      <p><strong>Target language:</strong> {job.target_lang}</p>
      <p><strong>Status:</strong> {job.status}</p>
      <p><strong>Progress:</strong> {job.progress ?? 0}%</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {job.status === 'queued' && (
          <button onClick={handleProcess} disabled={working}>Process</button>
        )}
        {canDownload && (
          <>
            <button onClick={() => JobsApi.downloadResult(job.job_id, `${job.original_filename || 'result'}`)}>Download result</button>
            <button onClick={() => JobsApi.downloadInput(job.job_id, `${job.original_filename || 'input'}`)}>Download input</button>
          </>
        )}
        <button onClick={handleDelete} disabled={working}>Delete</button>
        <button onClick={() => navigate('/jobs')}>Back to Jobs</button>
      </div>
    </div>
  );
}


