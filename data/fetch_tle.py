"""
fetch_tle.py
Downloads real TLE orbital data from Celestrak (free, no login needed).
Saves active satellites + debris objects locally for the agent to use.
"""

import requests
import json
from pathlib import Path

# Celestrak URLs — free, real NASA-standard TLE data
SOURCES = {
    "active_satellites": "https://celestrak.org/SOCRATES/query.php?catalog=active&format=tle",
    "debris": "https://celestrak.org/SOCRATES/query.php?catalog=cosmos-2251-debris&format=tle",
}

# Fallback hardcoded TLEs if internet is unavailable (demo-safe)
FALLBACK_TLES = {
    "active_satellites": [
        {
            "name": "ISRO RISAT-2BR1",
            "line1": "1 44233U 19028A   24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 44233  37.0000  60.0000 0010000  90.0000 270.0000 15.00000000000000",
        },
        {
            "name": "ISRO CARTOSAT-3",
            "line1": "1 44804U 19073A   24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 44804  97.5000 120.0000 0001000  90.0000 270.0000 14.90000000000000",
        },
        {
            "name": "ISS (ZARYA)",
            "line1": "1 25544U 98067A   24001.50000000  .00020000  00000-0  00000-0 0  9999",
            "line2": "2 25544  51.6400  80.0000 0001000  90.0000 270.0000 15.50000000000000",
        },
    ],
    "debris": [
        {
            "name": "COSMOS 2251 DEB",
            "line1": "1 34427U 93036RU  24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 34427  74.0000 100.0000 0050000  60.0000 300.0000 14.30000000000000",
        },
        {
            "name": "FENGYUN 1C DEB",
            "line1": "1 29228U 99025ADU 24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 29228  98.6000 140.0000 0020000  45.0000 315.0000 14.20000000000000",
        },
        {
            "name": "IRIDIUM 33 DEB",
            "line1": "1 33766U 97051CJ  24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 33766  86.4000 200.0000 0010000  30.0000 330.0000 14.40000000000000",
        },
        {
            "name": "SL-16 R/B",
            "line1": "1 22285U 92093B   24001.50000000  .00000000  00000-0  00000-0 0  9999",
            "line2": "2 22285  71.0000 160.0000 0030000  75.0000 285.0000 14.10000000000000",
        },
    ],
}


def parse_tle_text(text: str) -> list[dict]:
    """Parse raw TLE text into list of {name, line1, line2} dicts."""
    objects = []
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    i = 0
    while i < len(lines) - 2:
        if not lines[i].startswith("1 ") and not lines[i].startswith("2 "):
            name = lines[i]
            if i + 2 < len(lines) and lines[i+1].startswith("1 ") and lines[i+2].startswith("2 "):
                objects.append({"name": name, "line1": lines[i+1], "line2": lines[i+2]})
                i += 3
                continue
        i += 1
    return objects


def fetch_tles(use_fallback: bool = False) -> dict:
    """
    Fetch TLE data from Celestrak.
    Falls back to hardcoded data if network unavailable.
    """
    if use_fallback:
        print("Using fallback TLE data (offline mode)")
        return FALLBACK_TLES

    result = {}
    for key, url in SOURCES.items():
        try:
            print(f"Fetching {key} from Celestrak...")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.text) > 100:
                parsed = parse_tle_text(resp.text)
                # Limit to first 20 for performance in demo
                result[key] = parsed[:20]
                print(f"  Got {len(result[key])} objects for {key}")
            else:
                raise ValueError(f"Bad response: {resp.status_code}")
        except Exception as e:
            print(f"  Network unavailable ({e}), using fallback for {key}")
            result[key] = FALLBACK_TLES[key]

    return result


def save_tles(output_dir: str = "data") -> dict:
    """Fetch and save TLEs to JSON files. Returns the data."""
    Path(output_dir).mkdir(exist_ok=True)
    data = fetch_tles()

    out_path = Path(output_dir) / "tles.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved TLE data to {out_path}")
    print(f"  Active satellites: {len(data['active_satellites'])}")
    print(f"  Debris objects:    {len(data['debris'])}")
    return data


if __name__ == "__main__":
    save_tles()
