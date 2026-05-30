/**
 * api.js — Reusable fetch wrapper module.
 *
 * Features:
 *  - CSRF token injection on state-changing requests (POST/PUT/DELETE/PATCH)
 *  - 401 → redirect to /login?return_to=<current_path>
 *  - 403 CSRF_INVALID → refresh token from /api/v1/csrf-token and retry once
 *  - Network errors → toast notification with retry option
 *  - Returns parsed JSON on success, throws ApiError on failure
 *
 * Requirements: 9.1, 11.3, 11.5
 */

export class ApiError extends Error {
  constructor(status, code, message, details = [], traceId = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.traceId = traceId;
  }
}

const STATE_CHANGING_METHODS = new Set(['POST', 'PUT', 'DELETE', 'PATCH']);

/**
 * Read the CSRF token from the <meta name="csrf-token"> tag.
 * @returns {string} The current CSRF token, or empty string if not found.
 */
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

/**
 * Update the CSRF token stored in the <meta name="csrf-token"> tag.
 * @param {string} token - The new CSRF token value.
 */
function setCsrfToken(token) {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) meta.content = token;
}

/**
 * Fetch a fresh CSRF token from the server and update the meta tag.
 * @returns {Promise<string|null>} The new token, or null on failure.
 */
async function refreshCsrfToken() {
  try {
    const res = await fetch('/api/v1/csrf-token');
    if (res.ok) {
      const data = await res.json();
      setCsrfToken(data.csrf_token);
      return data.csrf_token;
    }
  } catch {
    // Silently fail — the retry will surface the error naturally.
  }
  return null;
}

/**
 * Display a toast notification for network errors with an optional retry button.
 * Appends to #notification-area if present in the DOM.
 *
 * @param {string} url - The URL that failed.
 * @param {object} options - The original fetch options.
 * @param {boolean} isRetry - Whether this is already a retry (omit retry button).
 */
function showNetworkError(url, options, isRetry) {
  const area = document.getElementById('notification-area');
  if (!area) return;

  const toast = document.createElement('div');
  toast.style.cssText = [
    'background:rgba(15,22,41,0.95)',
    'border:1px solid rgba(248,113,113,0.4)',
    'color:#fca5a5',
    'padding:12px 16px',
    'border-radius:8px',
    'font-size:0.875rem',
    'box-shadow:0 8px 24px rgba(0,0,0,0.4)',
    'display:flex',
    'align-items:center',
    'gap:8px',
  ].join(';');
  toast.setAttribute('role', 'alert');

  const msg = document.createElement('span');
  msg.textContent = 'Network error. Please check your connection.';
  toast.appendChild(msg);

  if (!isRetry) {
    const retryBtn = document.createElement('button');
    retryBtn.textContent = 'Retry';
    retryBtn.style.cssText = [
      'margin-left:8px',
      'color:#D4AF37',
      'font-weight:600',
      'background:none',
      'border:none',
      'cursor:pointer',
      'text-decoration:underline',
    ].join(';');
    retryBtn.addEventListener('click', () => {
      toast.remove();
      request(url, options);
    });
    toast.appendChild(retryBtn);
  }

  area.appendChild(toast);

  // Auto-dismiss after 5 seconds with a fade-out.
  setTimeout(() => {
    toast.style.transition = 'opacity 0.5s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 500);
  }, 5000);
}

/**
 * Core fetch wrapper.
 *
 * @param {string} url - The request URL.
 * @param {RequestInit} [options={}] - Standard fetch options.
 * @param {boolean} [_isRetry=false] - Internal flag to prevent infinite CSRF retry loops.
 * @returns {Promise<any>} Parsed JSON response body.
 * @throws {ApiError} On HTTP errors or network failures.
 */
export async function request(url, options = {}, _isRetry = false) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  if (STATE_CHANGING_METHODS.has(method)) {
    headers['X-CSRF-Token'] = getCsrfToken();
  }

  let response;
  try {
    response = await fetch(url, { ...options, method, headers });
  } catch (networkError) {
    showNetworkError(url, options, _isRetry);
    throw new ApiError(0, 'NETWORK_ERROR', 'Network error. Please check your connection.');
  }

  // 401 — redirect to login, preserving the current path for post-login redirect.
  if (response.status === 401) {
    const returnTo = encodeURIComponent(
      window.location.pathname + window.location.search
    );
    window.location.href = `/login?return_to=${returnTo}`;
    throw new ApiError(401, 'UNAUTHORIZED', 'Authentication required.');
  }

  // 403 with CSRF_INVALID — refresh token and retry once.
  if (response.status === 403 && !_isRetry) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = {};
    }
    if (data?.error?.code === 'CSRF_INVALID') {
      await refreshCsrfToken();
      return request(url, options, true);
    }
  }

  // Parse JSON body when the content-type indicates it.
  let body;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      body = await response.json();
    } catch {
      body = {};
    }
  } else {
    body = {};
  }

  if (!response.ok) {
    const err = body?.error || {};
    throw new ApiError(
      response.status,
      err.code || 'ERROR',
      err.message || 'An error occurred.',
      err.details || [],
      err.trace_id || null
    );
  }

  return body;
}

/**
 * Convenience API object with typed HTTP method helpers.
 *
 * @example
 * import api from './api.js';
 * const products = await api.get('/api/v1/products');
 * await api.post('/api/v1/cart/items', { product_id: id, quantity: 1 });
 */
export const api = {
  /**
   * Perform a GET request.
   * @param {string} url
   * @param {RequestInit} [options={}]
   */
  get: (url, options = {}) =>
    request(url, { ...options, method: 'GET' }),

  /**
   * Perform a POST request with a JSON body.
   * @param {string} url
   * @param {any} data - Will be JSON-serialised.
   * @param {RequestInit} [options={}]
   */
  post: (url, data, options = {}) =>
    request(url, { ...options, method: 'POST', body: JSON.stringify(data) }),

  /**
   * Perform a PUT request with a JSON body.
   * @param {string} url
   * @param {any} data - Will be JSON-serialised.
   * @param {RequestInit} [options={}]
   */
  put: (url, data, options = {}) =>
    request(url, { ...options, method: 'PUT', body: JSON.stringify(data) }),

  /**
   * Perform a DELETE request.
   * @param {string} url
   * @param {RequestInit} [options={}]
   */
  delete: (url, options = {}) =>
    request(url, { ...options, method: 'DELETE' }),
};

export default api;
