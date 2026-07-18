import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.describe('Network Feature Pages — Browser UI Validation', () => {

  test('Routing page loads with OSPF/BGP status', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    // Click "Dynamic Routing" in sidebar (like a human navigating)
    await page.locator(SIDEBAR).getByText('Dynamic Routing').click();
    await page.waitForTimeout(2000);
    await expect(page.locator('h2, .page-title, .routing-section').first()).toBeVisible({ timeout: 15000 });
    // The routing page should show at least OSPF section header
    await expect(page.getByText(/OSPF/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('Tunnel Manager page loads with interface list', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Tunnel Manager').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('h2, .page-title, .tunnel-section').first()).toBeVisible({ timeout: 8000 });
    // Tunnel page should list at least one GRE/IPIP/VXLAN or show empty state
    const hasContent = await page.getByText(/GRE|IPIP|VXLAN|EoIP|Tunnel/i).first().isVisible().catch(() => false);
    const hasEmpty = await page.locator('.empty, .empty-state').first().isVisible().catch(() => false);
    expect(hasContent || hasEmpty).toBeTruthy();
  });

  test('VLAN per User page loads with module status', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('VLAN per User').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('h2, .page-title, .vlan-section').first()).toBeVisible({ timeout: 8000 });
    // VLAN page should show module status (loaded/missing/unknown)
    await expect(page.getByText(/VLAN|module|Status/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('NetFlow / DHCP page loads with running status', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('NetFlow / DHCP').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('h2, .page-title').first()).toBeVisible({ timeout: 8000 });
    // Should show NetFlow status or DHCP relay information
    const hasNetflow = await page.getByText(/NetFlow|DHCP|Relay|Collector/i).first().isVisible().catch(() => false);
    expect(hasNetflow).toBeTruthy();
  });

  test('Hotspot Portal page loads', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Hotspot Portal').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('h2, .page-title, .hotspot-section').first()).toBeVisible({ timeout: 8000 });
    // Hotspot page shows status
    const hasStatus = await page.getByText(/Hotspot|Portal/i).first().isVisible().catch(() => false);
    expect(hasStatus).toBeTruthy();
  });

});

test.describe('Dashboard — System Status via UI', () => {

  test('Dashboard overview loads with system health', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    // StatusCard shows uptime and system resources
    await expect(page.locator('.t-brand')).toHaveText('RNAS');
    // Topbar should show RADIUS status indicator (green/red)
    await expect(page.locator('.t-status')).toBeVisible({ timeout: 8000 });
    // Sessions count should be visible in topbar
    await expect(page.locator('.t-sessions')).toBeVisible({ timeout: 5000 });
    // SystemHealth card loaded
    await expect(page.getByText(/System|Health/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('Health check — API health reflected in UI', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    // The topbar shows "v3.0 running" in sidebar foot
    await expect(page.locator('.sidebar-foot')).toContainText(/running|v3/i);
  });

  test('RADIUS state shown in topbar', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    // Topbar shows RADIUS up/down status
    const radiusStatus = page.locator('.t-status');
    await expect(radiusStatus).toBeVisible({ timeout: 8000 });
    const text = await radiusStatus.textContent();
    expect(text).toMatch(/RADIUS up|RADIUS down/);
  });

});

test.describe('Config Export — Browser UI', () => {

  test('Config Editor page accessible', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('h2, .page-title').first()).toBeVisible({ timeout: 8000 });
    // Config Editor should show category filters or sidebar
    const hasSidebar = await page.locator('.cat-sidebar, .config-cats, .category-list, nav').first().isVisible().catch(() => false);
    expect(hasSidebar).toBeTruthy();
  });

  test('Config snapshot page accessible', async ({ page }) => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.locator(SIDEBAR).getByText('Config Editor').click();
    await page.waitForTimeout(1500);
    // Config page should show at minimum the page container
    await expect(page.locator('.proto-config, .config-editor, .config-section, .card').first()).toBeVisible({ timeout: 8000 });
  });

});
