"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, Loader2, RotateCcw, Share2, Shield, Sparkles, Star, X } from "lucide-react";
import { exportAd, generateAd } from "@/lib/api";
import type {
  AdGenerateRequest,
  AdGenerateResponse,
  AdPlacement,
  AdValidation,
  BrandVoiceTag,
  CampaignGoal,
  Industry,
  ProductStage,
  ToneDial as ToneDialT,
} from "@/lib/types";
import { saveToHistory } from "@/lib/history";
import ToneDial from "@/components/workspace/ToneDial";
import ToolTopBar from "@/components/workspace/ToolTopBar";

const WPM: Record<"hinglish" | "english" | "hindi", number> = {
  hinglish: 138, english: 156, hindi: 120,
};
const DURATIONS = [6, 10, 15, 30, 45, 60, 90, 120, 180];

// Ad-specific defaults: moderate roast, medium chaos, low depth (punchy > insightful), high Hinglish
const DEFAULT_TONE: ToneDialT = { roast_level: 0.65, chaos: 0.55, depth: 0.35, hinglish_ratio: 0.70 };

const INDUSTRIES: { value: Industry; label: string }[] = [
  { value: "fintech", label: "Fintech" },
  { value: "d2c", label: "D2C / Consumer" },
  { value: "saas_b2b", label: "SaaS / B2B" },
  { value: "fmcg", label: "FMCG" },
  { value: "beauty", label: "Beauty" },
  { value: "edtech", label: "Edtech" },
  { value: "auto", label: "Auto" },
  { value: "realty", label: "Real Estate" },
  { value: "ott_media", label: "OTT / Media" },
  { value: "telecom", label: "Telecom" },
  { value: "healthcare", label: "Healthcare" },
  { value: "travel", label: "Travel" },
  { value: "other", label: "Other" },
];

const CAMPAIGN_GOALS: { value: CampaignGoal; label: string }[] = [
  { value: "awareness", label: "Awareness" },
  { value: "consideration", label: "Consideration" },
  { value: "conversion", label: "Conversion" },
  { value: "relaunch", label: "Relaunch" },
  { value: "feature_drop", label: "Feature drop" },
];

const PLACEMENTS: { value: AdPlacement; label: string }[] = [
  { value: "yt_bumper", label: "YouTube bumper (6s)" },
  { value: "yt_preroll", label: "YouTube pre-roll" },
  { value: "ig_reel", label: "Instagram Reel" },
  { value: "ig_story", label: "Instagram Story" },
  { value: "tv_spot", label: "TV spot" },
  { value: "ooh", label: "OOH / Billboard" },
  { value: "audio", label: "Audio-only / Podcast" },
  { value: "other", label: "Other" },
];

const PRODUCT_STAGES: { value: ProductStage; label: string }[] = [
  { value: "launch", label: "Launch" },
  { value: "relaunch", label: "Relaunch" },
  { value: "feature", label: "New feature" },
  { value: "seasonal", label: "Seasonal" },
  { value: "always_on", label: "Always-on" },
];

const BRAND_VOICE_TAGS: { value: BrandVoiceTag; label: string }[] = [
  { value: "premium", label: "Premium" },
  { value: "playful", label: "Playful" },
  { value: "cant_do_humor", label: "No humor" },
  { value: "family_safe_only", label: "Family-safe" },
  { value: "no_celebrity_impersonation", label: "No celeb impression" },
  { value: "educational", label: "Educational" },
  { value: "minimal", label: "Minimal" },
];

