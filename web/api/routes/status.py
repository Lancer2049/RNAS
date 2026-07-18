from fastapi import APIRouter, HTTPException
from services.accel_cmd import run_accel_cmd, parse_sessions, parse_stat, disconnect_session

router = APIRouter()


@router.get("/status")
async def get_status():
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
async def list_sessions():
    raw = run_accel_cmd(
        "show", "sessions",
        "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"
    )
    return parse_sessions(raw)


@router.post("/sessions/{sid}/disconnect")
async def disconnect_session_endpoint(sid: str):
    if disconnect_session(sid):
        return {"success": True, "message": f"Session {sid} terminated"}
    raise HTTPException(status_code=404, detail=f"Session {sid} not found")
