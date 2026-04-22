"""Build master manifest from the three source lists.

Inputs:
  logs/honestly_videos.tsv, honestly_streams.tsv, honestly_shorts.tsv
  logs/overpowered_videos.tsv
  logs/sheet_ids.txt

Output:
  manifest.json — flat list of {source, kind, video_id, title, duration_s, url}
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).parent
LOGS = DATA / "logs"


def read_tsv(path: Path, source: str, kind: str) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        vid, title, dur, url = parts[0], parts[1], parts[2], parts[3]
        try:
            duration_s = int(float(dur)) if dur and dur != "NA" else None
        except ValueError:
            duration_s = None
        rows.append(
            {
                "source": source,
                "kind": kind,
                "video_id": vid,
                "title": title,
                "duration_s": duration_s,
                "url": url,
            }
        )
    return rows


def read_ids(path: Path, source: str, kind: str) -> list[dict]:
    rows = []
    for vid in path.read_text().splitlines():
        vid = vid.strip()
        if not vid:
            continue
        rows.append(
            {
                "source": source,
                "kind": kind,
                "video_id": vid,
                "title": None,
                "duration_s": None,
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        )
    return rows


def main() -> None:
    entries: list[dict] = []
    entries += read_tsv(LOGS / "honestly_videos.tsv", "honestly", "video")
    entries += read_tsv(LOGS / "honestly_streams.tsv", "honestly", "stream")
    entries += read_tsv(LOGS / "honestly_shorts.tsv", "honestly", "short")
    entries += read_tsv(LOGS / "overpowered_videos.tsv", "overpowered", "video")
    entries += read_ids(LOGS / "sheet_ids.txt", "sheet", "video")

    seen = set()
    deduped = []
    for e in entries:
        key = (e["source"], e["video_id"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    out = DATA / "manifest.json"
    out.write_text(json.dumps(deduped, indent=2, ensure_ascii=False))

    by_source: dict[str, int] = {}
    for e in deduped:
        by_source[e["source"]] = by_source.get(e["source"], 0) + 1
    print(f"Total: {len(deduped)}  by source: {by_source}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
