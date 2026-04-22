export type Platform =
  | "youtube"
  | "x"
  | "linkedin"
  | "instagram"
  | "podcast"
  | "event"
  | "other";

export interface Citation {
  source_id: string;
  url: string;
  platform: Platform;
  title?: string | null;
  timestamp_seconds?: number | null;
  excerpt: string;
}

export interface ToneDial {
  roast_level: number;
  chaos: number;
  depth: number;
  hinglish_ratio: number;
}

export interface ContentGenerateRequest {
  idea: string;
  format: "long_podcast" | "reel" | "thread" | "stage";
  target_length_seconds: number;
  tone: ToneDial;
}

export interface AdCast {
  name: string;
  role?: string;
}

export interface AdGenerateRequest {
  product_name: string;
  product_description: string;
  target_audience?: string;
  duration_seconds: number;
  language: "hinglish" | "english" | "hindi";
  cast: AdCast[];
  celebrities: string[];
  notes?: string;
}

export interface AdScene {
  scene_number: number;
  setting: string;
  direction: string;
  characters: string[];
  lines: string[];
  duration_seconds: number;
}

export interface AdGenerateResponse {
  title: string;
  hook: string;
  scenes: AdScene[];
  cta: string;
  strategy_rationale: string;
  brand_safety_flags: string[];
  citations: Citation[];
}

export type QaStatus = "answered" | "refused_low_confidence" | "refused_sensitive";

export interface QaResponse {
  status: QaStatus;
  answer?: string | null;
  reason?: string | null;
  citations: Citation[];
  max_similarity?: number | null;
}
