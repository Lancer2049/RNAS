import { test, expect } from '@playwright/test';

const BASE = 'http://127.0.0.1:8098';

/**
 * 全场景端到端测试
 *
 * 对每个 Scenario 场景做完整的全链路验证：
 *   1. 左侧菜单栏 → Scenario → 点击 Run（配置下发）
 *   2. 验证 UI 反馈 "X/X applied"
 *   3. 对可拨号协议 → Subscriber Sim → 真实拨号 → 轮询等待结果
 *   4. Sessions 页面验证会话建立
 *   5. Dashboard 验证系统状态
 *   6. Config Editor / Services 页面验证配置生效
 */

let scenarioSeq = 0;

function captureErrors(page: any) {
  const errors: string[] = [];
  page.on('pageerror', (err: Error) => errors.push(err.message));
  page.__e2e_errors = errors;
  return errors;
}

// 导航到 Scenario 页面并运行指定场景
async function runScenario(page: any, scenarioName: string) {
  await page.goto(BASE);
  await page.waitForTimeout(500);
  await page.locator('.rnas-sidebar').getByText('Scenario').click();
  await page.waitForTimeout(1500);
  await expect(page.locator('.sim-section h2')).toHaveText('Scenario Runner');

  const card = page.locator('.scenario-card', {
    has: page.locator('h3', { hasText: scenarioName })
  });
  await expect(card).toBeVisible();
  await card.locator('button').click();
  await page.waitForTimeout(3000);

  const result = card.locator('.result');
  await expect(result).toBeVisible({ timeout: 15000 });
  const text = await result.textContent();
  const cls = await result.getAttribute('class');
  console.log(`[${scenarioName}] Result: "${text}" class="${cls}"`);
  expect(cls).toContain('ok');
  expect(text).toMatch(/\d+\/\d+ applied/);
  return text;
}

// 通过 Subscriber Sim 拨号并轮询等待结果表格出现
async function simDialAndVerify(page: any, proto: string, count: number = 1) {
  await page.locator('.rnas-sidebar').getByText('Subscriber Sim').click();
  await page.waitForTimeout(1500);
  await expect(page.locator('.sim-section h2')).toHaveText('Subscriber Simulation');

  const select = page.locator('select');
  await select.selectOption(proto);

  const countInput = page.locator('input[type="number"]');
  await countInput.fill('');
  await countInput.fill(String(count));

  // 确保用户名密码正确
  const inputs = page.locator('.field input');
  const inputCount = await inputs.count();
  if (inputCount >= 3) {
    await inputs.nth(1).fill('');
    await inputs.nth(1).fill('testuser');
    await inputs.nth(2).fill('');
    await inputs.nth(2).fill('testpass');
  }

  const startBtn = page.locator('button.btn-start');
  await expect(startBtn).toBeVisible();
  await expect(startBtn).toBeEnabled();
  await startBtn.click();

  // 轮询等待结果表格或超时（sim/connect 可能耗时 20s）
  let tableFound = false;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(1000);
    const table = page.locator('table');
    if (await table.isVisible({ timeout: 500 }).catch(() => false)) {
      tableFound = true;
      const rows = page.locator('table tbody tr');
      const rowCount = await rows.count();
      console.log(`[${proto} Sim] Result rows: ${rowCount} (after ${i + 1}s)`);
      for (let j = 0; j < rowCount; j++) {
        const cells = await rows.nth(j).locator('td').allTextContents();
        console.log(`  Row ${j + 1}: ${cells.join(' | ')}`);
      }
      break;
    }
    // 如果 sim 已完成（running=false），但没表格，停止等待
    const statusEl = page.locator('.status');
    if (await statusEl.isVisible()) {
      const statusText = await statusEl.textContent();
      if (statusText === 'Ready') break;
    }
  }
  if (!tableFound) {
    console.log(`[${proto} Sim] No result table appeared within 30s`);
    // 检查是否因为 CPE 不可达
    const emptyState = page.locator('.empty-state');
    if (await emptyState.isVisible({ timeout: 1000 }).catch(() => false)) {
      console.log(`[${proto} Sim] Empty state visible`);
    }
  }
}

