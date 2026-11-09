const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

export function apiBaseUrl() {
  return API_BASE_URL;
}

export async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    Accept: 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: options.method || 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 204) {
    return null;
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    let message = 'Something went wrong';
    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map((row) => row.msg || JSON.stringify(row)).join(' ');
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return payload;
}
