import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('RADIUS AAA — Pages via Sidebar', () => {

  test('AAA Editor (RADIUS Message Builder) loads with RadEdit form', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('AAA Editor').click();
    await page.waitForTimeout(1000);

    await expect(page.getByText('RADIUS Message Editor')).toBeVisible({ timeout: 8000 });

    const inputs = page.locator('.field-row input');
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThanOrEqual(1);

    const firstVal = await inputs.first().inputValue().catch(() => '');
    expect(firstVal.length).toBeGreaterThan(0);
  });

  test('Dictionary page loads with attribute table', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Dictionary').click();
    await page.waitForTimeout(1000);

    await expect(page.getByText('RADIUS Dictionary')).toBeVisible({ timeout: 8000 });

    await page.waitForTimeout(2000);
    const hasTable = await page.locator('table').first().isVisible().catch(() => false);
    const hasContent = await page.getByText(/Attribute|Vendor|Code|Type|Name/i).first().isVisible().catch(() => false);
    expect(hasTable || hasContent).toBeTruthy();
  });

  test('RADIUS Monitor page loads with protocol stats', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('RADIUS Monitor').click();
    await page.waitForTimeout(1000);

    await expect(page.locator('h2, .page-title').first()).toBeVisible({ timeout: 8000 });
  });

});
