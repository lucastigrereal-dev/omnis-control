"""OMNIS API — Servidor HTTP mínimo read-only para KRATOS.

Expõe dados operacionais do OMNIS via HTTP.
KRATOS lê daqui. OMNIS nunca escreve via API.

Uso:
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8765 --reload
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import health, queue, accounts, drafts, assets, missions, skills, reports, agent

app = FastAPI(
    title="OMNIS API",
    description="Read-only data API para KRATOS cockpit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/health",   tags=["health"])
app.include_router(queue.router,    prefix="/queue",    tags=["queue"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
app.include_router(drafts.router,   prefix="/drafts",   tags=["drafts"])
app.include_router(assets.router,   prefix="/assets",   tags=["assets"])
app.include_router(missions.router, prefix="/missions", tags=["missions"])
app.include_router(skills.router,   prefix="/skills",   tags=["skills"])
app.include_router(reports.router,  prefix="/reports",  tags=["reports"])
app.include_router(agent.router,    prefix="/agent",    tags=["agent"])


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"service": "omnis-api", "version": "1.0.0", "status": "ok"}
