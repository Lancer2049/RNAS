/**
 * E2E Test Authentication Helper
 *
 * Usage: import { setupAuth } from './auth-helper';
 *        test.beforeEach(async ({ page }) => { await setupAuth(page); });
 *
 * Password resolution order:
 *   1. RNAS_ADMIN_PASS env var (set in test harness)
 *   2. /etc/rnas/.admin_password file (persisted by the API on first boot)
 *   3. rnas-admin-2026 (legacy hardcoded fallback)
 */

import { readFileSync } from 'fs';

const API_BASE = 'http://127.0.0.1:8098';

function resolvePassword(): string {
  const env = process.env.RNAS_ADMIN_PASS;
  if (env) return env;
  try {
    const stored = readFileSync('/etc/rnas/.admin_password', 'utf-8').trim();
    if (stored) return stored;
  } catch {}
  return 'rnas-admin-2026';
}

let cachedToken: string | null = null;

export async function getAuthToken(): Promise<string> {
  if (cachedToken) {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/health`);
      if (resp.status === 200) return cachedToken;
    } catch {}
  }

  const resp = await fetch(`${API_BASE}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: resolvePassword() }),
  });

  if (!resp.ok) {
    throw new Error(`Auth failed: ${resp.status} ${await resp.text()}`);
  }

  const data = await resp.json();
  cachedToken = data.access_token;
  return cachedToken;
}

/**
 * Inject the auth token into the page so all fetch/XHR requests include
 * the Authorization header, and WebSocket URLs get ?token= (the frontend
 * reads localStorage 'rnas_token' to build WS URLs).
 */
export async function setupAuth(page: any): Promise<void> {
  const token = await getAuthToken();

  await page.addInitScript((t: string) => {
    localStorage.setItem('rnas_token', t);
    sessionStorage.setItem('rnas_token', t);
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
