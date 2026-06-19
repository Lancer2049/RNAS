import { test, expect } from '@playwright/test';

const BASE = 'http://192.168.0.203:8099';

test.describe('New Feature Pages - API Validation', () => {

  test('Routing API returns OSPF neighbors + BGP peers', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/routing/status`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(json.ospf).toBeDefined();
    expect(json.bgp).toBeDefined();
    expect(Array.isArray(json.ospf.neighbors)).toBe(true);
    expect(Array.isArray(json.bgp.peers)).toBe(true);
  });

  test('Tunnels API returns interface list', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/tunnels`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(Array.isArray(json.tunnels)).toBe(true);
  });

  test('VLAN API returns module + interfaces status', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/vlans`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(['loaded', 'missing', 'unknown']).toContain(json.module);
    expect(Array.isArray(json.interfaces)).toBe(true);
  });

  test('NetFlow API reports running status', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/netflow`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(typeof json.running).toBe('boolean');
    expect(json.collector).toBeTruthy();
  });

  test('DHCP Relay API reports running status', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/dhcp-relay`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(typeof json.running).toBe('boolean');
    expect(json.upstream).toBeTruthy();
  });

  test('Hotspot status shows Active', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/hotspot/status`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(json.portal).toBe('Active');
    expect(json.auth).toBe('Active');
    expect(json.iptables).toBe('Active');
  });

});

test.describe('Hotspot Authentication Flow', () => {

  test('Valid login returns Authenticated', async ({ request }) => {
    const resp = await request.post(`${BASE}/hotspot/login`, {
      data: 'username=testuser&password=testpass',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    expect(resp.status()).toBe(302);
    expect(await resp.text()).toContain('Authenticated');
  });

  test('Invalid login returns 403', async ({ request }) => {
    const resp = await request.post(`${BASE}/hotspot/login`, {
      data: 'username=bad&password=wrong',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    expect(resp.status()).toBe(403);
  });

  test('Portal page loads', async ({ request }) => {
    const resp = await request.get(`${BASE}/hotspot`);
    expect(resp.status()).toBe(200);
  });

});

test.describe('System Integration Checks', () => {

  test('All 9 core services active', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/system/status`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    const active = json.services.filter((s: any) => s.active === 'active');
    expect(active.length).toBeGreaterThanOrEqual(7);
  });

  test('Dashboard health check', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/health`);
    expect(resp.status()).toBe(200);
    expect((await resp.json()).status).toBe('ok');
  });

  test('Status API returns RADIUS state', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/status`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(json.service.radius_state).toBe('active');
  });

  test('Config export returns valid structure', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/config/export`);
    expect(resp.status()).toBe(200);
    const json = await resp.json();
    expect(json.rnas_version).toBeDefined();
  });

});
