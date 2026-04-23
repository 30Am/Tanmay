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
  const validation: AdValidation = {
    valid: res.headers.get("X-Ad-Valid") === "true",
    duration_seconds: Number(res.headers.get("X-Ad-Duration") || 0),
    words: Number(res.headers.get("X-Ad-Words") || 0),
    issues: (res.headers.get("X-Ad-Validation-Issues") || "none")
      .split(";")
      .filter((s) => s && s !== "none"),
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
