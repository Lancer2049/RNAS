# RNAS v2 Core Platform — Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use the appropriate execution skill (`executing-plans` or `subagent-driven-development`) to implement this plan.

**Goal:** Build the core RNAS v2 platform — unified config engine, systemd service orchestration, and web console — replacing v1's OpenWrt-dependent architecture with a standalone x86 Linux native design.

**Architecture:** Three-layer: `/etc/rnas/` config tree → `rnas-config` engine (reader/generator/applier) → `rnas-api` + Vue.js SPA dashboard. Services managed via systemd. v1 accel-ppp Lua/UCI artifacts absorbed as templates.

**Tech Stack:** Go (rnas-config CLI), Python/FastAPI (rnas-api), Vue.js 3 (frontend), systemd (service mgmt), Bash (installer). Reuses: accel-ppp binaries, existing test tools.

**Design Reference:** `docs/plans/2026-04-26-rnas-full-platform-design.md`

---

## Task Dependency Graph

```
Task 1 ──► Task 2 ──► Task 3 ──┐
                               ├──► Task 5 (integration)
Task 4 ────────────────────────┘
                               ┌──► Task 6.1
Task 5 ──► Task 6 ──► Task 7 ─┤
                               └──► Task 6.2
```

---

### Task 1: Define `/etc/rnas/` Config Schema & Templates

**Files:**
- Create: `configs/rnas.conf`
- Create: `configs/access.d/core.conf`
- Create: `configs/access.d/radius.conf`
- Create: `configs/access.d/ppp.conf`
- Create: `configs/access.d/pppoe.conf`
- Create: `configs/access.d/ipoe.conf`
- Create: `configs/access.d/l2tp.conf`
- Create: `configs/access.d/pptp.conf`
- Create: `configs/access.d/sstp.conf`
- Create: `configs/access.d/ip-pool.conf`
- Create: `configs/access.d/coa.conf`
- Create: `configs/network.d/interfaces.conf`
- Create: `configs/network.d/dhcp.conf`
- Create: `configs/network.d/firewall.conf`

**Step 1: Port v1 UCI schema to new INI-style format**

Port from `root/etc/config/rnas` into individual `.conf` files in `configs/access.d/`. Use INI-style `[section "name"]` format with `key = value` pairs. Replace all `testing123` with `${RNAS_RADIUS_SECRET}` placeholder.

**Step 2: Create network config templates**

`interfaces.conf`: LAN bridge with PPP pool subnet (192.168.100.1/24).
`dhcp.conf`: DHCP scope 192.168.100.100-200 for IPoE clients.
`firewall.conf`: NAS zone allowing PPP traffic, CoA port 3799.

**Step 3: Verify task**
Run: `grep -r 'testing123' configs/` should return **zero** matches (all replaced with `${RNAS_RADIUS_SECRET}`).
Run: `ls configs/access.d/ | wc -l` should return `10`.
Run: `ls configs/network.d/ | wc -l` should return `3`.

---

### Task 2: Build `rnas-config` — Config Reader

**Files:**
- Create: `cmd/rnas-config/main.go`
- Create: `cmd/rnas-config/reader/reader.go`
- Create: `cmd/rnas-config/reader/reader_test.go`

**Step 1: Implement INI-style parser**

Parse `[section "name"]` headers and `key = value` pairs. Store in a nested map structure:
```go
type Config map[string]map[string]map[string]string
// config["access"]["radius"]["auth_host"] = "192.168.0.85"
```

Support `${VAR}` environment variable interpolation.
Skip `#` comment lines. Skip blank lines.

**Step 2: Implement config tree reader**

Walk `/etc/rnas/` recursively, parse all `.conf` files, merge into single Config structure. Section name = filename without `.conf`. Subsection from `[section "name"]`.

**Step 3: Verify task**
```bash
cd cmd/rnas-config
go test ./reader -v -run TestParseSection    # passes: parses [server "primary"]
go test ./reader -v -run TestEnvInterp       # passes: ${VAR} resolved
go test ./reader -v -run TestWalkTree        # passes: walks test config tree
```

**Step 4: Commit**
```bash
git add cmd/rnas-config/
git commit -m "feat(rnas-config): add config reader with INI parser and tree walker"
```

---

### Task 3: Build `rnas-config` — Accel-PPP Generator

**Files:**
- Create: `cmd/rnas-config/generator/accel_ppp.go`
- Create: `cmd/rnas-config/generator/accel_ppp_test.go`
- Modify: `cmd/rnas-config/main.go`

**Step 1: Map `/etc/rnas/access.d/*` to accel-ppp.conf format**

Read config sections and produce native accel-ppp.conf output:

| Config Path | accel-ppp.conf Section |
|---|---|
| `access.core.thread_count` | `[core] thread-count` |
| `access.ppp.mtu` | `[ppp] mtu` |
| `access.radius.server.primary.auth_host` | `[radius] server=...` |
| `access.pppoe.interface` | `[pppoe] interface` |
| `access.coa.enabled` | `[radius] dae-server=...` |
| `access.ip-pool.gateway` | `[ip-pool] gw-ip-address` |

