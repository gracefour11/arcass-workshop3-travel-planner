from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are a semantic tagger for a list of tourist attractions.
1. For each attraction name, assign tags from this list: food, nature, history, culture, architecture, shopping, entertainment. 
2. Use common knowledge and context clues.
3. Remove duplicates from the list.
4. By default, include food in the list.
5. Sort the list by user preference first followed by default preference.
6. Return a JSON list of filtered attractions with their name and tags.
"""

llm = ChatOpenAI(
    model="gpt-5-nano",
    api_key=OPENAI_API_KEY,
    temperature=1,
    max_retries=2
)

tagging_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "User preferences: {preferences}\nAttractions:\n{attractions}")
])

tagging_chain = tagging_prompt | llm

def preference_filter_agent(state):
    print("🎯 Filtering attractions based on preferences...")
    user_prefs = set(state["preferences"])
    attractions = state.get("attractions", [])
    print(f"🎯 user preferences: {user_prefs}")
    print(f"🎯 attractions: {attractions}")

    # Format attraction names for batch prompt
    attraction_names = [a["name"] for a in attractions]
    formatted_list = "\n".join([f"- {name}" for name in attraction_names])
    prefs_str = ", ".join(user_prefs)
    print(f"🎯 formatted_list: {formatted_list}")
    print(f"🎯 prefs_str: {prefs_str}")
    # Invoke LLM once for all attractions
    response = tagging_chain.invoke({
        "preferences": prefs_str,
        "attractions": formatted_list
    })

    try:
        tagged = json.loads(response.content)
    except Exception as e:
        print(f"⚠️ Failed to parse LLM response: {e}")
        tagged = [{"name": a["name"], "tags": []} for a in attractions]

    # Merge tags back into attractions
    tag_map = {a["name"]: a["tags"] for a in tagged}
    for a in attractions:
        a["tags"] = tag_map.get(a["name"], [])

    # Filter by user preferences
    filtered = [a for a in attractions if user_prefs.intersection(set(a.get("tags", [])))]
    state["filtered_attractions"] = filtered
    return state