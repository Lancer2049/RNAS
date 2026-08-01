import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from api.auth import require_auth
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "cmd" / "rnas-config"))
from rnas_config import walk_config_tree, write_config_section

router = APIRouter(tags=["Configuration"])
DEFAULT_ROOT = "/etc/rnas"
_SCRIPT_TIMEOUT = 30
_IGNORED_DIRS = {"snapshots", "backup", "archive", "bak"}


def _active_config_files(root: Path | None = None) -> list[Path]:
    """Return active .conf files, excluding snapshot/backup directories."""
    root = root or Path(DEFAULT_ROOT)
    return [f for f in root.rglob("*.conf") if not any(p in _IGNORED_DIRS for p in f.parts)]


@router.get("/config")
async def get_all_config(user=Depends(require_auth)):
    config = walk_config_tree(Path(DEFAULT_ROOT))
    return {"config": {k: v for k, v in sorted(config.items())}}


SNAPSHOT_DIR = Path("/etc/rnas/snapshots")

@router.get("/config/snapshots")
async def list_snapshots(user=Depends(require_auth)):
    if not SNAPSHOT_DIR.exists():
        return {"snapshots": [], "total": 0}
    snapshots = []
    for d in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
        if d.is_dir():
            files = list(d.rglob("*.conf"))
            snapshots.append({"name": d.name, "created": d.stat().st_mtime, "files": len(files)})
    return {"snapshots": snapshots, "total": len(snapshots)}

@router.post("/config/snapshot")
async def create_snapshot(data: dict = Body({}), user=Depends(require_auth)):
    name = data.get("name", f"snap-{datetime.now():%Y%m%d-%H%M%S}")
    target = SNAPSHOT_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in _active_config_files():
        rel = f.relative_to(Path("/etc/rnas"))
        d = target / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f.read_text())
        count += 1
    return {"status": "created", "name": name, "files": count}

@router.post("/config/snapshot/{name}/restore")
async def restore_snapshot(name: str, user=Depends(require_auth)):
    source = SNAPSHOT_DIR / name
    if not source.exists():
        raise HTTPException(404, "Snapshot not found")
    config_root = Path(DEFAULT_ROOT)
    backup_name = f"pre-{datetime.now():%Y%m%d-%H%M%S}"
    backup_dir = SNAPSHOT_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in _active_config_files():
        rel = f.relative_to(config_root)
        d = backup_dir / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f.read_text())
    for f in _active_config_files():
        f.unlink()
    for f in source.rglob("*.conf"):
        rel = f.relative_to(source)
        if "snapshots" in rel.parts:
            continue
        d = config_root / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(f), str(d))
    try:
        subprocess.run(
            ["systemctl", "restart", "rnas-accel-ppp"],
            capture_output=True, timeout=_SCRIPT_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Service restart timed out during snapshot restore")
    return {"status": "restored", "name": name, "backup": backup_name}

@router.get("/config/snapshot/{name}/diff")
async def diff_snapshot(name: str, user=Depends(require_auth)):
    source = SNAPSHOT_DIR / name
    if not source.exists():
        raise HTTPException(404, "Snapshot not found")
    try:
        result = subprocess.run(
            ["diff", "-ru", str(source), DEFAULT_ROOT],
            capture_output=True, text=True, timeout=_SCRIPT_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Diff timed out")
    return {"diff": result.stdout or "(identical)", "has_diff": bool(result.stdout)}

@router.get("/config/{module:path}")
async def get_config_section(module: str, user=Depends(require_auth)):
    config = walk_config_tree(Path(DEFAULT_ROOT))
    matches = {k: v for k, v in config.items() if k.startswith(module.replace("/", "."))}
    if not matches:
        raise HTTPException(status_code=404, detail=f"Config section '{module}' not found")
    return {"module": module, "config": matches}


@router.put("/config/{module:path}")
async def update_config_section(module: str, values: Dict[str, str] = Body(...), user=Depends(require_auth)):
    root = Path(DEFAULT_ROOT)
    if not root.exists():
        raise HTTPException(status_code=503, detail="Config root /etc/rnas not found")
    section = module.replace("/", ".")
    success = write_config_section(root, section, values)
    if not success:
        raise HTTPException(status_code=404, detail=f"Section '{module}' not found")
    return {"success": True, "module": module, "updated": values}


@router.post("/config/apply")
async def apply_config(user=Depends(require_auth)):
    """Apply configuration with safety guards:
    1. flock lock (no concurrent applies)
    2. auto-snapshot (rollback point)
    3. dry-run validation (nft -c -f / dnsmasq --test)
    4. service reload
    """
    import fcntl

    LOCK_FILE = Path("/var/run/rnas-apply.lock")
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_fd = open(LOCK_FILE, "w")

    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fd.close()
        raise HTTPException(status_code=423, detail="Another apply is in progress")

    snapshot_name = f"auto-apply-{datetime.now():%Y%m%d-%H%M%S}"

    try:
        # Step 1: Auto-snapshot
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        target = SNAPSHOT_DIR / snapshot_name
        target.mkdir(parents=True, exist_ok=True)
        for f in _active_config_files():
            rel = f.relative_to(Path(DEFAULT_ROOT))
            d = target / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            d.write_text(f.read_text())

        # Step 2: Dry-run validation
        from rnas_config import walk_config_tree, GEN_MAP
        from validators import validate_config

        tree = walk_config_tree(Path(DEFAULT_ROOT))
        errors = []
        for name in ["accel-ppp", "dnsmasq", "firewall", "ha"]:
            if name not in GEN_MAP:
                continue
            out_path = Path(f"/var/run/rnas/{name}.conf")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(GEN_MAP[name](tree))
            err = validate_config(name, out_path)
            if err:
                errors.append(err)

        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"Config validation failed:\n" + "\n".join(errors),
            )

        # Step 3: Regenerate and reload services
        import shutil
        rnas_config_cli = shutil.which("rnas-config")
        gen_cmd = (
            [rnas_config_cli, "generate"]
            if rnas_config_cli
            else ["python3", "-m", "rnas_config", "generate"]
        )
        for svc in ["accel-ppp", "dnsmasq", "firewall", "snmp"]:
            res = subprocess.run(
                gen_cmd + [svc, "--root", DEFAULT_ROOT, "-o", f"/var/run/rnas/{svc}.conf"],
                capture_output=True, text=True, timeout=10,
            )
            if res.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Config generation failed for {svc}: {res.stderr[:300]}",
                )
        subprocess.run(["systemctl", "reload-or-restart", "rnas.target"],
                      capture_output=True, timeout=10)
        import time; time.sleep(2)  # wait for services to stabilize

        # Step 4: Health check — rollback on failure
        from health_check import health_check, restore_snapshot as do_restore
        if not health_check():
            do_restore(snapshot_name)
            subprocess.run(["systemctl", "reload-or-restart", "rnas.target"],
                          capture_output=True, timeout=10)
            raise HTTPException(
                status_code=500,
                detail=f"Config applied but health check failed. Rolled back to snapshot {snapshot_name}.",
            )

        return {
            "success": True,
            "message": "Configuration applied",
            "snapshot": snapshot_name,
            "health": "passed",
        }
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Config apply timed out")
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
