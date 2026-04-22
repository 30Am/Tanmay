# Phase 01 — Data Collection

Metadata registry for the 170 videos that seed TanmayGPT's persona corpus. Transcription
is handled in Phase 02 (Deepgram) — this directory contains URLs + full YouTube metadata,
not transcripts.

## Scope

| Source | Count | Duration (h) | URL |
| --- | ---: | ---: | --- |
| Honestly by Tanmay Bhat (channel) | 121 | 60.9 | https://www.youtube.com/channel/UCneQdPbDLwZ__ZXP0YVwiag |
| Overpowered (channel, filtered to Tanmay-present) | 33 collected / 14 tagged | 24.3 | https://www.youtube.com/@AI.Overpowered |
| Curated Google Sheet (external Tanmay interviews) | 16 | 24.7 | https://docs.google.com/spreadsheets/d/18YM_4kGJbmeMNQBg0ORRFKVkDJA_Wzd32zVFFwtjZ8Y/ |
| **Total** | **170** | **~110** | — |

Honestly breakdown: 107 videos + 10 streams + 4 shorts. "Count 122" in spec ≈ 121 found
on the channel today (YouTube sometimes counts deleted/private).

## Layout

```
data/
├── manifest.json              # source → video_id list, 170 entries (minimal fields)
├── index.json                 # enriched per-video record (title, description, tags, duration,
│                              #   upload_date, view_count, channel, has_subs, subs_langs)
├── overpowered_tanmay.json    # subset: 14 Overpowered videos tagged Tanmay-present
├── stats.md                   # human-readable summary (what finalize.py prints)
├── build_manifest.py          # step 1: channel-list TSVs → manifest.json
├── collect.py                 # step 2: manifest → per-video {vid}.info.json (+ transcripts, blocked)
├── finalize.py                # step 3: walk raw/ → index.json + overpowered_tanmay.json + stats.md
├── download_batch.sh          # (retired) early yt-dlp attempt, superseded by collect.py
├── run_downloads.sh           # (retired) early driver, superseded by collect.py
├── logs/
│   ├── collect.log            # per-video timestamps + failures
│   ├── honestly_videos.tsv    # raw flat-playlist dumps (inputs to build_manifest.py)
│   ├── honestly_streams.tsv
│   ├── honestly_shorts.tsv
│   ├── overpowered_videos.tsv
│   └── sheet_ids.txt
└── raw/
    ├── honestly/<video_id>/<video_id>.info.json
    ├── overpowered/<video_id>/<video_id>.info.json
    └── sheet/<video_id>/<video_id>.info.json
```

## Rerunning

All scripts are idempotent and resumable.

```bash
# Rebuild source lists + manifest from scratch
python3 build_manifest.py

# Fetch metadata only (IP-safe; yt-dlp info endpoint)
SKIP_TRANSCRIPTS=1 python3 collect.py

# Aggregate to index.json + filter Overpowered for Tanmay + write stats.md
python3 finalize.py
```

## Overpowered → Tanmay filter

`finalize.py` marks an Overpowered video as "Tanmay-present" iff the substring `tanmay`
(case-insensitive, word-boundary) appears in the video's title, description, channel
name, or tag list. 14 / 33 match today. Tanmay co-hosts the show so some episodes likely
feature him without explicitly naming him — a human pass over the 19 unmatched videos may
promote a few more. See `overpowered_tanmay.json` for the matched list.

## What's NOT in here (intentionally)

- **Transcripts.** YouTube's subtitle endpoint (both youtube-transcript-api and yt-dlp
  `--write-auto-sub`) returned `HTTP 429 / IpBlocked` about 15 videos into the first pass.
  The blueprint's Phase 02 is "Deepgram transcription + diarization backfill" anyway, and
  Deepgram's Hindi models outperform YouTube's auto-captions on Hinglish content, so we
  skip the YouTube-scraped pass and let Phase 02 transcribe from audio. (1 `.hi.vtt`
  remains in `raw/honestly/7VHiTGjkIvQ/` from the early test before the block — ignore.)
- **Audio or video files.** Phase 02 downloads audio on demand per video.
- **Tanmay's own channel (`@tanmaybhat`).** Out of Phase 01 scope per the user's brief;
  flagged `enabled: false` in `config/sources.yaml`.

## Guardrail check

The project README lists "No scraping runs before a signed license" under guardrails.
This pass was run on the explicit instruction of the repo owner. The data collected is
metadata (titles, descriptions, tags, view counts, durations, upload dates) — all
public-facing YouTube fields — and no audio/video. Transcripts, once they arrive via
Deepgram, should be treated as licensed content.
