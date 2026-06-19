"""RNAS Management API — FastAPI application with full endpoint coverage."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import status, config, tools, system as sys_routes, aaa, sim

app = FastAPI(title="RNAS API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router, prefix="/api", tags=["Status & Sessions"])
app.include_router(config.router, prefix="/api", tags=["Configuration"])
app.include_router(tools.router, prefix="/api", tags=["Tools"])
app.include_router(sys_routes.router, prefix="/api", tags=["System & Network"])
app.include_router(aaa.router, prefix="/api", tags=["AAA & RADIUS"])
app.include_router(sim.router, prefix="/api", tags=["Simulation"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}
