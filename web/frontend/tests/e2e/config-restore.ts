/**
 * Test config capture/restore — isolates scenario tests from each other.
 *
 * Scenario tests modify the live /etc/rnas config tree on VM3. Without
 * isolation, test files run later see polluted state (services disabled,
 * config sections overwritten) and fail non-deterministically.
 *
 * Usage in a scenario-heavy spec file:
 *   import { captureBaseline, restoreBaseline } from './config-restore';
 *   test.beforeAll(async ({ request }) => { await captureBaseline(request, 'scen'); });
 *   test.afterAll(async ({ request }) => { await restoreBaseline(request, 'scen'); });
 */

const API_BASE = 'http://127.0.0.1:8098';
const CREDS = { username: 'admin', password: 'rnas-admin-2026' };

async function authToken(request: any): Promise<string | null> {
  try {
    const login = await request.post(`${API_BASE}/api/auth/token`, { data: CREDS });
    if (!login.ok()) return null;
    const { access_token } = await login.json();
    return access_token;
  } catch { return null; }
}

export async function captureBaseline(request: any, tag: string): Promise<void> {
  const token = await authToken(request);
  if (!token) return;
  const name = `e2e-base-${tag}-${Date.now()}`;
  try {
    const res = await request.post(`${API_BASE}/api/v1/config/snapshot`, {
      headers: { Authorization: `Bearer ${token}` },
      data: { name },
    });
    console.log(`[capture] baseline "${name}" -> ${res.status()}`);
  } catch (e) {
    console.log(`[capture] failed: ${e}`);
  }
}

export async function restoreBaseline(request: any, tag: string): Promise<void> {
  const token = await authToken(request);
  if (!token) return;
  try {
    const list = await request.get(`${API_BASE}/api/v1/config/snapshots`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const { snapshots } = await list.json();
    const match = (snapshots || []).filter((s: any) => s.name.includes(`e2e-base-${tag}-`));
    if (match.length === 0) { console.log('[restore] no baseline found'); return; }
    const target = match[match.length - 1];
    const res = await request.post(`${API_BASE}/api/v1/config/snapshot/${target.name}/restore`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log(`[restore] → "${target.name}" -> ${res.status()}`);
  } catch (e) {
    console.log(`[restore] failed: ${e}`);
  }
}
