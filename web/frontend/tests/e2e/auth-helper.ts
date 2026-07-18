/**
 * E2E Test Authentication Helper
 *
 * Usage: import { setupAuth } from './auth-helper';
 *        test.beforeEach(async ({ page }) => { await setupAuth(page); });
 */

const API_BASE = 'http://127.0.0.1:8098';
const CREDENTIALS = { username: 'admin', password: 'rnas-admin-2026' };

let cachedToken: string | null = null;

export async function getAuthToken(): Promise<string> {
  if (cachedToken) {
    // Verify token is still valid
    try {
      const resp = await fetch(`${API_BASE}/api/v1/health`);
      if (resp.status === 200) return cachedToken;
    } catch {}
  }

  const resp = await fetch(`${API_BASE}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(CREDENTIALS),
  });

  if (!resp.ok) {
    throw new Error(`Auth failed: ${resp.status} ${await resp.text()}`);
  }

  const data = await resp.json();
  cachedToken = data.access_token;
  return cachedToken;
}

/**
 * Inject the auth token into the page so all fetch/XHR requests
 * include the Authorization header automatically.
 */
export async function setupAuth(page: any): Promise<void> {
  const token = await getAuthToken();

  await page.addInitScript((t: string) => {
    const _origFetch = window.fetch;
    window.fetch = function (input: RequestInfo | URL, init?: RequestInit) {
      const headers = new Headers(init?.headers || {});
      if (!headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${t}`);
      }
      return _origFetch(input, { ...init, headers });
    };
  }, token);
}
