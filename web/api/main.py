import os
import re
import json
import asyncio
import logging
import subprocess
from urllib.parse import parse_qs
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from routes import status, config, tools, system as sys_routes, aaa, sim, extra, auth as auth_routes
from api.auth import FEATURE_FLAGS, require_auth

logger = logging.getLogger("rnas-api")

_ENV = os.environ.get("RNAS_ENV", "production")

app = FastAPI(title="RNAS API", version="3.0.0")

# CORS: closed in production (frontend served from same origin by FastAPI).
# In development, frontend runs on Vite dev server (localhost:5173) and needs CORS.
if _ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/system/features", tags=["System"])
async def features():
    """Return enabled feature flags for the frontend."""
    return FEATURE_FLAGS

app.include_router(auth_routes.router)
app.include_router(status.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(sys_routes.router, prefix="/api")
app.include_router(aaa.router, prefix="/api")
app.include_router(sim.router, prefix="/api")
app.include_router(extra.router, prefix="/api")

# Hotspot login POST
_RADIUS_SECRET = os.environ.get("RNAS_RADIUS_SECRET", "testing123")
_RADIUS_SERVER = os.environ.get("RNAS_RADIUS_SERVER", "192.168.0.202")

@app.post("/hotspot/login")
async def hotspot_login(request: Request):
    body = await request.body()
    params = parse_qs(body.decode())
    user = params.get("username", [""])[0]
    pwd = params.get("password", [""])[0]
    if not user:
        return PlainTextResponse("Missing username", status_code=400)
    payload = f"User-Name={user},User-Password={pwd}"
    try:
        result = subprocess.run(
            ["radclient", "-r", "1", "-t", "3", f"{_RADIUS_SERVER}:1812", "auth", _RADIUS_SECRET],
            input=payload, capture_output=True, text=True, timeout=10
        )
        ok = "Access-Accept" in result.stdout
        return PlainTextResponse("Authenticated" if ok else "Access Denied", status_code=302 if ok else 403)
    except Exception as e:
        logger.error("hotspot_login failed: %s", e)
        return PlainTextResponse("Server error", status_code=500)

# Static files — only for non-API paths
sd = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(sd):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("hotspot/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        fp = os.path.join(sd, full_path if full_path else "index.html")
        if os.path.isfile(fp) and not fp.endswith(".py"):
            return FileResponse(fp)
        return FileResponse(os.path.join(sd, "index.html"))

_ACCEL_CMD = os.environ.get("RNAS_ACCEL_CMD", "accel-cmd")

@app.websocket("/api/ws")
async def ws_dashboard(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            try:
                stat = subprocess.run([_ACCEL_CMD, "show", "stat"], capture_output=True, text=True, timeout=3).stdout
                sessions_raw = subprocess.run([_ACCEL_CMD, "show", "sessions", "sid,ifname,username,ip,type,state,uptime-raw,rx-bytes-raw,tx-bytes-raw"], capture_output=True, text=True, timeout=3).stdout
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning("accel-cmd failed: %s", e)
                await asyncio.sleep(3)
                continue
            svc = {}
            for key, pat in [("uptime", r"uptime:\s*(\S+)"), ("cpu", r"cpu:\s*(\S+)"), ("mem", r"mem\(rss/virt\):\s*(\S+)"), ("radius_state", r"state:\s*(\S+)"), ("auth_sent", r"auth sent:\s*(\d+)"), ("acct_sent", r"acct sent:\s*(\d+)"), ("sessions_active", r"sessions:.*?active:\s*(\d+)")]:
                m = re.search(pat, stat, re.DOTALL)
                if m: svc[key] = m.group(1)
            sess = []
            for line in sessions_raw.splitlines()[1:]:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 9:
                    sid = parts[0]
                    if sid and not sid.startswith("-") and not sid.startswith("sid"):
                        sess.append({
                            "sid": parts[0],"ifname": parts[1],"username": parts[2],"ip": parts[3],
                            "type": parts[4],"state": parts[5],"uptime_raw": parts[6],
                            "rx_bytes_raw": parts[7],"tx_bytes_raw": parts[8],
                        })
            await ws.send_text(json.dumps({"service":svc,"sessions":sess,"sessions_count":len(sess)}))
            await asyncio.sleep(3)
    except Exception as e:
        logger.error("ws_dashboard disconnected: %s", e)
    finally:
        try:
            await ws.close()
        except Exception:
            pass

@app.websocket("/api/terminal")
async def terminal_shell(ws: WebSocket):
    """WebSocket shell — gated by RNAS_FEATURE_TERMINAL env flag."""
    if not FEATURE_FLAGS.get("web_terminal", False):
        await ws.accept()
        await ws.send_text("Terminal is disabled. Set RNAS_FEATURE_TERMINAL=true to enable.")
        await ws.close()
        return
    await ws.accept()
    process = await asyncio.create_subprocess_exec(
        "bash", "-c", "stty rows 24 cols 80 -echo && bash",
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    async def reader():
        try:
            while True:
                line = await process.stdout.readline()
                if not line: break
                await ws.send_text(line.decode(errors="replace"))
        except Exception as e:
            logger.debug("terminal reader done: %s", e)
    async def writer():
        try:
            while True:
                data = await ws.receive_text()
                if data == "__CLOSE__":
                    process.terminate()
                    break
                process.stdin.write(data.encode())
                await process.stdin.drain()
        except Exception as e:
            logger.debug("terminal writer done: %s", e)
    try:
        await asyncio.gather(reader(), writer())
    except Exception as e:
        logger.error("terminal shell disconnected: %s", e)
    finally:
        try:
            process.terminate()
            await process.wait()
        except Exception:
            pass
        try:
            await ws.close()
        except Exception:
            pass

