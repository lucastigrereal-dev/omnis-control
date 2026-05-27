"""OMNIS API — Servidor HTTP para KRATOS.

Expõe dados operacionais do OMNIS via HTTP.
KRATOS lê daqui. OMNIS nunca escreve via API.

Uso:
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8765 --reload
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import health, queue, accounts, drafts, assets, missions, skills, reports, agent
from src.api.routers.webhooks import router as webhooks_router
from src.api.routers.marketing import router as marketing_router
from src.api.routers.aurora import router as aurora_router
from src.api.routers.cost import router as cost_router
from src.api.routers.events import router as events_router
from src.api.auth import dev_mode
from src.api.structured_logging import StructuredLoggingMiddleware, setup_logging

setup_logging()

app = FastAPI(
    title="OMNIS API",
    description="Data API para KRATOS cockpit — W19: Structured Logging + Budget Guardrail",
    version="1.3.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(StructuredLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

app.include_router(health.router,      prefix="/health",    tags=["health"])
app.include_router(queue.router,       prefix="/queue",     tags=["queue"])
app.include_router(accounts.router,    prefix="/accounts",  tags=["accounts"])
app.include_router(drafts.router,      prefix="/drafts",    tags=["drafts"])
app.include_router(assets.router,      prefix="/assets",    tags=["assets"])
app.include_router(missions.router,    prefix="/missions",  tags=["missions"])
app.include_router(skills.router,      prefix="/skills",    tags=["skills"])
app.include_router(reports.router,     prefix="/reports",   tags=["reports"])
app.include_router(agent.router,       prefix="/agent",     tags=["agent"])
app.include_router(webhooks_router,    prefix="/webhooks",  tags=["webhooks"])
app.include_router(marketing_router,   prefix="/marketing", tags=["marketing"])
app.include_router(aurora_router,      prefix="/aurora",    tags=["aurora"])
app.include_router(cost_router,        prefix="/cost",      tags=["cost"])
app.include_router(events_router,      prefix="/events",    tags=["events"])

# v1 versioned contract (read-only integration surface for KRATOS)
app.include_router(missions.router,    prefix="/v1/missions", tags=["v1-missions"])
app.include_router(events_router,      prefix="/v1/events",   tags=["v1-events"])

# legacy live alias used by KRATOS current hooks
app.include_router(events_router,      prefix="/live",      tags=["live-events"])


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "omnis-api",
        "version": "1.3.0",
        "status": "ok",
        "auth": "dev" if dev_mode() else "required",
    }
