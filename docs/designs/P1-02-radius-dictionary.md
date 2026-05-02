# P1-02: RADIUS 属性字典详细设计

## 用户故事
> 作为 RADIUS 协议开发者和网络工程师，我需要 RNAS 支持华为/思科/MikroTik 等厂商的私有 RADIUS 属性（VSA），能够在 Web 界面浏览、搜索属性，在 RADIUS 测试工具中选择属性构建测试报文，以验证 RADIUS 服务器对各种厂商属性的兼容性。

## 当前状态
- ✅ FreeRADIUS 标准属性字典可用 (`/usr/share/freeradius/dictionary.*`)
- ✅ RADIUS 测试工具可用（PAP 认证测试）
- ❌ 厂商 VSA 字典缺失（华为/思科/华三/MikroTik）
- ❌ 无 Web 界面浏览属性
- ❌ 无可视化 RADIUS 报文构建

## 技术设计

### 数据模型

字典文件格式（兼容 FreeRADIUS 格式）：
```
# /etc/rnas/dictionary/huawei
VENDOR Huawei 2011
BEGIN-VENDOR Huawei
ATTRIBUTE Huawei-Input-Peak-Rate 1 integer
ATTRIBUTE Huawei-Output-Peak-Rate 2 integer
ATTRIBUTE Huawei-AVPair 3 string
END-VENDOR Huawei
```

### 文件结构
```
/etc/rnas/dictionary/
├── ietf           # RFC 标准属性
├── huawei         # 华为 VSA (vendor 2011)
├── cisco          # 思科 VSA (vendor 9)
├── h3c            # 华三 VSA (vendor 25506)
├── mikrotik       # MikroTik VSA (vendor 14988)
├── microsoft      # 微软 VSA (vendor 311)
├── wispr          # WISPr (vendor 14122)
└── custom         # 用户自定义属性
```

### Web API

```
GET  /api/dictionary                    → 列出所有厂商
GET  /api/dictionary/{vendor}           → 列出该厂商属性
GET  /api/dictionary/{vendor}/{attr}    → 查询单个属性详情
POST /api/dictionary/{vendor}           → 添加自定义属性
PUT  /api/dictionary/{vendor}/{attr}    → 修改属性
DELETE /api/dictionary/{vendor}/{attr}  → 删除属性
GET  /api/dictionary/search?q={keyword} → 全文搜索
```

### Web UI 设计

```
┌─────────────────────────────────────────────────┐
│ RADIUS Dictionary                                │
├──────────────┬──────────────────────────────────┤
│ Vendor       │ Attributes                        │
│ ──────────── │ ──────────────────────────────── │
│ ● IETF (RFC) │ ○ User-Name          (1)  string │
│ ○ Huawei     │ ○ User-Password      (2)  string │
│ ○ Cisco      │ ○ CHAP-Password      (3)  octets │
│ ○ H3C        │ ○ NAS-IP-Address     (4)  ipaddr │
│ ○ MikroTik   │ ○ NAS-Port           (5)  integer│
│ ○ Microsoft  │ ○ Service-Type       (6)  enum   │
│ ○ WISPr      │ ○ Framed-Protocol    (7)  enum   │
│ ○ Custom     │ ○ ...                             │
│              │                                   │
│ [+ Add VSA]  │ [Search: ______________] [🔍]    │
└──────────────┴──────────────────────────────────┘
```

### RADIUS 测试工具增强

当前工具只发送 `User-Name + User-Password`。增强后支持：
1. 下拉选择属性 → 填入值 → 添加行
2. 构建任意属性组合的 Access-Request
3. 预览报文（Wireshark-like hex dump）
4. 发送并显示原始响应 （Access-Accept/Reject + 返回属性列表）

### 实现步骤

| 步骤 | 内容 | 产出 |
|------|------|------|
| 1 | 下载/编写华为/思科/MikroTik 字典文件 | 6 个 .dict 文件 |
| 2 | 编写 Python 字典解析器 | `rnas-dict` 工具 |
| 3 | 添加 API 路由 (GET/POST/PUT/DELETE) | `server.py` 扩展 |
| 4 | 创建 Dictionary Vue 组件 | `DictionaryBrowser.vue` |
| 5 | 增强 RADIUS 测试工具 | 动态属性构建器 |
| 6 | 端到端测试 | 使用华为 VSA 构建 CoA 报文 |

### 字典属性类型支持

| 类型 | FreeRADIUS | 说明 |
|------|-----------|------|
| integer | integer | 32位整数 |
| string | string | UTF-8 字符串 |
| ipaddr | ipaddr | IPv4 地址 |
| date | date | 时间戳 |
| octets | octets | 二进制数据 (hex) |
| ifid | ifid | 接口 ID |
| ipv6addr | ipv6addr | IPv6 地址 |
| ipv6prefix | ipv6prefix | IPv6 前缀 |

### 厂商 ID 表

| 厂商 | Vendor-ID | 常用属性 |
|------|-----------|---------|
| IETF | — | User-Name, Framed-IP-Address, Session-Timeout |
| Huawei | 2011 | Huawei-Input-Peak-Rate, Huawei-QOS-Profile |
| Cisco | 9 | Cisco-AVPair, Cisco-Service-Info |
| H3C | 25506 | H3C-Input-Peak-Rate, H3C-NAS-Profile |
| MikroTik | 14988 | Mikrotik-Rate-Limit, Mikrotik-Address-List |
| Microsoft | 311 | MS-CHAP-Error, MS-Primary-DNS-Server |
| WISPr | 14122 | WISPr-Bandwidth-Max-Up, WISPr-Location-ID |

### 验收标准

| # | 标准 | 验证方法 |
|---|------|---------|
| 1 | 所有 6 个厂商字典加载成功 | `rnas-dict list` |
| 2 | Web UI 可浏览所有属性 | Playwright 测试 |
| 3 | 搜索功能返回正确结果 | 搜索 "rate" → 显示 Huawei/Cisco 速率属性 |
| 4 | RADIUS 工具可添加自定义属性 | 构建含 Huawei-QOS-Profile 的 Access-Request |
| 5 | CoA 工具可使用字典属性 | 含 VSA 的 Disconnect-Request 发送成功 |

### 预估工时
8-12 小时（字典编写 2h + 解析器 2h + API 2h + UI 3h + 测试 3h）
