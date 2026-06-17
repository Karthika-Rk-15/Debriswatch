#!/bin/bash
# DebrisWatch - one command setup and launch
# Usage: bash quickstart.sh

set -e

echo "================================================"
echo "  DEBRISWATCH — QUICKSTART"
echo "  FAR AWAY 2026 — Round 1 Submission Setup"
echo "================================================"
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.11+ first."
    exit 1
fi
echo "[1/6] Python found: $(python3 --version)"

# 2. Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[2/6] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[2/6] Virtual environment already exists, skipping."
fi

# 3. Activate venv
source venv/bin/activate || source venv/Scripts/activate
echo "[3/6] Virtual environment activated."

# 4. Install dependencies
echo "[4/6] Installing dependencies (this may take a minute)..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "      Dependencies installed."

# 5. Check .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found."
    echo "  Run: cp .env.example .env"
    echo "  Then add your ANTHROPIC_API_KEY before continuing."
    echo "  Get a free key at: https://console.anthropic.com"
    echo ""
    read -p "Press Enter once you've created .env, or Ctrl+C to exit..."
fi
echo "[5/6] Environment configured."

# 6. Fetch TLE data
echo "[6/6] Fetching orbital data from Celestrak..."
python3 data/fetch_tle.py

echo ""
echo "================================================"
echo "  SETUP COMPLETE"
echo "================================================"
echo ""
echo "Starting the API + autonomous agent..."
echo "  -> API will run at:        http://localhost:8000"
echo "  -> API docs available at:  http://localhost:8000/docs"
echo ""
echo "NEXT STEP: Open frontend/index.html in your browser"
echo "  (just double-click the file, no server needed)"
echo ""
echo "DEMO: Click 'Inject Critical Conjunction' button on"
echo "      the AI Agent or Console page to trigger the demo"
echo ""
echo "Press Ctrl+C to stop the agent."
echo "================================================"
echo ""

uvicorn api.main:app --reload --port 8000
