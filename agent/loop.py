"""
agent/loop.py
The autonomous DebrisWatch agent loop.

This is the brain of the system. It:
1. Loads TLE orbital data
2. Computes conjunctions between satellites and debris
3. Classifies risk using Claude LLM
4. Files advisories autonomously
5. Logs every decision
6. Repeats forever (or for N cycles)

No human in the loop per decision. That's what makes it agentic.
"""

import time
import json
import threading
from datetime import datetime
from pathlib import Path

from agent.tools.compute_conjunction import compute_conjunction, inject_critical_conjunction
from agent.tools.classify_risk import classify_risk
from agent.tools.file_advisory import file_advisory, log_decision


# Global flag to inject a forced critical event (demo trigger)
_inject_flag = {"active": False, "satellite": "ISRO RISAT-2BR1", "debris": "COSMOS 2251 DEB"}

# Agent state
_agent_state = {
    "running": False,
    "cycle": 0,
    "last_run": None,
    "total_advisories": 0,
    "total_decisions": 0,
    "status": "idle",
}


def trigger_injection(satellite: str = "ISRO RISAT-2BR1", debris: str = "COSMOS 2251 DEB"):
    """
    Called by POST /inject-conjunction to force a CRITICAL demo event.
    Thread-safe flag set.
    """
    _inject_flag["active"] = True
    _inject_flag["satellite"] = satellite
    _inject_flag["debris"] = debris
    print(f"\n[DEMO] Injection triggered: {satellite} ↔ {debris}")


def get_state() -> dict:
    """Return current agent state for the dashboard."""
    return {**_agent_state, "last_run": _agent_state["last_run"]}


def _load_tles() -> dict:
    """Load TLE data from file, or fetch if not available."""
    tle_path = Path("data/tles.json")
    if tle_path.exists():
        with open(tle_path) as f:
            return json.load(f)

    print("TLE file not found — fetching from Celestrak...")
    from data.fetch_tle import save_tles
    return save_tles()


def _process_pair(satellite: dict, debris: dict) -> dict | None:
    """
    Full agent decision pipeline for one satellite-debris pair.
    Returns advisory if risk >= MEDIUM, else None.
    """
    start_ms = time.time() * 1000

    # Step 1: Compute orbital conjunction
    print(f"  Computing: {satellite['name']} ↔ {debris['name']}")
    conjunction = compute_conjunction(satellite, debris)

    # Step 2: Classify risk with LLM
    classification = classify_risk(conjunction)
    risk = classification["risk_level"]

    print(f"    → {risk} | {conjunction['min_distance_km']}km | {classification['reasoning'][:80]}...")

    # Step 3: Act based on severity
    if risk == "LOW":
        # Log but don't file advisory
        duration_ms = time.time() * 1000 - start_ms
        log_decision(conjunction, classification, {"advisory_id": "N/A", "status": "LOGGED_ONLY"}, duration_ms)
        return None

    # Step 4: File advisory (MEDIUM or CRITICAL)
    advisory = file_advisory(conjunction, classification)

    # Step 5: Log full decision
    duration_ms = time.time() * 1000 - start_ms
    log_decision(conjunction, classification, advisory, duration_ms)

    _agent_state["total_advisories"] += 1
    _agent_state["total_decisions"] += 1

    return advisory


def run_cycle(tles: dict) -> list:
    """
    Run one full scan cycle across all satellite-debris pairs.
    Returns list of advisories filed this cycle.
    """
    advisories = []
    satellites = tles.get("active_satellites", [])
    debris_list = tles.get("debris", [])

    print(f"\n[CYCLE {_agent_state['cycle']}] Scanning {len(satellites)} satellites × {len(debris_list)} debris objects...")

    for satellite in satellites:
        for debris in debris_list:
            try:
                advisory = _process_pair(satellite, debris)
                if advisory:
                    advisories.append(advisory)
            except Exception as e:
                print(f"  Error processing {satellite['name']} ↔ {debris['name']}: {e}")

    return advisories


def agent_loop(scan_interval_seconds: int = 30, max_cycles: int = None):
    """
    Main autonomous agent loop. Runs indefinitely until stopped.

    Args:
        scan_interval_seconds: seconds between full scans (default 30s for demo)
        max_cycles: stop after N cycles (None = run forever)
    """
    print("\n" + "="*60)
    print("  DEBRISWATCH AUTONOMOUS AGENT — STARTING")
    print("  Monitoring orbital debris 24/7")
    print("="*60 + "\n")

    _agent_state["running"] = True
    _agent_state["status"] = "scanning"

    # Load TLE data once at startup
    tles = _load_tles()
    print(f"Loaded {len(tles.get('active_satellites', []))} satellites, {len(tles.get('debris', []))} debris objects\n")

    cycle = 0

    while _agent_state["running"]:
        # Check for demo injection trigger
        if _inject_flag["active"]:
            print(f"\n[DEMO INJECTION] Forcing CRITICAL conjunction...")
            _inject_flag["active"] = False

            # Create injected conjunction
            conj = inject_critical_conjunction(
                _inject_flag["satellite"],
                _inject_flag["debris"]
            )
            classification = classify_risk(conj)
            # Override to CRITICAL for demo reliability
            classification["risk_level"] = "CRITICAL"
            classification["collision_probability_pct"] = 23.7
            classification["urgency_hours"] = 6
            classification["reasoning"] = (
                f"INJECTED DEMO EVENT: {conj['satellite_name']} and {conj['debris_name']} "
                f"will approach within {conj['min_distance_km']}km at {conj['closing_velocity_kmps']}km/s "
                f"closing velocity. At this distance and speed, probability of catastrophic collision "
                f"is 23.7%. Immediate avoidance maneuver required within 6 hours."
            )
            classification["recommended_action"] = (
                "Execute emergency avoidance maneuver immediately. "
                "Burn 2.3 m/s delta-v to raise perigee by 3km. "
                "Alert ISRO mission control and ground stations."
            )

            advisory = file_advisory(conj, classification)
            log_decision(conj, classification, advisory, 850.0)
            _agent_state["total_advisories"] += 1
            _agent_state["total_decisions"] += 1

            print(f"[DEMO] Advisory filed: {advisory['advisory_id']} — CRITICAL")

        # Regular scan cycle
        _agent_state["cycle"] = cycle
        _agent_state["last_run"] = datetime.utcnow().isoformat() + "Z"
        _agent_state["status"] = "scanning"

        try:
            advisories = run_cycle(tles)
            print(f"\n  Cycle {cycle} complete. Filed {len(advisories)} advisories.")
        except Exception as e:
            print(f"  Cycle {cycle} error: {e}")

        _agent_state["status"] = f"sleeping ({scan_interval_seconds}s)"
        cycle += 1

        if max_cycles and cycle >= max_cycles:
            break

        # Wait for next cycle (check injection every second)
        for _ in range(scan_interval_seconds):
            if _inject_flag["active"] or not _agent_state["running"]:
                break
            time.sleep(1)

    _agent_state["running"] = False
    _agent_state["status"] = "stopped"
    print("\n[AGENT] DebrisWatch stopped.")


def start_agent_background(scan_interval: int = 30):
    """Start the agent loop in a background thread (called by FastAPI on startup)."""
    thread = threading.Thread(
        target=agent_loop,
        kwargs={"scan_interval_seconds": scan_interval},
        daemon=True,
        name="DebrisWatchAgent",
    )
    thread.start()
    print("[AGENT] Background agent thread started.")
    return thread


def stop_agent():
    """Signal the agent to stop."""
    _agent_state["running"] = False
