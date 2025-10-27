from typing import TypedDict, List, Optional

class TravelState(TypedDict):
    city: str
    days: int
    preferences: List[str]
    lat: Optional[float]
    lon: Optional[float]
    attractions: Optional[List[dict]]
    filtered_attractions: Optional[List[dict]]
    itinerary: Optional[str]