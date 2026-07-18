# RNAS 项目改进清单

> 根据 AI 分析报告对比实际代码生成的差距分析

## P1: 高优先级

- [x] `rnas-config` CLI 已有 generate/validate/show
- [x] **已加** snapshot/scenario/apply 子命令
- [ ] **测试套件补齐** — 下面 3 个脚本需要创建：

### 1.1 压力测试 `tests/stress/pppoe-stress.sh`
多客户端并发 PPPoE 拨号测试，测量 CPS、内存、CPU

### 1.2 故障注入 `tests/stress/fault-injection.sh`
tc netem 延迟/丢包、iptables RADIUS 阻断、进程崩溃恢复

### 1.3 基准测试 `tests/bench/rnas-bench.py`
asyncio + ThreadPoolExecutor 10000 并发认证请求

## P2: 中优先级

- [ ] **`rnas-cli` 诊断 CLI** — session/coa/capture/radius-test 子命令
  - `rnas-cli status` / `rnas-cli sessions` / `rnas-cli coa --user X --rate 10M`
- [ ] **Pydantic 数据模型** — API 响应使用 `BaseModel` 做校验
- [ ] **DHCP Relay Option 82** — Python 实现 DHCP relay 的 Option 82 插入

## P3: 低优先级

- [ ] **802.1X / MAC Auth** — hostapd 配置生成
- [ ] **pyrad 集成** — 替代 subprocess radclient
- [ ] **tcpdump 抓包 API** — `POST /api/tools/capture`
- [ ] **Docker 完善** — FreeRADIUS 独立镜像、accel-ppp 独立镜像

---

## 分析报告关键指标

| 指标 | 报告值 |
|------|--------|
| 总页数 | 31 |
| 配置生成器 | 19 个 |
| 测试场景 JSON | 10 个 |
| 接入协议 | 5/5 已验证 |
| RADIUS 字典厂商 | 13 + RFC Standard |
| systemd 服务单元 | 9 个 |
| 最大并发会话 | 10,000+ |
| RADIUS 认证 P99 | <100ms |
