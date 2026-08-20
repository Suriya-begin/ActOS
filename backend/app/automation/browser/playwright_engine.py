"""
ActOS — Playwright Browser Automation Engine
Fix: Run Playwright in a dedicated thread with its own ProactorEventLoop
so it never conflicts with uvicorn's asyncio worker loop on Windows.
"""
import asyncio
import threading
import sys
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger


class PlaywrightEngine:
    """
    Controls Chrome browser autonomously.
    Runs in a dedicated background thread with its own ProactorEventLoop
    to avoid the Windows NotImplementedError with asyncio.create_subprocess_exec.
    """

    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.page: Page = None

        # Dedicated event loop running in its own thread
        self._loop: asyncio.AbstractEventLoop = None
        self._thread: threading.Thread = None
        self._ready = threading.Event()
        self._start_thread()

    # ── Thread + Loop lifecycle ──────────────────────────────────────────

    def _start_thread(self):
        """Spin up a background daemon thread that runs a ProactorEventLoop forever."""
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="playwright-loop")
        self._thread.start()
        self._ready.wait(timeout=10)  # Wait until loop is ready

    def _run_loop(self):
        """Entry point for the Playwright thread."""
        if sys.platform == "win32":
            self._loop = asyncio.ProactorEventLoop()
        else:
            self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def _run(self, coro):
        """
        Submit a coroutine to the Playwright thread's loop and block
        the calling asyncio task (via run_in_executor) until it completes.
        Returns the result or raises the exception.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=60)  # 60-second hard timeout

    async def _run_async(self, coro):
        """Async-friendly bridge: runs coro in Playwright thread, awaitable from uvicorn."""
        loop = asyncio.get_event_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return await loop.run_in_executor(None, future.result, 60)

    # ── Browser lifecycle ────────────────────────────────────────────────

    async def _start_browser(self):
        """Must be called inside the Playwright thread loop."""
        from app.core.config import settings
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.PLAYWRIGHT_HEADLESS,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        self.page = await context.new_page()
        logger.info("✅ Playwright browser started in dedicated thread")

    async def _ensure_started(self):
        """Called from the main uvicorn loop — ensures browser is alive."""
        need_start = False
        if not self.browser or not self.page:
            need_start = True
        else:
            # Check connection state in Playwright thread
            try:
                connected = await self._run_async(self._check_connected())
                if not connected:
                    need_start = True
            except Exception:
                need_start = True

        if need_start:
            logger.info("🌐 Launching Playwright browser...")
            try:
                await self._run_async(self._start_browser())
            except Exception as e:
                logger.error(f"❌ Playwright browser launch failed: {e}")
                raise

    async def _check_connected(self):
        return self.browser and self.browser.is_connected() and self.page and not self.page.is_closed()

    async def stop(self):
        async def _stop():
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self.page = None
        try:
            await self._run_async(_stop())
        except Exception as e:
            logger.warning(f"Playwright stop warning: {e}")

    # ── Generic page action runner ───────────────────────────────────────

    async def _exec(self, coro_factory):
        """
        Ensures browser is started, then runs coro_factory(page) in Playwright thread.
        coro_factory is a callable that takes page and returns a coroutine.
        """
        await self._ensure_started()

        async def _inner():
            return await coro_factory(self.page)

        return await self._run_async(_inner())

    # ── WhatsApp ─────────────────────────────────────────────────────────

    async def whatsapp_send_message(self, contact: str, message: str) -> dict:
        logger.info(f"WhatsApp: Sending '{message}' to {contact}")

        async def _do(page: Page):
            await page.goto("https://web.whatsapp.com", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            search_box = await page.wait_for_selector('div[contenteditable="true"][data-tab="3"]', timeout=15000)
            await search_box.click()
            await search_box.type(contact, delay=100)
            await page.wait_for_timeout(1500)
            contact_item = await page.wait_for_selector(f'span[title="{contact}"]', timeout=8000)
            await contact_item.click()
            await page.wait_for_timeout(1000)
            msg_box = await page.wait_for_selector('div[contenteditable="true"][data-tab="10"]', timeout=8000)
            await msg_box.click()
            await msg_box.type(message, delay=80)
            return {"status": "ready_to_send", "contact": contact, "message": message, "requires_confirmation": True}

        try:
            return await self._exec(_do)
        except Exception as e:
            logger.error(f"WhatsApp automation error: {e}")
            return {"status": "error", "error": str(e)}

    async def whatsapp_confirm_send(self) -> dict:
        async def _do(page: Page):
            send_btn = await page.wait_for_selector('button[data-testid="send"]', timeout=5000)
            await send_btn.click()
            await page.wait_for_timeout(1000)
            return {"status": "sent"}

        try:
            return await self._exec(_do)
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── URL / Search ──────────────────────────────────────────────────────

    async def open_url(self, url: str) -> dict:
        if not url.startswith("http"):
            url = "https://" + url

        async def _do(page: Page):
            await page.goto(url, wait_until="domcontentloaded")
            title = await page.title()
            return {"status": "opened", "url": url, "title": title}

        return await self._exec(_do)

    async def search_google(self, query: str) -> dict:
        from urllib.parse import quote_plus

        async def _do(page: Page):
            await page.goto(f"https://www.google.com/search?q={quote_plus(query)}", wait_until="domcontentloaded")
            results = await page.evaluate("""
                () => Array.from(document.querySelectorAll('div.g'))
                    .slice(0, 5)
                    .map(el => ({
                        title: el.querySelector('h3')?.textContent || '',
                        url: el.querySelector('a')?.href || '',
                        snippet: el.querySelector('.VwiC3b')?.textContent || '',
                    }))
            """)
            return {"status": "done", "query": query, "results": results}

        return await self._exec(_do)

    async def youtube_play(self, query: str) -> dict:
        from urllib.parse import quote_plus

        async def _do(page: Page):
            await page.goto(f"https://www.youtube.com/results?search_query={quote_plus(query)}", wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            first_video = await page.query_selector("ytd-video-renderer a#video-title")
            if first_video:
                await first_video.click()
                await page.wait_for_timeout(2000)
                title = await page.title()
                return {"status": "playing", "title": title}
            return {"status": "not_found"}

        return await self._exec(_do)

    async def search_amazon(self, query: str) -> dict:
        async def _do(page: Page):
            await page.goto("https://www.amazon.in", wait_until="domcontentloaded")
            search_box = await page.wait_for_selector("#twotabsearchtextbox", timeout=8000)
            await search_box.fill(query)
            await search_box.press("Enter")
            await page.wait_for_load_state("networkidle")
            results = await page.evaluate("""
                () => Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'))
                    .slice(0, 5)
                    .map(el => ({
                        title: el.querySelector('h2 span')?.textContent?.trim() || '',
                        price: el.querySelector('.a-price .a-offscreen')?.textContent?.trim() || '',
                    }))
            """)
            return {"status": "done", "query": query, "results": results}

        return await self._exec(_do)

    async def take_screenshot(self) -> bytes:
        async def _do(page: Page):
            return await page.screenshot(type="png")
        return await self._exec(_do)

    async def read_page_content(self) -> str:
        async def _do(page: Page):
            return await page.evaluate("() => document.body.innerText")
        return await self._exec(_do)


playwright_engine = PlaywrightEngine()
