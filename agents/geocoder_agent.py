from tools.geocoder import geocode_city

def geocoder_agent(state):
    city = state["city"]
    lat, lon = geocode_city(city)
    state["lat"] = lat
    state["lon"] = lon
    return state