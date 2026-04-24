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

/* ---- Tab 1: Content ---- */
export interface ContentGenerateRequest {
  idea: string;
  format: "reel" | "youtube_short" | "talking_head" | "reaction" | "long_podcast" | "thread" | "stage" | "monologue" | "explainer" | "interview";
  target_length_seconds: number;
  tone: ToneDial;
  language: "hinglish" | "english" | "hindi";
}

export interface ContentGenerateResponse {
  script: string;
  description: string;
  rationale: string;
  citations: Citation[];
}

/* ---- Tab 2: Ad ---- */
export interface AdCast {
  name: string;
  role?: string;
}

export type Industry =
  | "fintech" | "d2c" | "saas_b2b" | "fmcg" | "beauty" | "edtech"
  | "auto" | "realty" | "ott_media" | "telecom" | "healthcare" | "travel" | "other";

export type CampaignGoal =
  | "awareness" | "consideration" | "conversion" | "relaunch" | "feature_drop";

export type AdPlacement =
  | "yt_preroll" | "yt_bumper" | "ig_reel" | "ig_story" | "tv_spot" | "ooh" | "audio" | "other";

export type ProductStage = "launch" | "relaunch" | "feature" | "seasonal" | "always_on";

export type BrandVoiceTag =
  | "premium" | "playful" | "cant_do_humor" | "family_safe_only"
  | "no_celebrity_impersonation" | "educational" | "minimal";

export interface AdGenerateRequest {
  product_name: string;
  product_description: string;
  target_audience?: string;
  duration_seconds: number;
  language: "hinglish" | "english" | "hindi";
  cast: AdCast[];
  celebrities: string[];
  notes?: string;
  tone: ToneDial;

  // New diversity/quality fields — all optional for backward compat.
  industry?: Industry;
  campaign_goal?: CampaignGoal;
  proof_point?: string;
  positioning?: string;
  competitor?: string;
  brand_voice_tags?: BrandVoiceTag[];
  do_not_say?: string[];
  placement?: AdPlacement;
  product_stage?: ProductStage;
}

export interface AdScene {
  scene_number: number;
  setting: string;
  direction: string;
  characters: string[];
  lines: string[];
  duration_seconds: number;
}

export interface AdQualityScores {
  on_brand: number;
  proof_point_present: number;
  audience_match: number;
  hook_strength: number;
  no_tanmay_leak: number;
  notes: string;
}

export interface AdGenerateResponse {
  title: string;
  hook: string;
  scenes: AdScene[];
  cta: string;
  strategy_rationale: string;
  brand_safety_flags: string[];
  citations: Citation[];
  quality?: AdQualityScores | null;
  do_not_say_hits: string[];
  proof_point_found: boolean | null;
}

export interface AdValidation {
  valid: boolean;
  duration_seconds: number;
  words: number;
  issues: string[];
  quality_total?: number | null;
  do_not_say_hits: string[];
  proof_found: boolean | null;
}

/* ---- Tab 3: Q&A ---- */
export type QaStatus = "answered" | "refused_low_confidence" | "refused_sensitive";

export interface VerifiedClaim {
  claim: string;
  citation_indices: number[];
  supported: boolean;
}

export interface QaResponse {
  status: QaStatus;
  answer?: string | null;
  reason?: string | null;
  citations: Citation[];
  max_similarity?: number | null;
  verified_claims: VerifiedClaim[];
  n_supported: number;
  n_unsupported: number;
  paraphrases_used: string[];
}
