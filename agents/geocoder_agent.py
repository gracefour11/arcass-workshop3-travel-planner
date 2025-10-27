# agents/geocoder_agent.py

import logging
from tools.geocoder import geocode_city  # your existing tool
from typing import Optional, Dict
from utils.logger import get_logger
logger = get_logger("geocoder_agent", level=logging.DEBUG)

def geocoder_agent(destination: str, country: Optional[str] = None) -> Dict:
    if not destination or not isinstance(destination, str):
        return {
            "lat": None,
            "lon": None,
            "error": "geocoder_agent: missing or invalid destination"
        }

    lat, lon = geocode_city(destination, country)
    logger.info(f"Geocoded '{destination}' (country: '{country}') to lat: {lat}, lon: {lon}")
    if lat is None or lon is None:
        return {
            "lat": None,
            "lon": None,
            "error": f"geocoder_agent: failed to geocode '{destination}'"
        }

    return {
        "lat": lat,
        "lon": lon,
        "city": destination,
        "country": country
    }