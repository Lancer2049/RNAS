"""RNAS Environment Configuration — all topology-specific values in one place."""
import os, subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Dict, Optional


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
    # Port-forwarded SSH ports (VMware NAT: 2201→.201:22, 2202→.202:22, 2203→.203:22)
    cpe_ssh_port: int = int(os.environ.get("RNAS_CPE_SSH_PORT", "2201"))
    radius_ssh_port: int = int(os.environ.get("RNAS_RADIUS_SSH_PORT", "2202"))
    nas_ssh_port: int = int(os.environ.get("RNAS_NAS_SSH_PORT", "2203"))

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

    # Port-forwarded host map: original IP → (reachable_address, port)
    # VMware NAT on the Windows host forwards 2201→.201:22, 2202→.202:22, 2203→.203:22
    # From WSL (mirrored networking), connect to 127.0.0.1 on the forwarded port.
    _NAT_MAP: ClassVar[Dict[str, tuple[str, int]]] = {}

    @property
    def _nat_map(self) -> Dict[str, tuple[str, int]]:
        if not self._NAT_MAP:
            self.__class__._NAT_MAP = {
                self.cpe_host: ("127.0.0.1", self.cpe_ssh_port),
                self.radius_host: ("127.0.0.1", self.radius_ssh_port),
                self.nas_host: ("127.0.0.1", self.nas_ssh_port),
            }
        return self._NAT_MAP

    def ssh_connect_params(self, host: str) -> tuple[str, int]:
        """Map a configured host IP through VMware NAT to reachable address + port."""
        if host in self._nat_map:
            return self._nat_map[host]
        return (host, 22)

    def ssh_cmd(self, host: str, command: str) -> list[str]:
        """Build an sshpass-based SSH command (for dev/test only)."""
        connect_host, port = self.ssh_connect_params(host)
        cmd = [
            "sshpass", "-p", self.ssh_pass,
            "ssh", "-o", "StrictHostKeyChecking=no",
        ]
        if port != 22:
            cmd += ["-p", str(port)]
        cmd += [f"{self.ssh_user}@{connect_host}", command]
        return cmd

    def db_query_str(self, sql: str) -> str:
        """Build a shell command string for remote PostgreSQL query (kept for compatibility)."""
        connect_host, port = self.ssh_connect_params(self.radius_host)
        port_flag = f" -p {port}" if port != 22 else ""
        cmd = (
            f"PGPASSWORD={self.db_pass} psql -h {self.db_host} "
            f"-U {self.db_user} -d {self.db_name} -t -c '{sql}'"
        )
        return (
            f'sshpass -p {self.ssh_pass} ssh -o StrictHostKeyChecking=no'
            f'{port_flag} {self.ssh_user}@{connect_host} \'{cmd}\''
        )

    def db_query(self, sql: str, timeout: int = 15) -> str:
        """Run a remote PostgreSQL query via SSH and return stdout.

        Uses argv list (no shell=True). PGPASSWORD is passed in the remote
        command string for the remote psql process only.
        """
        connect_host, port = self.ssh_connect_params(self.radius_host)
        remote_cmd = (
            f"PGPASSWORD={self.db_pass} psql -h {self.db_host} "
            f"-U {self.db_user} -d {self.db_name} -t -c '{sql}'"
        )
        cmd = [
            "sshpass", "-p", self.ssh_pass,
            "ssh", "-o", "StrictHostKeyChecking=no",
        ]
        if port != 22:
            cmd += ["-p", str(port)]
        cmd += [f"{self.ssh_user}@{connect_host}", remote_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout

    def ssh_cmd_str(self, host: str, command: str) -> str:
        """Build an sshpass shell command string (for subprocess shell=True)."""
        connect_host, port = self.ssh_connect_params(host)
        port_flag = f" -p {port}" if port != 22 else ""
        return (
            f'sshpass -p {self.ssh_pass} ssh -o StrictHostKeyChecking=no'
            f'{port_flag} {self.ssh_user}@{connect_host} \'{command}\''
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