**Step 2: Implement CLI**

```bash
rnas-config generate accel-ppp > /var/run/rnas/accel-ppp.conf
rnas-config generate accel-ppp --check   # dry-run + validate
```

**Step 3: Verify task**

Use existing `configs/accel-ppp-rnas-vm1.conf` as golden file. Compare generated output against golden:
```bash
cp configs/ configs-test/
# edit configs-test/ configs to match VM1 setup
rnas-config generate accel-ppp --root configs-test/ > /tmp/generated.conf
diff <(grep -v '^#' configs/accel-ppp-rnas-vm1.conf) <(grep -v '^#' /tmp/generated.conf)
# Output: only nas-identifier and nas-ip-address differ (expected)
```

Run: `go test ./generator -v -run TestAccelPPP`

**Step 4: Commit**
```bash
git add cmd/rnas-config/
git commit -m "feat(rnas-config): add accel-ppp config generator"
```

---

### Task 4: Create systemd Units

**Files:**
- Create: `systemd/rnas.target`
- Create: `systemd/rnas-accel-ppp.service`
- Create: `systemd/rnas-dnsmasq.service`
- Create: `systemd/rnas-firewall.service`
- Modify: `configs/accel-ppp.service` (delete, replaced by above)

**Step 1: `rnas.target` — master target**

```ini
[Unit]
Description=RNAS NAS Platform
Wants=rnas-accel-ppp.service rnas-dnsmasq.service rnas-firewall.service

[Install]
WantedBy=multi-user.target
```

**Step 2: `rnas-accel-ppp.service` — Type=simple, no -d flag**

Based on the working unit from VM1 (already tested):
```ini
[Unit]
Description=RNAS accel-ppp Access Server
After=network-online.target
Wants=network-online.target
PartOf=rnas.target

[Service]
Type=simple
ExecStartPre=/usr/bin/rnas-config generate accel-ppp
ExecStart=/usr/local/sbin/accel-pppd -c /var/run/rnas/accel-ppp.conf
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=rnas.target
```

**Step 3: `rnas-dnsmasq.service` and `rnas-firewall.service`**

Same pattern: ExecStartPre generates config, ExecStart runs the daemon.

**Step 4: Verify task**
```bash
# Syntax check only (can't test without systemd in CI)
for f in systemd/*.service systemd/*.target; do
  grep -q '\[Unit\]' $f && grep -q '\[Service\]' $f && echo "$f OK"
done
```

**Step 5: Commit**
```bash
git add systemd/
git rm configs/accel-ppp.service
git commit -m "feat(systemd): add rnas.target and service units"
```

---

### Task 5: Integration Test — Config Generation + Daemon Start

**Files:**
- Create: `tests/integration/test-config-to-daemon.sh`

**Step 1: End-to-end test**

```bash
#!/bin/bash
# 1. Copy test configs to /tmp/rnas-test/
# 2. Run rnas-config generate accel-ppp
# 3. Start accel-ppp with generated config
# 4. Verify port 3799 listening
# 5. Clean shutdown
set -e
cp -r configs/ /tmp/rnas-test/etc/rnas/
./rnas-config generate accel-ppp --root /tmp/rnas-test/etc/rnas/ > /tmp/rnas-test/accel-ppp.conf
accel-pppd -c /tmp/rnas-test/accel-ppp.conf &
sleep 3
ss -u -a | grep 3799 || { echo "FAIL: DAE not listening"; exit 1; }
kill %1
echo "PASS: integration test"
```

**Step 2: Verify task**
Run: `bash tests/integration/test-config-to-daemon.sh`
Expected: `PASS: integration test` (on a machine with accel-ppp installed)

**Step 3: Commit**
```bash
git add tests/integration/
git commit -m "test: add config-to-daemon integration test"
```

---

### Task 6: Build `rnas-api` Backend (FastAPI)

**Files:**
- Create: `web/api/main.py`
- Create: `web/api/routes/status.py`
- Create: `web/api/routes/config.py`
- Create: `web/api/routes/sessions.py`
- Create: `web/api/services/accel_cmd.py`

**Step 6.1: Status + Sessions endpoints**

```python
# web/api/main.py
from fastapi import FastAPI
app = FastAPI(title="RNAS API")

# web/api/routes/status.py
@router.get("/status")
async def status():
    stat = subprocess.run(["accel-cmd", "show", "stat"], capture_output=True, text=True)
    sessions = subprocess.run(["accel-cmd", "show", "sessions"], capture_output=True, text=True)
    return parse_status(stat.stdout, sessions.stdout)

# web/api/routes/sessions.py
@router.get("/sessions")
async def list_sessions():
    return parse_sessions(run_accel_cmd("show sessions sid,ifname,username,ip,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"))

@router.post("/sessions/{sid}/disconnect")
async def disconnect_session(sid: str):
    result = run_accel_cmd(f"terminate sid {sid} hard")
    return {"success": "terminated" in result}
```

