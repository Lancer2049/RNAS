# RNAS 分阶段开发计划

> **制定日期**: 2026-07-18  
> **制定依据**: RNAS 交接报告 v3.0 + 第三方深度分析报告（安全/架构/测试/战略）  
> **目标受众**: 接手开发团队  
> **计划周期**: 8 周止血 + 季度差异化  

---

## 目录

- [总体策略](#总体策略)
- [Phase 0: 止血（第 1–2 周）— 阻断级安全 + 工程底线](#phase-0-止血第-12-周--阻断级安全--工程底线)
  - [Sprint 0-A: 工程基础（3.5d）](#sprint-0-a-工程基础35d)
  - [Sprint 0-B: 安全防火墙（5d）](#sprint-0-b-安全防火墙5d)
  - [Sprint 0-C: 配置引擎安全阀（2.5d）](#sprint-0-c-配置引擎安全阀25d)
- [Phase 1: 结构性修复（第 3–4 周）— 架构债务清理](#phase-1-结构性修复第-34-周--架构债务清理)
  - [Sprint 1-A: 状态一致性 + 事件驱动（5d）](#sprint-1-a-状态一致性--事件驱动5d)
  - [Sprint 1-B: 模块拆分 + 测试底座（5d）](#sprint-1-b-模块拆分--测试底座5d)
- [Phase 2: S 级补齐（第 2 个月）— 风险缓解优先](#phase-2-s-级补齐第-2-个月--风险缓解优先)
  - [Sprint 2-A: 风险缓解（审计 + 报警 + 配置漂移）（4.5d）](#sprint-2-a-风险缓解审计--报警--配置漂移45d)
  - [Sprint 2-B: 持久化 + 测试工程化（5.5d）](#sprint-2-b-持久化--测试工程化55d)
  - [Sprint 2-C: 文档收敛 + DevEx（3d）](#sprint-2-c-文档收敛--devex3d)
- [Phase 3: 差异化（季度级）— 测试装置定位](#phase-3-差异化季度级--测试装置定位)
  - [Epic 3-A: netns 批量 CPE 压测框架（3-4w）](#epic-3-a-netns-批量-cpe-压测框架3-4w)
  - [Epic 3-B: YAML 场景 DSL（4-6w）](#epic-3-b-yaml-场景-dsl4-6w)
  - [Epic 3-C: RBAC + 版本发布（2-3w）](#epic-3-c-rbac--版本发布2-3w)
  - [Epic 3-D: 可观测性体系（4-5w）](#epic-3-d-可观测性体系4-5w)
- [依赖关系图](#依赖关系图)
- [风险与缓解](#风险与缓解)
- [成功度量](#成功度量)

---

## 总体策略

### 核心原则

1. **止血优先**：安全漏洞 > 架构债务 > 功能缺失。Phase 0 不涉及任何功能开发，仅修复阻断级问题。
2. **单 Worker 过渡**：结构性修复阶段（Phase 1）将 worker 降为 1，消除多进程状态不一致。差异化阶段（Phase 3）再考虑状态外置并恢复多 worker。
3. **测试前移**：每提交一个路由改动，必须伴随 pytest 单测。目标是 Phase 2 结束时路由层覆盖率 > 60%。
4. **差异化聚焦**：功能扩张（CGNAT/QinQ/组播等）全部暂缓。资源投向 netns 压测 + YAML 场景 DSL。

### 工时估算汇总

| 阶段 | 周期 | 核心任务 | 预估总工时 |
|------|------|----------|-----------|
| Phase 0 | 第 1–2 周 | 提交未提交文件 + 认证 + 关 CORS + 输入校验 + apply 安全阀 + CI 门禁 | 11d |
| Phase 1 | 第 3–4 周 | worker 降 1 + WebSocket 事件驱动 + 拆分 extra.py + 测试底座 + server.py 迁移 | 10d |
| Phase 2 | 第 2 个月 | 审计日志 + 健康报警 + 配置漂移 + 流量历史 + E2E 工程化 + 文档收敛 | 13d |
| Phase 3 | 季度级 | netns 压测 + YAML DSL + RBAC + 版本发布 + 可观测性（最后） | 17-23w |
| **合计** | | | **约 2 个月止血 + 季度差异化** |

---

## Phase 0: 止血（第 1–2 周）— 阻断级安全 + 工程底线

> **目标**: 消除 4 个阻断级安全风险中的 3 个（WebTerminal、API 无认证、flag 注入），建立工程纪律基线。  
> **前置**: 无  
> **产出**: 23 个文件已提交、JWT 认证可用、CORS 已关闭、tools 输入校验已上线、apply 流程有安全阀、CI 质量门禁通过  

### Sprint 0-A: 工程基础（3.5d）

#### T0-A1: 提交全部未提交变更 — 0.5d

**目标**: 将 23 个 modified + 7 个 untracked 文件整理后提交，这是所有后续开发的基线。

**操作步骤**:
1. `git add` 所有 `M` 文件（23 个）
2. `git add` 新增的配置引擎模块（`cmd/rnas-config/config_ops.py`、`core.py`、`generators.py`、`tests/`）
3. `git add docs/HANDOVER_REPORT.md`
4. 检查 `.opencode.json`、`.opencode/` 是否应加入 `.gitignore`
5. 按功能分组提交：
   - `fix: security hardening — eliminate shell=True and bare except across web/`
   - `feat: config engine — parser, generators, and 36 unit tests`
   - `feat: lazy loading helper for 34 async components`
   - `feat: E2E test files — monitoring, cross-feature, stability`
   - `docs: comprehensive handover report`
6. `git push`

**涉及文件**:
```
 M web/api/routes/extra.py          (5 shell=True → param lists, 7 bare except → Exception)
 M web/api/routes/aaa.py            (4 shell=True → db_query())
 M web/api/routes/tools.py          (4 shell=True → param lists, 3 bare except → Exception)
 M web/api/routes/config.py         (shell=True cleanup)
 M web/api/routes/sim.py            (shell=True cleanup)
 M web/api/routes/status.py
 M web/api/routes/system.py
 M web/api/services/traffic.py      (4 bare except → Exception)
 M web/server.py                    (18 shell=True → Path.read_text(), 10 bare except → Exception)
 M web/rnas_env.py                  (+db_query() wrapper)
 M web/api/main.py
 M web/frontend/src/App.vue         (lazy() helper)
 M web/frontend/src/components/ProtocolConfig.vue
 M web/frontend/tests/e2e/dashboard.spec.ts
 M web/frontend/tests/e2e/full-integration.spec.ts
 M web/frontend/tests/e2e/new-features.spec.ts
 M .github/workflows/ci.yml         (+pytest step, +Python3.x, -2>/dev/null)
 M AGENTS.md
 M cmd/rnas-config/rnas_config.py
 M configs/README.md
 M scripts/deploy-to-vm3.sh
 M scripts/install.sh
 M systemd/rnas.target
?? cmd/rnas-config/config_ops.py    (new: config read/write operations)
?? cmd/rnas-config/core.py          (new: INI parser + config tree walker)
?? cmd/rnas-config/generators.py    (new: 19 protocol config generators)
?? cmd/rnas-config/tests/           (new: 36 pytest unit tests)
?? web/frontend/tests/e2e/monitoring.spec.ts      (new)
?? web/frontend/tests/e2e/cross-feature.spec.ts   (new)
?? web/frontend/tests/e2e/stability.spec.ts       (new)
?? docs/HANDOVER_REPORT.md
```

**验收标准**: `git status` 干净；CI 通过。

---

#### T0-A2: CI 质量门禁（ruff + bandit + pip-audit + npm audit）— 1d

**目标**: 在 CI 中加入自动化质量检查，阻断低质量代码合入。

**操作步骤**:
1. 修改 `.github/workflows/ci.yml`，在现有 pytest 步骤之后新增：

```yaml
# Python 代码质量
- name: Lint (ruff)
  run: |
    pip install ruff
    ruff check web/ cmd/ --select=E,F,I,N,UP,B,SIM
    ruff format --check web/ cmd/

# 安全扫描
- name: Security scan (bandit)
  run: |
    pip install bandit
    bandit -r web/ -ll --skip B101,B104

# 依赖漏洞
- name: Dependency audit (pip-audit)
  run: |
    pip install pip-audit
    pip-audit

# 前端安全
- name: Frontend security audit
  run: |
    cd web/frontend
    npm audit --audit-level=high
```

2. 修复首次运行发现的 lint 问题（预计 `ruff check` 会报 `B904: bare raise`、`UP006: use `list` instead of `List`` 等）
3. 确认 bandit 不报高风险（`shell=True` 已消除）

**验收标准**: CI 新增步骤全绿；ruff 零警告（如有无法修复的，在 `pyproject.toml` 中加 `per-file-ignores` 并注释原因）

---

#### T0-A3: pre-commit 钩子 — 0.5d

**目标**: 在开发机上也能在提交前自动检查，不依赖 CI。

**操作步骤**:
1. 项目根目录创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix, --select=E,F,I,N,UP,B,SIM]
      - id: ruff-format
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.31.0
    hooks:
      - id: commitizen
      - id: commitizen-branch
        stages: [push]
```

2. 安装: `pip install pre-commit && pre-commit install`
3. 配置 `.cz.toml` 定义 commit message 格式（`fix:` / `feat:` / `docs:` / `test:` / `refactor:`）

**验收标准**: `git commit` 时自动运行 ruff 检查；不合规的提交被拒绝

---

#### T0-A4: 暴露 OpenAPI 文档 — 0.5d

**目标**: 用自动生成的 `/docs` (Swagger) 和 `/redoc` 替代手写的 `docs/API.md`。

**操作步骤**:
1. 确认 `web/api/main.py` 中 `app = FastAPI()` 未禁用 docs（FASTAPI 默认启用）
2. 修改 `docs/API.md`，删掉所有端点的手动列表，改为：

```markdown
# RNAS REST API

实时 API 文档通过 FastAPI 内置的 OpenAPI 自动生成：

- **Swagger UI**: `http://<host>:8099/docs`
- **ReDoc**: `http://<host>:8099/redoc`
- **OpenAPI JSON**: `http://<host>:8099/openapi.json`

## 认证（Phase 0 后）

所有端点（除 `/api/health`）需要 Bearer Token 认证...
```

3. 将所有路由的 `tags` 参数补齐，确保 SwaggerUI 分组清晰
4. 为关键端点补 `summary` 和 `description` docstring

**验收标准**: 启动 `uvicorn` 后访问 `/docs` 可交互式测试所有端点；`docs/API.md` 从 75 行缩减到 < 20 行

---

### Sprint 0-B: 安全防火墙（5d）

#### T0-B1: JWT 认证中间件 — 3d

> ⚠️ **此任务必须在 T0-B2（禁用 WebTerminal）之前启动**，因为该 Feature Flag 依赖认证中间件的 `get_current_user()` 判断

**目标**: 为所有 API 端点（除 `/api/health`）添加 JWT Bearer Token 认证。

**实现方案**:

1. 新建 `web/api/auth.py`：

```python
"""JWT authentication module"""
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# --- Config ---
SECRET_KEY = os.environ.get("RNAS_JWT_SECRET", os.urandom(32).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 临时本地账号（后期替换为数据库/文件）
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": "",  # 安装时生成
        "role": "admin",
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str, role: str = "admin") -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    """返回当前用户，或 None（供可选认证的端点使用）"""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def require_auth(user=Depends(get_current_user)):
    """强制认证依赖注入——未认证返回 401"""
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user
```

2. 新建 `web/api/routes/auth.py`，提供两个端点：

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from api.auth import verify_password, create_access_token, USERS_DB

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/token", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = USERS_DB.get(req.username)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(req.username, user["role"])
    return TokenResponse(access_token=token)
```

3. 在 `web/api/main.py` 中注册 `auth.router`
4. 逐文件改造现有路由——从 `/health` 开始向外扩展：

**改法 A — 需要认证的端点**：
```python
# web/api/routes/config.py 示例
from api.auth import require_auth

@router.get("/api/config/{module}")
async def get_config(module: str, user=Depends(require_auth)):
    ...
```

**改法 B — 可选认证的端点（WebSocket、health）**：
```python
# web/api/main.py 示例
from api.auth import get_current_user

@app.websocket("/api/ws")
async def ws(ws: WebSocket, token: str = Query(None)):
    user = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user = {"username": payload["sub"]}
        except:
            await ws.close(code=4001)
            return
    ...
```

**改造顺序**（按风险排序）：
| 批次 | 模块 | 端点 |
|------|------|------|
| 第 1 批 | tools.py | `/tools/ping`, `/tools/trace`, `/tools/dns`, `/tools/radius-test`, `/tools/coa` |
| 第 2 批 | extra.py | `/interfaces/*`, `/firewall/*`, `/tools/capture`, `/setup/apply` |
| 第 3 批 | sim.py | `/sim/connect`, `/sim/disconnect` |
| 第 4 批 | config.py | `/config/*`, 快照, 导入导出 |
| 第 5 批 | aaa.py | `/aaa/*` |
| 第 6 批 | system.py | `/system/*` |
| 保留免认证 | status.py | `/api/health` |

5. 生成 admin 初始密码：在 `scripts/install.sh` 中增加步骤：
```bash
ADMIN_PASS=$(openssl rand -base64 12)
python3 -c "
from passlib.context import CryptContext
print(CryptContext(schemes=['bcrypt']).hash('$ADMIN_PASS'))
"  # 写入用户文件
echo "ADMIN PASSWORD: $ADMIN_PASS  # 保存此密码"
```

**涉及文件**: 新建 `web/api/auth.py`、`web/api/routes/auth.py`；修改 `web/api/main.py`、`routes/*.py`（6 个）、`scripts/install.sh`

**验收标准**: 访问 `/api/config` 返回 401；`POST /api/auth/token` 获取 token 后带上 `Authorization: Bearer xxx` 可以正常访问；`/api/health` 仍然免认证

---

#### T0-B2: Feature Flag 禁用裸露 WebTerminal + 抓包/带宽端点 — 0.5d

> 前置: T0-B1（认证中间件完成）

**目标**: 在认证完全落地前，用 Feature Flag 默认禁用高风险端点。

**操作步骤**:

1. 在 `web/api/auth.py` 末尾增加：

```python
# 高风险功能 Feature Flag
FEATURE_FLAGS = {
    "web_terminal": os.environ.get("RNAS_FEATURE_TERMINAL", "false").lower() == "true",
    "packet_capture": os.environ.get("RNAS_FEATURE_CAPTURE", "false").lower() == "true",
    "bandwidth_test": os.environ.get("RNAS_FEATURE_BANDWIDTH", "false").lower() == "true",
}
```

2. 在对应的路由中加守卫：

```python
# web/api/routes/extra.py
from api.auth import FEATURE_FLAGS

@router.get("/api/tools/capture")
async def capture(..., user=Depends(require_auth)):
    if not FEATURE_FLAGS["packet_capture"]:
        raise HTTPException(503, detail="Feature disabled. Set RNAS_FEATURE_CAPTURE=true to enable.")
    ...
```

3. 前端 `WebTerminal.vue` 同样需要感知——在页面加载时调用一个 `/api/system/features` 端点返回启用的功能列表，前端据此隐藏/禁用按钮。

4. 更新 `scripts/install.sh` 和 `.env.example`:

```bash
# 安全相关
export RNAS_FEATURE_TERMINAL=false
export RNAS_FEATURE_CAPTURE=false
export RNAS_FEATURE_BANDWIDTH=false
```

**涉及文件**: `web/api/auth.py`（+FEATURE_FLAGS）、`web/api/routes/extra.py`、`web/api/routes/system.py`（+GET /api/system/features）、`web/frontend/src/App.vue`

**验收标准**: 默认启动后访问 WebTerminal 页面返回 503；设置 `RNAS_FEATURE_TERMINAL=true` 重启后恢复可用

---

#### T0-B3: 关 CORS — 0.5d

**目标**: 前端由 FastAPI 静态托管是同源，生产环境直接关闭 CORS。

**操作步骤**:
1. 修改 `web/api/main.py`：

```python
import os

# 开发模式允许 CORS，生产模式同源（关闭）
_ENV = os.environ.get("RNAS_ENV", "production")
if _ENV == "development":
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)
# 生产模式不添加 CORS 中间件
```

2. 更新启动命令文档：开发模式需设置 `RNAS_ENV=development`

**涉及文件**: `web/api/main.py`、`docs/API.md`

**验收标准**: 生产模式下 `curl -H "Origin: http://evil.com" http://host:8099/api/health` 返回的响应头中**不含** `Access-Control-Allow-Origin`；开发模式下通过 Vite dev server (`localhost:5173`) 可以跨域访问 API

---

#### T0-B4: `db_query()` 去 shell — 0.5d

**目标**: 全库唯一的 `shell=True` 彻底消除。

**操作步骤**:
1. 修改 `web/rnas_env.py` 的 `db_query()` 方法：

```python
import os
import subprocess

def db_query(query: str, db: str = "radius") -> str:
    """
    Execute MySQL query using argv list (no shell=True).
    Password MUST be passed via MYSQL_PWD environment variable.
    """
    mysql_bin = "/usr/bin/mysql"
    env = os.environ.copy()
    # MYSQL_PWD 环境变量传密码，不会出现在 ps aux 输出中
    # 调用方必须在环境变量中设置 MYSQL_PWD
    cmd = [
        mysql_bin,
        "--defaults-extra-file=",  # 跳过默认配置文件
        "-u", os.environ.get("MYSQL_USER", "root"),
        "-h", os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "-N",  # 跳过列名
        "-B",  # 批处理模式
        "-e", query,
        db,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)
    if result.returncode != 0:
        raise RuntimeError(f"MySQL query failed: {result.stderr.strip()}")
    return result.stdout
```

**涉及文件**: `web/rnas_env.py`

**验收标准**: `grep -r "shell=True" web/` 返回空；`db_query("SELECT 1")` 正常返回结果

---

#### T0-B5: tools 端点的 flag 注入防护 — 0.5d

> ⚠️ 与 T0-B1 一起做——认证中间件先挡住未授权请求，再做参数白名单校验。实现可与 T0-B1 的 "第 1 批" 路由改造合并。

**目标**: 防止 `host=-c%201%20evil.com` 这类以 `-` 开头的参数改变子进程命令行为。

**操作步骤**:
1. 新建 `web/api/validators.py`：

```python
import ipaddress
import re
from fastapi import HTTPException

# 域名白名单：字母数字 + 点 + 连字符，不能以 - 开头
_HOSTNAME_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$")

def validate_ip_or_hostname(value: str) -> str:
    """校验 IP 或域名，拒绝 flag 注入"""
    # 显式拒绝以 - 开头的参数（命令 flag）
    if value.startswith("-"):
        raise HTTPException(400, f"Invalid host: '{value}' — parameters starting with '-' are rejected")
    # 尝试解析为 IP
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    # 尝试作为域名
    if _HOSTNAME_RE.match(value):
        return value
    raise HTTPException(400, f"Invalid host: '{value}' — must be a valid IP address or hostname")
```

2. 在 `tools.py` 中使用：

```python
from api.validators import validate_ip_or_hostname

@router.get("/api/tools/ping")
async def ping(host: str, user=Depends(require_auth)):
    host = validate_ip_or_hostname(host)
    result = subprocess.run(["ping", "-c", "3", "-W", "2", host],
                           capture_output=True, text=True, timeout=10)
    return {"output": result.stdout}
```

3. 同样改造 `/trace`、`/dns`、`/radius-test`、`/coa`

**涉及文件**: 新建 `web/api/validators.py`；修改 `web/api/routes/tools.py`

**验收标准**:
- `GET /api/tools/ping?host=127.0.0.1` → 200
- `GET /api/tools/ping?host=google.com` → 200
- `GET /api/tools/ping?host=-c%201%20evil.com` → 400
- `GET /api/tools/ping?host=;cat%20/etc/passwd` → 400

---

#### T0-B6: 统一 HTTP Client + 默认 timeout — 0.5d

**目标**: 一处修复，全库 `requests` 都有默认 timeout，防止慢速攻击耗尽 worker。

**操作步骤**:
1. 新建 `web/api/http_client.py`：

```python
import httpx

# 全局复用的异步 HTTP 客户端，默认 10s 超时
_client: httpx.AsyncClient | None = None

def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(10.0), limits=httpx.Limits(max_keepalive_connections=5))
    return _client
```

2. 全库搜索 `requests.get(`、`requests.post(`、`httpx.get(` 等直接调用，替换为 `get_client().get(...)` 或显式加 timeout 参数
3. 在 `web/api/validators.py` 中加一个运行时检查——通过 `pytest` fixture 在测试中 mock httpx 并验证 timeout 已设置

**涉及文件**: 新建 `web/api/http_client.py`；修改 `web/api/routes/tools.py`、`web/api/routes/extra.py`、`web/api/routes/system.py`、`web/api/services/traffic.py` 等含 HTTP 调用的文件

**验收标准**: 所有 HTTP 调用在 10s 无响应后自动超时，不阻塞 worker

---

### Sprint 0-C: 配置引擎安全阀（2.5d）

#### T0-C1: apply 预校验（nft/dnsmasq 干跑）— 1d

**目标**: apply 之前先对生成的原生配置做语法检查，错误配置不会落地。

**操作步骤**:
1. 在 `cmd/rnas-config/rnas_config.py` 的增加 `apply` 子命令中，先调 `--dry-run` 校验：

```python
@cli.command()
@click.option("--root", default="/etc/rnas")
@click.option("--dry-run", is_flag=True, help="Validate without applying")
def apply(root, dry_run):
    """Regenerate and apply all configs"""
    tree = walk_config_tree(Path(root))
    for name, gen_func in GEN_MAP.items():
        output = gen_func(tree)
        target_path = _target_path(name)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(output)
        # 预校验
        _validate_config(name, target_path)
    if not dry_run:
        _reload_services()
```

2. 新建 `cmd/rnas-config/validators.py`：

```python
import subprocess
from pathlib import Path
from typing import Optional

_VALIDATORS = {
    "firewall": lambda p: subprocess.run(["nft", "-c", "-f", str(p)], capture_output=True, text=True, timeout=10),
    "dnsmasq": lambda p: subprocess.run(["dnsmasq", "--test", "--conf-file=" + str(p)], capture_output=True, text=True, timeout=10),
    "ha": lambda p: subprocess.run(["keepalived", "-t", "-f", str(p)], capture_output=True, text=True, timeout=10),
}

def validate_config(generator_name: str, config_path: Path) -> Optional[str]:
    """返回错误信息或 None（通过）"""
    validator = _VALIDATORS.get(generator_name)
    if validator is None:
        return None  # 该生成器无校验器
    result = validator(config_path)
    if result.returncode != 0:
        return f"[{generator_name}] validation failed:\n{result.stderr}"
    return None
```

3. 修改 `web/api/routes/config.py` 的 apply 端点——调用 `rnas-config apply` 前先 `rnas-config apply --dry-run`

**涉及文件**: 新建 `cmd/rnas-config/validators.py`；修改 `cmd/rnas-config/rnas_config.py`、`web/api/routes/config.py`

**验收标准**: 提交一个语法错误的 nftables 规则后，`POST /api/config/apply` 返回 400 并提示具体错误，**原始配置不变**；有效的配置正常应用

---

#### T0-C2: apply 加 flock 并发锁 — 0.5d

**目标**: 两个并发 apply 请求不会交错写入导致配置文件损坏。

**操作步骤**:
1. 在 `cmd/rnas-config/rnas_config.py` 的 apply 流程中加文件锁：

```python
import fcntl
import time

LOCK_FILE = Path("/var/run/rnas-apply.lock")

def _acquire_lock(timeout: int = 30) -> bool:
    """获取全局 apply 锁，timeout 秒内未获取则返回 False"""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCK_FILE, "w")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            time.sleep(0.5)
    return False

def _release_lock(lock_fd):
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()
```

2. 在 apply 端点中包装：

```python
import fastapi
from fastapi.responses import JSONResponse

@router.post("/api/config/apply")
async def apply_config(user=Depends(require_auth)):
    lock_fd = _acquire_lock()
    if not lock_fd:
        return JSONResponse(status_code=423, content={"error": "Another apply is in progress"})
    try:
        # ... 原有 apply 逻辑
        pass
    finally:
        _release_lock(lock_fd)
```

**涉及文件**: `cmd/rnas-config/rnas_config.py`、`web/api/routes/config.py`

**验收标准**: 同时发送两个 apply 请求，第二个返回 423 "Another apply is in progress"；第一个完成后第二个可以正常提交

---

#### T0-C3: apply 自动快照（回滚基础）— 1d

**目标**: 每次 apply 前自动创建快照，为 Phase 1 的回滚机制提供基础。

**操作步骤**:
1. 修改 `cmd/rnas-config/rnas_config.py` 的 apply 流程：

```python
from datetime import datetime

def apply(root: Path):
    """apply 前自动创建快照"""
    lock_fd = _acquire_lock()
    try:
        # Step 1: 自动快照
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _create_snapshot(root, f"auto-apply-{timestamp}")
        
        # Step 2: 生成 + 校验
        errors = _regenerate_and_validate_all(root)
        if errors:
            return {"status": "error", "errors": errors}
        
        # Step 3: 应用 + 重载
        _reload_services()
        return {"status": "ok", "snapshot": f"auto-apply-{timestamp}"}
    finally:
        _release_lock(lock_fd)
```

**注意**: Phase 1 会在此基础上增加"健康检查失败 → 自动回滚到快照"的逻辑。当前先做快照，回滚是下一步。

**涉及文件**: `cmd/rnas-config/rnas_config.py`

**验收标准**: 执行 `rnas-config apply` 后，`rnas-config snapshot list` 中能看到 `auto-apply-*` 快照；执行 `rnas-config snapshot restore <id>` 可以恢复到 apply 前状态

---

## Phase 0 里程碑检查清单

- [ ] 23 个文件已分组提交并 push
- [ ] CI 包含 ruff lint + format check + bandit + pip-audit + npm audit
- [ ] `pre-commit` 钩子生效（ruff + commitizen）
- [ ] `/docs` 可以交互式测试所有端点
- [ ] `/api/health` 免认证；其他端点返回 401
- [ ] `POST /api/auth/token` 正常签发 JWT
- [ ] 所有路由已改造认证依赖（除 `/api/health`）
- [ ] `RNAS_FEATURE_TERMINAL=false` 时 WebTerminal 返回 503
- [ ] 生产模式下 CORS 不设置（响应头无 `Access-Control-Allow-Origin`）
- [ ] `grep -r "shell=True" web/` 返回空
- [ ] `curl .../ping?host=-c` 返回 400
- [ ] 所有 HTTP 调用有 10s 默认超时
- [ ] apply 并发请求第二个返回 423
- [ ] apply 前干跑校验失败则返回 400，原配置不变
- [ ] apply 后自动创建 `auto-apply-*` 快照
- [ ] 全部 18 个 web/ Python 文件通过 `ruff check` 零错误

---

## Phase 1: 结构性修复（第 3–4 周）— 架构债务清理

> **目标**: 消除多 worker 状态不一致、拆分上帝模块、建立测试底座、迁移遗留服务器  
> **前置**: Phase 0 全部完成  
> **产出**: worker=1 稳定运行、WebSocket 事件驱动、450 行 extra.py 拆为 6 个域模块、路由单测覆盖率 > 60%、server.py 已删除  

### Sprint 1-A: 状态一致性 + 事件驱动（5d）

#### T1-A1: worker 降 1 — 0.5d

**目标**: 消除多进程状态不一致问题。管理面单进程性能绰绰有余。

**操作步骤**:
1. 修改 `web/api/main.py` 的启动逻辑——去掉 `--workers`：

```python
# main.py 底部
if __name__ == "__main__":
    import uvicorn
    # 管理面，单进程足够。多 worker 会导致进程内状态不一致。
    uvicorn.run("main:app", host="0.0.0.0", port=8099, workers=1)
```

2. 更新部署文档和 `scripts/install.sh` 中的启动命令：`uvicorn main:app --host 0.0.0.0 --port 8099`（无 `--workers`）
3. 更新 `docker/Dockerfile.rnas-api` 的 CMD

**涉及文件**: `web/api/main.py`、`docs/API.md`、`scripts/install.sh`、`docker/Dockerfile.rnas-api`

**验收标准**: 重启后 `ps aux | grep uvicorn | wc -l` = 1；所有 E2E 测试仍然通过；流量历史、抓包、SIM 等状态相关功能在单 worker 下行为一致

---

#### T1-A2: WebSocket 改为事件驱动 — 2.5d

**目标**: 替代固定 3s 全量推送，改为"状态变化才推送 + 心跳保活"。

**设计**:
```
[accel-cmd 查询] ──(背景线程, 动态间隔)──→ [状态快照缓存]
                                                 ↓
[WebSocket 连接]  ←──(事件总线)──────────  only changed fields
[WebSocket 连接]  ←──(ping/pong 30s)─────  心跳检测
```

**操作步骤**:

1. 新建 `web/api/event_bus.py`（进程内事件总线）:

```python
"""In-process event bus for WebSocket push"""
import asyncio
import json
import time
from typing import Any, Callable

# 状态快照
_state_snapshot: dict = {}
_subscribers: list[asyncio.Queue] = []
_last_push_time: float = 0

def register_subscriber() -> asyncio.Queue:
    q = asyncio.Queue()
    _subscribers.append(q)
    return q

def unregister_subscriber(q: asyncio.Queue):
    if q in _subscribers:
        _subscribers.remove(q)

def update_state(new_state: dict):
    """发布状态变更，仅推送变更字段"""
    global _state_snapshot, _last_push_time
    delta = _diff(_state_snapshot, new_state)
    if delta or time.time() - _last_push_time > 10:
        msg = json.dumps(delta or new_state)
        for q in _subscribers:
            q.put_nowait(msg)
        _state_snapshot.update(new_state)
        _last_push_time = time.time()

def _diff(old: dict, new: dict) -> dict:
    """返回变更的 key"""
    return {k: new[k] for k in new if old.get(k) != new[k]}
```

2. 新建 `web/api/state_collector.py`（后台采集线程，动态间隔）:

```python
"""Background state collector with adaptive interval"""
import threading

_active_collectors: dict[str, threading.Thread] = {}

def start_collector(interval: float = 3.0):
    """启动后台采集器。间隔自适应：空闲 5s，活跃 1s"""
    def _collect():
        idle_interval = 5.0
        active_interval = 1.0
        current = idle_interval
        from api.event_bus import update_state
        while True:
            state = _gather_state()
            # 如果有活动会话，加速采集
            current = active_interval if state.get("sessions_active", 0) > 0 else idle_interval
            update_state(state)
            time.sleep(current)
    t = threading.Thread(target=_collect, daemon=True)
    t.start()
    _active_collectors["default"] = t

def _gather_state() -> dict:
    """采集系统状态：调用 accel-cmd、读取系统文件"""
    # 复用现有的 status.py 逻辑
    ...
```

3. 修改 `web/api/main.py` 的 WebSocket 端点：

```python
@app.websocket("/api/ws")
async def ws_endpoint(ws: WebSocket, token: str = Query(None)):
    from api.auth import get_current_user
    user = await get_current_user(token)  # Phase 0 已实现
    await ws.accept()
    queue = event_bus.register_subscriber()
    try:
        # 发送当前快照
        await ws.send_json(event_bus._state_snapshot)
        # 事件循环
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30)  # 30s 心跳
                await ws.send_text(msg)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unregister_subscriber(queue)
```

4. 启动时注册：在 `main.py` 的 `@app.on_event("startup")` 中调 `start_collector()`

**涉及文件**: 新建 `web/api/event_bus.py`、`web/api/state_collector.py`；修改 `web/api/main.py`

**验收标准**: WebSocket 连接后，无状态变化时 > 5s 无推送；会话数变化时 < 1s 收到增量推送；30s 无推送时收到 `{"type":"ping"}`

---

#### T1-A3: 确认定时任务不会重复执行 — 1d

**目标**: 检查 `Scheduler.vue` 背后的后端定时任务逻辑，确保单 worker 下不会重复调度。

**操作步骤**:
1. 审计所有可能存在的 `threading.Timer`、`asyncio.create_task`、`schedule` 库等定时调用
2. 如有定时任务，确认它们只在 `@app.on_event("startup")` 中注册一次
3. 如有多个实例，用 `threading.Lock` 或文件锁防止重复执行
4. 若无定时任务（仅仅是前端触发的即时操作），文档记录确认结果

**涉及文件**: 审计 `web/api/` 下所有文件

**验收标准**: 无任何定时任务在单 worker 下重复执行两次以上

---

#### T1-A4: 快照恢复 + 健康检查回滚 — 1d

**目标**: 在 Phase 0-C3 的快照基础上，增加"apply 后健康检查失败 → 自动回滚"。

**操作步骤**:
1. 修改 `cmd/rnas-config/rnas_config.py` 的 apply 流程：

```python
def apply(root: Path):
    lock_fd = _acquire_lock()
    snapshot_name = f"auto-apply-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        # Step 1: 快照
        _create_snapshot(root, snapshot_name)
        
        # Step 2: 生成 + 干跑校验
        errors = _regenerate_and_validate_all(root)
        if errors:
            return {"status": "error", "errors": errors, "snapshot": snapshot_name}
        
        # Step 3: 应用
        _reload_services()
        time.sleep(2)  # 等服务稳定
        
        # Step 4: 健康检查
        if not _health_check():
            # 回滚
            _restore_snapshot(root, snapshot_name)
            _reload_services()
            return {"status": "error", "error": "Health check failed. Rolled back.", "snapshot": snapshot_name}
        
        return {"status": "ok", "snapshot": snapshot_name}
    finally:
        _release_lock(lock_fd)

def _health_check() -> bool:
    """检查管理通道和核心服务是否存活"""
    # 1. accel-ppp 进程存在
    # 2. 管理网络接口可达（避免防火墙把自己锁死）
    # 3. 关键服务端口监听
    checks = [
        subprocess.run(["pgrep", "-x", "accel-pppd"], capture_output=True).returncode == 0,
        # ... 其他检查
    ]
    return all(checks)
```

**涉及文件**: `cmd/rnas-config/rnas_config.py`

**验收标准**: apply 一个会使 accel-ppp 崩溃的配置后，系统自动回滚到快照状态，accel-ppp 恢复正常

---

### Sprint 1-B: 模块拆分 + 测试底座（5d）

#### T1-B1: 拆分 `extra.py`（756 行 → 6 个域路由）— 2d

**目标**: 上帝模块按职责域拆分为独立路由文件。

**拆分方案**:

| 原 extra.py 功能 | → | 新文件 | 预估行数 |
|---|---|---|---|
| 防火墙规则 CRUD + 排序 + 启停 | → | `routes/firewall.py` | ~200 |
| 接口查询与详情 + 流量历史 | → | `routes/interfaces.py` | ~150 |
| 抓包 start/stop/status | → | `routes/capture.py` | ~80 |
| 带宽测试 | → | `routes/bandwidth.py` | ~80 |
| 快速设置向导 | → | `routes/setup.py` | ~100 |
| 端口转发 + 健康报警 | → | `routes/port_forward.py` | ~100 |

**操作步骤**:
1. 逐个功能域提取到独立文件
2. 每个新文件使用独立的 `APIRouter(prefix="/api/xxx", tags=["xxx"])`
3. 在 `main.py` 中注册新 router
4. 更新 imports，确保所有现有路由正常
5. 运行 E2E 测试确认无回归

**涉及文件**: 新建 6 个 `web/api/routes/*.py`；修改 `web/api/main.py`；删除 `extra.py` 中已迁移的部分后重命名为 `extra_legacy.py`（暂存一周后删除）

**验收标准**: 全部 125 个 E2E 测试通过；`web/api/routes/` 下有 14 个文件（8 原有 + 6 新 - 1 删除），每个文件 < 250 行

---

#### T1-B2: 迁移 `server.py` → FastAPI（580 行 → 0）— 2d

**目标**: 删除遗留 HTTP 服务器，所有功能在 FastAPI 中统一。

**操作步骤**:
1. 审计 `server.py` 中哪些端点尚未在 FastAPI 实现
2. 逐个迁移到对应的 FastAPI 路由：
   - `/api/health` → 已在 `status.py`
   - 遗留的配置端点 → 合并到 `config.py` 或新拆分的域路由
   - 遗留的系统信息 → 合并到 `system.py`
3. 确认 `scripts/deploy-to-vm3.sh` 已改为启动 uvicorn
4. 删除 `web/server.py`
5. CI 加守卫：

```yaml
- name: Check server.py is deleted
  run: |
    if git grep -q "server.py" -- "web/" ":!web/api/main.py"; then
      echo "ERROR: server.py still referenced"
      exit 1
    fi
```

**涉及文件**: `web/server.py`（删除）、`web/api/routes/*.py`（并入功能）、`scripts/deploy-to-vm3.sh`、`.github/workflows/ci.yml`

**验收标准**: `web/server.py` 不存在；CI 守卫通过；原 `server.py` 提供的端点全部在 FastAPI 中可用

---

#### T1-B3: API 版本化 `/api/v1` — 0.5d

**目标**: 趁消费者少，先挂版本前缀，避免未来的 breaking change。

**操作步骤**:
1. 在 `main.py` 中统一加前缀：

```python
# 所有路由使用版本化前缀
app.include_router(status.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
# ... 其他路由

# 向后兼容：旧路径（无版本）重定向或直接挂载
# 可选：deprecated 模式下返回 Warning header
```

2. 或者更干净的做法——引入 `APIRouter(prefix="/api/v1")` 作为父路由：

```python
v1 = APIRouter(prefix="/api/v1")
v1.include_router(status.router)  # status.py 内的路由去掉 /api 前缀
# ...
app.include_router(v1)
```

3. 更新 `docs/API.md` 和前端 `BASE=...` 配置
4. 更新 E2E 测试的 base URL

**涉及文件**: `web/api/main.py`、所有 `routes/*.py`（去掉 `/api` 前缀）、`web/frontend/tests/e2e/*.spec.ts`（BASE URL）、`docs/API.md`

**验收标准**: 所有 API 在 `/api/v1/health`、`/api/v1/config/...` 下可用；E2E 测试通过

---

#### T1-B4: 路由层单测底座（`TestClient` + `monkeypatch`）— 1d

**目标**: 给高频路由 `config.py`、`aaa.py`、`tools.py` 补第一批单测，建立测试模式。

**操作步骤**:
1. 新建 `web/api/tests/conftest.py`：

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

@pytest.fixture
def client() -> TestClient:
    """创建带认证的测试客户端"""
    from api.main import app
    from api.auth import create_access_token
    token = create_access_token("test_admin", "admin")
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture
def mock_subprocess():
    """通用 subprocess.run mock"""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        yield mock
```

2. 新建 `web/api/tests/test_config.py`（示例）：

```python
def test_get_config_modules(client, mock_subprocess):
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    assert "modules" in response.json()

def test_apply_config_requires_auth():
    from api.main import app
    no_auth = TestClient(app)
    response = no_auth.post("/api/v1/config/apply")
    assert response.status_code == 401
```

3. 新建 `web/api/tests/test_tools.py`:

```python
def test_ping_valid_host(client, mock_subprocess):
    mock_subprocess.return_value.stdout = "3 packets transmitted, 3 received"
    response = client.get("/api/v1/tools/ping?host=127.0.0.1")
    assert response.status_code == 200
    assert "transmitted" in response.json()["output"]

def test_ping_rejects_flag_injection(client):
    response = client.get("/api/v1/tools/ping?host=-c%20evil")
    assert response.status_code == 400
```

4. 运行: `pytest -v web/api/tests/`

**涉及文件**: 新建 `web/api/tests/conftest.py`、`test_config.py`、`test_tools.py`、`test_aaa.py`；修改 `web/api/main.py`（确保可以被 TestClient 导入）

**验收标准**: 新增 15-20 个路由单测；全部通过；`pytest --cov=web/api/routes --cov-report=term` 显示 routes 覆盖率 > 60%

---

#### T1-B5: 生成器金样本测试 — 0.5d

**目标**: 为每个生成器建立 fixture INI → 期望输出 → 实际输出 → diff 测试。

**操作步骤**:
1. 新建 `cmd/rnas-config/tests/golden/` 目录：

```bash
cmd/rnas-config/tests/golden/
├── accel_ppp/
│   ├── input/                       # INI fixture
│   │   └── basic.conf
│   ├── expected/                    # 期望输出
│   │   └── accel-ppp-basic.conf
│   └── test_accel_ppp.py            # diff 断言
├── dnsmasq/
├── firewall/
└── ...
```

2. 每个测试模式：

```python
# test_accel_ppp.py
from pathlib import Path
from generators import GEN_MAP

def test_accel_ppp_basic():
    from core import parse_config
    input_txt = Path("golden/accel_ppp/input/basic.conf").read_text()
    expected = Path("golden/accel_ppp/expected/accel-ppp-basic.conf").read_text()
    tree = parse_config(input_txt)
    actual = GEN_MAP["accel-ppp"](tree)
    assert actual == expected, f"Diff:\n{_diff(actual, expected)}"
```

3. 至少覆盖 5 个核心生成器（accel-ppp, dnsmasq, firewall, qos, ipsec）
4. CI 中运行: `pytest -v cmd/rnas-config/tests/golden/`

**涉及文件**: 新建 `cmd/rnas-config/tests/golden/` 下 10+ 个文件；修改 `.github/workflows/ci.yml`

**验收标准**: 每个核心生成器至少 1 个金样本测试；全部通过；修改生成器逻辑后金样本测试失败能明确指出 diff

---

## Phase 1 里程碑检查清单

- [ ] `ps aux | grep uvicorn` 只有 1 个进程
- [ ] WebSocket 无状态变化时 > 5s 无推送
- [ ] WebSocket 会话数变化时 < 1s 收到增量推送
- [ ] 30s 无推送时收到 `{"type":"ping"}`
- [ ] apply 健康检查失败后自动回滚
- [ ] `extra.py` 已拆分为 6 个域路由，每个 < 250 行
- [ ] `server.py` 已删除，CI 守卫通过
- [ ] API 版本化 `/api/v1` 已生效
- [ ] 路由单测最少 20 个，覆盖率 > 60%
- [ ] 生成器金样本测试覆盖 5+ 个生成器
- [ ] 125 个 E2E 测试全部通过

---

## Phase 2: S 级补齐（第 2 个月）— 风险缓解优先

> **目标**: 完成审计/报警/配置漂移风险项 + 流量历史持久化 + E2E 测试工程化 + 文档收敛 + DevEx  
> **前置**: Phase 1 全部完成  
> **产出**: 审计日志可查、健康报警可邮件/webhook、配置漂移可感知、流量趋势图可用、E2E 不再 flaky、docs/ 已收敛  

### Sprint 2-A: 风险缓解（审计 + 报警 + 配置漂移）（4.5d）

> **目标**: 优先完成所有 Phase 2 中的风险缓解项目——审计、报警、配置漂移检测。可观测性（Prometheus/结构化日志）延后至 Phase 3。

#### T2-A1: 审计日志（who-when-what）— 2d

> ⚠️ **必须在 Phase 0 认证完成后才能做**——没有 "who" 的审计日志没有意义

**目标**: 记录关键配置变更的 who/when/what。

**Schema**:

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    username TEXT NOT NULL,
    action TEXT NOT NULL,        -- "config.apply", "config.modify", "firewall.add_rule", "session.disconnect", etc.
    target TEXT,                 -- 操作对象: "access.d.core", "firewall.filter.input", etc.
    diff TEXT,                   -- 变更前后的 JSON diff
    ip_address TEXT,             -- 请求来源 IP
    result TEXT NOT NULL         -- "success" or "error: <msg>"
);
```

**实现方案**:
1. 新建 `web/api/services/audit.py`：

```python
from fastapi import Request
from api.auth import get_current_user  # Phase 0 产物

async def record_audit(request: Request, action: str, target: str = None, diff: dict = None, result: str = "success"):
    user = await get_current_user(request.headers.get("Authorization", "").replace("Bearer ", ""))
    username = user["username"] if user else "anonymous"
    import sqlite3
    db = sqlite3.connect("/var/lib/rnas/audit.db")
    db.execute("INSERT INTO audit_log (username, action, target, diff, ip_address, result) VALUES (?,?,?,?,?,?)",
               [username, action, target, json.dumps(diff) if diff else None,
                request.client.host if request.client else "unknown", result])
    db.commit()
```

2. 在关键路由中埋点：

```python
@router.post("/api/v1/config/apply")
async def apply_config(request: Request, user=Depends(require_auth)):
    result = do_apply()
    audit.record_audit(request, "config.apply", result=result["status"])
    return result
```

3. 新增 API: `GET /api/v1/audit?limit=50` 返回最近 N 条审计记录

**涉及文件**: 新建 `web/api/services/audit.py`；修改 `web/api/routes/config.py`、`firewall.py`、`tools.py` 等关键路由

**验收标准**: apply 一次配置后 `GET /api/v1/audit` 能看到本次操作的记录，包含用户名、操作、时间、结果

---

#### T2-A2: 健康报警系统 — 1d

**目标**: 服务/系统异常时通过 webhook/邮件通知。

**实现方案**:
1. 新建 `web/api/services/alerts.py`：

```python
import httpx

ALERT_CHANNELS = {
    "webhook": os.environ.get("RNAS_ALERT_WEBHOOK"),
    "email_smtp": os.environ.get("RNAS_ALERT_EMAIL"),
}

async def send_alert(title: str, message: str, severity: str = "warning"):
    if ALERT_CHANNELS["webhook"]:
        async with httpx.AsyncClient() as c:
            await c.post(ALERT_CHANNELS["webhook"], json={"title": title, "message": message, "severity": severity})
```

2. 在后台健康检查线程中（Phase 1 的 `state_collector.py`），如果核心服务异常，触发报警：

```python
def _gather_state() -> dict:
    state = {...}
    if not _check_accel_ppp():
        asyncio.run(send_alert("accel-ppp down", "accel-ppp process not found", "critical"))
    return state
```

3. 前端 `SystemHealth.vue` 增加报警规则配置（CPU > 80%、disk > 90%、radius down 等）

**涉及文件**: 新建 `web/api/services/alerts.py`；修改 `web/api/state_collector.py`、`web/frontend/src/components/SystemHealth.vue`

**验收标准**: kill accel-ppp 后 30s 内收到 webhook 报警；恢复后收到 recovery 通知

---

#### T2-A3: 配置漂移检测 — 0.5d

**目标**: 若有人直接手改 `/etc/accel-ppp/accel-ppp.conf`，引擎能感知并告警。

**操作步骤**:
1. 修改 `cmd/rnas-config/generators.py`，在生成文件头部写入内容哈希：

```python
import hashlib

def _write_with_hash(path: Path, content: str):
    """写入配置文件，头部包含内容哈希"""
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    header = f"# RNAS-GENERATED: sha256={content_hash}\n"
    header += "# DO NOT EDIT MANUALLY — changes will be overwritten on next apply\n\n"
    path.write_text(header + content)
```

2. 在 `rnas_config.py` 增加 `status` 子命令——扫描所有生成文件，对比哈希：

```python
@cli.command()
@click.option("--root", default="/etc/rnas")
def status(root):
    """Check config drift"""
    tree = walk_config_tree(Path(root))
    drift = []
    for name, gen_func in GEN_MAP.items():
        output = gen_func(tree)
        target = _target_path(name)
        if target.exists():
            content = target.read_text()
            if not content.startswith("# RNAS-GENERATED:"):
                drift.append({"file": str(target), "reason": "Not RNAS-managed or header stripped"})
            else:
                # 解析头部哈希
                expected_hash = content.split("sha256=")[1].split("\n")[0]
                actual_content = "\n".join(content.split("\n")[2:])
                actual_hash = hashlib.sha256(actual_content.encode()).hexdigest()[:16]
                if expected_hash != actual_hash:
                    drift.append({"file": str(target), "reason": "Content modified outside RNAS"})
    if drift:
        click.echo(json.dumps(drift, indent=2))
        raise SystemExit(1)
    click.echo("All configs clean")
```

3. 在 `GET /api/v1/system/status` 中增加 `config_drift: bool` 字段

**涉及文件**: `cmd/rnas-config/generators.py`、`cmd/rnas-config/rnas_config.py`、`web/api/routes/system.py`

**验收标准**: 手动修改 `/etc/accel-ppp/accel-ppp.conf` 后，`rnas-config status` 返回非 0 并列出漂移文件；API `/system/status` 返回 `config_drift: true`

---

### Sprint 2-B: 持久化 + 测试工程化（5.5d）

> **目标**: 流量历史持久化已完成，E2E 测试不再 flaky，E2E CI 可运行，Vitest 起步

#### T2-B1: 流量历史 SQLite 持久化 — 2d

**目标**: 用 SQLite 环形缓冲 + 降采样实现流量趋势数据。

**Schema 设计**:

```sql
CREATE TABLE traffic_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface TEXT NOT NULL,
    rx_bytes INTEGER NOT NULL,
    tx_bytes INTEGER NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE traffic_hourly (
    interface TEXT NOT NULL, rx_avg REAL NOT NULL, tx_avg REAL NOT NULL,
    hour TEXT NOT NULL, PRIMARY KEY (interface, hour)
);
CREATE TABLE traffic_daily (
    interface TEXT NOT NULL, rx_avg REAL NOT NULL, tx_avg REAL NOT NULL,
    date TEXT NOT NULL, PRIMARY KEY (interface, date)
);
CREATE TRIGGER cleanup_traffic_history AFTER INSERT ON traffic_history
BEGIN
    DELETE FROM traffic_history WHERE timestamp < datetime('now', '-24 hours');
END;
```

**实现方案**:
1. 新建 `web/api/services/traffic_store.py`：

```python
import sqlite3
from pathlib import Path

DB_PATH = Path("/var/lib/rnas/traffic.db")

class TrafficStore:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as db:
            db.executescript(SQL_SCHEMA)
    def insert_sample(self, iface: str, rx: int, tx: int): ...
    def get_history(self, iface: str, period: str = "5m") -> list[dict]: ...
    def _run_downsample(self): ...
```

2. 修改 `traffic.py` 的后台采集线程：采集后同时写入 SQLite
3. 新增 API: `GET /api/v1/traffic/history?interface=ens33&period=5m`
4. 前端 `TrafficMonitor.vue` 改为从该 API 拉取历史数据

**涉及文件**: 新建 `web/api/services/traffic_store.py`；修改 `web/api/services/traffic.py`、`web/api/routes/interfaces.py`、`web/frontend/src/components/TrafficMonitor.vue`

**验收标准**: 运行 6 小时后 `GET /api/v1/traffic/history` 返回 5m 粒度数据点；24 小时后原始数据自动清理，降采样数据保留

---

#### T2-B1b: 证书管理前端完善 — 1d

**目标**: 前端 CertManager.vue 完成完整的证书列表/生成/下载/删除功能。

**操作步骤**:
1. 完善 `web/frontend/src/components/CertManager.vue`（当前只有 generate 弹窗）：证书列表表格 (Name/Type/Size/Expiry/Actions)、Download/Delete 按钮、生成前校验
2. 确保后端 `system.py` 的证书端点全部可用

**涉及文件**: `web/frontend/src/components/CertManager.vue`、`web/api/routes/system.py`

**验收标准**: 完整的 CRUD——生成证书 → 列表可见 → 可下载 → 可删除

---

#### T2-B2: E2E 测试去 flaky — 2d

**目标**: 消除 E2E 测试的三个不稳定因素。

**操作步骤**:

1. **去 `waitForTimeout`（1d）**：
   - 全局搜索 `waitForTimeout`，替换为 Playwright 自动等待断言：
   ```typescript
   // 改前
   await page.waitForTimeout(1500);
   // 改后
   await expect(page.locator('.sessions-section, .empty-state')).toBeVisible({timeout: 5000});
   ```
   - 每个替换后运行 3 次确认不 flaky

2. **测试夹具造会话（0.5d）**：
   - 新建 `tests/e2e/fixtures.ts`：
   ```typescript
   import { request } from '@playwright/test';
   
   async function createTestSession(apiBase: string, token: string) {
       // 通过 API 触发 sim/connect，或直接通过 SSH mock 创建会话
       const ctx = await request.newContext({
           baseURL: apiBase,
           extraHTTPHeaders: { Authorization: `Bearer ${token}` }
       });
       await ctx.post('/api/v1/sim/connect', { data: { protocol: 'pppoe', username: 'testuser', password: 'testpass' } });
       await ctx.dispose();
   }
   ```
   - session 相关测试在 beforeAll 中调 fixture，消除 4 个跳过

3. **随机端口（0.5d）**：
   - `playwright.config.ts` 中改用随机空闲端口：
   ```typescript
   import { createServer } from 'net';
   
   function getFreePort(): Promise<number> { ... }
   const PORT = await getFreePort();
   ```

**涉及文件**: 全部 19 个 `tests/e2e/*.spec.ts`、`playwright.config.ts`

**验收标准**: `waitForTimeout` 调用数为 0；4 个跳过用例全部通过；连续运行 5 次零 flaky 失败

---

#### T2-B3: E2E 接 docker-compose CI — 1d

**目标**: CI 每晚能用 docker-compose 全栈环境跑 E2E。

**操作步骤**:
1. 修改 `.github/workflows/ci.yml` 或新建 `.github/workflows/e2e-nightly.yml`：

```yaml
name: E2E Nightly
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨 2 点
  workflow_dispatch:

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start test environment
        run: docker compose -f docker/docker-compose.yml up -d --wait
      - name: Run E2E tests
        run: |
          cd web/frontend
          npx playwright test
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: web/frontend/playwright-report
```

2. 确保 docker-compose 环境不依赖特定实验室 IP（192.168.0.x）
3. 如果某些测试必须依赖真实 CPE，用 `test.skip(process.env.CI)` 标记

**涉及文件**: `.github/workflows/e2e-nightly.yml`（新建）、`docker/docker-compose.yml`（可能需要调整）

**验收标准**: CI nightly 流水线通过，报告可下载查看

---

#### T2-B4: 前端 Vitest 起步 — 1d

**目标**: 给 3-5 个核心组件补单元测试，建立测试模式。

**操作步骤**:
1. 安装: `npm install -D vitest @vue/test-utils jsdom`
2. 配置 `vitest.config.ts`
3. 给以下组件写第一批测试：
   - `StatusCard.vue`（props 渲染）
   - `SessionDetail.vue`（computed 逻辑）
   - `QueueManager.vue`（表单验证）
   - `TrafficMonitor.vue`（数据格式化）
4. CI 中加入：`npx vitest --run`

**涉及文件**: 新建 `web/frontend/src/components/__tests__/` 下 3-5 个测试文件；`vitest.config.ts`；`.github/workflows/ci.yml`

**验收标准**: 至少 10 个 Vitest 测试通过；CI 中包含 `npx vitest --run` 步骤

---

### Sprint 2-C: 文档收敛 + DevEx（3d）

> **目标**: 10+ 份规划类文档收敛为一份 ROADMAP.md，建立 ADR、运行手册、编辑器规范、一键开发环境

#### T2-C1: 文档收敛 — 1d

**目标**: 10+ 份规划类文档收敛为一份 `ROADMAP.md`，其余归档。

**操作步骤**:
1. 新建 `docs/archive/` 目录
2. 移入归档：
   - `docs/GAP_ANALYSIS.md`、`docs/COMPETITIVE_ANALYSIS.md`、`docs/rnas-improvement-report.md`
   - `docs/plans/2026-04-21-*.md`（4 份）、`docs/plans/2026-04-26-*.md`（3 份）
   - `docs/designs/`（4 份）
3. 新建 `docs/ROADMAP.md`，包含：当前状态摘要、已完成 vs 计划中 vs 暂缓的功能、Phase 规划链接、ADR 链接
4. 新建 `docs/adr/`，写入关键决策：
   - `adr/001-choose-uci-config-format.md` — 为何用 UCI 格式
   - `adr/002-choose-sqlite-for-state.md` — 为何用 SQLite
   - `adr/003-single-worker-decision.md` — 为何单 worker
5. 新建 `docs/runbook.md` 运行手册：启动/停止/重启流程、常见故障排查、回滚步骤、备份/恢复

**涉及文件**: 新建 5 个文档；移动 10+ 个文档到 `archive/`

**验收标准**: `docs/` 下只有 5-6 个活跃文档；新开发者能在 30 分钟内读完 `docs/` 全部活跃文档并开始开发

---

#### T2-C2: `.editorconfig` + 开发体验完善 — 1d

**操作步骤**:
1. 新建 `.editorconfig`：统一缩进、换行符、字符编码
2. 从 OpenAPI schema 自动生成 TS 类型（`openapi-typescript`）
3. `Makefile` / `docker-compose.dev.yml` 一键启动开发环境
4. 可选：`devcontainer.json` 提供 VS Code 开发容器配置
5. `husky` + `commitlint` 强制 commit 规范

**涉及文件**: 新建 4+ 个配置文件

**验收标准**: `make dev` 或 `docker compose -f docker-compose.dev.yml up` 一键启动前后端；`git commit` 自动运行 pre-commit 检查

---

## Phase 2 里程碑检查清单

- [ ] 审计日志记录 config apply / firewall change / session disconnect / snapshot 操作
- [ ] 健康检查异常时收到 webhook 报警
- [ ] 配置漂移可检测：手动改文件后 `rnas-config status` 返回非 0
- [ ] 流量历史 5m/1h/1d 粒度可用
- [ ] 证书管理完整 CRUD
- [ ] E2E `waitForTimeout` 清零，连续 5 次运行零 flaky
- [ ] E2E nightly CI 流水线通过
- [ ] Vitest 至少 10 个测试通过
- [ ] `docs/archive/` 已建立，活跃文档 < 6 个
- [ ] `docs/adr/` 包含 3+ 决策记录
- [ ] `docs/runbook.md` 覆盖基本运维操作
- [ ] `.editorconfig` + `pre-commit` 钩子生效

---

## Phase 3: 差异化（季度级）— 测试装置定位

> **目标**: 将 RNAS 从"又一个 NAS 管理面"升级为"NAS 协议测试装置"——开源生态中几乎空白的位置  
> **前置**: Phase 0 + Phase 1 完成，Phase 2 至少完成 T2-A1/T2-A2  
> **产出**: netns 压测框架可用、YAML 场景 DSL v1 可用、RBAC 完成、可观测性就绪、首个带 CHANGELOG 的版本发布  

### Epic 3-A: netns 批量 CPE 压测框架（3-4w）

**目标**: 用 Linux network namespace 在单机上模拟数百个 PPPoE 并发会话，让"压力测试"名副其实。

**架构**:
```
┌────────────────────────────────────┐
│           RNAS 主机                │
│                                    │
│  ┌─────────────────────────┐       │
│  │  压测管理器 (Python)     │       │
│  │  - 创建/销毁 netns       │       │
│  │  - 批量启动 pppd         │       │
│  │  - 断言 RADIUS 计费记录  │       │
│  │  - 收集性能指标           │       │
│  └──────────┬──────────────┘       │
│             │                      │
│  ┌──────────┴──────────┐           │
│  │  虚拟 CPE 集群       │           │
│  │  ┌────────┐ ┌──────┐ │           │
│  │  │ netns  │ │ netns│ │  ... × N  │
│  │  │ cpe-01 │ │cpe-02│ │           │
│  │  │ pppd   │ │ pppd │ │           │
│  │  └───┬────┘ └──┬───┘ │           │
│  │      └────┬────┘     │           │
│  │      veth bridge      │           │
│  └───────────┬───────────┘           │
│              │                       │
│       accel-ppp (被测)               │
│              │                       │
│       FreeRADIUS (被测)              │
└──────────────────────────────────────┘
```

**实现方案**:

1. **新建 `cmd/rnas-test/` 子项目**（3-4w）

```python
# cmd/rnas-test/stress_engine.py
class StressEngine:
    def __init__(self, cpe_count: int = 100):
        self.cpe_count = cpe_count
    
    def setup_network(self):
        """创建 bridge + veth pairs"""
        for i in range(self.cpe_count):
            ns_name = f"cpe-{i:03d}"
            subprocess.run(["ip", "netns", "add", ns_name])
            subprocess.run(["ip", "link", "add", f"veth-{ns_name}", "type", "veth", "peer", f"vpeer-{ns_name}"])
            subprocess.run(["ip", "link", "set", f"vpeer-{ns_name}", "netns", ns_name])
            # ... IP 分配、路由设置
    
    def start_pppoe_session(self, ns_name: str, username: str, password: str):
        """在 netns 内启动 pppd"""
        subprocess.run(["ip", "netns", "exec", ns_name, "pppd", "call", "rnas-pppoe",
                       "user", username, "password", password])
    
    def wait_for_sessions(self, count: int, timeout: int = 30):
        """轮询 accel-cmd 等待会话数达到目标"""
        ...
    
    def assert_radius_acct(self, min_records: int):
        """验证 FreeRADIUS 计费记录 >= N 条"""
        ...
    
    def teardown(self):
        """清理所有 netns 和 veth"""
        ...
```

2. **CLI 接口**:

```bash
rnas-test stress --cpe-count 100 --proto pppoe --username-prefix testuser --password testpass
rnas-test stress --cpe-count 500 --rate 10/s --duration 60s  # 速率控制
```

3. **Web UI 集成**（`StressTest.vue`）: 设置并发数/协议/速率/持续时间 → 运行 → 实时图表

**涉及文件**: 新建 `cmd/rnas-test/`（整个子项目）；新建 `web/frontend/src/components/StressTest.vue`

**验收标准**: 单机可模拟 200+ PPPoE 并发会话；压测过程中 API 响应时间 < 2s；压测报告输出 JSON 格式（session 建立时间 / RADIUS 响应时间 / accel-ppp CPU / 内存）

---

### Epic 3-B: YAML 场景 DSL（4-6w）

**目标**: 用声明式 YAML 描述测试场景（拓扑 + 动作 + 断言），让 RNAS 成为 CI 流水线里的"NAS 协议测试装置"。

**DSL 设计**:

```yaml
# scenarios/pppoe-batch-stress.yaml
name: PPPoE 批量并发压力测试
description: 100 用户 PPPoE 并发拨号 + RADIUS 认证 + 会话验证
version: "1.0"

topology:
  cpe_count: 100
  auth:
    type: pap
    radius_server: "${RADIUS_AUTH_SERVER:-192.168.0.202}:1812"
    secret: "${RADIUS_SECRET}"
  
  credentials:
    prefix: testuser
    password: testpass

actions:
  - name: "建立 PPPoE 会话"
    command: connect
    protocol: pppoe
    target: all
    rate: 5/s           # 每秒建立 5 个会话
    
  - name: "等待所有会话建立"
    command: wait
    timeout: 60s
    condition:
      sessions_active: 100
  
  - name: "验证 RADIUS 认证"
    command: assert
    checks:
      - radius_auth_accepted: 100
      - radius_acct_start: 100
      - avg_auth_latency_ms < 50

  - name: "验证会话详情"
    command: assert
    checks:
      - sessions_by_proto.pppoe == 100
      - sessions_by_state.active == 100
      - ip_pool_usage_percent > 0

  - name: "断开所有会话"
    command: disconnect
    target: all
    rate: 10/s

  - name: "验证清理"
    command: assert
    checks:
      - sessions_active == 0
      - radius_acct_stop == 100

report:
  format: [junit, html, json]
  output: /var/log/rnas/scenarios/
```

**实现方案** (4-6w):

1. **解析器 `cmd/rnas-test/scenario_parser.py`**: YAML → AST → 动作序列
2. **执行引擎 `cmd/rnas-test/scenario_engine.py`**: 顺序执行动作，实时收集结果
3. **断言器 `cmd/rnas-test/assertions.py`**: 支持 `==`、`>`、`<`、`contains`、`starts_with` 等操作符
4. **报告生成器 `cmd/rnas-test/reporters.py`**: JUnit XML（CI 集成）、HTML（人工查看）、JSON（自动化消费）
5. **CLI**:

```bash
rnas-test run scenario scenarios/pppoe-batch-stress.yaml
rnas-test run scenario scenarios/ --format junit  # 批量运行 → CI
```

6. **Web UI**: 场景编辑器 + 历史结果浏览

**涉及文件**: 新建 `cmd/rnas-test/scenario_parser.py`、`scenario_engine.py`、`assertions.py`、`reporters.py`、`scenario_models.py`；新建 `web/frontend/src/components/ScenarioEditor.vue`

**验收标准**: `rnas-test run scenario` 执行 YAML 场景并输出 JUnit XML；CI 中能运行这些场景并基于结果决定 pass/fail；至少 5 个预定义场景（PPPoE / L2TP / PPTP / 混合 / 压力）

---

### Epic 3-C: RBAC + 版本发布（2-3w）

**RBAC 三层角色**:
- **管理员** (admin): 全权限
- **操作员** (operator): 查看 + 执行诊断/配置（不含系统设置/证书）
- **只读** (viewer): 仅查看，不可修改

**实现方案**:
1. 在 `web/api/auth.py` 中扩展 JWT payload 携带 role，所有需要授权的端点用 `Depends(require_role("admin"))` 做权限检查
2. 新建 `web/api/routes/admin.py` — 用户管理端点 (list/add/remove/change-role)
3. 前端根据 role 隐藏/禁用按钮和页面入口

**版本发布**:
1. 语义化版本 `v4.0.0`
2. `CHANGELOG.md` 记录本次 Phase 0-3 的全部变更
3. Git tag + GitHub Release
4. Docker 镜像推送

---

### Epic 3-D: 可观测性体系（4-5w）

> **目标**: 完整的 Prometheus + Grafana + OpenTelemetry 三支柱 + 结构化日志。此 Epic 排最后，依赖前端所有功能稳定。

#### T3-D1: Prometheus metrics 基础（2d）

**目标**: 暴露 `/metrics` 端点，接入 Prometheus 基础指标。

**操作步骤**:
1. 安装: `pip install prometheus-fastapi-instrumentator`
2. 在 `main.py` 中：

```python
from prometheus_fastapi_instrumentator import Instrumentator
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")
```

3. 增加业务指标：

```python
from prometheus_client import Gauge, Histogram, Counter
sessions_active = Gauge("rnas_sessions_active", "Active PPP sessions")
apply_duration = Histogram("rnas_apply_duration_seconds", "Config apply duration")
subprocess_errors = Counter("rnas_subprocess_errors_total", "Subprocess errors", ["command"])
```

**涉及文件**: `web/api/main.py`、`web/api/routes/config.py`、`web/api/services/traffic.py`

**验收标准**: `GET /metrics` 返回 Prometheus 格式指标；`rnas_sessions_active` 如实反映当前会话数

---

#### T3-D2: 结构化日志（structlog + trace_id）（1d）

**目标**: 用 structlog 输出 JSON 日志，请求串联 trace_id。

**操作步骤**:
1. 新建 `web/api/logging_config.py`：

```python
import structlog, uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if os.environ.get("RNAS_ENV") == "development"
        else structlog.processors.JSONRenderer(),
    ],
)
logger = structlog.get_logger()
def add_request_id(rid: str = None): request_id_ctx.set(rid or str(uuid.uuid4())[:8])
def get_logger(): return logger.bind(request_id=request_id_ctx.get())
```

2. 在 FastAPI middleware 中注入 trace_id
3. 全库 `print()` → `get_logger().info()`，`traceback.print_exc()` → `get_logger().exception()`

**验收标准**: 生产日志为 JSON 行；同一请求的日志行包含相同 trace_id

---

#### T3-D3: Grafana + OpenTelemetry + 告警（2-3w）

1. Grafana dashboard 模板（`dashboards/rnas-overview.json`）
2. OpenTelemetry SDK 集成：`pip install opentelemetry-instrumentation-fastapi`
3. 追踪链路：`前端 fetch → API → subprocess.run → accel-cmd → accel-ppp` 全链路 trace_id 传递
4. 告警规则: `prometheus-alerts.yml`
5. `docker-compose.monitoring.yml`: Prometheus + Grafana + Loki 三件套

---

## Phase 3 里程碑检查清单

- [ ] `rnas-test stress --cpe-count 200` 成功模拟 200 并发会话
- [ ] 5 个 YAML 场景模板可用
- [ ] `rnas-test run scenario` 输出 JUnit XML 可在 CI 中集成
- [ ] RBAC 三层角色生效（admin/operator/viewer）
- [ ] CHANGELOG.md + Git Tag v4.0.0 + GitHub Release
- [ ] `GET /metrics` 返回 Prometheus 格式指标
- [ ] Grafana dashboard 展示核心指标
- [ ] OpenTelemetry 追踪 "前端 → API → subprocess" 全链路
- [ ] 生产日志 JSON 格式 + trace_id 串联
- [ ] `docker-compose.monitoring.yml` 一键启动监控栈

---

## 依赖关系图

```
Phase 0 ──────────────────────────────────────────────┐
│                                                      │
├─ Sprint 0-A (工程基础) ──────┐                       │
│  T0-A1: 提交未提交文件        │                       │
│  T0-A2: CI 质量门禁          │                       │
│  T0-A3: pre-commit 钩子      │                       │
│  T0-A4: 暴露 OpenAPI 文档     │                       │
│                              ↓                       │
├─ Sprint 0-B (安全防火墙) ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│  T0-B1: JWT 认证 ──────────┼──→ T0-B2: 禁用WebTerminal
│  T0-B3: 关 CORS             │                       │
│  T0-B4: db_query 去 shell   │     Phase 1 ─────────┐│
│  T0-B5: flag 注入防护       │     │                  ││
│  T0-B6: HTTP client+timeout │     ├─ Sprint 1-A     ││
│                              │     │  T1-A1: wkr↓1  ││
├─ Sprint 0-C (配置引擎安全阀) ─│─ ─ ┤  T1-A2: WS事件  ││
│  T0-C1: apply 预校验         │     │  T1-A3: 定时器  ││
│  T0-C2: apply 并发锁         │     │  T1-A4: 回滚    ││
│  T0-C3: apply 自动快照 ──────┼──→  │                  ││
│                              │     ├─ Sprint 1-B     ││
│                              │     │  T1-B1: 拆分    ││
│                              │     │  T1-B2: 删srv.py││
│                              │     │  T1-B3: /api/v1 ││
│                              │     │  T1-B4: 路由单测││
│                              │     │  T1-B5: 金样本  ││
│                              │     └────────┬────────┘│
│                              │              ↓         │
│                              │     Phase 2 ──────────┤│
│                              │     │                  ││
│                              │     ├─ Sprint 2-A     ││
│                              │     │  T2-A1: 审计 ←──┼── 依赖 Phase 0 认证
│                              │     │  T2-A2: 报警    ││
│                              │     │  T2-A3: 漂移检测││
│                              │     │                  ││
│                              │     ├─ Sprint 2-B     ││
│                              │     │  T2-B1: 流量历史││
│                              │     │  T2-B1b:证书前端││
│                              │     │  T2-B2: E2E去flaky│
│                              │     │  T2-B3: E2E CI  ││
│                              │     │  T2-B4: Vitest  ││
│                              │     │                  ││
│                              │     ├─ Sprint 2-C     ││
│                              │     │  T2-C1: 文档收敛││
│                              │     │  T2-C2: DevEx   ││
│                              │     └────────┬────────┘│
│                              │              ↓         │
│                              │     Phase 3 ──────────┤│
│                              │     │                  ││
│                              │     ├─ 3-A: netns 压测││
│                              │     ├─ 3-B: YAML DSL  ││
│                              │     ├─ 3-C: RBAC+发布 ││
│                              │     └─ 3-D: 可观测性   ││
│                              └────────────────────────┘│
└───────────────────────────────────────────────────────┘
```

**关键依赖链**:
- `T0-B1 (认证)` → `T0-B2 (禁用WebTerminal)` → `T2-A1 (审计日志)`
- `T0-C3 (apply快照)` → `T1-A4 (apply回滚)`
- `T1-A1 (worker降1)` → `T1-A2 (WS事件驱动)`
- `T1-B1 (拆分extra.py)` + `T1-B4 (路由单测)`（可并行）

---

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 认证改造导致 E2E 测试大面积失败 | 高 | 中 | E2E 修改 BASE → 带 token 的 authenticated client；改造时并行维护旧路径 |
| worker 降 1 后性能瓶颈 | 中 | 低 | 管理面负载极低（< 10 req/s），单 worker 足够；若有性能问题，先做状态外置再恢复多 worker |
| apply 回滚不完整（部分配置已生效） | 高 | 中 | 保守回滚策略——仅重置 accel-ppp + nftables 主配置；其他服务失败可由运维手动恢复 |
| E2E flaky 修复后引入新 flaky | 中 | 中 | 每次改动后--repeat-each=5 运行；CI nightly 持续监控 |
| netns 压测框架代码量大 | 高 | 中 | 最小可行版本 MVP（单协议 + 100 CPE + JSON 报告）先交付，再逐步扩展 |
| YAML DSL 范围蔓延（语法过于复杂） | 中 | 高 | v1.0 仅支持 sequence 型动作 + 简单条件断言；不支持循环/条件分支/并行 |

---

## 成功度量

| 指标 | 当前 | Phase 0 目标 | Phase 1 目标 | Phase 2 目标 | Phase 3 目标 |
|------|------|-------------|-------------|-------------|-------------|
| `grep shell=True web/` | 1 (db_query) | 0 | 0 | 0 | 0 |
| API 认证覆盖率 | 0% | 100% (除health) | 100% | 100% | 100% |
| WebTerminal 默认状态 | 开放 | Feature Flag 禁用 | 禁用 | 可选启用 | 可选启用 |
| CORS 生产模式 | `allow_origins=["*"]` | 关闭 | 关闭 | 关闭 | 关闭 |
| 路由单测覆盖率 | 0% | — | > 60% | > 80% | > 80% |
| E2E 跳过用例 | 4 | 4 | 4 | 0 | 0 |
| E2E flaky 率 | 未知 | 未知 | < 5% | 0% | 0% |
| apply 有预校验 | 否 | **是** | 是 | 是 | 是 |
| apply 有回滚 | 否 | 否 | **是** | 是 | 是 |
| 配置漂移检测 | 否 | 否 | 否 | **是** | 是 |
| 审计日志 | 否 | 否 | 否 | **是** | 是 |
| 健康报警 | 否 | 否 | 否 | **是** | 是 |
| 流量历史趋势图 | 否 | 否 | 否 | **是** | 是 |
| 证书管理 CRUD | 部分 | 部分 | 部分 | **完整** | 完整 |
| Prometheus metrics | 否 | 否 | 否 | 否 | **是** |
| 结构化日志 (JSON+trace_id) | 否 | 否 | 否 | 否 | **是** |
| Grafana dashboard | 否 | 否 | 否 | 否 | **是** |
| OpenTelemetry 全链路追踪 | 否 | 否 | 否 | 否 | **是** |
| 批量压测能力 | SSH to 1 CPE | SSH to 1 CPE | SSH to 1 CPE | SSH to 1 CPE | **netns 200+ 并发** |
| YAML 场景 DSL | 否 | 否 | 否 | 否 | **v1.0** |
| RBAC 角色 | 0 | 0 | 0 | 0 | 3 (admin/ops/viewer) |

---

*本计划基于 RNAS 交接报告 v3.0 + 第三方深度分析报告制定。*  
*每个 Phase 里程碑检查清单是验收的唯一标准——清单全勾才可进入下一阶段。*  
*计划随开发进展动态更新，重大范围变更记录在 `docs/adr/`。*
