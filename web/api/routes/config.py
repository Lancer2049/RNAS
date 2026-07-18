import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "cmd" / "rnas-config"))
from rnas_config import walk_config_tree, write_config_section

router = APIRouter()
DEFAULT_ROOT = "/etc/rnas"
_SCRIPT_TIMEOUT = 30


@router.get("/config")
async def get_all_config():
    config = walk_config_tree(Path(DEFAULT_ROOT))
    return {"config": {k: v for k, v in sorted(config.items())}}


SNAPSHOT_DIR = Path("/etc/rnas/snapshots")

@router.get("/config/snapshots")
async def list_snapshots():
    if not SNAPSHOT_DIR.exists():
        return {"snapshots": [], "total": 0}
    snapshots = []
    for d in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
        if d.is_dir():
            files = list(d.rglob("*.conf"))
            snapshots.append({"name": d.name, "created": d.stat().st_mtime, "files": len(files)})
    return {"snapshots": snapshots, "total": len(snapshots)}

@router.post("/config/snapshot")
async def create_snapshot(data: dict = Body({})):
    name = data.get("name", f"snap-{datetime.now():%Y%m%d-%H%M%S}")
    target = SNAPSHOT_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in Path("/etc/rnas").rglob("*.conf"):
        rel = f.relative_to(Path("/etc/rnas"))
        d = target / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f.read_text())
        count += 1
    return {"status": "created", "name": name, "files": count}

@router.post("/config/snapshot/{name}/restore")
async def restore_snapshot(name: str):
    source = SNAPSHOT_DIR / name
    if not source.exists():
        raise HTTPException(404, "Snapshot not found")
    config_root = Path(DEFAULT_ROOT)
    backup_name = f"pre-{datetime.now():%Y%m%d-%H%M%S}"
    backup_dir = SNAPSHOT_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in config_root.rglob("*.conf"):
        rel = f.relative_to(config_root)
        d = backup_dir / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f.read_text())
    for f in config_root.rglob("*.conf"):
        f.unlink()
    for f in source.rglob("*.conf"):
        rel = f.relative_to(source)
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
async def diff_snapshot(name: str):
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
async def get_config_section(module: str):
    config = walk_config_tree(Path(DEFAULT_ROOT))
    matches = {k: v for k, v in config.items() if k.startswith(module.replace("/", "."))}
    if not matches:
        raise HTTPException(status_code=404, detail=f"Config section '{module}' not found")
    return {"module": module, "config": matches}


@router.put("/config/{module:path}")
async def update_config_section(module: str, values: Dict[str, str] = Body(...)):
    root = Path(DEFAULT_ROOT)
    if not root.exists():
        raise HTTPException(status_code=503, detail="Config root /etc/rnas not found")
    section = module.replace("/", ".")
    success = write_config_section(root, section, values)
    if not success:
        raise HTTPException(status_code=404, detail=f"Section '{module}' not found")
    return {"success": True, "module": module, "updated": values}


@router.post("/config/apply")
async def apply_config():
    try:
        result = subprocess.run(
            ["rnas-config", "validate", "--root", DEFAULT_ROOT],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr.strip())
        # Regenerate and reload services
        for svc in ["accel-ppp", "dnsmasq", "firewall", "snmp"]:
            subprocess.run(
                ["rnas-config", "generate", svc, "--root", DEFAULT_ROOT,
                 "-o", f"/var/run/rnas/{svc}.conf"],
                capture_output=True, timeout=5
            )
        subprocess.run(["systemctl", "reload-or-restart", "rnas.target"], capture_output=True, timeout=10)
        return {"success": True, "message": "Configuration applied"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Config apply timed out")

SNAPSHOT_DIR = Path("/etc/rnas/snapshots")

@router.get("/config/snapshots")
async def list_snapshots():
    if not SNAPSHOT_DIR.exists():
        return {"snapshots": [], "total": 0}
    snapshots = []
    for d in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
        if d.is_dir():
            files = list(d.rglob("*.conf"))
            snapshots.append({"name": d.name, "created": d.stat().st_mtime, "files": len(files)})
    return {"snapshots": snapshots, "total": len(snapshots)}

@router.post("/config/snapshot")
async def create_snapshot(data: dict = Body({})):
    from datetime import datetime
    name = data.get("name", f"snap-{datetime.now():%Y%m%d-%H%M%S}")
    target = SNAPSHOT_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    for f in Path("/etc/rnas").rglob("*.conf"):
        rel = f.relative_to(Path("/etc/rnas"))
        d = target / rel; d.parent.mkdir(parents=True, exist_ok=True); d.write_text(f.read_text())
    return {"status": "created", "name": name, "files": len(list(target.rglob("*.conf")))}

@router.post("/config/snapshot/{name}/restore")
async def restore_snapshot(name: str):
    import shutil, subprocess
    from datetime import datetime
    source = SNAPSHOT_DIR / name
    if not source.exists():
        raise HTTPException(404, f"Snapshot not found")
    backup_name = f"pre-{datetime.now():%Y%m%d-%H%M%S}"
    backup_dir = SNAPSHOT_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in Path("/etc/rnas").rglob("*.conf"):
        rel = f.relative_to(Path("/etc/rnas"))
        d = backup_dir / rel; d.parent.mkdir(parents=True, exist_ok=True); d.write_text(f.read_text())
    shutil.rmtree("/etc/rnas")
    shutil.copytree(source, "/etc/rnas")
    subprocess.run(["systemctl", "restart", "rnas-accel-ppp"])
    return {"status": "restored", "name": name, "backup": backup_name}

@router.get("/config/snapshot/{name}/diff")
async def diff_snapshot(name: str):
    import subprocess
    source = SNAPSHOT_DIR / name
    result = subprocess.run(["diff", "-ru", str(source), "/etc/rnas"], capture_output=True, text=True)
    return {"diff": result.stdout or "(identical)", "has_diff": bool(result.stdout)}
