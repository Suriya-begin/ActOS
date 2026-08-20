from loguru import logger
from app.automation.browser.playwright_engine import playwright_engine

async def startup_event():
    logger.info("Running default startup event actions...")

async def shutdown_event():
    logger.info("Stopping shared Playwright engine...")
    await playwright_engine.stop()
