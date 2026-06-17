"""
api/main.py
FastAPI backend for DebrisWatch.

Endpoints:
  GET  /              — health check
  GET  /stream        — SSE live event stream (dashboard connects here)
  GET  /advisories    — list all advisories
  GET  /decisions     — list all agent decisions
  GET  /state         — current agent state
  POST /inject-conjunction — trigger CRITICAL demo event
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from agent.loop import start_agent_background, trigger_injection, get_state, stop_agent
from agent.tools.file_advisory import (
    get_advisories,
    get_decisions,
    get_latest_events,
    register_subscriber,
    unregister_subscriber,
)


# ── Lifespan: start agent when API starts ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the autonomous agent on server startup."""
    print("\n[API] Starting DebrisWatch API...")
    start_agent_background(scan_interval=30)
    yield
    print("\n[API] Shutting down...")
    stop_agent()


# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DebrisWatch API",
    description="Autonomous orbital debris collision risk agent — FAR AWAY 2026",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────

class InjectRequest(BaseModel):
    satellite_name: str = "ISRO RISAT-2BR1"
    debris_name: str = "COSMOS 2251 DEB"


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
async def health():
    return {
        "status": "online",
        "service": "DebrisWatch",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": get_state(),
    }


@app.get("/stream")
async def event_stream():
    """
    Server-Sent Events stream.
    Dashboard connects here and receives live advisories + decisions.
    """
    queue = asyncio.Queue()
    register_subscriber(queue)

    # Send recent history to new connections immediately
    recent = get_latest_events(limit=10)

    async def generator():
        try:
            # Send recent events first
            for event in recent:
                yield f"data: {json.dumps(event)}\n\n"

            # Then stream live events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat', 'ts': datetime.utcnow().isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unregister_subscriber(queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/advisories")
async def list_advisories(limit: int = 50):
    """Return all filed advisories, newest first."""
    return JSONResponse({"advisories": get_advisories(limit), "count": limit})


@app.get("/decisions")
async def list_decisions(limit: int = 50):
    """Return all agent decisions with full reasoning, newest first."""
    return JSONResponse({"decisions": get_decisions(limit), "count": limit})


@app.get("/state")
async def agent_state():
    """Return current agent status."""
    return JSONResponse(get_state())


@app.post("/inject-conjunction")
async def inject_conjunction(body: InjectRequest = None):
    """
    DEMO ENDPOINT: Triggers a forced CRITICAL conjunction event.
    Simulates a real emergency — agent responds autonomously within seconds.
    """
    sat = body.satellite_name if body else "ISRO RISAT-2BR1"
    deb = body.debris_name if body else "COSMOS 2251 DEB"

    trigger_injection(sat, deb)

    return JSONResponse({
        "status": "injection_triggered",
        "message": f"CRITICAL conjunction injected: {sat} ↔ {deb}",
        "note": "Watch the dashboard — advisory will appear within 3 seconds",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.get("/stats")
async def get_stats():
    """Return summary statistics."""
    advisories = get_advisories(1000)
    decisions = get_decisions(1000)

    risk_counts = {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0}
    for a in advisories:
        level = a.get("risk_level", "LOW")
        risk_counts[level] = risk_counts.get(level, 0) + 1

    return JSONResponse({
        "total_advisories": len(advisories),
        "total_decisions": len(decisions),
        "risk_breakdown": risk_counts,
        "agent_state": get_state(),
    })
