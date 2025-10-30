# agents/tagging_agent.py

import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict
from utils.logger import get_logger
from typing import Dict
import re

# Load environment variables
load_dotenv()

logger = get_logger("tagging_agent", level=logging.DEBUG)


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-5-nano",
    temperature=os.getenv("OPENAI_TEMPERATURE"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    # max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "128"))
)

# Optional system prompt to guide consistent tagging
system_prompt = SystemMessage(content="""
You are a semantic tagging assistant for travel attractions. Your job is to analyze each attraction and return a comma-separated list of descriptive tags that reflect its appeal, audience, and experience type.

# Use tags like:
# - entertainment
# - historical
# - sightseeing
# - indoor
# - outdoor
# - adventurous
# - educational
                              
Allowed tags (example set, return only tags from this domain): food, dining, restaurant, cafe, bar, nightlife, shopping, museum, historical, sightseeing, park, nature, beach, entertainment, adventurous, educational, indoor, outdoor, family_friendly, romantic, relaxation, wellness, cultural.
When the attraction is a place to eat/drink (categories like food, restaurant, cafe, bar, bakery) you MUST return at least one food-related tag (e.g., food, dining, restaurant, cafe, bar). Only return the tags. Do not explain or format them. Limit the number of tags to a maximum of 3 per attraction or highlight.
""")

# def tag_attraction(attraction: Dict, limitations=None) -> Dict:
#     name = attraction.get("name", "")
#     categories = ", ".join(attraction.get("categories", []))
#     # features = ", ".join(attraction.get("features", []))

#     logger.info(f"Tagging attraction: {name}")

#     prompt = f"""
#     Name: {name}
#     Categories: {categories}
#     Based on the above information, provide a list of relevant tags from system prompt for this attraction. Limit to maximum of 3 tags.
#     """

#     response = llm.invoke([system_prompt, HumanMessage(content=prompt)])
#     logger.info(f"Response for tagging: {response.content}")

#     tags = [tag.strip() for tag in response.content.split(",")]
#     logger.info(f"Tags generated: {tags}")

#     return {**attraction, "tags": tags}


PREFERRED_TAGS = {
    "food","dining","restaurant","cafe","bar","nightlife","shopping","museum","historical",
    "sightseeing","park","nature","beach","entertainment","adventurous","educational",
    "indoor","outdoor","family_friendly","romantic","relaxation","wellness","cultural"
}

FOOD_KEYWORDS = ["food","restaurant","cafe","eat","dining","bakery","bistro","bar","coffee","cuisine"]

def _heuristic_tags_from_categories(categories: list) -> list:
    cats = " ".join([str(c).lower() for c in categories])
    # food
    if any(k in cats for k in FOOD_KEYWORDS):
        # prefer restaurant/cafe/dining -> choose top relevant
        if "bar" in cats or "pub" in cats:
            return ["bar","nightlife"]
        if "cafe" in cats or "coffee" in cats:
            return ["cafe","food"]
        return ["food","dining","restaurant"]
    # museum / history
    if "museum" in cats or "histor" in cats:
        return ["museum","historical","educational"]
    # park / nature / beach
    if "park" in cats or "nature" in cats or "beach" in cats:
        return ["park","nature","outdoor"]
    # shopping
    if "shop" in cats or "market" in cats:
        return ["shopping","entertainment"]
    # fallback
    return []

def _normalize_tag_list(raw_text: str) -> list:
    if not raw_text:
        return []
    parts = re.split(r"[,\n]+", raw_text)
    cleaned = []
    for p in parts:
        t = p.strip().lower()
        t = re.sub(r"[^a-z0-9_ ]", "", t)
        if t:
            cleaned.append(t)
    return cleaned



