# Create with Tanmay

Licensed creator-persona platform. Three creator tools, one persona core:

| Tab | Purpose |
| --- | --- |
| **Content** | Idea → script + description in Tanmay's register. |
| **Ad** | Structured brief → scene-by-scene ad with rationale + brand-safety gate. |
| **Q&A** | "How would Tanmay answer this?" — grounded answers or an honest refusal. |

Blueprint lives at `docs/tanmay-gpt-architecture.html` (source of truth for the design).

---

## Repo layout

```
.
├── apps/
│   ├── api/            FastAPI backend (RAG orchestrator, 3 endpoints, streaming)
│   └── web/            Next.js 14 frontend (3 tabs, SSE streaming, tone dial)
├── packages/
│   └── ingestion/      Celery workers + processing pipeline (chunker, tagger, embedder)
├── config/
│   ├── sources.yaml           Source registry (one entry = one ingestion job)
│   └── sources.schema.yaml    JSON-schema validation
├── infra/
│   ├── docker-compose.yml     Local Postgres + Redis + Qdrant + MinIO + api + web
│   └── init.sql               Relational schema (sources, chunk_metadata, users, generations)
├── scripts/                   Ops helpers (ingest, reindex, evals)
└── README.md
```

---

## Quick start (local)

### Prereqs
- Docker + Docker Compose
- Python 3.12 (for running backend/ingestion locally without Docker)
- Node 20+ (for running web without Docker)

### 1. Clone + env files
```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
# Fill in ANTHROPIC_API_KEY, VOYAGE_API_KEY, COHERE_API_KEY, DEEPGRAM_API_KEY
```

### 2. Bring up local infra
```bash
cd infra
docker compose up -d postgres redis qdrant minio
# Apply schema
docker compose exec -T postgres psql -U tanmay -d tanmay < init.sql
```

### 3. Run the backend
```bash
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### 4. Run the frontend
```bash
cd apps/web
npm install
npm run dev  # http://localhost:3000
```

### 5. (Optional) Run Celery worker + beat
```bash
cd packages/ingestion
pip install -e .
celery -A celery_app.celery_app worker --loglevel=info
celery -A celery_app.celery_app beat --loglevel=info
```

---

## Build order (from the blueprint)

| Phase | Deliverable | Time |
| --- | --- | --- |
| 00 | Licensing agreement | 1 wk |
| 01 | Source registry + platform scrapers | 1.5 wk |
| 02 | Deepgram transcription + diarization backfill | 1 wk |
| 03 | Chunking, tagging, embedding into Qdrant | 1 wk |
| 04 | Persona prompt + blind-test validation | 1 wk |
| 05 | RAG orchestrator + Tab 1 MVP | 1.5 wk |
| 06 | Tab 2 with brand-safety gate | 1 wk |
| 07 | Tab 3 with confidence gate + citation verifier | 1 wk |
| 08 | Frontend polish (parallel track) | 2 wk |
| 09 | Evals + red team | 1 wk |
| 10 | Private beta → public launch | 2 wk |

Ship **Tab 3 first** — it's the cheapest to validate retrieval quality against.

---

## Guardrails (non-negotiable)

1. **Legal first.** No scraping runs before a signed license.
2. **Refuse honestly.** Tab 3 declines when max similarity < threshold — no fabrication.
3. **Sensitive-topic hard refusals.** Politics, religion, mental-health prescriptions.
4. **Brand-safety gate on Tab 2.** Flag refused categories (gambling, predatory finance) before generating.
5. **Cite everything.** Every public response ships with source links + timestamps.
6. **Watermark voice.** If ElevenLabs voice ships, every audio is watermarked, logged, revocable.

---

## Key tech decisions

- **Frontend:** Next.js 14 App Router + Tailwind + shadcn/ui + Vercel AI SDK for SSE.
- **Backend:** FastAPI + Pydantic v2 + SSE-Starlette. LangGraph optional for multi-step flows.
- **LLM:** Claude Sonnet 4.6 primary, Opus 4.6 premium, Haiku 4.5 utility (tagging, query expansion).
- **Embeddings:** Voyage-3 (1024d). Cohere Rerank 3 as the final squeeze.
- **Vector DB:** Qdrant self-hosted. Postgres for metadata + FTS. Redis for cache + Celery broker.
- **Observability:** Langfuse for LLM traces, PostHog for product analytics, Sentry for errors.

See `docs/tanmay-gpt-architecture.html` for the full blueprint (diagrams, phase-by-phase plan, risks).
