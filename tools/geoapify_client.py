import requests
from dotenv import load_dotenv
import os

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# 🗺️ Places: Discover attractions near lat/lon
def get_geoapify_attractions(city_name, lat, lon, radius=10000, limit=30):
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": "tourism",
        "filter": f"circle:{lon},{lat},{radius}",
        "limit": limit,
        "apiKey": GEOAPIFY_API_KEY,
        "lang": "en"
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        features = data.get("features", [])
        attractions = []
        for f in features:
            props = f.get("properties", {})
            attractions.append({
                "name": props.get("name:en") or props.get("name"),
                "address": f"{props.get('address_line1', '')}, {props.get('address_line2', '')}",
                "coordinates": {
                    "lat": f["geometry"]["coordinates"][1],
                    "lon": f["geometry"]["coordinates"][0]
                },
                "website": props.get("website"),
                "opening_hours": props.get("opening_hours"),
                "categories": props.get("categories", [])
            })
        return attractions
    except Exception as e:
        print(f"❌ Geoapify Places request failed: {e}")
        return []