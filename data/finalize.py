"""Post-download finalization.

1. Walk raw/<source>/<video_id>/<vid>.info.json, aggregate metadata.
2. For Overpowered: flag videos where Tanmay appears in title/description/tags.
3. Emit:
    - data/index.json       enriched manifest (all fields + has_subs + subs_langs)
    - data/overpowered_tanmay.json  subset where Tanmay-present = True
    - data/stats.md         human-readable summary
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DATA = Path(__file__).parent
RAW = DATA / "raw"

TANMAY_PAT = re.compile(r"\btanmay\b", re.IGNORECASE)


def parse_info(path: Path) -> dict:
    d = json.loads(path.read_text())
    return {
        "video_id": d.get("id"),
        "title": d.get("title"),
        "description": d.get("description") or "",
        "upload_date": d.get("upload_date"),
        "duration_s": d.get("duration"),
        "view_count": d.get("view_count"),
        "channel": d.get("channel"),
        "channel_id": d.get("channel_id"),
        "tags": d.get("tags") or [],
        "uploader": d.get("uploader"),
        "webpage_url": d.get("webpage_url"),
    }


def mentions_tanmay(meta: dict) -> bool:
    haystack = " ".join(
        [
            meta.get("title") or "",
            meta.get("description") or "",
            meta.get("channel") or "",
            " ".join(meta.get("tags") or []),
        ]
    )
    return bool(TANMAY_PAT.search(haystack))


def main() -> None:
    index = []
    for source_dir in sorted(RAW.iterdir()):
        if not source_dir.is_dir():
            continue
        source = source_dir.name
        for vid_dir in sorted(source_dir.iterdir()):
            if not vid_dir.is_dir():
                continue
            info = vid_dir / f"{vid_dir.name}.info.json"
            if not info.exists():
                continue
            meta = parse_info(info)
            subs = sorted(p.name for p in vid_dir.glob("*.vtt"))
            subs_langs = sorted({p.name.split(".")[-2] for p in vid_dir.glob("*.vtt")})
            meta.update(
                {
                    "source": source,
                    "has_subs": bool(subs),
                    "subs_langs": subs_langs,
                    "sub_files": subs,
                    "dir": str(vid_dir.relative_to(DATA)),
                }
            )
            index.append(meta)

    (DATA / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))

    op_tanmay = [e for e in index if e["source"] == "overpowered" and mentions_tanmay(e)]
    (DATA / "overpowered_tanmay.json").write_text(
        json.dumps(op_tanmay, indent=2, ensure_ascii=False)
    )

    by_source: dict[str, dict] = {}
    for e in index:
        s = e["source"]
        b = by_source.setdefault(s, {"count": 0, "with_subs": 0, "total_duration_h": 0.0})
        b["count"] += 1
        if e["has_subs"]:
            b["with_subs"] += 1
        if e.get("duration_s"):
            b["total_duration_h"] += e["duration_s"] / 3600.0

    op_total = by_source.get("overpowered", {}).get("count", 0)

    lines = ["# Phase 01 — Data Collection Stats\n"]
    lines.append(f"Total videos ingested: **{len(index)}**\n")
    lines.append("| Source | Count | With subs | Duration (h) |")
    lines.append("| --- | ---: | ---: | ---: |")
    for s, b in sorted(by_source.items()):
        lines.append(f"| {s} | {b['count']} | {b['with_subs']} | {b['total_duration_h']:.1f} |")
    lines.append("")
    lines.append(f"## Overpowered — Tanmay appearances\n")
    lines.append(f"{len(op_tanmay)} / {op_total} videos mention Tanmay "
                 f"in title/description/tags.\n")
    for e in op_tanmay:
        lines.append(f"- `{e['video_id']}` — {e['title']}")

    (DATA / "stats.md").write_text("\n".join(lines))
    print("\n".join(lines[:10]))
    print(f"\nWrote index.json, overpowered_tanmay.json, stats.md")


if __name__ == "__main__":
    main()
