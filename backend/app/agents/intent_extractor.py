"""
ActOS — Intent Extraction Engine
Blueprint: LangChain + OpenAI to parse Tamil/Tanglish/English commands into structured intent
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import settings, get_llm
from loguru import logger
import json


INTENT_PROMPT = """
You are ActOS, an AI Voice Operating System that understands Tamil, Tanglish (Tamil+English mixed),
English, Hindi, Telugu and Malayalam commands.

Extract structured intent from the user's voice command.

User command: "{command}"

Return ONLY valid JSON in this exact format:
{{
  "intent": "send_message | open_browser | search | make_call | play_music | set_reminder | book_service | open_app | scroll | fill_form | other",
  "app": "whatsapp | chrome | gmail | youtube | spotify | maps | instagram | calendar | notes | uber | zomato | amazon | other",
  "action": "specific action verb",
  "target": "contact name, URL, search query, or app name",
  "params": {{
    "contact": "name if messaging/calling",
    "message": "message text if sending",
    "url": "URL if browsing",
    "query": "search query if searching",
    "time": "time if scheduling",
    "location": "location if maps/booking"
  }},
  "language": "tamil | tanglish | english | hindi | mixed",
  "requires_auth": true or false,
  "confidence": 0.0 to 1.0
}}

Examples:
- "Dei WhatsApp la poyi Ravi ku hi nu oru message podu"
  → intent: send_message, app: whatsapp, target: Ravi, params.message: "hi", requires_auth: true

- "Chrome open panni Amazon la headphones search pannu"
  → intent: search, app: chrome, target: amazon.com, params.query: "headphones"

- "YouTube la AR Rahman songs play pannu"
  → intent: play_music, app: youtube, params.query: "AR Rahman songs"
"""


class IntentExtractor:
    """
    LangChain-powered intent extraction.
    Converts natural Tamil/Tanglish/English speech into structured JSON intent.
    """

    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.parser = JsonOutputParser()
        self.prompt = ChatPromptTemplate.from_template(INTENT_PROMPT)
        self.chain = self.prompt | self.llm | self.parser

    async def extract(self, command: str) -> dict:
        """Extract intent from voice command text."""
        logger.info(f"Extracting intent from: '{command}'")
        try:
            result = await self.chain.ainvoke({"command": command})
            logger.info(f"Intent: {result.get('intent')} | App: {result.get('app')} | Target: {result.get('target')}")
            return result
        except Exception as e:
            logger.error(f"Intent extraction failed: {e}")
            return {"intent": "unknown", "app": "other", "action": "unknown", "target": "", "params": {}, "requires_auth": False, "confidence": 0.0}


intent_extractor = IntentExtractor()
