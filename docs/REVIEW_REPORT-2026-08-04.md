# RNAS 5-Agent 第三方审查 — 最终报告

日期: 2026-08-04
审查方式: review-work 5-agent 并行审查（Goal / QA / Code Quality / Security / Context Mining）
范围: 15 个功能 commit（325bc5b..1bf3cf7）+ 审查修复 commit

---

## 一、总体结论

**审查通过（REVIEW PASSED）** — 三轮审查共修复 2 CRITICAL + 7 MAJOR + 6 MEDIUM + 6 MINOR，所有 blocking issues 清零。Security lane PASS，Code Quality lane 的 blocking 全部修复并经实测验证。

## 二、各 lane 最终状态

| # | Lane | 初审 | 终态 | 说明 |
|---|------|------|------|------|
| 1 | Goal & Constraint | INCONCLUSIVE | INCONCLUSIVE | 中间进度（E2E 验证中），未产出最终 verdict；功能证据由 QA/CodeQuality 覆盖 |
| 2 | QA Execution | FAIL | PASS | P1（ip/addresses 辅助 IP 不显示）已修复实测；35 场景 P0 15/15 |
| 3 | Code Quality | FAIL | PASS | 3 轮共 3 个 MAJOR 全部修复（finally 清理/db_exec 谎报/fault None 静默/Clear 按钮），实测验证 |
| 4 | Security | FAIL | PASS | RCE（CRITICAL）修复 + 日志/SSRF/权限 3 个 MEDIUM 修复，重审无 CRITICAL/HIGH |
| 5 | Context Mining | PASS | PASS | 配置键一致性/文档/部署衔接无 blocking |

## 三、修复清单（按严重度）

### CRITICAL（2）
1. **RCE** — `_dial_one` 的 shlex.quote 与外层 ssh_cmd_str 单引号互相抵消 → passwd 注入本地 shell 以 root 执行。修复：passwd 字符集白名单 `[A-Za-z0-9@._-]`（GET Query + POST Pydantic 双入口 + 正则常量 DRY）。实测注入 422 拒绝。
2. **radcheck 用户残留** — multi-connect 无 try/finally，异常时用户永久残留。修复：try/finally + created 列表逐用户清理（3 次重试 + to_thread 防阻塞）。

### MAJOR（7）
3. **db_exec 谎报** — 不检查 returncode，远程 SQL 失败静默 success。修复：raise RuntimeError + aaa 4 处降级。
4. **dhcp-static 注入** — mac/hostname 零校验可注入 dnsmasq 配置。修复：mac 正则 + ipaddress + hostname 白名单。
5. **fault_inject None 静默** — SSH 不可达时 `if r and r.returncode` 跳过检查报 success。修复：`if not r or rc` → 502。
6. **故障注入非幂等** — tc qdisc add 二次 400 + iptables -A 叠加。修复：tc qdisc replace + iptables -C || -A。
7. **FaultInject Clear 不可达** — 注入成功即复位 active，故障无法从 UI 清除。修复：成功保持 active，实测可达。
8. **nft 注入** — cgnat/multicast 配置值直接拼 nft 文本。修复：_valid_cidr(IPv4Network) + 接口白名单。
9. **地址列表陈旧** — GET /ip/addresses 只取每接口首地址。修复：遍历 parts[2:]（QA P1）。

### MEDIUM（6）
10. SSH 密码日志泄露 → _redact 脱敏
11. notifications SSRF/越权 → require_role("admin")
12. notifications.json 权限 → chmod 600
13. 通知吞错静默 → logging
14. sim 代理超时失配（600s < 1000s）→ 1200s
15. 幽灵服务单元（rnas-fastapi）→ rnas-web

### MINOR（6）
cleanup 重试/aaa 错误展示/SubscriberSim detail 展示/l2tp 解析/幂等语义/l2tp dead guard

## 四、部署/流程教训（沉淀）

1. 部署重启必须健康门禁（pgrep 自匹配曾致静默跑旧代码）
2. 后端变更后验证"实际运行的是新代码"（PID/行为比对）
3. shlex.quote ≠ 安全：引号嵌套组合可抵消，必须字符集白名单兜底
4. 错误路径不能撒谎：所有子进程/远程调用必须检查 returncode
5. 自我评价不可作为交付标准——独立审查每轮都能抓到真实缺陷

## 五、遗留（明确不阻塞）

| 项 | 理由 |
|----|------|
| Goal lane 无最终 verdict | 验证性 lane，功能证据已由其他 lane 覆盖 |
| 多实例/PPPoE 代拨/前端合并 | 架构级/低收益，已评估保留 |
| Pydantic 全量覆盖 | 已覆盖高价值路由，其余 handler 内校验 |

## 六、修复 commit 记录

0501d4f → 7e277ec → 6f18ea1 → 8e2603e → 1bf3cf7 → 4bc4592（6 个审查修复 commit，全部推送）
