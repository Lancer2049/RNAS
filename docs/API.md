# RNAS REST API Reference

Base URL: `http://192.168.0.203:8099`

## Status & Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | `{"status":"ok","version":"3.0"}` |
| GET | `/api/status` | Service stats + active sessions |

## Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sessions` | List active sessions with RX/TX bytes |
| POST | `/api/sessions/{sid}/disconnect` | Terminate session by SID |

## Configuration (CRUD)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config` | Export all 42 config sections as JSON |
| POST | `/api/config/apply` | Regenerate + reload services from `/etc/rnas/` |
| PUT | `/api/config/{module}` | Write key=value pairs to config section |
| POST | `/api/config/export` | Full config export with version + timestamp |
| POST | `/api/config/import` | Bulk import config sections (JSON body) |
| POST | `/api/config/snapshot` | Create named snapshot of current config |
| GET | `/api/config/snapshots` | List recent snapshots |
| POST | `/api/config/snapshot/{id}/restore` | Restore config from snapshot |
| DELETE | `/api/config/snapshot/{id}` | Delete snapshot |

## RADIUS Dictionary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dictionary` | All attributes (169 entries, 6 vendors) |
| GET | `/api/dictionary/search?q=` | Search by attribute name or vendor |

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/status` | All 10 services status + memory/disk |
| GET | `/api/system/logs` | Recent accel-ppp logs (30 lines) |
| GET | `/api/airos/status` | AirOS (AIRadius) connectivity check |

## Tools

| Method | Path | Parameters | Description |
|--------|------|------------|-------------|
| GET | `/api/tools/ping` | `host` | Ping test (3 packets) |
| GET | `/api/tools/trace` | `host` | Traceroute (10 hops) |
| GET | `/api/tools/radius-test` | `user`, `pass`, `attrs` | RADIUS auth test with optional VSA |
| GET | `/api/tools/coa` | `user` | CoA Disconnect by username |

## WebSocket (Real-time)

| Protocol | Path | Description |
|----------|------|-------------|
| WS | `/api/ws` | Push sessions + stats every 3s |

### RADIUS Test with VSA Example

```bash
curl 'http://192.168.0.203:8099/api/tools/radius-test?user=testuser&pass=testpass&attrs=Huawei-QOS-Profile-Name=gold,WISPr-Bandwidth-Max-Up=5000000'
```

### Config Import Example

```bash
curl -X POST http://192.168.0.203:8099/api/config/import \
  -H 'Content-Type: application/json' \
  -d '{"config":{"access.d.core":{"pppoe":"yes","l2tp":"yes"}}}'
```
