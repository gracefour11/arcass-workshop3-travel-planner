from typing import List, TypedDict


class TravelState(TypedDict):
    destination: str
    days: int
    slots: List[str]
    preferences: List[str]
    location: dict
    raw_attractions: List[dict]
    tagged_attractions: List[dict]
    itinerary: str