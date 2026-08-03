import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Network Config — Multicast (P2)', () => {

  test('P2-1: Network page shows Multicast card with loaded values', async ({ page }) => {
    await page.route('**/api/config', route => route.fulfill({
      json: { config: { 'network.d.multicast': { enabled: 'yes', multicast_net: '224.0.0.0/4' } } },
    }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Interfaces').click();
    await expect(page.locator('.card h3', { hasText: 'Multicast' })).toBeVisible({ timeout: 8000 });
    const mcastCard = page.locator('.card').filter({ hasText: 'Multicast' });
    await expect(mcastCard.locator('input').first()).toHaveValue('yes');
    await expect(mcastCard.locator('input').nth(1)).toHaveValue('224.0.0.0/4');
  });

  test('P2-2: Saving Multicast persists values via config API', async ({ page }) => {
    let savedBody = null;
    await page.route('**/api/config', route => route.fulfill({
      json: { config: { 'network.d.multicast': { enabled: 'no', multicast_net: '224.0.0.0/4' } } },
    }));
    await page.route('**/api/config/multicast', async route => {
      if (route.request().method() === 'PUT') {
        savedBody = route.request().postDataJSON();
        await route.fulfill({ json: { success: true } });
      } else {
        await route.fulfill({ json: { module: 'multicast', config: { 'network.d.multicast': { enabled: 'no', multicast_net: '224.0.0.0/4' } } } });
      }
    });
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Interfaces').click();
    await expect(page.locator('.card h3', { hasText: 'Multicast' })).toBeVisible({ timeout: 8000 });
    const mcastCard = page.locator('.card').filter({ hasText: 'Multicast' });

    await mcastCard.locator('input').first().fill('yes');
    await mcastCard.locator('.btn-save').click();
    await expect(mcastCard.locator('.saved-msg')).toBeVisible({ timeout: 5000 });
    expect(savedBody).toEqual({ enabled: 'yes', multicast_net: '224.0.0.0/4' });
  });

});
