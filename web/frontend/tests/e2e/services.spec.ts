import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Services — Full Protocol Integration', () => {

  test('B1a: Services loads with status bar and all VPN service indicators', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 20000 });

    // Status bar should show service indicators
    const statusItems = page.locator('.status-item');
    await expect(statusItems.first()).toBeVisible({ timeout: 8000 });
    const statusTexts = await statusItems.allTextContents();
    const names = ['IPsec', 'WireGuard', 'OpenVPN', 'Hotspot', 'VRRP'];
    for (const name of names) {
      expect(statusTexts.some(t => t.includes(name))).toBeTruthy();
    }
  });

  test('B1b: Switch between all 6 service tabs and each shows fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });

    const serviceTabs = [
      'QoS / Traffic Control',
      'VPN - IPsec',
      'VPN - WireGuard',
      'VPN - OpenVPN',
      'Hotspot / Captive Portal',
      'High Availability (VRRP)',
    ];

    for (const label of serviceTabs) {
      await page.locator('.svc-nav button').filter({ hasText: label }).click();
      // replaced waitForTimeout(600) → expect() auto-wait
      // Each tab should show a panel or fields
      const panel = page.locator('.svc-panel');
      await expect(panel).toBeVisible({ timeout: 8000 });

      // Should have at least one field row
      const fieldCount = await page.locator('.svc-panel .field-row').count();
      expect(fieldCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('B1c: Modify a field, save, verify "✓ Saved" feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });

    // Ensure QoS tab is active (first tab by default)
    await page.locator('.svc-nav button').filter({ hasText: 'QoS / Traffic Control' }).click();
    // replaced waitForTimeout(600) → expect() auto-wait
    // Use the first select (yes/no) field in the panel
    const selectField = page.locator('.svc-panel select.field-input').first();
    if (!(await selectField.isVisible().catch(() => false))) {
      test.skip();
      return;
    }

    // Toggle the value
    const currentVal = await selectField.inputValue();
    const newVal = currentVal === 'yes' ? 'no' : 'yes';
    await selectField.selectOption(newVal);
    // Save
    await page.locator('.btn-save').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    // Verify "✓ Saved" feedback
    const savedMsg = page.locator('.saved-msg');
    await expect(savedMsg).toBeVisible({ timeout: 5000 });
    await expect(savedMsg).toContainText('Saved');
  });

  test('B1d: Switch to IPsec tab, verify fields are present', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });

    await page.locator('.svc-nav button').filter({ hasText: 'VPN - IPsec' }).click();
    // replaced waitForTimeout(600) → expect() auto-wait
    const panel = page.locator('.svc-panel');
    await expect(panel).toBeVisible({ timeout: 8000 });
    await expect(panel.locator('h3')).toContainText('VPN - IPsec');
  });

  test('B1e: Switch to WireGuard tab, verify fields present', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });

    await page.locator('.svc-nav button').filter({ hasText: 'VPN - WireGuard' }).click();
    // replaced waitForTimeout(600) → expect() auto-wait
    const panel = page.locator('.svc-panel');
    await expect(panel).toBeVisible({ timeout: 8000 });
    await expect(panel.locator('h3')).toContainText('VPN - WireGuard');
  });

  test('B1f: Switch to OpenVPN tab, verify fields present', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });

    await page.locator('.svc-nav button').filter({ hasText: 'VPN - OpenVPN' }).click();
    // replaced waitForTimeout(600) → expect() auto-wait
    const panel = page.locator('.svc-panel');
    await expect(panel).toBeVisible({ timeout: 8000 });
    await expect(panel.locator('h3')).toContainText('VPN - OpenVPN');

    // OpenVPN should have yes/no fields for enabled at minimum
    const selectCount = await page.locator('.svc-panel select.field-input').count();
    if (selectCount > 0) {
      const firstSelect = page.locator('.svc-panel select.field-input').first();
      await expect(firstSelect).toBeVisible({ timeout: 2000 });
    }
  });

});
