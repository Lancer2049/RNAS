import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.describe('PPPoE Config — Browser UI End-to-End', () => {

  test('Configure PPPoE via web form → Save → Apply → verify UI feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await expect(page.locator('.rnas-topbar .t-brand')).toHaveText('RNAS', { timeout: 10000 });

    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await page.waitForTimeout(1500);

    await expect(page.getByRole('heading', { name: 'Protocol Configuration' })).toBeVisible({ timeout: 10000 });

    await expect(page.locator('.proto-tabs button.active')).toContainText('PPPoE');

    const toggleCheckbox = page.locator('.toggle input[type="checkbox"]');
    await toggleCheckbox.check();
    await page.waitForTimeout(200);

    const interfaceSelect = page.locator('.field-row').filter({ hasText: 'Interface' }).locator('select.field-input');
    await interfaceSelect.selectOption('ens33');
    await page.waitForTimeout(100);

    const acNameInput = page.locator('.field-row').filter({ hasText: 'AC Name' }).locator('input.field-input');
    await acNameInput.fill('RNAS-PPPoE');
    await page.waitForTimeout(100);

    const serviceNameInput = page.locator('.field-row').filter({ hasText: 'Service Name' }).locator('input.field-input');
    await serviceNameInput.fill('isp-pppoe');
    await page.waitForTimeout(100);

    const mtuInput = page.locator('.field-row').filter({ hasText: 'MTU' }).locator('input.field-input');
    await mtuInput.fill('1492');
    await page.waitForTimeout(100);

    const mruInput = page.locator('.field-row').filter({ hasText: 'MRU' }).locator('input.field-input');
    await mruInput.fill('1492');
    await page.waitForTimeout(100);

    await page.locator('.btn-primary').filter({ hasText: 'Save' }).click();
    await page.waitForTimeout(1000);

    const msgEl = page.locator('.msg.ok');
    await expect(msgEl).toHaveText('Saved', { timeout: 5000 });

    const applyBtn = page.locator('.btn-primary').filter({ hasText: 'Apply & Restart' });
    if (await applyBtn.isVisible().catch(() => false)) {
      await applyBtn.click();
      await page.waitForTimeout(1000);
    }
    await page.waitForTimeout(500);
  });

  test('Disable PPPoE via web form and verify', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Access Protocols').click();
    await page.waitForTimeout(1500);
    await expect(page.getByRole('heading', { name: 'Protocol Configuration' })).toBeVisible({ timeout: 10000 });

    const toggleCheckbox = page.locator('.toggle input[type="checkbox"]');
    if (await toggleCheckbox.isChecked()) {
      await toggleCheckbox.uncheck();
      await page.waitForTimeout(200);
    }

    await page.locator('.btn-primary').filter({ hasText: 'Save' }).click();
    await page.waitForTimeout(500);

    const applyBtn = page.locator('.btn-primary').filter({ hasText: 'Apply & Restart' });
    if (await applyBtn.isVisible().catch(() => false)) {
      await applyBtn.click();
      await page.waitForTimeout(1000);
    }

    const statusDot = page.locator('.proto-tabs button.active .status-dot');
    const dotClass = await statusDot.getAttribute('class').catch(() => '');
    expect(dotClass.includes('off')).toBeTruthy();
  });

});
