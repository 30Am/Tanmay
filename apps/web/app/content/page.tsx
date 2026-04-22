"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Citations } from "@/components/ui/Citations";
import { Label, Select, Slider, Textarea, Input } from "@/components/ui/Field";
import { streamContent } from "@/lib/api";
import type { Citation, ContentGenerateRequest } from "@/lib/types";

export default function ContentPage() {
  const [idea, setIdea] = useState("");
  const [format, setFormat] = useState<ContentGenerateRequest["format"]>("reel");
  const [length, setLength] = useState(60);
  const [roast, setRoast] = useState(0.5);
  const [chaos, setChaos] = useState(0.5);
  const [depth, setDepth] = useState(0.5);
  const [hinglish, setHinglish] = useState(0.6);

  const [output, setOutput] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!idea.trim()) return;
    setOutput("");
    setCitations([]);
    setError(null);
    setBusy(true);
    await streamContent(
      {
        idea,
        format,
        target_length_seconds: length,
        tone: { roast_level: roast, chaos, depth, hinglish_ratio: hinglish },
      },
      {
        onCitations: setCitations,
        onToken: (t) => setOutput((prev) => prev + t),
        onDone: () => setBusy(false),
        onError: (e) => {
          setError(e.message);
          setBusy(false);
        },
      },
    );
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
      <div className="space-y-5">
        <div>
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Tab 01</div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Content Generation</h1>
          <p className="mt-1 text-sm text-muted">Idea in, script + description out.</p>
        </div>
        <div>
          <Label htmlFor="idea">Idea</Label>
          <Textarea
            id="idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="e.g. Why YouTube Shorts feels designed to ruin your mood"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="format">Format</Label>
            <Select id="format" value={format} onChange={(e) => setFormat(e.target.value as ContentGenerateRequest["format"])}>
              <option value="reel">Reel</option>
              <option value="long_podcast">Long podcast</option>
              <option value="thread">Thread</option>
              <option value="stage">Stage</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="length">Length (sec)</Label>
            <Input
              id="length"
              type="number"
              min={15}
              max={3600}
              value={length}
              onChange={(e) => setLength(parseInt(e.target.value, 10) || 60)}
            />
          </div>
        </div>
        <div className="space-y-3 rounded-lg border border-border bg-panel p-4">
          <div className="text-xs uppercase tracking-[0.15em] text-accentPurple">Tone dial</div>
          <Slider value={roast} onChange={setRoast} label="Roast" />
          <Slider value={chaos} onChange={setChaos} label="Chaos" />
          <Slider value={depth} onChange={setDepth} label="Depth" />
          <Slider value={hinglish} onChange={setHinglish} label="Hinglish" />
        </div>
        <Button onClick={handleGenerate} disabled={busy || !idea.trim()}>
          {busy ? "Generating…" : "Generate"}
        </Button>
        {error && <div className="text-sm text-red-400">{error}</div>}
      </div>

      <div>
        <div className="min-h-[420px] whitespace-pre-wrap rounded-xl border border-border bg-panel p-6 font-mono text-sm leading-relaxed">
          {output || <span className="text-muted">Output will stream here…</span>}
        </div>
        <Citations citations={citations} />
      </div>
    </div>
  );
}
