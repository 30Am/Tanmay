import { API_BASE } from "./utils";
import type {
  AdGenerateRequest,
  AdGenerateResponse,
  AdValidation,
  ContentGenerateRequest,
  ContentGenerateResponse,
  QaResponse,
} from "./types";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const err = new Error(`${res.status} ${res.statusText}`);
    (err as Error & { detail?: unknown }).detail = detail;
    throw err;
  }
  return (await res.json()) as T;
}

export function generateContent(req: ContentGenerateRequest): Promise<ContentGenerateResponse> {
  return post<ContentGenerateResponse>("/generate/content", req);
}

export type ContentStreamEvent =
  | { type: "token"; text: string }
  | { type: "done"; script: string; description: string; rationale: string; citations: ContentGenerateResponse["citations"] };

export async function* generateContentStream(
  req: ContentGenerateRequest,
): AsyncGenerator<ContentStreamEvent> {
  const res = await fetch(`${API_BASE}/generate/content/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const line = part.trim();
      if (line.startsWith("data: ")) {
        const payload = line.slice(6).trim();
        if (payload) yield JSON.parse(payload) as ContentStreamEvent;
      }
    }
  }
}

export async function generateAd(
  req: AdGenerateRequest,
): Promise<{ data: AdGenerateResponse; validation: AdValidation }> {
  const res = await fetch(`${API_BASE}/generate/ad`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const err = new Error(`${res.status} ${res.statusText}`);
    (err as Error & { detail?: unknown }).detail = detail;
    throw err;
  }
  const data = (await res.json()) as AdGenerateResponse;
  const qualityTotalRaw = res.headers.get("X-Ad-Quality-Total") || "na";
  const proofRaw = res.headers.get("X-Ad-Proof-Found") || "na";
  const validation: AdValidation = {
    valid: res.headers.get("X-Ad-Valid") === "true",
    duration_seconds: Number(res.headers.get("X-Ad-Duration") || 0),
    words: Number(res.headers.get("X-Ad-Words") || 0),
    issues: (res.headers.get("X-Ad-Validation-Issues") || "none")
      .split(";")
      .filter((s) => s && s !== "none"),
    quality_total: qualityTotalRaw === "na" ? null : Number(qualityTotalRaw),
    do_not_say_hits: (res.headers.get("X-Ad-DNS-Hits") || "none")
      .split(";")
      .filter((s) => s && s !== "none"),
    proof_found: proofRaw === "true" ? true : proofRaw === "false" ? false : null,
  };
  return { data, validation };
}

export async function exportAd(
  req: AdGenerateRequest,
  format: "md" | "fountain",
): Promise<string> {
  const res = await fetch(`${API_BASE}/generate/ad?format=${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Ad export failed: ${res.status}`);
  return res.text();
}

export function qa(question: string): Promise<QaResponse> {
  return post<QaResponse>("/generate/qa", { question });
}
