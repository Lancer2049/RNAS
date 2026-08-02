import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Notification Settings — Alert Channels (C5)', () => {

  test('C5-1: Page loads with channel form and action buttons', async ({ page }) => {
    await page.route('**/api/system/notifications', route => route.fulfill({
      json: { enabled: false, telegram_bot_token: '', telegram_chat_id: '', webhook_url: '' },
    }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Notifications').click();
    await expect(page.locator('.notif-page h2')).toContainText('Notification Settings', { timeout: 5000 });
    await expect(page.locator('.nf-enabled')).toBeVisible();
    await expect(page.locator('.field:has-text("Bot Token") input')).toBeVisible();
    await expect(page.locator('.field:has-text("Chat ID") input')).toBeVisible();
    await expect(page.locator('.field:has-text("Webhook") input')).toBeVisible();
    await expect(page.locator('.btn-save')).toBeVisible();
    await expect(page.locator('.btn-test')).toBeVisible();
  });

  test('C5-2: Save persists config and shows success feedback', async ({ page }) => {
    let savedBody = null;
    await page.route('**/api/system/notifications', async route => {
      if (route.request().method() === 'POST') {
        savedBody = route.request().postDataJSON();
        await route.fulfill({ json: { status: 'saved' } });
      } else {
        await route.fulfill({ json: { enabled: false, telegram_bot_token: '', telegram_chat_id: '', webhook_url: '' } });
      }
    });
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Notifications').click();
    await expect(page.locator('.notif-page h2')).toBeVisible({ timeout: 5000 });

    await page.locator('.nf-enabled').check();
    await page.locator('.field:has-text("Bot Token") input').fill('123456:TESTTOKEN');
    await page.locator('.field:has-text("Chat ID") input').fill('-100123456');
    await page.locator('.field:has-text("Webhook") input').fill('https://example.com/hook');
    await page.locator('.btn-save').click();

    await expect(page.locator('.nf-msg')).toContainText('saved', { timeout: 5000 });
    await expect(page.locator('.nf-msg')).toHaveClass(/ok/);
    expect(savedBody).toEqual({
      enabled: true,
      telegram_bot_token: '123456:TESTTOKEN',
      telegram_chat_id: '-100123456',
      webhook_url: 'https://example.com/hook',
    });
  });

  test('C5-3: Test button reports per-channel delivery results', async ({ page }) => {
    await page.route('**/api/system/notifications', route => route.fulfill({
      json: { enabled: false, telegram_bot_token: '', telegram_chat_id: '', webhook_url: '' },
    }));
    await page.route('**/api/system/notifications/test', route => route.fulfill({
      json: { results: [{ channel: 'telegram', ok: true }, { channel: 'webhook', ok: false }] },
    }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Notifications').click();
    await expect(page.locator('.notif-page h2')).toBeVisible({ timeout: 5000 });

    await page.locator('.field:has-text("Bot Token") input').fill('123456:TESTTOKEN');
    await page.locator('.field:has-text("Chat ID") input').fill('-100123456');
    await page.locator('.btn-test').click();

    await expect(page.locator('.nf-result').first()).toContainText('telegram: delivered', { timeout: 5000 });
    await expect(page.locator('.nf-result').nth(1)).toContainText('webhook: failed');
  });

  test('C5-4: Existing config is pre-filled on load', async ({ page }) => {
    await page.route('**/api/system/notifications', route => route.fulfill({
      json: { enabled: true, telegram_bot_token: '111:PRESET', telegram_chat_id: '-100999', webhook_url: 'https://preset.example/hook' },
    }));
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Notifications').click();
    await expect(page.locator('.field:has-text("Bot Token") input')).toHaveValue('111:PRESET', { timeout: 5000 });
    await expect(page.locator('.field:has-text("Chat ID") input')).toHaveValue('-100999');
    await expect(page.locator('.field:has-text("Webhook") input')).toHaveValue('https://preset.example/hook');
    await expect(page.locator('.nf-enabled')).toBeChecked();
  });

});
