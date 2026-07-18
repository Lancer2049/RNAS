# RNAS Architecture Decision Records

## ADR-001: UCI-format configuration tree

**Date**: 2026-04-26  
**Status**: Accepted

**Context**: RNAS needs to manage configs for 10+ services (accel-ppp, dnsmasq, nftables, strongSwan, keepalived, etc.) under a unified interface.

**Decision**: Use OpenWrt-style UCI INI format (`[section "name"]`) under `/etc/rnas/`, with a Python config engine that generates native service configs.

**Consequences**:
- + Single config tree, single source of truth
- + Familiar to network engineers (OpenWrt/RouterOS paradigm)
- - Config engine is a custom parser, not a standard tool

## ADR-002: Single-worker uvicorn for management plane

**Date**: 2026-07-18  
**Status**: Accepted

**Context**: The management API handles <10 req/s. Multi-worker mode causes process-internal state inconsistency (traffic history, capture tasks, SSH connections).

**Decision**: Run uvicorn with a single worker. If performance becomes an issue, externalize state to SQLite/Redis before adding workers.

**Consequences**:
- + Eliminates state inconsistency bugs
- + Simpler operational model
- - Single point of failure (acceptable for management plane)

## ADR-003: SQLite for persistent state

**Date**: 2026-07-18  
**Status**: Accepted

**Context**: Traffic history, audit logs, and configuration metadata need persistence but don't warrant a full RDBMS deployment.

**Decision**: Use SQLite for all local persistent state, with ring buffer patterns for time-series data (traffic_history → hourly/daily downsampling).

**Consequences**:
- + Zero deployment dependencies
- + Simple backup (copy .db files)
- - Not suitable for multi-writer scenarios (acceptable for single-worker API)
