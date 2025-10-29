from tools.geoapify_client import get_geoapify_attractions

# def attraction_discovery_agent(state):
#     print(f"📍 Discovering attractions in {state['city']}...")
#     attractions = get_geoapify_attractions(state["city"], state["lat"], state["lon"])
#     state["attractions"] = attractions
#     print(f"attractions: {attractions}")
#     return state

def attraction_discovery_agent(location, limit=None, limitations=None):
    # support being passed either a state dict or a simple city string
    city = None
    lat = None
    lon = None
    if isinstance(location, dict):
        city = location.get("city") or location.get("name") or location.get("destination")
        lat = location.get("lat") or location.get("latitude")
        lon = location.get("lon") or location.get("lng") or location.get("longitude")
    else:
        city = str(location)

    # Normalize limitations to a dict to prevent AttributeError when caller passes a list/string
    def _normalize_limitations(lim):
        if lim is None:
            return {}
        if isinstance(lim, str):
            try:
                import json
                parsed = json.loads(lim)
                lim = parsed if isinstance(parsed, dict) else [lim]
            except Exception:
                lim = [lim]
        if isinstance(lim, list):
            def tok(t):
                t = str(t).strip().lower()
                if t.startswith("avoid:"):
                    t = t.split(":",1)[1]
                if t.startswith("no "):
                    t = t[3:]
                return t.replace("no_", "").replace("avoid_", "").strip()
            return {"avoid_categories": [tok(x) for x in lim]}
        if isinstance(lim, dict):
            avoid = lim.get("avoid_categories") or lim.get("avoid") or []
            if isinstance(avoid, (list, tuple)):
                return {"avoid_categories": [str(a).strip().lower().replace("no_","").replace("avoid_","").replace("no ","").replace("avoid:","") for a in avoid]}
            return lim
        return {}

    limitations = _normalize_limitations(limitations)

    print(f"📍 Discovering attractions in {city}...")
    attractions = get_geoapify_attractions(city, lat, lon) or []

    # Apply limitations (if provided)
    if limitations:
        avoid = set(limitations.get("avoid_categories", []))
        if avoid:
            attractions = [a for a in attractions if not (set([c.lower() for c in a.get("categories", [])]) & avoid)]
        max_walk_km = limitations.get("max_walking_distance_km")
        if max_walk_km is not None:
            try:
                max_walk_km = float(max_walk_km)
                attractions = [a for a in attractions if a.get("distance_km") is None or a["distance_km"] <= max_walk_km]
            except Exception:
                pass

    # Apply an explicit limit (if provided)
    if limit is not None:
        try:
            n = int(limit)
            if n >= 0:
                attractions = attractions[:n]
        except Exception:
            pass

    return {"attractions": attractions}
