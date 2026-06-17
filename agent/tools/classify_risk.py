"""
agent/tools/classify_risk.py
Sends conjunction data to Claude LLM and gets back:
- risk level: LOW / MEDIUM / CRITICAL
- detailed reasoning explaining the risk
- recommended action
"""

import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are DebrisWatch — an expert orbital debris risk analyst AI embedded in an autonomous satellite safety system.

You receive conjunction data (close approach events between active satellites and space debris) and must classify the collision risk.

RISK CLASSIFICATION RULES:
- CRITICAL: distance < 5km OR closing velocity > 10 km/s AND distance < 10km — immediate avoidance maneuver required
- MEDIUM: distance 5–25km — monitor closely, prepare contingency
- LOW: distance > 25km — log only, no action needed

You must respond ONLY with valid JSON in this exact format:
{
  "risk_level": "CRITICAL" | "MEDIUM" | "LOW",
  "reasoning": "A detailed 2-3 sentence explanation of why this risk level was assigned, referencing the specific numbers",
  "recommended_action": "Specific action the satellite operator should take",
  "collision_probability_pct": <float between 0 and 100>,
  "urgency_hours": <int — how many hours until action must be taken>
}

Be precise, technical, and reference actual values from the input data. Never be vague."""


def classify_risk(conjunction: dict) -> dict:
    """
    Classify collision risk using Claude LLM.

    Args:
        conjunction: output from compute_conjunction()

    Returns:
        {
            "risk_level": "CRITICAL"|"MEDIUM"|"LOW",
            "reasoning": str,
            "recommended_action": str,
            "collision_probability_pct": float,
            "urgency_hours": int,
        }
    """
    prompt = f"""Analyse this conjunction event and classify the collision risk:

Satellite: {conjunction['satellite_name']}
Debris Object: {conjunction['debris_name']}
Minimum Approach Distance: {conjunction['min_distance_km']} km
Time of Closest Approach: {conjunction['time_of_closest_approach']}
Satellite Altitude: {conjunction['satellite_alt_km']} km
Debris Altitude: {conjunction['debris_alt_km']} km
Closing Velocity: {conjunction['closing_velocity_kmps']} km/s

Classify the risk and provide your analysis in the required JSON format."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return result

    except json.JSONDecodeError:
        # Fallback: rule-based classification if LLM response is malformed
        return _rule_based_classify(conjunction)
    except Exception as e:
        print(f"LLM call failed: {e}, using rule-based fallback")
        return _rule_based_classify(conjunction)


def _rule_based_classify(conjunction: dict) -> dict:
    """Rule-based fallback if LLM is unavailable."""
    dist = conjunction["min_distance_km"]
    vel = conjunction.get("closing_velocity_kmps", 7.5)

    if dist < 5 or (dist < 10 and vel > 10):
        level = "CRITICAL"
        action = "Initiate emergency avoidance maneuver immediately. Alert satellite operators."
        prob = round(max(0.1, min(99.9, 100 - dist * 8)), 2)
        urgency = 2
        reasoning = (
            f"Minimum approach distance of {dist}km is below the 5km critical threshold. "
            f"At {vel}km/s closing velocity, collision is imminent without intervention. "
            f"This represents a catastrophic risk to the spacecraft."
        )
    elif dist < 25:
        level = "MEDIUM"
        action = "Monitor conjunction closely. Prepare avoidance maneuver as contingency."
        prob = round(max(0.01, min(10, 50 / dist)), 2)
        urgency = 24
        reasoning = (
            f"Minimum approach distance of {dist}km falls in the medium risk zone (5–25km). "
            f"At {vel}km/s closing velocity, the situation warrants close monitoring. "
            f"No immediate action needed but avoidance maneuver should be prepared."
        )
    else:
        level = "LOW"
        action = "Log event. No immediate action required."
        prob = round(max(0.001, 1 / dist), 3)
        urgency = 72
        reasoning = (
            f"Minimum approach distance of {dist}km is above the 25km monitoring threshold. "
            f"Risk of collision is negligible at this separation distance. "
            f"Standard logging and monitoring protocols apply."
        )

    return {
        "risk_level": level,
        "reasoning": reasoning,
        "recommended_action": action,
        "collision_probability_pct": prob,
        "urgency_hours": urgency,
    }
