import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8099';
const SIDEBAR = 'nav.rnas-sidebar';

test('Dashboard: topbar and status', async ({ page }) => {
  await page.goto(BASE);
  await expect(page.locator('.rnas-topbar .t-brand')).toHaveText('RNAS');
  await expect(page.locator('.ros-status')).toBeVisible({ timeout: 8000 });
});

test('Protocols: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Access Protocols').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Protocol Configuration')).toBeVisible({ timeout: 5000 });
});

test('Sessions: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.click(SIDEBAR + ' a:nth-child(2)');
  await page.waitForTimeout(2000);
  await expect(page.getByRole('heading', { name: /Active Sessions/ })).toBeVisible({ timeout: 8000 });
});

test('Network: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Interfaces').click();
  await page.waitForTimeout(500);
  await expect(page.locator('h2').filter({ hasText: 'Network' })).toBeVisible({ timeout: 5000 });
});

test('RADIUS Editor: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('AAA Editor').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('RADIUS Message Editor')).toBeVisible({ timeout: 5000 });
});

test('Dictionary: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Dictionary').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('RADIUS Dictionary')).toBeVisible({ timeout: 5000 });
});

test('Torch: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Traffic Torch').first().click();
  await page.waitForTimeout(500);
  await expect(page.getByRole('heading', { name: 'Traffic Torch' })).toBeVisible({ timeout: 5000 });
});

test('Queues: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Queue (QoS)').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Queue Management')).toBeVisible({ timeout: 5000 });
});

test('Subscribers: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('Subscriber Sim').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('Subscriber Simulation')).toBeVisible({ timeout: 5000 });
});

test('System: page loads', async ({ page }) => {
  await page.goto(BASE);
  await page.locator(SIDEBAR).getByText('System Log').click();
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
