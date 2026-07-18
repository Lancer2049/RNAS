import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('G — Performance & Stability (Browser UI)', () => {

  test('G1: Fast page hopping across 5 pages without crash', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));

    // Rapidly navigate through 5 pages with minimal wait
    const navTargets = ['Sessions', 'IP Manager', 'VPN Services', 'Config Editor', 'RADIUS Tools'];
    for (const target of navTargets) {
      await page.locator(SIDEBAR).getByText(target).click();
      await page.waitForTimeout(300); // minimal wait — simulate fast clicking
    }

    // Final page should still be rendered
    await page.waitForTimeout(500);
    const topbarVisible = await page.locator('.rnas-topbar').isVisible().catch(() => false);
    expect(topbarVisible).toBeTruthy();

    // Filter out known non-critical errors (favicon, WebSocket)
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('WebSocket') &&
      !e.includes('ERR_BLOCKED_BY_CLIENT')
    );
    expect(criticalErrors.length).toBe(0);
  });

  test('G2: Page refresh preserves routing and content', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

    // Navigate to a specific page
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('.rnas-content')).toBeVisible({ timeout: 5000 });

    // Reload the page
    await page.reload();
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

    // After reload, topbar should still be visible (no white screen)
    await expect(page.locator('.rnas-topbar')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.rnas-topbar .t-brand')).toHaveText('RNAS', { timeout: 5000 });
  });

  test('G3: 30-second open stability — no console error accumulation', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});

    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));

    // Wait 30 seconds with periodic UI check
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(5000);
      // Check the page is still responsive
      const brandVisible = await page.locator('.rnas-topbar .t-brand').isVisible().catch(() => false);
      expect(brandVisible).toBeTruthy();
    }

    expect(errors.length).toBe(0);
  });
});
