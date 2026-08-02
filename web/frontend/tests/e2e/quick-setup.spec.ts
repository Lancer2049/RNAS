import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Quick Setup Wizard — API Integration (A1)', () => {

  test('A1-1: Wizard loads with 3-step indicator and Step 1 Network form', async ({ page }) => {
    await page.route('**/api/setup/status', route => route.fulfill({ json: { configured: false, first_run: true } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Quick Setup').click();
    await expect(page.locator('.qs-step')).toHaveCount(3);
    await expect(page.locator('.qs-step').first()).toHaveClass(/active/);
    await expect(page.locator('input[placeholder="ens33"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.btn-next')).toBeVisible();
    await expect(page.locator('.qs-banner')).toHaveCount(0);
  });

  test('A1-2: Configured banner shows when setup/status reports configured', async ({ page }) => {
    await page.route('**/api/setup/status', route => route.fulfill({ json: { configured: true, first_run: false } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Quick Setup').click();
    await expect(page.locator('.qs-banner')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.qs-banner')).toContainText('Already configured');
  });

  test('A1-3: Full 3-step walkthrough applies and shows result feedback', async ({ page }) => {
    await page.route('**/api/setup/status', route => route.fulfill({ json: { configured: false, first_run: true } }));
    await page.route('**/api/setup/apply', route => route.fulfill({ json: { status: 'applied', services: ['radius.conf', 'pppoe.conf', 'ip-pool.conf'] } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Quick Setup').click();
    await expect(page.locator('.qs-step').first()).toHaveClass(/active/);

    await page.locator('.btn-next').click();
    await expect(page.locator('.qs-step').nth(1)).toHaveClass(/active/);
    await expect(page.locator('input[placeholder="192.168.0.202"]')).toBeVisible({ timeout: 3000 });

    await page.locator('.btn-next').click();
    await expect(page.locator('.qs-step').nth(2)).toHaveClass(/active/);
    await expect(page.locator('.qs-summary')).toContainText('ens33');
    await expect(page.locator('.qs-summary')).toContainText('192.168.0.202');

    await page.locator('.btn-apply').click();
    await expect(page.locator('.qs-result')).toContainText('applied', { timeout: 5000 });
    await expect(page.locator('.qs-result')).toHaveClass(/ok/);
  });

});
