# from state_schema import TravelState
# from workflow import build_graph
# from utils.input import prompt_input
# from typing import Any

# def get_user_input():
#     # country is now requested before city and is mandatory
#     country = ""
#     while not country:
#         country = prompt_input("Enter destination country (name or ISO code): ").strip()
#         if not country:
#             print("Country is required. Please enter a country name or ISO code.")

#     city = prompt_input("Enter your destination city: ").strip()
#     days = int(prompt_input("Enter number of travel days: "))
#     prefs = prompt_input("Enter your travel preferences (comma-separated, e.g., nature, food, history): ")
#     preferences = [p.strip().lower() for p in prefs.split(",") if p.strip()]

#     return TravelState(
#         city=city,
#         country=country,
#         days=days,
#         preferences=preferences,
#         lat=None,
#         lon=None,
#         attractions=None,
#         filtered_attractions=None,
#         itinerary=None
#     )


# def _print_activity(a):
#     print(f"- {a.get('name', 'Unknown')}")
#     if a.get("address"):
#         print(f"  📍 {a['address']}")
#     if a.get("summary"):
#         print(f"  📝 {a['summary']}")
#     if a.get("tags"):
#         print(f"  🏷️ Tags: {a['tags']}")


# def main():
#     try:
#         state = get_user_input()
#         graph = build_graph()
#         final_state = graph.invoke(state)

#         print("\n🗺️ Final Travel Plan:")
#         dest_line = final_state.get("city", "") + (f", {final_state.get('country')}" if final_state.get("country") else "")
#         print(f"Destination: {dest_line}")
#         print(f"Days: {final_state.get('days', '?')}\n")

#         itinerary = final_state.get("itinerary") or final_state.get("filtered_attractions")
#         if not itinerary:
#             print("No itinerary or attractions found.")
#             return

#         print("🗓️ Itinerary:\n")

#         # Case 1: itinerary is a list of day buckets (each bucket is a list of activities)
#         if isinstance(itinerary, list) and itinerary and isinstance(itinerary[0], list):
#             for i, day_acts in enumerate(itinerary, start=1):
#                 print(f"Day {i}:")
#                 if not day_acts:
#                     print("  (no activities)")
#                 for a in day_acts:
#                     _print_activity(a)
#                 print()

#         # Case 2: list of dicts where each dict has a 'day' key or 'day' field
#         elif isinstance(itinerary, list) and all(isinstance(x, dict) for x in itinerary):
#             # group by day if possible
#             days_map = {}
#             for item in itinerary:
#                 day = item.get("day") or item.get("day_number") or 1
#                 try:
#                     day_idx = int(day)
#                 except Exception:
#                     day_idx = 1
#                 days_map.setdefault(day_idx, []).append(item)
#             for day_idx in sorted(days_map.keys()):
#                 print(f"Day {day_idx}:")
#                 for a in days_map[day_idx]:
#                     _print_activity(a)
#                 print()

#         # Case 3: dict keyed by day labels
#         elif isinstance(itinerary, dict):
#             # try numeric sort of keys
#             def keyfn(k):
#                 try:
#                     return int(k)
#                 except Exception:
#                     return k
#             for k in sorted(itinerary.keys(), key=keyfn):
#                 print(f"Day {k}:")
#                 day_acts = itinerary[k] or []
#                 for a in day_acts:
#                     _print_activity(a)
#                 print()

#         # Fallback: single-day list of activities
#         elif isinstance(itinerary, list):
#             print("Day 1:")
#             for a in itinerary:
#                 _print_activity(a)
#             print()

#         else:
#             print("Unrecognized itinerary format. Raw output:")
#             print(itinerary)

#     except Exception as e:
#         print(f"\n❌ Error: {e}")

# if __name__ == "__main__":
#     main()


from orchestrator import run_orchestrator
from utils.input import prompt_input
from state_schema import TravelState
def get_user_input():
    city = prompt_input("Enter your destination city: ").strip()
    days = int(prompt_input("Enter number of travel days: "))
    prefs = prompt_input("Enter your travel preferences (comma-separated, e.g., nature, food, history): ")
    preferences = [p.strip().lower() for p in prefs.split(",") if p.strip()]

    # read raw limitations from user
    limitations_raw = prompt_input("Enter your travel limitations (comma-separated, e.g., avoid:bars, no_night_activities, max_walking_distance_km, max_total_attractions, max_per_day): ").strip()
    raw_tokens = [l.strip().lower() for l in limitations_raw.split(",") if l.strip()]

    def _normalize_token(tok: str) -> str:
        # support "no X", "no_x", "avoid:X", "avoid_x"
        tok = tok.strip().lower()
        if tok.startswith("avoid:"):
            tok = tok.split(":", 1)[1].strip()
        if tok.startswith("no "):
            tok = tok[3:].strip()
        tok = tok.replace("no_", "").replace("avoid_", "")
        return tok

    if raw_tokens:
        avoid_list = [_normalize_token(t) for t in raw_tokens]
        limitations = {"avoid_categories": avoid_list}
    else:
        limitations = {}

    return TravelState(
        destination = city,
        days = days,
        slots = None,
        preferences = preferences,
        location = None,
        raw_attractions = None,
        tagged_attractions = None,
        itinerary = None,
        limitations = limitations
    )


# TODO: replace user_input with get_user_input()
# user_input = {
#     "destination": "Singapore",
#     "days": 5,
#     "preferences": ["nature", "educational"]
# }

itinerary = run_orchestrator(get_user_input())
print(itinerary)