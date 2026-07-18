import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';
const SIDEBAR = 'nav.rnas-sidebar';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Diagnostic Tools — Ping/Trace/DNS/RADIUS', () => {

  test('C1: Ping tab loads with default host and button', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 20000 });

    const pingCard = page.locator('.card').first();
    await expect(pingCard).toBeVisible({ timeout: 8000 });
    await expect(pingCard.locator('h3')).toHaveText('Ping');

    // Default host input should have a value
    const hostInput = pingCard.locator('input').first();
    await expect(hostInput).toBeVisible({ timeout: 3000 });
    const hostVal = await hostInput.inputValue();
    expect(hostVal.length).toBeGreaterThan(0);

    // Ping button exists
    const pingBtn = pingCard.locator('button').filter({ hasText: 'Ping' });
    await expect(pingBtn).toBeVisible({ timeout: 3000 });
  });

  test('C1b: Execute ping and see output', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 15000 });

    const pingCard = page.locator('.card').first();
    await expect(pingCard.locator('h3')).toHaveText('Ping');

    // Type a reachable host
    const hostInput = pingCard.locator('input').first();
    await expect(hostInput).toBeVisible({ timeout: 5000 });
    await hostInput.fill('127.0.0.1');
    // Click Ping button
    await pingCard.locator('button').filter({ hasText: 'Ping' }).click();
    await page.waitForTimeout(3000);

    // Output should appear
    const output = pingCard.locator('.output');
    await expect(output).toBeVisible({ timeout: 10000 });
    const outputText = await output.textContent();
    expect(outputText.length).toBeGreaterThan(0);
  });

  test('C2: Traceroute tab renders and executes', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    await page.locator('.diag-tabs').getByText('Traceroute').click();
    const traceCard = page.locator('.card').first();
    await expect(traceCard.locator('h3')).toHaveText('Traceroute');

    const hostInput = traceCard.locator('input').first();
    await hostInput.fill('127.0.0.1');
    await traceCard.locator('button').filter({ hasText: 'Trace' }).click();
    await page.waitForTimeout(3000);

    const output = traceCard.locator('.output');
    await expect(output).toBeVisible({ timeout: 10000 });
  });

  test('C3: DNS Lookup tab executes query', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    await page.locator('.diag-tabs').getByText('DNS').click();
    const dnsCard = page.locator('.card').first();
    await expect(dnsCard.locator('h3')).toHaveText('DNS Lookup');

    // Default host should be google.com or similar
    const hostInput = dnsCard.locator('input').first();
    await hostInput.fill('localhost');
    await dnsCard.locator('button').filter({ hasText: 'Lookup' }).click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    const output = dnsCard.locator('.output');
    await expect(output).toBeVisible({ timeout: 10000 });
  });

  test('C4: RADIUS auth test executes with default credentials', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    await page.locator('.diag-tabs').getByText('RADIUS').click();
    const radCard = page.locator('.card').first();
    await expect(radCard.locator('h3')).toHaveText('RADIUS Test');

    // Defaults should be testuser/testpass
    const userInput = radCard.locator('input').first();
    const passInput = radCard.locator('input[type="password"]').first();
    await expect(userInput).toBeVisible({ timeout: 3000 });
    const userVal = await userInput.inputValue();
    expect(userVal.length).toBeGreaterThan(0);

    // Execute auth test
    await radCard.locator('button').filter({ hasText: 'Auth Test' }).click();
    // replaced waitForTimeout(2000) → expect() auto-wait
    const output = radCard.locator('.output');
    await expect(output).toBeVisible({ timeout: 10000 });
    const outputText = await output.textContent();
    expect(outputText.length).toBeGreaterThan(0);
  });

  test('C5: CoA tab renders with input fields', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    await page.locator('.diag-tabs').getByText('CoA').click();
    const coaCard = page.locator('.card').first();
    await expect(coaCard.locator('h3')).toHaveText('CoA Disconnect');

    const userInput = coaCard.locator('input').first();
    await expect(userInput).toBeVisible({ timeout: 3000 });

    const coaBtn = coaCard.locator('button').filter({ hasText: 'Disconnect' });
    await expect(coaBtn).toBeVisible({ timeout: 3000 });
  });

  test('C6: Capture tab renders with start/stop/status', async ({ page }) => {
    await page.goto(BASE);
    await page.locator(SIDEBAR).getByText('RADIUS Tools').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.diag-tabs')).toBeVisible({ timeout: 10000 });

    await page.locator('.diag-tabs').getByText('Capture').click();
    const capCard = page.locator('.card').first();
    await expect(capCard.locator('h3')).toHaveText('Packet Capture');

    // Start, Stop, Status buttons should exist
    await expect(capCard.locator('button').filter({ hasText: 'Start' })).toBeVisible({ timeout: 3000 });
    await expect(capCard.locator('button').filter({ hasText: 'Stop' })).toBeVisible({ timeout: 3000 });
    await expect(capCard.locator('button').filter({ hasText: 'Status' })).toBeVisible({ timeout: 3000 });

    // Check Status should work without errors
    await capCard.locator('button').filter({ hasText: 'Status' }).click();
    // replaced waitForTimeout(1000) → expect() auto-wait
    // Output div uses v-if="capMsg" — only appears after API responds
    const msg = capCard.locator('.output');
    await expect(msg).toBeVisible({ timeout: 10000 });
  });

});
