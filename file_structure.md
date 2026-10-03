# File Structure — GHOST THREAD

## Overview

Intended file and folder layout for GHOST THREAD. Source of truth for where code from `tasks.md` (68 tasks, 10 phases) lives. Goals: clean separation by domain, 1–3 files per task, no clutter, scalable hunter/tool/skill additions without refactors.

Stack: Python 3.11+ FastAPI backend (`backend/`), Vite React frontend (`frontend/`), SQLite WAL+FTS5 local store, file locker, Docker split images. All paths relative to repo root.

## Root Tree

```text
GHOST_THREAD/
├── tasks.md
├── file_structure.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.worker
├── docs/
│   └── WALKTHROUGH.md
├── terraform/
│   └── README.md
├── .github/
│   └── workflows/
│       ├── tests.yml
│       ├── build.yml
│       └── llm-costs.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── health.py
│   │   ├── config.py
│   │   ├── config_schema.py
│   │   ├── models/
│   │   ├── graph/
│   │   ├── store/
│   │   ├── llm/
│   │   ├── prompts/
│   │   ├── validation/
│   │   ├── memory/
│   │   ├── collect/
│   │   ├── retrieval/
│   │   ├── temporal/
│   │   ├── tools/
│   │   ├── skills/
│   │   ├── agents/
│   │   ├── cartographer/
│   │   ├── hunters/
│   │   ├── verify/
│   │   ├── brief/
│   │   ├── sync/
│   │   ├── api/
│   │   ├── obs/
│   │   ├── cost/
│   │   ├── security/
│   │   └── ops/
│   ├── tests/
│   │   ├── mocks/
│   │   └── fixtures/
│   ├── evals/
│   └── scripts/
└── frontend/
    ├── package.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── pages/
        ├── components/
        └── hooks/
```

Gitignored at runtime (never committed): `data/` (SQLite, journals, lockers), `*.db*`, `backend/app/store/*.db`, `/tmp/opencode/` scratch.

## Backend: `backend/app/` by Domain

### Entry + Config (Tasks 1–2)
```text
backend/app/
├── main.py            # FastAPI app factory, router mounting (Task 1)
├── health.py          # GET /health (Task 1)
├── config.py          # Config loader: defaults < JSON < env (Task 2)
└── config_schema.py   # Typed namespaces: llm/retrieval/scraping/gaps/cases/costs (Task 2)
```

### Security + Collection Policy (Tasks 3–4)
```text
backend/app/security/
├── url_guard.py       # is_url_allowed(), punycode/private-IP/block-page checks (Task 3)
└── policy.py          # Case scope policy: allow/deny lists, approved-private overrides (Task 3)
backend/app/collect/
└── profile.py         # InvestigatorProfile base + override_for_case() (Task 4)
```

### Observability + Cost (Tasks 5–6)
```text
backend/app/obs/
├── logging.py         # Console + RESULT level (Task 5)
├── journal.py         # Per-case JSONL event journal, atomic append (Task 5)
└── tracing.py         # observe() decorator, Laminar/OTel or no-op (Task 5)
backend/app/cost/
├── tracker.py         # record_usage(), budgets, per-case/gap/role attribution (Task 6)
└── pricing.py         # Custom pricing table + LiteLLM cache (Task 6)
```

### Models + Graph + Store (Tasks 7–14)
```text
backend/app/models/
├── entities.py        # Entity person|company|event (Task 7)
├── expected.py        # ExpectedItem, ExpectedSchema + jurisdiction variants (Task 7)
├── gaps.py            # Gap 4 types + lifecycle transition() (Task 8)
├── trace.py           # StepRecord + HistoryList queries (Task 10)
└── investigation.py   # Wide InvestigationState + narrow Plan/Draft states (Task 11)
backend/app/graph/
├── schema.py          # KnownEntity, GhostNode, 4 edge types (Task 9)
└── store.py           # GraphStore: upsert/add_edge/competing hypotheses (Task 9)
backend/app/store/
├── session_store.py   # SQLite WAL+FTS5 system of record + outbox hooks (Task 12)
├── migrations.sql     # Tables, FTS triggers, watermark tables (Task 12)
└── locker.py          # Per-thread evidence locker + manifest/snapshot (Task 13)
backend/app/retrieval/
└── vector_index.py    # Derived vector index + hydrate-or-drop (Task 14)
```

