import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8099';

test('Dashboard: topbar and status', async ({ page }) => {
  await page.goto(BASE);
  await expect(page.locator('.topbar .brand')).toHaveText('RNAS');
  await expect(page.getByText('Uptime')).toBeVisible({ timeout: 8000 });
});

test('Protocols: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForSelector('nav.sidebar a', {timeout:5000}); await page.locator('nav.sidebar a:has-text("Protocols")').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Protocol').first()).toBeVisible({ timeout: 5000 });
});

test('Sessions: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Sessions').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Active Sessions').first()).toBeVisible({ timeout: 5000 });
});

test.skip('Network: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Interfaces').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Network')).toBeVisible({ timeout: 5000 });
});

test('RADIUS Editor: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Editor').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('RADIUS Message')).toBeVisible({ timeout: 5000 });
});

test('Dictionary: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Dictionary').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('RADIUS Dictionary')).toBeVisible({ timeout: 5000 });
});

test('Torch: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Torch').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Traffic Torch')).toBeVisible({ timeout: 5000 });
});

test('Queues: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Queues').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Queue Management')).toBeVisible({ timeout: 5000 });
});

test('Subscribers: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar').getByText('Subscribers').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Subscriber Simulation')).toBeVisible({ timeout: 5000 });
});

test.skip('System: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator('nav.sidebar a:has-text("System")').last().click();
  await page.waitForTimeout(500);
  await expect(page.getByText('System').first()).toBeVisible({ timeout: 5000 });
});

test('No console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  const real = errors.filter(e => !e.includes('favicon') && !e.includes('WebSocket') && !e.includes('Failed to load'));
  expect(real).toHaveLength(0);
});
