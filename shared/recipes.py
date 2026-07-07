"""Canned recipe data so Sage's suggestions are reproducible (no external API).

Each recipe has tags (vegetarian / pescatarian / quick / budget …) and an optional
`contains` list (ingredients someone might want to avoid).
"""
RECIPES = [
    {"name": "lentil curry",        "tags": ["vegetarian", "budget", "hearty"], "minutes": 30, "contains": []},
    {"name": "black bean tacos",    "tags": ["vegetarian", "budget", "quick"],  "minutes": 20, "contains": []},
    {"name": "mushroom risotto",    "tags": ["vegetarian", "cozy"],             "minutes": 40, "contains": ["mushroom"]},
    {"name": "caprese pasta",       "tags": ["vegetarian", "quick"],            "minutes": 20, "contains": ["dairy"]},
    {"name": "chickpea shakshuka",  "tags": ["vegetarian", "budget"],           "minutes": 25, "contains": ["egg"]},
    {"name": "grilled salmon bowl", "tags": ["pescatarian", "healthy"],         "minutes": 25, "contains": ["fish"]},
    {"name": "shrimp stir-fry",     "tags": ["pescatarian", "quick"],           "minutes": 20, "contains": ["shellfish"]},
    {"name": "chicken fajitas",     "tags": ["quick", "budget"],                "minutes": 25, "contains": ["chicken"]},
]


def pick(preferences: list[str]) -> dict:
    """Return the first recipe that satisfies all preferences (or any recipe if none fit)."""
    prefs = " ".join(preferences).lower()
    for r in RECIPES:
        if "vegetarian" in prefs and "vegetarian" not in r["tags"]:
            continue
        if "pescatarian" in prefs and not ({"vegetarian", "pescatarian"} & set(r["tags"])):
            continue
        if "quick" in prefs and "quick" not in r["tags"]:
            continue
        if "budget" in prefs and "budget" not in r["tags"]:
            continue
        if any(bad in prefs for bad in r["contains"]):   # e.g. "no mushroom" avoids mushroom
            continue
        return r
    return RECIPES[0]
