# Phase 02 — Transcription

Total videos transcribed: **170 / 170** (Deepgram Nova-3, diarized, smart-formatted)

Total audio: **109.8 hours**
Total utterance segments: **68,548**
Total Deepgram spend: **$28.34**

| Source | Videos | Duration (h) | Segments | Languages |
| --- | ---: | ---: | ---: | --- |
| honestly | 121 | 60.9 | 38,917 | en=117, hi=2, unknown=2 |
| overpowered | 33 | 24.3 | 13,893 | en=33 |
| sheet | 16 | 24.7 | 15,738 | en=16 |

Outputs per video at `raw/<source>/<video_id>/`:
- `transcript.json` — normalized (speakers, start/end, text, confidence)
- `provider_raw.json` — unmodified Deepgram response

---

# Phase 03 — Chunking, Tagging, Embedding

Pipeline: word-level Deepgram → speaker/pause-aware chunker (400-800 tok target) → Gemini 2.5 Flash-Lite tagger → Voyage-3 embeddings (1024d) → Qdrant upsert.

Total chunks in Qdrant `tanmay_chunks`: **3,208**
Vector dim: 1024 (Voyage-3, cosine)

| Source | Chunks |
| --- | ---: |
| honestly | 1,692 |
| overpowered | 771 |
| sheet | 745 |

### By register (Gemini tagger, improved prompt with rubric + few-shot)

| register | count | share |
| --- | ---: | ---: |
| informative | 1,697 | 53% |
| comedic | 965 | 30% |
| reflective | 467 | 15% |
| roast | 61 | 1.9% |
| sincere | 18 | 0.6% |

### By dominant language

| language | count |
| --- | ---: |
| English-dominant | 3,142 |
| Mixed | 25 |
| Hindi-dominant | 41 |

### Tanmay speaker identification

Per-video Gemini pass identifies which Deepgram speaker-id is Tanmay.

| confidence | videos |
| --- | ---: |
| high | 169 |
| medium | 1 |
| low / null | 0 |

**Tanmay-labeled chunks: 958 / 3,208** (~30%). Stored as `is_tanmay=true` in Qdrant payload, with `tanmay_speaker` (int) and `tanmay_confidence` (string) metadata.

Identification map: [data/tanmay_speakers.json](data/tanmay_speakers.json).

### Style-exemplar collection

Separate Qdrant collection `tanmay_exemplars` for few-shot prompting in Phase 04+.
Selection: Tanmay-only chunks, medium/high confidence, filtered by register with caps:

| register | cap | selected |
| --- | ---: | ---: |
| comedic | 80 | 80 |
| reflective | 60 | 60 |
| roast | 40 | 17 |
| sincere | 20 | 7 |

**Total exemplars: 164** (limited by natural scarcity of roast/sincere in the corpus).

### Chunk payload fields

Per-chunk Qdrant payload: `source, video_id, title, url, upload_date, duration_s, channel, language, source_id, text, start_seconds, end_seconds, speaker, speakers, is_tanmay, tanmay_speaker, tanmay_confidence, topic_tags, register, language_mix, entities, sentiment, chunk_id`

### Infra

- Qdrant v1.17.1 running locally (REST 6333, gRPC 6334), storage at `infra/qdrant/storage/`
- Collections: `tanmay_chunks` (3,208 pts, 1024d cosine), `tanmay_exemplars` (164 pts, 1024d cosine)
- Scripts (all idempotent):
  - [data/embed.py](data/embed.py) — chunk + tag + embed + upsert
  - [data/identify_speaker.py](data/identify_speaker.py) — per-video Tanmay-speaker ID
  - [data/mark_tanmay.py](data/mark_tanmay.py) — stamp `is_tanmay` on Qdrant chunks
  - [data/retag.py](data/retag.py) — retag all chunks with updated prompt
  - [data/build_exemplars.py](data/build_exemplars.py) — build exemplars collection

---

# Phase 04 — Persona Engineering (v1 draft)

Data-grounded rewrite of `PERSONA_IDENTITY`, `VOICE_PATTERNS`, `TOPIC_POSTURE` in [apps/api/app/services/persona.py](apps/api/app/services/persona.py). Based on automated voice analysis of 94 high-register Tanmay chunks.

