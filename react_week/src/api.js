const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // Keep the HTTP status message if the server did not return JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

export async function fetchDashboardData() {
  const [summary, feedback, reports, alerts, predictions] = await Promise.all([
    apiRequest('/api/dashboard/summary/'),
    apiRequest('/api/feedback/?limit=100'),
    apiRequest('/api/reports/'),
    apiRequest('/api/alerts/'),
    apiRequest('/api/predictions/'),
  ]);
  return { summary, feedback, reports: reports.items, alerts: alerts.items, predictions: predictions.items };
}

export async function uploadFeedbackFile(file) {
  const form = new FormData();
  form.append('file', file);
  return apiRequest('/api/upload-and-analyze/', { method: 'POST', body: form });
}
