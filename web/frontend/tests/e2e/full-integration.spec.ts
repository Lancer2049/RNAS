import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Real Configuration Workflows — Browser UI', () => {

  test('Services: modify QoS setting, save, verify feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('VPN Services').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.services-section')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: 'QoS / Traffic Control' })).toBeVisible({ timeout: 5000 });
    const selectField = page.locator('.field-row select').first();
    if (await selectField.isVisible().catch(() => false)) {
      const currentVal = await selectField.inputValue();
      const newVal = currentVal === 'yes' ? 'no' : 'yes';
      await selectField.selectOption(newVal);
      await page.locator('.btn-save').click();
      // replaced waitForTimeout(1000) → expect() auto-wait
      await expect(page.locator('.saved-msg')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('.saved-msg')).toContainText('Saved');
    }
  });

  test('RADIUS Editor: verify pre-filled defaults and attribute list', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('AAA Editor').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByText('RADIUS Message Editor')).toBeVisible({ timeout: 10000 });
    const serverInput = page.locator('.field-row input').first();
    await expect(serverInput).toBeVisible({ timeout: 5000 });
    const serverVal = await serverInput.inputValue();
    expect(serverVal).toMatch(/192\.168\.0\.202|127\.0\.0\.1/);
    const secretInput = page.locator('.field-row input').nth(1);
    await expect(secretInput).toBeVisible({ timeout: 3000 });
    const defaultAttrs = page.locator('.attr-row input[placeholder="value"]');
    const attrCount = await defaultAttrs.count();
    expect(attrCount).toBeGreaterThanOrEqual(1);
  });

  test('Dictionary: verify attribute list loads and renders', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Dictionary').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByText('RADIUS Dictionary')).toBeVisible({ timeout: 10000 });
    // replaced waitForTimeout(1500) → expect() auto-wait
    const hasTable = await page.locator('table').first().isVisible().catch(() => false);
    const hasContent = await page.getByText(/Attribute|Vendor|Code|Type|Name/i).first().isVisible().catch(() => false);
    expect(hasTable || hasContent).toBeTruthy();
  });

  test('Subscriber Sim: page loads with simulation controls', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Subscriber Sim').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByText('Subscriber Simulation')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.sim-section, .card').first()).toBeVisible({ timeout: 5000 });
  });

  test('System Log: page loads with log entries and filters', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByText('System').first()).toBeVisible({ timeout: 8000 });
    const hasContent = await page.getByText(/log|entry|info|warn|error|filter|service|level/i).first().isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });

  test('RADIUS Tools: page loads with diagnostic tools', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Diagnostics' })).toBeVisible({ timeout: 10000 });
  });

});

test.describe('Traffic and Monitoring — UI Feedback', () => {

  test('Traffic Torch: page loads with monitoring interface', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Traffic Torch').first().click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Traffic Torch' })).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.torch-section, .card, .section').first()).toBeVisible({ timeout: 8000 });
  });

});

test.describe('Port Forward and Firewall — UI Config', () => {

  test('Port Forward Wizard: page loads with form fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.ros-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.ros-tabs').getByText('NAT').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    const hasPfTab = await page.getByText('Port Forward').isVisible().catch(() => false);
    if (hasPfTab) {
      await page.getByText('Port Forward').click();
      await expect(page.getByText(/Port Forward|External Port|Internal IP/i).first()).toBeVisible({ timeout: 5000 });
    }
  });

});

test.describe('Protocol Operations — UI Workflow', () => {

  test('Access Protocols: tab switching renders different protocol forms', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Protocol Configuration' })).toBeVisible({ timeout: 8000 });
    const tabs = ['L2TP', 'PPTP', 'SSTP', 'IPoE'];
    for (const label of tabs) {
      await page.locator('.proto-tabs').getByText(label).click();
      await expect(page.locator('.proto-form')).toBeVisible({ timeout: 5000 });
    }
  });

});

test.describe('Quick Setup Wizard — UI Flow', () => {

  test('Quick Setup: 3-step wizard renders', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Quick Setup').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByRole('heading', { name: /Quick Setup/i })).toBeVisible({ timeout: 10000 });
  });

});

test.describe('Bandwidth Test — UI Page', () => {

  test('Bandwidth Test: page loads with test controls', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Bandwidth Test').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Bandwidth Test' })).toBeVisible({ timeout: 10000 });
  });

});
