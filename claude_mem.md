# Repository Analysis Report
## Reusable Components & Architectural References for GHOST THREAD — Agentic OSINT Gap-Detection System

**Analyzed Repository:** https://github.com/thedotmack/claude-mem
**Analysis Date:** 2026-10-02
**Repository Primary Language(s):** TypeScript (Node.js / Bun), Python (Chroma sidecar, cost-report skill), SQL (SQLite FTS5 / Postgres), Shell (installers/hooks)
**Repository Framework(s):** Express, BullMQ + Redis, Model Context Protocol SDK, Claude Agent SDK, SQLite (bun:sqlite, WAL), ChromaDB, Postgres, Cloudflare Durable Objects
**Repository Architecture Style:** Local-first daemon + optional hosted server; plugin/hook-driven event pipeline with worker-queue orchestration and MCP tool exposure (monolith with pluggable provider/mode lanes)

---

## Executive Summary

Claude-mem is a persistent memory compression system for coding agents. It captures tool-use observations via host hooks and transcript watchers, generates structured summaries with LLMs (Claude / Gemini / OpenRouter / Codex providers), stores them in SQLite FTS5 + Chroma vector + Postgres server layers, and re-injects ranked context at session start or via MCP search tools. Maturity is high: version 13.28.0, extensive test suites, Docker/E2E harnesses, multi-IDE adapters, and a server-beta with team multi-tenancy.

For GHOST THREAD — whose core is subtractive reasoning about absence (completeness maps, ghost nodes, temporal/structural gaps, counter-narratives, saturation briefs) — this repository does not implement OSINT gap detection, but it implements almost every supporting primitive: orchestrator-to-specialist dispatch, lossless event ingestion, hybrid retrieval, timeline reconstruction, salience ranking beyond recency, deduplication/conflict surfacing, structured-evidence validation, budgeted briefing, multi-tenant hardened APIs, and exactly-once evidence replication. A total of 19 relevant components were identified, richest in orchestration/worker dispatch, retrieval/timeline reasoning, and evidence storage.

The closest analogues to adapt are the Cartographer-to-hunter dispatch (SessionManager / BullMQ lanes / ModeManager), the Temporal Gap foundation (ObservationCompiler + TimelineService), the Counter-Narrative foundation (dedup + output classifier + structured prompt builder), and the ghost-node-capable evidence ledger (SessionStore + ChromaSync + Postgres with idempotency keys).

---

## Table of Contents

