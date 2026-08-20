# ============================================================
# ActOS — Messaging Agent (WhatsApp Automation)
# Tech Stack: Playwright + CrewAI
# Handles: WhatsApp Web automation via browser
# ============================================================

from playwright.async_api import async_playwright, Page, Browser
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import asyncio
from loguru import logger
from dataclasses import dataclass

from app.core.config import settings
from app.core.intent_extractor import ExtractedIntent


@dataclass
class MessageResult:
    success: bool
    message: str
    contact_found: bool = False
    message_sent: bool = False


class MessagingAgent:
    """
    WhatsApp Automation Agent
    Uses Playwright to control WhatsApp Web
    
    Capabilities:
    - Send messages to contacts
    - Make voice/video calls
    - Read last messages
    - Forward messages
    """

    WHATSAPP_URL = "https://web.whatsapp.com"

    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None
        logger.info("✅ Messaging Agent initialized")

    async def _ensure_browser(self):
        """Launch Playwright browser if not running"""
        from app.automation.browser.playwright_engine import playwright_engine
        await playwright_engine._ensure_started()
        self.browser = playwright_engine.browser
        self.page = playwright_engine.page
        self.playwright = playwright_engine.playwright

    async def _ensure_whatsapp(self):
        """Open WhatsApp Web tab"""
        await self._ensure_browser()

        if self.WHATSAPP_URL not in self.page.url:
            await self.page.goto(self.WHATSAPP_URL)
            logger.info("📱 WhatsApp Web opened — waiting for QR scan if needed")

            # Wait for WhatsApp to load (QR scan or already logged in)
            await self.page.wait_for_selector(
                '[data-testid="chat-list-search"]',
                timeout=60000,
            )
            logger.info("✅ WhatsApp Web ready")

    async def execute(
        self,
        intent: ExtractedIntent,
        memory_context: dict,
        user_id: str,
    ) -> dict:
        """
        Execute messaging action based on intent
        Dispatches to the right method
        """
        action = intent.action

        if action == "send_message":
            result = await self.send_whatsapp_message(
                contact=intent.target,
                message=intent.content or "hi",
                memory_context=memory_context,
            )
        elif action == "make_call":
            result = await self.make_whatsapp_call(
                contact=intent.target,
                memory_context=memory_context,
            )
        elif action == "read_messages":
            result = await self.read_last_messages(
                contact=intent.target,
                memory_context=memory_context,
            )
        else:
            result = MessageResult(
                success=False,
                message=f"Action '{action}' not supported by Messaging Agent",
            )

        return {
            "success": result.success,
            "message": result.message,
            "agent": "messaging",
            "action": action,
        }

    async def send_whatsapp_message(
        self,
        contact: str,
        message: str,
        memory_context: dict,
    ) -> MessageResult:
        """
        Send WhatsApp message to a contact
        
        Steps:
        1. Open WhatsApp Web
        2. Search for contact
        3. Open chat
        4. Type message
        5. Send (after auth confirmation from orchestrator)
        """
        try:
            await self._ensure_whatsapp()

            # Resolve contact from memory if needed
            resolved_contact = self._resolve_contact(contact, memory_context)
            logger.info(f"📤 Sending WhatsApp message to: {resolved_contact}")

            # Step 1: Click search box
            search_box = await self.page.wait_for_selector(
                '[data-testid="chat-list-search"]'
            )
            await search_box.click()
            await search_box.fill(resolved_contact)
            await asyncio.sleep(1.5)

            # Step 2: Find and click the contact
            contact_item = await self.page.wait_for_selector(
                f'[title="{resolved_contact}"]',
                timeout=5000,
            )

            if not contact_item:
                # Try partial match
                contact_item = await self.page.query_selector(
                    '[data-testid="cell-frame-title"]'
                )

            if not contact_item:
                return MessageResult(
                    success=False,
                    message=f"Contact '{resolved_contact}' not found in WhatsApp",
                    contact_found=False,
                )

            await contact_item.click()
            await asyncio.sleep(1)

            # Step 3: Type message in chat input
            msg_box = await self.page.wait_for_selector(
                '[data-testid="conversation-compose-box-input"]'
            )
            await msg_box.click()
            await msg_box.type(message, delay=50)
            await asyncio.sleep(0.5)

            # Step 4: Send message (Enter key)
            await msg_box.press("Enter")
            await asyncio.sleep(1)

            logger.info(f"✅ WhatsApp message sent to {resolved_contact}: '{message}'")
            return MessageResult(
                success=True,
                message=f"Message '{message}' sent to {resolved_contact} on WhatsApp.",
                contact_found=True,
                message_sent=True,
            )

        except Exception as e:
            logger.error(f"❌ WhatsApp send failed: {e}")
            return MessageResult(
                success=False,
                message=f"Failed to send WhatsApp message: {str(e)}",
            )

    async def make_whatsapp_call(
        self,
        contact: str,
        memory_context: dict,
    ) -> MessageResult:
        """Initiate WhatsApp voice call"""
        try:
            await self._ensure_whatsapp()
            resolved_contact = self._resolve_contact(contact, memory_context)

            # Open contact chat
            search_box = await self.page.wait_for_selector('[data-testid="chat-list-search"]')
            await search_box.fill(resolved_contact)
            await asyncio.sleep(1.5)

            contact_item = await self.page.wait_for_selector(f'[title="{resolved_contact}"]')
            await contact_item.click()
            await asyncio.sleep(1)

            # Click voice call button
            call_btn = await self.page.wait_for_selector('[data-testid="call-button"]')
            await call_btn.click()

            return MessageResult(
                success=True,
                message=f"Calling {resolved_contact} on WhatsApp.",
                contact_found=True,
            )
        except Exception as e:
            return MessageResult(success=False, message=str(e))

    async def read_last_messages(
        self,
        contact: str,
        memory_context: dict,
    ) -> MessageResult:
        """Read last few messages from a contact"""
        try:
            await self._ensure_whatsapp()
            resolved_contact = self._resolve_contact(contact, memory_context)

            search_box = await self.page.wait_for_selector('[data-testid="chat-list-search"]')
            await search_box.fill(resolved_contact)
            await asyncio.sleep(1.5)

            contact_item = await self.page.wait_for_selector(f'[title="{resolved_contact}"]')
            await contact_item.click()
            await asyncio.sleep(1)

            # Extract last 3 messages
            messages = await self.page.query_selector_all('[data-testid="msg-container"]')
            last_msgs = []
            for msg in messages[-3:]:
                text = await msg.inner_text()
                last_msgs.append(text.strip())

            summary = " | ".join(last_msgs[-3:]) if last_msgs else "No messages found"
            return MessageResult(
                success=True,
                message=f"Last messages from {resolved_contact}: {summary}",
                contact_found=True,
            )
        except Exception as e:
            return MessageResult(success=False, message=str(e))

    def _resolve_contact(self, name: str, memory_context: dict) -> str:
        """
        Resolve contact name from memory
        e.g. "Amma" → actual contact name stored in memory
        """
        if not name:
            return "Unknown"

        # Check memory context for contact resolution
        contacts = memory_context.get("contacts", {})
        resolved = contacts.get(name.lower(), name)

        # Common Tamil family name resolutions
        defaults = {
            "amma": "Mom",
            "appa": "Dad",
            "anna": "Brother",
            "akka": "Sister",
        }
        if name.lower() in defaults and name.lower() not in contacts:
            resolved = defaults[name.lower()]

        return resolved

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
