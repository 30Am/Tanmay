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