### Voice corpus (Tanmay-only, high-confidence)

| register | chunks |
| --- | ---: |
| comedic | 40 |
| reflective | 30 |
| roast | 17 |
| sincere | 7 |
| **total** | **94** |

Saved at [data/voice_corpus.json](data/voice_corpus.json).

### Voice profile (Gemini 2.5 Flash analysis)

Structured output with chunk_id citations per observation. Saved at [data/voice_profile.json](data/voice_profile.json). Includes:
- 6 signature phrases (`Right?`, `dude/bro/man`, `you know`, etc.)
- Sentence mechanics (mixed length, high rhetorical question rate, frequent direct address)
- 4 opener / transition patterns with example quotes
- Self-deprecation style + triggers (money mistakes, appearance, ignorance admission, production fumbles)
- Roast technique: targets, escalation, when he softens
- Hinglish mechanics: ratio, 20+ frequent Hindi anchors, code-switch triggers
- Topic posture across 6 domains
- Avoided / absent patterns (no partisan politics, no preachy tone, no hero-worship)

### Persona prompt v1

Canonical source of truth: [config/persona/v1.md](config/persona/v1.md).
Python module: [apps/api/app/services/persona.py](apps/api/app/services/persona.py) (`PERSONA_VERSION = "v1"`).

Assembled prompt size (content tab example): ~4,500 chars / ~1,130 tokens.

### Still pending for Phase 04

- **Blind-test validation** — requires human panel (target: 50% indistinguishable vs real Tanmay content). Deferred until Phase 05 generation harness is live.
- **Per-tab format rules** — Tab 1 (content), Tab 2 (ad), Tab 3 (Q&A) need their own `FORMAT:` blocks. Currently only stubbed.
- **Tone dial calibration** — `tone_modifier()` implemented, but no empirical testing of how the dial actually shifts outputs.

### Phase 04 scripts

- [data/pull_voice_corpus.py](data/pull_voice_corpus.py) — pulls voice corpus from Qdrant
- [data/voice_analyze.py](data/voice_analyze.py) — Gemini voice analysis
- [config/persona/v1.md](config/persona/v1.md) — human-readable persona prompt

---

# Phase 05 — RAG Orchestrator + Tab 1/2/3 MVP

End-to-end pipeline live: query → Voyage embed → Qdrant search → Claude generate, with persona v1 + style exemplars + prompt caching.

### Stack wired

- **LLM:** Claude Sonnet 4.6 (primary), Haiku 4.5 (utility). Dev work done on Haiku, final tests on Sonnet.
- **Embeddings:** Voyage-3 (1024d, cosine)
- **Vector DB:** Qdrant v1.17.1 (`tanmay_chunks` 3,208 pts, `tanmay_exemplars` 164 pts)
- **Rerank:** Cohere Rerank 3 — stubbed; falls back to embedding-score ordering (no Cohere key yet)
- **API:** FastAPI — 3 routes live: `POST /generate/content`, `POST /generate/ad`, `POST /generate/qa`

### Files

- [apps/api/app/services/rag.py](apps/api/app/services/rag.py) — `RAGEngine` orchestrator with prompt caching on the persona prefix
- [apps/api/app/routers/content.py](apps/api/app/routers/content.py) — Tab 1 (script + description + rationale + citations)
- [apps/api/app/routers/ad.py](apps/api/app/routers/ad.py) — Tab 2 (JSON-schema ad with scenes, CTA, brand-safety flags)
- [apps/api/app/routers/qa.py](apps/api/app/routers/qa.py) — Tab 3 (confidence-gated, sensitive-topic refuser, cited)

### Smoke test (Haiku 4.5)

All three tabs produced coherent Tanmay-voice output for **~$0.03 total**.
[data/rag_smoke.py](data/rag_smoke.py) is the reproducible driver.

### FastAPI live test

`POST http://localhost:8000/generate/qa` with question "what does Tanmay think about therapy":

- HTTP 200, 16.5s latency (Sonnet 4.6)
- Answer in Tanmay voice with signature phrases ("Right? Let me tell you…", "gym for your head")
- 8 citations with URL + timestamps, max_similarity 0.504
- `status=answered` — confidence gate passed

