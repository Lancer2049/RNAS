import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('B4 — Config Snapshots Management Page', () => {

  async function openSnapshots(page) {
    await page.goto(BASE);
    await page.waitForTimeout(800);
    await page.locator('.rnas-sidebar').getByText('Config Snapshots').click();
    await page.waitForTimeout(600);
    await expect(page.locator('h2', { hasText: 'Config Snapshots' })).toBeVisible({ timeout: 5000 });
  }

  test('B4-1: Snapshots page lists existing snapshots', async ({ page }) => {
    await openSnapshots(page);
    // Table header present
    await expect(page.locator('th', { hasText: 'Name' })).toBeVisible();
    await expect(page.locator('th', { hasText: 'Files' })).toBeVisible();
    // Existing pre-import snapshots should be listed (from prior import flows)
    const rows = page.locator('tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 5000 });
    const firstRow = await rows.first().textContent();
    expect(firstRow ?? '').toContain('pre-import');
  });

  test('B4-2: Create a named snapshot shows feedback and appears in list', async ({ page }) => {
    await openSnapshots(page);
    const nameInput = page.locator('.name-input');
    await nameInput.fill('e2e-snap-check');
    await page.locator('.snap-actions .btn-accent').click();
    // Success feedback with file count
    await expect(page.locator('.msg')).toContainText('Snapshot created', { timeout: 8000 });
    // New row appears
    await expect(page.locator('tbody tr', { hasText: 'e2e-snap-check' })).toBeVisible();
    const rowText = await page.locator('tbody tr', { hasText: 'e2e-snap-check' }).textContent();
    expect(/\b\d+\b/.test(rowText ?? '')).toBeTruthy();
  });

  test('B4-3: Diff panel opens and shows live-config differences', async ({ page }) => {
    await openSnapshots(page);
    // Pick the first snapshot row and click Diff
    const firstRow = page.locator('tbody tr').first();
    const rowName = await firstRow.locator('td').first().textContent();
    await firstRow.locator('button', { hasText: 'Diff' }).click();
    // Diff panel appears with the snapshot name
    await expect(page.locator('.diff-panel')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('.diff-head .mono')).toHaveText(rowName ?? '');
    // Status label shows either identical or differs
    const statusText = await page.locator('.diff-status').textContent();
    expect(statusText === 'identical' || statusText === 'differs from live config').toBeTruthy();
    // Close button collapses the panel
    await page.locator('.diff-head button', { hasText: '✕' }).click();
    await expect(page.locator('.diff-panel')).toBeHidden();
  });

  test('B4-4: Delete snapshot removes it from the list', async ({ page }) => {
    // Ensure a deletable snapshot exists first
    await openSnapshots(page);
    const nameInput = page.locator('.name-input');
    await nameInput.fill('e2e-snap-del');
    await page.locator('.snap-actions .btn-accent').click();
    await expect(page.locator('.msg')).toContainText('Snapshot created', { timeout: 8000 });

    // Accept the confirm dialog, then click Delete on that row
    page.on('dialog', d => d.accept());
    const delRow = page.locator('tbody tr', { hasText: 'e2e-snap-del' });
    await delRow.locator('button.btn-del').click();
    await expect(page.locator('.msg')).toContainText('Deleted', { timeout: 8000 });
    await expect(page.locator('tbody tr', { hasText: 'e2e-snap-del' })).toHaveCount(0);
  });
});
