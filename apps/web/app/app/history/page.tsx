"use client";

import { useEffect, useState } from "react";
import { Clock, Trash2, ExternalLink } from "lucide-react";
import Link from "next/link";
import {
  getAllHistory,
  deleteEntry,
  clearHistory,
  relativeTime,
  type HistoryEntry,
} from "@/lib/history";
import { cn } from "@/lib/utils";

const TAB_META: Record<string, { label: string; color: string; href: string }> = {
  qa:      { label: "Q&A",     color: "bg-mint",      href: "/app/qa" },
  content: { label: "Content", color: "bg-coral/80",   href: "/app/content" },
  ad:      { label: "Ads",     color: "bg-lavender",   href: "/app/ads" },
};

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [filter, setFilter] = useState<"all" | "qa" | "content" | "ad">("all");

  useEffect(() => {
    setEntries(getAllHistory());
  }, []);

  const visible = filter === "all" ? entries : entries.filter((e) => e.tab === filter);

  function handleDelete(id: string) {
    deleteEntry(id);
    setEntries(getAllHistory());
  }

  function handleClearAll() {
    if (confirm("Clear all history? This can't be undone.")) {
      clearHistory();
      setEntries([]);
    }
  }

  return (
    <>
      {/* Header */}
      <div className="pt-12 pb-6 flex items-end justify-between">
        <div>
          <div className="caption text-ink-3">WORKSPACE</div>
          <h1 className="mt-2 text-[38px] font-bold tracking-[-0.02em] text-ink">History</h1>
          <p className="mt-1 text-body text-ink-2">
            Your last {entries.length} generation{entries.length !== 1 ? "s" : ""}, saved locally.
          </p>
        </div>
        {entries.length > 0 && (
          <button
            onClick={handleClearAll}
            className="inline-flex items-center gap-1.5 text-[13px] text-ink-3 hover:text-coral-deep transition"
          >
            <Trash2 size={13} /> Clear all
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2 mb-6">
        {(["all", "qa", "content", "ad"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={cn(
              "rounded-pill px-3.5 py-1.5 text-[13px] font-medium transition",
              filter === t
                ? "bg-ink text-surface"
                : "border border-border bg-surface text-ink-2 hover:text-ink",
            )}
          >
            {t === "all" ? "All" : TAB_META[t].label}
          </button>
        ))}
      </div>

      {/* Entry list */}
      {visible.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Clock size={32} className="text-ink-3 mb-4" />
          <p className="text-[15px] font-medium text-ink-2">No history yet</p>
          <p className="mt-1 text-body text-ink-3">
            Generations you create will appear here automatically.
          </p>
          <Link
            href="/app/content"
            className="mt-6 inline-flex items-center gap-2 rounded-pill bg-ink text-surface px-5 py-2.5 text-[14px] font-medium hover:translate-y-[-1px] transition"
          >
            Start creating
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((entry) => {
            const meta = TAB_META[entry.tab];
            return (
              <div
                key={entry.id}
                className="card p-5 flex items-start gap-4 group"
              >
                {/* Tab dot */}
                <span className={cn("mt-1 h-[22px] w-[22px] rounded-[7px] shrink-0", meta.color)} />

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[11px] font-semibold tracking-wider text-ink-3">
                      {meta.label}
                    </span>
                    <span className="text-[11px] text-ink-3">·</span>
                    <span className="text-[12px] text-ink-3">{relativeTime(entry.savedAt)}</span>
                  </div>
                  <p className="mt-1 text-[15px] font-medium text-ink truncate">{entry.label}</p>
                  <p className="mt-1 text-[13px] text-ink-2 leading-snug line-clamp-2">
                    {entry.preview}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition shrink-0">
                  <Link
                    href={meta.href}
                    className="inline-flex items-center gap-1 rounded-pill border border-border bg-surface px-3 py-1.5 text-[12px] text-ink-2 hover:text-ink transition"
                  >
                    <ExternalLink size={11} /> Open tab
                  </Link>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="h-8 w-8 rounded-full border border-border bg-surface grid place-items-center text-ink-3 hover:text-coral-deep hover:border-coral/40 transition"
                    aria-label="Delete entry"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
