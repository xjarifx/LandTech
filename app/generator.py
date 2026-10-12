"""Fixed-seed synthetic Bengali demo data; never use real records."""

import random
from datetime import date, timedelta

NAMES = ["রহিম উদ্দিন", "করিম মিয়া", "সাবিনা আক্তার", "মেহেদী হাসান", "সুমি রহমান"]
DISTRICTS = ["ঢাকা", "কুমিল্লা", "গাজীপুর", "ময়মনসিংহ"]


def generate() -> tuple[list[dict], list[dict]]:
    rng = random.Random(2026)
    plots = []
    for number in range(1, 51):
        plots.append({"plot_id": f"P-{number:03}", "area": float(rng.randint(30, 180)),
                      "survey_type": rng.choice(["CS", "SA", "RS", "BS"]),
                      "mouza": f"ডেমো মৌজা {number:02}", "upazila": "ডেমো উপজেলা",
                      "district": rng.choice(DISTRICTS), "status": "CLEAR", "pending_case": 0})
    plots[3]["status"] = "KHAS_OR_ACQUIRED"
    plots[4]["pending_case"] = 1
    start = date(2026, 1, 1)
    deeds = []
    for number in range(1, 101):
        plot = plots[(number - 1) % 50]
        deeds.append({"deed_id": f"D-{number:04}", "plot_id": plot["plot_id"],
                      "seller": NAMES[(number - 1) % len(NAMES)],
                      "buyer": NAMES[number % len(NAMES)], "area": min(10 + number % 20, plot["area"]),
                      "father_name": f"ডেমো পিতা {number:03}", "khatian_no": f"K-{10000 + number}",
                      "dag_no": f"{500 + number}", "deed_no": f"REG-{2026}-{number:04}",
                      "registration_date": (start + timedelta(days=number * 3)).isoformat(),
                      "registered_at": (start + timedelta(days=number * 3)).isoformat(),
                      "mouza": plot["mouza"], "upazila": plot["upazila"], "district": plot["district"],
                      "survey_type": plot["survey_type"], "sub_registry": "ডেমো সাব-রেজিস্ট্রি অফিস",
                      "mutation_status": "PENDING"})
    # Deliberate double sale and rapid transfer scenarios.
    deeds[50].update(plot_id="P-001", seller="রহিম উদ্দিন", registered_at="2026-02-01")
    deeds[51].update(plot_id="P-001", seller="রহিম উদ্দিন", registered_at="2026-02-03")
    deeds[52].update(plot_id="P-002", registered_at="2026-02-04")
    deeds[53].update(plot_id="P-002", registered_at="2026-02-05")
    return plots, deeds
