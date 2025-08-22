// Simple API helper for Jobs endpoints
const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

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
    
    console.log('Downloading result for job:', jobId);
    console.log('Using token:', token ? 'Present' : 'None');
    
    try {
      const resp = await fetch(`${BASE_URL}/jobs/${jobId}/download`, {
        credentials: 'include',
        headers,
      });
      
      console.log('Download response status:', resp.status);
      console.log('Download response headers:', resp.headers);
      
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `Download failed (${resp.status})`);
      }
      
      const blob = await resp.blob();
      console.log('Downloaded blob size:', blob.size);
      console.log('Downloaded blob type:', blob.type);
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      
      // Try to read filename from Content-Disposition
      const cd = resp.headers.get('content-disposition') || '';
      console.log('Content-Disposition header:', cd);
      
      const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
      const filename = decodeURIComponent(match?.[1] || match?.[2] || suggestedName || `job_${jobId}`);
      console.log('Using filename:', filename);
      
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      
      console.log('Download completed successfully');
    } catch (error) {
      console.error('Fetch download failed, trying direct link:', error);
      
      // Fallback: try direct download link
      try {
        const downloadUrl = `${BASE_URL}/jobs/${jobId}/download`;
        console.log('Trying direct download URL:', downloadUrl);
        
        // Create a temporary link and click it
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = suggestedName || `job_${jobId}`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('Direct download link clicked');
      } catch (directError) {
        console.error('Direct download also failed:', directError);
        throw new Error('All download methods failed');
      }
    }
  },
  downloadInput: async (jobId, suggestedName) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const headers = new Headers();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    
    console.log('Downloading input for job:', jobId);
    console.log('Using token:', token ? 'Present' : 'None');
    
    try {
      const resp = await fetch(`${BASE_URL}/jobs/${jobId}/download/input`, {
        credentials: 'include',
        headers,
      });
      
      console.log('Download input response status:', resp.status);
      console.log('Download input response headers:', resp.headers);
      
      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error(msg || `Download failed (${resp.status})`);
      }
      
      const blob = await resp.blob();
      console.log('Downloaded input blob size:', blob.size);
      console.log('Downloaded input blob type:', blob.type);
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      
      const cd = resp.headers.get('content-disposition') || '';
      console.log('Input Content-Disposition header:', cd);
      
      const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
      const filename = decodeURIComponent(match?.[1] || match?.[2] || suggestedName || `job_${jobId}_input`);
      console.log('Using input filename:', filename);
      
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      
      console.log('Input download completed successfully');
    } catch (error) {
      console.error('Fetch input download failed, trying direct link:', error);
      
      // Fallback: try direct download link
      try {
        const downloadUrl = `${BASE_URL}/jobs/${jobId}/download/input`;
        console.log('Trying direct input download URL:', downloadUrl);
        
        // Create a temporary link and click it
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = suggestedName || `job_${jobId}_input`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('Direct input download link clicked');
      } catch (directError) {
        console.error('Direct input download also failed:', directError);
        throw new Error('All input download methods failed');
      }
    }
  },
};

export default JobsApi;