export default function AdsTab() {
  const [productName, setProductName] = useState("");
  const [productDescription, setProductDescription] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [duration, setDuration] = useState(45);
  const [language, setLanguage] = useState<"hinglish" | "english" | "hindi">("hinglish");
  const [celebs, setCelebs] = useState<string[]>([]);
  const [celebInput, setCelebInput] = useState("");
  const [notes, setNotes] = useState("");
  const [tone, setTone] = useState<ToneDialT>(DEFAULT_TONE);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<{ message: string; detail?: unknown } | null>(null);
  const [out, setOut] = useState<{ data: AdGenerateResponse; validation: AdValidation } | null>(null);
  const [exportBusy, setExportBusy] = useState<null | "md" | "fountain">(null);

  // New diversity/quality fields
  const [industry, setIndustry] = useState<Industry | "">("");
  const [campaignGoal, setCampaignGoal] = useState<CampaignGoal | "">("");
  const [placement, setPlacement] = useState<AdPlacement | "">("");
  const [productStage, setProductStage] = useState<ProductStage | "">("");
  const [proofPoint, setProofPoint] = useState("");
  const [positioning, setPositioning] = useState("");
  const [competitor, setCompetitor] = useState("");
  const [brandVoiceTags, setBrandVoiceTags] = useState<BrandVoiceTag[]>([]);
  const [dnsInput, setDnsInput] = useState("");
  const [doNotSay, setDoNotSay] = useState<string[]>([]);

  const req: AdGenerateRequest = useMemo(
    () => ({
      product_name: productName,
      product_description: productDescription,
      target_audience: targetAudience || undefined,
      duration_seconds: duration,
      language,
      cast: [],
      celebrities: celebs,
      notes: notes || undefined,
      tone,
      industry: industry || undefined,
      campaign_goal: campaignGoal || undefined,
      placement: placement || undefined,
      product_stage: productStage || undefined,
      proof_point: proofPoint || undefined,
      positioning: positioning || undefined,
      competitor: competitor || undefined,
      brand_voice_tags: brandVoiceTags.length ? brandVoiceTags : undefined,
      do_not_say: doNotSay.length ? doNotSay : undefined,
    }),
    [
      productName, productDescription, targetAudience, duration, language, celebs, notes, tone,
      industry, campaignGoal, placement, productStage, proofPoint, positioning, competitor,
      brandVoiceTags, doNotSay,
    ],
  );

  function toggleVoiceTag(tag: BrandVoiceTag) {
    setBrandVoiceTags((prev) => (prev.includes(tag) ? prev.filter((x) => x !== tag) : [...prev, tag]));
  }
  function addDns() {
    const t = dnsInput.trim();
    if (t && !doNotSay.includes(t)) setDoNotSay([...doNotSay, t]);
    setDnsInput("");
  }

  const wpm = WPM[language];
  const wordBand = [Math.round((duration * wpm) / 60 * 0.9), Math.round((duration * wpm) / 60 * 1.1)] as const;

  async function run() {
    setLoading(true);
    setErr(null);
    setOut(null);
    try {
      const result = await generateAd(req);
      setOut(result);
      if (result.data.hook) {
        saveToHistory({
          tab: "ad",
          label: productName.length > 60 ? productName.slice(0, 57) + "…" : productName,
          input: productName,
          preview: [result.data.hook, ...(result.data.scenes?.[0]?.lines ?? [])].join(" ").slice(0, 200),
        });
      }
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
      a.download = `${productName.replace(/\s+/g, "_") || "ad"}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportBusy(null);
    }
  }

  function addCeleb() {
    const t = celebInput.trim();
    if (t && !celebs.includes(t)) setCelebs([...celebs, t]);
    setCelebInput("");
  }

  const disabled = loading || productName.trim().length < 2 || productDescription.trim().length < 3;
  const refused = err?.detail && typeof err.detail === "object" && err.detail !== null
    && (err.detail as Record<string, unknown>).error === "refused_brand_safety";

  return (
    <>
      <ToolTopBar
        right={
          <>
            <button
              onClick={() => out && download("fountain")}
              disabled={!out || !!exportBusy}
              className="inline-flex items-center gap-2 rounded-pill border border-border bg-surface px-4 py-2 text-[13px] text-ink-2 hover:text-ink disabled:opacity-40"
            >
              <Download size={13} />
              {exportBusy === "fountain" ? "…" : "Export as Fountain"}
            </button>
            <button
              onClick={() => out && download("md")}
              disabled={!out || !!exportBusy}
              className="inline-flex items-center gap-2 rounded-pill bg-ink text-surface px-5 py-2 text-[14px] font-medium hover:translate-y-[-1px] transition disabled:opacity-40"
            >
              <Share2 size={13} />
              {exportBusy === "md" ? "…" : "Share brief"}
            </button>
          </>
        }
      />

      <div>
        <div className="caption text-[#7d6ec6]">TAB 02 · AD GENERATION</div>
        <h1 className="mt-3 font-bold tracking-[-0.02em] leading-[1.08] text-[44px] text-ink">
          Write a branded ad.
        </h1>
      </div>

      <div className="mt-8 grid lg:grid-cols-[480px_1fr] gap-5 items-start">
        {/* ───────── LEFT: CAMPAIGN BRIEF ───────── */}
        <aside className="card p-7 space-y-5">
          <div className="caption text-ink-3">CAMPAIGN BRIEF</div>

          <div>
            <label className="field-label">Product name</label>
            <input
              className="field"
              value={productName}
              placeholder="Cred Max · revolving credit card"
              onChange={(e) => setProductName(e.target.value)}
            />
          </div>

          <div>
            <label className="field-label">Product description</label>
            <textarea
              className="textarea-field min-h-[96px]"
              value={productDescription}
              placeholder="A credit card that gives you more credit as you use more. Targeted at young professionals with proven repayment history."
              onChange={(e) => setProductDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="field-label">Celebs to feature</label>
            <div className="min-h-[52px] rounded-pill bg-surface border border-border px-3 py-2 flex flex-wrap items-center gap-2">
              {celebs.map((c) => (
                <span key={c} className="inline-flex items-center gap-1.5 rounded-pill bg-coral/25 px-3 py-1 text-[13px] text-ink">
                  {c}
                  <button
                    type="button"
                    onClick={() => setCelebs(celebs.filter((x) => x !== c))}
                    className="hover:text-coral-deep"
                    aria-label={`Remove ${c}`}
                  >
                    <X size={13} />
                  </button>
                </span>
              ))}
              <input
                className="flex-1 min-w-[120px] bg-transparent outline-none text-[14px] px-2 py-1 placeholder:text-ink-3"
                value={celebInput}
                placeholder={celebs.length ? "Add another…" : "Rohan Joshi, Kusha Kapila…"}
                onChange={(e) => setCelebInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addCeleb(); }
                  if (e.key === "Backspace" && !celebInput && celebs.length) {
                    setCelebs(celebs.slice(0, -1));
                  }
                }}
                onBlur={addCeleb}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="field-label">Duration</label>
              <select
                className="select-field"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
              >
                {DURATIONS.map((s) => (
                  <option key={s} value={s}>{s} seconds</option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label">Language</label>
              <select
                className="select-field"
                value={language}
                onChange={(e) => setLanguage(e.target.value as "hinglish" | "english" | "hindi")}
              >
                <option value="hinglish">Hinglish (70/30)</option>
                <option value="english">English</option>
                <option value="hindi">Hindi</option>
              </select>
            </div>
          </div>

          <div>
            <label className="field-label">Target audience</label>
            <textarea
              className="textarea-field min-h-[80px]"
              value={targetAudience}
              placeholder="Urban, 22-34, tier-1 cities. Young professionals who've lived through at least one credit card scam."
              onChange={(e) => setTargetAudience(e.target.value)}
            />
          </div>

          {/* ───────── CATEGORY & CAMPAIGN ───────── */}
          <div className="pt-2 border-t border-border">
            <div className="caption text-ink-3 mb-3">CATEGORY & CAMPAIGN</div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="field-label">Industry</label>
                <select
                  className="select-field"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value as Industry | "")}
                >
                  <option value="">Unspecified</option>
                  {INDUSTRIES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Campaign goal</label>
                <select
                  className="select-field"
                  value={campaignGoal}
                  onChange={(e) => setCampaignGoal(e.target.value as CampaignGoal | "")}
                >
                  <option value="">Unspecified</option>
                  {CAMPAIGN_GOALS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Placement</label>
                <select
                  className="select-field"
                  value={placement}
                  onChange={(e) => setPlacement(e.target.value as AdPlacement | "")}
                >
                  <option value="">Unspecified</option>
                  {PLACEMENTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="field-label">Product stage</label>
                <select
                  className="select-field"
                  value={productStage}
                  onChange={(e) => setProductStage(e.target.value as ProductStage | "")}
                >
                  <option value="">Unspecified</option>
                  {PRODUCT_STAGES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* ───────── STRATEGY ───────── */}
          <div className="pt-2 border-t border-border">
            <div className="caption text-ink-3 mb-3">STRATEGY</div>
            <div>
              <label className="field-label">Proof point (the one thing this ad must anchor around)</label>
              <input
                className="field"
                value={proofPoint}
                placeholder="Processes ₹1Cr in 60 seconds · 24-month battery · zero-FX on first ₹10k"
                maxLength={280}
                onChange={(e) => setProofPoint(e.target.value)}
              />
            </div>
            <div className="mt-4">
              <label className="field-label">Positioning / USP</label>
              <input
                className="field"
                value={positioning}
                placeholder="The only bank account that pays you to use it."
                maxLength={280}
                onChange={(e) => setPositioning(e.target.value)}
              />
            </div>
            <div className="mt-4">
              <label className="field-label">Competitor or displaces (optional)</label>
              <input
                className="field"
                value={competitor}
                placeholder="UPI apps · the spreadsheet · traditional bank"
                maxLength={140}
                onChange={(e) => setCompetitor(e.target.value)}
              />
            </div>
          </div>

          {/* ───────── BRAND GUARDRAILS ───────── */}
          <div className="pt-2 border-t border-border">
            <div className="caption text-ink-3 mb-3">BRAND GUARDRAILS</div>
            <label className="field-label">Voice tags</label>
            <div className="flex flex-wrap gap-2">
              {BRAND_VOICE_TAGS.map((t) => {
                const active = brandVoiceTags.includes(t.value);
                return (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => toggleVoiceTag(t.value)}
                    className={`rounded-pill px-3.5 py-1.5 text-[13px] border transition ${active ? "bg-ink text-surface border-ink" : "bg-surface text-ink-2 border-border hover:text-ink"}`}
                  >
                    {t.label}
                  </button>
                );
              })}
            </div>

            <div className="mt-4">
              <label className="field-label">Do-not-say list (legal / compliance / no-gos)</label>
              <div className="min-h-[44px] rounded-pill bg-surface border border-border px-3 py-2 flex flex-wrap items-center gap-2">
                {doNotSay.map((w) => (
                  <span key={w} className="inline-flex items-center gap-1.5 rounded-pill bg-coral/25 px-3 py-1 text-[13px] text-ink">
                    {w}
                    <button
                      type="button"
                      onClick={() => setDoNotSay(doNotSay.filter((x) => x !== w))}
                      className="hover:text-coral-deep"
                      aria-label={`Remove ${w}`}
                    >
                      <X size={12} />
                    </button>
                  </span>
                ))}
                <input
                  className="flex-1 min-w-[120px] bg-transparent outline-none text-[14px] px-2 py-1 placeholder:text-ink-3"
                  value={dnsInput}
                  placeholder={doNotSay.length ? "Add another…" : "guaranteed, cure, cheap, [competitor]"}
                  onChange={(e) => setDnsInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addDns(); }
                    if (e.key === "Backspace" && !dnsInput && doNotSay.length) {
                      setDoNotSay(doNotSay.slice(0, -1));
                    }
                  }}
                  onBlur={addDns}
                />
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-mint/50 border border-mint px-4 py-3 flex items-center gap-2.5 text-[13px] text-ink">
            <CheckCircle2 size={15} className="text-[#1f7a4a] shrink-0" />
            Target word count: {wordBand[0]}-{wordBand[1]} words ({duration}s @ {wpm} WPM)
          </div>

          <div className="rounded-2xl bg-surface border border-border px-5 py-5">
            <ToneDial value={tone} onChange={setTone} onReset={() => setTone(DEFAULT_TONE)} />
          </div>

          <button
            onClick={run}
            disabled={disabled}
            className="relative w-full rounded-pill py-4 font-semibold text-ink bg-gradient-twilight shadow-card transition hover:translate-y-[-1px] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading
              ? <><Loader2 size={16} className="animate-spin" />Generating…</>
              : <><Sparkles size={16} />Generate ad script</>}
          </button>
        </aside>

        {/* ───────── RIGHT: OUTPUT ───────── */}
        <section className="space-y-5">
          {/* Brand-safety banner */}
          {err ? (
            <div className={`rounded-2xl p-5 flex items-start gap-3 ${refused ? "bg-coral/15 border border-coral/40" : "bg-butter border border-border"}`}>
              <Shield size={18} className="mt-0.5 shrink-0 text-ink" />
              <div>
                <div className="font-semibold text-ink">
                  {refused ? "Refused by brand-safety gate" : "Error"}
                </div>
                <div className="mt-1 text-body text-ink-2">
                  {refused ? (err.detail as { reason?: string }).reason : err.message}
                </div>
              </div>
            </div>
          ) : out ? (
            <div className={`rounded-2xl p-5 flex items-start gap-3 ${out.data.brand_safety_flags.length === 0 ? "bg-mint/60 border border-mint" : "bg-butter border border-border"}`}>
              {out.data.brand_safety_flags.length === 0 ? (
                <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-[#1f7a4a]" />
              ) : (
                <AlertTriangle size={20} className="mt-0.5 shrink-0 text-[#a26a1a]" />
              )}
              <div>
                <div className="font-semibold text-ink">
                  {out.data.brand_safety_flags.length === 0 ? "Brand-safety gate passed" : "Brand-safety flags"}
                </div>
                <div className="mt-1 text-body text-ink-2">
                  {out.data.brand_safety_flags.length === 0
                    ? "No category conflicts. This brief matches the archive's sponsor patterns."
                    : out.data.brand_safety_flags.join(" · ")}
                </div>
              </div>
            </div>
          ) : null}

          {/* Ad script panel */}
          <div className="card p-7">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="caption text-ink-3">
                  AD SCRIPT{out?.data?.scenes?.length ? ` · ${out.data.scenes.length} SCENES` : ""}
                </span>
                {out && (
                  <div className="flex items-center gap-2">
                    <span className="chip bg-butter text-ink">{out.validation.duration_seconds}s</span>
                    <span className="chip bg-peach text-ink">{out.validation.words} words</span>
                    <span className="chip bg-lavender/70 text-ink capitalize">{language}</span>
                    {!out.validation.valid && (
                      <span className="chip bg-coral/25 text-coral-deep">
                        <AlertTriangle size={11} />
                        {out.validation.issues.join(" · ")}
                      </span>
                    )}
                  </div>
                )}
              </div>
              {out && (
                <button
                  onClick={run}
                  className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-3.5 py-1.5 text-[13px] text-ink-2 hover:text-ink"
                >
                  <RotateCcw size={13} /> Regenerate
                </button>
              )}
            </div>

            <div className="mt-6 space-y-3">
              {out?.data?.scenes?.length ? (
                out.data.scenes.map((s, i) => (
                  <SceneRow key={s.scene_number} scene={s} runningStart={cumStart(out.data.scenes, i)} />
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-border p-7 text-[14px] text-ink-3 text-center">
                  Scene-by-scene ad script with director notes and dialogue will appear here.
                </div>
              )}
            </div>

            {out?.data?.cta && (
              <div className="mt-5 rounded-2xl bg-gradient-sunrise p-5">
                <div className="caption text-coral-deep">CALL TO ACTION</div>
                <div className="mt-2 text-[17px] font-semibold text-ink">{out.data.cta}</div>
              </div>
            )}

            {out?.data?.hook && (
              <div className="mt-5 rounded-2xl bg-butter p-5 border border-border">
                <div className="caption text-coral-deep">HOOK</div>
                <div className="mt-2 text-[16px] italic text-ink">"{out.data.hook}"</div>
              </div>
            )}
          </div>

          {/* Quality panel — visible only when we have signals to show */}
          {out && (out.data.quality || out.data.do_not_say_hits.length || out.data.proof_point_found !== null) && (
            <div className="card p-6">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="caption text-ink-3 flex items-center gap-2">
                  <Star size={13} /> QUALITY SIGNALS
                </div>
                {out.data.quality && (
                  <div className="text-[15px] font-semibold text-ink">
                    {out.data.quality.on_brand + out.data.quality.proof_point_present + out.data.quality.audience_match + out.data.quality.hook_strength + out.data.quality.no_tanmay_leak}<span className="text-ink-3 font-normal"> / 25</span>
                  </div>
                )}
              </div>

              {out.data.quality && (
                <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-2">
                  <QualityBar label="On-brand" score={out.data.quality.on_brand} />
                  <QualityBar label="Proof point" score={out.data.quality.proof_point_present} />
                  <QualityBar label="Audience" score={out.data.quality.audience_match} />
                  <QualityBar label="Hook" score={out.data.quality.hook_strength} />
                  <QualityBar label="No Tanmay leak" score={out.data.quality.no_tanmay_leak} />
                </div>
              )}

              {out.data.quality?.notes && (
                <div className="mt-4 text-[13px] text-ink-2 italic">{out.data.quality.notes}</div>
              )}

              <div className="mt-4 flex flex-wrap gap-2 text-[12px]">
                {out.data.proof_point_found === true && (
                  <span className="inline-flex items-center gap-1 chip bg-mint/70 text-ink">
                    <CheckCircle2 size={11} /> Proof point anchored
                  </span>
                )}
                {out.data.proof_point_found === false && (
                  <span className="inline-flex items-center gap-1 chip bg-coral/25 text-coral-deep">
                    <AlertTriangle size={11} /> Proof point missing from output
                  </span>
                )}
                {out.data.do_not_say_hits.length > 0 && (
                  <span className="inline-flex items-center gap-1 chip bg-coral/25 text-coral-deep">
                    <AlertTriangle size={11} /> Banned term(s): {out.data.do_not_say_hits.join(", ")}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Strategic rationale */}
          <div className="rounded-2xl bg-lavender/60 p-8 border border-border">
            <div className="caption text-[#7d6ec6]">STRATEGIC RATIONALE</div>
            {out?.data?.strategy_rationale ? (
              <>
                <h3 className="mt-3 text-[22px] font-semibold text-ink leading-snug">
                  Why this beat-structure works{productName ? ` for ${productName.split("·")[0].trim()}` : ""}
                </h3>
                <div className="mt-4 text-body text-ink-2 leading-relaxed whitespace-pre-wrap">
                  {out.data.strategy_rationale}
                </div>
              </>
            ) : (
              <p className="mt-3 text-body text-ink-2 leading-relaxed">
                The reasoning behind the structure — which archive patterns this mirrors, why the
                scene order lands, where the callbacks fire — will land here after generation.
              </p>
            )}
          </div>
        </section>
      </div>
    </>
  );
}

function cumStart(scenes: { duration_seconds: number }[], idx: number): number {
  let s = 0;
  for (let i = 0; i < idx; i++) s += scenes[i]?.duration_seconds ?? 0;
  return s;
}

function SceneRow({ scene, runningStart }: { scene: AdGenerateResponse["scenes"][number]; runningStart: number }) {
  const end = runningStart + scene.duration_seconds;
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 flex gap-5">
      <div className="shrink-0 w-12 text-center">
        <div className="h-9 w-9 rounded-full bg-gradient-sunrise grid place-items-center font-semibold text-ink">
          {scene.scene_number}
        </div>
        <div className="mt-2 text-[10px] font-mono text-ink-3">
          {fmt(runningStart)}-{fmt(end)}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[15px] font-semibold text-ink">{scene.setting || `Scene ${scene.scene_number}`}</span>
          {scene.direction && (
            <span className="chip bg-lavender/60 text-[#7d6ec6] text-[11px]">{truncate(scene.direction, 40)}</span>
          )}
        </div>
        {scene.characters.length > 0 && (
          <div className="mt-1 text-[12px] text-ink-3">{scene.characters.join(" · ")}</div>
        )}
        <div className="mt-2 space-y-1.5">
          {scene.lines.map((line, i) => (
            <div key={i} className="text-[14px] text-ink leading-relaxed">
              {line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function fmt(s: number) {
  const m = Math.floor(s / 60);
  const ss = Math.floor(s % 60);
  return `${m}:${String(ss).padStart(2, "0")}`;
}
function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function QualityBar({ label, score }: { label: string; score: number }) {
  const pct = Math.max(0, Math.min(5, score)) / 5;
  const color =
    score >= 4 ? "bg-mint" : score >= 3 ? "bg-butter" : "bg-coral/50";
  return (
    <div className="rounded-xl bg-surface border border-border p-3">
      <div className="text-[11px] text-ink-3 mb-1.5 truncate">{label}</div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-[18px] font-bold text-ink leading-none">{score}</span>
        <span className="text-[11px] text-ink-3">/5</span>
      </div>
      <div className="mt-2 h-1.5 rounded-pill bg-border overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct * 100}%` }} />
      </div>
    </div>
  );
}
