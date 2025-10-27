from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SYSTEM_PROMPT = """
You are a modular travel planning agent. Your job is to generate a reliable, user-friendly itinerary based on city, preferences, and number of days. You must:

1. Use the provided attractions. Generate a brief summary of each attractions.
2. Group them by geographic proximity.
3. Ensure each day has 2–4 attractions.
4. Return a structured itinerary grouped by day, with each attraction's title and summary.
5. Do not have repeat attractions in the itinerary.
"""


llm = ChatOpenAI(
    model="gpt-5-nano",
    api_key=OPENAI_API_KEY,
    temperature=1,
    max_retries=2
)

itinerary_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "City: {city}\nDays: {days}\nAttractions:\n{attractions}\nPreferences:\n{preferences}")
])


itinerary_chain = itinerary_prompt | llm

def itinerary_agent(state):
    attractions = state.get("filtered_attractions", [])
    if not attractions:
        state["itinerary"] = "No attractions available."
        return state

    formatted_attractions = "\n".join([
        f"- {a['name']}: {a.get('summary', '')}" for a in attractions
    ])

    response = itinerary_chain.invoke({
        "city": state["city"],
        "days": state["days"],
        "preferences": ", ".join(state["preferences"]),
        "attractions": formatted_attractions
    })

    state["itinerary"] = response.content.strip()
    return state