**Step 6.2: Config CRUD endpoints**

```python
# web/api/routes/config.py
@router.get("/config/{module}")
async def get_config(module: str):
    return read_config_file(module)

@router.put("/config/{module}")
async def update_config(module: str, data: dict):
    write_config_file(module, data)
    subprocess.run(["rnas-config", "generate", module])
    return {"applied": True}
```

**Step 7: Verify task**
```bash
cd web/api
uvicorn main:app &
sleep 2
curl -s http://localhost:8000/api/status | jq .service.uptime   # non-empty
curl -s http://localhost:8000/api/sessions | jq '. | length'     # >= 0
kill %1
```

**Step 8: Commit**
```bash
git add web/api/
git commit -m "feat(api): add FastAPI backend with status, sessions, config endpoints"
```

---

### Task 7: Build Dashboard SPA Frontend (Vue.js)

**Files:**
- Create: `web/frontend/` (Vue 3 + Vite scaffold)

**Step 7.1: Dashboard page with live status**

```vue
<!-- Dashboard.vue -->
<template>
  <div>
    <StatusCard :stat="status" />
    <SessionsTable :sessions="sessions" @disconnect="handleDisconnect" />
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
const status = ref({})
const sessions = ref([])
onMounted(async () => {
  status.value = await fetch('/api/status').then(r => r.json())
  sessions.value = await fetch('/api/sessions').then(r => r.json())
})
</script>
```

**Step 7.2: Sessions table with disconnect action**

Reuse the column layout from `luci-app-rnas/luasrc/view/rnas/sessions_table.htm`:
sid | ifname | username | ip | state | uptime | rx_bytes | tx_bytes | [Disconnect]

Use `format_bytes()` helper (ported from Lua to JS).

**Step 8: Verify task**
```bash
cd web/frontend
npm install && npm run build     # produces dist/
ls dist/index.html               # exists
```

**Step 9: Commit**
```bash
git add web/frontend/
git commit -m "feat(frontend): add Vue.js dashboard with status and sessions"
```

---

### Task 8: Bootstrap Install Script

**Files:**
- Create: `scripts/install.sh`

**Step 1: One-command installer**

```bash
#!/bin/bash
# install.sh - RNAS one-command installer for Debian/Ubuntu/UOS
set -e
echo "[1/5] Installing system dependencies..."
apt-get update && apt-get install -y accel-ppp dnsmasq nftables

echo "[2/5] Installing rnas-config..."
cp cmd/rnas-config/rnas-config /usr/bin/

echo "[3/5] Deploying config templates..."
mkdir -p /etc/rnas/
cp -r configs/* /etc/rnas/

echo "[4/5] Installing systemd units..."
cp systemd/*.service systemd/*.target /etc/systemd/system/
systemctl daemon-reload
systemctl enable rnas.target

echo "[5/5] Starting RNAS..."
systemctl start rnas.target
echo "RNAS installed! Web console: http://$(hostname -I | awk '{print $1}'):8080"
```

**Step 2: Verify task**
Run: `bash scripts/install.sh --dry-run` prints commands without executing.
Run: `shellcheck scripts/install.sh` → exit 0.

**Step 3: Commit**
```bash
git add scripts/install.sh
git commit -m "feat(install): add one-command bootstrap installer"
```

---

### Task 9: Update README & State

**Files:**
- Modify: `README.md`
- Modify: `state.md`

**Step 1: Update README for v2 architecture**

Replace the v1 project structure diagram with the v2 architecture diagram from the design doc. Update quick-start to use `scripts/install.sh`.

**Step 2: Update state.md**

Record Phase 1 completion, current architecture, and Phase 2 entry point.

**Step 3: Commit**
```bash
git add README.md state.md
git commit -m "docs: update README and state for v2 architecture"
```

---

## Verification Checkpoint

After all tasks complete, run:

```bash
# 1. Config tests
cd cmd/rnas-config && go test ./... -count=1
# Expected: PASS (reader + generator)

# 2. Integration test
bash tests/integration/test-config-to-daemon.sh
# Expected: PASS: integration test

# 3. API smoke test
cd web/api && uvicorn main:app --port 8099 &
curl -s http://localhost:8099/api/status | jq .
# Expected: JSON with service stats
kill %1

# 4. Frontend build
cd web/frontend && npm run build
# Expected: dist/ created

# 5. ShellCheck
shellcheck scripts/install.sh tools/*.sh
# Expected: exit 0

# 6. Git status
git status
# Expected: clean (all committed)
```

---

## Phase 2 Preview

After Phase 1 green-lights, Phase 2 adds:
- `rnas-config generate dnsmasq` + `rnas-config generate nftables`
- SNMP + NetFlow + syslog integration (`configs/monitor.conf`)
- Traffic dashboard (real-time graphs via Chart.js)
- `rnas-network` + `rnas-mon` deb packages
