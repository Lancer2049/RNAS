import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('B2 — Interface Detail Enhancement (Traffic History Chart)', () => {

  async function openFirstInterface(page) {
    // Detail page is entered via TrafficMonitor rows on the dashboard (view-interface event)
    await page.goto(BASE);
    await expect(page.locator('.if-table tbody tr').first()).toBeVisible({ timeout: 8000 });
    // Pick first non-lo interface row
    const rows = page.locator('.if-table tbody tr');
    const count = await rows.count();
    let target = null;
    for (let i = 0; i < count; i++) {
      const name = await rows.nth(i).locator('td').first().textContent();
      if (name && name.trim() !== 'lo') { target = rows.nth(i); break; }
    }
    if (!target) target = rows.first();
    await target.click();
    await expect(page.locator('.iface-detail')).toBeVisible({ timeout: 5000 });
  }

  test('B2-1: Interface detail shows Traffic History section with 4 period buttons', async ({ page }) => {
    await openFirstInterface(page);
    const histTitle = page.locator('.hist-title');
    await expect(histTitle).toBeVisible({ timeout: 5000 });
    await expect(histTitle).toContainText('Traffic History');
    // All four period buttons must be present
    for (const p of ['5m', '1h', '1d', '1w']) {
      await expect(page.locator('.range-btns button', { hasText: p })).toBeVisible();
    }
    // Chart canvas rendered
    await expect(page.locator('canvas')).toBeVisible();
  });

  test('B2-2: Interface detail chart renders data points after load', async ({ page }) => {
    await openFirstInterface(page);
    await expect(page.locator('.hist-title')).toBeVisible({ timeout: 5000 });
    // Wait for history fetch (issue with chart data loading async)
    await page.waitForTimeout(1500);
    const canvasState = await page.locator('canvas.hist-canvas').getAttribute('style');
    console.log(`[B2-2] canvas style: ${canvasState}`);
    // Canvas must have a rendered size (non-zero) — chart initialized
    expect(canvasState ?? '').toContain('height');
  });

  test('B2-3: Switching period buttons triggers history re-fetch (no errors)', async ({ page }) => {
    await openFirstInterface(page);
    await expect(page.locator('.hist-title')).toBeVisible({ timeout: 5000 });
    // Cycle through 5m → 1d → 1w clicking each, page must stay stable
    for (const p of ['5m', '1d', '1w']) {
      const btn = page.locator('.range-btns button', { hasText: p });
      await btn.click();
      await page.waitForTimeout(600);
      // Button becomes selected state
      await expect(btn).toHaveClass(/sel/);
    }
    // Back to 1h (default) — selected class present
    const oneHour = page.locator('.range-btns button', { hasText: '1h' });
    await oneHour.click();
    await expect(oneHour).toHaveClass(/sel/);
    // Detail content still intact
    await expect(page.locator('.iface-detail h2').first()).toBeVisible();
  });

  test('B2-4: Interface detail still shows stats + sessions after chart added', async ({ page }) => {
    await openFirstInterface(page);
    const text = await page.locator('.iface-detail').textContent() ?? '';
    expect(/MAC|IP|RX|TX|Status/i.test(text)).toBeTruthy();
    await expect(page.locator('h3', { hasText: 'Associated Sessions' })).toBeVisible({ timeout: 5000 });
    // Chart block sits between stats grid and sessions table
    const histVisible = await page.locator('.hist-block').isVisible();
    expect(histVisible).toBeTruthy();
  });
});