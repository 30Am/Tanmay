"use client";

import { useState } from "react";
import { Copy, Sparkles, Loader2 } from "lucide-react";
import { generateContent } from "@/lib/api";
import type {
  ContentGenerateRequest,
  ContentGenerateResponse,
  ToneDial as ToneDialT,
} from "@/lib/types";
import ToneDial from "@/components/workspace/ToneDial";
import CitationCard from "@/components/workspace/CitationCard";
import Reveal from "@/components/motion/Reveal";

type Format = ContentGenerateRequest["format"];
const FORMAT_OPTIONS: { value: Format; label: string }[] = [
  { value: "reel", label: "Reel / short" },
  { value: "thread", label: "Twitter / X thread" },
  { value: "long_podcast", label: "Podcast cold-open" },
  { value: "stage", label: "Stage bit" },
];

const DEFAULT_TONE: ToneDialT = { roast_level: 0.5, chaos: 0.5, depth: 0.5, hinglish_ratio: 0.5 };

export default function ContentTab() {
  const [idea, setIdea] = useState("");
  const [format, setFormat] = useState<Format>("reel");
  const [length, setLength] = useState(60);
  const [tone, setTone] = useState<ToneDialT>(DEFAULT_TONE);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<ContentGenerateResponse | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setOut(null);
    try {
      const res = await generateContent({
        idea,
        format,
        target_length_seconds: length,
        tone,
      });
      setOut(res);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function copyAll() {
    if (!out) return;
    navigator.clipboard.writeText(
      `SCRIPT\n\n${out.script}\n\nDESCRIPTION\n\n${out.description}\n\nRATIONALE\n\n${out.rationale}`,
    );
  }

  const disabled = loading || idea.trim().length < 3;

  return (
    <div className="p-6 md:p-8 space-y-6">
      <header className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-serif text-2xl">Content Generation</h2>
          <p className="text-sm text-inkMuted">Drop an idea, get a cited draft in his voice.</p>
        </div>
        <span className="pill"><span className="pill-dot bg-salmon" />TOOL 01</span>
      </header>

      <div className="grid lg:grid-cols-[1fr_280px] gap-5">
        <div className="space-y-4">
          <div>
            <label className="label">Your idea</label>
            <textarea
              className="textarea"
              placeholder="e.g. Why I quit journaling after six years. Dry tone, soft punchline."
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Format</label>
              <select
                className="select"
                value={format}
                onChange={(e) => setFormat(e.target.value as Format)}
              >
                {FORMAT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Length (sec): <span className="text-ink font-semibold">{length}</span></label>
              <input
                type="range"
                min={15}
                max={600}
                step={15}
                value={length}
                onChange={(e) => setLength(parseInt(e.target.value))}
                className="w-full accent-pinkDeep"
              />
              <div className="flex justify-between text-[10px] text-inkSubtle mt-1">
                <span>15s</span><span>10m</span>
              </div>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-canvas/50 p-4">
          <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-3">TONE DIAL</div>
          <ToneDial value={tone} onChange={setTone} />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={run} disabled={disabled} className="btn-gradient">
          <span>{loading ? (<><Loader2 size={14} className="mr-2 animate-spin" />Generating…</>) : (<><Sparkles size={14} className="mr-2" />Generate draft</>)}</span>
        </button>
        {out && (
          <button onClick={copyAll} className="btn-ghost">
            <Copy size={14} />Copy all
          </button>
        )}
      </div>

      {err && (
        <div className="rounded-xl border border-refuseRose bg-refuseRose/30 p-4 text-sm text-ink">
          <strong>Error:</strong> {err}
        </div>
      )}

      {out && (
        <div key={out.script.slice(0, 32)} className="space-y-5 pt-2">
          <Reveal><Section title="SCRIPT" body={out.script} mono={false} emphasis /></Reveal>
          {out.description && <Reveal delay={1}><Section title="DESCRIPTION" body={out.description} /></Reveal>}
          {out.rationale && <Reveal delay={2}><Section title="RATIONALE" body={out.rationale} /></Reveal>}
          {out.citations.length > 0 && (
            <Reveal delay={3}>
              <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-2">
                CITATIONS ({out.citations.length})
              </div>
              <div className="grid sm:grid-cols-2 gap-2.5">
                {out.citations.map((c, i) => (
                  <CitationCard key={c.source_id + i} idx={i + 1} c={c} />
                ))}
              </div>
            </Reveal>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ title, body, mono = false, emphasis = false }: { title: string; body: string; mono?: boolean; emphasis?: boolean }) {
  return (
    <div>
      <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-2">{title}</div>
      <div
        className={`rounded-2xl border border-line bg-white p-5 whitespace-pre-wrap leading-relaxed ${
          mono ? "font-mono text-[13px]" : ""
        } ${emphasis ? "text-[15px]" : "text-[14px] text-inkMuted"}`}
      >
        {body}
      </div>
    </div>
  );
}
