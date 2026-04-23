import { ExternalLink } from "lucide-react";
import type { Citation } from "@/lib/types";

function timestampedUrl(c: Citation): string {
  if (c.platform === "youtube" && c.timestamp_seconds != null && c.url.includes("watch?v=")) {
    const sep = c.url.includes("?") ? "&" : "?";
    return `${c.url}${sep}t=${c.timestamp_seconds}s`;
  }
  return c.url;
}

function fmtTs(s: number | null | undefined): string {
  if (s == null) return "";
  const total = Math.floor(s);
  const m = Math.floor(total / 60);
  const ss = total % 60;
  return `${m}:${String(ss).padStart(2, "0")}`;
}

export default function CitationCard({ idx, c }: { idx: number; c: Citation }) {
  return (
    <a
      href={timestampedUrl(c)}
      target="_blank"
      rel="noreferrer"
      className="block rounded-xl border border-line bg-canvas/50 hover:bg-white transition p-3.5 group"
    >
      <div className="flex items-start gap-3">
        <div className="shrink-0 h-6 w-6 rounded-md bg-white border border-line text-[11px] font-mono grid place-items-center text-inkMuted">
          {idx}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[13px] font-medium truncate max-w-[90%]">
              {c.title || "(untitled)"}
            </span>
            {c.timestamp_seconds != null && (
              <span className="font-mono text-[10px] text-inkSubtle">@ {fmtTs(c.timestamp_seconds)}</span>
            )}
          </div>
          <div className="mt-1 text-[12px] text-inkMuted line-clamp-2 leading-snug">
            {c.excerpt}
          </div>
        </div>
        <ExternalLink size={14} className="shrink-0 text-inkSubtle group-hover:text-pinkDeep transition" />
      </div>
    </a>
  );
}
