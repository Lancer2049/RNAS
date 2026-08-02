import { setupAuth, getAuthToken } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('802.1X Enterprise Access (P2-01)', () => {

  test('X1: 802.1X tab loads in Protocol Configuration with fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: '802.1X' });
    await expect(tab).toBeVisible({ timeout: 10000 });
    await tab.click();

    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });
    // RADIUS/EAP fields live under the collapsed Advanced Settings group
    await page.getByText('Advanced Settings').click();
    const labels = await page.locator('.field-row label').allTextContents();
    const expected = ['Auth Server', 'Auth Port', 'NAS Identifier', 'EAP Methods'];
    for (const l of expected) {
      expect(labels.some(t => t.includes(l))).toBeTruthy();
    }
  });

  test('X2: Save 802.1X config via UI shows "Saved" feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: '802.1X' });
    await expect(tab).toBeVisible({ timeout: 10000 });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    // Enable 802.1X via the toggle
    const toggle = page.locator('.toggle input');
    await toggle.check({ force: true });

    // NAS Identifier lives under Advanced Settings (collapsed by default)
    await page.getByText('Advanced Settings').click();
    const nasRow = page.locator('.field-row').filter({ has: page.locator('label', { hasText: 'NAS Identifier' }) });
    await nasRow.locator('input').fill('rnas-dot1x-e2e');

    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.msg.ok')).toContainText('Saved');
  });

  test('X3: Apply & Restart returns success after 802.1X config change', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: '802.1X' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    await page.locator('.form-actions .btn-primary', { hasText: 'Apply & Restart' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('.msg.ok')).toContainText(/Applied/);
  });

  test('X4: System Status page lists 802.1X Authenticator service', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    await expect(page.locator('.rnas-content')).toBeVisible({ timeout: 20000 });

    // Verify via API that rnas-dot1x shows active
    const token = await getAuthToken();
    const resp = await fetch(`${BASE}/api/v1/system/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await resp.json();
    const dot1x = data.services?.find((s: any) => s.name === 'rnas-dot1x');
    expect(dot1x).toBeTruthy();
    expect(dot1x.active).toBe('active');
  });

});
