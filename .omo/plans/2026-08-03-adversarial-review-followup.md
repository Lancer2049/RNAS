# 对抗性审查后续 — 解决方案与任务计划

日期: 2026-08-03
状态: 待确认
审查方式: 第三方 agent 审查（5 路并行）因 subagent 模型配置故障不可用 → 以对抗性审查者立场执行

---

## 一、审查发现总览

### A. 已修复并验证（commit `0501d4f`，全量回归 206 passed）

| # | 严重度 | 发现 | 修复 | 验证 |
|---|--------|------|------|------|
| A1 | CRITICAL | `sim/multi-connect` 创建/拨号/清理无 try/finally，异常时 radcheck 用户永久残留 | 全程包 try/finally + `created` 列表保证清理 | subscriber-sim E2E 4/4 |
| A2 | MAJOR | `POST /ip/dhcp-static` mac/ip/hostname 零校验，hostname 含换行/逗号可注入 dnsmasq 配置 | mac 正则 + ipaddress + hostname 白名单 | curl 实测非法 400 / 合法 ok |
| A3 | MEDIUM | cgnat/multicast 生成器配置值直接拼 nft 文本（注入面） | `_valid_cidr` + 接口名白名单 | 生成器单测：注入值被拦截 |
| A4 | MEDIUM | alerts.py 三处空 except 吞错，通知失败静默 | `logging.warning` 记录 | 语法验证 + E2E 通过 |

### B. 附带发现（已修复，运维层）

| # | 发现 | 修复 |
|---|------|------|
| B1 | `start9099.sh` 的 `kill $(pgrep -f ...)` pgrep 自匹配 → 旧 9099 进程从未被杀、后续重启全部静默失败（**多次"重启"实际在跑旧代码**） | 按 `/proc/*/cmdline` 精确匹配 `port 9099` |

### C. 审查确认仍存在的遗留问题（本计划范围）

| # | 严重度 | 问题 | 位置 |
|---|--------|------|------|
| C1 | MINOR | `GET /sim/connect` 的 user/passwd Query 无长度/字符限制（POST 路径已有 Pydantic 限制，GET 未同步） | `web/api/routes/sim.py:71-75` |
| C2 | MEDIUM | alert_worker 用 threading 每 uvicorn 进程一个实例——若生产以多 worker 启动会重复通知；当前单 worker 无碍但无防御 | `web/api/services/alert_worker.py` |
| C3 | LOW | `docs/API.md` 未记录新增端点（multi-connect / notifications / cgnat / multicast） | `docs/API.md` |
| C4 | LOW | 部署/重启流程非正式化：`start9099.sh` 是 VM3 临时脚本未入仓库，无健康检查门禁 | `scripts/` |

---

## 二、解决方案

### C1. GET /sim/connect 参数限制
- 方案: 与 POST 路径对齐，用 Pydantic 校验。最简：Query 加 `min_length/max_length` 参数（FastAPI 原生支持），或复用 `MultiConnectRequest` 的校验逻辑抽公共函数
- 取舍: 最小改动选 Query 约束（`user: str = Query("testuser", min_length=1, max_length=32)` + pattern）；彻底方案是引入 `DialRequest` 模型
- 风险: 低；现有 E2E 用 testuser/testpass 不受影响

### C2. alert_worker 单实例保证
- 方案: 启动时用 PID 锁文件（`/var/run/rnas-alert-worker.lock`，flock 非阻塞）——若已被占则跳过启动，防止多 worker 重复通知线程
- 取舍: flock 文件锁轻量可靠；不做 Redis/DB 分布式锁（过度设计）
- 风险: 低；单 worker 部署行为不变

### C3. API.md 文档补齐
- 方案: 新增端点文档块：`POST /api/sim/multi-connect`（请求/响应示例）、`GET/POST /api/system/notifications`、`POST /api/system/notifications/test`、`PUT /api/config/cgnat`、`PUT /api/config/multicast`，标注 Pydantic 校验行为（422）
- 取舍: 纯文档，无代码风险

### C4. 部署流程正式化
- 方案:
  1. 将启动/重启脚本写入 `scripts/restart-api.sh`（含精确 kill + 启动 + 健康检查门禁：`curl /api/health` 重试 10 次，失败则回滚告警）
  2. 脚本入 git；`deploy-to-vm3.sh` 引用它
  3. 文档记录"后端变更部署流程"（当前流程分散在会话记忆）
- 取舍: 脚本幂等 + 健康门禁，防止"旧进程未杀净"类静默失败再次发生

---

## 三、任务计划

| # | 任务 | 优先级 | 依赖 | 验收标准 |
|---|------|--------|------|----------|
| 1 | C1: `sim.py` GET /sim/connect 加 Query 长度/pattern 约束 | P1 | 无 | curl 非法 user 返回 422；subscriber-sim E2E 4/4 |
| 2 | C2: `alert_worker.py` 加 flock 单实例锁 | P2 | 无 | 二次启动 start_alert_worker 不产生第二个线程（单测或日志验证） |
| 3 | C3: `API.md` 补 5 个新端点文档 | P2 | 无 | grep 确认端点均有文档块 |
| 4 | C4: `scripts/restart-api.sh` 入仓库 + deploy-to-vm3 引用 | P2 | 无 | 脚本在 VM3 执行成功 + 健康门禁生效 |
| 5 | 全量回归 + HANDOVER_REPORT 更新 + push | P1 | 1-4 | 206+ E2E 全绿 |
| 6 | 重启 opencode 后重跑 5-agent review-work 交叉验证 | P0(流程) | opencode 重启 | 5 lane 全部 PASS/INCONCLUSIVE 明确 |

---

## 四、明确不做的项（保留理由）

| 项 | 理由 |
|----|------|
| PPPoE 代拨 | 与 B3 Subscriber Sim 拨号机制重叠，增量价值低 |
| 多实例支持 | 架构级，当前单实例场景无实际需求 |
| 前端组件合并 | 低收益高风险重构，已评估保留 |
| Pydantic 全量覆盖所有路由 | 已覆盖 3 个高价值路由；其余 dict Body 有 handler 内校验，收益递减 |

---

## 五、审查流程教训（沉淀到 HANDOVER）

1. 部署重启必须含健康检查门禁（B1 教训：静默失败无感知）
2. 后端代码变更后必须验证"实际运行的是新代码"（比对 PID/行为，而非假设重启成功）
3. 文档（API.md）与功能开发同步更新
4. 技术债务清零的判定需外部视角交叉验证（本次自我评价掩盖了 CRITICAL 缺陷）

---

## 六、待办

- [ ] 用户确认本计划（确认后按优先级 1-5 实施）
- [ ] opencode 重启后执行任务 6（5-agent 审查）
