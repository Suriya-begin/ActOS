"""
ActOS — Desktop Automation Engine (Phase 3)
Blueprint: PyAutoGUI + pygetwindow for desktop app control
"""
import pyautogui
import pygetwindow as gw
import subprocess, time, platform
from loguru import logger

pyautogui.FAILSAFE = True   # move mouse to corner to abort
pyautogui.PAUSE = 0.3       # delay between actions


class DesktopEngine:
    """
    Controls desktop applications on Windows/Mac/Linux.
    Phase 3 — Universal Automation.
    """

    def get_os(self) -> str:
        return platform.system().lower()   # windows / darwin / linux

    async def open_app(self, app_name: str) -> dict:
        """Open a desktop application by name."""
        logger.info(f"Opening desktop app: {app_name}")
        os_type = self.get_os()
        try:
            if os_type == "windows":
                subprocess.Popen(["start", app_name], shell=True)
            elif os_type == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            time.sleep(2)
            return {"status": "opened", "app": app_name}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def focus_window(self, title_fragment: str) -> bool:
        """Bring a window to foreground by partial title match."""
        windows = gw.getWindowsWithTitle(title_fragment)
        if windows:
            win = windows[0]
            win.activate()
            time.sleep(0.5)
            return True
        return False

    async def type_text(self, text: str, interval: float = 0.05):
        """Type text into currently focused window."""
        pyautogui.typewrite(text, interval=interval)

    async def press_keys(self, *keys):
        """Press key combination — e.g. ('ctrl', 'c')."""
        pyautogui.hotkey(*keys)

    async def click_at(self, x: int, y: int):
        """Click at screen coordinates."""
        pyautogui.click(x, y)

    async def scroll(self, direction: str = "down", amount: int = 3):
        """Scroll up or down."""
        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)

    async def screenshot(self) -> object:
        """Take a screenshot — used by Phase 4 vision pipeline."""
        return pyautogui.screenshot()

    async def find_and_click(self, image_path: str) -> bool:
        """Find a UI element by image and click it (image recognition)."""
        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
        if location:
            pyautogui.click(location)
            return True
        return False


desktop_engine = DesktopEngine()