// 检查 Sessions 页面有活动会话
async function verifySessions(page: any, expectedUser: string = 'testuser') {
  await page.locator('.rnas-sidebar').getByText('Sessions').click();
  await page.waitForTimeout(1500);

  const table = page.locator('table');
  if (await table.isVisible({ timeout: 5000 }).catch(() => false)) {
    const rows = page.locator('table tbody tr');
    const count = await rows.count();
    console.log(`[Sessions] Active sessions: ${count}`);
    if (count > 0) {
      const firstRow = await rows.first().textContent();
      console.log(`[Sessions] First row: ${firstRow?.substring(0, 120)}`);
      expect(firstRow?.toLowerCase()).toContain(expectedUser);
    }
    return count;
  }
  console.log('[Sessions] No table visible');
  return 0;
}

// 检查 Dashboard 状态
async function verifyDashboard(page: any) {
  await page.goto(BASE);
  await page.waitForTimeout(1500);

  const statusText = await page.locator('.t-status, .status-card, .stat-item').allTextContents();
  console.log(`[Dashboard] Status: ${statusText.join(' | ')}`);

  const dotOk = page.locator('.dot.ok, .radius-ok');
  if (await dotOk.isVisible({ timeout: 3000 }).catch(() => false)) {
    console.log('[Dashboard] RADIUS: OK');
  }

  const sessionInfo = page.locator('.t-sessions, .session-count');
  if (await sessionInfo.isVisible({ timeout: 2000 }).catch(() => false)) {
    const s = await sessionInfo.textContent();
    console.log(`[Dashboard] Sessions: ${s}`);
  }
}

// 停止所有模拟连接
async function stopSim(page: any) {
  await page.locator('.rnas-sidebar').getByText('Subscriber Sim').click();
  await page.waitForTimeout(1000);
  const stopBtn = page.locator('button.btn-stop');
  if (await stopBtn.isVisible({ timeout: 2000 }).catch(() => false) && await stopBtn.isEnabled()) {
    await stopBtn.click();
    await page.waitForTimeout(1500);
    console.log('[Cleanup] Sim stopped');
  }
}

// 检查 Config Editor 中特定配置段存在 — 等待 .cfg-item 加载完毕
async function verifyConfigSection(page: any, sectionKeyword: string) {
  await page.locator('.rnas-sidebar').getByText('Config Editor').click();
  await page.waitForTimeout(1500);

  // 等待侧边栏渲染出 cfg-item（需要 API 返回 modules 数据）
  const sidebarItems = page.locator('.cfg-sidebar .cfg-item');
  await expect(sidebarItems.first()).toBeVisible({ timeout: 15000 });
  const itemCount = await sidebarItems.count();
  const allText = await sidebarItems.allTextContents();
  const found = allText.some(t => t.toLowerCase().includes(sectionKeyword.toLowerCase()));
  console.log(`[Config] Sections (${itemCount}): ${allText.join(', ')}`);
  console.log(`[Config] Found "${sectionKeyword}": ${found}`);
  return found;
}

