from tools.geoapify_client import get_geoapify_attractions

def attraction_discovery_agent(state):
    print(f"📍 Discovering attractions in {state['city']}...")
    attractions = get_geoapify_attractions(state["city"], state["lat"], state["lon"])
    state["attractions"] = attractions
    print(f"attractions: {attractions}")
    return state