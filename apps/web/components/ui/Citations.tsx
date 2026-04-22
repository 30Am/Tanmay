import type { Citation } from "@/lib/types";

function buildHref(c: Citation): string {
  if (c.platform === "youtube" && c.timestamp_seconds != null) {
    const sep = c.url.includes("?") ? "&" : "?";
    return `${c.url}${sep}t=${c.timestamp_seconds}s`;
  }
  return c.url;
}

export function Citations({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-6 rounded-lg border border-border bg-panel p-4">
      <div className="mb-3 text-xs uppercase tracking-[0.15em] text-accentGreen">Sources</div>
      <ol className="space-y-2 text-sm">
        {citations.map((c, i) => (
          <li key={`${c.source_id}-${i}`} className="flex gap-2">
            <span className="text-muted">[{i + 1}]</span>
            <div className="flex-1">
              <a
                href={buildHref(c)}
                target="_blank"
                rel="noreferrer"
                className="text-accentBlue hover:underline"
              >
                {c.platform}
                {c.timestamp_seconds != null ? ` @${c.timestamp_seconds}s` : ""}
              </a>
              <div className="text-xs text-muted">{c.excerpt}</div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
