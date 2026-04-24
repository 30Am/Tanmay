"use client";

import { useState } from "react";
import { Copy, Loader2, RotateCcw, Sparkles } from "lucide-react";
import { generateContentStream } from "@/lib/api";
import type { ContentGenerateRequest, ContentGenerateResponse, ToneDial as ToneDialT } from "@/lib/types";
import { saveToHistory } from "@/lib/history";
import ToneDial from "@/components/workspace/ToneDial";
import ToolTopBar from "@/components/workspace/ToolTopBar";

type Format = ContentGenerateRequest["format"];
const FORMATS: { value: Format; label: string }[] = [
  { value: "reel",          label: "Instagram Reel" },
  { value: "youtube_short", label: "YouTube Short" },
  { value: "talking_head",  label: "Talking Head" },
  { value: "reaction",      label: "Reaction video" },
  { value: "long_podcast",  label: "Podcast cold-open" },
  { value: "thread",        label: "Twitter / X thread" },
  { value: "stage",         label: "Stage bit" },
  { value: "monologue",     label: "Stand-up monologue" },
  { value: "explainer",     label: "Explainer" },
  { value: "interview",     label: "Interview / conversation" },
];

const LENGTHS = [30, 45, 60, 90, 120, 180, 300, 600];

const DEFAULT_TONE: ToneDialT = { roast_level: 0.62, chaos: 0.4, depth: 0.78, hinglish_ratio: 0.55 };

type Language = "hinglish" | "english" | "hindi";

