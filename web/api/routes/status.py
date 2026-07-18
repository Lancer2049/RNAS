from fastapi import APIRouter, Depends, HTTPException
from api.auth import require_auth
from services.accel_cmd import run_accel_cmd, parse_sessions, parse_stat, disconnect_session

router = APIRouter(tags=["Status"])


@router.get("/status")
async def get_status(user=Depends(require_auth)):
    stat_raw = run_accel_cmd("show", "stat")
    sessions_raw = run_accel_cmd(
        "show", "sessions",
        "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"
    )
    sessions = parse_sessions(sessions_raw)
    return {
        "service": parse_stat(stat_raw),
        "sessions": sessions,
        "sessions_count": len(sessions),
    }


@router.get("/sessions")
async def list_sessions(user=Depends(require_auth)):
    raw = run_accel_cmd(
        "show", "sessions",
        "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"
    )
    return parse_sessions(raw)


@router.post("/sessions/{sid}/disconnect")
async def disconnect_session_endpoint(sid: str, user=Depends(require_auth)):
    if disconnect_session(sid):
        return {"success": True, "message": f"Session {sid} terminated"}
    raise HTTPException(status_code=404, detail=f"Session {sid} not found")
