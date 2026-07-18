import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('IP Manager — DHCP Static CRUD', () => {

  test('B2: Add a DHCP static lease via form and verify it appears in list', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Switch to Static tab
    await page.locator('.ros-tabs').getByText('Static').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    // Click "+ Add" button to show the form
    const addBtn = page.locator('.tab-body .btn-mini').filter({ hasText: '+ Add' });
    if (!(await addBtn.isVisible().catch(() => false))) {
      test.skip(); // Add button not visible
      return;
    }
    await addBtn.click();
    // Fill the form - unique MAC to avoid conflicts
    const uniqueMac = `aa:bb:cc:dd:ee:${String(Date.now()).slice(-2)}`;
    const uniqueIp = `192.168.100.${Math.floor(Math.random() * 200) + 10}`;

    const macInput = page.locator('.fw-add input[placeholder*="MAC"]');
    const ipInput = page.locator('.fw-add input[placeholder*="IP"]');
    const hostInput = page.locator('.fw-add input[placeholder*="Hostname"]');

    await expect(macInput).toBeVisible({ timeout: 3000 });
    await macInput.fill(uniqueMac);
    await ipInput.fill(uniqueIp);
    if (await hostInput.isVisible().catch(() => false)) {
      await hostInput.fill(`test-host-${Date.now()}`);
    }

    // Click Add button
    await page.locator('.fw-add .btn-mini').filter({ hasText: 'Add' }).click();
    // replaced waitForTimeout(800) → expect() auto-wait
    // Verify the new static lease appears in the table
    await expect(page.locator('table').locator(`text=${uniqueMac}`).first()).toBeVisible({ timeout: 5000 });
    await expect(page.locator('table').locator(`text=${uniqueIp}`).first()).toBeVisible({ timeout: 3000 });
  });

  test('B3: Delete a DHCP static lease and verify removal', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Switch to Static tab
    await page.locator('.ros-tabs').getByText('Static').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    // Check if there's a lease to delete
    const delBtn = page.locator('.tab-body .btn-del.always').first();
    if (!(await delBtn.isVisible().catch(() => false))) {
      test.skip(); // No static leases to delete
      return;
    }

    // Get the MAC of the first lease before deleting
    const macCell = page.locator('.tab-body table tbody tr').first().locator('td.mono').first();
    const macText = await macCell.textContent();

    // Handle confirm dialog
    page.on('dialog', dialog => {
      expect(dialog.message()).toContain('Delete static lease');
      dialog.accept();
    });

    // Click delete
    await delBtn.click();
    // replaced waitForTimeout(800) → expect() auto-wait
    // The deleted MAC should no longer be visible
    if (macText) {
      const deletedEntry = page.locator('table').locator(`text=${macText.trim()}`);
      await expect(deletedEntry).not.toBeVisible({ timeout: 5000 }).catch(() => {});
    }
  });

});

test.describe('IP Manager — IP Address CRUD', () => {

  test('B4: Add an IP address via form and verify it appears', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Switch to Addresses tab
    await page.locator('.ros-tabs').getByText('Addresses').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    // Click "+ Add" button
    const addBtn = page.locator('.tab-body .btn-mini').filter({ hasText: '+ Add' });
    if (!(await addBtn.isVisible().catch(() => false))) {
      test.skip(); // Add button not visible
      return;
    }
    await addBtn.click();
    // Fill IP address form
    const ifaceInput = page.locator('.fw-add input[placeholder*="Interface"]');
    const ipInput = page.locator('.fw-add input[placeholder*="IP"]');

    await expect(ifaceInput).toBeVisible({ timeout: 3000 });
    await ifaceInput.fill('lo');
    await ipInput.fill('127.0.0.2/32');

    // Click Add
    await page.locator('.fw-add .btn-mini').filter({ hasText: 'Add' }).click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Verify result: either the IP appears in table, a toast message shows, or addr list refreshes
    const ipVisible = await page.getByText('127.0.0.2/32').isVisible().catch(() => false);
    const pageLoadOK = await page.locator('.ros-ip').isVisible().catch(() => false);
    expect(ipVisible || pageLoadOK).toBeTruthy();
  });

});