export default function ContentTab() {
  const [idea, setIdea] = useState("");
  const [format, setFormat] = useState<Format>("reel");
  const [length, setLength] = useState(90);
  const [language, setLanguage] = useState<Language>("hinglish");
  const [tone, setTone] = useState<ToneDialT>(DEFAULT_TONE);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<ContentGenerateResponse | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setOut(null);
    setStreamingText("");
    try {
      for await (const event of generateContentStream({ idea, format, target_length_seconds: length, tone, language })) {
        if (event.type === "token") {
          setStreamingText((prev) => prev + event.text);
        } else {
          const result = { script: event.script, description: event.description, rationale: event.rationale, citations: event.citations };
          setOut(result);
          setStreamingText("");
          setSavedAt(new Date());
          if (result.script) {
            saveToHistory({
              tab: "content",
              label: idea.length > 60 ? idea.slice(0, 57) + "…" : idea,
              input: idea,
              preview: result.script.slice(0, 200),
            });
          }
        }
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || idea.trim().length < 3;

  return (
    <>
      <ToolTopBar
        right={
          <>
            <span className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-4 py-2 text-[13px] text-ink-2">
              {savedAt
                ? <>Draft saved · {formatAgo(savedAt)}</>
                : <>Not saved yet</>}
            </span>
            <button
              onClick={() => out && navigator.clipboard.writeText(buildExportText(out))}
              disabled={!out}
              className="inline-flex items-center gap-2 rounded-pill bg-ink text-surface px-5 py-2 text-[14px] font-medium disabled:opacity-40 hover:translate-y-[-1px] transition"
            >
              Export
            </button>
          </>
        }
      />

      <div>
        <div className="caption text-coral-deep">TAB 01 · CONTENT GENERATION</div>
        <h1 className="mt-3 font-bold tracking-[-0.02em] leading-[1.08] text-[44px] text-ink">
          Generate a script.
        </h1>
      </div>

      <div className="mt-8 grid lg:grid-cols-[480px_1fr] gap-5 items-start">
        {/* ───────── LEFT: YOUR INPUT ───────── */}
        <aside className="card p-7 space-y-6">
          <div className="caption text-ink-3">YOUR INPUT</div>

          <div>
            <label className="field-label">Content idea</label>
            <textarea
              className="textarea-field min-h-[150px]"
              placeholder="A reaction video to the recent UPSC topper interview. Start with a callback to last week's 'productivity gurus' rant, slowly build to why rote memorisation isn't the enemy, end on a soft Hinglish punchline."
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Format</label>
              <select
                className="select-field"
                value={format}
                onChange={(e) => setFormat(e.target.value as Format)}
              >
                {FORMATS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label">Length</label>
              <select
                className="select-field"
                value={length}
                onChange={(e) => setLength(parseInt(e.target.value))}
              >
                {LENGTHS.map((s) => (
                  <option key={s} value={s}>{s < 60 ? `${s} seconds` : `${s / 60} min`}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="field-label">Language</label>
            <div className="grid grid-cols-3 gap-2">
              {(["hinglish", "english", "hindi"] as Language[]).map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => setLanguage(lang)}
                  className={`rounded-pill py-2.5 text-[13px] font-medium capitalize border transition
                    ${language === lang
                      ? "bg-ink text-surface border-ink"
                      : "bg-surface text-ink-2 border-border hover:border-ink-2 hover:text-ink"
                    }`}
                >
                  {lang === "hinglish" ? "Hinglish" : lang === "english" ? "English" : "Hindi"}
                </button>
              ))}
            </div>
          </div>

          <ToneDial value={tone} onChange={setTone} onReset={() => setTone(DEFAULT_TONE)} />

          <button
            onClick={run}
            disabled={disabled}
            className="relative w-full rounded-pill py-4 font-semibold text-ink bg-gradient-sunrise shadow-card transition hover:translate-y-[-1px] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" />Generating…</>
            ) : (
              <><Sparkles size={16} />Generate script</>
            )}
          </button>

          {err && (
            <div className="rounded-2xl bg-coral/15 border border-coral/40 p-4 text-[14px] text-ink">
              <strong>Error:</strong> {err}
            </div>
          )}
        </aside>

        {/* ───────── RIGHT: OUTPUT ───────── */}
        <section className="space-y-5">
          <div className="card p-8 min-h-[520px]">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <span className="caption text-ink-3">SCRIPT</span>
                {loading && (
                  <span className="inline-flex items-center gap-2 rounded-pill bg-mint/70 px-3 py-1 text-[12px] font-medium text-ink">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#16a34a] animate-pulse" />
                    Streaming
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => out && navigator.clipboard.writeText(out.script)}
                  disabled={!out}
                  className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink disabled:opacity-40"
                >
                  <Copy size={13} /> Copy
                </button>
                <button
                  onClick={run}
                  disabled={disabled}
                  className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink disabled:opacity-40"
                >
                  <RotateCcw size={13} /> Regenerate
                </button>
              </div>
            </div>

            <div className="mt-5 text-[16px] leading-[1.7] text-ink whitespace-pre-wrap">
              {out?.script ? (
                out.script
              ) : streamingText ? (
                streamingText
              ) : loading ? (
                <span className="text-ink-3">Retrieving context, first tokens incoming…</span>
              ) : (
                <span className="text-ink-3">
                  Drop an idea on the left and hit <span className="text-ink">Generate</span>.
                  Your Tanmay-voice script will stream in here with clickable citations.
                </span>
              )}
            </div>
          </div>

          <div className="grid md:grid-cols-[1fr_1fr] gap-5">
            {/* WHY THIS WORKS card — pink-blossom gradient */}
            <div className="rounded-2xl bg-gradient-blossom p-7 min-h-[260px] border border-border">
              <div className="caption text-coral-deep">WHY THIS WORKS</div>
              {out?.rationale ? (
                <>
                  <h3 className="mt-4 text-[20px] font-semibold text-ink leading-snug">
                    Three techniques you just used:
                  </h3>
                  <div className="mt-5 text-body text-ink-2 leading-relaxed whitespace-pre-wrap">
                    {out.rationale}
                  </div>
                </>
              ) : (
                <p className="mt-4 text-body text-ink-2 leading-relaxed">
                  After you generate, the rhetorical moves Tanmay leans on for this topic
                  will land here — callbacks, pattern interrupts, soft Hinglish landings.
                </p>
              )}
            </div>

            {/* CITATIONS */}
            <div className="card p-6 min-h-[260px]">
              <div className="caption text-ink-3">
                SOURCE CITATIONS · {out?.citations?.length ?? 0}
              </div>
              {out && out.citations.length > 0 ? (
                <ul className="mt-4 space-y-2.5">
                  {out.citations.slice(0, 4).map((c, i) => (
                    <li key={c.source_id + i}>
                      <a
                        href={buildTimestampedUrl(c.url, c.platform, c.timestamp_seconds)}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-start gap-3 rounded-xl hover:bg-bg transition px-2 py-2 -mx-2"
                      >
                        <span className="h-8 w-8 rounded-lg bg-coral/25 grid place-items-center text-[11px] font-mono text-ink shrink-0">
                          {i + 1}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="block text-[14px] font-medium text-ink truncate">
                            {(c.title || "untitled")}{" "}
                            {c.timestamp_seconds != null && (
                              <span className="font-mono text-[12px] text-ink-3">· {fmtTs(c.timestamp_seconds)}</span>
                            )}
                          </span>
                          <span className="block mt-0.5 text-[13px] text-ink-2 line-clamp-1">
                            {c.excerpt}
                          </span>
                        </span>
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-body text-ink-2">
                  Citations will appear here with timestamped deep-links so you can verify
                  every line against the archive in one click.
                </p>
              )}
            </div>
          </div>
        </section>
      </div>
    </>
  );
}

/* helpers */
function buildExportText(r: ContentGenerateResponse): string {
  return `SCRIPT\n\n${r.script}\n\nDESCRIPTION\n\n${r.description}\n\nRATIONALE\n\n${r.rationale}`;
}

function buildTimestampedUrl(url: string, platform: string, ts?: number | null): string {
  if (platform === "youtube" && ts != null && url.includes("watch?v=")) {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}t=${ts}s`;
  }
  return url;
}

function fmtTs(s: number): string {
  const m = Math.floor(s / 60);
  const ss = Math.floor(s % 60);
  return `${m}:${String(ss).padStart(2, "0")}`;
}

function formatAgo(d: Date): string {
  const ms = Date.now() - d.getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}
