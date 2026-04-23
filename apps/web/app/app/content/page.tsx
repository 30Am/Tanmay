"use client";

import { useState } from "react";
import { Copy, Loader2, Sparkles } from "lucide-react";
import { generateContent } from "@/lib/api";
import type { ContentGenerateRequest, ContentGenerateResponse, ToneDial as ToneDialT } from "@/lib/types";
import ToneDial from "@/components/workspace/ToneDial";
import CitationCard from "@/components/workspace/CitationCard";
import ToolHeader from "@/components/workspace/ToolHeader";

type Format = ContentGenerateRequest["format"];
const FORMATS: { value: Format; label: string }[] = [
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
    setLoading(true); setErr(null); setOut(null);
    try {
      const res = await generateContent({ idea, format, target_length_seconds: length, tone });
      setOut(res);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || idea.trim().length < 3;

  return (
    <div className="max-w-[1100px]">
      <ToolHeader
        eyebrow="TAB 01"
        title="Content Generation"
        subtitle="Feed an idea, dial the tone, get a Tanmay-voiced draft with citations."
        chipClass="chip-content"
      />

      <div className="grid lg:grid-cols-[1fr_340px] gap-6">
        <div className="card p-8 space-y-6">
          <div>
            <label className="field-label">Your idea</label>
            <textarea
              className="textarea-field"
              placeholder="e.g. Why I quit journaling after six years. Dry tone, soft punchline."
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
            />
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="field-label">Format</label>
              <select className="select-field" value={format} onChange={(e) => setFormat(e.target.value as Format)}>
                {FORMATS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label">Length: <span className="text-ink font-semibold">{length}s</span></label>
              <input
                type="range"
                min={15}
                max={600}
                step={15}
                value={length}
                onChange={(e) => setLength(parseInt(e.target.value))}
                className="w-full accent-coral-deep mt-3"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button onClick={run} disabled={disabled} className="btn-primary">
              {loading
                ? <><Loader2 size={16} className="mr-2 animate-spin" />Generating…</>
                : <><Sparkles size={16} className="mr-2" />Generate</>}
            </button>
            {out && (
              <button
                onClick={() => navigator.clipboard.writeText(`SCRIPT\n\n${out.script}\n\nDESCRIPTION\n\n${out.description}\n\nRATIONALE\n\n${out.rationale}`)}
                className="btn-ghost"
              >
                <Copy size={15} className="mr-2" />Copy all
              </button>
            )}
          </div>
        </div>

        <aside className="card p-6">
          <div className="caption text-coral-deep">TONE DIAL</div>
          <div className="mt-5">
            <ToneDial value={tone} onChange={setTone} />
          </div>
        </aside>
      </div>

      {err && (
        <div className="mt-6 rounded-2xl bg-coral/15 border border-coral/40 p-5 text-body text-ink">
          <strong>Error:</strong> {err}
        </div>
      )}

      {out && (
        <div className="mt-8 space-y-6">
          <OutputSection title="SCRIPT" body={out.script} emphasis />
          {out.description && <OutputSection title="DESCRIPTION" body={out.description} />}
          {out.rationale && <OutputSection title="RATIONALE" body={out.rationale} />}
          {out.citations.length > 0 && (
            <div>
              <div className="caption text-coral-deep mb-3">
                CITATIONS · {out.citations.length}
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                {out.citations.map((c, i) => <CitationCard key={c.source_id + i} idx={i + 1} c={c} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function OutputSection({ title, body, emphasis }: { title: string; body: string; emphasis?: boolean }) {
  return (
    <div>
      <div className="caption text-coral-deep mb-3">{title}</div>
      <div className={`card-flat p-6 whitespace-pre-wrap leading-relaxed ${emphasis ? "text-body-l text-ink" : "text-body text-ink-2"}`}>
        {body}
      </div>
    </div>
  );
}
