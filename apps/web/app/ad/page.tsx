"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Citations } from "@/components/ui/Citations";
import { Input, Label, Select, Textarea } from "@/components/ui/Field";
import { generateAd } from "@/lib/api";
import type { AdGenerateRequest, AdGenerateResponse } from "@/lib/types";

export default function AdPage() {
  const [req, setReq] = useState<AdGenerateRequest>({
    product_name: "",
    product_description: "",
    target_audience: "",
    duration_seconds: 45,
    language: "hinglish",
    cast: [],
    celebrities: [],
    notes: "",
  });
  const [celebsText, setCelebsText] = useState("");
  const [castText, setCastText] = useState("");
  const [output, setOutput] = useState<AdGenerateResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setBusy(true);
    setError(null);
    try {
      const celebrities = celebsText.split(",").map((s) => s.trim()).filter(Boolean);
      const cast = castText
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .map((name) => ({ name }));
      const payload: AdGenerateRequest = { ...req, celebrities, cast };
      const result = await generateAd(payload);
      setOutput(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
      <div className="space-y-4">
        <div>
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Tab 02</div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight">Ad Generation</h1>
          <p className="mt-1 text-sm text-muted">Structured brief in, scene-by-scene script out.</p>
        </div>
        <div>
          <Label>Product name</Label>
          <Input
            value={req.product_name}
            onChange={(e) => setReq({ ...req, product_name: e.target.value })}
            placeholder="e.g. Rage Coffee"
          />
        </div>
        <div>
          <Label>Product description</Label>
          <Textarea
            value={req.product_description}
            onChange={(e) => setReq({ ...req, product_description: e.target.value })}
            placeholder="What it is, what makes it different."
          />
        </div>
        <div>
          <Label>Target audience</Label>
          <Input
            value={req.target_audience ?? ""}
            onChange={(e) => setReq({ ...req, target_audience: e.target.value })}
            placeholder="e.g. urban 22-35 coffee-first millennials"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Duration (sec)</Label>
            <Input
              type="number"
              min={10}
              max={180}
              value={req.duration_seconds}
              onChange={(e) => setReq({ ...req, duration_seconds: parseInt(e.target.value, 10) || 30 })}
            />
          </div>
          <div>
            <Label>Language</Label>
            <Select
              value={req.language}
              onChange={(e) => setReq({ ...req, language: e.target.value as AdGenerateRequest["language"] })}
            >
              <option value="hinglish">Hinglish</option>
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
            </Select>
          </div>
        </div>
        <div>
          <Label>Cast (comma separated)</Label>
          <Input value={castText} onChange={(e) => setCastText(e.target.value)} placeholder="Tanmay, friend, barista" />
        </div>
        <div>
          <Label>Celebrity cameos (comma separated)</Label>
          <Input value={celebsText} onChange={(e) => setCelebsText(e.target.value)} placeholder="optional" />
        </div>
        <div>
          <Label>Notes</Label>
          <Textarea
            value={req.notes ?? ""}
            onChange={(e) => setReq({ ...req, notes: e.target.value })}
            placeholder="Anything specific to include or avoid."
          />
        </div>
        <Button onClick={handleGenerate} disabled={busy || !req.product_name || !req.product_description}>
          {busy ? "Generating…" : "Generate ad"}
        </Button>
        {error && <div className="text-sm text-red-400">{error}</div>}
      </div>

      <div>
        {output ? (
          <div className="space-y-5">
            {output.brand_safety_flags.length > 0 && (
              <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm">
                <div className="mb-1 font-semibold text-red-300">Brand safety flags</div>
                <ul className="list-disc pl-5 text-red-200">
                  {output.brand_safety_flags.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="rounded-xl border border-border bg-panel p-6">
              <div className="text-xs uppercase tracking-[0.15em] text-accentGreen">Title</div>
              <div className="mt-1 text-xl font-bold">{output.title}</div>
              <div className="mt-4 text-xs uppercase tracking-[0.15em] text-accentGreen">Hook</div>
              <div className="mt-1 text-sm">{output.hook}</div>
            </div>

            <div className="rounded-xl border border-border bg-panel p-6">
              <div className="mb-3 text-xs uppercase tracking-[0.15em] text-accentGreen">Scenes</div>
              <div className="space-y-5">
                {output.scenes.map((s) => (
                  <div key={s.scene_number} className="border-l-2 border-accent pl-4">
                    <div className="text-sm font-semibold">
                      Scene {s.scene_number} · {s.duration_seconds}s · {s.setting}
                    </div>
                    <div className="mt-1 text-xs text-muted">{s.direction}</div>
                    <div className="mt-2 text-xs text-accentPurple">{s.characters.join(", ")}</div>
                    <ul className="mt-2 space-y-1 text-sm">
                      {s.lines.map((l, i) => (
                        <li key={i} className="font-mono">
                          {l}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-panel p-6">
              <div className="text-xs uppercase tracking-[0.15em] text-accentGreen">CTA</div>
              <div className="mt-1 text-sm">{output.cta}</div>
              <div className="mt-4 text-xs uppercase tracking-[0.15em] text-accentGreen">Strategy rationale</div>
              <div className="mt-1 text-sm whitespace-pre-wrap text-muted">{output.strategy_rationale}</div>
            </div>

            <Citations citations={output.citations} />
          </div>
        ) : (
          <div className="flex min-h-[420px] items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted">
            Your generated ad script will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
