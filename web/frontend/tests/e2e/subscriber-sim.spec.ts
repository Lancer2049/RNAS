import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('B3 — Subscriber Sim Multi-User Batch Dial', () => {

  async function openSim(page) {
    await page.goto(BASE);
    await page.waitForTimeout(800);
    await page.locator('.rnas-sidebar').getByText('Subscriber Sim').click();
    await page.waitForTimeout(600);
    await expect(page.locator('h2', { hasText: 'Subscriber Simulation' })).toBeVisible({ timeout: 5000 });
  }

  test('B3-1: Sim page renders controls and multi-user hint', async ({ page }) => {
    await openSim(page);
    // All controls present
    await expect(page.locator('select')).toBeVisible();
    const inputs = page.locator('.controls input');
    await expect(inputs.nth(0)).toHaveValue('5');  // Count default
    await expect(inputs.nth(1)).toHaveValue('testuser');  // User default
    await expect(page.locator('.btn-start')).toBeVisible();
    await expect(page.locator('.btn-stop')).toBeVisible();
    // Count > 1 shows multi-user hint (user-1 … user-N)
    await inputs.nth(0).fill('3');
    await expect(page.locator('.multi-hint')).toContainText('testuser-1');
    await expect(page.locator('.multi-hint')).toContainText('testuser-3');
    // Count = 1 hides the hint
    await inputs.nth(0).fill('1');
    await expect(page.locator('.multi-hint')).toHaveCount(0);
  });

  test('B3-2: Multi-user dial creates N connections with distinct users', async ({ page }) => {
    test.setTimeout(180000);
    await openSim(page);
    const inputs = page.locator('.controls input');
    await inputs.nth(0).fill('2');           // Count
    await inputs.nth(1).fill('b3e2e');       // User base
    await inputs.nth(2).fill('testpass');    // Pass
    await page.locator('.btn-start').click();

    // Two result rows, both successful, distinct usernames and IPs
    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(2, { timeout: 120000 });
    const rowTexts = await rows.allTextContents();
    const first = rowTexts[0] ?? '';
    const second = rowTexts[1] ?? '';
    expect(first).toContain('b3e2e-1');
    expect(second).toContain('b3e2e-2');
    expect(first).toContain('✅');
    expect(second).toContain('✅');
    const ip1 = first.match(/192\.168\.\d+\.\d+/) ?? [];
    const ip2 = second.match(/192\.168\.\d+\.\d+/) ?? [];
    expect(ip1.length).toBe(1);
    expect(ip2.length).toBe(1);
    expect(ip1[0]).not.toBe(ip2[0]);
  });

  test('B3-3: Count=1 still uses single dial path', async ({ page }) => {
    test.setTimeout(90000);
    await openSim(page);
    const inputs = page.locator('.controls input');
    await inputs.nth(0).fill('1');
    await inputs.nth(1).fill('testuser');
    await page.locator('.btn-start').click();
    const rows = page.locator('table tbody tr');
    await expect(rows).toHaveCount(1, { timeout: 60000 });
    const rowText = await rows.first().textContent() ?? '';
    expect(rowText).toContain('testuser');
    expect(rowText).toContain('✅');
  });

  test('B3-4: Stop resets state and cleans up sessions', async ({ page }) => {
    test.setTimeout(90000);
    await openSim(page);
    const inputs = page.locator('.controls input');
    await inputs.nth(0).fill('1');
    await inputs.nth(1).fill('testuser');
    await page.locator('.btn-start').click();
    // Stop must be clicked while the dial is still running (it is disabled after)
    await expect(page.locator('.btn-stop')).toBeEnabled({ timeout: 15000 });
    await page.locator('.btn-stop').click();
    await expect(page.locator('.status')).toContainText('Ready', { timeout: 60000 });
    // The dial request completes after Stop; wait for its result row
    await expect(page.locator('table tbody tr')).toHaveCount(1, { timeout: 60000 });
    await page.waitForTimeout(1000);
    await expect(page.locator('.btn-start')).toBeEnabled();
    // Session table no longer shows the test user (refresh until cleared)
    await page.locator('.rnas-sidebar').getByText('Active Sessions').click();
    await expect.poll(async () => {
      await page.locator('.btn-refresh').click();
      await expect(page.locator('.btn-refresh')).toBeEnabled({ timeout: 15000 });
      await page.waitForTimeout(300);
      const body = await page.locator('.rnas-content').textContent() ?? '';
      return !body.includes('testuser');
    }, { timeout: 60000 }).toBe(true);
  });
});
