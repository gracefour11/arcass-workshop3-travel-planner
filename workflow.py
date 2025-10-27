from langgraph.graph import StateGraph, END
from agents.geocoder_agent import geocoder_agent
from agents.discovery_agent import attraction_discovery_agent
from agents.preference_filter_agent import preference_filter_agent
from agents.itinerary_agent import itinerary_agent
from state_schema import TravelState

def build_graph():
    graph = StateGraph(TravelState)

    # Agent nodes
    graph.add_node("geocode", geocoder_agent)
    graph.add_node("discover", attraction_discovery_agent)
    graph.add_node("filter", preference_filter_agent)
    graph.add_node("itinerary", itinerary_agent)

    # Flow
    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "discover")
    graph.add_edge("discover", "filter")
    graph.add_edge("filter", "itinerary")
    graph.add_edge("itinerary", END)
    return graph.compile()