"""Gemini 2.5 Flash-Lite chunk tagger.

For each chunk, returns:
  - topic_tags:       list of 3-6 short tags
  - register:         roast | reflective | informative | comedic | sincere
  - language_mix:     {hi: 0..1, en: 0..1}
  - entities:         named people/brands/products mentioned
  - sentiment:        -1..1
"""
from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

TAG_SYSTEM = """You annotate short excerpts from podcast/interview transcripts featuring the Indian
comedian/creator Tanmay Bhat. Output strict JSON only.

REGISTER RUBRIC — pick the single best fit. When two fit, prefer the more specific one
(comedic/roast over informative, roast over comedic).

- roast: mocks or playfully insults a person, brand, or group; punches at a target. Signals:
  sarcastic comparisons, exaggerated put-downs, rapid-fire jabs, "bro is…", imitation.
- comedic: humor-forward without a specific target. Signals: bits, absurdist riffs, self-
  deprecation, punchlines, laughter-inducing asides, jokey tangents.
- roast and comedic are common for Tanmay — do NOT default to reflective/informative just
  because the topic is serious.
- reflective: introspective or personal — emotional, values-driven, vulnerability, lessons
  learned, mental-health talk, regret, growth.
- informative: explains facts, mechanics, data, how-things-work with neutral tone. News
  recaps, tool walkthroughs, finance/crypto explainers.
- sincere: heartfelt gratitude, earnest praise, emotional tribute; non-joking, non-analytic.

EXAMPLES

Text: "Bro thinks he's Elon Musk because he raised 50K on a Google form. The entire round is his mom, his chacha, and one guy from IIT who pressed the wrong button."
-> register: "roast"

Text: "So basically the way this ChatGPT agent thing works is, it spawns a browser, clicks through flights, compares prices, then hands you the cheapest one. It's slow but it actually books the ticket."
-> register: "informative"

Text: "I used to think losing the weight would fix everything. It didn't. The brain stuff was still there, just in a smaller body. That was a rough realisation, honestly."
-> register: "reflective"

Text: "No man, the Sam Altman India trip was wild. He's in a Nehru jacket eating butter chicken and everyone's acting like he's Gandhi 2.0. I was dying."
-> register: "comedic"

Text: "Ma, thank you for staying up that whole night when I was shooting and couldn't call. I don't say it enough but I see it."
-> register: "sincere"

LANGUAGE_MIX — approximate ratio of Hindi vs English in the text. Sum to 1.0. Code-switched
Hinglish is common — estimate.

TOPIC_TAGS — 3-6 short phrases (lowercase, 1-3 words). Examples: "ai tools", "mental health",
"aib", "crypto", "podcast guest intro", "weight loss".

ENTITIES — named people, brands, products, shows, cities mentioned. Skip pronouns.

SENTIMENT — -1.0 to 1.0. Negative = critical/sad/angry. Positive = celebratory/happy.

Output JSON only. No prose."""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "topic_tags": {"type": "array", "items": {"type": "string"}},
        "register": {"type": "string", "enum": ["roast", "reflective", "informative", "comedic", "sincere"]},
        "language_mix": {
            "type": "object",
            "properties": {"hi": {"type": "number"}, "en": {"type": "number"}},
            "required": ["hi", "en"],
        },
        "entities": {"type": "array", "items": {"type": "string"}},
        "sentiment": {"type": "number"},
    },
    "required": ["topic_tags", "register", "language_mix", "entities", "sentiment"],
}


class Tagger:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = genai.Client(api_key=api_key or os.environ.get("GOOGLE_API_KEY", ""))

    async def tag(self, text: str) -> dict[str, Any]:
        try:
            response = await self._client.aio.models.generate_content(
                model=MODEL,
                contents=text[:4000],
                config=types.GenerateContentConfig(
                    system_instruction=TAG_SYSTEM,
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.1,
                    max_output_tokens=500,
                ),
            )
            return json.loads(response.text)
        except (json.JSONDecodeError, AttributeError, Exception):  # noqa: BLE001
            return {
                "topic_tags": [],
                "register": "comedic",
                "language_mix": {"hi": 0.5, "en": 0.5},
                "entities": [],
                "sentiment": 0.0,
            }
