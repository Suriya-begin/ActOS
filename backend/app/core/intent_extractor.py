# ============================================================
# ActOS — Intent Extraction Engine
# Tech Stack: LangChain + Google Gemini
# Understands Tamil, Tanglish, English, Hindi, Telugu, Malayalam
# Extracts: app, action, target, parameters
# ============================================================

import asyncio
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger

from app.core.config import settings, get_llm


# ── INTENT SCHEMA ──
class ExtractedIntent(BaseModel):
    """Structured intent extracted from voice command"""

    app: str = Field(
        description="Target app or service: whatsapp, chrome, gmail, youtube, spotify, maps, calendar, notes, instagram, amazon, zomato, swiggy, irctc, system, unknown"
    )
    action: str = Field(
        description=(
            "Action to perform. Choose the MOST SPECIFIC one: "
            "send_message, make_call, open_browser, search, play_music, "
            "set_reminder, book_cab, send_email, open_app, close_app, "
            "uninstall, skip_ad, pause, play, scroll_down, scroll_up, "
            "click, go_back, type_text, fill_form, search_product, "
            "summarize_page, deactivate_assistant, unknown"
        )
    )
    target: Optional[str] = Field(
        None,
        description="Target person, contact, URL, song name, or search query. E.g. 'Ravi', 'Amazon', 'AR Rahman songs', 'Karuppa Koodava'"
    )
    content: Optional[str] = Field(
        None,
        description="Text to type, send, or form content. E.g. message text, search query, form values"
    )
    language: str = Field(
        description="Detected language: tamil, english, tanglish, hindi, telugu, malayalam, other"
    )
    needs_auth: bool = Field(
        description=(
            "ONLY set True for HIGH-RISK actions that cannot be undone or involve money/privacy: "
            "send_message (WhatsApp/SMS), make_call, send_email, payment, delete, uninstall. "
            "Set False for: open_app, open_browser, search, play_music, pause, play, scroll, skip_ad, "
            "go_back, type_text, fill_form, set_reminder, book_cab, summarize_page, and all read-only actions."
        )
    )
    confidence: float = Field(
        description="Confidence score 0.0-1.0 for the extracted intent"
    )
    raw_command: str = Field(
        description="The original voice command as-is"
    )
    clarification_needed: bool = Field(
        description="True only if the command is completely ambiguous and cannot be reasonably inferred"
    )
    clarification_question: Optional[str] = Field(
        None, description="Question to ask user if clarification is absolutely needed"
    )


