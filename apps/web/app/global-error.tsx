"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("[global error]", error);
  }, [error]);

  return (
    <html>
      <body className="min-h-screen bg-[#0f0f0f] flex items-center justify-center text-white font-sans">
        <div className="text-center px-6 max-w-md">
          <div className="text-[40px] mb-4">⚠️</div>
          <h1 className="text-[24px] font-bold mb-2">TanmayGPT crashed</h1>
          <p className="text-[14px] text-white/60 mb-6">
            {error.message || "A critical error occurred. Our team has been notified."}
          </p>
          {error.digest && (
            <p className="mb-4 font-mono text-[11px] text-white/30">ref: {error.digest}</p>
          )}
          <button
            onClick={reset}
            className="rounded-full bg-white text-black px-6 py-2.5 text-[14px] font-medium hover:bg-white/90 transition"
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
