import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Port Forward Wizard (A2)', () => {

  test('P1: NAT → Port Forward subtab renders form fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.locator('.ros-tabs').getByText('NAT').click();
    await page.locator('.fw-subtabs').getByText('Port Forward').click();
    await expect(page.locator('.fw-pf h3')).toHaveText('Port Forward', { timeout: 8000 });

    const proto = page.locator('.pf-form select');
    await expect(proto).toBeVisible();
    await expect(page.locator('.pf-form input[placeholder*="External Port"]')).toBeVisible();
    await expect(page.locator('.pf-form input[placeholder*="Internal IP"]')).toBeVisible();
    await expect(page.locator('.pf-form input[placeholder*="Internal Port"]')).toBeVisible();
    await expect(page.locator('.pf-form input[placeholder*="Description"]')).toBeVisible();
    await expect(page.locator('.pf-form .btn-mini', { hasText: 'Add' })).toBeVisible();
  });

  test('P2: Add a port forward rule with description via UI', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.locator('.ros-tabs').getByText('NAT').click();
    await page.locator('.fw-subtabs').getByText('Port Forward').click();
    await expect(page.locator('.fw-pf h3')).toBeVisible({ timeout: 8000 });

    const uniqPort = 18000 + Math.floor(Math.random() * 2000);
    const desc = `e2e-pf-${Date.now()}`;

    await page.locator('.pf-form input[placeholder*="External Port"]').fill(String(uniqPort));
    await page.locator('.pf-form input[placeholder*="Internal IP"]').fill('192.168.100.50');
    await page.locator('.pf-form input[placeholder*="Internal Port"]').fill('8080');
    await page.locator('.pf-form input[placeholder*="Description"]').fill(desc);
    await page.locator('.pf-form .btn-mini', { hasText: 'Add' }).click();

    const row = page.locator('.fw-pf table tbody tr', { hasText: String(uniqPort) });
    await expect(row).toBeVisible({ timeout: 8000 });
    await expect(row).toContainText(desc);
  });

  test('P3: Port forward rule persists with comment in ruleset', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.locator('.ros-tabs').getByText('NAT').click();
    await page.locator('.fw-subtabs').getByText('Port Forward').click();
    await expect(page.locator('.fw-pf h3')).toBeVisible({ timeout: 8000 });

    const uniqPort = 20000 + Math.floor(Math.random() * 1000);
    const desc = `persist-${Date.now()}`;

    await page.locator('.pf-form input[placeholder*="External Port"]').fill(String(uniqPort));
    await page.locator('.pf-form input[placeholder*="Internal IP"]').fill('192.168.100.60');
    await page.locator('.pf-form input[placeholder*="Internal Port"]').fill('9090');
    await page.locator('.pf-form input[placeholder*="Description"]').fill(desc);
    await page.locator('.pf-form .btn-mini', { hasText: 'Add' }).click();

    const row = page.locator('.fw-pf table tbody tr', { hasText: String(uniqPort) });
    await expect(row).toContainText(desc, { timeout: 8000 });

    // Reload the page — rule (with comment) must still be parsed and shown
    await page.reload();
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.locator('.ros-tabs').getByText('NAT').click();
    await page.locator('.fw-subtabs').getByText('Port Forward').click();
    const row2 = page.locator('.fw-pf table tbody tr', { hasText: String(uniqPort) });
    await expect(row2).toBeVisible({ timeout: 8000 });
    await expect(row2).toContainText(desc);
  });

  test('P4: Delete a port forward rule via UI', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.locator('.ros-tabs').getByText('NAT').click();
    await page.locator('.fw-subtabs').getByText('Port Forward').click();
    await expect(page.locator('.fw-pf h3')).toBeVisible({ timeout: 8000 });

    const uniqPort = 22000 + Math.floor(Math.random() * 1000);

    await page.locator('.pf-form input[placeholder*="External Port"]').fill(String(uniqPort));
    await page.locator('.pf-form input[placeholder*="Internal IP"]').fill('192.168.100.70');
    await page.locator('.pf-form input[placeholder*="Internal Port"]').fill('7070');
    await page.locator('.pf-form .btn-mini', { hasText: 'Add' }).click();

    const row = page.locator('.fw-pf table tbody tr', { hasText: String(uniqPort) });
    await expect(row).toBeVisible({ timeout: 8000 });

    await row.locator('.btn-del').click();
    await expect(row).not.toBeVisible({ timeout: 8000 }).catch(() => {});
    const count = await page.locator('.fw-pf table tbody tr', { hasText: String(uniqPort) }).count();
    expect(count).toBe(0);
  });

});
