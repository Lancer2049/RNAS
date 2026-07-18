# RNAS REST API

实时 API 文档由 FastAPI 内置的 OpenAPI 自动生成，**无需手动维护端点列表**。

## 访问方式

启动 RNAS API 后（`uvicorn main:app --host 0.0.0.0 --port 8099`），访问以下地址：

| 地址 | 说明 |
|------|------|
| `http://<host>:8099/docs` | **Swagger UI** — 交互式API测试，按 tags 分组 |
| `http://<host>:8099/redoc` | **ReDoc** — 更美观的文档视图 |
| `http://<host>:8099/openapi.json` | **OpenAPI Schema** — 机器可读，可用于代码生成 |

## 路由分组（Swagger tags）

| Tag | 路由模块 | 主要端点 |
|-----|----------|----------|
| **Status** | `routes/status.py` | `/api/health`, `/api/status` |
| **Configuration** | `routes/config.py` | `/api/config`, `/api/config/apply`, 快照  |
| **Network** | `routes/extra.py` | 接口/防火墙/抓包/带宽/隧道/VLAN/QoS |
| **Diagnostics** | `routes/tools.py` | Ping/Trace/DNS/RADIUS/CoA |
| **System** | `routes/system.py` | 系统状态/日志/证书/服务 |
| **AAA RADIUS** | `routes/aaa.py` | 用户/计费/组/NAS客户端 |
| **Simulation** | `routes/sim.py` | 用户拨号仿真 |

## 认证

Phase 0（2026-07）后引入 JWT Bearer Token 认证，`/api/health` 除外。

## 代码生成

从前端生成 TS 类型：

```bash
npx openapi-typescript http://localhost:8099/openapi.json -o src/types/api.ts
```
