import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Protocol Config — Speed Limit & IPoE Option 60 (P0)', () => {

  test('P0-1: PPPoE form shows Speed Limit field', async ({ page }) => {
    await page.route('**/api/config', route => route.fulfill({ json: { config: { 'access.d.pppoe': {} } } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.page-title')).toContainText('Protocol Configuration', { timeout: 8000 });
    const speedField = page.locator('.field-row').filter({ hasText: 'Speed Limit' });
    await expect(speedField).toBeVisible({ timeout: 5000 });
    await expect(speedField).toContainText('Kbit/s per session');
  });

  test('P0-2: IPoE form shows Speed Limit and Option 60 fields', async ({ page }) => {
    await page.route('**/api/config', route => route.fulfill({ json: { config: { 'access.d.ipoe': {} } } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.page-title')).toContainText('Protocol Configuration', { timeout: 8000 });
    await page.locator('.proto-tabs').getByText('IPoE').click();
    const speedField = page.locator('.field-row').filter({ hasText: 'Speed Limit' });
    await expect(speedField).toBeVisible({ timeout: 5000 });
    const opt60Field = page.locator('.field-row').filter({ hasText: 'Option 60' });
    await expect(opt60Field).toBeVisible({ timeout: 5000 });
    await expect(opt60Field).toContainText('Vendor Class');
  });

  test('P0-3: Saving speed limit and option 60 persists values', async ({ page }) => {
    let savedBody = null;
    await page.route('**/api/config', route => route.fulfill({ json: { config: { 'access.d.ipoe': {} } } }));
    await page.route('**/api/config/ipoe', route => route.fulfill({ json: { status: 'saved' } }));
    await page.route('**/api/config/core', route => route.fulfill({ json: { status: 'saved' } }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await expect(page.locator('.page-title')).toContainText('Protocol Configuration', { timeout: 8000 });
    await page.locator('.proto-tabs').getByText('IPoE').click();
    await expect(page.locator('.field-row').filter({ hasText: 'Speed Limit' })).toBeVisible({ timeout: 5000 });

    const speedInput = page.locator('.field-row').filter({ hasText: 'Speed Limit' }).locator('input');
    await speedInput.fill('512/1024');
    const opt60Input = page.locator('.field-row').filter({ hasText: 'Option 60' }).locator('input');
    await opt60Input.fill('OpenWrt-IPoE');

    await page.route('**/api/config/ipoe', async route => {
      savedBody = route.request().postDataJSON();
      await route.fulfill({ json: { status: 'saved' } });
    });
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.locator('.msg.ok, .msg')).toContainText('Saved', { timeout: 5000 });
    expect(savedBody).toMatchObject({ speed_limit: '512/1024', option60: 'OpenWrt-IPoE' });
  });

});
