# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
# import os
# import json
# import re
# import time
# import logging
# from typing import Any, List, Dict

# # replace inline logger setup with utils helper
# from utils.logger import get_logger

# load_dotenv()

# # Simple configurable limits
# MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano")
# MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "128"))
# MAX_ATTRACTIONS = int(os.getenv("ITINERARY_MAX_ATTRACTIONS", "12"))

# SYSTEM_PROMPT = """
# You are a travel-planning assistant. Reply in English only and return valid JSON with a single top-level key named "itinerary".
# The "itinerary" value must be an object that maps day labels in the format of "Day <number>" starting from 1 to arrays of activity objects.
# Each activity object must include:
# - attraction: the attraction name (string),
# - summary: a one- or two-sentence description (string),
# - location: an address or area (string),
# - website: a website URL or null.
# When splitting the activities into days, try to balance the number of activities per day as evenly as possible. Group the activities by proximity or theme where possible.
# Do not include any other top-level keys or explanatory text. Return only the JSON object.
# """

# HUMAN_TEMPLATE = "City: {city}\nDays: {days}\nPreferences: {preferences}\nAttractions: {attractions}\n\nRespond with the exact JSON shape described."

# llm = ChatOpenAI(model=MODEL, temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")), max_tokens=MAX_TOKENS)
# prompt = ChatPromptTemplate.from_messages([
#     ("system", SYSTEM_PROMPT),
#     ("human", HUMAN_TEMPLATE),
# ])
# chain = prompt | llm

# # use shared helper; choose desired level (DEBUG to see debug+info)
# logger = get_logger(__name__, level=logging.DEBUG)


# def _get(state: Any, k: str, default=None):
#     return state.get(k, default) if isinstance(state, dict) else getattr(state, k, default)


# def _set(state: Any, k: str, v):
#     if isinstance(state, dict):
#         state[k] = v
#     else:
#         try:
#             state[k] = v
#         except Exception:
#             setattr(state, k, v)


# def _extract_json(text: str) -> Dict:
#     if not text:
#         return None
#     # strip fences and leading commentary
#     t = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
#     t = re.sub(r"```$", "", t, flags=re.I).strip()
#     t = re.sub(r"(?i)^response[:\s]*", "", t).strip()
#     # try normal json
#     try:
#         o = json.loads(t)
#         if isinstance(o, dict) and "itinerary" in o:
#             return o
#     except Exception:
#         pass
#     # try replacing single quotes (last resort)
#     try:
#         alt = re.sub(r"(?<!\\)'", '"', t)
#         o = json.loads(alt)
#         if isinstance(o, dict) and "itinerary" in o:
#             return o
#     except Exception:
#         pass
#     return None


# def _normalize_itinerary_json(obj: Dict, days: int) -> List[Dict]:
#     if not isinstance(obj, dict):
#         return None
#     itin = obj.get("itinerary")
#     if not isinstance(itin, dict):
#         return None
#     final = [{"day": i + 1, "activities": []} for i in range(days)]
#     non_numeric = []
#     for key, acts in itin.items():
#         m = re.search(r"(\d+)", str(key))
#         if m:
#             idx = max(0, min(days - 1, int(m.group(1)) - 1))
#         else:
#             non_numeric.append(acts)
#             continue
#         if not isinstance(acts, list):
#             continue
#         for a in acts:
#             if isinstance(a, dict):
#                 name = a.get("attraction") or a.get("name") or "Unknown"
#                 summary = a.get("summary") or ""
#                 location = a.get("location") or a.get("address") or ""
#                 website = a.get("website") or a.get("url") or None
#             else:
#                 name = str(a); summary = ""; location = ""; website = None
#             final[idx]["activities"].append({
#                 "name": name,
#                 "address": location,
#                 "summary": summary,
#                 "tags": [],
#                 "website": website
#             })
#     # place non-numeric buckets sequentially
#     slot = 0
#     for acts in non_numeric:
#         while slot < days and final[slot]["activities"]:
#             slot += 1
#         if slot >= days:
#             break
#         if isinstance(acts, list):
#             for a in acts:
#                 if isinstance(a, dict):
#                     name = a.get("attraction") or a.get("name") or "Unknown"
#                     summary = a.get("summary") or ""
#                     location = a.get("location") or a.get("address") or ""
#                     website = a.get("website") or a.get("url") or None
#                 else:
#                     name = str(a); summary = ""; location = ""; website = None
#                 final[slot]["activities"].append({
#                     "name": name,
#                     "address": location,
#                     "summary": summary,
#                     "tags": [],
#                     "website": website
#                 })
#         slot += 1
#     return final


