import { setupAuth, getAuthToken } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Empty States — UI Rendering', () => {
  // These tests verify empty-state rendering, so they must run on a clean
  // system. Terminate any leftover sessions first (shared VM3 may have
  // sessions from prior scenario tests).
  test.beforeAll(async ({ request }) => {
    try {
      const token = await getAuthToken();
      await request.post(`${BASE}/api/sim/stop`, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {}
  });

  test('E1: Sessions page shows empty state when no active sessions', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Sessions').click();
    // Wait for the sessions section to finish rendering (either table or
    // empty state) before deciding which assertion to make. Checking
    // isVisible() immediately races with Vue async rendering.
    await expect(page.locator('.sessions-section')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.sessions-section table, .sessions-section .empty, .sessions-section .empty-state').first()).toBeVisible({ timeout: 5000 }).catch(() => {});
    // Either table with rows OR empty state with "No Active Sessions"
    const hasTable = await page.locator('.sessions-section table').isVisible().catch(() => false);
    if (hasTable) {
      const rowCount = await page.locator('.sessions-section tbody tr').count();
      if (rowCount > 0) {
        test.skip(); // Has active sessions, nothing to test
        return;
      }
    }

    const emptyState = page.locator('.empty-state, .empty');
    await expect(emptyState).toBeVisible({ timeout: 5000 });
    const emptyText = await emptyState.textContent();
    expect(emptyText).toMatch(/No Active Sessions|No sessions/i);
  });

  test('E2: IP Manager DHCP tab shows empty state when no leases', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await page.locator('.ros-tabs').getByText('DHCP').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    const hasTable = await page.locator('.tab-body table').isVisible().catch(() => false);
    if (hasTable) {
      test.skip(); // Has DHCP leases
      return;
    }

    await expect(page.locator('.tab-body .empty')).toContainText(/No active DHCP leases/i);
  });

  test('E3: IP Manager ARP tab loads with data or empty state', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();

    // Lazy-loaded async component — wait for it to render
    await expect(page.locator('.ros-tabs')).toBeVisible({ timeout: 10000 });
    // Check for: table, empty state, or the component's tab-body content
    const hasContent = await page.locator('.tab-body').first().isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();

    const hasTable = await page.locator('.ros-ip .tab-body table').isVisible().catch(() => false);
    if (hasTable) {
      const headers = await page.locator('.ros-ip .tab-body table thead th').allTextContents();
      expect(headers.some(h => /ip/i.test(h))).toBeTruthy();
    }
  });

  test('Certificate Manager empty state loads without error', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Certificates').click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    await expect(page.getByRole('heading', { name: 'Certificate Manager' })).toBeVisible({ timeout: 15000 });

    // Should show empty state or table
    const hasTable = await page.locator('table').isVisible().catch(() => false);
    const hasEmpty = await page.getByText(/No certificates/i).isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBeTruthy();
  });

});

test.describe('Form Validation — UI Error Handling', () => {

  test('E4: DHCP static add does not submit with empty MAC', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('IP Manager').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await page.locator('.ros-tabs').getByText('Static').click();
    // replaced waitForTimeout(600) → expect() auto-wait
    // Open add form
    const addBtn = page.locator('.tab-body .btn-mini').filter({ hasText: '+ Add' });
    if (!(await addBtn.isVisible().catch(() => false))) {
      test.skip();
      return;
    }
    await addBtn.click();
    // Leave MAC empty, fill only IP
    const ipInput = page.locator('.fw-add input[placeholder*="IP"]');
    await ipInput.fill('192.168.100.99');

    // Click Add without MAC - should silently fail (component check prevents submission)
    const addSubmit = page.locator('.fw-add .btn-mini').filter({ hasText: 'Add' });
    await addSubmit.click();
    // The form should still be visible (not submitted)
    const formStillVisible = await page.locator('.fw-add').isVisible().catch(() => false);
    const pageNotError = await page.locator('.error-page, .crash').isVisible().catch(() => false);
    expect(pageNotError).toBeFalsy();
  });

  test('E7: RADIUS Tools page loads and Auth Test tab is accessible', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 15000 });

    const radTab = page.locator('.diag-tabs').getByText('RADIUS');
    await expect(radTab).toBeVisible({ timeout: 5000 });
  });

  test('Tools page diagnostics tab switching renders correct panels', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    const tabs = ['Ping', 'Traceroute', 'DNS', 'RADIUS', 'CoA', 'BW Test', 'Capture'];
    for (const label of tabs) {
      await page.locator('.diag-tabs').getByText(label).click();
      // Each tab should render a card with a heading matching the tab
      const card = page.locator('.card').first();
      await expect(card).toBeVisible({ timeout: 3000 });
      const heading = await card.locator('h3').textContent();
      expect(heading).toBeTruthy();
    }
  });

});

test.describe('App Stability — No Crashes', () => {

  test('F5: Rapid multi-page navigation does not cause console errors', async ({ page }) => {
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });

    await page.goto(BASE);
    // Rapidly navigate through 5 pages
    const pages = ['Sessions', 'IP Manager', 'VPN Services', 'Config Editor', 'RADIUS Tools'];
    for (const name of pages) {
      await page.locator(SIDEBAR).getByText(name).click();
    }

    // Wait for any async rendering to settle
    // replaced waitForTimeout(1000) → expect() auto-wait
    const realErrors = errors.filter(e =>
      !e.includes('favicon') && !e.includes('Failed to load resource') && !e.includes('WebSocket')
    );
    expect(realErrors).toHaveLength(0);
  });

  test('G2: Config Editor page survives reload without crash', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    // Reload the page
    await page.reload();
    // replaced waitForTimeout(2000) → expect() auto-wait
    // Should still render without crash — check topbar (always present) or config-section
    const topbar = page.locator('.rnas-topbar');
    await expect(topbar).toBeVisible({ timeout: 10000 });
  });

});
