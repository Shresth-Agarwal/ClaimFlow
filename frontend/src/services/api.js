/**
 * ClaimFlow API Service Layer
 * All backend communication is centralized here.
 * No fetch calls should exist directly in components.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Core request helper — attaches auth header when a token is available.
 */
async function request(method, path, body = null, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);

  const url = `${BASE_URL}${path}`;

  console.group(`[API] ${method} ${path}`);
  console.log('URL:', url);
  console.log('Headers:', headers);
  if (body) console.log('Body:', body);

  try {
    const res = await fetch(url, options);
    console.log('Status:', res.status, res.statusText);
    console.log('Response headers:', Object.fromEntries(res.headers.entries()));

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      console.error('Error response:', error);
      console.groupEnd();
      throw new Error(error.detail || `Request failed: ${res.status}`);
    }

    const data = await res.json();
    console.log('Response data:', data);
    console.groupEnd();
    return data;
  } catch (err) {
    console.error('Fetch error:', err.message);
    console.groupEnd();
    throw err;
  }
}

/**
 * Multipart form request helper — used for file uploads.
 */
async function requestForm(method, path, formData, token = null) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ─── Auth Endpoints ────────────────────────────────────────────────────────────

/**
 * POST /auth/register
 * @param {{ username: string, email: string, password: string, role: 'user'|'agent' }} data
 */
export async function registerUser(data) {
  return request('POST', '/auth/register', {
    username: data.username,
    email: data.email,
    password: data.password,
    role: data.role,
  });
}

/**
 * POST /auth/login
 * @param {{ email: string, password: string }} data
 * @returns {{ token: string, ... }}
 */
export async function loginUser(data) {
  return request('POST', '/auth/login', {
    email: data.email,
    password: data.password,
  });
}

// ─── User Endpoints ────────────────────────────────────────────────────────────

/**
 * GET /users/profile
 * Requires "user" role.
 */
export async function getUserProfile(token) {
  return request('GET', '/users/profile', null, token);
}

/**
 * GET /users/orders
 * Requires "user" role.
 */
export async function getUserOrders(token) {
  return request('GET', '/users/orders', null, token);
}

// ─── Agent Endpoints ───────────────────────────────────────────────────────────

/**
 * POST /agents/verify
 * Requires "agent" role.
 * @param {string} token
 */
export async function verifyAgent(token) {
  return request('POST', '/agents/verify', { is_valid: true }, token);
}

/**
 * POST /agents/verify-id-proof
 * Requires "agent" role.
 * Backend expects: proof (file), id_type (form), id_number (form)
 * @param {{ file: File, id_type: string, id_number: string }} data
 * @param {string} token
 */
export async function verifyAgentIdProof(data, token) {
  const formData = new FormData();
  formData.append('proof', data.file);        // backend field name is 'proof'
  formData.append('id_type', data.id_type);
  formData.append('id_number', data.id_number);
  return requestForm('POST', '/agents/verify-id-proof', formData, token);
}

/**
 * GET /agents/sensitive-data
 * Requires "agent" role and verified=true.
 */
export async function getAgentSensitiveData(token) {
  return request('GET', '/agents/sensitive-data', null, token);
}

/**
 * GET /agents/profile
 * Requires "agent" role.
 */
export async function getAgentProfile(token) {
  return request('GET', '/agents/profile', null, token);
}

// ─── Products Endpoints ────────────────────────────────────────────────────────

/**
 * GET /products
 * Returns the full list of available insurance products / domains.
 * Public endpoint — no auth required.
 * @returns {{ products: Array<{ id: string, name: string, category: string, description: string }> }}
 */
export async function getInsuranceProducts() {
  return request('GET', '/products');
}

/**
 * POST /products/recommend
 * AI-driven plan recommendation based on the user's claim context.
 * Requires authenticated user.
 *
 * @param {{
 *   policy_type: string,
 *   policy_number: string,
 *   insured_amount: number,
 *   message_count: number
 * }} payload
 * @param {string} token
 * @returns {{ recommended_plan: string, premium_estimate: string, reasoning: string }}
 */
export async function getProductRecommendation(payload, token) {
  return request('POST', '/products/recommend', payload, token);
}

// ─── Advisors Endpoints ────────────────────────────────────────────────────────

/**
 * GET /advisors
 * Returns the list of available expert advisors.
 * Requires authenticated user.
 * @param {string} token
 * @returns {{ advisors: Array<{ id, name, specialty, badge, badgeIcon, photo }> }}
 */
export async function getAdvisors(token) {
  return request('GET', '/advisors', null, token);
}

/**
 * POST /advisors/book
 * Book a consultation with a specific advisor.
 * Requires authenticated user.
 *
 * @param {{
 *   advisor_id: number,
 *   advisor_name: string,
 *   specialty: string,
 *   policy_type: string | null,
 *   policy_number: string | null,
 *   recommended_plan: string | null
 * }} payload
 * @param {string} token
 * @returns {{ booking_id: string, status: string, message: string }}
 */
export async function bookAdvisorConsultation(payload, token) {
  return request('POST', '/advisors/book', payload, token);
}
