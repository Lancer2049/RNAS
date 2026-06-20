import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from routes import status, config, tools, system as sys_routes, aaa, sim, extra

app = FastAPI(title="RNAS API", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}

app.include_router(status.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(sys_routes.router, prefix="/api")
app.include_router(aaa.router, prefix="/api")
app.include_router(sim.router, prefix="/api")
app.include_router(extra.router, prefix="/api")

# Hotspot login POST
@app.post("/hotspot/login")
async def hotspot_login(request: Request):
    import subprocess as _sp
    body = await request.body()
    from urllib.parse import parse_qs
    params = parse_qs(body.decode())
    user = params.get("username", [""])[0]
    pwd = params.get("password", [""])[0]
    if not user:
        return PlainTextResponse("Missing username", status_code=400)
    payload = f"User-Name={user},User-Password={pwd}"
    result = _sp.run(["radclient", "-r", "1", "-t", "3", "192.168.0.202:1812", "auth", "testing123"],
                     input=payload, capture_output=True, text=True, timeout=10)
    ok = "Access-Accept" in result.stdout
    return PlainTextResponse("Authenticated" if ok else "Access Denied", status_code=302 if ok else 403)

# Static files — only for non-API paths
sd = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(sd):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("hotspot/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        fp = os.path.join(sd, full_path if full_path else "index.html")
        if os.path.isfile(fp) and not fp.endswith(".py"):
            return FileResponse(fp)
        return FileResponse(os.path.join(sd, "index.html"))
