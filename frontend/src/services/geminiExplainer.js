/**
 * src/services/geminiExplainer.js
 *
 * Sends claim context to YOUR Django backend, which calls Gemini server-side.
 * The Gemini API key is NEVER shipped to the browser.
 *
 * All requests go through the same axios/fetch instance as the rest of your
 * api.js calls, so the user's auth token is included automatically.
 */

// ── Adjust this import to match wherever you export your base API client ──
import { api } from './api';

/**
 * generateFraudExplanation
 * ────────────────────────
 * @param {object} params
 * @param {object} params.claim          - Full claim object from api.getClaim()
 * @param {object} params.policyholder   - Full policyholder object
 * @param {object} params.vehicle        - Full vehicle object
 * @param {object} params.policy         - Full policy object
 * @param {object} params.fraudAnalysis  - Full response from api.detectFraud()
 * @param {string} params.currency       - 'USD' | 'ZWG'
 * @param {Function} params.fmtMoney     - Optional currency formatter (unused server-side, kept for parity)
 *
 * @returns {Promise<string>} Plain-English explanation paragraphs
 */
export async function generateFraudExplanation({
  claim,
  policyholder,
  vehicle,
  policy,
  fraudAnalysis,
  currency = 'USD',
}) {
  // Call the new method we just added to your ApiService
  const response = await api.explainClaim({
    claim,
    policyholder,
    vehicle,
    policy,
    fraud_analysis: fraudAnalysis,
    currency,
  });

  // Because api.request automatically parses JSON, the response is the data object
  return response?.explanation ?? '';
}


// ─────────────────────────────────────────────────────────────────────────────
// If your api.js does NOT expose a generic .post() method, use this
// raw-fetch fallback instead (uncomment and delete the import above):
//
// const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
//
// export async function generateFraudExplanation({ claim, policyholder, vehicle, policy, fraudAnalysis, currency = 'USD' }) {
//   const token = localStorage.getItem('authToken') ?? sessionStorage.getItem('authToken') ?? '';
//   const res = await fetch(`${BASE_URL}/api/ai/explain-claim/`, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       ...(token ? { Authorization: `Bearer ${token}` } : {}),
//     },
//     body: JSON.stringify({ claim, policyholder, vehicle, policy, fraud_analysis: fraudAnalysis, currency }),
//   });
//   if (!res.ok) throw new Error(`Explanation service returned ${res.status}`);
//   const data = await res.json();
//   return data.explanation ?? '';
// }
// ─────────────────────────────────────────────────────────────────────────────