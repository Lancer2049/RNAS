import { setupAuth } from './auth-helper';
import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';

test.beforeEach(async ({ page }) => {
  await setupAuth(page);
});


test.describe('Scenario Runner — 预定义测试场景', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE);
    // 通过左侧菜单栏导航到 Scenario 页面
    await page.locator('.rnas-sidebar').getByText('Scenario').click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    // 验证页面标题
    await expect(page.locator('.sim-section h2')).toHaveText('Scenario Runner');
  });

  test('S1: Scenario 页面加载并显示所有 10 个场景卡片', async ({ page }) => {
    const cards = page.locator('.scenario-card');
    await expect(cards).toHaveCount(10);

    const names = await page.locator('.scenario-card h3').allTextContents();
    expect(names).toContain('All VPNs');
    expect(names).toContain('Enterprise VPN');
    expect(names).toContain('Full Load Test');
    expect(names).toContain('Home Broadband');
    expect(names).toContain('Hotel WiFi');
    expect(names).toContain('IPTV Multicast');
    expect(names).toContain('L2TP VPN');
    expect(names).toContain('PPPoE Only');
    expect(names).toContain('PPTP Legacy');
    expect(names).toContain('SSTP Only');
  });

  test('S2: Home Broadband 场景 — 点击 Run 验证 UI 反馈 "X/Y applied"', async ({ page }) => {
    // 找到 Home Broadband 场景卡片
    const hbCard = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'Home Broadband' }) });
    await expect(hbCard).toBeVisible();

    // 点击 Run 按钮
    const runBtn = hbCard.locator('button');
    await expect(runBtn).toBeVisible();
    await runBtn.click();

    // 等待运行结果
    await page.waitForTimeout(3000);

    // 验证 UI 反馈 — 结果标签出现
    const result = hbCard.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    // 获取结果文字并验证
    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');

    console.log(`[Home Broadband] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S3: PPPoE Only 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const pppoeCard = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'PPPoE Only' }) });
    await expect(pppoeCard).toBeVisible();

    await pppoeCard.locator('button').click();
    await page.waitForTimeout(3000);

    const result = pppoeCard.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[PPPoE Only] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S4: L2TP VPN 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'L2TP VPN' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[L2TP VPN] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S5: SSTP Only 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'SSTP Only' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[SSTP Only] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S6: PPTP Legacy 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'PPTP Legacy' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[PPTP Legacy] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S7: Enterprise VPN 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'Enterprise VPN' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[Enterprise VPN] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S8: IPTV Multicast 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'IPTV Multicast' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[IPTV Multicast] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S9: Hotel WiFi 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'Hotel WiFi' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[Hotel WiFi] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S10: Full Load Test 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'Full Load Test' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[Full Load Test] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S11: All VPNs 场景 — 运行并验证 UI 反馈', async ({ page }) => {
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'All VPNs' }) });
    await expect(card).toBeVisible();

    await card.locator('button').click();
    await page.waitForTimeout(3000);

    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    const resultText = await result.textContent();
    const resultClass = await result.getAttribute('class');
    console.log(`[All VPNs] Result: "${resultText}" class="${resultClass}"`);
    expect(resultText).toMatch(/\d+\/\d+ applied|Failed/);
  });

  test('S12: 场景运行后按钮恢复为 "▶ Run" 状态', async ({ page }) => {
    // 运行一个场景，验证完成后按钮恢复可用
    const card = page.locator('.scenario-card', { has: page.locator('h3', { hasText: 'PPPoE Only' }) });
    const btn = card.locator('button');

    await expect(btn).toBeVisible();
    await expect(btn).toBeEnabled();
    await btn.click();

    await page.waitForTimeout(3000);
    const result = card.locator('.result');
    await expect(result).toBeVisible({ timeout: 10000 });

    // 按钮恢复为可用的 "▶ Run"
    await expect(btn).toBeEnabled({ timeout: 10000 });
    await expect(btn).toHaveText('▶ Run');
  });

  test('S13: 控制台无错误 — Scenario 页面导航', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', err => errors.push(err.message));

    // 重新加载页面确保干净状态
    await page.goto(BASE);
    // 通过侧边栏导航到 Scenario
    await page.locator('.rnas-sidebar a:has(.si)').filter({ hasText: 'Scenario' }).click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.sim-section h2')).toHaveText('Scenario Runner');

    // 导航到其他页面再回来
    await page.locator('.rnas-sidebar a:has(.si)').filter({ hasText: 'Sessions' }).click();
    // replaced waitForTimeout(800) → expect() auto-wait
    await page.locator('.rnas-sidebar a:has(.si)').filter({ hasText: 'Scenario' }).click();
    // replaced waitForTimeout(1500) → expect() auto-wait
    await expect(page.locator('.sim-section h2')).toHaveText('Scenario Runner');

    expect(errors).toHaveLength(0);
  });
});
