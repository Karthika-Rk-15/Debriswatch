<div align="center">

# 🛰️ DebrisWatch

### Autonomous Orbital Debris Collision Risk Agent

**FAR AWAY 2026 — India's Biggest International Hackathon**
**Theme: Space & Aerospace × Agentic & Autonomous Systems**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Claude](https://img.shields.io/badge/Claude-Sonnet-purple?style=flat-square)](https://anthropic.com)
[![Skyfield](https://img.shields.io/badge/Skyfield-1.46-orange?style=flat-square)](https://rhodesmill.org/skyfield)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

*"Space is not empty. It is a junkyard hurtling at 28,000 km/h — and it's getting worse."*

[Demo Video](#demo) · [Architecture](#architecture) · [Setup](#setup) · [API Reference](#api)

</div>

---

## The Problem

Space debris is one of the most critical and underreported threats to modern civilisation. Every smartphone, weather forecast, GPS navigation, and internet connection depends on satellites orbiting alongside **27,000+ tracked debris objects** — each travelling at 28,000 km/h. A collision at that speed is catastrophic, and each collision creates thousands more fragments (the Kessler Syndrome).

| Scale of the problem | Numbers |
|---|---|
| Tracked debris objects in orbit | **27,000+** |
| Untracked objects > 1cm (each capable of destroying a satellite) | **500,000+** |
| Global satellite industry at risk | **$369 Billion** |
| ISRO active satellites at risk | **50+** |
| Current detection method | **Manual analyst review — slow and unscalable** |

**Current process:** Human analysts at space agencies manually review Conjunction Data Messages (CDMs) from US Space Surveillance Network. It is slow, reactive, runs during business hours only, and does not scale as debris count grows exponentially.

**DebrisWatch changes this.** It is an autonomous agent that monitors real orbital data 24/7, predicts collision risks before they become emergencies, and files avoidance advisories — all without a human analyst in the loop for every decision.

---
## Why Now?

The space environment is becoming increasingly congested due to the rapid growth of satellite mega-constellations such as Starlink, OneWeb, and upcoming commercial deployments. Thousands of new satellites are being launched every year, significantly increasing the number of potential conjunction events that must be monitored and assessed.

Traditional collision monitoring relies heavily on human analysts reviewing conjunction reports and determining whether avoidance actions are required. As the volume of orbital objects continues to grow, this approach becomes difficult to scale. Autonomous systems capable of continuously monitoring orbital activity, assessing risks, and generating actionable recommendations are becoming essential for the future of safe space operations.

DebrisWatch addresses this challenge by combining orbital mechanics, real-time monitoring, and AI-driven decision support to provide a scalable approach to space traffic management and satellite safety.

---
## Solution

DebrisWatch is a **fully autonomous multi-tool AI agent** that:

1. **Ingests** real TLE (Two-Line Element) orbital data from Celestrak — the same data NASA and ISRO use
2. **Computes** conjunction events: moments when a satellite and debris object will come dangerously close, over a 72-hour prediction window
3. **Classifies** collision risk using Claude LLM with full contextual reasoning (distance, velocity, orbital zone, object type)
4. **Acts autonomously** — filing structured avoidance advisories, logging decisions with complete AI reasoning, and pushing live alerts to a mission control dashboard
5. **Repeats** continuously, every 30 seconds, with no human click required per decision

> *"The goal is not to write every line of code yourself. The goal is to build something meaningful."* — FAR AWAY 2026

---

## Demo
![alt text](<Screenshot 2026-06-17 111420.png>) ![alt text](<Screenshot 2026-06-17 110031.png>) ![alt text](<Screenshot 2026-06-17 110107.png>) ![alt text](<Screenshot 2026-06-17 110203.png>) ![alt text](<Screenshot 2026-06-17 110223.png>) ![alt text](<Screenshot 2026-06-17 110237.png>) ![alt text](<Screenshot 2026-06-17 110301.png>)
### The demo moment

```
POST /inject-conjunction

  Agent wakes up
  → compute_conjunction()  : ISRO RISAT-2BR1 ↔ COSMOS 2251 DEB → 1.8km closest approach
  → classify_risk()        : Claude LLM → CRITICAL | P(collision) = 23.7%
  → file_advisory()        : ADV-A3F9C2B1 filed
  → log_decision()         : Full reasoning logged to decisions.jsonl
  → SSE push               : Red alert appears on dashboard
  
  Total time: < 3 seconds. Zero human clicks.
```

### Dashboard

The live mission control dashboard shows:

- **Orbital conjunction map** — animated 2D orbital view with real-time conjunction flashes
- **Live advisory feed** — colour-coded CRITICAL / MEDIUM / LOW cards with full LLM reasoning
- **Decision log** — every autonomous agent decision with satellite pair, distance, risk, and response time
- **One-click demo trigger** — inject a forced CRITICAL conjunction and watch the agent respond

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 1 — DATA INGESTION                      │
│                                                                  │
│   Celestrak TLE API  ──►  fetch_tle.py  ──►  data/tles.json     │
│   (27,000+ objects)       (parser)           (local cache)       │
│                                                                  │
│   POST /inject-conjunction  ──►  Forced demo event               │
└──────────────────────────────────┬───────────────────────────────┘
                                   │  TLE data + events
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                LAYER 2 — AUTONOMOUS AGENT CORE                   │
│                                                                  │
│   agent/loop.py  (LangGraph orchestrator)                        │
│        │                                                         │
│        ├── compute_conjunction()  Skyfield orbital mechanics      │
│        │   └── min approach distance over 72hr window            │
│        │                                                         │
│        ├── classify_risk()        Claude claude-sonnet-4-6 LLM   │
│        │   └── risk level + reasoning + recommended action        │
│        │                                                         │
│        ├── file_advisory()        Structured advisory record      │
│        │   └── advisories.json + SSE broadcast                   │
│        │                                                         │
│        └── log_decision()         Full audit trail               │
│            └── decisions.jsonl (every decision, forever)         │
└──────────────────────────────────┬───────────────────────────────┘
                                   │  advisories + decisions
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│              LAYER 3 — OUTPUTS & OBSERVABILITY                   │
│                                                                  │
│   FastAPI (api/main.py)                                          │
│     GET  /stream          ──►  SSE live event stream             │
│     GET  /advisories      ──►  All filed advisories              │
│     GET  /decisions       ──►  Full decision log with reasoning  │
│     GET  /state           ──►  Agent health + cycle count        │
│     POST /inject-conjunction ►  Demo trigger                     │
│                                                                  │
│   frontend/index.html     ──►  Mission control dashboard         │
│     Orbital map · Advisory feed · Decision log · Inject button   │
└──────────────────────────────────────────────────────────────────┘
```

### Agent decision loop

```
Load TLE data (Celestrak)
         │
         ▼
  For each satellite × debris pair:
         │
         ▼
  compute_conjunction()
  [Skyfield: propagate orbits, find min distance over 72h]
         │
         ▼
  classify_risk()  ◄── Claude LLM call with full context
  [Returns: risk_level + reasoning + recommended_action]
         │
         ├── LOW      ──► log_decision() only
         │
         ├── MEDIUM   ──► file_advisory() → log_decision()
         │
         └── CRITICAL ──► file_advisory() → log_decision()
                          → SSE broadcast → dashboard alert
                                   │
                                   ▼
                         sleep(30s) → next cycle  ↻
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Orbital mechanics** | [Skyfield 1.46](https://rhodesmill.org/skyfield/) | Industry-standard Python orbital propagation library — same math NASA uses |
| **Orbital data** | [Celestrak TLE](https://celestrak.org) | Free, real-time, no login — 27,000+ tracked objects |
| **Agent orchestration** | Python async loop + threading | Lightweight, no external agent framework dependency |
| **LLM reasoning** | [Anthropic Claude claude-sonnet-4-6](https://anthropic.com) | Context-aware risk classification with detailed chain-of-thought reasoning |
| **API backend** | [FastAPI](https://fastapi.tiangolo.com) + SSE | Real-time streaming, auto-generated OpenAPI docs at `/docs` |
| **Frontend** | Vanilla HTML + Canvas API | Zero build step — open `index.html` in any browser |
| **Data storage** | JSONL + JSON flat files | Zero database setup — judges can inspect every decision in a text editor |
| **Environment** | Python 3.11 | Standard, reproducible |

---

## Project Structure

```
debriswatch/
│
├── README.md                         ← You are here
├── .env.example                      ← Copy to .env, add API key
├── requirements.txt                  ← pip install -r requirements.txt
│
├── agent/
│   ├── __init__.py                   ← loads .env
│   ├── loop.py                       ← main autonomous agent orchestrator
│   └── tools/
│       ├── __init__.py
│       ├── compute_conjunction.py    ← Skyfield orbital mechanics
│       ├── classify_risk.py          ← Claude LLM risk classification
│       └── file_advisory.py          ← advisory filing + decision logging + SSE
│
├── api/
│   ├── __init__.py
│   └── main.py                       ← FastAPI app, all endpoints, lifespan
│
├── data/
│   ├── fetch_tle.py                  ← Celestrak TLE downloader + fallback
│   ├── tles.json                     ← cached TLE data (auto-generated)
│   ├── advisories.json               ← filed advisories (auto-generated)
│   └── decisions.jsonl               ← full decision audit log (auto-generated)
│
├── frontend/
│   └── index.html                    ← mission control dashboard (no build needed)
│
└── docs/
    ├── architecture.png              ← system architecture diagram
    ├── agent_loop.png                ← decision flow diagram
    └── demo_screenshot.png           ← dashboard screenshot
```

---

## Setup

### Prerequisites

- Python 3.11 or higher
- An Anthropic API key — free at [console.anthropic.com](https://console.anthropic.com)
- Any modern browser (Chrome, Firefox, Safari)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/debriswatch.git
cd debriswatch
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Fetch real orbital data

```bash
python data/fetch_tle.py
# Downloads live TLE data from Celestrak
# Falls back to built-in data if offline
```

### 5. Start the agent + API

```bash
uvicorn api.main:app --reload --port 8000
```

You will see:

```
[API] Starting DebrisWatch API...
[AGENT] Background agent thread started.
DEBRISWATCH AUTONOMOUS AGENT — STARTING
Loaded 20 satellites, 4 debris objects
[CYCLE 0] Scanning 20 satellites × 4 debris objects...
```

### 6. Open the dashboard

Open `frontend/index.html` in your browser. No server needed — just double-click the file.

The dashboard connects to `localhost:8000` automatically.

### 7. Trigger the demo

In a new terminal:

```bash
curl -X POST http://localhost:8000/inject-conjunction
```

Or click the **"⚡ Inject Critical Conjunction"** button on the dashboard.

Watch the agent respond autonomously in under 3 seconds — no human click per decision.

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` when running.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check + agent state |
| `GET` | `/stream` | SSE live event stream (dashboard connects here) |
| `GET` | `/advisories` | All filed advisories, newest first |
| `GET` | `/decisions` | Full decision log with LLM reasoning |
| `GET` | `/state` | Current agent status + cycle count |
| `GET` | `/stats` | Summary statistics + risk breakdown |
| `POST` | `/inject-conjunction` | Trigger forced CRITICAL demo event |

### Sample decision record (`decisions.jsonl`)

```json
{
  "decision_id": "d7f3a1c2-9b4e-4f2a-8c1d-e5f6a7b8c9d0",
  "timestamp": "2026-06-14T08:34:15Z",
  "satellite_name": "ISRO RISAT-2BR1",
  "debris_name": "COSMOS 2251 DEB",
  "min_distance_km": 1.8,
  "risk_level": "CRITICAL",
  "collision_probability_pct": 23.7,
  "reasoning": "ISRO RISAT-2BR1 and COSMOS 2251 DEB will approach within 1.8km at 14.2km/s closing velocity. At this distance and speed, the probability of catastrophic collision is 23.7%. The debris object is a known high-risk fragment from the 2009 Cosmos-Iridium collision. Immediate avoidance maneuver required within 6 hours.",
  "recommended_action": "Execute emergency avoidance maneuver immediately. Burn 2.3 m/s delta-v to raise perigee by 3km. Alert ISRO mission control and ground stations.",
  "advisory_id": "ADV-A3F9C2B1",
  "action_taken": "Filed advisory ADV-A3F9C2B1 | Status: OPEN",
  "duration_ms": 1847.3,
  "agent": "DebrisWatch-v1"
}
```

---

## What Makes This Truly Agentic

Most teams build a classifier or a chatbot. DebrisWatch is different:

**Multi-step autonomous reasoning** — The agent does not just label data. It runs a full pipeline: orbital computation → contextual LLM analysis → decision → action → logging. Each step informs the next.

**Real tool execution** — The agent calls real functions that create real artefacts: advisory JSON records, JSONL audit entries, SSE broadcasts. These are not simulated outputs.

**Continuous autonomous loop** — The agent runs indefinitely, processing every satellite-debris pair every 30 seconds, with no human required to trigger each evaluation.

**Explainable decisions** — Every advisory includes the AI's detailed decision rationale and risk assessment explanation. Operators can review why the system classified a conjunction as CRITICAL, MEDIUM, or LOW, along with the recommended response. This makes the system transparent, trustworthy, and auditable for aerospace operations.

**Graceful degradation** — If the Anthropic API is unavailable, the agent falls back to rule-based classification and continues operating. If Celestrak is unreachable, built-in TLE data is used. The agent never stops.

---

## Judging Criteria — How DebrisWatch Scores

| Criterion | How DebrisWatch addresses it |
|---|---|
| **Innovation & Technical Depth** | Real orbital mechanics (Skyfield), LLM tool-calling agent, SSE streaming — not a chatbot wrapper |
| **Engineering Quality** | Modular architecture, graceful fallbacks, clean separation of concerns, 8+ meaningful commits |
| **Real-World Impact** | Protects $369B satellite industry including 50+ ISRO satellites; directly addresses Kessler Syndrome risk |
| **Scalability** | Stateless agent loop — deployable per orbital zone, horizontally scalable; add more TLE sources trivially |
| **Design & UX** | Live mission control dashboard with orbital map, severity colour-coding, real-time decision stream |
| **Execution Quality** | 3-command setup, working demo endpoint, full audit trail in decisions.jsonl |

---

## India & Japan Context

**India (Delhi Round 2):** ISRO operates Chandrayaan-3 relay satellites, RISAT-2BR1 (surveillance), CARTOSAT-3 (Earth observation), and the upcoming Gaganyaan crewed mission. A single debris collision could cripple national weather forecasting, crop monitoring, and border surveillance. DebrisWatch is directly relevant to ISRO's Debris Monitoring & Mitigation Centre.

**Japan (Final Round):** JAXA operates 20+ active satellites including ALOS-3 (Earth observation) and the Hayabusa sample-return mission. Japan is a leading contributor to the Inter-Agency Space Debris Coordination Committee (IADC). A debris avoidance agent has direct applicability to JAXA operations.

---

## Future Scope

- **Real MQTT integration** — live telemetry from actual ground station feeds
- **Multi-zone deployment** — separate agent instances per orbital shell (LEO, MEO, GEO) with coordinator meta-agent
- **Maneuver optimisation** — LLM suggests fuel-optimal avoidance burn parameters
- **ISRO API integration** — direct submission of advisories to ISRO's Space Situational Awareness Control Centre
- **Probabilistic ensemble** — combine LLM reasoning with Monte Carlo collision probability for higher accuracy
- **Mobile alerting** — push notifications to mission control mobile devices on CRITICAL events

---

## Team

| Name |Role|
|------------|----------------------------|
| Madhumitha N | Team Leadership, System Reliability, API Security & Deployment Strategy |
| Karthika R | Backend Development, FastAPI APIs, Autonomous Agent Workflow & System Integration |
| Kavitha S | Claude AI Integration, Risk Classification & Decision Intelligence |
| Prasannaa DP | Orbital Data Processing, Analytics & Risk Assessment Evaluation |
| Avinash K| Space Debris Research, Documentation, Impact Analysis & Presentation |
---

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**Built for FAR AWAY 2026 — India's Biggest International Hackathon**

*Themes: Space & Aerospace × Agentic & Autonomous Systems*

🛰️ *Protecting satellites. Autonomously.*

</div>
