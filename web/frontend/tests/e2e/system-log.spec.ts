import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});

test.describe('System Log — Keyword Search (B1)', () => {

  test('B1-L1: System Log page loads with search box and log content', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    await expect(page.locator('.log-toolbar')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('.log-toolbar .kw')).toBeVisible();
    await expect(page.locator('.log-content')).toBeVisible({ timeout: 5000 });

    const meta = page.locator('.log-meta');
    await expect(meta).toBeVisible({ timeout: 5000 });
    const metaText = await meta.textContent();
    expect(metaText).toMatch(/showing \d+ \/ \d+ lines/);
  });

  test('B1-L2: Typing a keyword filters log lines to matches only', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    await expect(page.locator('.log-content')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('.log-meta')).toBeVisible({ timeout: 5000 });

    // Read all currently-shown lines, grab the first non-empty one
    await page.waitForTimeout(800);
    const beforeText = await page.locator('.log-content').textContent();
    const totalBefore = beforeText ? beforeText.split('\n').filter(l => l.trim()).length : 0;
    expect(totalBefore).toBeGreaterThan(0);

    // Search for a term that must exist in journalctl output ("systemd" or "journal")
    const kw = 'systemd';
    await page.locator('.log-toolbar .kw').fill(kw);

    // Every remaining visible line must contain the keyword
    await expect(page.locator('.log-meta')).toContainText('lines', { timeout: 5000 });
    const filtered = await page.locator('.log-content').textContent();
    const lines = filtered ? filtered.split('\n').filter(l => l.trim()) : [];
    expect(lines.length).toBeLessThanOrEqual(totalBefore);
    for (const line of lines) {
      expect(line.toLowerCase()).toContain(kw);
    }
  });

  test('B1-L3: Non-matching keyword yields zero visible log lines', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    await expect(page.locator('.log-content')).toBeVisible({ timeout: 8000 });

    await page.locator('.log-toolbar .kw').fill('zzzz-no-such-term-xyzzy');
    await expect(page.locator('.log-meta')).toContainText('0 /', { timeout: 5000 });

    const content = await page.locator('.log-content').textContent();
    const visibleLines = content ? content.split('\n').filter(l => l.trim()) : [];
    expect(visibleLines.length).toBe(0);
  });

  test('B1-L4: Clearing the search restores the full log', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('System Log').click();
    await expect(page.locator('.log-content')).toBeVisible({ timeout: 8000 });
    await expect(page.locator('.log-meta')).toBeVisible({ timeout: 5000 });

    await page.waitForTimeout(800);
    const kw = page.locator('.log-toolbar .kw');
    await kw.fill('systemd');
    await expect(page.locator('.log-meta')).toContainText(' / ', { timeout: 5000 });
    const filteredText = await page.locator('.log-content').textContent();
    const filteredLines = filteredText ? filteredText.split('\n').filter(l => l.trim()).length : 0;

    await kw.fill('');
    await expect(page.locator('.log-meta')).toContainText(/showing \d+ \/ \d+ lines/, { timeout: 5000 });
    const restoredText = await page.locator('.log-content').textContent();
    const restoredLines = restoredText ? restoredText.split('\n').filter(l => l.trim()).length : 0;

    expect(restoredLines).toBeGreaterThanOrEqual(filteredLines);
  });

});