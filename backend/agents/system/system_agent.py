from app.automation.desktop.adb_engine import adb_engine
from app.core.intent_extractor import ExtractedIntent
from dataclasses import dataclass
from loguru import logger

@dataclass
class SystemResult:
    success: bool
    message: str

class SystemAgent:
    """
    System Agent handles OS-level operations (e.g. app management, settings)
    using ADB for Android operations.
    """
    
    def __init__(self):
        logger.info("✅ System Agent initialized")
        
    async def execute(
        self,
        intent: ExtractedIntent,
        memory_context: dict,
        user_id: str,
    ) -> dict:
        action = intent.action
        
        if action in ["uninstall", "delete_app"]:
            app_name = intent.app or intent.target
            if not app_name:
                return {
                    "success": False,
                    "message": "App name not specified for uninstallation.",
                    "agent": "system",
                    "action": action
                }
            package_name = self._get_package_name(app_name)
            
            try:
                result_dict = await adb_engine.uninstall_app(package_name)
                success = result_dict.get("status") == "uninstalled"
                message = f"Successfully uninstalled {app_name}." if success else f"Failed to uninstall {app_name}."
                return {
                    "success": success,
                    "message": message,
                    "agent": "system",
                    "action": action
                }
            except Exception as e:
                logger.error(f"Failed to uninstall app via ADB: {e}")
                return {
                    "success": False,
                    "message": f"Could not uninstall {app_name}. Error: {str(e)}",
                    "agent": "system",
                    "action": action
                }
                
        elif action in ["close_app"]:
            return {
                "success": True,
                "message": f"Closed {intent.app or intent.target}.",
                "agent": "system",
                "action": action
            }

        return {
            "success": False,
            "message": f"Action '{action}' not supported by System Agent",
            "agent": "system",
            "action": action,
        }
        
    def _get_package_name(self, app_name: str) -> str:
        if not app_name:
            return ""
        name = app_name.lower()
        if "whatsapp" in name:
            return "com.whatsapp"
        elif "spotify" in name:
            return "com.spotify.music"
        elif "youtube" in name:
            return "com.google.android.youtube"
        elif "chrome" in name:
            return "com.android.chrome"
        elif "instagram" in name:
            return "com.instagram.android"
        return f"com.{name}"

    async def close(self):
        pass
