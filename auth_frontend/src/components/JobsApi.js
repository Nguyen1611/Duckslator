// Simple API helper for Jobs endpoints
const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8001';

async function apiRequest(path, options = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers = new Headers(options.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const resp = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
    headers,
  });
  const contentType = resp.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  if (!resp.ok) {
    const errorPayload = isJson ? await resp.json().catch(() => ({})) : { detail: await resp.text() };
    const message = errorPayload?.detail || errorPayload?.message || `Request failed with ${resp.status}`;
    throw new Error(message);
  }
  return isJson ? resp.json() : resp;
}

export const JobsApi = {
  list: () => apiRequest('/jobs/'),
  create: (file, targetLang) => {
    const form = new FormData();
    form.append('file', file);
    form.append('target_lang', targetLang);
    return apiRequest('/jobs/', { method: 'POST', body: form });
  },
  get: (jobId) => apiRequest(`/jobs/${jobId}`),
  process: (jobId) => apiRequest(`/jobs/${jobId}/process`, { method: 'POST' }),
  remove: (jobId) => apiRequest(`/jobs/${jobId}`, { method: 'DELETE' }),
  downloadResult: async (jobId, suggestedName) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers = new Headers();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const resp = await fetch(`${BASE_URL}/jobs/${jobId}/download`, {
      credentials: 'include',
      headers,
    });
    if (!resp.ok) {
      const msg = await resp.text();
      throw new Error(msg || `Download failed (${resp.status})`);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    // Try to read filename from Content-Disposition
    const cd = resp.headers.get('content-disposition') || '';
    const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
    const filename = decodeURIComponent(match?.[1] || match?.[2] || suggestedName || `job_${jobId}`);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
  downloadInput: async (jobId, suggestedName) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers = new Headers();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const resp = await fetch(`${BASE_URL}/jobs/${jobId}/download/input`, {
      credentials: 'include',
      headers,
    });
    if (!resp.ok) {
      const msg = await resp.text();
      throw new Error(msg || `Download failed (${resp.status})`);
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const cd = resp.headers.get('content-disposition') || '';
    const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
    const filename = decodeURIComponent(match?.[1] || match?.[2] || suggestedName || `job_${jobId}_input`);
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};

export default JobsApi;


