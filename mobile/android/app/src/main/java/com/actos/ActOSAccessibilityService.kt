package com.actos

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.util.Log

/**
 * ActOS Android Accessibility Service
 * Blueprint: Kotlin + Android Accessibility APIs for deep app control
 * Phase 3 — Universal Automation
 *
 * Enables ActOS to:
 * - Control any Android app UI
 * - Read screen content
 * - Click buttons, type text, scroll
 * - Monitor notifications
 */
class ActOSAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        val info = serviceInfo
        info.eventTypes = AccessibilityEvent.TYPES_ALL_MASK
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
        info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS or
                     AccessibilityServiceInfo.FLAG_REQUEST_ENHANCED_WEB_ACCESSIBILITY
        info.notificationTimeout = 100
        serviceInfo = info
        Log.d("ActOS", "Accessibility Service connected")
        sendToActOSBackend("service_ready", mapOf())
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                val pkg = event.packageName?.toString() ?: return
                sendToActOSBackend("app_changed", mapOf("package" to pkg))
            }
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED -> {
                val text = event.text.joinToString(" ")
                sendToActOSBackend("notification", mapOf("text" to text, "package" to (event.packageName ?: "")))
            }
        }
    }

    override fun onInterrupt() {
        Log.d("ActOS", "Accessibility Service interrupted")
    }

    /** Click a UI element by text label */
    fun clickByText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val nodes = root.findAccessibilityNodeInfosByText(text)
        if (nodes.isNotEmpty()) {
            nodes[0].performAction(AccessibilityNodeInfo.ACTION_CLICK)
            return true
        }
        return false
    }

    /** Type text into the focused field */
    fun typeText(text: String) {
        val args = android.os.Bundle()
        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        rootInActiveWindow?.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            ?.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
    }

    /** Scroll down the current view */
    fun scrollDown() {
        rootInActiveWindow?.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD)
    }

    /** Send event to ActOS backend via HTTP */
    private fun sendToActOSBackend(event: String, data: Map<String, Any>) {
        // TODO: Use Retrofit/OkHttp to POST to http://actos-backend:8000/api/mobile/event
        Log.d("ActOS", "Event: $event | Data: $data")
    }
}
