import { API_BASE } from "./utils";
import type {
  AdGenerateRequest,
  AdGenerateResponse,
  Citation,
  ContentGenerateRequest,
  QaResponse,
} from "./types";

export async function generateAd(req: AdGenerateRequest): Promise<AdGenerateResponse> {
  const res = await fetch(`${API_BASE}/generate/ad`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Ad generation failed: ${res.status}`);
  return res.json();
}

export async function qa(question: string): Promise<QaResponse> {
  const res = await fetch(`${API_BASE}/generate/qa`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Q&A failed: ${res.status}`);
  return res.json();
}

export interface ContentStreamEvents {
  onCitations?: (citations: Citation[]) => void;
  onToken?: (token: string) => void;
  onDone?: () => void;
  onError?: (err: Error) => void;
}

export async function streamContent(
  req: ContentGenerateRequest,
  events: ContentStreamEvents,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const res = await fetch(`${API_BASE}/generate/content`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(req),
      signal,
    });
    if (!res.ok || !res.body) throw new Error(`Content stream failed: ${res.status}`);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let currentEvent = "message";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const rawLine of lines) {
        const line = rawLine.trimEnd();
        if (!line) {
          currentEvent = "message";
          continue;
        }
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          const data = line.slice(6);
          if (currentEvent === "citations") {
            try {
              events.onCitations?.(JSON.parse(data));
            } catch {
              /* ignore bad JSON */
            }
          } else if (currentEvent === "token") {
            events.onToken?.(data);
          } else if (currentEvent === "done") {
            events.onDone?.();
          }
        }
      }
    }
    events.onDone?.();
  } catch (err) {
    events.onError?.(err instanceof Error ? err : new Error(String(err)));
  }
}
