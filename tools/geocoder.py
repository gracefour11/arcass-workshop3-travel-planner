import requests

def geocode_city(city_name: str):
    print(f"🌍 Geocoding '{city_name}' with Nominatim...")
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "DevTravelPlanner/1.0"}  # Required by Nominatim
    res = requests.get(url, params=params, headers=headers, timeout=10)
    res.raise_for_status()
    data = res.json()
    if not data:
        raise ValueError(f"No coordinates found for city: {city_name}")
    return float(data[0]["lat"]), float(data[0]["lon"])