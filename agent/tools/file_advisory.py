"""
agent/tools/file_advisory.py
Creates structured avoidance advisory records and logs all agent decisions.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

ADVISORIES_FILE = Path("data/advisories.json")
DECISIONS_FILE = Path("data/decisions.jsonl")

# In-memory store for SSE streaming to dashboard
_advisory_subscribers = []
_latest_events = []


def register_subscriber(queue):
    """Register a FastAPI SSE queue to receive live events."""
    _advisory_subscribers.append(queue)


def unregister_subscriber(queue):
    """Remove a subscriber when their connection closes."""
    if queue in _advisory_subscribers:
        _advisory_subscribers.remove(queue)


def _broadcast(event: dict):
    """Push event to all connected SSE clients."""
    _latest_events.append(event)
    if len(_latest_events) > 100:
        _latest_events.pop(0)
    for queue in _advisory_subscribers:
        try:
            queue.put_nowait(event)
        except Exception:
            pass


def file_advisory(conjunction: dict, classification: dict) -> dict:
    """
    Create and store an avoidance advisory.

    Args:
        conjunction: output from compute_conjunction()
        classification: output from classify_risk()

    Returns:
        The advisory record dict with advisory_id
    """
    advisory_id = f"ADV-{str(uuid.uuid4())[:8].upper()}"

    advisory = {
        "advisory_id": advisory_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "satellite_name": conjunction["satellite_name"],
        "debris_name": conjunction["debris_name"],
        "risk_level": classification["risk_level"],
        "min_distance_km": conjunction["min_distance_km"],
        "time_of_closest_approach": conjunction["time_of_closest_approach"],
        "closing_velocity_kmps": conjunction.get("closing_velocity_kmps", 0),
        "satellite_alt_km": conjunction.get("satellite_alt_km", 0),
        "collision_probability_pct": classification.get("collision_probability_pct", 0),
        "reasoning": classification["reasoning"],
        "recommended_action": classification["recommended_action"],
        "urgency_hours": classification.get("urgency_hours", 72),
        "status": "OPEN",
        "injected": conjunction.get("injected", False),
    }

    # Persist to file
    ADVISORIES_FILE.parent.mkdir(exist_ok=True)
    advisories = _load_advisories()
    advisories.insert(0, advisory)  # newest first
    with open(ADVISORIES_FILE, "w") as f:
        json.dump(advisories, f, indent=2)

    # Broadcast to SSE subscribers
    _broadcast({
        "type": "advisory",
        "data": advisory,
    })

    print(f"  Advisory filed: {advisory_id} | {classification['risk_level']} | {conjunction['satellite_name']} ↔ {conjunction['debris_name']}")
    return advisory


def log_decision(
    conjunction: dict,
    classification: dict,
    advisory: dict,
    duration_ms: float,
) -> dict:
    """
    Append a full decision record to decisions.jsonl.
    This is the audit trail judges will review.

    Args:
        conjunction: raw conjunction data
        classification: LLM classification
        advisory: filed advisory
        duration_ms: how long the full agent decision took

    Returns:
        The decision record
    """
    decision = {
        "decision_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "satellite_name": conjunction["satellite_name"],
        "debris_name": conjunction["debris_name"],
        "min_distance_km": conjunction["min_distance_km"],
        "risk_level": classification["risk_level"],
        "collision_probability_pct": classification.get("collision_probability_pct", 0),
        "reasoning": classification["reasoning"],
        "recommended_action": classification["recommended_action"],
        "advisory_id": advisory["advisory_id"],
        "action_taken": f"Filed advisory {advisory['advisory_id']} | Status: {advisory['status']}",
        "duration_ms": round(duration_ms, 1),
        "agent": "DebrisWatch-v1",
    }

    DECISIONS_FILE.parent.mkdir(exist_ok=True)
    with open(DECISIONS_FILE, "a") as f:
        f.write(json.dumps(decision) + "\n")

    # Broadcast decision to dashboard
    _broadcast({
        "type": "decision",
        "data": decision,
    })

    return decision


def get_advisories(limit: int = 50) -> list:
    """Load advisories from file."""
    return _load_advisories()[:limit]


def get_decisions(limit: int = 50) -> list:
    """Load decisions from JSONL file."""
    if not DECISIONS_FILE.exists():
        return []
    decisions = []
    with open(DECISIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    decisions.append(json.loads(line))
                except Exception:
                    pass
    return list(reversed(decisions))[:limit]


def get_latest_events(limit: int = 20) -> list:
    """Return recent in-memory events for new SSE connections."""
    return _latest_events[-limit:]


def _load_advisories() -> list:
    if not ADVISORIES_FILE.exists():
        return []
    try:
        with open(ADVISORIES_FILE) as f:
            return json.load(f)
    except Exception:
        return []
