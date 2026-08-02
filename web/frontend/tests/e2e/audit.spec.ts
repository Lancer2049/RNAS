import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Audit Log (S4)', () => {

  test('A1: Audit Log page loads with table or empty state', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Audit Log').click();
    await expect(page.getByRole('heading', { name: 'Audit Log' })).toBeVisible({ timeout: 8000 });

    const hasTable = await page.locator('.audit-table').isVisible().catch(() => false);
    const hasEmpty = await page.getByText(/No audit entries/i).isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test('A2: Saving a config through UI creates a config_update audit entry', async ({ page }) => {
    // 1. Change a config through the UI (MAC Auth tab save)
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.proto-config')).toBeVisible({ timeout: 20000 });
    const tab = page.locator('.proto-tabs button', { hasText: 'MAC Auth' });
    await tab.click();
    await expect(page.locator('.proto-form')).toBeVisible({ timeout: 10000 });
    await page.locator('.form-actions .btn-primary', { hasText: 'Save' }).click();
    await expect(page.locator('.msg.ok')).toContainText('Saved', { timeout: 10000 });

    // 2. Navigate to Audit Log and confirm a config_update row exists
    await page.locator(SIDEBAR).getByText('Audit Log').click();
    await expect(page.getByRole('heading', { name: 'Audit Log' })).toBeVisible({ timeout: 8000 });

    const rows = page.locator('.audit-table tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 5000 });
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);

    const actions = await page.locator('.act-badge').allTextContents();
    expect(actions.some(a => a.trim() === 'config_update')).toBeTruthy();
  });

  test('A3: Action filter narrows the audit table', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Audit Log').click();
    await expect(page.getByRole('heading', { name: 'Audit Log' })).toBeVisible({ timeout: 8000 });

    // Select config_update in the filter dropdown
    await page.locator('.filter-select').selectOption({ label: 'config_update' });
    await expect(page.locator('.audit-table tbody tr').first()).toBeVisible({ timeout: 5000 });

    // All visible badges must be config_update
    const actions = await page.locator('.act-badge').allTextContents();
    expect(actions.length).toBeGreaterThan(0);
    for (const a of actions) {
      expect(a.trim()).toBe('config_update');
    }
  });

});