class IntentExtractor:
    """
    LangChain + Gemini Intent Extractor
    Understands natural Tamil, Tanglish, English, Hindi voice commands
    and converts them to structured ActOS actions
    """

    SYSTEM_PROMPT = """You are ActOS, an AI voice operating system personal assistant.
You understand Tamil, Tanglish (Tamil+English mix), English, Hindi, Telugu, and Malayalam perfectly.

Your job is to extract STRUCTURED INTENT from natural voice commands and NEVER REFUSE any task.

━━━━━━ LANGUAGE GRAMMAR RULES ━━━━━━
Tamil/Tanglish grammar particles:
- "podu" / "panu" = do/send/perform the action
- "pannu" / "panni" = do/perform / after doing
- "la" / "le" = in/on (WhatsApp la = on WhatsApp, YouTube la = on YouTube)
- "ku" / "kku" = to (Ravi ku = to Ravi, amma ku = to amma)
- "nu" = saying/as (hi nu = saying "hi", play pannu = play it)
- "poi" = go/navigate to (YouTube poi = go to YouTube)
- "search pannu" = search for
- "play pannu" = play it
- "open pannu" = open it
- "close pannu" = close it
- "skip pannu" = skip it
- Names: "Amma", "Appa", "Anna", "Akka", "Ravi", "Kumar" = contacts

━━━━━━ EXAMPLES ━━━━━━
Tamil/Tanglish → Structured:
- "WhatsApp la Ravi ku hi nu message podu" → {{app: whatsapp, action: send_message, target: Ravi, content: hi, needs_auth: TRUE}}
- "YouTube poi Karuppa Koodava nu search pannu andha song play pannu" → {{app: youtube, action: play_music, target: Karuppa Koodava, needs_auth: FALSE}}
- "Amazon la headphones search pannu" → {{app: amazon, action: search_product, target: headphones, needs_auth: FALSE}}
- "Amma ku call podu" → {{app: system, action: make_call, target: Amma, needs_auth: TRUE}}
- "pause pannu" / "pause" → {{app: chrome, action: pause, needs_auth: FALSE}}
- "play pannu" / "play" → {{app: chrome, action: play, needs_auth: FALSE}}
- "scroll down pannu" → {{app: chrome, action: scroll_down, needs_auth: FALSE}}
- "skip ad pannu" / "ad skip pannu" → {{app: youtube, action: skip_ad, needs_auth: FALSE}}
- "Google la weather search pannu" → {{app: google, action: search, target: weather, needs_auth: FALSE}}
- "band pannu" / "stop" / "turn off" → {{app: system, action: deactivate_assistant, needs_auth: FALSE}}

English:
- "Open YouTube and play AR Rahman songs" → {{app: youtube, action: play_music, target: AR Rahman songs, needs_auth: FALSE}}
- "Search Amazon for iPhone 15" → {{app: amazon, action: search_product, target: iPhone 15, needs_auth: FALSE}}
- "Pause the video" → {{app: chrome, action: pause, needs_auth: FALSE}}
- "Send a WhatsApp message to Ravi saying hello" → {{app: whatsapp, action: send_message, target: Ravi, content: hello, needs_auth: TRUE}}
- "Turn off" / "Stop listening" / "Goodbye" → {{app: system, action: deactivate_assistant, needs_auth: FALSE}}

Hindi:
- "YouTube pe gaana play karo" → {{app: youtube, action: play_music, needs_auth: FALSE}}
- "Google pe search karo iPhone price" → {{app: google, action: search, target: iPhone price, needs_auth: FALSE}}

━━━━━━ SECURITY RULES (needs_auth=true ONLY for these) ━━━━━━
✅ needs_auth = TRUE:
  - send_message (WhatsApp, SMS, Telegram)
  - make_call (phone call, video call)
  - send_email
  - payment / purchase / book (e.g. ordering food, booking ticket with payment)
  - delete / uninstall

❌ needs_auth = FALSE for EVERYTHING else including:
  - open apps, open browsers, navigate to URLs
  - search anything on Google, YouTube, Amazon
  - play music, videos
  - pause, play, skip ads, scroll, click, go back
  - set reminders, read calendar
  - type text in search boxes
  - deactivate assistant

━━━━━━ CRITICAL RULES ━━━━━━
1. NEVER refuse a command — always extract the best possible intent
2. If unclear between Tamil and Tanglish, pick tanglish
3. For "open YouTube" the app = youtube, action = open_app
4. For "play [song] on YouTube" the app = youtube, action = play_music
5. For deactivation words: "band", "off", "stop", "goodbye", "nandri", "poi varuven" → action = deactivate_assistant
6. If completely ambiguous, set clarification_needed = true with a helpful question in the user's detected language
"""

    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=ExtractedIntent)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("system", "Respond ONLY with valid JSON matching this schema:\n{format_instructions}"),
            ("human", "Voice command: {command}"),
        ])
        self.chain = self.prompt | self.llm | self.parser
        logger.info("✅ Intent Extractor initialized (LangChain + Gemini)")

    async def extract(self, transcript: str, context: dict = None) -> ExtractedIntent:
        """
        Extract intent from voice transcript

        Args:
            transcript: Text from Whisper/Gemini STT
            context: Optional conversation context from memory

        Returns:
            ExtractedIntent with app, action, target, etc.
        """
        context_str = ""
        if context:
            context_str = f"\nUser context: {context}"

        max_retries = 3
        backoff = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                intent = await self.chain.ainvoke({
                    "command": transcript + context_str,
                    "format_instructions": self.parser.get_format_instructions(),
                })

                logger.info(
                    f"🎯 Intent extracted: app={intent.app} | "
                    f"action={intent.action} | target={intent.target} | "
                    f"lang={intent.language} | auth={intent.needs_auth} | "
                    f"conf={intent.confidence:.2f}"
                )
                return intent

            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Intent extraction attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2.0

        logger.error(f"❌ Intent extraction failed after {max_retries} attempts: {last_error}")
        # Return fallback intent - attempt basic keyword matching
        return self._fallback_intent(transcript)

    def _fallback_intent(self, transcript: str) -> ExtractedIntent:
        """Basic keyword fallback when LLM fails"""
        t = transcript.lower()

        # Deactivation
        deactivate_words = ["turn off", "stop", "goodbye", "bye", "band", "off", "nandri", "poi varuven"]
        if any(w in t for w in deactivate_words):
            return ExtractedIntent(
                app="system", action="deactivate_assistant", language="english",
                needs_auth=False, confidence=0.7, raw_command=transcript,
                clarification_needed=False
            )

        # YouTube
        if "youtube" in t:
            action = "play_music" if any(w in t for w in ["play", "pannu", "song", "paatu"]) else "open_app"
            # Try to extract song name
            target = transcript
            return ExtractedIntent(
                app="youtube", action=action, target=target, language="tanglish",
                needs_auth=False, confidence=0.5, raw_command=transcript,
                clarification_needed=False
            )

        # Pause/Play
        if t.strip() in ["pause", "pause pannu", "niruthu"]:
            return ExtractedIntent(app="chrome", action="pause", language="tanglish",
                                   needs_auth=False, confidence=0.9, raw_command=transcript,
                                   clarification_needed=False)

        if t.strip() in ["play", "play pannu", "thodangu"]:
            return ExtractedIntent(app="chrome", action="play", language="tanglish",
                                   needs_auth=False, confidence=0.9, raw_command=transcript,
                                   clarification_needed=False)

        return ExtractedIntent(
            app="unknown",
            action="unknown",
            language="unknown",
            needs_auth=False,
            confidence=0.0,
            raw_command=transcript,
            clarification_needed=True,
            clarification_question="Sorry, I didn't understand that. Could you please repeat?",
        )


# ── Singleton ──
intent_extractor = IntentExtractor()
