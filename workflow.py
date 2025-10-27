from langgraph.graph import StateGraph, END
from agents.geocoder_agent import geocoder_agent
from agents.discovery_agent import attraction_discovery_agent
from agents.preference_filter_agent import preference_filter_agent
from agents.itinerary_agent import itinerary_agent
from tools.wikipedia_client import get_summary_from_wikipedia
from state_schema import TravelState

# Optional inline enrichment node
def enrich_node(state):
    print("📚 Enriching attractions with Wikipedia summaries...")
    for a in state["attractions"]:
        a["summary"] = get_summary_from_wikipedia(a["name"])
    return state

def build_graph():
    graph = StateGraph(TravelState)

    # Agent nodes
    graph.add_node("geocode", geocoder_agent)
    graph.add_node("discover", attraction_discovery_agent)
    # graph.add_node("enrich", enrich_node)
    graph.add_node("filter", preference_filter_agent)
    graph.add_node("itinerary", itinerary_agent)

    # Flow
    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "discover")
    # graph.add_edge("discover", "enrich")
    # graph.add_edge("enrich", "filter")
    # graph.add_edge("filter", "itinerary")
    # graph.add_edge("itinerary", END)
    graph.add_edge("discover", "filter")
    graph.add_edge("filter", "itinerary")
    graph.add_edge("itinerary", END)
    return graph.compile()