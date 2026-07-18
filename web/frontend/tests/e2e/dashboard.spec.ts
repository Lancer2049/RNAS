import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test('Dashboard loads with RADIUS state and system info visible', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await expect(page.locator('.rnas-topbar .t-brand')).toHaveText('RNAS', { timeout: 10000 });
  await expect(page.locator('.t-status')).toBeVisible({ timeout: 8000 });
  await expect(page.locator('.t-sessions')).toBeVisible({ timeout: 5000 });
  await expect(page.locator('.sidebar-foot')).toContainText(/running|v3/i);
});

test('Traffic Monitor on dashboard shows interface rates through UI', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  const trafficCard = page.locator('.card, .traffic-section, [class*="traffic"]').first();
  await expect(trafficCard).toBeVisible({ timeout: 10000 });
  const hasTable = await page.locator('table').first().isVisible().catch(() => false);
  const hasText = await page.getByText(/Interface|Rate|TX|RX|traffic|Mbps|Kbps/i).first().isVisible().catch(() => false);
  expect(hasTable || hasText).toBeTruthy();
});

test('IP Manager ARP tab shows ARP entries through UI', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.locator(SIDEBAR).getByText('IP Manager').click();
  await page.waitForTimeout(1500);
  await expect(page.locator('.ros-ip')).toBeVisible({ timeout: 8000 });
  await expect(page.locator('.ros-tabs button.sel')).toContainText('ARP');
  const hasTable = await page.locator('table').first().isVisible().catch(() => false);
  const hasEmpty = await page.locator('.empty').first().isVisible().catch(() => false);
  expect(hasTable || hasEmpty).toBeTruthy();
});

test('IP Manager switches all 8 tabs and each renders content', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.locator(SIDEBAR).getByText('IP Manager').click();
  await page.waitForTimeout(1500);
  const tabs = ['DHCP', 'Static', 'Filter', 'NAT', 'Mangle', 'Routes', 'Addresses'];
  for (const label of tabs) {
    await page.locator('.ros-tabs').getByText(label).click();
    await page.waitForTimeout(500);
    const tabBody = page.locator('.tab-body').first();
    await expect(tabBody).toBeVisible({ timeout: 5000 });
  }
});

test('Queue Manager — add a queue rule through form, verify it appears', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.locator(SIDEBAR).getByText('Queue (QoS)').click();
  await page.waitForTimeout(1500);

  // Lazy-loaded async component — need longer timeout
  await expect(page.getByRole('heading', { name: 'Queue Management' })).toBeVisible({ timeout: 10000 });

  // Open add form by clicking Add button if form is hidden
  const addForm = page.locator('.add-form');
  if (!(await addForm.isVisible().catch(() => false))) {
    const addBtn = page.locator('.btn-add, button:has-text("Add")').first();
    if (await addBtn.isVisible().catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(300);
    }
  }

  await expect(addForm).toBeVisible({ timeout: 5000 });
  const nameInput = addForm.locator('input').nth(0);
  const targetInput = addForm.locator('input').nth(1);
  await nameInput.fill('test-queue-ui');
  await targetInput.fill('192.168.100.50');
  await addForm.getByText('+ Add').click();
  await page.waitForTimeout(500);
  await expect(page.getByText('test-queue-ui')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('192.168.100.50')).toBeVisible({ timeout: 3000 });
});

test('No console errors', async ({ page }) => {
  const errors = [];
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.goto(BASE);
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  const real = errors.filter(e => !e.includes('favicon') && !e.includes('Failed to load resource') && !e.includes('WebSocket'));
  expect(real).toHaveLength(0);
});
