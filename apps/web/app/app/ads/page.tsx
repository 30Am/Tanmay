"use client";

import { useState } from "react";
import { AlertTriangle, Copy, Download, Loader2, Shield, Sparkles } from "lucide-react";
import { exportAd, generateAd } from "@/lib/api";
import type { AdGenerateRequest, AdGenerateResponse, AdValidation } from "@/lib/types";
import CitationCard from "@/components/workspace/CitationCard";
import ToolHeader from "@/components/workspace/ToolHeader";

const DEFAULT_REQ: AdGenerateRequest = {
  product_name: "",
  product_description: "",
  target_audience: "",
  duration_seconds: 30,
  language: "hinglish",
  cast: [],
  celebrities: [],
  notes: "",
};

export default function AdsTab() {
  const [req, setReq] = useState<AdGenerateRequest>(DEFAULT_REQ);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<{ message: string; detail?: unknown } | null>(null);
  const [out, setOut] = useState<{ data: AdGenerateResponse; validation: AdValidation } | null>(null);
  const [exportBusy, setExportBusy] = useState<null | "md" | "fountain">(null);

  async function run() {
    setLoading(true); setErr(null); setOut(null);
    try {
      setOut(await generateAd(req));
    } catch (e) {
      const error = e as Error & { detail?: unknown };
      setErr({ message: error.message, detail: error.detail });
    } finally {
      setLoading(false);
    }
  }

  async function download(format: "md" | "fountain") {
    setExportBusy(format);
    try {
      const body = await exportAd(req, format);
      const blob = new Blob([body], { type: format === "md" ? "text/markdown" : "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${req.product_name.replace(/\s+/g, "_") || "ad"}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally { setExportBusy(null); }
  }

  const disabled = loading || req.product_name.trim().length < 2 || req.product_description.trim().length < 3;
  const refused = err?.detail && typeof err.detail === "object" && err.detail !== null
    && (err.detail as Record<string, unknown>).error === "refused_brand_safety";

  return (
    <div className="max-w-[1100px]">
      <ToolHeader
        eyebrow="TAB 02"
        title="Ad Generation"
        subtitle="Structured brief → scene-by-scene ad. Brand-safety gate + duration validator baked in."
        chipClass="chip-ads"
      />

      <div className="card p-8 space-y-5">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="field-label">Product name</label>
            <input className="field" value={req.product_name} placeholder="e.g. Cred Max"
              onChange={(e) => setReq((r) => ({ ...r, product_name: e.target.value }))} />
          </div>
          <div>
            <label className="field-label">Target audience</label>
            <input className="field" value={req.target_audience ?? ""} placeholder="Gen Z college students in India"
              onChange={(e) => setReq((r) => ({ ...r, target_audience: e.target.value }))} />
          </div>
        </div>
        <div>
          <label className="field-label">Description</label>
          <textarea className="textarea-field" value={req.product_description} placeholder="Say it like you mean it — what makes this product real"
            onChange={(e) => setReq((r) => ({ ...r, product_description: e.target.value }))} />
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="field-label">Duration: <span className="font-semibold text-ink">{req.duration_seconds}s</span></label>
            <input type="range" min={10} max={180} step={5} value={req.duration_seconds}
              onChange={(e) => setReq((r) => ({ ...r, duration_seconds: parseInt(e.target.value) }))}
              className="w-full accent-coral-deep mt-3" />
          </div>
          <div>
            <label className="field-label">Language</label>
            <select className="select-field" value={req.language}
              onChange={(e) => setReq((r) => ({ ...r, language: e.target.value as AdGenerateRequest["language"] }))}>
              <option value="hinglish">Hinglish</option>
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
            </select>
          </div>
          <div>
            <label className="field-label">Notes</label>
            <input className="field" value={req.notes ?? ""} placeholder="fun not preachy; demystify investing"
              onChange={(e) => setReq((r) => ({ ...r, notes: e.target.value }))} />
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap pt-2">
          <button onClick={run} disabled={disabled} className="btn-primary">
            {loading
              ? <><Loader2 size={16} className="mr-2 animate-spin" />Generating…</>
              : <><Sparkles size={16} className="mr-2" />Generate ad</>}
          </button>
          {out && (
            <>
              <button onClick={() => download("md")} disabled={!!exportBusy} className="btn-outline">
                <Download size={14} className="mr-2" />{exportBusy === "md" ? "…" : "Markdown"}
              </button>
              <button onClick={() => download("fountain")} disabled={!!exportBusy} className="btn-outline">
                <Download size={14} className="mr-2" />{exportBusy === "fountain" ? "…" : "Fountain"}
              </button>
              <button onClick={() => navigator.clipboard.writeText(JSON.stringify(out.data, null, 2))} className="btn-ghost">
                <Copy size={14} className="mr-2" />JSON
              </button>
            </>
          )}
        </div>
      </div>

      {err && (
        <div className={`mt-6 rounded-2xl p-5 text-body ${refused ? "bg-coral/15 border border-coral/40" : "bg-butter border border-border"}`}>
          <div className="flex items-center gap-2 font-semibold text-ink">
            <Shield size={16} />
            {refused ? "Refused by brand-safety gate" : "Error"}
          </div>
          <div className="mt-1.5 text-ink-2">
            {refused ? (err.detail as { reason?: string }).reason : err.message}
          </div>
        </div>
      )}

      {out && (
        <div className="mt-10 space-y-6">
          <div className="flex items-center gap-2 flex-wrap">
            <ValidationBadge v={out.validation} />
            {out.data.brand_safety_flags.map((f) => (
              <span key={f} className="chip bg-butter text-ink">
                <AlertTriangle size={12} />{f}
              </span>
            ))}
          </div>

          <div className="card-flat p-7">
            <h2 className="font-bold tracking-[-0.015em] text-[30px] text-ink">{out.data.title}</h2>
            <div className="mt-1 font-mono text-[12px] text-ink-3">
              {out.data.scenes.length} scenes · {out.validation.duration_seconds}s · {out.validation.words} words
            </div>
            {out.data.hook && (
              <div className="mt-5 rounded-2xl bg-gradient-sunrise p-5 text-body-l text-ink italic leading-relaxed">
                <span className="not-italic caption text-coral-deep block mb-2">HOOK</span>
                "{out.data.hook}"
              </div>
            )}
          </div>

          <div className="space-y-3">
            {out.data.scenes.map((s) => (
              <div key={s.scene_number} className="card-flat p-6">
                <div className="flex items-center justify-between mb-4 text-[12px] font-mono text-ink-3">
                  <span>SCENE {s.scene_number}</span>
                  <span>{s.duration_seconds}s</span>
                </div>
                <div className="text-[13px] text-ink-2">
                  <span className="font-semibold text-ink">Setting:</span> {s.setting}
                </div>
                <div className="mt-1 text-[13px] text-ink-2">
                  <span className="font-semibold text-ink">Direction:</span> {s.direction}
                </div>
                {s.characters.length > 0 && (
                  <div className="mt-1 text-[13px] text-ink-2">
                    <span className="font-semibold text-ink">Cast:</span> {s.characters.join(", ")}
                  </div>
                )}
                <div className="mt-4 space-y-2">
                  {s.lines.map((line, i) => (
                    <blockquote key={i} className="border-l-2 border-coral pl-4 text-body-l text-ink leading-relaxed">
                      {line}
                    </blockquote>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {out.data.cta && (
            <div className="card-flat bg-gradient-blossom p-6">
              <div className="caption text-coral-deep mb-2">CTA</div>
              <div className="text-body-l text-ink font-medium">{out.data.cta}</div>
            </div>
          )}

          {out.data.strategy_rationale && (
            <div>
              <div className="caption text-coral-deep mb-3">STRATEGY RATIONALE</div>
              <div className="card-flat p-6 text-body text-ink-2 leading-relaxed">{out.data.strategy_rationale}</div>
            </div>
          )}

          {out.data.citations.length > 0 && (
            <div>
              <div className="caption text-coral-deep mb-3">CITATIONS · {out.data.citations.length}</div>
              <div className="grid sm:grid-cols-2 gap-3">
                {out.data.citations.map((c, i) => <CitationCard key={c.source_id + i} idx={i + 1} c={c} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ValidationBadge({ v }: { v: AdValidation }) {
  if (v.valid) {
    return (
      <span className="chip bg-mint text-ink">
        <span className="h-1.5 w-1.5 rounded-full bg-green-600" />
        VALIDATED · {v.duration_seconds}s
      </span>
    );
  }
  return (
    <span className="chip bg-butter text-ink">
      <AlertTriangle size={12} />
      {v.issues.join(" · ") || "validation warning"}
    </span>
  );
}
