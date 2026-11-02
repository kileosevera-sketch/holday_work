const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const AUTH_TOKEN_KEY = 'customer-intelligence-token';

export function getAccessToken() {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAccessToken(token) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAccessToken() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
}

export async function apiFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  let response;
  try {
    const headers = new Headers(options.headers || {});
    const token = getAccessToken();
    if (token) headers.set('Authorization', `Bearer ${token}`);
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    throw new Error(
      `Cannot connect to backend server at ${API_BASE_URL}. Ensure 'python -m uvicorn main:app --port 8000' is running.`,
      { cause: err }
    );
  }

  if (!response.ok) {
    if (response.status === 401 && path !== '/api/auth/login') {
      clearAccessToken();
      window.dispatchEvent(new Event('auth:expired'));
    }
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // Keep the HTTP status message if the server did not return JSON.
    }
    throw new Error(message);
  }
  return response;
}

export async function apiRequest(path, options = {}) {
  const response = await apiFetch(path, options);
  return response.json();
}

export async function fetchDashboardData() {
  const [summary, feedback, batches, dailyTrends] = await Promise.all([
    apiRequest('/api/dashboard/summary'),
    apiRequest('/api/feedback?limit=100'),
    apiRequest('/api/batches'),
    apiRequest('/api/dashboard/daily-trends'),
  ]);
  return {
    summary,
    feedback: { items: feedback.items || [], total: feedback.total || 0 },
    reports: (batches.batches || []).map(batch => ({
      id: batch.id,
      filename: batch.filename,
      feedback_count: batch.feedback_count,
      created_at: batch.uploaded_at,
      critical: batch.critical_count,
      duplicate_records_skipped: batch.duplicate_records_skipped,
    })),
    dailyTrends: dailyTrends.items || [],
    alerts: summary.alerts || [],
    predictions: summary.causes || [],
  };
}

export async function analyzePendingFeedback() {
  return apiRequest('/api/analysis/pending', { method: 'POST' });
}

export async function uploadFeedbackFile(file, idempotencyKey) {
  const form = new FormData();
  form.append('file', file);
  if (idempotencyKey) form.append('idempotency_key', idempotencyKey);
  // Post to the production upload endpoint
  return apiRequest('/api/upload', { method: 'POST', body: form });
}
