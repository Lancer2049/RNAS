import os
import re
import json
import asyncio
import logging
import subprocess
import queue
import uuid
from urllib.parse import parse_qs
from fastapi import FastAPI, Request, WebSocket, APIRouter, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse, RedirectResponse
from routes import status, config, tools, system as sys_routes, aaa, sim, extra, auth_endpoints as auth_routes
from routes import interfaces, firewall as fw_routes, network_services, system_extra
from api.auth import FEATURE_FLAGS, require_auth

logger = logging.getLogger("rnas-api")

from logging_config import setup_logging
setup_logging()

_ENV = os.environ.get("RNAS_ENV", "production")

app = FastAPI(title="RNAS API", version="3.0.0")

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    from logging_config import request_id_ctx
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request_id_ctx.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.set("")
    return response

# CORS: closed in production (frontend served from same origin by FastAPI).
# In development, frontend runs on Vite dev server (localhost:5173) and needs CORS.
if _ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

@app.get("/api/v1/system/features", tags=["System"])
async def features():
    """Return enabled feature flags for the frontend."""
    return FEATURE_FLAGS

# ── Prometheus metrics (zero-dependency) ──────────────────────────────────

@app.get("/metrics", tags=["Metrics"])
async def metrics():
    from metrics import render_metrics
    return PlainTextResponse(render_metrics(), media_type="text/plain; version=0.0.4")

app.include_router(auth_routes.router)

# ── API v1 router ───────────────────────────────────────────────────────
v1 = APIRouter(prefix="/api/v1")
v1.include_router(status.router)         # /api/v1/status, /api/v1/sessions
v1.include_router(config.router)         # /api/v1/config/*
v1.include_router(tools.router)          # /api/v1/tools/*
v1.include_router(sys_routes.router)     # /api/v1/system/*
v1.include_router(aaa.router)            # /api/v1/aaa/*
v1.include_router(sim.router)            # /api/v1/sim/*
v1.include_router(extra.router)              # /api/v1/* (backward compat, delegates to new modules)
v1.include_router(interfaces.router)         # /api/v1/interfaces, /api/v1/routing, /api/v1/tunnels, /api/v1/vlans
v1.include_router(fw_routes.router)          # /api/v1/ip/firewall, /api/v1/ip/arp
v1.include_router(network_services.router)   # /api/v1/netflow, /api/v1/dhcp-relay, /api/v1/hotspot
v1.include_router(system_extra.router)       # /api/v1/system/log, /api/v1/protocol/events, /api/v1/setup, /api/v1/certs
app.include_router(v1)

# Backward compat: /api/* → /api/v1/* via server-side proxy (preserves method/headers/body)
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], tags=["Status"])
async def compat_proxy(path: str, request: Request):
    if path.startswith("v1/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if path == "health":
        return {"status": "ok", "version": "3.0.0"}
    if path == "ws" or path == "terminal":
        raise HTTPException(status_code=410, detail="Use /api/v1/ws or /api/v1/terminal")

    from http_client import get_client, get_sim_client, get_notify_client
    from urllib.parse import urlsplit
    loopback_port = os.environ.get("RNAS_API_PORT", "9099")
    parts = urlsplit(str(request.url).replace("/api/", "/api/v1/", 1))
    target_url = f"http://127.0.0.1:{loopback_port}{parts.path}?{parts.query}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    try:
        if path.startswith("sim/"):
            proxy = get_sim_client()
        elif path == "system/notifications/test":
            proxy = get_notify_client()
        else:
            proxy = get_client()
        resp = await proxy.request(
            request.method,
            target_url,
            headers=headers,
            content=body if body else None,
            params=request.query_params,
        )
        return JSONResponse(
            status_code=resp.status_code,
            content=resp.json() if resp.headers.get("content-type", "").startswith("application/json")
            else {"detail": resp.text},
            headers={"X-Compat-Proxy": "true"},
        )
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"Compat proxy failed: {e}"})

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
            # Hashed build assets are immutable → long-lived cache. index.html
            # itself is not hashed → no-cache so new deploys are picked up.
            cache_control = "public, max-age=31536000, immutable" if full_path.startswith("assets/") else "no-cache"
            return FileResponse(fp, headers={"Cache-Control": cache_control})
        return FileResponse(os.path.join(sd, "index.html"), headers={"Cache-Control": "no-cache"})

# ── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_collector():
    from state_collector import start_collector
    start_collector()
    from services.alert_worker import start_alert_worker
    start_alert_worker()

# ── WebSocket (event-driven) ───────────────────────────────────────────────

@app.websocket("/api/ws")
async def ws_dashboard(ws: WebSocket, token: str = Query("")):
    from api.auth import get_current_user, require_auth
    from event_bus import register_subscriber, unregister_subscriber, get_full_state

    # WebSocket can't carry Authorization header — validate via query token
    if not token:
        await ws.accept()
        await ws.send_text(json.dumps({"type": "error", "detail": "Missing token"}))
        await ws.close(code=4401)
        return
    try:
        user = await get_current_user(token)
    except Exception:
        user = None
    if user is None:
        await ws.accept()
        await ws.send_text(json.dumps({"type": "error", "detail": "Invalid token"}))
        await ws.close(code=4401)
        return

    await ws.accept()
    queue = register_subscriber()
    try:
        # Send full snapshot on connect
        await ws.send_text(json.dumps(get_full_state()))
        while True:
            try:
                # queue is thread-safe (queue.Queue); block via to_thread
                msg = await asyncio.wait_for(asyncio.to_thread(queue.get), timeout=30)
                await ws.send_text(msg)
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"type": "ping"}))
            except queue.Empty:
                pass
    except Exception as e:
        logger.debug("ws_dashboard disconnected: %s", e)
    finally:
        unregister_subscriber(queue)
        try:
            await ws.close()
        except Exception:
            pass

@app.websocket("/api/terminal")
async def terminal_shell(ws: WebSocket, token: str = Query("")):
    """WebSocket shell — gated by RNAS_FEATURE_TERMINAL env flag, requires JWT."""
    if not FEATURE_FLAGS.get("web_terminal", False):
        await ws.accept()
        await ws.send_text("Terminal is disabled. Set RNAS_FEATURE_TERMINAL=true to enable.")
        await ws.close()
        return
    from api.auth import get_current_user
    if not token:
        await ws.accept()
        await ws.send_text("Authentication required.")
        await ws.close(code=4401)
        return
    try:
        user = await get_current_user(token)
    except Exception:
        user = None
    if user is None:
        await ws.accept()
        await ws.send_text("Invalid token.")
        await ws.close(code=4401)
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

