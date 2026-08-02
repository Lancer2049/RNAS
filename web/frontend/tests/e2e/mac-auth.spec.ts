import { setupAuth, getAuthToken } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('MAC Auth Bypass (P2-03)', () => {

  test('M1: MAC Auth tab loads in Protocol Configuration with fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'MAC Auth' });
    await expect(tab).toBeVisible({ timeout: 10000 });
    await tab.click();

    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });
    // Username/NAS fields live under the collapsed Advanced Settings group
    await page.getByText('Advanced Settings').click();
    const labels = await page.locator('.field-row label').allTextContents();
    const expected = ['Username Format', 'NAS Identifier', 'VLAN'];
    for (const l of expected) {
      expect(labels.some(t => t.includes(l))).toBeTruthy();
    }
  });

  test('M2: Save MAC Auth config via UI shows "Saved" feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'MAC Auth' });
    await expect(tab).toBeVisible({ timeout: 10000 });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    // Enable MAC Auth via the toggle
    const toggle = page.locator('.toggle input');
    await toggle.check({ force: true });

    // NAS Identifier lives under Advanced Settings (collapsed by default)
    await page.getByText('Advanced Settings').click();
    const nasRow = page.locator('.field-row').filter({ has: page.locator('label', { hasText: 'NAS Identifier' }) });
    await nasRow.locator('input').fill('rnas-mac-auth-e2e');

    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.msg.ok')).toContainText('Saved');
  });

  test('M3: Apply & Restart returns success after MAC Auth config change', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'MAC Auth' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    await page.locator('.form-actions .btn-primary', { hasText: 'Apply & Restart' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('.msg.ok')).toContainText(/Applied/);
  });

  test('M4: MAC Auth config section persists with enabled flag', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'MAC Auth' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    const toggle = page.locator('.toggle input');
    await toggle.check({ force: true });
    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toContainText('Saved', { timeout: 10000 });

    // Verify persisted state via API
    const token = await getAuthToken();
    const resp = await fetch(`${BASE}/api/config/mac_auth`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.ok).toBeTruthy();
    const data = await resp.json();
    const macAuth = data.config?.['access.d.mac_auth'] || {};
    expect(macAuth.enabled).toBe('yes');
  });

});
