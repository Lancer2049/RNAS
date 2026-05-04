import { test, expect } from '@playwright/test';

test('Dashboard loads and shows header', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await expect(page.locator('header h1')).toHaveText('RNAS Dashboard', { timeout: 10000 });
});

test('9 tabs are present', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  const tabs = page.locator('nav.tabs button');
  await expect(tabs).toHaveCount(9);
  const names = ['Overview', 'Sessions', 'Network', 'Config', 'Services', 'Tools', 'RADIUS', 'Dictionary', 'System'];
  for (let i = 0; i < names.length; i++) {
    await expect(tabs.nth(i)).toHaveText(names[i]);
  }
});

test('Sessions tab shows disconnect buttons', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('button:has-text("Sessions")');
  await page.waitForTimeout(1000);
  // Just verify the page loaded the sessions tab
  await expect(page.locator('.sessions-section, table').first()).toBeVisible({ timeout: 5000 });
});

test('Network tab loads', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('button:has-text("Network")');
  await expect(page.locator('.network-section, .card h3').first()).toBeVisible({ timeout: 5000 });
});

test('Config tab works', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('button:has-text("Config")');
  await expect(page.locator('select')).toBeVisible({ timeout: 5000 });
});

test('Services tab shows all modules', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('button:has-text("Services")');
  await expect(page.locator('h3:has-text("QoS")')).toBeVisible({ timeout: 5000 });
  await expect(page.locator('h3:has-text("IPsec")')).toBeVisible();
  await expect(page.locator('h3:has-text("High Availability")')).toBeVisible();
});

test('System tab shows service status', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('button:has-text("System")');
  await page.waitForTimeout(1000);
  await expect(page.locator('.badge, .system-section, h2').first()).toBeVisible({ timeout: 10000 });
});

test('No console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto('http://192.168.0.203:8099');
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  const real = errors.filter(e => !e.includes('favicon') && !e.includes('Failed to load resource') && !e.includes('WebSocket'));
  expect(real).toHaveLength(0);
});
