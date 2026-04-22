from __future__ import annotations

from dataclasses import dataclass, field


REFUSED_CATEGORIES: dict[str, list[str]] = {
    "real_money_gaming": ["rummy", "poker", "fantasy money", "betting", "gambling", "teen patti cash"],
    "predatory_finance": ["loan app", "instant loan", "high-interest", "payday loan"],
    "sketchy_crypto": ["memecoin", "pump", "shitcoin", "rugpull", "airdrop farm"],
    "pseudoscience_health": ["miracle cure", "detox tea", "weight-loss pill", "alkaline"],
}


@dataclass
class SafetyReport:
    ok: bool
    flags: list[str] = field(default_factory=list)


def check_product(
    *,
    product_name: str,
    product_description: str,
) -> SafetyReport:
    haystack = f"{product_name} {product_description}".lower()
    flags: list[str] = []
    for category, keywords in REFUSED_CATEGORIES.items():
        if any(k in haystack for k in keywords):
            flags.append(category)
    return SafetyReport(ok=not flags, flags=flags)
