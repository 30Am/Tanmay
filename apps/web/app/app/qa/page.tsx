"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Shield, Sparkles, XCircle } from "lucide-react";
import { qa } from "@/lib/api";
import type { QaResponse, VerifiedClaim } from "@/lib/types";
import CitationCard from "@/components/workspace/CitationCard";
import ToolHeader from "@/components/workspace/ToolHeader";

export default function QaTab() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<QaResponse | null>(null);

  async function run() {
    setLoading(true); setErr(null); setOut(null);
    try { setOut(await qa(question)); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    finally { setLoading(false); }
  }

  const disabled = loading || question.trim().length < 3;

  return (
    <div className="max-w-[900px]">
      <ToolHeader
        eyebrow="TAB 03"
        title="How Would Tanmay Answer"
        subtitle="Grounded in his actual words. Refuses honestly when he hasn't spoken on it."
        chipClass="chip-qa"
      />

      <div className="card p-8 space-y-5">
        <div>
          <label className="field-label">Your question</label>
          <textarea
            className="textarea-field"
            placeholder="e.g. what does Tanmay think about therapy and friendships"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !disabled) run();
            }}
          />
          <div className="mt-2 text-[12px] text-ink-3">⌘ / Ctrl + Enter to submit</div>
        </div>
        <button onClick={run} disabled={disabled} className="btn-primary">
          {loading
            ? <><Loader2 size={16} className="mr-2 animate-spin" />Thinking…</>
            : <><Sparkles size={16} className="mr-2" />Ask</>}
        </button>
      </div>

      {err && (
        <div className="mt-6 rounded-2xl bg-coral/15 border border-coral/40 p-5 text-body text-ink">
          <strong>Error:</strong> {err}
        </div>
      )}

      {out && <div className="mt-8"><QaResult r={out} /></div>}
    </div>
  );
}

function QaResult({ r }: { r: QaResponse }) {
  if (r.status === "refused_sensitive") {
    return (
      <div className="card-flat bg-coral/10 border-coral/40 p-6">
        <div className="flex items-center gap-2 font-semibold text-ink"><Shield size={17} />Refused — sensitive topic</div>
        <p className="mt-2 text-body text-ink-2">{r.reason}</p>
      </div>
    );
  }
  if (r.status === "refused_low_confidence") {
    return (
      <div className="card-flat bg-butter/60 p-6">
        <div className="flex items-center gap-2 font-semibold text-ink"><AlertCircle size={17} />Tanmay hasn't spoken on this</div>
        <p className="mt-2 text-body text-ink-2">{r.reason}</p>
        {r.max_similarity != null && (
          <div className="mt-2 text-[12px] text-ink-3 font-mono">max sim {r.max_similarity.toFixed(3)}</div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="chip bg-mint text-ink"><CheckCircle2 size={12} />ANSWERED</span>
        {r.max_similarity != null && (
          <span className="font-mono text-[12px] text-ink-3">sim {r.max_similarity.toFixed(3)}</span>
        )}
        <span className="font-mono text-[12px] text-ink-3">
          {r.n_supported}/{r.n_supported + r.n_unsupported} claims verified
        </span>
      </div>

      <div className="card-flat p-7 text-body-l text-ink leading-relaxed whitespace-pre-wrap">
        {r.answer}
      </div>

      {r.verified_claims.length > 0 && (
        <details className="card-flat p-5">
          <summary className="cursor-pointer caption text-coral-deep">
            CLAIM-BY-CLAIM VERIFICATION · {r.verified_claims.length}
          </summary>
          <ul className="mt-4 space-y-2.5">
            {r.verified_claims.map((c, i) => <ClaimRow key={i} c={c} />)}
          </ul>
        </details>
      )}

      {r.paraphrases_used.length > 0 && (
        <details className="card-flat p-4">
          <summary className="cursor-pointer text-[13px] text-ink-3">Multi-query paraphrases</summary>
          <ul className="mt-2 list-disc pl-5 space-y-1 text-[13px] text-ink-2">
            {r.paraphrases_used.map((p, i) => <li key={i}>{p}</li>)}
          </ul>
        </details>
      )}

      {r.citations.length > 0 && (
        <div>
          <div className="caption text-coral-deep mb-3">CITATIONS · {r.citations.length}</div>
          <div className="grid sm:grid-cols-2 gap-3">
            {r.citations.map((c, i) => <CitationCard key={c.source_id + i} idx={i + 1} c={c} />)}
          </div>
        </div>
      )}
    </div>
  );
}

function ClaimRow({ c }: { c: VerifiedClaim }) {
  const Icon = c.supported ? CheckCircle2 : XCircle;
  return (
    <li className="flex items-start gap-3 text-body">
      <Icon size={16} className={`mt-0.5 shrink-0 ${c.supported ? "text-green-600" : "text-coral-deep"}`} />
      <div className="flex-1">
        <div className="text-ink">{c.claim}</div>
        {c.citation_indices.length > 0 && (
          <div className="mt-1 flex gap-1.5">
            {c.citation_indices.map((idx) => (
              <span key={idx} className="font-mono text-[11px] rounded-md bg-surface border border-border px-2 py-0.5 text-ink-3">
                [{idx}]
              </span>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}
