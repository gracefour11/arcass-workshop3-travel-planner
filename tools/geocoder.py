import requests
from typing import Optional, Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def _build_query(city: str, country: Optional[str]) -> str:
    if country:
        return f"{city}, {country}"
    return city

def geocode_city(city: str, country: Optional[str] = None, timeout: int = 10) -> Tuple[Optional[float], Optional[float]]:
    """
    Geocode a city (optionally with country) using Nominatim.
    Returns (lat, lon) as floats or (None, None) on failure.
    Raises on network-level errors.
    """
    if not city:
        return (None, None)

    q = _build_query(city.strip(), country.strip() if country else None)
    params = {
        "q": q,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    headers = {"User-Agent": "travel-planner/1.0 (contact@example.com)"}  # replace contact if needed

    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return (None, None)

    first = data[0]
    try:
        lat = float(first.get("lat"))
        lon = float(first.get("lon"))
        return (lat, lon)
    except Exception:
        return (None, None)