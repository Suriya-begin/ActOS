"""
ActOS — CrewAI Multi-Agent System
Blueprint: CrewAI for specialized agents — messaging, browser, calendar, research, email
"""
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from app.core.config import settings, get_llm


llm = get_llm(temperature=0)


# ── AGENT DEFINITIONS ────────────────────────────────────────────────────────

messaging_agent = Agent(
    role="Messaging Agent",
    goal="Send and manage messages on WhatsApp, SMS, and Email on behalf of the user",
    backstory="""You are the ActOS Messaging Agent. You handle all communication tasks.
    You understand Tamil, Tanglish, and English commands. You open WhatsApp, find contacts,
    compose messages, and confirm before sending. You never send without user confirmation.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

browser_agent = Agent(
    role="Browser Agent",
    goal="Autonomously browse the web, search products, fill forms, and complete online tasks",
    backstory="""You are the ActOS Browser Agent. You control Chrome using Playwright.
    You navigate to websites, search for information, compare products, fill forms,
    and report back what you found. You handle Amazon, Zomato, BookMyShow, and any website.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

calendar_agent = Agent(
    role="Calendar & Scheduling Agent",
    goal="Manage the user's schedule, set reminders, and organize appointments",
    backstory="""You are the ActOS Calendar Agent. You manage Google Calendar, set reminders,
    schedule meetings, and send notifications. You understand time expressions in Tamil and English
    like 'naalaikku kaalaila 8 mani' (tomorrow morning 8am).""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

research_agent = Agent(
    role="Research Agent",
    goal="Search the web and summarize information for the user",
    backstory="""You are the ActOS Research Agent. You search Google, Wikipedia, and news sites
    to find accurate information. You summarize results in simple Tamil or English as preferred.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

email_agent = Agent(
    role="Email Agent",
    goal="Read, compose, and manage emails in Gmail",
    backstory="""You are the ActOS Email Agent. You open Gmail, read emails, compose replies,
    and organize the inbox. You summarize long emails and flag important ones.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

reminder_agent = Agent(
    role="Reminder Agent",
    goal="Set, track, and trigger reminders and notifications",
    backstory="""You are the ActOS Reminder Agent. You set time-based and location-based reminders,
    track deadlines, and proactively notify the user. You understand recurring patterns.""",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


# ── AGENT SELECTOR ────────────────────────────────────────────────────────────

AGENT_MAP = {
    "whatsapp":  messaging_agent,
    "sms":       messaging_agent,
    "gmail":     email_agent,
    "email":     email_agent,
    "chrome":    browser_agent,
    "amazon":    browser_agent,
    "zomato":    browser_agent,
    "youtube":   browser_agent,
    "calendar":  calendar_agent,
    "reminder":  reminder_agent,
    "research":  research_agent,
    "search":    research_agent,
}


def get_agent_for_intent(intent: dict) -> Agent:
    """Select the right agent based on extracted intent."""
    app = intent.get("app", "").lower()
    intent_type = intent.get("intent", "").lower()

    if app in AGENT_MAP:
        return AGENT_MAP[app]
    if "reminder" in intent_type or "schedule" in intent_type:
        return reminder_agent
    if "search" in intent_type or "research" in intent_type:
        return research_agent
    if "message" in intent_type or "send" in intent_type:
        return messaging_agent
    return browser_agent


async def run_agent_task(command: str, intent: dict, context: str = "") -> str:
    """
    Run the appropriate CrewAI agent for the given command.
    Returns the agent's execution result as a string.
    """
    agent = get_agent_for_intent(intent)

    task = Task(
        description=f"""
        Execute this user command: "{command}"
        
        Intent details: {intent}
        User context: {context}
        
        Steps:
        1. Understand what the user wants
        2. Plan the exact actions needed
        3. Execute step by step
        4. Confirm each critical action before doing it
        5. Report the result clearly
        """,
        agent=agent,
        expected_output="Confirmation of completed action with details",
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = await crew.kickoff_async()
    return str(result)
