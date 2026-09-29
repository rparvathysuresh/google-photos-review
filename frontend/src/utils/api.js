/**
 * API utility for the Discovery Engine frontend.
 * 
 * Provides a configured fetch wrapper with base URL,
 * error handling, and typed methods for all API endpoints.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // Remove Content-Type for FormData (browser sets it with boundary)
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        errorData.detail || `API Error: ${response.status} ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(`Network error: ${error.message}`, 0, null);
  }
}

/**
 * Custom API error class.
 */
class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

// ── System ───────────────────────────────────────────────────

export async function healthCheck() {
  return request('/api/health');
}

// ── Ingestion ────────────────────────────────────────────────

export async function uploadFeedback(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/api/ingest/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function triggerScrape(source, query, options = {}) {
  return request('/api/ingest/scrape', {
    method: 'POST',
    body: JSON.stringify({ source, query, ...options }),
  });
}

export async function triggerExtraction() {
  return request('/api/ingest/extract', {
    method: 'POST',
  });
}

export async function getIngestionStatus() {
  return request('/api/ingest/status');
}

// ── Ask Engine ───────────────────────────────────────────────

export async function askQuestion(question, filters = {}) {
  return request('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question, filters }),
  });
}

export async function getAskHistory() {
  return request('/api/ask/history');
}

// ── Clusters ─────────────────────────────────────────────────

export async function getClusters() {
  return request('/api/clusters');
}

export async function getClusterDetail(clusterId) {
  return request(`/api/clusters/${clusterId}`);
}

export async function getClusterEpisodes(clusterId, page = 1) {
  return request(`/api/clusters/${clusterId}/episodes?page=${page}`);
}

// ── Analytics ────────────────────────────────────────────────

export async function getAnalyticsOverview() {
  return request('/api/analytics/overview');
}

export async function getSourceBreakdown() {
  return request('/api/analytics/sources');
}

export async function getDistributions() {
  return request('/api/analytics/distributions');
}

export async function getTrends() {
  return request('/api/analytics/trends');
}

export { APIError };
export default {
  healthCheck,
  uploadFeedback,
  triggerScrape,
  triggerExtraction,
  getIngestionStatus,
  askQuestion,
  getAskHistory,
  getClusters,
  getClusterDetail,
  getClusterEpisodes,
  getAnalyticsOverview,
  getSourceBreakdown,
  getDistributions,
  getTrends,
};
