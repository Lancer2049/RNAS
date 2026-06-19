"""RNAS Environment Configuration — all topology-specific values in one place."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class RNASEnv:
    """Environment configuration for RNAS web server and tools."""
    # ── Topology ──
    cpe_host: str = field(default_factory=lambda: os.environ.get("RNAS_CPE_HOST", "192.168.0.201"))
    radius_host: str = field(default_factory=lambda: os.environ.get("RNAS_RADIUS_HOST", "192.168.0.202"))
    nas_host: str = field(default_factory=lambda: os.environ.get("RNAS_NAS_HOST", "192.168.0.203"))

    # ── SSH credentials ──
    ssh_user: str = field(default_factory=lambda: os.environ.get("RNAS_SSH_USER", "root"))
    ssh_pass: str = field(default_factory=lambda: os.environ.get("RNAS_SSH_PASS", "123456"))

    # ── RADIUS ──
    radius_auth_port: int = 1812
    radius_acct_port: int = 1813
    radius_secret: str = field(default_factory=lambda: os.environ.get("RNAS_RADIUS_SECRET", "testing123"))
    radius_coa_port: int = 3799

    # ── Database (PostgreSQL on RADIUS host) ──
    db_user: str = field(default_factory=lambda: os.environ.get("RNAS_DB_USER", "radius"))
    db_pass: str = field(default_factory=lambda: os.environ.get("RNAS_DB_PASS", "radpass"))
    db_name: str = "radius"
    db_host: str = "localhost"

    # ── Web ──
    web_port: int = 8099
    static_dir: Path = Path(__file__).parent / "static"
    dict_dir: Path = Path("/etc/rnas/dictionary")

    # ── AIRadius ──
    airos_url: str = field(default_factory=lambda: f"http://{os.environ.get('RNAS_RADIUS_HOST', '192.168.0.202')}:8000")

    # ── Config ──
    rnas_config_root: Path = Path("/etc/rnas")
    accel_cmd_bin: str = "/usr/bin/accel-cmd"

    def ssh_cmd(self, host: str, command: str) -> list[str]:
        """Build an sshpass-based SSH command (for dev/test only)."""
        return [
            "sshpass", "-p", self.ssh_pass,
            "ssh", "-o", "StrictHostKeyChecking=no",
            f"{self.ssh_user}@{host}", command,
        ]

    def db_query_str(self, sql: str) -> str:
        """Build a shell command string for remote PostgreSQL query (for subprocess shell=True)."""
        cmd = (
            f"PGPASSWORD={self.db_pass} psql -h {self.db_host} "
            f"-U {self.db_user} -d {self.db_name} -t -c '{sql}'"
        )
        return f"sshpass -p {self.ssh_pass} ssh -o StrictHostKeyChecking=no {self.ssh_user}@{self.radius_host} '{cmd}'"

    def ssh_cmd_str(self, host: str, command: str) -> str:
        """Build an sshpass shell command string (for subprocess shell=True)."""
        return (
            f'sshpass -p {self.ssh_pass} ssh -o StrictHostKeyChecking=no '
            f'{self.ssh_user}@{host} \'{command}\''
        )

    def radius_test_payload(self, user: str = "testuser", password: str = "testpass", extra_attrs: str = "") -> str:
        """Build a radclient test payload."""
        pairs = [f"User-Name={user},User-Password={password}"]
        if extra_attrs:
            pairs.append(extra_attrs)
        return ",".join(pairs)

    def radclient_cmd(self, server: str, port_type: str, payload: str, secret: Optional[str] = None) -> list[str]:
        """Build a radclient command."""
        return ["radclient", "-r", "1", "-t", "3", server, port_type, secret or self.radius_secret]

    def radclient_coa(self, username: str, server: str = "127.0.0.1") -> str:
        """Build a CoA disconnect shell command."""
        return (
            f"echo 'User-Name={username}' | "
            f"radclient -r 1 -t 5 {server}:{self.radius_coa_port} disconnect {self.radius_secret}"
        )


# Singleton instance
_env: Optional[RNASEnv] = None


def get_env() -> RNASEnv:
    global _env
    if _env is None:
        _env = RNASEnv()
    return _env
