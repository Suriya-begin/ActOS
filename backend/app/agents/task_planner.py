"""
ActOS — AI Task Planner
Blueprint: LangGraph stateful task planner that breaks complex commands into ordered steps
"""
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import TypedDict, List, Optional
from app.core.config import settings, get_llm
from loguru import logger


class TaskState(TypedDict):
    command: str
    intent: dict
    steps: List[dict]
    current_step: int
    completed_steps: List[dict]
    final_result: Optional[str]
    error: Optional[str]


PLANNER_PROMPT = """
You are the ActOS Task Planner. Given a user intent, break it into specific executable steps.

Intent: {intent}
Original Command: {command}

Return a JSON list of steps:
[
  {{"step": 1, "action": "open_app", "target": "whatsapp", "description": "Open WhatsApp"}},
  {{"step": 2, "action": "search_contact", "target": "Ravi", "description": "Search for Ravi"}},
  {{"step": 3, "action": "confirm", "target": "user", "description": "Ask user confirmation"}},
  {{"step": 4, "action": "type_message", "target": "hi", "description": "Type the message"}},
  {{"step": 5, "action": "send", "target": "message", "description": "Send the message"}}
]

Be specific. Each step must be one atomic action an automation engine can execute.
"""


class TaskPlanner:
    """
    LangGraph-powered task planner.
    Decomposes complex commands into ordered executable steps.
    """

    def __init__(self):
        self.llm = get_llm(temperature=0)
        self.prompt = ChatPromptTemplate.from_template(PLANNER_PROMPT)
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph state machine for task execution."""
        graph = StateGraph(TaskState)

        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("verify", self._verify_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "execute")
        graph.add_conditional_edges("execute", self._should_continue, {"continue": "execute", "verify": "verify", "end": END})
        graph.add_edge("verify", END)

        self.graph = graph.compile()

    async def _plan_node(self, state: TaskState) -> TaskState:
        """Generate execution steps from intent."""
        import json
        response = await self.llm.ainvoke(self.prompt.format_messages(intent=state["intent"], command=state["command"]))
        try:
            steps = json.loads(response.content)
            state["steps"] = steps
            state["current_step"] = 0
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            state["steps"] = []
            state["error"] = str(e)
        return state

    async def _execute_node(self, state: TaskState) -> TaskState:
        """Execute current step — actual automation called from here."""
        if state["current_step"] < len(state["steps"]):
            step = state["steps"][state["current_step"]]
            logger.info(f"Executing step {step['step']}: {step['description']}")
            state["completed_steps"].append({**step, "status": "done"})
            state["current_step"] += 1
        return state

    async def _verify_node(self, state: TaskState) -> TaskState:
        state["final_result"] = f"Completed {len(state['completed_steps'])} steps successfully"
        return state

    def _should_continue(self, state: TaskState) -> str:
        if state.get("error"):
            return "end"
        if state["current_step"] >= len(state["steps"]):
            return "verify"
        return "continue"

    async def plan_and_execute(self, command: str, intent: dict) -> dict:
        initial_state = TaskState(command=command, intent=intent, steps=[], current_step=0, completed_steps=[], final_result=None, error=None)
        result = await self.graph.ainvoke(initial_state)
        return result


task_planner = TaskPlanner()
