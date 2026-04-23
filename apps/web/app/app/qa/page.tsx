"use client";

import { useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Shield, Sparkles, XCircle } from "lucide-react";
import { qa } from "@/lib/api";
import type { QaResponse, VerifiedClaim } from "@/lib/types";
import CitationCard from "@/components/workspace/CitationCard";

export default function QaTab() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [out, setOut] = useState<QaResponse | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setOut(null);
    try {
      const res = await qa(question);
      setOut(res);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || question.trim().length < 3;

  return (
    <div className="p-6 md:p-8 space-y-6">
      <header className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-serif text-2xl">How Would Tanmay Answer</h2>
          <p className="text-sm text-inkMuted">
            Grounded answers from the archive. Refuses honestly when he hasn't spoken on it.
          </p>
        </div>
        <span className="pill"><span className="pill-dot bg-lavenderDeep" />TOOL 03</span>
      </header>

      <div>
        <label className="label">Your question</label>
        <textarea
          className="textarea"
          placeholder="e.g. what does Tanmay think about therapy and friendships"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !disabled) run();
          }}
        />
        <div className="mt-1.5 text-[11px] text-inkSubtle">⌘/Ctrl + Enter to submit</div>
      </div>

      <button onClick={run} disabled={disabled} className="btn-gradient">
        {loading ? (<><Loader2 size={14} className="mr-2 animate-spin" />Thinking…</>) : (<><Sparkles size={14} className="mr-2" />Ask</>)}
      </button>

      {err && (
        <div className="rounded-xl border border-refuseRose bg-refuseRose/30 p-4 text-sm">
          <strong>Error:</strong> {err}
        </div>
      )}

      {out && <QaResult result={out} />}
    </div>
  );
}

function QaResult({ result }: { result: QaResponse }) {
  if (result.status === "refused_sensitive") {
    return (
      <div className="rounded-2xl border border-refuseRose bg-refuseRose/20 p-5">
        <div className="flex items-center gap-2 font-semibold">
          <Shield size={16} />Refused — sensitive topic
        </div>
        <div className="mt-2 text-sm text-inkMuted">{result.reason}</div>
      </div>
    );
  }
  if (result.status === "refused_low_confidence") {
    return (
      <div className="rounded-2xl border border-line bg-cream/60 p-5">
        <div className="flex items-center gap-2 font-semibold">
          <AlertCircle size={16} />Tanmay hasn't spoken on this
        </div>
        <div className="mt-2 text-sm text-inkMuted">{result.reason}</div>
        {result.max_similarity != null && (
          <div className="mt-1 text-[11px] text-inkSubtle font-mono">
            max similarity {result.max_similarity.toFixed(3)}
          </div>
        )}
        {result.paraphrases_used.length > 0 && (
          <details className="mt-3 text-[11px] text-inkSubtle">
            <summary className="cursor-pointer">paraphrases tried</summary>
            <ul className="mt-1 list-disc pl-4 space-y-1">
              {result.paraphrases_used.map((p, i) => (<li key={i}>{p}</li>))}
            </ul>
          </details>
        )}
      </div>
    );
  }

  // answered
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap text-[11px]">
        <span className="pill bg-[#d4f0de]/40 border-okGreen/40 text-[#1f7a4a]">
          <CheckCircle2 size={10} />ANSWERED
        </span>
        {result.max_similarity != null && (
          <span className="font-mono text-inkSubtle">sim {result.max_similarity.toFixed(3)}</span>
        )}
        <span className="font-mono text-inkSubtle">
          {result.n_supported}/{result.n_supported + result.n_unsupported} claims verified
        </span>
      </div>

      <div className="rounded-2xl border border-line bg-white p-6 text-[15px] leading-relaxed whitespace-pre-wrap">
        {result.answer}
      </div>

      {result.verified_claims.length > 0 && (
        <details className="rounded-2xl border border-line bg-canvas/50 p-4">
          <summary className="cursor-pointer text-[11px] tracking-[0.18em] font-semibold text-inkSubtle">
            CLAIM-BY-CLAIM VERIFICATION ({result.verified_claims.length})
          </summary>
          <ul className="mt-3 space-y-2">
            {result.verified_claims.map((c, i) => (
              <ClaimRow key={i} c={c} />
            ))}
          </ul>
        </details>
      )}

      {result.paraphrases_used.length > 0 && (
        <details className="rounded-xl border border-line bg-canvas/50 p-3 text-[11px] text-inkSubtle">
          <summary className="cursor-pointer">multi-query paraphrases used</summary>
          <ul className="mt-2 list-disc pl-4 space-y-1">
            {result.paraphrases_used.map((p, i) => (<li key={i}>{p}</li>))}
          </ul>
        </details>
      )}

      {result.citations.length > 0 && (
        <div>
          <div className="text-[11px] tracking-[0.18em] font-semibold text-inkSubtle mb-2">
            CITATIONS ({result.citations.length})
          </div>
          <div className="grid sm:grid-cols-2 gap-2.5">
            {result.citations.map((c, i) => (
              <CitationCard key={c.source_id + i} idx={i + 1} c={c} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ClaimRow({ c }: { c: VerifiedClaim }) {
  const Icon = c.supported ? CheckCircle2 : XCircle;
  return (
    <li className="flex items-start gap-2.5 text-[13px]">
      <Icon size={14} className={`mt-0.5 shrink-0 ${c.supported ? "text-[#1f9d5a]" : "text-salmon"}`} />
      <div className="flex-1">
        <div className="leading-relaxed">{c.claim}</div>
        {c.citation_indices.length > 0 && (
          <div className="mt-1 flex gap-1">
            {c.citation_indices.map((idx) => (
              <span key={idx} className="font-mono text-[10px] rounded-md border border-line bg-white px-1.5 py-0.5 text-inkSubtle">
                [{idx}]
              </span>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}
