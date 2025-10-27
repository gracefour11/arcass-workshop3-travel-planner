# orchestrator.py
import logging
from langgraph.graph import StateGraph
from langchain_core.runnables.config import RunnableConfig
from agents.geocoder_agent import geocoder_agent  
from agents.discovery_agent import attraction_discovery_agent  
from agents.tagging_agent import tag_attraction
from agents.itinerary_agent import generate_itinerary
from state_schema import TravelState
from utils.logger import get_logger

MAX_RETRIES = 3
logger = get_logger("orchestrator", level=logging.DEBUG)

def retry_node(fn, key):
    def wrapper(state):
        for attempt in range(MAX_RETRIES):
            try:
                result = fn(state)
                if result.get(key):
                    return result
            except Exception:
                continue
        return {key: None}
    return wrapper

def build_travel_graph():
    graph = StateGraph(TravelState)

    # Step 1: Geocode
    def geocode_node(state):
        location = geocoder_agent(state["destination"])
        return {"location": location}

    # Step 2: Discover attractions
    def discover_node(state):
        result = attraction_discovery_agent(state["location"])
        return {"raw_attractions": result["attractions"]}

    # Step 3: Tag attractions (new)
    def tag_node(state):
        attractions = state.get("raw_attractions", [])
        tagged = [tag_attraction(a) for a in attractions]
        return {"tagged_attractions": tagged}
    
    # Step 4: Generate itinerary (refactored)
    def itinerary_node(state):
        input_data = {
            "days": state["days"],
            "slots": state["slots"],
            "preferences": state.get("preferences", []),
            "attractions": state["tagged_attractions"]
        }
        itinerary = generate_itinerary(input_data)
        return {"itinerary": itinerary}

    # Register nodes
    graph.add_node("geocode", geocode_node)
    graph.add_node("discover", discover_node)
   
    graph.add_node("tag", tag_node)
    graph.add_node("plan", itinerary_node)
     # graph.add_node("tag", retry_node(tag_node, "tagged_attractions"))
    # graph.add_node("plan", retry_node(itinerary_node, "itinerary"))

    # Define flow
    graph.set_entry_point("geocode")
    graph.add_edge("geocode", "discover")
    graph.add_edge("discover", "tag")
    graph.add_edge("tag", "plan")

    return graph.compile()

def run_orchestrator(user_input):
    graph = build_travel_graph()
    config = RunnableConfig()
    result = graph.invoke({
        "destination": user_input["destination"],
        "days": user_input["days"],
        "slots": ["morning", "afternoon", "evening"],
        "preferences": user_input.get("preferences", [])
    }, config)

    if not result.get("itinerary"):
        return "Sorry, itinerary generation failed after multiple attempts."
    return result["itinerary"]