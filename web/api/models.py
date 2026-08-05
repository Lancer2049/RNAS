"""Pydantic data models for RNAS API request/response validation"""
from pydantic import BaseModel, Field
from typing import List, Optional

class StatusResponse(BaseModel):
    uptime: str = "N/A"
    cpu: str = "N/A"
    mem: str = "N/A"
    sessions_active: int = 0
    radius_state: str = "unknown"
    auth_sent: int = 0
    acct_sent: int = 0

class SessionItem(BaseModel):
    sid: str = ""
    ifname: str = ""
    username: str = ""
    ip: str = ""
    type: str = ""
    state: str = ""
    uptime_raw: str = ""
    rx_bytes_raw: int = 0
    tx_bytes_raw: int = 0

class FirewallRule(BaseModel):
    chain: str = Field(..., description="nftables chain name")
    table: str = Field("filter", description="nftables table")
    family: str = Field("ip", description="nftables address family")
    rule: str = Field(..., description="nftables rule text")
    handle: Optional[int] = None
    position: Optional[int] = None

class FirewallReorder(FirewallRule):
    handle: int = Field(..., description="Rule handle to move")
    position: int = Field(..., description="Target position handle")

class SnapshotCreate(BaseModel):
    name: Optional[str] = Field(None, description="Snapshot name, auto-generated if empty")

class BandwidthTestRequest(BaseModel):
    target: str = Field("127.0.0.1", description="iperf3 server IP")
    port: int = Field(5201, ge=1, le=65535)
    duration: int = Field(5, ge=1, le=60)
    proto: str = Field("tcp", pattern="^(tcp|udp)$")

class CaptureRequest(BaseModel):
    action: str = Field("start", pattern="^(start|stop|status)$")
    interface: str = Field("ens33")
    port: int = Field(0, ge=0, le=65535)
    count: int = Field(100, ge=1, le=10000)

class SetupConfig(BaseModel):
    pppoe_iface: str = Field("ens33")
    radius_server: str = Field("192.168.0.202")
    radius_secret: str = Field("testing123")
    lan_ip: str = Field("192.168.100.1/24")
    ac_name: str = Field("RNAS")
    ip_pool_start: str = Field("192.168.100.10")
    ip_pool_end: str = Field("192.168.100.200")

class FirewallToggle(BaseModel):
    chain: str = Field(...)
    table: str = Field("filter")
    family: str = Field("ip")
    enabled: bool = Field(True)

PROTO_RE = "^(pppoe|pptp|sstp|l2tp)$"
USER_RE = r"^[A-Za-z0-9_.-]{1,32}$"
PASSWD_RE = r"^[A-Za-z0-9@._\-]{1,128}$"

class MultiConnectRequest(BaseModel):
    proto: str = Field("pppoe", pattern=PROTO_RE)
    user: str = Field("testuser", min_length=1, max_length=32, pattern=USER_RE)
    password: str = Field("testpass", alias="pass", min_length=1, max_length=128, pattern=PASSWD_RE)
    count: int = Field(5, ge=1, le=50)

    model_config = {"populate_by_name": True}