### LLM + Prompts + Memory (Tasks 15–18)
```text
backend/app/llm/
├── gateway.py         # BaseChatModel.invoke(), get_llm_by_name(), timeouts (Task 15)
└── providers.py       # OpenAI/Anthropic via LiteLLM + mock provider (Task 15)
backend/app/prompts/
├── family.py          # PromptFamily loader, prefix + override merge (Task 16)
├── base.md            # Shared prefix: citations, absence taxonomy, hypothesis format (Task 16)
├── cartographer.md    # Expected-schema generation (Task 16/34)
├── reconstruction.md  # (Task 16/42)
├── temporal.md        # (Task 16/43)
├── structural.md      # (Task 16/44)
├── comparator.md      # (Task 16/45)
└── counter.md         # (Task 16/46)
backend/app/validation/
├── parser.py          # parse_agent_xml(), closed-taxonomy enforce (Task 17)
├── classifier.py      # idle vs prose diagnostics (Task 17)
└── redaction.py       # PII strip + placeholder substitution (Task 17)
backend/app/memory/
└── manager.py         # 3-slot memory, compaction, loop detector, plan items (Task 18)
```

### Collection Substrate (Tasks 19–26, 61–63)
```text
backend/app/collect/
├── base_retriever.py  # BaseRetriever contract + provenance envelope (Task 19)
├── factory.py         # get_retriever(s)/default (Task 19)
├── providers.py       # Fleet: tavily/exa/brave + wayback/registry/trademark/domain/social (Task 20)
├── quorum.py          # Corroboration quorum checker + providers_consulted log (Task 20)
├── scraper.py         # Dispatcher: static → browser → archival → PDF (Task 21)
├── adapters_registry.py  # Corporate registry normalizer (Task 22)
├── adapters_archive.py   # Social/web archive normalizer (Task 22)
├── adapters_domain.py    # Domain infra normalizer (Task 22)
├── checkpoints.py     # Byte-offset resume cursors (Task 22)
├── documents.py       # Local/remote/blob/leaked loaders + memory/ ingest (Task 32)
├── markdown_extract.py# Fidelity markdown + structural chunking + offsets (Task 32)
├── throttle.py        # Per-source semaphore table + throttle_wait events (Task 25)
├── sandbox.py         # sandboxed_run() for untrusted targets (Task 26)
├── evidence.py        # Screenshots/HAR/video/downloads/PDF chain (Task 61)
├── watchdogs.py       # Base watchdog + politeness/archive-fallback + stubs (Task 62)
├── session.py         # BrowserSession facade (Task 63)
└── target_pool.py     # Tab pool + focus recovery (Task 63)
backend/app/tools/
├── registry.py        # @action decorator, domain-scoped toolset (Task 23)
└── mcp_bridge.py      # Inbound/outbound MCP bridge (Task 23)
backend/app/skills/
├── catalog.py         # Skill registry + version pinning (Task 24)
├── domain_sweep.py    # (Task 24)
├── archive_diff.py    # (Task 24)
├── filing_lapse.py    # (Task 24)
└── peer_baseline.py   # (Task 24)
```

