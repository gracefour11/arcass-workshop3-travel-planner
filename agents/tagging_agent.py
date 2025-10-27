# agents/tagging_agent.py

import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("tagging_agent", level=logging.DEBUG)


# Initialize LLM
llm = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    # max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "128"))
)

# Optional system prompt to guide consistent tagging
system_prompt = SystemMessage(content="""
You are a semantic tagging assistant for travel attractions. Your job is to analyze each attraction and return a comma-separated list of descriptive tags that reflect its appeal, audience, and experience type.

Use tags like:
- entertainment
- historical
- sightseeing
- indoor
- outdoor
- adventurous
- educational

Only return the tags. Do not explain or format them.
""")

def tag_attraction(attraction: Dict) -> Dict:
    name = attraction.get("name", "")
    categories = ", ".join(attraction.get("categories", []))
    # features = ", ".join(attraction.get("features", []))

    logger.info(f"Tagging attraction: {name}")

    prompt = f"""
    Name: {name}
    Categories: {categories}
    Based on the above information, provide a list of relevant tags from system prompt for this attraction.
    """

    response = llm.invoke([system_prompt, HumanMessage(content=prompt)])
    logger.info(f"Response for tagging: {response.content}")

    tags = [tag.strip() for tag in response.content.split(",")]
    logger.info(f"Tags generated: {tags}")

    return {**attraction, "tags": tags}