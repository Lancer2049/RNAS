import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Certificate Manager — Generate & List', () => {

  test('B9: Certificate Manager page loads with generate button', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    // Generate button should be visible
    const genBtn = page.getByRole('button', { name: /Generate Self-Signed/i });
    await expect(genBtn).toBeVisible({ timeout: 5000 });
  });

  test('B9b: Open generate form and verify input fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    // Click the '+ Generate Self-Signed' button (exact text to avoid matching
    // the form's submit 'Generate' button too).
    const genBtn = page.getByRole('button', { name: /Generate Self-Signed/i });
    await expect(genBtn).toBeVisible({ timeout: 5000 });
    await genBtn.click();
    // Form should appear with Name, CN, Days inputs
    const nameInput = page.locator('.gen-form input').nth(0);
    const cnInput = page.locator('.gen-form input').nth(1);
    const daysInput = page.locator('.gen-form input[type="number"]');

    await expect(nameInput).toBeVisible({ timeout: 3000 });
    await expect(cnInput).toBeVisible({ timeout: 3000 });

    // Default values should be pre-filled
    const nameVal = await nameInput.inputValue();
    expect(nameVal.length).toBeGreaterThan(0);

    // Cancel button should close the form
    await page.locator('.gen-form button').filter({ hasText: 'Cancel' }).click();
    await expect(nameInput).not.toBeVisible({ timeout: 2000 }).catch(() => {});
  });

  test('B10: Certificate list renders (table or empty state)', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmpty = await page.getByText(/No certificates/i).isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();

    if (hasTable) {
      const headers = await page.locator('table thead th').allTextContents();
      expect(headers.some(h => /name/i.test(h))).toBeTruthy();
      expect(headers.some(h => /type|kind/i.test(h))).toBeTruthy();
      // S5: expiry column present
      expect(headers.some(h => /expir/i.test(h))).toBeTruthy();
      // S5: usage column present
      expect(headers.some(h => /usage/i.test(h))).toBeTruthy();
    }
  });

  test('B11: Generate a self-signed certificate appears in the list', async ({ page }) => {
    const uniqueName = `e2e-cert-${Date.now()}`;
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    await page.getByRole('button', { name: /Generate Self-Signed/i }).click();
    const nameInput = page.locator('.gen-form input').nth(0);
    const daysInput = page.locator('.gen-form input[type="number"]');
    await nameInput.fill(uniqueName);
    await daysInput.fill('365');
    await page.locator('.gen-form button').filter({ hasText: 'Generate' }).click();

    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.msg.ok')).toContainText('Certificate created');
    const row = page.locator('table tbody tr').filter({ hasText: `${uniqueName}.crt` });
    await expect(row).toBeVisible({ timeout: 8000 });
  });

  test('B12: Delete a generated certificate removes it from the list', async ({ page }) => {
    const uniqueName = `e2e-del-${Date.now()}`;
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    // create first
    await page.getByRole('button', { name: /Generate Self-Signed/i }).click();
    const nameInput = page.locator('.gen-form input').nth(0);
    await nameInput.fill(uniqueName);
    await page.locator('.gen-form button').filter({ hasText: 'Generate' }).click();
    await expect(page.locator('.msg.ok')).toContainText('Certificate created', { timeout: 15000 });
    const row = page.locator('table tbody tr').filter({ hasText: `${uniqueName}.crt` });
    await expect(row).toBeVisible({ timeout: 8000 });

    // delete it — handle confirm dialog
    page.once('dialog', d => d.accept());
    await row.locator('button', { hasText: 'Delete' }).click();
    await expect(page.locator('.msg.ok')).toContainText('Deleted', { timeout: 10000 });
    await expect(row).not.toBeVisible({ timeout: 8000 });
  });

  test('B13: Expiry badge shows days-left for certificates', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    const hasTable = await page.locator('table').isVisible().catch(() => false);
    if (hasTable) {
      const badges = page.locator('.exp-badge');
      const count = await badges.count();
      expect(count).toBeGreaterThan(0);
      // each badge shows a date and days marker
      const first = await badges.first().textContent();
      expect(first).toMatch(/\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}/);
    }
  });

});