### Phase 04 completion — the three pending items

1. **Blind-test proxy (automated).** 10 samples compared via Voyage embedding similarity: generated output vs source real-chunk, and vs a random Tanmay baseline.
   - Avg voice_match: **0.440**, random_baseline: **0.320**, **lift: +0.120**
   - 8/10 samples show positive delta — persona is measurably shifting generations toward target voice
   - [data/blind_test_proxy.py](data/blind_test_proxy.py) + [data/blind_test_results.json](data/blind_test_results.json)
   - Caveat: this is an automated proxy, not a fan-panel blind test. Real blind-test still pending.

2. **Per-tab FORMAT rules.** Added to [persona.py](apps/api/app/services/persona.py):
   - `FORMAT_CONTENT` — SCRIPT / DESCRIPTION / RATIONALE / CITATIONS
   - `FORMAT_AD` — strict JSON schema with scenes, CTA, brand_safety_flags
   - `FORMAT_QA` — confidence gate, sensitive-topic refusal, cited claims

3. **Tone-dial calibration.** Generated the same query at 8 dial settings (4 dimensions × 2 extremes + baseline).
   - Roast/chaos/depth/hinglish dials all measurably shift outputs in expected directions.
   - Effect is subtle (~sentence-level) at v1 prompt size. Works, but not dramatic.
   - [data/tone_calibrate.py](data/tone_calibrate.py) is the harness.

### Spend tracking

| Activity | Model | Cost |
| --- | --- | ---: |
| Smoke test (3 tabs) | Haiku | $0.03 |
| Tone calibration (8 runs) | Haiku | $0.065 |
| Blind-test proxy (10 gens) | Haiku | $0.09 |
| FastAPI live test (1 gen) | Sonnet | $0.05 |
| **Phase 05 total** | — | **~$0.24** |

### Still missing / deferred

- **SSE streaming** — endpoints return full JSON. `LLMService.stream()` exists but routers don't use it yet. Add for Phase 08 UI polish.
- **Cohere rerank** — key not provisioned. Currently falls back to pure-cosine ordering. Works OK for v1 retrieval.
- **Langfuse tracing** — not wired.
- **Postgres BM25 / hybrid retrieval** — deferred; vector-only retrieval is serviceable.
- **Real human blind-test** — still pending a fan panel.

---

## Overpowered — Tanmay appearances

14 / 33 videos mention Tanmay in title/description/tags.

- `0GBFCspv2H0` — Future of Communication, Midjourney Might Get Sued, Text To Music Just Got Insane and more....
- `1m4PAiExVuk` — How These People are Doing 4+ Jobs Using ChatGPT
- `Ey9xEBgG96E` — Who Said You Need to Code? - Building Chrome Extensions with SmolAI
- `JDYpGnlWuPY` — AutoGPT Replaced Software Devs? GPT Robots, One-Click VFX and More! ft. Tanmay Bhat & Varun Mayya
- `LRdS4BAfgMo` — Faceswap Yourself Into Any Image Using AI For Free!
- `L_wYrpW8N-M` — How ChatGPT Is Turning Everyone Into a Data Scientist!
- `WITWMclds2c` — Tanmay Bhat Turns From Comedian to Music Producer (Using AI)
- `_YyGsZPX24k` — How AI Just Disrupted E-KYC Human Verification
- `e29dJSuktWc` — Raised $2.3M at 19 From Sam Altman, Life in San Francisco, Web's Future & More Ft. Aryan Sharma
- `hY7S35KmOX8` — Building For The World From India ft. Vargab Bakshi, Meeting Sundar and more...
- `ne6FYUEdbuE` — MC Stan AI Diss Track By Eminem Ft. @VarunMayya  & @tanmaybhat | Overpowered
- `wv8vgbi5ToM` — Sam Altman In India, Apple Vision Pro, Problem With Text-to-video and more | Overpowered Episode 5
- `yR_CPoHSyjI` — Phone Calling AI Tanmay Bhat, Building React Apps Using Claude & more!
- `zMVTsykitiI` — ChatGPT Just Killed Exams & College Assignments!
