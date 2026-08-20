# ============================================================
# ActOS — Multi-Agent Orchestrator
# Tech Stack: LangGraph (state machine) + CrewAI (agent crews)
# Routes commands to the right specialized agent
# ============================================================

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, Sequence, Callable, Optional
from langchain_core.messages import BaseMessage
import operator
from loguru import logger

from app.core.intent_extractor import ExtractedIntent
from agents.messaging.whatsapp_agent import MessagingAgent
from agents.browser.browser_agent import BrowserAgent
from agents.calendar.calendar_agent import CalendarAgent
from agents.research.research_agent import ResearchAgent
from agents.email.email_agent import EmailAgent
from agents.reminder.reminder_agent import ReminderAgent
from agents.system.system_agent import SystemAgent
from memory.vector.memory_engine import MemoryEngine
from security.auth.security_gate import SecurityGate


# ── STATE ──
class AgentState(TypedDict):
    """Full state passed through LangGraph pipeline"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    intent: ExtractedIntent
    user_id: str
    session_id: str
    memory_context: dict
    auth_verified: bool
    current_agent: str
    task_steps: list
    current_step: int
    result: dict
    error: str
    voice_response: str
    step_callback: Optional[object]  # Async callable for live step updates


# System-level apps that should be opened via desktop/OS rather than browser
SYSTEM_APPS = {
    "calculator", "settings", "files", "explorer", "notepad",
    "camera", "gallery", "contacts", "phone", "clock", "timer",
    "alarm", "control panel", "task manager"
}

# Interactive browser actions (always go to browser agent)
BROWSER_INTERACTIVE_ACTIONS = {
    "skip_ad", "pause", "play", "scroll_down", "scroll_up",
    "click", "go_back", "type_text", "fill_form", "summarize_page"
}

# Browser navigation actions
BROWSER_NAV_ACTIONS = {
    "open_app", "open_browser", "search", "play_music",
    "search_product", "book_cab"
}

# System OS actions
SYSTEM_ACTIONS = {
    "uninstall", "delete_app", "install_app", "close_app",
    "make_call", "deactivate_assistant"
}


class ActOSOrchestrator:
    """
    LangGraph State Machine Orchestrator

    Flow:
    START → memory_recall → security_check → agent_router →
    [messaging|browser|calendar|research|email|reminder|system] →
    response_builder → END

    On auth failure: → auth_request → wait_confirmation → retry
    """

    # Maps intent.app → agent
    AGENT_MAP = {
        "whatsapp":    "messaging",
        "telegram":    "messaging",
        "gmail":       "email",
        "chrome":      "browser",
        "youtube":     "browser",
        "maps":        "browser",
        "spotify":     "browser",
        "instagram":   "browser",
        "amazon":      "browser",
        "flipkart":    "browser",
        "zomato":      "browser",
        "swiggy":      "browser",
        "irctc":       "browser",
        "bookmyshow":  "browser",
        "google":      "browser",
        "calendar":    "calendar",
        "notes":       "reminder",
        "system":      "system",
    }

    def __init__(self):
        self.memory = MemoryEngine()
        self.security = SecurityGate()

        # Initialize all specialized agents
        self.agents = {
            "messaging": MessagingAgent(),
            "browser":   BrowserAgent(),
            "calendar":  CalendarAgent(),
            "research":  ResearchAgent(),
            "email":     EmailAgent(),
            "reminder":  ReminderAgent(),
            "system":    SystemAgent(),
        }

        # Build LangGraph
        self.graph = self._build_graph()
        logger.info("✅ ActOS Orchestrator initialized (LangGraph + multi-agent)")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("memory_recall",    self._memory_recall)
        graph.add_node("security_check",   self._security_check)
        graph.add_node("agent_router",     self._agent_router)
        graph.add_node("execute_agent",    self._execute_agent)
        graph.add_node("response_builder", self._response_builder)
        graph.add_node("auth_required",    self._auth_required)

        # Entry point
        graph.set_entry_point("memory_recall")

        # Edges
        graph.add_edge("memory_recall", "security_check")

        # Conditional: auth needed or not
        graph.add_conditional_edges(
            "security_check",
            self._needs_auth,
            {
                "auth_required": "auth_required",
                "proceed":       "agent_router",
            }
        )

        graph.add_edge("auth_required",    END)  # Wait for user confirmation
        graph.add_edge("agent_router",     "execute_agent")
        graph.add_edge("execute_agent",    "response_builder")
        graph.add_edge("response_builder", END)

        return graph.compile()

    # ── NODES ──

    async def _memory_recall(self, state: AgentState) -> AgentState:
        """Recall relevant memories for this command"""
        try:
            memories = await self.memory.recall(
                user_id=state["user_id"],
                query=state["intent"].raw_command,
                limit=5,
            )
            state["memory_context"] = memories
            logger.info(f"💾 Memory recalled: {len(memories)} relevant items")
        except Exception as e:
            logger.warning(f"Memory recall failed (non-fatal): {e}")
            state["memory_context"] = {}
        return state

    async def _security_check(self, state: AgentState) -> AgentState:
        """Check if action requires authentication"""
        if state["intent"].needs_auth:
            try:
                verified = await self.security.check_voice_auth(
                    user_id=state["user_id"],
                    action=state["intent"].action,
                )
                state["auth_verified"] = verified
            except Exception as e:
                logger.warning(f"Security check failed (defaulting to auth-required): {e}")
                state["auth_verified"] = False
        else:
            state["auth_verified"] = True
        return state

    def _needs_auth(self, state: AgentState) -> str:
        """Router: needs auth confirmation?"""
        if state["intent"].needs_auth and not state["auth_verified"]:
            return "auth_required"
        return "proceed"

    async def _agent_router(self, state: AgentState) -> AgentState:
        """Select the right agent based on intent"""
        app = (state["intent"].app or "").lower()
        action = (state["intent"].action or "").lower()
        target = (state["intent"].target or "").lower()

        # Route interactive browser actions to browser agent regardless of app
        if action in BROWSER_INTERACTIVE_ACTIONS:
            agent_name = "browser"

        # Route system-level actions
        elif action in SYSTEM_ACTIONS and action not in {"deactivate_assistant"}:
            # Check if target is a system app
            target_lower = target.lower() if target else ""
            if any(sys_app in target_lower for sys_app in SYSTEM_APPS):
                agent_name = "system"
            else:
                agent_name = "system"

        # WhatsApp / messaging routing
        # "open_app" or "open_browser" for WhatsApp = navigate to WhatsApp Web (browser agent)
        # "send_message" = compose/send via messaging agent
        elif app in {"whatsapp", "telegram"} and action in {"send_message", "send_whatsapp"}:
            agent_name = "messaging"
        elif app in {"whatsapp", "telegram"} and action in {"open_app", "open_browser", "open"}:
            agent_name = "browser"  # open WhatsApp Web in Playwright
        elif action in {"send_message"}:
            agent_name = "messaging"

        # Email routing
        elif app in {"gmail", "email"} or action in {"send_email"}:
            agent_name = "email"

        # Calendar routing
        elif app in {"calendar"} or action in {"set_reminder"}:
            agent_name = "calendar"

        # Notes/reminders
        elif app in {"notes"} or action in {"create_note"}:
            agent_name = "reminder"

        # System agent for system app
        elif app == "system":
            agent_name = "system"

        # All web/browser navigation
        elif action in BROWSER_NAV_ACTIONS:
            agent_name = "browser"

        # Default: map by app, fallback to browser
        else:
            agent_name = self.AGENT_MAP.get(app, "browser")

        state["current_agent"] = agent_name
        logger.info(f"🤖 Routing to: {agent_name} agent (app={app}, action={action})")
        return state

    async def _execute_agent(self, state: AgentState) -> AgentState:
        """Execute the selected agent"""
        agent_name = state["current_agent"]
        agent = self.agents.get(agent_name)

        if not agent:
            state["error"] = f"No agent found for: {agent_name}"
            return state

        try:
            # Send step update if callback available
            cb = state.get("step_callback")
            if cb:
                try:
                    await cb(f"Running {agent_name} agent...")
                except Exception:
                    pass

            result = await agent.execute(
                intent=state["intent"],
                memory_context=state["memory_context"],
                user_id=state["user_id"],
            )
            state["result"] = result

            # Store this action in memory (non-fatal)
            try:
                await self.memory.store(
                    user_id=state["user_id"],
                    key=f"last_{state['intent'].action}",
                    value={"intent": state["intent"].dict(), "result": result},
                )
            except Exception as mem_err:
                logger.warning(f"Memory store failed (non-fatal): {mem_err}")

        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            state["error"] = str(e)

        return state

    async def _response_builder(self, state: AgentState) -> AgentState:
        """Build natural language voice response"""
        intent = state["intent"]
        lang = intent.language or "english"

        if state.get("error"):
            if "tanglish" in lang or "tamil" in lang:
                state["voice_response"] = f"Sorry, oru problem vandhuchu. {state['error']}"
            else:
                state["voice_response"] = f"Sorry, something went wrong. Please try again."

        elif state.get("result"):
            result = state["result"]
            if result.get("success"):
                state["voice_response"] = result.get(
                    "message",
                    "Done. Action completed successfully."
                )
            else:
                msg = result.get("message", "Sorry, I was unable to complete the task.")
                state["voice_response"] = msg
        else:
            state["voice_response"] = "Done. Action completed successfully."

        return state

    async def _auth_required(self, state: AgentState) -> AgentState:
        """Request authentication from user"""
        intent = state["intent"]
        target_str = intent.target or intent.app or ""
        lang = intent.language or "english"

        action_display_map = {
            "send_message": f"send a message to {target_str}",
            "make_call": f"call {target_str}",
            "send_email": f"send an email to {target_str}",
            "uninstall": f"uninstall {target_str}",
            "delete_app": f"delete {target_str}",
        }
        action_msg = action_display_map.get(
            intent.action,
            f"{intent.action} {target_str}".strip()
        )

        if "tanglish" in lang or "tamil" in lang:
            state["voice_response"] = (
                f"Confirm pannunga — {action_msg} pannalama? "
                f"Yes nu sollunga proceed aagurom."
            )
        elif "hindi" in lang:
            state["voice_response"] = (
                f"Confirm karo — kya main {action_msg} karun? "
                f"Yes bolo toh karta hun."
            )
        else:
            state["voice_response"] = (
                f"This action requires confirmation. "
                f"I'm about to {action_msg}. "
                f"Please say yes to proceed or no to cancel."
            )
        return state

    # ── MAIN ENTRY ──
    async def process_command(
        self,
        intent: ExtractedIntent,
        user_id: str,
        session_id: str,
        step_callback=None,
    ) -> dict:
        """
        Main entry: process an extracted intent through the full pipeline
        """
        import uuid
        initial_state: AgentState = {
            "messages": [],
            "intent": intent,
            "user_id": user_id,
            "session_id": session_id,
            "memory_context": {},
            "auth_verified": False,
            "current_agent": "",
            "task_steps": [],
            "current_step": 0,
            "result": {},
            "error": "",
            "voice_response": "",
            "step_callback": step_callback,
        }

        run_id = uuid.uuid4().hex[:8]
        config = {
            "configurable": {"thread_id": f"{session_id}_{run_id}"},
            "recursion_limit": 100
        }
        final_state = await self.graph.ainvoke(initial_state, config)

        return {
            "voice_response": final_state["voice_response"],
            "result": final_state.get("result", {}),
            "auth_required": final_state["intent"].needs_auth and not final_state["auth_verified"],
            "agent_used": final_state.get("current_agent"),
            "error": final_state.get("error"),
            "language": final_state["intent"].language,
        }


# ── Singleton ──
orchestrator = ActOSOrchestrator()
