# agents/itinerary_agent.py

import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("itinerary_agent", level=logging.DEBUG)


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-5-nano",
    temperature=os.getenv("OPENAI_TEMPERATURE"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    # max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "128"))
)

# Optional system prompt to guide itinerary structure
system_prompt = SystemMessage(content="""
You are a travel itinerary planner. Your job is to create a multi-day itinerary using a list of tagged attractions and user preferences. Return response in English only.

Each day should include:
- Morning
- Afternoon
- Evening

Avoid duplicates. Prioritize attractions that match user preferences. Use tags to guide pacing and variety. Format clearly by day and time slot. Evenly distribute activities across days. Take into account any user limitations provided. Provide a maximum of 5 activities or places to visit per day.
""")

# def generate_itinerary(input_data: Dict) -> str:
#     attractions = input_data["attractions"]
#     preferences = ", ".join(input_data.get("preferences", []))
#     days = input_data["days"]
#     slots = ", ".join(input_data["slots"])

#     compact_list = "\n".join(
#         f"- {a['name']}: {', '.join(a['tags'])}" for a in attractions
#     )

#     prompt = f"""
#         Create a {days}-day itinerary using the following attractions and tags.
#         Each day should include: {slots}.
#         User preferences: {preferences}
#         Limitations: {input_data.get("limitations", "none")}

#         Attractions:
#         {compact_list}
#     """
#     response = llm.invoke([system_prompt, HumanMessage(content=prompt)])
#     logger.info(f"Itinerary generation: {response.content}")

#     if response.content.strip():
#         return response.content.strip()

#     return "Sorry, I couldn't generate the itinerary. Please try again."

def _filter_by_limitations(attractions: List[Dict], limitations: Dict, days: int) -> List[Dict]:
    if not attractions:
        return []

    # Normalize/validate input to ensure only dict attractions are processed
    normalized = []
    bad_items = []
    for i, a in enumerate(attractions):
        if isinstance(a, dict):
            normalized.append(a)
        else:
            # handle nested lists of dicts by flattening
            if isinstance(a, (list, tuple)):
                for item in a:
                    if isinstance(item, dict):
                        normalized.append(item)
                    else:
                        bad_items.append((i, type(item).__name__))
            else:
                bad_items.append((i, type(a).__name__))

    if bad_items:
        logger.debug("Skipping non-dict attraction entries (index, type): %s", bad_items)

    # Process normalized list only
    filtered = [a for a in normalized if not a.get("excluded")]

    # Filter wheelchair requirement: only keep True-accessible items when required
    if limitations.get("wheelchair_accessible"):
        filtered = [a for a in filtered if a.get("wheelchair_accessible") is True]

    # Remove night-only activities if requested (heuristics)
    if limitations.get("no_night_activities"):
        def is_night(a):
            bt = (a.get("best_time") or "").lower() if isinstance(a, dict) else ""
            tags = [t.lower() for t in (a.get("tags") or []) if isinstance(t, str)] if isinstance(a, dict) else []
            return bt == "night" or "nightlife" in tags or "night" in tags
        filtered = [a for a in filtered if not is_night(a)]

    # Apply max walking distance if distances are available
    max_walk = limitations.get("max_walking_distance_km")
    if max_walk is not None:
        try:
            mw = float(max_walk)
            filtered = [a for a in filtered if a.get("distance_km") is None or a["distance_km"] <= mw]
        except Exception:
            pass

    # Compute caps: max_total_attractions and max_per_day
    max_total = limitations.get("max_total_attractions")
    max_per_day = limitations.get("max_per_day")

    # Enforce an max per-day cap of 5 if not explicitly higher
    PER_DAY_ABSOLUTE = 5
    if isinstance(max_per_day, int) and max_per_day > 0:
        per_day_limit = min(max_per_day, PER_DAY_ABSOLUTE)
    else:
        per_day_limit = PER_DAY_ABSOLUTE

    # Determine total allowed by per-day x days
    total_by_per_day = per_day_limit * max(1, int(days))
    
    # Determine final total allowed combining max_total and per-day limit
    if isinstance(max_total, int) and max_total > 0:
        total_allowed = min(len(filtered), max_total, total_by_per_day)
    else:
        total_allowed = min(len(filtered), total_by_per_day)

    return filtered[:total_allowed]



def generate_itinerary(input_data: Dict) -> str:
    attractions = list(input_data.get("attractions") or [])
    preferences = ", ".join(input_data.get("preferences", []) or [])
    try:
        days = int(input_data.get("days", 1) or 1)
    except Exception:
        days = 1
    slots = ", ".join(input_data.get("slots", ["morning", "afternoon", "evening"]) or ["morning", "afternoon", "evening"])

    # Apply limitations-driven filtering
    limitations = input_data.get("limitations") or {}
    filtered_attractions = _filter_by_limitations(attractions, limitations, days)

    # Determine per-day limit for prompt
    max_per_day = limitations.get("max_per_day")
    per_day_prompt_limit = min(int(max_per_day) if isinstance(max_per_day, int) and max_per_day > 0 else 5, 5)

    lines = []
    for a in filtered_attractions:
        if isinstance(a, dict):
            name = a.get("name") or a.get("attraction") or str(a)
            tags = a.get("tags") or a.get("categories") or []
            tags_str = ", ".join(tags) if isinstance(tags, (list, tuple)) else str(tags)
            lines.append(f"- {name}: {tags_str}")
        else:
            lines.append(f"- {str(a)}")
    compact_list = "\n".join(lines) if lines else "(no attractions provided)"

    prompt = f"""
        Create a {days}-day itinerary using the following attractions and tags.
        Each day should include: {slots}.
        User preferences: {preferences}
        Limitations: {limitations or 'none'}
        Please provide up to {per_day_prompt_limit} activities per day and distribute activities evenly across days.

        Attractions:
        {compact_list}
        """

    # Call LLM and normalize different response shapes
    try:
        try:
            response = llm.invoke([system_prompt, HumanMessage(content=prompt)])
        except Exception:
            try:
                response = llm([system_prompt, HumanMessage(content=prompt)])
            except Exception:
                response = llm.call([system_prompt, HumanMessage(content=prompt)]) if hasattr(llm, "call") else None
    except Exception as exc:
        logger.exception("LLM call failed: %s", exc)
        response = None

    text = ""
    if response is None:
        text = ""
    elif isinstance(response, str):
        text = response
    elif hasattr(response, "content"):
        text = getattr(response, "content") or ""
    elif isinstance(response, dict):
        text = response.get("text") or response.get("content") or ""
    else:
        try:
            text = str(response)
        except Exception:
            text = ""

    text = text.strip()
    if text:
        logger.info("Itinerary generated (len=%d) attractions_used=%d", len(text), len(filtered_attractions))
        return text

    logger.warning("Itinerary generation returned no text")
    return "Sorry, I couldn't generate the itinerary. Please try again."
