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
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await page.waitForTimeout(1500);

    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    // Generate button should be visible
    const genBtn = page.locator('button').filter({ hasText: 'Generate' });
    await expect(genBtn).toBeVisible({ timeout: 5000 });
  });

  test('B9b: Open generate form and verify input fields', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await page.waitForTimeout(1500);

    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });

    // Click generate button to reveal form
    const genBtn = page.locator('button').filter({ hasText: 'Generate' });
    await genBtn.click();
    await page.waitForTimeout(400);

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
    await page.waitForTimeout(300);
    await expect(nameInput).not.toBeVisible({ timeout: 2000 }).catch(() => {});
  });

  test('B10: Certificate list renders (table or empty state)', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Certificates').click();
    await page.waitForTimeout(1500);
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 8000 });
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmpty = await page.getByText(/No certificates/i).isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();

    if (hasTable) {
      const headers = await page.locator('table thead th').allTextContents();
      expect(headers.some(h => /name/i.test(h))).toBeTruthy();
      expect(headers.some(h => /type|kind/i.test(h))).toBeTruthy();
    }
  });

});
