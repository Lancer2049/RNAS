import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('DHCP Relay + Option 82 (A5)', () => {

  test('N1: NetFlow/DHCP page loads with relay status row', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('NetFlow / DHCP').click();
    await expect(page.getByText('DHCP Relay (RFC 3046)')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('.relay-form').getByText('Option 82')).toBeVisible({ timeout: 5000 });
  });

  test('N2: Relay config form renders with all fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('NetFlow / DHCP').click();
    await expect(page.getByText('DHCP Relay (RFC 3046)')).toBeVisible({ timeout: 8000 });

    const labels = await page.locator('.relay-form .field-row label').allTextContents();
    const expected = ['Enabled', 'Upstream Server', 'GIADDR', 'Interface', 'Option 82'];
    for (const l of expected) {
      expect(labels.some(t => t.includes(l))).toBeTruthy();
    }
  });

  test('N3: Enable Option 82, save relay config, verify feedback and persistence', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('NetFlow / DHCP').click();
    await expect(page.getByText('DHCP Relay (RFC 3046)')).toBeVisible({ timeout: 8000 });

    // Wait for form to be populated from server before editing (avoid
    // overwriting upstream/giaddr/interface with empty strings on race)
    const upstreamInput = page.locator('.field-row', { hasText: 'Upstream Server' }).locator('input');
    await expect(upstreamInput).toHaveValue('192.168.0.202', { timeout: 5000 });

    // Enable Option 82 → circuit/remote ID fields appear
    const opt82Toggles = page.locator('.relay-form .toggle input');
    await opt82Toggles.nth(1).check({ force: true });
    await expect(page.locator('.opt82-fields')).toBeVisible({ timeout: 3000 });

    // Fill circuit/remote IDs
    const inputs = page.locator('.opt82-fields input');
    await inputs.nth(0).fill('rnas-e2e-port');
    await inputs.nth(1).fill('rnas-e2e');

    await page.locator('.relay-form .btn-primary', { hasText: /Save/i }).click();
    await expect(page.locator('.msg.ok')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.msg.ok')).toContainText('saved');
  });

  test('N4: Saved Option 82 config persists in config tree', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('NetFlow / DHCP').click();
    await expect(page.getByText('DHCP Relay (RFC 3046)')).toBeVisible({ timeout: 8000 });

    // Option 82 should now be enabled with the values saved in N3
    const opt82Toggles = page.locator('.relay-form .toggle input');
    await expect(opt82Toggles.nth(1)).toBeChecked({ timeout: 5000 });
    const inputs = page.locator('.opt82-fields input');
    await expect(inputs.nth(0)).toHaveValue('rnas-e2e-port', { timeout: 3000 });
    await expect(inputs.nth(1)).toHaveValue('rnas-e2e', { timeout: 3000 });
  });

});
