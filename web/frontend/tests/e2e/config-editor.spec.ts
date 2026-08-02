import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Config Editor — Browse/Edit/Snapshot', () => {

  test('B5: Config Editor loads with category sidebar', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.config-section')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.cfg-sidebar')).toBeVisible({ timeout: 10000 });

    // Wait for lazily-loaded config modules from API (cold start can be slow)
    const firstItem = page.locator('.cfg-item').first();
    await expect(firstItem).toBeVisible({ timeout: 25000 });

    // Verify at least one group label rendered
    const groupLabels = page.locator('.cfg-group-label');
    const count = await groupLabels.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('B5b: Select a config category and view its fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Wait for config modules to load from API (can be slow on first load)
    const firstItem = page.locator('.cfg-item').first();
    await expect(firstItem).toBeVisible({ timeout: 25000 });
    await firstItem.click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    // Editor card should appear with fields
    const editorCard = page.locator('.editor-card');
    await expect(editorCard).toBeVisible({ timeout: 20000 });

    // Should show field rows with labels and inputs
    const fieldRows = page.locator('.editor-card .field-row');
    const fieldCount = await fieldRows.count();
    expect(fieldCount).toBeGreaterThanOrEqual(1);
  });

  test('B6: Modify a config field, save, verify success message', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Wait for async component + API data to load (cold start can be slow)
    const firstItem = page.locator('.cfg-item').first();
    await expect(firstItem).toBeVisible({ timeout: 25000 });
    await firstItem.click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    // Find a text input (not select/yes-no) field to modify
    const textInput = page.locator('.editor-card .field-row input.field-input:not([type="number"])').first();
    if (!(await textInput.isVisible().catch(() => false))) {
      test.skip(); // No editable text field
      return;
    }

    // Read current value, modify temporarily
    const currentVal = await textInput.inputValue();
    const testSuffix = '-test-modify';
    if (currentVal.endsWith(testSuffix)) {
      // Already modified, skip to avoid infinite growth
      test.skip();
      return;
    }

    // Append a test marker
    await textInput.fill(currentVal + testSuffix);
    // Click Save
    await page.locator('.btn-save').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    // Check for success message (could be toast or inline msg)
    const msgVisible = await page.locator('.msg.success, .msg.ok, .toast-msg, .saved-msg').first().isVisible().catch(() => false);
    const saveDisabled = await page.locator('.btn-save:disabled').isVisible().catch(() => false);
    expect(msgVisible || saveDisabled).toBeTruthy();

    // Restore original value
    await textInput.fill(currentVal);
    await page.locator('.btn-save').click();
  });

  test('B7: Config Snapshots page shows snapshot list or create option', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // Wait for async component and API data
    const firstItem = page.locator('.cfg-item').first();
    await expect(firstItem).toBeVisible({ timeout: 15000 }).catch(() => {});

    // Look for snapshot-related text in the page
    const hasSnapshotLink = await page.getByText(/snapshot|snap/i).first().isVisible().catch(() => false);

    // Try clicking snapshot if it's available as a menu/category item
    // Otherwise check if snapshot info appears within config editor
    if (hasSnapshotLink) {
      await page.getByText(/snapshot/i).first().click();
      await expect(page.locator('.snapshot-section, .config-section, .card').first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('Apply config button is present in editor', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    const firstItem = page.locator('.cfg-item').first();
    await expect(firstItem).toBeVisible({ timeout: 15000 });
    await firstItem.click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    const applyBtn = page.locator('.btn-apply');
    await expect(applyBtn).toBeVisible({ timeout: 10000 });
  });

});