def tag_attraction(attraction: Dict, limitations=None, preferences=None) -> Dict:
    """
    Enrich an attraction dict with tags, excluded flag and wheelchair_accessible flag.
    - limitations: dict | list | str (normalized here)
    - preferences: list[str] or comma string (used to bias tagging, e.g., 'food')
    """
    # Normalize limitations input
    if limitations is None:
        limitations = {}
    elif isinstance(limitations, list):
        limitations = {"avoid_categories": [str(x).strip().lower().replace("no_","").replace("avoid_","").replace("no ","").replace("avoid:","") for x in limitations]}
    elif isinstance(limitations, str):
        try:
            import json
            parsed = json.loads(limitations)
            limitations = parsed if isinstance(parsed, dict) else {"avoid_categories": [limitations]}
        except Exception:
            limitations = {"avoid_categories": [limitations]}
    elif not isinstance(limitations, dict):
        limitations = {}

    # Normalize preferences to list[str]
    if preferences is None:
        prefs = []
    elif isinstance(preferences, str):
        prefs = [p.strip().lower() for p in preferences.split(",") if p.strip()]
    elif isinstance(preferences, (list, tuple)):
        prefs = [str(p).strip().lower() for p in preferences if isinstance(p, (str, int))]
    else:
        prefs = []

    # Ensure attraction fields are normalized
    name = attraction.get("name") or attraction.get("attraction") or "Unknown"
    raw_categories = attraction.get("categories", [])

    # normalize categories to list[str]
    categories = []
    if isinstance(raw_categories, (list, tuple)):
        for c in raw_categories:
            if isinstance(c, dict):
                if "name" in c:
                    categories.append(str(c["name"]))
                else:
                    categories.append(str(c))
            else:
                categories.append(str(c))
    else:
        if raw_categories:
            categories = [str(raw_categories)]

    categories_str = ", ".join(categories) if categories else ""

    logger.info(f"Tagging attraction: {name}")

    prompt = f"""
        Name: {name}
        Categories: {categories_str}
        User preferences: {', '.join(prefs) if prefs else 'none'}
        Based on the above information, return a comma-separated list of up to 3 tags from the allowed tag set (food, dining, restaurant, cafe, bar, nightlife, shopping, museum, historical, sightseeing, park, nature, beach, entertainment, adventurous, educational, indoor, outdoor, family_friendly, romantic, relaxation, wellness, cultural). 
        If the place is a food/drink place, include at least one food-related tag. Return only the tags.
        """

    # compute limitation-driven flags (ensure lowercasing / normalization)
    raw_avoid = limitations.get("avoid_categories", [])
    avoid = set()
    for it in raw_avoid:
        if not it:
            continue
        t = str(it).strip().lower()
        if t.startswith("no "):
            t = t[3:]
        if t.startswith("avoid:"):
            t = t.split(":",1)[1]
        t = t.replace("no_","").replace("avoid_","").strip()
        if t:
            avoid.add(t)

    # determine excluded using normalized categories and name
    excluded = False
    if avoid and categories:
        cat_lc = set([c.lower() for c in categories if isinstance(c, str)])
        name_lc = str(name).lower()
        if cat_lc & avoid or any(a in name_lc for a in avoid):
            excluded = True

    # Wheelchair/accessibility inference
    wheelchair_flag = None
    if "wheelchair" in attraction:
        wheelchair_flag = bool(attraction.get("wheelchair"))
    elif "wheelchair_accessible" in attraction:
        wheelchair_flag = bool(attraction.get("wheelchair_accessible"))
    elif "accessibility" in attraction and isinstance(attraction["accessibility"], dict):
        wheelchair_flag = bool(attraction["accessibility"].get("wheelchair"))

    tags = []
    try:
        resp = llm.invoke([system_prompt, HumanMessage(content=prompt)])
        text = getattr(resp, "content", "") or (resp.get("text") if isinstance(resp, dict) else str(resp))
        raw_tags = _normalize_tag_list(text)

        # prefer allowed tags
        tags = [t for t in raw_tags if t in PREFERRED_TAGS]
        if not tags and raw_tags:
            tags = raw_tags[:3]
    except Exception as exc:
        logger.exception("Tagging LLM failed, falling back to categories: %s", exc)
        tags = [c.lower() for c in categories][:3]

    # Heuristic fallback based on categories/name
    heur = _heuristic_tags_from_categories(categories)
    if heur:
        if not any(h in tags for h in heur):
            tags = (tags + [h for h in heur if h not in tags])[:3]

    # If user prefers food, and categories/name imply food, ensure at least one food tag
    if "food" in prefs or "dining" in prefs or "eat" in prefs:
        cats_joined = " ".join([c.lower() for c in categories])
        name_lower = str(name).lower()
        if any(k in cats_joined for k in FOOD_KEYWORDS) or any(k in name_lower for k in FOOD_KEYWORDS):
            if not any(t in {"food", "dining", "restaurant", "cafe", "bar"} for t in tags):
                food_h = _heuristic_tags_from_categories(categories) or ["food"]
                for fh in food_h:
                    if fh not in tags:
                        tags = ([fh] + tags)[:3]
                        break

    # Final safety: fallback to categories if still empty
    if not tags:
        tags = [c.lower() for c in categories][:3]

    logger.info(f"Tags generated for '{name}': {tags}")

    return {
        **attraction,
        "tags": tags,
        "excluded": excluded,
        "wheelchair_accessible": wheelchair_flag
    }