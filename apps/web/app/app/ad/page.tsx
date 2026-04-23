"use client";

import { useState } from "react";
import { AlertTriangle, Copy, Download, Loader2, Shield, Sparkles } from "lucide-react";
import { exportAd, generateAd } from "@/lib/api";
import type {
  AdGenerateRequest,
  AdGenerateResponse,
  AdValidation,
} from "@/lib/types";
import CitationCard from "@/components/workspace/CitationCard";
import Reveal from "@/components/motion/Reveal";

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

export default function AdTab() {
  const [req, setReq] = useState<AdGenerateRequest>(DEFAULT_REQ);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<{ message: string; detail?: unknown } | null>(null);
  const [out, setOut] = useState<{ data: AdGenerateResponse; validation: AdValidation } | null>(null);
  const [exportBusy, setExportBusy] = useState<null | "md" | "fountain">(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setOut(null);
    try {
      const res = await generateAd(req);
      setOut(res);
    } catch (e) {
      const err = e as Error & { detail?: unknown };
      setErr({ message: err.message, detail: err.detail });
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
      const ext = format === "md" ? "md" : "fountain";
      a.download = `${req.product_name.replace(/\s+/g, "_") || "ad"}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export failed: ${e instanceof Error ? e.message : e}`);
    } finally {
      setExportBusy(null);
    }
  }

  const disabled = loading || req.product_name.trim().length < 2 || req.product_description.trim().length < 3;

  const refusedBrandSafety =
    err?.detail && typeof err.detail === "object" && err.detail !== null && "error" in (err.detail as Record<string, unknown>)
      ? ((err.detail as Record<string, unknown>).error === "refused_brand_safety")
      : false;

  return (
    <div className="p-6 md:p-8 space-y-6">
      <header className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-serif text-2xl">Ad Generation</h2>
          <p className="text-sm text-inkMuted">
            Structured brief → schema-validated ad with brand-safety gate + duration validator.
          </p>
        </div>
        <span className="pill"><span className="pill-dot bg-[#60a5fa]" />TOOL 02</span>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <label className="label">Product name</label>
          <input className="input" value={req.product_name} placeholder="Stonks Neobank"
            onChange={(e) => setReq((r) => ({ ...r, product_name: e.target.value }))} />
        </div>
        <div>
          <label className="label">Target audience</label>
          <input className="input" value={req.target_audience ?? ""} placeholder="Gen Z college students in India"
            onChange={(e) => setReq((r) => ({ ...r, target_audience: e.target.value }))} />
        </div>
      </div>

      <div>
        <label className="label">Product description</label>
        <textarea className="textarea" value={req.product_description} placeholder="one-tap SIP + fractional stock investing for 18-25 year olds"
          onChange={(e) => setReq((r) => ({ ...r, product_description: e.target.value }))} />
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div>
          <label className="label">Duration (sec): <span className="font-semibold">{req.duration_seconds}</span></label>
          <input type="range" min={10} max={180} step={5} value={req.duration_seconds}
            onChange={(e) => setReq((r) => ({ ...r, duration_seconds: parseInt(e.target.value) }))}
            className="w-full accent-pinkDeep" />
        </div>
        <div>
          <label className="label">Language</label>
          <select className="select" value={req.language}
            onChange={(e) => setReq((r) => ({ ...r, language: e.target.value as AdGenerateRequest["language"] }))}>
            <option value="hinglish">Hinglish</option>
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
          </select>
        </div>
        <div>
          <label className="label">Notes (optional)</label>
          <input className="input" value={req.notes ?? ""} placeholder="fun not preachy; demystify investing"
            onChange={(e) => setReq((r) => ({ ...r, notes: e.target.value }))} />
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <button onClick={run} disabled={disabled} className="btn-gradient">
          {loading ? (<><Loader2 size={14} className="mr-2 animate-spin" />Generating…</>) : (<><Sparkles size={14} className="mr-2" />Generate ad</>)}
        </button>
        {out && (
          <>
            <button onClick={() => download("md")} disabled={!!exportBusy} className="btn-ghost">
              <Download size={14} />{exportBusy === "md" ? "…" : "Markdown"}
            </button>
            <button onClick={() => download("fountain")} disabled={!!exportBusy} className="btn-ghost">
              <Download size={14} />{exportBusy === "fountain" ? "…" : "Fountain"}
            </button>
            <button onClick={() => navigator.clipboard.writeText(JSON.stringify(out.data, null, 2))} className="btn-ghost">
              <Copy size={14} />JSON
            </button>
          </>
        )}
      </div>

      {err && (
        <div className={`rounded-xl border p-4 text-sm ${refusedBrandSafety ? "bg-refuseRose/30 border-refuseRose" : "bg-cream border-line"}`}>
          <div className="flex items-center gap-2 font-semibold">
            <Shield size={14} />
            {refusedBrandSafety ? "Refused by brand-safety gate" : "Error"}
          </div>
          <div className="mt-1.5 text-inkMuted">
            {refusedBrandSafety ? (err.detail as { reason?: string }).reason : err.message}
          </div>
        </div>
      )}

      {out && (
        <div key={out.data.title.slice(0, 32)} className="space-y-5">
          <Reveal className="flex items-center gap-2 flex-wrap">
            <ValidationBadge validation={out.validation} />
            {out.data.brand_safety_flags.map((f) => (
              <span key={f} className="pill border-amber-200 bg-amber-50 text-[#a26a1a]">
                <AlertTriangle size={10} className="text-[#a26a1a]" />{f}
              </span>
            ))}
          </Reveal>

          <Reveal delay={1}>
            <div className="flex items-baseline justify-between">
              <h3 className="font-serif text-2xl">{out.data.title}</h3>
              <span className="font-mono text-[11px] text-inkSubtle">
                {out.data.scenes.length} scenes · {out.validation.duration_seconds}s · {out.validation.words} words
              </span>
            </div>
            {out.data.hook && (
              <div className="mt-3 rounded-2xl border border-line bg-cream/50 p-4 text-[15px] leading-relaxed italic">
                <span className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle not-italic block mb-1">HOOK</span>
                "{out.data.hook}"
              </div>
            )}
          </Reveal>

          <div className="space-y-3">
            {out.data.scenes.map((s, i) => (
              <Reveal key={s.scene_number} delay={((Math.min(i + 1, 6)) as 1 | 2 | 3 | 4 | 5 | 6)} className="rounded-2xl border border-line bg-white p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-[11px] text-inkSubtle">SCENE {s.scene_number}</span>
                  <span className="font-mono text-[11px] text-inkSubtle">{s.duration_seconds}s</span>
                </div>
                <div className="text-[13px] text-inkMuted italic">
                  <span className="font-semibold not-italic text-ink">Setting:</span> {s.setting}
                </div>
                <div className="mt-1.5 text-[13px] text-inkMuted italic">
                  <span className="font-semibold not-italic text-ink">Direction:</span> {s.direction}
                </div>
                {s.characters.length > 0 && (
                  <div className="mt-1.5 text-[13px] text-inkMuted">
                    <span className="font-semibold text-ink">Cast:</span> {s.characters.join(", ")}
                  </div>
                )}
                <div className="mt-3 space-y-2">
                  {s.lines.map((line, lineIdx) => (
                    <blockquote key={lineIdx} className="border-l-2 border-pinkDeep/40 pl-3 text-[15px] leading-relaxed">
                      {line}
                    </blockquote>
                  ))}
                </div>
              </Reveal>
            ))}
          </div>

          {out.data.cta && (
            <div className="rounded-2xl border border-line bg-gradient-card p-5">
              <div className="text-[11px] tracking-[0.2em] font-semibold text-inkSubtle mb-1">CTA</div>
              <div className="font-serif text-lg">{out.data.cta}</div>
            </div>
          )}

          {out.data.strategy_rationale && (
            <div>
              <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-2">STRATEGY RATIONALE</div>
              <div className="rounded-2xl border border-line bg-white p-4 text-[14px] text-inkMuted leading-relaxed">
                {out.data.strategy_rationale}
              </div>
            </div>
          )}

          {out.data.citations.length > 0 && (
            <div>
              <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-2">
                CITATIONS ({out.data.citations.length})
              </div>
              <div className="grid sm:grid-cols-2 gap-2.5">
                {out.data.citations.map((c, i) => (
                  <CitationCard key={c.source_id + i} idx={i + 1} c={c} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ValidationBadge({ validation }: { validation: AdValidation }) {
  if (validation.valid) {
    return (
      <span className="pill border-okGreen/40 bg-[#d4f0de]/40 text-[#1f7a4a]">
        <span className="pill-dot bg-[#16a34a]" />VALIDATED · {validation.duration_seconds}s
      </span>
    );
  }
  return (
    <span className="pill border-amber-200 bg-amber-50 text-[#a26a1a]">
      <AlertTriangle size={10} />{validation.issues.join(" · ") || "validation warning"}
    </span>
  );
}
