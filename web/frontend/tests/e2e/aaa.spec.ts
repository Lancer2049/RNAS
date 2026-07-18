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
    await page.locator(SIDEBAR).getByText('AAA Editor').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    await expect(page.getByText('RADIUS Message Editor')).toBeVisible({ timeout: 8000 });

    const inputs = page.locator('.field-row input');
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThanOrEqual(1);

    const firstVal = await inputs.first().inputValue().catch(() => '');
    expect(firstVal.length).toBeGreaterThan(0);
  });

  test('Dictionary page loads with attribute table', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Dictionary').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    await expect(page.getByText('RADIUS Dictionary')).toBeVisible({ timeout: 8000 });

    // replaced waitForTimeout(2000) → expect() auto-wait
    const hasTable = await page.locator('table').first().isVisible().catch(() => false);
    const hasContent = await page.getByText(/Attribute|Vendor|Code|Type|Name/i).first().isVisible().catch(() => false);
    expect(hasTable || hasContent).toBeTruthy();
  });

  test('RADIUS Monitor page loads with protocol stats', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Monitor').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    await expect(page.locator('h2, .page-title').first()).toBeVisible({ timeout: 8000 });
  });

});
