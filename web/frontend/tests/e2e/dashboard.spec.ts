import { test, expect } from '@playwright/test';

test('Dashboard loads and shows topbar', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await expect(page.locator('.topbar .brand')).toHaveText('RNAS', { timeout: 10000 });
});

test('9 sidebar links present', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  const links = page.locator('nav.sidebar a');
  await expect(links).toHaveCount(9);
  const names = [/Overview/, /Sessions/, /Interfaces/, /VPN/, /Config/, /Editor/, /Dictionary/, /Tools/, /System/];
  for (let i = 0; i < names.length; i++) {
    await expect(links.nth(i)).toHaveText(names[i]);
  }
});

test('Sessions page shows table', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('nav.sidebar a:has-text("Sessions")');
  await page.waitForTimeout(1000);
  await expect(page.locator('.sessions-section, table').first()).toBeVisible({ timeout: 5000 });
});

test('Network page loads', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('nav.sidebar a:has-text("Interfaces")');
  await expect(page.locator('.network-section, .card h3').first()).toBeVisible({ timeout: 5000 });
});

test('Config page works', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('nav.sidebar a:has-text("Config")');
  await expect(page.locator('select')).toBeVisible({ timeout: 5000 });
});

test('Services page shows VPN modules', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('nav.sidebar a:has-text("VPN")');
  await expect(page.locator('h3:has-text("VPN")').first()).toBeVisible({ timeout: 5000 });
});

test('System page shows service status', async ({ page }) => {
  await page.goto('http://192.168.0.203:8099');
  await page.click('nav.sidebar a:has-text("System")');
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
