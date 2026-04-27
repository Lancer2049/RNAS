import sys
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException, Body
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "cmd" / "rnas-config"))
from rnas_config import walk_config_tree, write_config_section

router = APIRouter()
DEFAULT_ROOT = "/etc/rnas"


@router.get("/config")
async def get_all_config():
    config = walk_config_tree(Path(DEFAULT_ROOT))
    return {"config": {k: v for k, v in sorted(config.items())}}


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
