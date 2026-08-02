import { setupAuth, getAuthToken } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('Config Import/Export (P3-06)', () => {

  test('I1: Config Editor shows Export and Import buttons', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    await expect(page.locator('.config-section')).toBeVisible({ timeout: 20000 });

    const exportBtn = page.locator('.btn-export');
    const importBtn = page.locator('.btn-import');
    await expect(exportBtn).toBeVisible();
    await expect(importBtn).toBeVisible();
  });

  test('I2: Export downloads a tar.gz and shows "Exported" feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    await expect(page.locator('.config-section')).toBeVisible({ timeout: 20000 });

    const downloadPromise = page.waitForEvent('download', { timeout: 20000 });
    await page.locator('.btn-export').click();
    const download = await downloadPromise;
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/rnas-config.*\.tar\.gz/);

    await expect(page.locator('.msg.success')).toContainText('Exported', { timeout: 10000 });
  });

  test('I3: Import rejects a non-tar.gz upload with error feedback', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    await expect(page.locator('.config-section')).toBeVisible({ timeout: 20000 });

    // Upload an invalid payload directly through the hidden file input
    const fileInput = page.locator('input[type=file]');
    await fileInput.setInputFiles({
      name: 'bad.bin',
      mimeType: 'application/octet-stream',
      buffer: Buffer.from('this is not a tarball'),
    });

    await expect(page.locator('.msg.error')).toBeVisible({ timeout: 15000 });
  });

  test('I4: Export API returns valid tar.gz with config files', async ({ page }) => {
    const token = await getAuthToken();
    const resp = await fetch(`${BASE}/api/v1/config/export`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(resp.status).toBe(200);
    expect(resp.headers.get('content-type')).toContain('application/gzip');
    const buf = Buffer.from(await resp.arrayBuffer());
    expect(buf.length).toBeGreaterThan(1000);
  });

});
