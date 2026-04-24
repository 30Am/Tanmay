"use client";

import { useState } from "react";
import { ArrowRight, Copy, ExternalLink, Loader2, Plus, RotateCcw, Share2, ThumbsDown, ThumbsUp } from "lucide-react";
import { qa } from "@/lib/api";
import type { Citation, QaResponse } from "@/lib/types";
import { saveToHistory } from "@/lib/history";
import ToolTopBar from "@/components/workspace/ToolTopBar";

export default function QaTab() {
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<QaResponse | null>(null);

  async function run(q: string) {
    if (q.trim().length < 3) return;
    setLoading(true); setErr(null); setOut(null);
    setSubmitted(q);
    try {
      const result = await qa(q);
      setOut(result);
      if (result.status === "answered" && result.answer) {
        saveToHistory({
          tab: "qa",
          label: q.length > 60 ? q.slice(0, 57) + "…" : q,
          input: q,
          preview: result.answer.slice(0, 200),
        });
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function newQuestion() {
    setSubmitted(null); setOut(null); setErr(null); setQuestion("");
  }

  return (
    <>
      <ToolTopBar
        right={
          <>
            <button
              onClick={() => out?.answer && navigator.clipboard.writeText(out.answer)}
              disabled={!out?.answer}
              className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-4 py-2 text-[13px] text-ink-2 hover:text-ink disabled:opacity-40"
            >
              <Share2 size={13} /> Share answer
            </button>
            <button
              onClick={newQuestion}
              className="inline-flex items-center gap-2 rounded-pill bg-ink text-surface px-5 py-2 text-[14px] font-medium hover:translate-y-[-1px] transition"
            >
              <Plus size={13} /> New question
            </button>
          </>
        }
      />

      <div>
        <div className="caption text-[#2e9a7a]">TAB 03 · HOW WOULD TANMAY ANSWER</div>
        <h1 className="mt-3 font-bold tracking-[-0.02em] leading-[1.08] text-[44px] text-ink">
          Ask Tanmay anything.
        </h1>
      </div>

      <div className="mt-8 grid lg:grid-cols-[1fr_384px] gap-5 items-start">
        {/* ───────── LEFT: conversation ───────── */}
        <section className="card p-8 min-h-[640px]">
          {!submitted ? (
            <EmptyAsk
              value={question}
              onChange={setQuestion}
              onSubmit={() => run(question)}
              loading={loading}
            />
          ) : (
            <div className="space-y-6">
              {/* Question bubble */}
              <div className="flex items-start justify-end gap-3">
                <div className="rounded-[22px] bg-coral/25 text-ink px-5 py-3 max-w-[70%] text-[15px] leading-relaxed">
                  {submitted}
                </div>
                <div className="h-10 w-10 rounded-full bg-gradient-sunrise shrink-0" />
              </div>

              {/* Answer block */}
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-full bg-ink text-surface grid place-items-center font-semibold text-[14px] shrink-0">
                  T
                </div>
                <div className="flex-1 min-w-0">
                  {loading ? (
                    <LoadingState />
                  ) : err ? (
                    <div className="rounded-2xl bg-coral/15 border border-coral/40 p-4 text-body text-ink">
                      <strong>Error:</strong> {err}
                    </div>
                  ) : out ? (
                    <AnswerBody resp={out} onRegenerate={() => run(submitted)} />
                  ) : null}
                </div>
              </div>
            </div>
          )}

          {/* Follow-up input (after first question) */}
          {submitted && !loading && (
            <div className="mt-8">
              <div className="flex items-center gap-3 rounded-pill border border-border bg-surface pl-5 pr-1.5 py-1.5">
                <input
                  className="flex-1 bg-transparent outline-none text-[15px] placeholder:text-ink-3 py-2"
                  placeholder="Ask a follow-up…"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") run(question); }}
                />
                <button
                  onClick={() => run(question)}
                  disabled={question.trim().length < 3}
                  className="h-10 w-10 rounded-full bg-ink text-surface grid place-items-center disabled:opacity-40 hover:translate-y-[-1px] transition"
                  aria-label="Send"
                >
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}
        </section>

        {/* ───────── RIGHT: sources ───────── */}
        <aside className="rounded-2xl bg-gradient-sage border border-border p-6 space-y-4 min-h-[640px]">
          <div>
            <div className="caption text-[#2e9a7a]">
              SOURCES{out?.citations?.length ? ` · ${out.citations.length} CHUNKS` : ""}
            </div>
            <h2 className="mt-3 text-[22px] font-semibold text-ink leading-snug">Every claim, traceable.</h2>
            <p className="mt-2 text-[14px] text-ink-2 leading-relaxed">
              Click a source to jump to the exact second in the original clip.
            </p>
          </div>

          <div className="space-y-2.5">
            {out?.citations?.length ? (
              out.citations.map((c, i) => <SourceCard key={c.source_id + i} idx={i + 1} c={c} />)
            ) : (
              <div className="rounded-2xl border border-dashed border-border/60 bg-surface/60 p-5 text-[13px] text-ink-3">
                Source cards will appear here after you ask a question.
              </div>
            )}
          </div>
        </aside>
      </div>
    </>
  );
}

function EmptyAsk({
  value, onChange, onSubmit, loading,
}: { value: string; onChange: (s: string) => void; onSubmit: () => void; loading: boolean }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[540px] text-center px-6">
      <div className="h-14 w-14 rounded-2xl bg-gradient-sage grid place-items-center">
        <span className="text-[22px]">💬</span>
      </div>
      <h2 className="mt-5 text-[28px] font-semibold tracking-tight text-ink">
        What do you want to ask Tanmay?
      </h2>
      <p className="mt-2 text-body text-ink-2 max-w-[480px]">
        Paraphrases are fused with RRF retrieval. Every factual claim in the answer is
        verified against the retrieved chunks before it ships.
      </p>

      <div className="mt-8 w-full max-w-[640px]">
        <div className="flex items-center gap-3 rounded-pill border border-border bg-surface pl-5 pr-1.5 py-1.5">
          <input
            className="flex-1 bg-transparent outline-none text-[16px] placeholder:text-ink-3 py-2.5"
            placeholder="What does Tanmay think about the future of stand-up comedy in India?"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") onSubmit(); }}
          />
          <button
            onClick={onSubmit}
            disabled={loading || value.trim().length < 3}
            className="h-11 w-11 rounded-full bg-ink text-surface grid place-items-center disabled:opacity-40 hover:translate-y-[-1px] transition"
            aria-label="Ask"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
          </button>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-[560px]">
        {[
          "what does Tanmay think about therapy",
          "how does he approach AI doom takes",
          "is he optimistic about Indian stand-up in 2030",
        ].map((s) => (
          <button
            key={s}
            onClick={() => { onChange(s); setTimeout(onSubmit, 0); }}
            className="rounded-pill bg-surface border border-border px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink transition"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="rounded-2xl card-flat p-6">
      <div className="inline-flex items-center gap-2.5 text-[13px] text-ink-2">
        <Loader2 size={14} className="animate-spin text-coral-deep" />
        Paraphrasing · retrieving · grounding · verifying claims…
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-3 rounded-pill bg-border/60 animate-pulse w-[92%]" />
        <div className="h-3 rounded-pill bg-border/60 animate-pulse w-[86%]" />
        <div className="h-3 rounded-pill bg-border/60 animate-pulse w-[74%]" />
      </div>
    </div>
  );
}

function AnswerBody({ resp, onRegenerate }: { resp: QaResponse; onRegenerate: () => void }) {
  if (resp.status === "refused_sensitive") {
    return (
      <div className="rounded-2xl bg-coral/15 border border-coral/40 p-5">
        <div className="font-semibold text-ink">Refused — sensitive topic</div>
        <p className="mt-2 text-body text-ink-2">{resp.reason}</p>
      </div>
    );
  }
  if (resp.status === "refused_low_confidence") {
    return (
      <div className="rounded-2xl bg-butter/60 border border-border p-5">
        <div className="font-semibold text-ink">Tanmay hasn't spoken on this</div>
        <p className="mt-2 text-body text-ink-2">{resp.reason}</p>
      </div>
    );
  }

  const total = resp.n_supported + resp.n_unsupported;
  const confidence =
    resp.max_similarity == null ? null
    : resp.max_similarity > 0.6 ? { label: "High confidence", color: "bg-mint text-[#1f7a4a]" }
    : resp.max_similarity > 0.45 ? { label: "Medium confidence", color: "bg-butter text-[#a26a1a]" }
    : { label: "Low confidence", color: "bg-coral/25 text-coral-deep" };

  return (
    <div>
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-[17px] font-semibold text-ink">Tanmay's take</span>
        {confidence && resp.max_similarity != null && (
          <span className={`inline-flex items-center gap-1.5 rounded-pill px-3 py-1 text-[12px] font-medium ${confidence.color}`}>
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {confidence.label} · {resp.max_similarity.toFixed(2)}
          </span>
        )}
        {resp.citations.length > 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-pill bg-periwinkle/60 px-3 py-1 text-[12px] font-medium text-ink">
            {resp.citations.length} sources
          </span>
        )}
      </div>

      <div className="mt-4 text-[15px] text-ink leading-[1.75] whitespace-pre-wrap">
        {resp.answer}
      </div>

      {/* Verified claims detail */}
      {resp.verified_claims.length > 0 && (
        <details className="mt-5 rounded-xl card-flat p-4">
          <summary className="cursor-pointer text-[12px] font-medium text-ink-2">
            Claim-by-claim verification · {resp.n_supported}/{total} supported
          </summary>
          <ul className="mt-3 space-y-2 text-[13px]">
            {resp.verified_claims.map((c, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className={`mt-1 h-1.5 w-1.5 rounded-full shrink-0 ${c.supported ? "bg-[#1f9d5a]" : "bg-coral-deep"}`} />
                <div className="flex-1 min-w-0">
                  <span className="text-ink">{c.claim}</span>
                  {c.citation_indices.length > 0 && (
                    <span className="ml-2 font-mono text-[11px] text-ink-3">
                      [{c.citation_indices.join(",")}]
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </details>
      )}

      {/* Action row */}
      <div className="mt-5 flex items-center gap-2 flex-wrap">
        <button className="inline-flex items-center gap-1.5 rounded-pill bg-mint/50 hover:bg-mint/80 transition px-3.5 py-1.5 text-[13px] text-ink">
          <ThumbsUp size={13} /> Helpful
        </button>
        <button className="inline-flex items-center gap-1.5 rounded-pill bg-coral/15 hover:bg-coral/25 transition px-3.5 py-1.5 text-[13px] text-ink">
          <ThumbsDown size={13} /> Off voice
        </button>
        <button
          onClick={onRegenerate}
          className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink"
        >
          <RotateCcw size={13} /> Regenerate
        </button>
        <button
          onClick={() => resp.answer && navigator.clipboard.writeText(resp.answer)}
          className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink"
        >
          <Copy size={13} /> Copy with citations
        </button>
      </div>
    </div>
  );
}

function SourceCard({ idx, c }: { idx: number; c: Citation }) {
  const url = buildUrl(c);
  const typeLabel = platformLabel(c.platform);
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className="block rounded-2xl bg-surface border border-border p-4 hover:shadow-card transition group"
    >
      <div className="flex items-start gap-3">
        <span className="h-8 w-8 rounded-lg bg-bg border border-border grid place-items-center text-[12px] font-mono text-ink-2 shrink-0">
          {idx}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[14px] font-medium text-ink truncate">
              {c.title || "(untitled)"}
            </span>
            <span className="shrink-0 text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-md bg-bg border border-border text-ink-3">
              {typeLabel}
            </span>
          </div>
          {c.timestamp_seconds != null && (
            <div className="mt-0.5 text-[12px] font-mono text-ink-3">
              {c.platform === "youtube" ? "YT" : c.platform} · {fmtTs(c.timestamp_seconds)}
            </div>
          )}
          <p className="mt-1.5 text-[13px] text-ink-2 leading-snug line-clamp-2">
            "{c.excerpt}"
          </p>
        </div>
        <ExternalLink size={13} className="text-ink-3 group-hover:text-ink shrink-0 mt-1" />
      </div>
    </a>
  );
}

function buildUrl(c: Citation): string {
  if (c.platform === "youtube" && c.timestamp_seconds != null && c.url.includes("watch?v=")) {
    const sep = c.url.includes("?") ? "&" : "?";
    return `${c.url}${sep}t=${c.timestamp_seconds}s`;
  }
  return c.url;
}

function platformLabel(p: string): string {
  const m: Record<string, string> = {
    youtube: "PODCAST", x: "TWEET", instagram: "REEL", linkedin: "POST", podcast: "PODCAST", event: "STAGE", other: "CLIP",
  };
  return m[p] ?? "CLIP";
}

function fmtTs(s: number): string {
  const m = Math.floor(s / 60);
  const ss = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}
