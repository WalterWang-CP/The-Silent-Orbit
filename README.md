# The Silent Orbit — Stateful AI Simulation Engine (Gemini + MongoDB)

**The Silent Orbit** is a stateful AI simulation engine where a language model (Gemini) generates narrative and proposes state changes, while the system persists the canonical state in **MongoDB**.

The key design goal is to treat the AI model as an **untrusted component**:
- The model can narrate and propose updates.
- The system validates and applies allowed updates to the database.
- Game/simulation state remains consistent across sessions.

> Current implementation uses an update protocol embedded in text:
> `UPDATE_START { ... } UPDATE_END`

---

## Architecture

**Core Ideas**
- **Persistence-first**: Character/world state lives in MongoDB (`players`, `world_lore`, `game_logs`).
- **Guardrails**: AI output is parsed and filtered before mutating state.
- **Two interfaces**:
  - CLI loop (fast development)
  - Web UI (later polish)

**Main Components**
- `core/database.py` — MongoDB connection + collections
- `core/main.py` — CLI runtime, Gemini orchestration, update parsing
- `scripts/init_character.py` — inserts canonical character schema
- `scripts/init_world.py` — seeds world lore data
- `web/app.py` — Flask API wrapper around the engine
- `web/templates/index.html` — browser UI

---

## Current Features

- Gemini-powered narrative loop (CLI + Web)
- Persistent character stats and status in MongoDB
- World lore lookup by character location
- Update protocol: model proposes database updates via `UPDATE_START ... UPDATE_END`
- Update application supports `$inc` (numbers) and `$set` (strings/objects)

---

## Roadmap (in progress)

### Validator (core priority)
A dedicated validator module will:
- validate update **format** (JSON parse + required structure)
- validate update **permissions** (allowed fields only)
- validate update **ranges** (max delta, clamping rules)
- enforce **invariants** (e.g., integrity never < 0, derived states)

### Structured Output (future improvement)
Move from regex parsing to **structured JSON output**:
- model returns `{ narrative: "...", updates: {...} }`
- validator consumes `updates` directly

### Memory / Logs
- store turn logs into `game_logs`
- allow retrieval-based memory for long-term consistency

---

## Requirements

- Python 3.11+ recommended
- MongoDB (local or Atlas)
- Gemini API key

Python packages (typical):
- `pymongo`
- `python-dotenv`
- `flask`
- `google-generativeai` (current; migration planned)

> Note: `google.generativeai` currently shows a deprecation warning in newer environments. A migration to the newer Google GenAI SDK is planned.

---

## Setup

### 1) Create `.env` in project root
Create a file named `.env` at the project root:

```env
MONGO_URI=mongodb://localhost:27017
GEMINI_API_KEY=YOUR_KEY_HERE