# def _distribute_evenly(items: List[Any], days: int) -> List[Dict]:
#     buckets = [[] for _ in range(days)]
#     for i, it in enumerate(items):
#         buckets[i % days].append(it)
#     result = []
#     for i in range(days):
#         acts = []
#         for it in buckets[i]:
#             if isinstance(it, dict):
#                 acts.append({
#                     "name": it.get("name") or it.get("attraction") or "Unknown",
#                     "address": it.get("address") or "",
#                     "summary": it.get("summary") or "",
#                     "tags": [],
#                     "website": it.get("website") or None
#                 })
#             else:
#                 acts.append({"name": str(it), "address": "", "summary": "", "tags": [], "website": None})
#         result.append({"day": i + 1, "activities": acts})
#     return result


# def itinerary_agent(state: Any) -> Any:
#     start = time.time()
#     days = int(_get(state, "days", 1) or 1)
#     raw = _get(state, "filtered_attractions") or _get(state, "attractions") or []
#     logger.info("itinerary_agent start: city=%s days=%s attractions=%d", _get(state, "city", ""), days, len(raw))

#     if not raw:
#         empty = [{"day": i + 1, "activities": []} for i in range(days)]
#         _set(state, "itinerary", empty)
#         logger.info("itinerary_agent end (no attractions) duration=%.3fs", time.time() - start)
#         return state

#     selected = raw[:MAX_ATTRACTIONS]
#     try:
#         attractions_json = json.dumps(selected, ensure_ascii=False, indent=2)
#     except Exception:
#         # simplest coercion
#         attractions_json = json.dumps([str(a) for a in selected], ensure_ascii=False)

#     prompt_inputs = {
#         "city": _get(state, "city", ""),
#         "days": days,
#         "preferences": ", ".join(_get(state, "preferences", []) or []),
#         "attractions": attractions_json
#     }

#     try:
#         logger.info("Invoking LLM for itinerary...")
#         t0 = time.time()
#         result = chain.invoke(prompt_inputs)
#         logger.debug("LLM raw output: %s", str(result))
#         llm_time = time.time() - t0
#         logger.info("LLM call completed in %.3fs", llm_time)

#         result_text = result.get("text") if isinstance(result, dict) else str(result)
#         parsed = _extract_json(result_text or "")
#         normalized = _normalize_itinerary_json(parsed, days) if parsed else None

#         if not normalized:
#             logger.warning("LLM output not usable; falling back to even distribution")
#             normalized = _distribute_evenly(selected, days)

#         _set(state, "itinerary", normalized)
#         logger.info("itinerary_agent completed in %.3fs", time.time() - start)
#         return state

#     except Exception as exc:
#         logger.exception("itinerary_agent error: %s", exc)
#         _set(state, "error", f"itinerary_agent: {type(exc).__name__}: {exc}")
#         fallback = _distribute_evenly(selected, days)
#         _set(state, "itinerary", fallback)
#         return state



# agents/itinerary_agent.py

import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("itinerary_agent", level=logging.DEBUG)


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.2,
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

Avoid duplicates. Prioritize attractions that match user preferences. Use tags to guide pacing and variety. Format clearly by day and time slot. Evenly distribute activities across days.
""")

def generate_itinerary(input_data: Dict) -> str:
    attractions = input_data["attractions"]
    preferences = ", ".join(input_data.get("preferences", []))
    days = input_data["days"]
    slots = ", ".join(input_data["slots"])

    compact_list = "\n".join(
        f"- {a['name']}: {', '.join(a['tags'])}" for a in attractions
    )

    prompt = f"""
Create a {days}-day itinerary using the following attractions and tags.
Each day should include: {slots}.
User preferences: {preferences}

Attractions:
{compact_list}
"""
    response = llm.invoke([system_prompt, HumanMessage(content=prompt)])
    logger.info(f"Itinerary generation: {response.content}")

    if response.content.strip():
        return response.content.strip()

    return "Sorry, I couldn't generate the itinerary. Please try again."