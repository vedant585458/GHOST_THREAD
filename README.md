# GHOST THREAD

Agentic OSINT gap-detection system — **absence is the signal**. A Cartographer orchestrator
builds a completeness map for an entity, dispatches ghost-hunter specialists against what
*should* exist but doesn't, and produces a saturation brief with replayable provenance.

> **Status: Task 1 — scaffold only.** Runnable monorepo (FastAPI + Vite React + split Docker
> images). No agent logic, no store, no collection yet. See `file_structure.md` for the full
> 68-task layout and where later code lands.

---

## Layout

```text
GHOST_THREAD/
├── pyproject.toml          # Python >=3.11,<4.0 — serving deps + [worker] / [dev] extras
├── .env.example            # LLM keys, search keys, registry endpoints, case data dirs
├── docker-compose.yml      # api + worker (split images, shared case-data volume)
├── Dockerfile.backend      # serving tier — browser-free, small, stays responsive
├── Dockerfile.worker       # browser tier — Playwright + browsers pinned for determinism
├── backend/
│   ├── app/main.py         # FastAPI app factory + router mounting
│   ├── app/health.py       # GET /health -> {"status":"ok"}
│   └── tests/test_health.py
└── frontend/               # Vite + React + TypeScript analyst console
    ├── package.json        # Node >= 20.19 (also pinned in frontend/.nvmrc)
    └── src/main.tsx, src/App.tsx
```

## Toolchain

| Component | Version | Pinned in |
|---|---|---|
| Python | `>=3.11,<4.0` | `pyproject.toml` (`requires-python`) |
| Node.js | `>=20.19` (npm `>=10`) | `frontend/package.json` (`engines`), `frontend/.nvmrc` |
| Playwright + browsers | `1.47.0` (exact) | `pyproject.toml` `[worker]` extra, `Dockerfile.worker`, `PLAYWRIGHT_VERSION` |

Playwright is pinned **exactly** (library *and* the bundled browser build via the
`mcr.microsoft.com/playwright/python:v1.47.0-jammy` base image) so archival captures —
screenshots, HAR, PDF — are deterministic and defensible as evidence. The worker Dockerfile
fails the build if the installed library drifts from the pinned browser bundle.

---

## Local development

### 1. Configure

```bash
cp .env.example .env   # all placeholders; the scaffold runs with them unset
```

### 2. Backend (FastAPI)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.app.main:app --reload       # http://127.0.0.1:8000
curl -s localhost:8000/health               # {"status":"ok"}
```

Interactive docs at `/docs`. Tests: `pytest -q`. Lint: `ruff check backend`.

### 3. Frontend (Vite + React)

```bash
cd frontend
nvm use          # Node 20.19+
npm install
npm run dev      # http://localhost:5173 — renders the GHOST THREAD heading
```

The browser never calls the API directly: requests go to the relative `/api` prefix and the
Vite dev server proxies them to `VITE_API_TARGET` (default `http://127.0.0.1:8000`), so the
app also works behind containers and remote preview proxies.

### 4. Both services in Docker

```bash
docker compose config        # validate
docker compose up --build    # api on :8000, worker idling on the pinned browser image
```

`api` and `worker` are built from separate Dockerfiles and share the `case-data` volume
(`/data/{cases,journals,captures}` + SQLite). The worker waits for the API healthcheck
(`service_healthy`) and gets `shm_size: 1gb` so Chromium can screenshot large archival pages.
Split-image rationale: analyst-facing serving must stay responsive during long browser-heavy
crawls (see `gpt-researcher.md`, Category 9 / Finding 9.1).

---

## Conventions

- **Contracts first.** Pydantic models under `backend/app/models/` (Task 7+) are the only
  cross-agent interface; agents exchange ids and refs, never raw blobs.
- **One domain per folder**, additive extension, no refactors — see `file_structure.md`.
- **Never commit** `.env` or `data/` (evidence lockers, journals, SQLite); both are gitignored.
- **UI stays plain** — tables and lists, no styling polish; all data via REST/MCP.

## Reference analyses

`browser-use.md`, `gpt-researcher.md`, `swarms.md`, `claude_mem.md` — upstream repository
analyses that inform the architecture. `file_structure.md` is the source of truth for layout.
