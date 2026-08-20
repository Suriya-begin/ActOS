"""
ActOS — Android Automation Engine (Phase 3)
Blueprint: ADB (Android Debug Bridge) for mobile device control
"""
import subprocess, asyncio
from loguru import logger


class ADBEngine:
    """
    Controls Android device via ADB.
    Blueprint Phase 3: Android automation — calls, SMS, WhatsApp, notifications.
    Requires: Android device connected via USB or ADB over WiFi.
    """

    async def _run(self, *args) -> str:
        """Execute an ADB command and return output."""
        proc = await asyncio.create_subprocess_exec(
            "adb", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            return stdout.decode().strip()
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise TimeoutError("ADB command timed out")

    async def get_connected_devices(self) -> list:
        """List connected Android devices."""
        output = await self._run("devices")
        lines = output.split("\n")[1:]
        return [line.split("\t")[0] for line in lines if "device" in line]

    async def launch_app(self, package_name: str) -> dict:
        """Launch an Android app by package name."""
        # e.g. package_name = "com.whatsapp" | "com.spotify.music"
        result = await self._run("shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1")
        return {"status": "launched", "package": package_name}

    async def uninstall_app(self, package_name: str) -> dict:
        """Uninstall an Android app by package name via ADB."""
        logger.info(f"ADB: Uninstalling app '{package_name}'")
        result = await self._run("uninstall", package_name)
        return {"status": "uninstalled", "package": package_name, "output": result}

    async def send_text_input(self, text: str) -> dict:
        """Type text into currently focused field."""
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        await self._run("shell", "input", "text", escaped)
        return {"status": "typed", "text": text}

    async def tap(self, x: int, y: int) -> dict:
        """Tap at screen coordinates."""
        await self._run("shell", "input", "tap", str(x), str(y))
        return {"status": "tapped", "x": x, "y": y}

    async def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """Swipe gesture."""
        await self._run("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration))

    async def press_back(self):
        await self._run("shell", "input", "keyevent", "KEYCODE_BACK")

    async def press_home(self):
        await self._run("shell", "input", "keyevent", "KEYCODE_HOME")

    async def screenshot(self) -> bytes:
        """Take a screenshot of the Android screen."""
        await self._run("shell", "screencap", "-p", "/sdcard/actos_screen.png")
        proc = await asyncio.create_subprocess_exec("adb", "pull", "/sdcard/actos_screen.png", "/tmp/actos_android.png", stdout=asyncio.subprocess.PIPE)
        await proc.communicate()
        with open("/tmp/actos_android.png", "rb") as f:
            return f.read()

    async def make_call(self, phone_number: str) -> dict:
        """Initiate a phone call."""
        await self._run("shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{phone_number}")
        return {"status": "calling", "number": phone_number}

    async def send_sms(self, phone_number: str, message: str) -> dict:
        """Open SMS app to send message — requires confirmation."""
        await self._run("shell", "am", "start", "-a", "android.intent.action.SENDTO",
                  "-d", f"smsto:{phone_number}", "--es", "sms_body", message)
        return {"status": "sms_ready", "number": phone_number, "message": message}

    async def get_notifications(self) -> str:
        """Dump current notification list."""
        return await self._run("shell", "dumpsys", "notification", "--noredact")


adb_engine = ADBEngine()
