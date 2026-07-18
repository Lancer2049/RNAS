# RNAS AGENTS — AI Agent Context File

## Project Identity

RNAS is a **standalone NAS simulation platform** for x86 Linux/VM — not an OpenWrt distribution. It fuses accel-ppp with standard Linux networking under a unified `/etc/rnas/` config tree.

## Architecture (v2 Fusion Model)

```
 /etc/rnas/*.conf  →  rnas-config (Python)  →  native daemon configs
     ↓                                              ↓
 rnas-api (FastAPI)  ←──  accel-cmd  ←──  accel-ppp/dnsmasq/nftables
     ↓
 Vue.js SPA Dashboard  (web/frontend/)
```

- **Base OS**: Debian/Ubuntu/UOS x86_64, NOT OpenWrt firmware
- **Service mgmt**: systemd units in `systemd/`
- **Config**: INI-style UCI-format files in `/etc/rnas/`
- **OpenWrt**: secondary target only (package/ directory preserved)

## Key Directories

| Path | Purpose |
|------|---------|
| `cmd/rnas-config/rnas_config.py` | Config engine: parser + accel-ppp generator |
| `web/api/` | FastAPI: status, sessions, config endpoints |
| `web/frontend/` | Vue.js 3 SPA dashboard |
| `web/frontend/src/components/` | All Vue.js 3 page components |
| `web/frontend/tests/e2e/` | Playwright E2E tests (browser only) |
| `configs/` | `/etc/rnas/` config templates (14 files) |
| `systemd/` | systemd units: target + services |
| `tools/` | CLI testing tools (coa-test, acct-verify, etc.) |
| `tests/` | Integration tests |
| `scripts/install.sh` | One-command installer |

## Frontend Components (web/frontend/src/components/)

| Component | Route | Purpose |
|-----------|-------|---------|
| `App.vue` | root | Dashboard layout, sidebar, hash routing, toast notifications |
| `ConfigEditor.vue` | config | Category sidebar + search config editor |
| `ProtocolConfig.vue` | protocols | 5 access protocol config forms (PPPoE/L2TP/PPTP/SSTP/IPoE) |
| `ServicesConfig.vue` | services | VPN service configs with status bar |
| `IPManager.vue` | ip | 8-tab IP management (ARP/DHCP/Filter/NAT/Mangle/Routes/Addresses/Static) |
| `SessionsTable.vue` | sessions | Active PPPoE/L2TP session management |
| `QueueManager.vue` | queues | HTB/CAKE/Simple QoS with ceil/burst/prio |
| `TrafficMonitor.vue` | traffic | Interface rate chart (5m/1h/1d) + history |
| `ToolsPage.vue` | tools | 7-tab diagnostics (Ping/Trace/DNS/RADIUS/CoA/BW/Capture) |
| `WebTerminal.vue` | terminal | xterm.js + WebSocket shell |
| `SystemLog.vue` | system | Service/level filtered log viewer |
| `CertificateManager.vue` | certs | TLS certificate list + generate |
| `QuickSetup.vue` | setup | 3-step wizard (Network→RADIUS→Confirm) |
| `PortForward.vue` | firewall | Port forwarding wizard |
| `ConfigSnapshots.vue` | snapshots | Config snapshot list/create/restore/diff |
| `HealthAlerts.vue` | alerts | Health alert management |
| `RADIUSUsers.vue` | radius-users | RADIUS user CRUD |
| `InterfaceDetail.vue` | interface/:name | Per-interface stats + sessions |

## Test Environment (Current)

```
Host (WSL2)    —  VMware NAT, port forwarding on 192.168.0.x LAN
RNAS API       —  127.0.0.1:8099  (FastAPI, local for Playwright tests)
Frontend       —  Vue.js 3 SPA served via FastAPI static mount
RADIUS         —  192.168.0.202:1812, secret=testing123
accel-ppp      —  local VM, PPPoE/L2TP/PPTP/SSTP server
```

Test user: `testuser` / `testpass` in FreeRADIUS radcheck.

## Hard Rules (ALL agents MUST follow)

### 1. Integration Tests MUST Be Browser-UI-Based
- **NEVER write tests that call backend API directly** (no `request.get()`, no `fetch()`)
- All integration tests must use Playwright `page` object: click buttons, fill forms, navigate, verify through UI feedback
- Test like a human: configure through web forms → click Apply → check result message / page state
- Exception: health-check pings (`/api/health`) are allowed for setup/teardown

### 2. E2E Test Files
- Add new tests to `web/frontend/tests/e2e/`
- Always use `page.goto(BASE)` with `BASE = 'http://127.0.0.1:8099'`
- Use `page.locator('.rnas-sidebar').getByText('...')` for sidebar navigation
- Use `page.waitForTimeout(500)` after navigation for Vue async rendering
- Verify success through page element feedback (message text, status changes, UI state)

### 3. Frontend Stack
- Vue.js 3 SPA, hash routing (`#/sessions`, `#/ip`, `#/protocols`, etc.)
- Components lazy-loaded via `defineAsyncComponent`
- RouterOS dark theme (GitHub-dark palette)
- Sidebar selector: `nav.rnas-sidebar`
- Wait for async components: `page.waitForTimeout(500)` after click

## Conventions

- Python code: `cmd/rnas-config/` and `web/api/`
- Shell scripts: must pass `shellcheck`, use `set -e`
- Config files: INI format, `${VAR:-default}` for secrets
- No hardcoded passwords — use `${RNAS_RADIUS_SECRET}` env var
- Git: `node_modules/`, `dist/`, `__pycache__/` in `.gitignore`
