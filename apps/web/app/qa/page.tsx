"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Citations } from "@/components/ui/Citations";
import { Label, Textarea } from "@/components/ui/Field";
import { qa } from "@/lib/api";
import type { QaResponse } from "@/lib/types";

export default function QaPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QaResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask() {
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await qa(question));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-accent">Tab 03</div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">How Would Tanmay Answer This</h1>
        <p className="mt-1 text-sm text-muted">
          Answers grounded in his actual words, with clickable citations. If he hasn't spoken on it, the system says so
          rather than guess.
        </p>
      </div>

      <div>
        <Label>Question</Label>
        <Textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What does Tanmay think about AI replacing creators?"
        />
      </div>
      <Button onClick={ask} disabled={busy || !question.trim()}>
        {busy ? "Thinking…" : "Ask"}
      </Button>
      {error && <div className="text-sm text-red-400">{error}</div>}

      {result && (
        <div className="space-y-4">
          {result.status === "answered" && (
            <div className="rounded-xl border border-border bg-panel p-6">
              <div className="mb-1 flex items-center justify-between">
                <div className="text-xs uppercase tracking-[0.15em] text-accentGreen">Answer</div>
                {result.max_similarity != null && (
                  <div className="font-mono text-xs text-muted">sim {result.max_similarity.toFixed(2)}</div>
                )}
              </div>
              <div className="whitespace-pre-wrap text-sm">{result.answer}</div>
            </div>
          )}
          {result.status === "refused_low_confidence" && (
            <div className="rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-6 text-sm">
              <div className="mb-1 font-semibold text-yellow-300">Tanmay hasn't spoken publicly on this.</div>
              <div className="text-yellow-100/80">{result.reason}</div>
            </div>
          )}
          {result.status === "refused_sensitive" && (
            <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6 text-sm">
              <div className="mb-1 font-semibold text-red-300">Declined.</div>
              <div className="text-red-100/80">{result.reason}</div>
            </div>
          )}
          <Citations citations={result.citations} />
        </div>
      )}
    </div>
  );
}
