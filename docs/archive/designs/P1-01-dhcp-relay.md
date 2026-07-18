# P1-01: DHCP Relay 详细设计

## 用户故事
> 作为网络工程师，我需要 RNAS 能将 DHCP 请求中继到上游 DHCP/RADIUS 服务器，同时插入 Option 82（Circuit-ID/Remote-ID），以便在端到端 IPoE 场景中验证 RADIUS 服务器对 DHCP 属性的处理逻辑。

## 当前状态
- ✅ IPoE 本地模式工作（accel-ppp 内建 DHCP server，CIDR range + named pool）
- ❌ 无 DHCP Relay 功能（无法将请求转发到外部 DHCP 服务器）
- ❌ 无 Option 82 支持
- ❌ 无 RADIUS 集成（relay 场景下，RADIUS 根据 Option 82 信息做认证）

## 技术设计

### 架构
```
VM1 (CPE)                 VM3 (RNAS)                    VM2 (RADIUS + DHCP)
   |                          |                              |
   |-- DHCP DISCOVER -------->|                              |
   |                          |-- Insert Option 82 --------->|
   |                          |   (Circuit-ID=ens33,         |
   |                          |    Remote-ID=MAC)            |
   |                          |                              |
   |                          |<-- DHCP OFFER (with IP) -----|
   |<-- DHCP OFFER -----------|                              |
   |                          |                              |
   |-- DHCP REQUEST --------->|                              |
   |                          |-- Access-Request ----------->|
   |                          |   (User-Name=DHCP-Option-82) |
   |                          |<-- Access-Accept ------------|
   |                          |                              |
   |<-- DHCP ACK -------------|<-- DHCP ACK ----------------|
```

### 实现方案

#### 方案 A：dnsmasq DHCP relay（推荐）
利用已有 dnsmasq，配置 `dhcp-relay` 模式：
```
dhcp-range=192.168.100.0,proxy,255.255.255.0
dhcp-relay=192.168.0.202  # relay to VM2
```
优点：极小改动，只需生成 dnsmasq 配置
缺点：dnsmasq relay 不插入 Option 82

#### 方案 B：isc-dhcp-relay
安装 `isc-dhcp-relay`，配置 Option 82：
```
dhcrelay -i ens33 -a 192.168.0.202
```
优点：标准实现，支持 Option 82
缺点：额外依赖

#### 方案 C：accel-ppp IPoE relay 模式
accel-ppp IPoE 模块支持 relay 模式，插入 RADIUS 属性
优点：与现有 accel-ppp 集成
缺点：配置复杂，需要额外测试

**推荐方案 A + Option 82 补充**：用 dnsmasq relay + 独立 Python 脚本插入 Option 82

### 配置模板变更

`/etc/rnas/network.d/dhcp.conf` 新增：
```ini
[relay]
enabled = yes
server = 192.168.0.202
interface = ens33
option_82 = yes
circuit_id = ens33
remote_id_format = mac
```

### rnas-config 生成器变更
`generate_dnsmasq()` 新增 relay 模式输出：
```python
if relay.get("enabled") == "yes":
    w(f"dhcp-relay={relay['server']}")
    w(f"dhcp-range={pool},proxy,{netmask}")
```

### 测试计划

| 测试项 | 方法 | 验收标准 |
|--------|------|---------|
| Relay 启动 | VM1 dhcpcd → VM3 relay → VM2 | VM1 获取 IP |
| Option 82 | tcpdump 抓包 | DHCP 包包含 Option 82 |
| RADIUS 集成 | 检查 radacct | Calling-Station-Id 包含 Option 82 |
| Option 82 格式 | 检查电路ID格式 | `ens33:000c29760fe4` |
| 无 relay 服务器 | 停止 VM2 DHCP | VM1 获取不到 IP |

### 依赖
- VM2 需要运行 DHCP 服务（isc-dhcp-server 或 dnsmasq DHCP）
- 不需要新的 VM3 包依赖

### 预估工时
4-6 小时（含编写、部署、调试、测试）
