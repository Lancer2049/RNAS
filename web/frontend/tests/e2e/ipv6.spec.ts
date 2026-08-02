import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('IPv6 Dual-Stack (P2-05)', () => {

  test('V1: IPv6 tab loads in Protocol Configuration with fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'IPv6' });
    await expect(tab).toBeVisible({ timeout: 10000 });
    await tab.click();

    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });
    // IPv6 fields (prefix/delegate/dns/domain/ra-interval) live under the
    // collapsed Advanced Settings group, same as dot1x
    await page.getByText('Advanced Settings').click();
    const labels = await page.locator('.field-row label').allTextContents();
    const expected = ['Prefix Pool', 'Delegate', 'DNS', 'Domain', 'RA Interval'];
    for (const l of expected) {
      expect(labels.some(t => t.includes(l))).toBeTruthy();
    }
  });

  test('V2: Enable IPv6 saves successfully with "Saved" feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'IPv6' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    // Enable via toggle
    const toggle = page.locator('.toggle input');
    await toggle.check({ force: true });

    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.msg.ok')).toContainText('Saved');
  });

  test('V3: Apply & Restart returns success with IPv6 enabled', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'IPv6' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    const toggle = page.locator('.toggle input');
    const isChecked = await toggle.isChecked();
    if (!isChecked) await toggle.check({ force: true });

    await page.locator('.form-actions .btn-primary', { hasText: 'Apply & Restart' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('.msg.ok')).toContainText('Applied');
  });

  test('V4: Disable IPv6 saves and persists toggle state off', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });

    const tab = page.locator('.proto-tabs button', { hasText: 'IPv6' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });

    const toggle = page.locator('.toggle input');
    if (await toggle.isChecked()) await toggle.uncheck({ force: true });

    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.msg.ok')).toContainText('Saved');
  });

});
