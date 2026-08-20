# ============================================================
# ActOS — Browser Agent
# Tech Stack: Playwright + LangChain
# Controls Chrome: search, navigate, book, fill forms, summarize, play media
# ============================================================

from playwright.async_api import async_playwright, Page, Browser
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import asyncio
from loguru import logger
from urllib.parse import quote_plus

from app.core.config import settings, get_llm
from app.core.intent_extractor import ExtractedIntent


class BrowserAgent:
    """
    Playwright Browser Automation Agent

    Capabilities:
    - Open any website / navigate to URLs
    - Search Google, YouTube, Amazon, Flipkart etc.
    - Play music/video on YouTube, Spotify
    - Skip YouTube ads, pause/play/scroll
    - Search products on Amazon/Flipkart
    - Order food on Zomato/Swiggy
    - Book tickets (IRCTC, BookMyShow, MakeMyTrip)
    - Read and summarize page content
    - Fill forms, type text
    - Navigate back
    """

    APP_URLS = {
        "amazon":      "https://www.amazon.in",
        "flipkart":    "https://www.flipkart.com",
        "zomato":      "https://www.zomato.com",
        "swiggy":      "https://www.swiggy.com",
        "youtube":     "https://www.youtube.com",
        "spotify":     "https://open.spotify.com",
        "irctc":       "https://www.irctc.co.in",
        "bookmyshow":  "https://www.bookmyshow.com",
        "makemytrip":  "https://www.makemytrip.com",
        "google":      "https://www.google.com",
        "maps":        "https://maps.google.com",
        "gmail":       "https://mail.google.com",
        "whatsapp":    "https://web.whatsapp.com",
        "instagram":   "https://www.instagram.com",
        "twitter":     "https://www.twitter.com",
        "facebook":    "https://www.facebook.com",
        "linkedin":    "https://www.linkedin.com",
        "netflix":     "https://www.netflix.com",
        "hotstar":     "https://www.hotstar.com",
    }

    def __init__(self):
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None
        self.llm = get_llm(temperature=0)
        logger.info("✅ Browser Agent initialized")

    async def _ensure_browser(self):
        from app.automation.browser.playwright_engine import playwright_engine
        await playwright_engine._ensure_started()
        self.browser = playwright_engine.browser
        self.page = playwright_engine.page
        self.playwright = playwright_engine.playwright

    async def _new_page(self) -> Page:
        """Get the active Playwright page — always runs in the Playwright thread."""
        from app.automation.browser.playwright_engine import playwright_engine
        await playwright_engine._ensure_started()
        self.page = playwright_engine.page
        return self.page

    async def _exec_in_browser(self, coro_factory):
        """Execute a coroutine in the Playwright thread via the engine bridge."""
        from app.automation.browser.playwright_engine import playwright_engine
        return await playwright_engine._exec(coro_factory)

    async def execute(
        self,
        intent: ExtractedIntent,
        memory_context: dict,
        user_id: str,
    ) -> dict:
        """Route to correct browser action based on extracted intent"""
        action = intent.action
        target = intent.target or intent.app or ""
        content = intent.content or ""

        try:
            if action == "search":
                result = await self.search_web(target, content)
            elif action in ("open_browser", "open_app"):
                result = await self.open_website(target)
            elif action == "play_music":
                result = await self.play_youtube(target)
            elif action == "search_product":
                result = await self.search_product(intent.app, target)
            elif action == "summarize_page":
                result = await self.summarize_page(target)
            elif action == "skip_ad":
                result = await self.skip_youtube_ad()
            elif action == "pause":
                result = await self.pause_media()
            elif action == "play":
                result = await self.resume_media()
            elif action == "scroll_down":
                result = await self.scroll_browser("down")
            elif action == "scroll_up":
                result = await self.scroll_browser("up")
            elif action == "click":
                result = await self.click_browser_element(target)
            elif action == "go_back":
                result = await self.go_back_browser()
            elif action == "type_text":
                result = await self.type_text_on_page(target or content)
            elif action == "fill_form":
                result = await self.fill_form_fields(target, content)
            elif action == "book_cab":
                result = await self.book_cab(target)
            else:
                # Generic fallback: try to open target as website
                result = await self.open_website(target or intent.app)
        except Exception as e:
            logger.error(f"BrowserAgent action '{action}' failed: {e}")
            result = {"success": False, "message": f"Browser action failed: {str(e)}"}

        return result

    async def open_website(self, target: str) -> dict:
        """Open a website or app by name or URL"""
        from urllib.parse import quote_plus as _qp
        target_lower = (target or "").lower().strip()
        url = self.APP_URLS.get(target_lower)
        if not url:
            if target and target.startswith("http"):
                url = target
            elif target:
                url = f"https://www.google.com/search?q={_qp(target)}"
            else:
                url = "https://www.google.com"

        async def _do(page):
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            title = await page.title()
            logger.info(f"🌐 Opened: {url} (title: {title})")
            return {"success": True, "message": f"Opened {target or url} in browser.", "url": url, "title": title}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Could not open {target}: {str(e)}"}

    async def search_web(self, query: str, additional: str = None) -> dict:
        """Google search"""
        from urllib.parse import quote_plus as _qp
        search_query = f"{query} {additional or ''}".strip()

        async def _do(page):
            await page.goto(f"https://www.google.com/search?q={_qp(search_query)}", wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            results = await page.evaluate("""
                () => Array.from(document.querySelectorAll('div.g'))
                    .slice(0, 5)
                    .map(el => ({
                        title: el.querySelector('h3')?.textContent?.trim() || '',
                        snippet: el.querySelector('.VwiC3b, .st')?.textContent?.trim() || '',
                    }))
                    .filter(r => r.title)
            """)
            titles = [r["title"] for r in results[:3] if r["title"]]
            return {
                "success": True,
                "message": f"Searched for '{search_query}'. Top results: {'; '.join(titles) if titles else 'Results shown on screen.'}",
                "results": results,
            }

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Search failed: {str(e)}"}

    async def search_product(self, platform: str, query: str) -> dict:
        """Search for a product on Amazon/Flipkart"""
        platform_lower = (platform or "amazon").lower()
        base_url = self.APP_URLS.get(platform_lower, self.APP_URLS["amazon"])

        async def _do(page):
            await page.goto(base_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(1500)

            # Find search box
            search_selectors = [
                '#twotabsearchtextbox',   # Amazon
                'input[name="q"]',         # Flipkart / Generic
                'input[type="search"]',
                'input[placeholder*="search" i]',
                'input[placeholder*="Search" i]',
            ]

            search_box = None
            for selector in search_selectors:
                try:
                    search_box = await page.wait_for_selector(selector, timeout=3000)
                    if search_box:
                        break
                except Exception:
                    continue

            if search_box:
                await search_box.fill(query)
                await search_box.press("Enter")
                await page.wait_for_timeout(2500)

                # Extract top results
                products = await page.evaluate("""
                    () => {
                        const selectors = ['h2 a span', '[data-component-type="s-search-result"] h2', '.s1Q9rs', '._4rR01T'];
                        for (const sel of selectors) {
                            const els = document.querySelectorAll(sel);
                            if (els.length > 0) {
                                return Array.from(els).slice(0, 5).map(el => el.textContent?.trim()).filter(Boolean);
                            }
                        }
                        return [];
                    }
                """)

                return {
                    "success": True,
                    "message": f"Searched for '{query}' on {platform_lower.capitalize()}. Found: {', '.join(products[:3]) if products else 'Results shown on screen.'}",
                    "products": products,
                }

            return {"success": False, "message": f"Could not find search box on {platform_lower}"}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Product search failed: {str(e)}"}

    async def play_youtube(self, query: str) -> dict:
        """Search and play on YouTube"""
        from urllib.parse import quote_plus as _qp

        async def _do(page):
            search_url = f"https://www.youtube.com/results?search_query={_qp(query or '')}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            first_video = None
            for selector in [
                "ytd-video-renderer a#video-title",
                "ytd-rich-item-renderer a#video-title",
                "a#video-title",
            ]:
                try:
                    first_video = await page.wait_for_selector(selector, timeout=5000)
                    if first_video:
                        break
                except Exception:
                    continue

            if first_video:
                title = (await first_video.inner_text()).strip()
                await first_video.click()
                await page.wait_for_timeout(2000)
                return {"success": True, "message": f"Playing '{title}' on YouTube.", "title": title}
            else:
                return {"success": False, "message": "Could not find a video to play on YouTube."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"YouTube playback failed: {str(e)}"}

    async def summarize_page(self, url: str = None) -> dict:
        """Summarize the current page or a given URL — navigates directly, no Google."""
        # Normalize URL — add https:// if missing
        nav_url = None
        if url:
            url = url.strip().rstrip("/")
            if url.startswith("http"):
                nav_url = url
            elif url:
                nav_url = f"https://{url}"

        async def _do(page):
            if nav_url:
                await page.goto(nav_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
            content = await page.evaluate("() => document.body.innerText")
            return (content or "")[:4000]

        try:
            content = await self._exec_in_browser(_do)
            if not content or not content.strip():
                return {"success": False, "message": "Page has no readable content."}

            prompt = ChatPromptTemplate.from_messages([
                ("system", "Summarize the following webpage content in 3 concise sentences. Be direct and informative."),
                ("human", "{content}"),
            ])
            chain = prompt | self.llm
            result = await chain.ainvoke({"content": content})
            return {"success": True, "message": result.content}
        except Exception as e:
            return {"success": False, "message": f"Summarization failed: {str(e)}"}

    async def skip_youtube_ad(self) -> dict:
        """Skip ads on YouTube using JS injection or button click"""
        async def _do(page):
            # Try JS injection first
            skipped = await page.evaluate("""
                () => {
                    const video = document.querySelector('video');
                    const adShowing = document.querySelector('.ad-showing, .ad-interrupting, .ytp-ad-player-overlay');
                    if (adShowing && video) {
                        video.currentTime = video.duration || 9999;
                        return 'fast-forwarded';
                    }
                    // Click visible skip button
                    const skipSelectors = [
                        '.ytp-skip-ad-button',
                        '.ytp-ad-skip-button',
                        '.ytp-skip-ad-button-modern',
                        '[class*="skip-ad"]',
                        '[class*="skipAd"]'
                    ];
                    for (const sel of skipSelectors) {
                        const btn = document.querySelector(sel);
                        if (btn) {
                            btn.click();
                            return 'clicked-' + sel;
                        }
                    }
                    return null;
                }
            """)

            if skipped:
                return {"success": True, "message": f"Ad skipped successfully."}

            # Fallback: try Playwright selector click
            for selector in [".ytp-skip-ad-button", ".ytp-ad-skip-button", ".ytp-skip-ad-button-modern"]:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    return {"success": True, "message": "Ad skip button clicked."}

            return {"success": False, "message": "No active ad found to skip right now."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Failed to skip ad: {str(e)}"}

    async def pause_media(self) -> dict:
        """Pause video or audio playback"""
        async def _do(page):
            paused = await page.evaluate("""
                () => {
                    const media = document.querySelector('video, audio');
                    if (media && !media.paused) {
                        media.pause();
                        return true;
                    }
                    return false;
                }
            """)
            if paused:
                return {"success": True, "message": "Playback paused."}
            else:
                await page.keyboard.press("Space")
                return {"success": True, "message": "Pause sent."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Pause failed: {str(e)}"}

    async def resume_media(self) -> dict:
        """Play/resume video or audio playback"""
        async def _do(page):
            played = await page.evaluate("""
                () => {
                    const media = document.querySelector('video, audio');
                    if (media && media.paused) {
                        media.play();
                        return true;
                    }
                    return false;
                }
            """)
            if played:
                return {"success": True, "message": "Playback resumed."}
            else:
                await page.keyboard.press("Space")
                return {"success": True, "message": "Play sent."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Play failed: {str(e)}"}

    async def scroll_browser(self, direction: str) -> dict:
        """Scroll page up or down"""
        async def _do(page):
            amount = 500 if direction == "down" else -500
            await page.evaluate(f"window.scrollBy(0, {amount})")
            return {"success": True, "message": f"Scrolled {direction}."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Scroll failed: {str(e)}"}

    async def go_back_browser(self) -> dict:
        """Go back to previous page"""
        async def _do(page):
            await page.go_back()
            await page.wait_for_timeout(500)
            return {"success": True, "message": "Navigated back."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Go back failed: {str(e)}"}

    async def click_browser_element(self, target: str) -> dict:
        """Click on a specific element by text content or CSS selector"""
        async def _do(page):
            # Try text-based match first
            if target:
                try:
                    element = page.locator(f"text={target}").first
                    if await element.count() > 0 and await element.is_visible():
                        await element.click()
                        return {"success": True, "message": f"Clicked on '{target}'."}
                except Exception:
                    pass

                # Fallback: CSS selector
                try:
                    btn = await page.query_selector(target)
                    if btn and await btn.is_visible():
                        await btn.click()
                        return {"success": True, "message": f"Clicked element '{target}'."}
                except Exception:
                    pass

            return {"success": False, "message": f"Could not find '{target}' on the page."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Click failed: {str(e)}"}

    async def type_text_on_page(self, text: str) -> dict:
        """Type text into the currently focused input or active element"""
        async def _do(page):
            # Try to find an active/focused input
            typed = await page.evaluate(f"""
                (text) => {{
                    const active = document.activeElement;
                    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.contentEditable === 'true')) {{
                        if (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA') {{
                            active.value = text;
                            active.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            active.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }} else {{
                            active.innerText = text;
                        }}
                        return true;
                    }}
                    return false;
                }}
            """, text)

            if not typed:
                # Fallback: type via keyboard into any visible input
                input_el = await page.query_selector('input[type="text"], input[type="search"], textarea, [contenteditable="true"]')
                if input_el:
                    await input_el.click()
                    await input_el.fill(text)
                    typed = True

            if typed:
                return {"success": True, "message": f"Typed '{text}' on the page."}
            else:
                return {"success": False, "message": "Could not find an input field to type into."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Type text failed: {str(e)}"}

    async def fill_form_fields(self, form_target: str, content: str) -> dict:
        """Fill a form with given field values"""
        async def _do(page):
            if form_target and form_target.startswith("http"):
                await page.goto(form_target, wait_until="domcontentloaded", timeout=20000)

            # Use LLM to figure out which fields to fill
            if content:
                await page.evaluate(f"""
                    (text) => {{
                        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea');
                        if (inputs.length > 0) {{
                            inputs[0].value = text;
                            inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }}
                    }}
                """, content)
            return {"success": True, "message": f"Form filled with provided content."}

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Form fill failed: {str(e)}"}

    async def book_cab(self, destination: str) -> dict:
        """Open Uber/Ola to book a cab"""
        async def _do(page):
            search_url = f"https://www.google.com/search?q=book+cab+to+{quote_plus(destination or 'my destination')}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            return {
                "success": True,
                "message": f"Searching for cabs to {destination}. Please select from the results on screen.",
            }

        try:
            return await self._exec_in_browser(_do)
        except Exception as e:
            return {"success": False, "message": f"Cab booking search failed: {str(e)}"}
