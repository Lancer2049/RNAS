import { setupAuth } from './auth-helper';
import { test, expect, type Page } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

function mockAlerts(page: Page, alerts: any[]) {
  return page.route('**/api/system/health/alerts', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total: alerts.length,
        critical: alerts.filter(a => a.severity === 'critical').length,
        alerts,
      }),
    }),
  );
}

test.describe('Alert banner (Browser UI)', () => {

  test('banner is hidden when system is healthy', async ({ page }) => {
    await mockAlerts(page, []);
    await page.goto(BASE);
    await expect(page.locator('.alert-banner')).toHaveCount(0, { timeout: 8000 });
  });

  test('critical service alert renders in banner', async ({ page }) => {
    await mockAlerts(page, [{
      type: 'service', service: 'rnas-accel-ppp', desc: 'Access Server',
      status: 'failed', severity: 'critical',
      title: 'Service rnas-accel-ppp is failed', message: 'Access Server (PPPoE/L2TP/PPTP/SSTP)',
    }]);
    await page.goto(BASE);
    const item = page.locator('.alert-item').first();
    await expect(item).toBeVisible({ timeout: 8000 });
    await expect(item).toHaveClass(/sev-critical/);
    await expect(item.locator('.ai-title')).toContainText('rnas-accel-ppp');
  });

  test('warning disk alert uses warning styling', async ({ page }) => {
    await mockAlerts(page, [{
      type: 'disk', service: 'disk', status: 'warning', severity: 'warning',
      title: 'Disk usage at 85%', message: 'Root filesystem is 85% full.',
    }]);
    await page.goto(BASE);
    const item = page.locator('.alert-item').first();
    await expect(item).toBeVisible({ timeout: 8000 });
    await expect(item).toHaveClass(/sev-warning/);
    await expect(item.locator('.ai-title')).toContainText('Disk usage');
  });

  test('banner click navigates to system page', async ({ page }) => {
    await mockAlerts(page, [{
      type: 'service', service: 'dnsmasq', desc: 'DHCP/DNS',
      status: 'failed', severity: 'critical',
      title: 'Service dnsmasq is failed', message: 'DHCP/DNS',
    }]);
    await page.goto(BASE);
    const item = page.locator('.alert-item').first();
    await expect(item).toBeVisible({ timeout: 8000 });
    await item.click();
    await expect(page.locator('.system-section h2')).toHaveText('System', { timeout: 5000 });
  });

  test('topbar alert badge count matches mock', async ({ page }) => {
    await mockAlerts(page, [
      { type: 'service', service: 'x', status: 'failed', severity: 'critical', title: 'a', message: '' },
      { type: 'disk', service: 'disk', status: 'warning', severity: 'warning', title: 'b', message: '' },
    ]);
    await page.goto(BASE);
    const badge = page.locator('.t-alerts');
    await expect(badge).toBeVisible({ timeout: 8000 });
    await expect(badge).toContainText('3');
    await expect(page.locator('.alert-item')).toHaveCount(2);
  });

  test('topbar badge hidden when no alerts', async ({ page }) => {
    await mockAlerts(page, []);
    await page.goto(BASE);
    await expect(page.locator('.t-alerts')).toHaveCount(0, { timeout: 8000 });
  });
});
