"use client";

import { useEffect } from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

export default function WorkspaceError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to console in dev; swap for a proper error reporter in prod
    console.error("[workspace error]", error);
  }, [error]);

  const isBrandSafety = error.message?.toLowerCase().includes("brand_safety");
  const isRateLimit = error.message?.toLowerCase().includes("rate_limit") ||
    error.message?.toLowerCase().includes("429");

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-6">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-coral/15 border border-coral/30">
          <AlertTriangle size={24} className="text-coral-deep" />
        </div>

        <h2 className="text-[22px] font-semibold tracking-tight text-ink">
          {isRateLimit
            ? "Slow down a bit"
            : isBrandSafety
            ? "Category not supported"
            : "Something went wrong"}
        </h2>

        <p className="mt-2 text-[14px] text-ink-2 leading-relaxed">
          {isRateLimit
            ? "You've hit the request limit. Wait a moment and try again."
            : isBrandSafety
            ? "This product category falls outside what Tanmay endorses publicly."
            : error.message || "An unexpected error occurred. Try again or reload the page."}
        </p>

        {error.digest && (
          <p className="mt-2 font-mono text-[11px] text-ink-3">ref: {error.digest}</p>
        )}

        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-pill bg-ink text-surface px-5 py-2.5 text-[14px] font-medium hover:translate-y-[-1px] transition"
          >
            <RotateCcw size={14} /> Try again
          </button>
          <a
            href="/app"
            className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-5 py-2.5 text-[14px] text-ink-2 hover:text-ink transition"
          >
            Back to dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