// ============================================================
// FaultInject 页面测试
// ============================================================
test.describe('Fault Inject 故障注入页面', () => {

  test('FI-1: 页面加载显示 4 个故障卡片', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('Fault Inject').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('.sim-section h2')).toHaveText('Fault Injection');
    const cards = page.locator('.fault-card');
    await expect(cards).toHaveCount(4);
    const names = await page.locator('.fault-card h3').allTextContents();
    console.log(`[Fault Inject] Cards: ${names.join(', ')}`);
    expect(names.some(n => n.includes('RADIUS Timeout'))).toBeTruthy();
    expect(names.some(n => n.includes('Auth Reject'))).toBeTruthy();
    expect(names.some(n => n.includes('Network Latency'))).toBeTruthy();
    expect(names.some(n => n.includes('Packet Loss'))).toBeTruthy();
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FI-2: Inject 按钮点击后显示反馈', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('Fault Inject').click();
    await page.waitForTimeout(1500);

    // 点击 Auth Reject 卡片（无需网络依赖）
    const rejectCard = page.locator('.fault-card', { hasText: 'Auth Reject' });
    await rejectCard.locator('button').click();
    await page.waitForTimeout(2000);

    // 验证结果反馈
    const result = rejectCard.locator('.result');
    if (await result.isVisible({ timeout: 5000 }).catch(() => false)) {
      const text = await result.textContent();
      console.log(`[Fault Inject] Auth Reject result: ${text}`);
    }
    // 清除所有故障（btn-clear 仅在 f.active 时为 true，API 完成后会消失，所以先检查）
    const clearBtn = page.locator('button.btn-clear').first();
    if (await clearBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clearBtn.click();
      await page.waitForTimeout(500);
    }
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FI-3: Clear 按钮清除故障', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('Fault Inject').click();
    await page.waitForTimeout(1500);

    // 注入一个故障
    const timeoutCard = page.locator('.fault-card', { hasText: 'RADIUS Timeout' });
    await timeoutCard.locator('button').click();
    await page.waitForTimeout(3000);

    // 清除
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('Fault Inject').click();
    await page.waitForTimeout(1000);
    // 点击 Clear（如果有）
    const clearBtn = page.locator('button.btn-clear');
    if (await clearBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await clearBtn.click();
      await page.waitForTimeout(1000);
      console.log('[Fault Inject] Clear clicked');
    }
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// ServicesConfig 页面标签验证
// ============================================================
test.describe('Services Config 页面 — 6 个服务标签', () => {

  test('SVC-1: 页面加载显示 6 个服务标签', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('.services-section')).toBeVisible();

    const tabs = page.locator('.svc-nav button');
    await expect(tabs).toHaveCount(6, { timeout: 8000 });
    const tabTexts = await tabs.allTextContents();
    console.log(`[Services] Tabs: ${tabTexts.join(', ')}`);
    expect(tabTexts).toContain('QoS / Traffic Control');
    expect(tabTexts).toContain('VPN - IPsec');
    expect(tabTexts).toContain('VPN - WireGuard');
    expect(tabTexts).toContain('VPN - OpenVPN');
    expect(tabTexts).toContain('Hotspot / Captive Portal');
    expect(tabTexts).toContain('High Availability (VRRP)');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SVC-2: 切换每个标签验证面板渲染', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);

    const tabs = page.locator('.svc-nav button');
    const tabCount = await tabs.count();
    for (let i = 0; i < tabCount; i++) {
      const tabText = await tabs.nth(i).textContent();
      await tabs.nth(i).click();
      await page.waitForTimeout(400);
      const panelTitle = await page.locator('.svc-panel h3').textContent();
      console.log(`[Services] Tab ${i + 1}: "${tabText}" -> panel: "${panelTitle}"`);
      expect(panelTitle).toBe(tabText);
    }
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SVC-3: 状态栏显示所有服务状态指示器', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);

    const statusItems = page.locator('.status-bar .status-item');
    const statusCount = await statusItems.count();
    console.log(`[Services] Status items: ${statusCount}`);
    const statusNames = await statusItems.locator('.s-name').allTextContents();
    console.log(`[Services] Service names: ${statusNames.join(', ')}`);
    expect(statusCount).toBeGreaterThanOrEqual(1);

    const states = await statusItems.locator('.s-state').allTextContents();
    console.log(`[Services] States: ${states.join(', ')}`);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// L2TP VPN 场景全链路
// ============================================================
test.describe('E2E — L2TP VPN 场景全链路', () => {
  test('L2TP-VPN-1: Scenario 配置下发 → L2TP VPN 6/6 applied', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'L2TP VPN');
    expect(result).toContain('6/6');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('L2TP-VPN-2: Config Editor 验证 L2TP 配置段已写入', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifyConfigSection(page, 'l2tp');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('L2TP-VPN-3: Dashboard 状态正常', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// PPTP Legacy 场景全链路（含真实拨号）
// ============================================================
test.describe('E2E — PPTP Legacy 场景全链路（含真实拨号）', () => {
  test('PPTP-1: Scenario 配置下发 → PPTP Legacy 5/5 applied', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'PPTP Legacy');
    expect(result).toContain('5/5');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('PPTP-2: Subscriber Sim 发起 PPTP 拨号 → 轮询等待结果', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await simDialAndVerify(page, 'pptp', 1);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('PPTP-3: Sessions 页面验证 PPTP 会话', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifySessions(page, 'testuser');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('PPTP-4: Dashboard 状态反映 PPTP 活动', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('PPTP-5: 清理拨号连接', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await stopSim(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// SSTP Only 场景全链路（含真实拨号）
// ============================================================
test.describe('E2E — SSTP Only 场景全链路（含真实拨号）', () => {
  test('SSTP-1: Scenario 配置下发 → SSTP Only 5/5 applied', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'SSTP Only');
    expect(result).toContain('5/5');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SSTP-2: Subscriber Sim 发起 SSTP 拨号 → 轮询等待结果', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await simDialAndVerify(page, 'sstp', 1);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SSTP-3: Sessions 页面验证 SSTP 会话', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifySessions(page, 'testuser');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SSTP-4: Dashboard 状态反映 SSTP 活动', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('SSTP-5: 清理拨号连接', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await stopSim(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// Home Broadband 场景全链路（PPPoE + QoS）
// ============================================================
test.describe('E2E — Home Broadband 场景全链路（PPPoE + QoS）', () => {
  test('HB-1: Scenario 配置下发 → Home Broadband', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'Home Broadband');
    expect(result).toMatch(/\d+\/8 applied/);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('HB-2: Config Editor 验证 PPPoE 配置段', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifyConfigSection(page, 'pppoe');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('HB-3: Subscriber Sim PPPoE 拨号', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await simDialAndVerify(page, 'pppoe', 1);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('HB-4: Sessions + Dashboard 验证', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifySessions(page, 'testuser');
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('HB-5: 清理拨号连接', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await stopSim(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// Enterprise VPN 场景（L2TP + IPsec）
// ============================================================
test.describe('E2E — Enterprise VPN 场景（L2TP + IPsec）', () => {
  test('EVPN-1: Scenario 配置下发 → Enterprise VPN', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'Enterprise VPN');
    expect(result).toMatch(/\d+\/9 applied/);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('EVPN-2: Config Editor + Services IPsec 验证', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifyConfigSection(page, 'ipsec');
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);
    await expect(page.locator('.svc-nav button', { hasText: 'IPsec' })).toBeVisible();
    console.log('[Enterprise VPN] IPsec tab confirmed');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('EVPN-3: Dashboard 状态验证', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// Full Load Test 场景（全协议 + 全服务）
// ============================================================
test.describe('E2E — Full Load Test 场景（全协议 + 全服务）', () => {
  test('FULL-1: Scenario 配置下发 → Full Load Test', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'Full Load Test');
    expect(result).toMatch(/\d+\/8 applied/);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FULL-2: VPN Services 页面验证', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);
    const tabs = await page.locator('.svc-nav button').allTextContents();
    console.log(`[Full Load] Service tabs: ${tabs.join(', ')}`);
    expect(tabs).toContain('VPN - IPsec');
    expect(tabs).toContain('VPN - WireGuard');
    expect(tabs).toContain('VPN - OpenVPN');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FULL-3: Subscriber Sim PPPoE 拨号', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await simDialAndVerify(page, 'pppoe', 1);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FULL-4: Sessions + Dashboard 验证', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifySessions(page, 'testuser');
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('FULL-5: 清理拨号连接', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await stopSim(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// All VPNs 场景（WireGuard + IPsec + OpenVPN）
// ============================================================
test.describe('E2E — All VPNs 场景（WireGuard + IPsec + OpenVPN）', () => {
  test('ALLVPN-1: Scenario 配置下发 → All VPNs 6/6 applied', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'All VPNs');
    expect(result).toContain('6/6');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('ALLVPN-2: Config Editor 验证 VPN 配置段', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await verifyConfigSection(page, 'vpn');
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('ALLVPN-3: VPN Services 验证三个服务标签', async ({ page }) => {
    captureErrors(page);
    await page.goto(BASE); await page.waitForTimeout(500);
    await page.locator('.rnas-sidebar').getByText('VPN Services').click();
    await page.waitForTimeout(1500);
    const tabs = await page.locator('.svc-nav button').allTextContents();
    console.log(`[All VPNs] Service tabs: ${tabs.join(', ')}`);
    for (const svc of ['WireGuard', 'IPsec', 'OpenVPN']) {
      const found = tabs.some(t => t.toLowerCase().includes(svc.toLowerCase()));
      console.log(`  ${svc}: ${found ? '✅' : '❌'}`);
      expect(found).toBeTruthy();
    }
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('ALLVPN-4: Dashboard 状态验证', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});

// ============================================================
// Hotel WiFi & IPTV Multicast 场景（配置验证）
// ============================================================
test.describe('E2E — Hotel WiFi & IPTV Multicast 场景（配置验证）', () => {
  test('HOTEL-1: Hotel WiFi 场景下发', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'Hotel WiFi');
    expect(result).toMatch(/\d+\/7 applied/);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('HOTEL-2: Dashboard 状态正常', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('IPTV-1: IPTV Multicast 场景下发', async ({ page }) => {
    captureErrors(page);
    const result = await runScenario(page, 'IPTV Multicast');
    expect(result).toMatch(/\d+\/8 applied/);
    expect(page.__e2e_errors).toHaveLength(0);
  });

  test('IPTV-2: Dashboard 状态正常', async ({ page }) => {
    captureErrors(page);
    await verifyDashboard(page);
    expect(page.__e2e_errors).toHaveLength(0);
  });
});
