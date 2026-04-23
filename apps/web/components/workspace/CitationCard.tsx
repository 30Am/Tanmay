import { ExternalLink } from "lucide-react";
import type { Citation } from "@/lib/types";

function timestampedUrl(c: Citation): string {
  if (c.platform === "youtube" && c.timestamp_seconds != null && c.url.includes("watch?v=")) {
    const sep = c.url.includes("?") ? "&" : "?";
    return `${c.url}${sep}t=${c.timestamp_seconds}s`;
  }
  return c.url;
}

function fmt(s: number | null | undefined): string {
  if (s == null) return "";
  const m = Math.floor(s / 60);
  const ss = Math.floor(s % 60);
  return `${m}:${String(ss).padStart(2, "0")}`;
}

export default function CitationCard({ idx, c }: { idx: number; c: Citation }) {
  return (
    <a
      href={timestampedUrl(c)}
      target="_blank"
      rel="noreferrer"
      className="flex items-start gap-3 rounded-2xl bg-surface border border-border p-4 hover:shadow-card transition group"
    >
      <div className="h-7 w-7 rounded-lg bg-bg border border-border grid place-items-center text-[12px] font-mono text-ink-2 shrink-0">
        {idx}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[14px] font-medium text-ink truncate max-w-[95%]">
            {c.title || "(untitled)"}
          </span>
          {c.timestamp_seconds != null && (
            <span className="font-mono text-[11px] text-ink-3">@ {fmt(c.timestamp_seconds)}</span>
          )}
        </div>
        <p className="mt-1 text-[13px] text-ink-2 leading-snug line-clamp-2">{c.excerpt}</p>
      </div>
      <ExternalLink size={14} className="text-ink-3 group-hover:text-ink transition shrink-0 mt-1" />
    </a>
  );
}
