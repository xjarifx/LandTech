"""Transparent, rule-based demo flags. Thresholds are configuration, not law."""

from datetime import datetime


def flags(plot: dict, deeds: list[dict], candidate: dict, rapid_n: int = 2,
          rapid_days: int = 7) -> list[dict]:
    prior = [d for d in deeds if d["plot_id"] == candidate["plot_id"]]
    result = []
    if any(d["seller"] == candidate["seller"] for d in prior):
        result.append({"code": "SAME_SELLER_RESOLD", "en": "Same seller already transferred this plot.",
                       "bn": "একই বিক্রেতা এই প্লট আগে হস্তান্তর করেছেন।"})
    if sum(float(d["area"]) for d in prior) + float(candidate["area"]) > float(plot["area"]):
        result.append({"code": "OVER_SOLD_AREA", "en": "Transferred area exceeds plot area.",
                       "bn": "হস্তান্তরিত জমির পরিমাণ প্লটের চেয়ে বেশি।"})
    dates = [datetime.fromisoformat(d["registered_at"]).date() for d in prior]
    dates.append(datetime.fromisoformat(candidate["registered_at"]).date())
    if len(dates) >= rapid_n and (max(dates) - min(dates)).days <= rapid_days:
        result.append({"code": "RAPID_TRANSFER", "en": "Several transfers happened within the configured window.",
                       "bn": "নির্ধারিত অল্প সময়ে একাধিক হস্তান্তর হয়েছে।"})
    if candidate.get("mutation_status") == "PENDING":
        result.append({"code": "NO_MUTATION", "en": "No simulated mutation record is linked yet.",
                       "bn": "এখনও কোনো সিমুলেটেড নামজারি রেকর্ড যুক্ত নেই।"})
    return result
