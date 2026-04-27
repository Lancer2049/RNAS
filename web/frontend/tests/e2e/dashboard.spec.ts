import { test, expect } from '@playwright/test';

test.describe('RNAS Dashboard E2E', () => {

  test('Overview tab shows service status and sessions', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('header h1')).toHaveText('RNAS Dashboard');

    // Status cards should be visible
    await expect(page.locator('.status-grid')).toBeVisible();
    await expect(page.locator('.card-value').first()).toBeVisible();

    // Sessions table should be visible on overview
    const rows = page.locator('table tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 10000 });
  });

  test('Sessions tab shows session list', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Sessions")');

    // Should show sessions table
    await expect(page.locator('table')).toBeVisible({ timeout: 5000 });
    const rows = page.locator('table tbody tr');
    await expect(rows.first()).toBeVisible();
  });

  test('Network tab shows interfaces and DHCP config', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Network")');

    // Should show interfaces card
    await expect(page.locator('.card h3:has-text("Interfaces")')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.card h3:has-text("DHCP Server")')).toBeVisible();
    await expect(page.locator('.card h3:has-text("Firewall Zones")')).toBeVisible();
  });

  test('Disconnect button appears on sessions', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Sessions")');
    await page.waitForSelector('table tbody tr', { timeout: 5000 });

    // Disconnect button should exist
    const btn = page.locator('button:has-text("Disconnect")').first();
    await expect(btn).toBeVisible();
  });

  test('Dashboard loads without console errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0);
  });

  test('Config tab allows editing and saving', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Config")');

    // Should show the config editor header
    await expect(page.locator('h2:has-text("Configuration Editor")')).toBeVisible({ timeout: 5000 });

    // Select a module from dropdown
    await page.selectOption('select', { index: 1 });
    await page.waitForTimeout(500);

    // Should load config fields
    const inputs = page.locator('.field-row input').first();
    await expect(inputs).toBeVisible({ timeout: 3000 });

    // Verify save button exists
    const saveBtn = page.locator('button:has-text("Save")');
    await expect(saveBtn).toBeVisible();
  });

  test('Services tab shows QoS, VPN, Hotspot, HA config', async ({ page }) => {
    await page.goto('/');
    await page.click('button:has-text("Services")');

    // Should show each service card
    await expect(page.locator('h3:has-text("QoS")')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('h3:has-text("IPsec")')).toBeVisible();
    await expect(page.locator('h3:has-text("WireGuard")')).toBeVisible();
    await expect(page.locator('h3:has-text("OpenVPN")')).toBeVisible();
    await expect(page.locator('h3:has-text("Hotspot")')).toBeVisible();
    await expect(page.locator('h3:has-text("High Availability")')).toBeVisible();
  });
});