### Retrieval + Temporal Helpers (Tasks 27–32)
```text
backend/app/retrieval/
├── orchestrator.py    # SearchOrchestrator + hint routing (Task 27)
├── strategies.py      # vector|lexical|hybrid|temporal strategies (Task 27)
├── compress.py        # Two-track compression, absence-pinned trim (Task 29)
├── dedup.py           # classify_pair() + IDF veto + alias clusters (Task 30)
└── salience.py        # ACT-R blended_score() (Task 31)
backend/app/temporal/
├── timeline.py        # build_timeline() compact + human renders (Task 28)
└── gap_detect.py      # detect_silences/bursts/deletions + cadence table (Task 28)
```

### Agents + Cartographer (Tasks 33–41)
```text
backend/app/agents/
└── base.py            # Agent run loop: pause/resume/stop/inject, budgets (Task 33)
backend/app/cartographer/
├── schema_gen.py      # generate_expected_schema() + approval event (Task 34)
├── completeness.py    # build_completeness_map() + Gap[] emit (Task 35)
├── router.py          # Embedding + boss-model routing, topology registry (Task 36)
├── dispatch.py        # Director orders + flow-string executor (Task 37)
├── queue.py           # TaskQueue claim/fail/cancel + triage/deep lanes (Task 38)
├── spec.py            # CompletenessSpec validation + to_yaml/from_yaml (Task 39)
├── spawn.py           # AgentRegistry + live rearrange (Task 39)
├── handoff.py         # Connected-entity + trigger-kind (a/b/c) handoffs (Task 40)
└── saturation.py      # evaluate() + forced-closure flags (Task 41)
```

### Hunters (Tasks 42–47)
```text
backend/app/hunters/
├── reconstruction.py  # Wayback/cache/forum ladder + deletion-cluster handoff (Task 42)
├── temporal.py        # Silence windows + correlation (Task 43)
├── structural.py      # Filings/trademark/domain/partnership + shell handoff (Task 44)
├── comparator.py      # Peer cohort + deviation_score (Task 45)
└── counter.py         # Challenger with budget + contradicted_by edges (Task 46)
```

### Verification (Tasks 48–51)
```text
backend/app/verify/
├── judge.py           # judge_absence() upheld|rejected|unresolved (Task 48)
├── deliberation.py    # Debate/council/voting/consistency/ToT (Task 49)
├── resilience.py      # Retry taxonomy + forced-accept dissent (Task 50)
└── hypotheses.py      # HypothesisPair, unresolved preservation (Task 51)
```

### Brief + Sync + API (Tasks 52–60)
```text
backend/app/brief/
├── builder.py         # Saturation-brief assembler + budget fit (Task 52)
├── sections.py        # Header/map/timeline/hypotheses/deviation/footer (Task 52)
├── markdown.py        # TOC + absence index + sorted references (Task 53)
├── curator.py         # Authority/diversity rank + redundancy suppress (Task 54)
├── publisher.py       # Multi-format export, snapshots linked to graph ids (Task 60)
└── visuals.py         # Silence chart, deviation bars, ghost subgraph (Task 60)
backend/app/sync/
├── bus.py             # Typed event bus + size guards (Task 55)
├── graph_sink.py      # Bus → ghost nodes/edges projection (Task 55)
└── pg_ledger.py       # Postgres mirror, generation-key idempotency (Task 55)
backend/app/api/
├── routes.py          # REST v1: cases/gaps/timeline/brief/events/search (Task 57)
├── websocket.py       # WebSocketManager per investigation (Task 56)
├── events.py          # Gap-lifecycle event vocabulary (Task 56)
├── mcp_server.py      # Recall MCP tools + visibility gating (Task 57)
├── auth.py            # Scoped keys, rate limits, metering (Task 57)
└── approvals.py       # Schema + saturation approval gates (Task 58)
backend/app/ops/
├── daemon.py          # PID/version manifests, health, graceful shutdown (Task 64)
└── schedule.py        # Cron re-checks + grid sweeps with jitter (Task 64)
```

## Tests, Evals, Scripts

