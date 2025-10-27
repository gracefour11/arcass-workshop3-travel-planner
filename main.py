from state_schema import TravelState
from workflow import build_graph
from utils.input import prompt_input

def get_user_input():
    city = prompt_input("Enter your destination city: ")
    days = int(prompt_input("Enter number of travel days: "))
    prefs = prompt_input("Enter your travel preferences (comma-separated, e.g., nature, food, history): ")
    preferences = [p.strip().lower() for p in prefs.split(",") if p.strip()]

    return TravelState(
        city=city,
        days=days,
        preferences=preferences,
        lat=None,
        lon=None,
        attractions=None,
        filtered_attractions=None,
        itinerary=None
    )


def main():
    try:
        state = get_user_input()
        graph = build_graph()
        final_state = graph.invoke(state)

        print("\n🗺️ Final Travel Plan:")
        print(f"Destination: {final_state['city']}")
        print(f"Days: {final_state['days']}")
        print("\n🗓️ Itinerary:\n")
        for a in final_state["filtered_attractions"]:
            print(f"- {a['name']}")
            print(f"  📍 {a['address']}")
            print(f"  📝 {a.get('summary', 'No summary')}")
            print(f"  🏷️ Tags: {a.get('tags', [])}")
            print()
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()