- [Repository Structure Overview](#repository-structure-overview)
- [Findings by Category](#findings-by-category)
  - [Category 1: Agentic Orchestration & Dynamic Dispatch](#category-1-agentic-orchestration--dynamic-dispatch)
  - [Category 2: Evidence Capture & Ingestion](#category-2-evidence-capture--ingestion)
  - [Category 3: Retrieval, Timeline & Comparative Reasoning](#category-3-retrieval-timeline--comparative-reasoning)
  - [Category 4: Verification, Deduplication & Completion](#category-4-verification-deduplication--completion)
  - [Category 5: Evidence Storage & Replication (Knowledge-Graph Substrate)](#category-5-evidence-storage--replication-knowledge-graph-substrate)
  - [Category 6: API Exposure, Resilience & Security](#category-6-api-exposure-resilience--security)
- [Cross-Cutting Observations](#cross-cutting-observations)
- [Recommended Exploration Priority](#recommended-exploration-priority)
- [Potential Gaps & Caveats](#potential-gaps--caveats)
- [Licensing & Attribution Notice](#licensing--attribution-notice)

---

## Repository Structure Overview

```text
claude-mem/
  src/
    cli/               # Hook entry: stdin -> adapter.normalize -> handler.execute -> emit
      adapters/        # claude-code, codex, cursor, windsurf, kimi, antigravity, raw
      handlers/        # context, session-init, observation, summarize, session-end, file-*
    sdk/               # prompts.ts, parser.ts, output-classifier.ts, hardened-options.ts
    services/
      transcripts/     # watcher.ts, processor.ts — JSONL/zstd tail + checkpointing
      worker/          # SessionManager, providers, SearchManager, agents/, search/, knowledge/
      memory/          # ingest.ts — markdown memory auto-ingest
      context/         # ContextBuilder, ObservationCompiler, Budget, sections/, formatters/
      dedup/           # normalize, tfidfCosine, idf, idfVeto, nearDuplicate
      reinforcement/   # strength.ts, rank.ts, persist.ts (ACT-R)
      sqlite/          # SessionStore (~4426 lines), SessionSearch (~847 lines), connection
      sync/            # ChromaSync, CloudSync, SyncClient, SyncApply, CanonicalContent
      domain/          # ModeManager — swappable observer personas
      infrastructure/  # ProcessManager, HealthMonitor, GracefulShutdown, ProjectMerge
      hooks/           # runtime-selector, server-client, server-bootstrap
      smart-file-read/ # tree-sitter-backed file parsing/search
    server/            # Server-beta: runtime/, jobs/, queue/, routes/v1/, generation/, mcp/, auth/
    servers/           # mcp-server.ts (stdio), recall-mcp-server, visibility, checkout-scope
    storage/
      sqlite/          # memory-items, server-sessions, projects
      postgres/        # observations, agent-events, generation-jobs, server-sessions
    npx-cli/           # installer, doctor, server-jobs, telemetry
  plugin/
    hooks/hooks.json   # Setup/SessionStart/UserPromptSubmit/PostToolUse/Stop/SessionEnd
    modes/             # code--*.json observer mode configs
    scripts/           # bun-runner, worker-service.cjs, mcp-server.cjs
  workers/sync-hub/    # Cloudflare Durable Object per-user op log
  services/sync-api/   # Self-hostable Bun+Postgres hub
  tests/               # context, dedup, hooks, infra, server, sqlite, worker/agents|search
  docs/                # architecture-overview, server-*, security, api, adapters
  docker-compose*.yml, Dockerfile.test-installer, scripts/
```

Key annotations: `src/cli` is the non-blocking ingestion edge; `src/services/worker` is the orchestrator + provider pool; `src/services/context` is the briefing renderer; `src/services/sqlite` + `src/storage` are the evidence ledger; `src/server` is the hosted multi-tenant counterpart.

---

## Findings by Category

### Category 1: Agentic Orchestration & Dynamic Dispatch

#### Finding 1.1: Session-Scoped Observer Lifecycle Manager

| Attribute | Detail |
|---|---|
| **Location** | `src/services/worker/SessionManager.ts` |
| **Scope** | Class `SessionManager`, Class `SessionMessageBuffer` in `src/services/worker/SessionMessageBuffer.ts` |
| **Line Range** | Lines 1–787 approx. (SessionManager); Lines 1–100 approx. (Buffer) |
| **Dependencies** | Internal: provider-dispatch, DatabaseManager, SessionCompletionHandler, GeneratorRunner; External: Claude Agent SDK |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Maintains a map of live investigation sessions, buffers inbound messages per session, supervises underlying model processes, and coordinates wrap-up, retry, and resume. Acts as the central orchestrator that owns session lifetime from start through completion.

**How It Works (Conceptual):**
Follows a supervisor pattern with per-session state isolation. Inbound events are buffered rather than processed inline, allowing the orchestrator to sequence generation, handle stalls, and recycle conversations on overflow without losing session affinity.

**Relevance to Your Project:**
Direct template for the Cartographer Agent. Replace code-observation sessions with entity investigations, and the per-session buffer becomes the per-entity completeness-map workspace where gap-specific hunter threads are tracked.

**Suggested Adaptation Strategy:**
Study how session identity, buffering, and wrap-up are separated into distinct collaborators. Adapt the separation so the Cartographer owns routing and saturation bookkeeping while hunter agents own domain evidence collection. Preserve the resume/retry discipline for long-running OSINT hunts that hit provider rate limits.

#### Finding 1.2: Queued Specialist Dispatch with Dual Lanes

| Attribute | Detail |
|---|---|
| **Location** | `src/server/runtime/ActiveServerQueueManager.ts`, `src/server/jobs/ServerJobQueue.ts`, `src/server/generation/ProviderObservationGenerator.ts` |
| **Scope** | Class `ActiveServerQueueManager`, Class `ServerJobQueue`, Class `ProviderObservationGenerator` |
| **Line Range** | Lines 1–120 approx. each for managers; Lines 1–400 approx. for generator |
| **Dependencies** | Internal: Redis config, Postgres repositories; External: BullMQ, Redis |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Separates fast event ingestion from slower summarization work into distinct queue lanes, with a generic queue wrapper that supports stalled-job observation, concurrency control, and pluggable processors that load raw events and invoke an LLM provider.

**How It Works (Conceptual):**
Uses a producer/consumer work-queue pattern with lane isolation. Ingest writes durably first; background workers claim jobs idempotently. The generator builds a provider-specific prompt from stored events and routes the response through a transactional result handler.

**Relevance to Your Project:**
Models dynamic hunter-agent spawning. Each gap type (temporal, structural, relational, digital) can be a queue lane or job kind. Partial evidence that suggests deeper investigation maps to enqueuing a follow-up job with lineage to the parent gap.

**Suggested Adaptation Strategy:**
Replicate the two-lane split as fast gap-triage versus deep-dive investigation lanes. Study the stall-handling and retry semantics for hunts that depend on flaky external sources (Wayback, registries). Combine with Finding 1.4 for provider-agnostic hunter execution.

#### Finding 1.3: Swappable Specialist Personas via Mode Inheritance

| Attribute | Detail |
|---|---|
| **Location** | `src/services/domain/ModeManager.ts`, `plugin/modes/code--*.json`, `src/core/schemas/` |
| **Scope** | Class `ModeManager`, Config `ModeConfig`, observation-type schemas |
| **Line Range** | Lines 1–200 approx. for manager; JSON mode files 50–150 lines each |
| **Dependencies** | Internal: file-system mode dirs, Zod-style schemas; External: none |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Loads observer behavior definitions from layered directories with single-level inheritance, allowing a base mode to be specialized by an override without duplication. Observation types, prompts, and formatting guidance travel with the mode.

**How It Works (Conceptual):**
Implements Strategy plus Template Method via configuration: the orchestrator selects a mode identifier at runtime, merges base and override definitions, and injects the resulting prompt scaffold into generation. Validation constrains mode identifiers to a safe pattern.

**Relevance to Your Project:**
Direct mechanism for Profile Reconstruction vs. Temporal Gap vs. Structural Absence vs. Counter-Narrative vs. Context Comparator specialists. Each hunter shares a common evidence schema but differs in type guidance and sourcing strategy.

**Suggested Adaptation Strategy:**
Define a base OSINT-hunter mode (evidence schema, citation rules, absence-classification taxonomy) and per-specialist overrides. Study the durable user-modes directory versus shipped modes to allow analysts to add custom hunters without forking core.

#### Finding 1.4: On-Demand Deep-Dive Agent Over Rendered Corpus

| Attribute | Detail |
|---|---|
| **Location** | `src/services/worker/knowledge/KnowledgeAgent.ts`, `CorpusBuilder.ts`, `CorpusRenderer.ts`, `CorpusStore.ts` |
| **Scope** | Class `KnowledgeAgent`, Class `CorpusBuilder`, Class `CorpusRenderer` |
| **Line Range** | Lines 1–250 approx. (Agent); Lines 1–180 approx. each for store/builder |
| **Dependencies** | Internal: SessionStore, SearchManager; External: Claude Agent SDK |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Builds a file-system corpus from stored observations, renders it into a queryable form, and primes a dedicated agent instance to answer focused questions against that corpus on demand.

**How It Works (Conceptual):**
Applies a materialized-view pattern for agents: instead of re-searching from scratch per question, it compiles a task-specific snapshot and spawns an ephemeral agent scoped to that snapshot, preserving lineage to source observations.

**Relevance to Your Project:**
Models how a hunter thread should operate once spawned: compile the entity's known footprint plus expected-schema deltas into a scoped corpus, then investigate only within that scope. Prevents cross-entity leakage and bounds token cost.

**Suggested Adaptation Strategy:**
Adapt corpus compilation to include both present evidence and ghost-node placeholders (expected-but-absent). Study priming and query separation to let the Cartographer spawn a hunter with a narrow brief and later merge its evidence chain back into the global graph.

---

### Category 2: Evidence Capture & Ingestion

#### Finding 2.1: Lossless Transcript Tailing with Checkpoints

| Attribute | Detail |
|---|---|
| **Location** | `src/services/transcripts/watcher.ts`, `processor.ts`, `zstd-frames.ts`, `state.ts` |
| **Scope** | Class `TranscriptWatcher`, Class `TranscriptEventProcessor` |
| **Line Range** | Lines 1–742 approx. (watcher); Lines 1–450 approx. (processor) |
| **Dependencies** | Internal: worker HTTP ingest, field-utils matchers; External: file-system, zstd |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Tails append-only JSONL (including compressed frames) with byte-offset checkpoints and backfill, converting raw tool/prompt events into normalized observations via a worker endpoint without blocking the primary session.

**How It Works (Conceptual):**
Implements change-data-capture over local logs: incremental scans bounded by byte budgets, durable offsets, decompression of framed payloads, and rule-based field extraction before ingest. Failures degrade to no-ops rather than breaking the host.

**Relevance to Your Project:**
Template for OSINT source taps (registry polls, social archives, news feeds). GHOST THREAD needs the same lossless, resumable ingestion for public-record streams where deletions and lapsed records are themselves signals.

**Suggested Adaptation Strategy:**
Replace transcript paths with OSINT collectors that emit the same normalized observation envelope. Retain checkpointing and byte-budgeting to handle large dumps (filings, forum archives). Preserve the never-block-the-analyst discipline for background hunts.

#### Finding 2.2: Non-Blocking Multi-Host Hook Pipeline

| Attribute | Detail |
|---|---|
| **Location** | `src/cli/hook-command.ts`, `src/cli/adapters/`, `src/cli/handlers/`, `plugin/hooks/hooks.json` |
| **Scope** | Function `hookCommand`, Adapter `getPlatformAdapter`, Handler `getEventHandler` |
| **Line Range** | Lines 1–150 approx. (hook-command); Adapters 80–200 lines each; Handlers 50–150 lines each |
| **Dependencies** | Internal: runtime-selector, ServerClient; External: host CLI event JSON on stdin |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Normalizes heterogeneous host events (SessionStart, PostToolUse, Stop, SessionEnd, etc.) through per-platform adapters into a common handler interface that emits model context or triggers background work, always exiting successfully.

**How It Works (Conceptual):**
Uses Adapter plus Pipeline patterns: stdin JSON is normalized per host, dispatched by event type, executed by a focused handler, and rendered back in host-specific shape. Errors collapse to a no-op envelope to preserve host liveness.

**Relevance to Your Project:**
Shows how to normalize heterogeneous OSINT source payloads (APIs, scrapes, archive formats) into a single gap-reasoning pipeline. The fail-open philosophy is critical when a single source outage must not abort an entire investigation.

**Suggested Adaptation Strategy:**
Mirror the adapter/handler split: one adapter per source family (corporate registries, social archives, domain infra) feeding common gap-detection handlers. Study timeout and async flags in `hooks.json` to keep interactive briefs responsive while hunts continue in background.

#### Finding 2.3: Markdown Memory Auto-Ingest

| Attribute | Detail |
|---|---|
| **Location** | `src/services/memory/ingest.ts` |
| **Scope** | Function `ingestMemorySource`, Function `buildMemoryObservation`, Function `scanMemorySource` |
| **Line Range** | Lines 1–700 approx. |
| **Dependencies** | Internal: SessionStore, ChromaSync; External: file-system |
| **Relevance Rating** | ★★★☆☆ |

**What It Does:**
Scans a conventional memory directory for analyst-authored notes, derives titles, parses frontmatter, enforces size caps, and stores them as first-class observations with vector sync, without invoking an LLM.

**How It Works (Conceptual):**
Treats the file system as an outbox: enumeration with allow/deny rules, deterministic title derivation, and direct persistence. Provides a cheap path for human knowledge to enter the same retrieval substrate as machine observations.

**Relevance to Your Project:**
Allows analysts to inject prior knowledge, hypotheses, or known-absence assertions (e.g., claimed non-existence) as evidence that hunters and the Counter-Narrative Agent must reconcile, without LLM paraphrase loss.

**Suggested Adaptation Strategy:**
Adopt the same DB-free ingest path for analyst briefs and watchlists. Enforce caps and frontmatter conventions so ghost-node assertions remain queryable alongside scraped evidence.

---

### Category 3: Retrieval, Timeline & Comparative Reasoning

#### Finding 3.1: Hybrid Retrieval Orchestrator (Vector + Lexical + Merged)

| Attribute | Detail |
|---|---|
| **Location** | `src/services/worker/search/SearchOrchestrator.ts`, `strategies/ChromaSearchStrategy.ts`, `strategies/SQLiteSearchStrategy.ts`, `strategies/HybridSearchStrategy.ts`, `src/services/worker/SearchManager.ts` |
| **Scope** | Class `SearchOrchestrator`, Class `ChromaSearchStrategy`, Class `SQLiteSearchStrategy`, Class `HybridSearchStrategy` |
| **Line Range** | Lines 1–245 approx. (orchestrator); Strategies 150–250 lines each; Manager Lines 1–1259 approx. |
| **Dependencies** | Internal: SessionStore, ChromaSync, TimelineService, FormattingService; External: ChromaDB, SQLite FTS5 |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Fans out a single search request to vector, full-text, or merged strategies based on an explicit hint or automatic selection, hydrates vector hits from the authoritative store, and wraps results with telemetry and pagination.

**How It Works (Conceptual):**
Implements Strategy plus Facade: the orchestrator validates that a query or filter is present, delegates to swappable strategies that share a common result shape, and the manager adds formatting, timeline slicing, and usage accounting. Project scoping filters are pushed into both backends.

**Relevance to Your Project:**
Core for Profile Reconstruction (cached/deleted profile discovery via fuzzy vector match) and Counter-Narrative search (finding contradicting invoices, mirrors, or name variants that lexical search alone would miss). Hybrid ranking is essential for noisy OSINT text with aliases and transliterations.

**Suggested Adaptation Strategy:**
Replicate the strategy-hint interface so each hunter declares its preferred recall mode (e.g., reconstruction prefers hybrid, structural checks prefer lexical for registry IDs). Study hydration discipline: vectors propose, authoritative store disposes, preventing hallucinated evidence from entering chains.

#### Finding 3.2: Timeline Reconstruction for Silence and Burst Detection

| Attribute | Detail |
|---|---|
| **Location** | `src/services/context/ObservationCompiler.ts`, `src/services/worker/TimelineService.ts`, `src/services/context/sections/TimelineRenderer.ts` |
| **Scope** | Function `buildTimeline`, Class `TimelineService`, Function `renderAgentTimeline` |
| **Line Range** | Lines 1–311 approx. (compiler); Lines 1–40 approx. (service); Renderer Lines 30–160 approx. |
| **Dependencies** | Internal: SessionStore queries, reinforcement rank; External: none |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Queries observations and summaries across sessions, merges them into a chronological timeline with prior-message extraction, slices by depth/anchor, and renders agent-compact versus human-readable variants.

**How It Works (Conceptual):**
Treats stored observations as an event log and builds a temporal projection on demand. Depth-limited slicing keeps recent anchors stable while older history is summarized, supporting both machine reasoning and analyst review from the same rows.

**Relevance to Your Project:**
Foundation for the Temporal Gap Agent. Unexplained silences, simultaneous deletions, and behavior-change points are computed over exactly this kind of merged timeline. Anchor slicing maps to focusing on deletion windows and correlating them with external events.

**Suggested Adaptation Strategy:**
Extend the timeline builder with explicit gap markers (expected cadence vs. observed silence) and burst markers. Study how prior-session lookup walks newest rows so gap annotations do not displace recency-critical anchors. Add jurisdiction/entity-type expected-cadence tables alongside.

#### Finding 3.3: Budgeted Briefing Under Token Limits

| Attribute | Detail |
|---|---|
| **Location** | `src/services/context/ContextBuilder.ts`, `ContextBudget.ts`, `TokenCalculator.ts`, `ContextConfigLoader.ts` |
| **Scope** | Function `generateContext`, Function `fitContextToBudget`, Function `calculateObservationTokens` |
| **Line Range** | Lines 1–584 approx. (builder); Budget Lines 1–90 approx.; Calculator Lines 1–70 approx. |
| **Dependencies** | Internal: ObservationCompiler, ServerContextRows, section renderers; External: none |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Assembles header, timeline, summary, and footer sections from multi-source rows, trims to a configured output limit, and supports both local and server-backed row shapes with health warnings.

**How It Works (Conceptual):**
Applies a budget pattern: fetch generously, render structurally, then fit to delivery constraints while preserving section integrity. Configuration is layered from environment through settings files to defaults.

**Relevance to Your Project:**
Direct model for the saturation brief: explainable vs. anomalous absences, competing hypotheses, and evidence chains must fit an analyst-readable budget without dropping ghost-node distinctions.

**Suggested Adaptation Strategy:**
Reuse the section-renderer split (header/completeness map, timeline/gaps, summaries/hypotheses, footer/unknowns). Study server-versus-local row normalization to let briefs merge field-collected and centrally-stored evidence uniformly.

#### Finding 3.4: ACT-R Salience Ranking Beyond Recency

| Attribute | Detail |
|---|---|
| **Location** | `src/services/reinforcement/strength.ts`, `rank.ts`, `persist.ts` |
| **Scope** | Function `blendedScore`, Function `rankByStrength`, Function `appendReinforcement` |
| **Line Range** | Lines 1–72 approx. (strength); Lines 1–105 approx. (rank); Lines 1–42 approx. (persist) |
| **Dependencies** | Internal: SessionStore reinforcement_dates column; External: none |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Maintains per-observation reinforcement dates and scores candidates with a power-law decay that rewards repeated re-confirmation, preserving a recency head while re-ranking older history by durable importance without vectors.

**How It Works (Conceptual):**
Adapts cognitive-science base-level activation: creation is the first presentation, each re-confirmation day adds a decayed term. Ranking is opt-in via a weight parameter; when disabled the system reverts to pure recency, preserving backward compatibility.

**Relevance to Your Project:**
Lets persistent absences (e.g., a filing missing across multiple checks) outrank transient noise, and lets repeatedly contradicted absences decay appropriately. Embedding-free scoring keeps comparator logic cheap across many entities.

**Suggested Adaptation Strategy:**
Treat each corroborating sighting of an absence as a reinforcement event. Study the recency-head guarantee so the newest counter-evidence is never buried by older reinforced claims. Tune the decay exponent and pool multiplier for OSINT cadences (days to years, not minutes).

---

### Category 4: Verification, Deduplication & Completion

#### Finding 4.1: Near-Duplicate Guard with Rare-Token Veto

| Attribute | Detail |
|---|---|
| **Location** | `src/services/dedup/nearDuplicate.ts`, `tfidfCosine.ts`, `idf.ts`, `idfVeto.ts`, `normalize.ts`, `src/services/sqlite/dedup-store.ts` |
| **Scope** | Function `classifyPair`, Function `tfidfCosine`, Function `vetoFires` |
| **Line Range** | Lines 1–76 approx. (nearDuplicate); Supporting files 24–50 lines each; Store Lines 1–272 approx. |
| **Dependencies** | Internal: SessionStore content_hash; External: none |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Classifies observation pairs as exact, candidate, or non-duplicates using normalized titles and TF-IDF cosine with an inverse-document-frequency veto that prevents common-term collisions from suppressing genuinely distinct evidence.

**How It Works (Conceptual):**
Combines hashing for exact matches with sparse lexical similarity for fuzzy matches, gated by a rare-token requirement. The veto ensures that shared boilerplate (e.g., registry disclaimers) cannot merge distinct filings.

**Relevance to Your Project:**
Prevents the Context Comparator from conflating distinct shell entities with similar names and stops the Counter-Narrative Agent from dismissing real contradictions as duplicates. Also the base for alias/name-variant clustering.

**Suggested Adaptation Strategy:**
Retain the veto concept but retrain IDF over OSINT corpora (company suffixes, transliterated person names). Study content-hash plus fuzzy two-stage ordering to keep ingest cheap at scale.

#### Finding 4.2: Structured-Evidence Validation and Schema-Drift Detection

| Attribute | Detail |
|---|---|
| **Location** | `src/sdk/parser.ts`, `output-classifier.ts`, `src/server/generation/providers/shared/prompt-builder.ts`, `processGeneratedResponse.ts` |
| **Scope** | Function `parseAgentXml`, Function `previewOutput`, Function `buildServerGenerationPrompt` |
| **Line Range** | Lines 1–329 approx. (parser); Lines 1–451 approx. (classifier); Builder Lines 1–228 approx. |
| **Dependencies** | Internal: ModeManager schemas; External: LLM providers |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Enforces a strict observation/summary XML schema from free-form model output, classifies non-conforming outputs into idle versus prose for visible diagnostics, and strips private content before persistence, all within idempotent transactions.

**How It Works (Conceptual):**
Treats the model as untrusted: prompts declare the schema, the parser validates and salvages drifted tags, the classifier makes silent drops observable, and the response processor guarantees exactly-once storage via generation keys.

**Relevance to Your Project:**
Blueprint for evidence-chain integrity. Hunter findings (confirmed absent vs. possibly deleted vs. contradicted) must validate against a ghost-node taxonomy; drift (e.g., inventing new absence types) should be flagged, not silently stored. The idle/prose split maps to distinguishing investigated-and-truly-absent from failed-to-investigate.

**Suggested Adaptation Strategy:**
Define GHOST THREAD absence states as a closed taxonomy in the prompt builder and enforce it in the parser. Reuse the preview-logging idea so analysts can audit why a hunt produced no evidence. Carry over private-content stripping for PII in OSINT briefs.

#### Finding 4.3: Saturation and Overflow-Resilient Completion

| Attribute | Detail |
|---|---|
| **Location** | `src/services/worker/session/SessionCompletionHandler.ts`, `src/server/services/EndSessionService.ts`, `src/services/worker/session/recycle-conversation.ts`, `src/cli/handlers/summarize.ts` |
| **Scope** | Class `SessionCompletionHandler`, Service `EndSessionService`, Function `recycleObserverConversation` |
| **Line Range** | Lines 1–120 approx. (handler); Recycle Lines 1–180 approx.; EndSession 80–150 lines approx. |
| **Dependencies** | Internal: SessionStore summaries, provider dispatch; External: LLM providers |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Finalizes turns and sessions, persists summaries, handles context-overflow by reloading start context and recycling the observer conversation, and exposes explicit end-session semantics for both worker and server runtimes.

**How It Works (Conceptual):**
Models completion as a first-class transition, not merely connection close: finalize, summarize, persist, and release. Overflow is treated as a recoverable state via context reload rather than data loss.

**Relevance to Your Project:**
Maps to saturation-point logic: all gaps investigated, counter-narratives explored, remaining unknowns classified. Overflow recycling is a pattern for hunts whose evidence exceeds model windows — checkpoint, summarize, and continue with preserved ghost-node state.

**Suggested Adaptation Strategy:**
Implement explicit investigation states (open, counter-narrative pending, explainable absence, anomalous absence) and gate saturation on them as this codebase gates session end on summary persistence. Study compat adapters to keep completion semantics uniform across local and hosted deployments.

---

### Category 5: Evidence Storage & Replication (Knowledge-Graph Substrate)

#### Finding 5.1: Local-First Authoritative Store with FTS

| Attribute | Detail |
|---|---|
| **Location** | `src/services/sqlite/SessionStore.ts`, `SessionSearch.ts`, `connection.ts` |
| **Scope** | Class `SessionStore`, Class `SessionSearch` |
| **Line Range** | Lines 1–4426 approx. (store); Lines 1–847 approx. (search); Connection Lines 1–66 approx. |
| **Dependencies** | Internal: dedup-store, ChromaSync, CloudSync; External: bun:sqlite (WAL, FTS5) |
| **Relevance Rating** | ★★★★★ |

**What It Does:**
Owns sessions, prompts, observations, summaries, tool uses, and sync outbox tables with content-hash deduplication, FTS5 external-content indexes with triggers, Unicode-aware tokenization, and pragmatic connection tuning for concurrent daemon access.

**How It Works (Conceptual):**
Establishes SQLite as the system of record: writes are transactional and hashed for idempotency, reads are served via parameterized FTS queries with project/platform/date filters, and side effects (vector sync, cloud outbox) are derived from the committed row, never the reverse.

**Relevance to Your Project:**
Direct substrate for the knowledge graph including ghost nodes. Expected-but-absent entities can be rows with absence-state edges (should-exist, confirmed-absent, possibly-deleted, contradicted-by) benefiting from the same FTS, filter, and outbox machinery as present entities.

**Suggested Adaptation Strategy:**
Extend the schema with ghost-node tables or typed edges rather than forking a graph DB prematurely; retain FTS for registry-ID and alias search. Study trigger-maintained FTS and WAL/busy-timeout pragmatics for analyst-concurrent hunts.

#### Finding 5.2: Vector Layer as Derived Index (Not Source of Truth)

| Attribute | Detail |
|---|---|
| **Location** | `src/services/sync/ChromaSync.ts`, `ChromaMcpManager.ts`, `src/services/worker/knowledge/CorpusStore.ts` |
| **Scope** | Class `ChromaSync`, Class `ChromaMcpManager` |
| **Line Range** | Lines 1–800 approx. (sync); Manager Lines 1–400 approx. |
| **Dependencies** | Internal: SessionStore; External: ChromaDB via managed MCP/uvx lifecycle |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Mirrors authoritative rows into a managed Chroma collection with watermarks, health checks, and wipe/rebuild paths, handling lifecycle of the vector process and reconciling upserts and deletes.

**How It Works (Conceptual):**
Treats vectors as a recall accelerator: the relational store proposes truth, the vector index proposes candidates, and hydration revalidates against truth. Watermarks bound re-sync work after restarts.

**Relevance to Your Project:**
Enables the Context Comparator (what normal looks like) via similarity over entity footprints without risking vector hallucinations entering evidence chains. Deletion handling here informs how to represent removed profiles (tombstones vs. hard deletes).

**Suggested Adaptation Strategy:**
Keep ghost nodes out of the vector index or tag them distinctly so similarity compares present footprints only, while absence patterns are reasoned relationally. Reuse watermark and corrupt-collection recovery for large OSINT re-indexes.

#### Finding 5.3: Server Ledger with Idempotency and Team Scoping

| Attribute | Detail |
|---|---|
| **Location** | `src/storage/postgres/observations.ts`, `agent-events.ts`, `generation-jobs.ts`, `src/storage/sqlite/memory-items.ts` |
| **Scope** | Class `PostgresObservationRepository`, Class `PostgresObservationGenerationJobRepository` |
| **Line Range** | Lines 1–380 approx. each |
| **Dependencies** | Internal: ServerService graph; External: Postgres, BullMQ |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Persists observations, raw agent events, and generation outbox jobs in Postgres with unique generation keys, team/project scoping, and transactional result handling that separates event history from derived observations.

**How It Works (Conceptual):**
Separates immutable history (agent events) from interpreted results (observations) with an explicit job outbox bridging them. Idempotency keys make retries safe; scoping predicates enforce multi-tenant isolation at query time.

**Relevance to Your Project:**
Needed when GHOST THREAD moves from single-analyst to team investigations with shared ghost graphs. The event-versus-observation split maps to raw source captures versus hunter interpretations, preserving audit trails for competing hypotheses.

**Suggested Adaptation Strategy:**
Adopt the generation-key discipline for hunter jobs so re-running a hunt over the same source snapshot does not duplicate ghost nodes. Study scoped-project filters as the model for case-level access control.

#### Finding 5.4: Exactly-Once Multi-Device Evidence Replication

| Attribute | Detail |
|---|---|
| **Location** | `workers/sync-hub/src/do/SyncHub.ts`, `services/sync-api/src/store.ts`, `src/services/sync/SyncApply.ts`, `CanonicalContent.ts` |
| **Scope** | Class `SyncHub`, Class `HubStore`, Class `SyncApply` |
| **Line Range** | Lines 1–300 approx. each; CanonicalContent 100–200 lines approx. |
| **Dependencies** | Internal: SQLite outbox, cursor-in-transaction; External: Cloudflare Durable Objects or Postgres hub, WebSocket advisory layer |
| **Relevance Rating** | ★★★☆☆ |

**What It Does:**
Replicates canonical operations across devices via a hub log with sequence numbers, cursors advanced in the same transaction as applied rows, echo guards, and an advisory WebSocket speed layer with poll fallback.

**How It Works (Conceptual):**
Implements a durable op log with at-least-once transport and exactly-once apply: cursors and mutations commit atomically, origins are skipped on echo, and epochs handle resets. Content operations use stable document identifiers and canonical JSON.

**Relevance to Your Project:**
Supports distributed hunts (field collectors plus central reasoner) and analyst handoff without forking ghost graphs. The echo-guard and epoch concepts map to merging overlapping investigations of the same entity.

**Suggested Adaptation Strategy:**
Defer full replication until multi-collector operation is needed, but design ghost-node identifiers as stable from the start so later sync does not require remapping. Study cursor-in-transaction as the correctness anchor if you build your own hub.

---

### Category 6: API Exposure, Resilience & Security

#### Finding 6.1: Dual-Runtime MCP Tool Exposure with Visibility Control

| Attribute | Detail |
|---|---|
| **Location** | `src/servers/mcp-server.ts`, `src/server/mcp/recall-mcp-server.ts`, `src/servers/mcp-tool-visibility.ts` |
| **Scope** | Function `selectRuntime`, Function `createRecallMcpServer`, Function `getAdvertisedMcpToolsForRuntime` |
| **Line Range** | Lines 1–300 approx. (mcp-server); Recall server 100–200 lines approx. |
| **Dependencies** | Internal: SearchManager, ServerClient, worker lifecycle; External: MCP SDK (stdio) |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Exposes search, timeline, context, and corpus operations as MCP tools over stdio and HTTP, routing per call to either a local worker or a hosted server, and hides server-only tools when running in worker mode.

**How It Works (Conceptual):**
Uses a Backend-for-Frontend over MCP: a narrow recall backend (search/context/recent) is wrapped by transport adapters, with runtime resolution and capability advertisement decided per invocation rather than at install time.

**Relevance to Your Project:**
Shows how hunter agents and analyst copilots should consume GHOST THREAD: Cartographer and hunters as MCP tools (gap-list, evidence-search, timeline, corpus-query) callable from any agent host, with graceful fallback when the hosted graph is unreachable.

**Suggested Adaptation Strategy:**
Define a minimal read-only recall surface first (entity-context, gap-search, timeline) before exposing mutating hunts. Reuse visibility gating to hide administrative or bulk-rebuild tools from routine analyst sessions.

#### Finding 6.2: Hardened Multi-Tenant API with Scoped Keys and Metering

| Attribute | Detail |
|---|---|
| **Location** | `src/server/routes/v1/ServerV1PostgresRoutes.ts`, `src/server/middleware/auth.ts`, `rate-limit.ts`, `usage-metering.ts`, `src/server/auth/sqlite-api-key-service.ts` |
| **Scope** | Class `ServerV1PostgresRoutes`, Function `requireServerAuth`, Function `createServerApiKey` |
| **Line Range** | Lines 1–400 approx. (routes); Middleware 50–120 lines each |
| **Dependencies** | Internal: IngestEventsService, EndSessionService; External: Express, BetterAuth, SHA256 hashing |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Provides versioned REST (events, sessions, memories, search/context, jobs) guarded by bearer-or-key auth with scoped permissions, loopback-only local-dev bypass, rate limiting, request IDs, and usage accounting.

**How It Works (Conceptual):**
Enforces defense in depth at the edge: authentication resolves team/project scope, authorization checks per-route scopes, and metering records consumption for quota and audit. Key material is hashed at rest with bootstrapped hook-scoped keys.

**Relevance to Your Project:**
OSINT systems face scraping-rate limits, source ToS sensitivity, and case confidentiality. This is the reference for isolating investigations by case/team, throttling hunts per source, and auditing who triggered which hunter.

**Suggested Adaptation Strategy:**
Copy scope granularity (events-write, sessions-write, observations-read, jobs-read) as hunt-trigger vs. evidence-read vs. job-admin. Study local-dev bypass constraints to avoid accidentally exposing case graphs on loopback in field deployments.

#### Finding 6.3: Resilient Daemon Spawning and Health Supervision

| Attribute | Detail |
|---|---|
| **Location** | `src/services/infrastructure/ProcessManager.ts`, `HealthMonitor.ts`, `GracefulShutdown.ts`, `src/services/worker-service.ts`, `worker-spawner.ts` |
| **Scope** | Function `spawnDaemon`, Function `waitForHealth`, Class `GracefulShutdown` |
| **Line Range** | Lines 1–200 approx. each |
| **Dependencies** | Internal: PID/port runtime files, settings; External: OS process primitives |
| **Relevance Rating** | ★★★☆☆ |

**What It Does:**
Spawns and supervises background worker/server daemons across POSIX and Windows, waits for health/readiness with port-occupancy classification, verifies versions, and shuts down gracefully without orphaning jobs.

**How It Works (Conceptual):**
Treats background agents as supervised processes with explicit runtime manifests (PID, port, version). Health is probed over HTTP with bounded waits; ownership is verified via PID files rather than error codes to avoid killing unrelated processes.

**Relevance to Your Project:**
Infrastructure for long-running hunter fleets that must survive analyst laptop sleep, network partitions, and source throttling. Stale-spawn recovery here maps to reaping orphaned hunts after Cartographer restarts.

**Suggested Adaptation Strategy:**
Adopt PID-file ownership and version-match checks before reusing a running hunter pool. Study detached-spawn differences per OS if field kits include Windows. Combine with queue stall handling (Finding 1.2) for end-to-end hunt supervision.

#### Finding 6.4: Privacy-Preserving Prompt Construction and Redaction

| Attribute | Detail |
|---|---|
| **Location** | `src/server/generation/providers/shared/prompt-builder.ts`, `src/sdk/prompts.ts`, `src/utils/redaction.ts`, `src/sdk/hardened-options.ts` |
| **Scope** | Function `buildServerGenerationPrompt`, Constant `REDACTION_MARKER_HINT` |
| **Line Range** | Lines 1–228 approx. (builder); Prompts Lines 1–514 approx.; Redaction 30–80 lines approx. |
| **Dependencies** | Internal: ModeManager, SessionStore; External: LLM providers |
| **Relevance Rating** | ★★★★☆ |

**What It Does:**
Builds bounded, schema-guided prompts from stored events while stripping tagged private content, enforcing output-format headers, and constraining SDK options to a hardened subset.

**How It Works (Conceptual):**
Applies data minimization at prompt-build time: event blocks are size-capped, sensitive spans are removed before the model sees them, and system identity plus format examples steer output toward validatable structures.

**Relevance to Your Project:**
OSINT evidence routinely contains PII that must not leak into model logs, briefs, or cross-case corpora. This is the pattern for building hunter prompts that carry only case-scoped, redacted evidence with explicit absence-taxonomy guidance.

**Suggested Adaptation Strategy:**
Introduce redaction markers at ingestion so stripping is deterministic at prompt time. Study byte-capped event blocks to bound prompt cost when filings or forum threads are large. Pair with Finding 4.2 validation so redacted gaps are not misclassified as absent.

---

## Cross-Cutting Observations

- **Worker proposes, store disposes.** Across search, generation, and sync, vectors, queues, and model outputs are treated as untrusted hints; SQLite/Postgres rows are the only truth. GHOST THREAD should enforce the same for hunter claims about absence.
- **Budgeted briefing is architectural, not cosmetic.** ContextBuilder, pool sizing in reinforcement ranking, and prompt byte caps all reflect a philosophy of fetch-generously then fit-to-budget. Saturation briefs need identical section-aware trimming.
- **Absence is already a first-class signal in miniature.** Idle-versus-prose classification, reinforced-but-old observations, tombstone-aware vector deletes, and echo-guarded sync all reason about what is missing or stale. None combine into a completeness map, which is precisely the Cartographer opportunity.
- **Strategy + adapter ubiquity.** Search strategies, provider dispatch, platform adapters, and runtime selectors all isolate variation behind narrow interfaces. Hunter specializations and OSINT source adapters fit naturally in the same shape.
- **Fail-open edge, strict core.** Hooks never break the host, but parsers, idempotency keys, and transactional applies are strict. Preserve this split: hunts may degrade, evidence commits must not.

---

## Recommended Exploration Priority

1. **SessionManager + SessionMessageBuffer** — Clone Cartographer session/buffer separation for per-entity investigation workspaces.
2. **SearchOrchestrator + Hybrid strategy** — Foundation for reconstruction and counter-narrative recall over noisy aliases.
3. **ObservationCompiler.buildTimeline + TimelineService** — Base for Temporal Gap detection of silences and coordinated deletions.
4. **Parser + output-classifier + prompt-builder** — Enforce ghost-node taxonomy and make failed hunts auditable.
5. **SessionStore + SessionSearch FTS** — Substrate for ghost-node rows with project/case scoping and lexical registry search.
6. **ProviderObservationGenerator + BullMQ lanes** — Model for gap-triage versus deep-dive hunter queues with stall recovery.
7. **ContextBuilder + Budget + TokenCalculator** — Template for saturation briefs that preserve absence distinctions under limits.
8. **ModeManager inheritance** — Implement hunter specialists as base-plus-override configs.
9. **ACT-R strength/rank** — Reward persistently re-confirmed absences without vectors.
10. **ChromaSync as derived index** — Power Context Comparator similarity without letting vectors invent evidence.
11. **KnowledgeAgent corpus pattern** — Scope each hunter to a compiled entity snapshot.
12. **TranscriptWatcher + hook pipeline** — Pattern for resumable OSINT source taps with fail-open ingestion.
13. **Postgres ledger + generation keys** — Audit raw captures versus interpretations with safe retries.
14. **MCP recall server + visibility gating** — Expose gap-search and timeline as tools to analyst agents.
15. **Redaction + scoped API keys + rate limits** — Handle PII, case isolation, and source throttling from day one.

---

## Potential Gaps & Caveats

- **No absence reasoning.** The repository never builds expected-information schemas, ghost nodes, or deviation scoring. Completeness-map logic, expected-cadence tables, and anomaly thresholds must be built new.
- **No OSINT connectors.** Wayback, registries, social archives, and domain infra sources are absent. Transcript and memory ingestors are patterns only; source-specific fetching, ToS compliance, and anti-blocking are unsolved.
- **Single-entity myopia.** Context and search are project/session-scoped, not entity-graph scoped. Cross-entity joins (shell networks, shared officers, correlated deletion timing) require a graph layer beyond FTS + vectors.
- **Scale mismatch.** SQLite WAL plus single-concurrency queues suit single-analyst use; multi-analyst concurrent hunts will need Postgres server mode, Redis tuning, and explicit sharding that the migration docs flag as in-progress.
- **Language and dependency weight.** Primary runtime is Bun/Node TypeScript with a Python sidecar for Chroma and many tree-sitter grammars. If GHOST THREAD targets Python-native OSINT tooling, interop costs and supply-chain surface (esbuild-inlined deps, uv-managed Chroma) should be weighed.
- **No adversarial evaluation.** Dedup and classifier tests cover benign drift, not deliberate disinformation, sockpuppet aliasing, or poisoned archives that a Counter-Narrative Agent must withstand.

---

## Licensing & Attribution Notice

The analyzed repository declares Apache License 2.0 (see `LICENSE` at repository root, `NOTICE`, and `docs/license.md`). This report contains no reproduced source code, only conceptual descriptions with file-path and symbol references. Before adapting patterns or porting logic into GHOST THREAD, review the license obligations for attribution, modification notices, and included-notice propagation, and verify dependency licenses for bundled components (MCP SDK, agent SDKs, ChromaDB, BullMQ). Consult counsel for OSINT-specific collection and retention duties that are independent of software licensing.