```text
backend/tests/
├── test_config.py test_url_guard.py test_profile.py test_cost.py
├── test_expected.py test_gaps.py test_graph.py test_trace.py
├── test_store.py test_locker.py test_vector_index.py
├── test_gateway.py test_validation.py test_memory.py
├── test_retrievers.py test_scraper.py test_tools.py test_throttle.py
├── test_hybrid.py test_timeline.py test_documents.py test_dedup.py test_salience.py
├── test_base_agent.py test_schema_gen.py test_completeness.py test_router.py
├── test_queue.py test_spawn.py test_handoff.py test_saturation.py
├── test_reconstruction.py test_temporal.py test_structural.py
├── test_comparator.py test_counter.py test_company_example.py
├── test_judge.py test_deliberation.py test_hypotheses.py
├── test_brief_md.py test_guards.py test_e2e_demo.py
├── mocks/
│   └── providers.py       # Mock search/scrape/LLM/registry, no live keys (Task 66)
└── fixtures/
    └── company_gaps.json  # Company fan-out fixture + README field (Task 47)
backend/evals/
├── faithfulness.py        # Citation/diversity/hallucination (Task 65)
├── absence_metrics.py     # Corroboration/archival/counter coverage (Task 65)
└── run.py                 # Eval runner + perturbation checks (Task 65)
backend/scripts/
└── seed_demo.py           # Mocked end-to-end seed (Task 68)
```

## Frontend: `frontend/src/` (Tasks 59)

```text
frontend/src/
├── main.tsx               # Vite entry (Task 1)
├── App.tsx                # Router: Intake ↔ CaseView (Task 59)
├── pages/
│   ├── Intake.tsx         # Entity form → POST /cases + schema approval (Task 59)
│   └── CaseView.tsx       # Map table + threads + saturation badge + brief (Task 59)
├── components/
│   ├── GapList.tsx        # Gaps: type/status/priority/quorum (Task 59)
│   └── BriefView.tsx      # TOC + absence index + hypotheses + exhibits + costs (Task 59)
└── hooks/
    └── useCaseSocket.ts   # WebSocket subscribe + mirror replay (Tasks 56/59)
```

Rules: plain tables/lists only, no styling polish; all data via REST/MCP recall; no direct DB imports.

## Conventions & Scalability Rules

1. **One domain per folder.** New collectors go in `collect/` (adapter or provider), new reasoning in `retrieval/`/`temporal/`/`verify/`, never in `api/` or `hunters/` directly.
2. **Additive extension, no refactors.** New hunter: add `hunters/<name>.py` + prompt `<name>.md` + capability paragraph in `cartographer/router.py` + tests. New source: add provider in `collect/providers.py` + quorum entry + mock in `tests/mocks/providers.py`. New skill: add `skills/<name>.py` + catalog entry.
3. **Naming.** Files `snake_case.py`, prompts `<role>.md`, tests `test_<module>.py`, fixtures `<scenario>.json`. Ghost edges fixed vocabulary only: `should_exist|confirmed_absent|possibly_deleted|contradicted_by` — never add types without updating `graph/schema.py` + `validation/parser.py` + Coverage Checklist.
4. **Contracts first.** Pydantic models in `models/`/`graph/schema.py` are the only cross-agent interface; agents exchange ids + refs, never raw blobs. Vectors hydrate from store; manifests (not dumps) go to Counter-Narrative.
5. **Provenance mandatory.** Every ghost node/edge needs `gap_id` + `provenance_step_ids`; every brief section links to graph ids; every rejection/cost/trim logged with reason.
6. **Budgets enforced in code.** Cost, throttle, loop, and revision caps live in `cost/`, `collect/throttle.py`, `memory/manager.py`, `verify/` — not in prompts.
7. **Task→file mapping.** Each `tasks.md` task touches ≤3 files listed in its header; if a change needs a 4th file, split the task. Phase order is build order: config → models/graph → LLM/prompts → collection → retrieval → Cartographer → hunters → verification → brief/API/UI → ops/quality.
