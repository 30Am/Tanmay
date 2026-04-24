/**
 * localStorage-backed generation history.
 *
 * Structure: { qa: HistoryEntry[], content: HistoryEntry[], ad: HistoryEntry[] }
 * Max 20 entries per tab — oldest entries are pruned automatically.
 */

export type HistoryTab = "qa" | "content" | "ad";

export interface HistoryEntry {
  id: string;
  tab: HistoryTab;
  /** Short human-readable label shown in the sidebar */
  label: string;
  /** Full input (question / idea / product name) */
  input: string;
  /** First ~200 chars of the output for preview */
  preview: string;
  /** ISO timestamp */
  savedAt: string;
}

const STORAGE_KEY = "tgpt_history";
const MAX_PER_TAB = 20;

function readStore(): Record<HistoryTab, HistoryEntry[]> {
  if (typeof window === "undefined") return { qa: [], content: [], ad: [] };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { qa: [], content: [], ad: [] };
    const parsed = JSON.parse(raw);
    return {
      qa: Array.isArray(parsed.qa) ? parsed.qa : [],
      content: Array.isArray(parsed.content) ? parsed.content : [],
      ad: Array.isArray(parsed.ad) ? parsed.ad : [],
    };
  } catch {
    return { qa: [], content: [], ad: [] };
  }
}

function writeStore(store: Record<HistoryTab, HistoryEntry[]>) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    // Storage quota exceeded — clear and retry once
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    } catch { /* give up */ }
  }
}

/** Save a new entry, deduplicating by input and pruning to MAX_PER_TAB. */
export function saveToHistory(entry: Omit<HistoryEntry, "id" | "savedAt">) {
  const store = readStore();
  const tab = entry.tab;

  const newEntry: HistoryEntry = {
    ...entry,
    id: `${tab}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    savedAt: new Date().toISOString(),
  };

  // Remove any existing entry with the same input to avoid near-duplicates
  const filtered = store[tab].filter(
    (e) => e.input.trim().toLowerCase() !== entry.input.trim().toLowerCase()
  );

  store[tab] = [newEntry, ...filtered].slice(0, MAX_PER_TAB);
  writeStore(store);
  return newEntry;
}

/** Get all entries for a tab, newest first. */
export function getHistory(tab: HistoryTab): HistoryEntry[] {
  return readStore()[tab];
}

/** Get entries across all tabs, newest first (for the combined history page). */
export function getAllHistory(): HistoryEntry[] {
  const store = readStore();
  return [...store.qa, ...store.content, ...store.ad].sort(
    (a, b) => new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
  );
}

/** Delete a single entry by id. */
export function deleteEntry(id: string) {
  const store = readStore();
  for (const tab of ["qa", "content", "ad"] as HistoryTab[]) {
    store[tab] = store[tab].filter((e) => e.id !== id);
  }
  writeStore(store);
}

/** Clear all history. */
export function clearHistory() {
  writeStore({ qa: [], content: [], ad: [] });
}

/** Human-readable relative time (e.g. "2 min ago", "yesterday"). */
export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "yesterday";
  if (days < 7) return `${days} days ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}
