# Travel Planner

A multi agent-based travel-planning prototype that:
- Geocodes a destination
- Discovers attractions
- Tags attractions
- Filters by user preferences
- Generates a day-by-day itinerary

Built around a simple state graph (orchestrator.py) that composes modular agents.

Project structure
- README.md
- .env
- main.py
- orchestrator.py
- state_schema.py
- requirements.txt
- agents/
  - geocoder_agent.py
  - discovery_agent.py
  - tagging_agent.py
  - itinerary_agent.py
- tools/
  - geocoder.py
  - geoapify_client.py
- utils/
  - input.py
  - logger.py


Setup
1. Setup Python virtual environment:
    ```sh
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    source .venv/bin/activate
    ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Provide API keys as environment variables:
   - OPENAI_API_KEY (generate from https://platform.openai.com/)
   - GEOAPIFY_API_KEY (generate from https://www.geoapify.com/ [free tier])

Run
```sh
python main.py
```
The CLI will prompt for destination, number of days, and preferences, then run the composed workflow (see `orchestrator.build_travel_graph`).

Notes
- Network calls (Geoapify, geocoding) require valid API credentials and internet access.
- The project expects environment variables for secrets rather than committed secret files.
- Refer to individual modules in `agents/`, `tools/`, and `state_schema.py` to modify behaviour or state shape.

