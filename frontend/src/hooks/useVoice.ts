// ============================================================
// ActOS — useVoice Hook (v2 — Continuous Always-On Mode)
// Tech Stack: Web Audio API + WebRTC + WebSockets
// Features:
//   • Continuous listening: auto-restart after each command
//   • VAD (Voice Activity Detection): silence detection
//   • Works seamlessly across multi-step tasks
//   • "OK ActOS" wake-word optional toggle
//   • Never drops a step mid-task
// ============================================================

import { useState, useRef, useCallback, useEffect } from "react"

export type VoiceStatus =
  | "idle"
  | "listening"
  | "processing"
  | "speaking"
  | "confirming"
  | "error"

export interface VoiceEvent {
  type: string
  text?: string
  language?: string
  code?: string
  intent?: Record<string, unknown>
  message?: string
  audio?: string
  data?: any
  success?: boolean
  agent?: string
  step?: number
}

export interface UseVoiceOptions {
  userId: string
  wsUrl?: string
  onTranscript?: (text: string, language: string) => void
  onIntent?: (intent: Record<string, unknown>) => void
  onResponse?: (message: string) => void
  onConfirmRequired?: (message: string, intent: Record<string, unknown>) => void
  onComplete?: (success: boolean, message: string) => void
  onError?: (error: string) => void
}

// VAD config
const VAD_VOLUME_THRESHOLD = 0.012   // min avg volume to count as speech
const VAD_SILENCE_AFTER_SPEECH = 1800 // ms of silence before auto-stop
const VAD_MAX_SILENCE_BEFORE_SPEECH = 15000 // 15s idle timeout without any speech
const MIN_AUDIO_BYTES = 2000         // skip if audio blob is smaller than this

export function useVoice({
  userId,
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000",
  onTranscript,
  onIntent,
  onResponse,
  onConfirmRequired,
  onComplete,
  onError,
}: UseVoiceOptions) {
  const [status, setStatus] = useState<VoiceStatus>("idle")
  const [transcript, setTranscript] = useState("")
  const [lastResponse, setLastResponse] = useState("")
  const [currentStep, setCurrentStep] = useState("")
  const [detectedLanguage, setDetectedLanguage] = useState("")
  const [pendingIntent, setPendingIntent] = useState<Record<string, unknown> | null>(null)
  const [waveformData, setWaveformData] = useState<number[]>(Array(32).fill(0))
  const [isContinuous, setIsContinuous] = useState(false)

  // ── Internal refs ──
  const isContinuousRef = useRef(false)
  const lastVoiceTimeRef = useRef<number>(Date.now())
  const hasSpokenRef = useRef<boolean>(false)
  const isPlayingAudioRef = useRef<boolean>(false)
  const isProcessingRef = useRef<boolean>(false)  // prevent double-processing

  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animFrameRef = useRef<number>(0)
  const audioContextRef = useRef<AudioContext | null>(null)
  const pendingIntentRef = useRef<Record<string, unknown> | null>(null)
  const startListeningRef = useRef<() => void>(() => {})
  const stopListeningRef = useRef<() => void>(() => {})
  const pendingTextCommandRef = useRef<string | null>(null)
  const currentStreamRef = useRef<MediaStream | null>(null)
  const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Cleanup helpers ──
  const _cleanupRecording = useCallback(() => {
    cancelAnimationFrame(animFrameRef.current)
    setWaveformData(Array(32).fill(0))
    if (currentStreamRef.current) {
      currentStreamRef.current.getTracks().forEach(t => t.stop())
      currentStreamRef.current = null
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }
    analyserRef.current = null
  }, [])

  const _clearRestartTimer = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current)
      restartTimerRef.current = null
    }
  }, [])

  // ── Schedule re-listen after a delay ──
  const _scheduleRestart = useCallback((delayMs = 600) => {
    _clearRestartTimer()
    restartTimerRef.current = setTimeout(() => {
      if (isContinuousRef.current && !isProcessingRef.current && !isPlayingAudioRef.current && !pendingIntentRef.current) {
        startListeningRef.current()
      }
    }, delayMs)
  }, [_clearRestartTimer])

  // ── PLAY AUDIO ──
  const playAudioB64 = useCallback((b64: string) => {
    try {
      const binary = atob(b64)
      const bytes = new Uint8Array(binary.length)
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
      const blob = new Blob([bytes], { type: "audio/mpeg" })
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)

      isPlayingAudioRef.current = true
      setStatus("speaking")

      audio.play().catch(err => {
        console.warn("Audio play failed:", err)
        isPlayingAudioRef.current = false
        isProcessingRef.current = false
        if (isContinuousRef.current && !pendingIntentRef.current) _scheduleRestart(400)
        else setStatus("idle")
      })

      audio.onended = () => {
        URL.revokeObjectURL(url)
        isPlayingAudioRef.current = false
        isProcessingRef.current = false
        setCurrentStep("")

        if (isContinuousRef.current && !pendingIntentRef.current) {
          // Auto-restart listening after TTS finishes
          _scheduleRestart(400)
        } else if (!pendingIntentRef.current) {
          setStatus("idle")
        }
      }

      audio.onerror = () => {
        URL.revokeObjectURL(url)
        isPlayingAudioRef.current = false
        isProcessingRef.current = false
        if (isContinuousRef.current && !pendingIntentRef.current) _scheduleRestart(400)
        else setStatus("idle")
      }
    } catch (err) {
      console.error("Audio decode error:", err)
      isPlayingAudioRef.current = false
      isProcessingRef.current = false
      if (isContinuousRef.current && !pendingIntentRef.current) _scheduleRestart(600)
    }
  }, [_scheduleRestart])

  // ── HANDLE SERVER MESSAGES ──
  const handleServerMessage = useCallback((msg: VoiceEvent) => {
    switch (msg.type) {

      case "transcript":
        setTranscript(msg.text || "")
        setCurrentStep("")
        setStatus("processing")
        isProcessingRef.current = true
        onTranscript?.(msg.text || "", msg.language || "en")
        break

      case "language":
        setDetectedLanguage(msg.text || "")
        break

      case "intent":
        onIntent?.(msg as unknown as Record<string, unknown>)
        break

      case "step":
        setCurrentStep(msg.text || "")
        break

      case "status":
        if (msg.text === "idle" && !isPlayingAudioRef.current && !isProcessingRef.current) {
          // Backend says idle — if continuous, restart
          if (isContinuousRef.current && !pendingIntentRef.current) {
            _scheduleRestart(300)
          }
        }
        break

      case "confirmation_required":
        isProcessingRef.current = false
        setStatus("confirming")
        pendingIntentRef.current = msg.intent as Record<string, unknown>
        setPendingIntent(msg.intent as Record<string, unknown>)
        setLastResponse(msg.message || "")
        onConfirmRequired?.(msg.message || "", msg.intent as Record<string, unknown>)
        break

      case "audio_reply":
      case "audio_response": {
        const audioData = msg.data || msg.audio
        if (audioData) playAudioB64(audioData)
        break
      }

      case "result":
      case "action_complete": {
        const resText = msg.text || msg.message || ""
        setLastResponse(resText)
        pendingIntentRef.current = null
        setPendingIntent(null)
        onComplete?.(msg.success ?? true, resText)
        onResponse?.(resText)
        // Don't restart yet — audio_reply comes immediately after
        // If no audio follows within 1.5s, restart ourselves
        if (isContinuousRef.current) {
          _scheduleRestart(2000) // fallback if no audio comes
        } else {
          isProcessingRef.current = false
        }
        break
      }

      case "clarification":
        isProcessingRef.current = false
        if (isContinuousRef.current) _scheduleRestart(500)
        else setStatus("listening")
        break

      case "cancelled":
        isProcessingRef.current = false
        pendingIntentRef.current = null
        setPendingIntent(null)
        setCurrentStep("")
        if (!isPlayingAudioRef.current) {
          if (isContinuousRef.current) _scheduleRestart(400)
          else setStatus("idle")
        }
        break

      case "deactivate":
        isContinuousRef.current = false
        setIsContinuous(false)
        isProcessingRef.current = false
        pendingIntentRef.current = null
        setPendingIntent(null)
        setCurrentStep("")
        _clearRestartTimer()
        if (msg.text) {
          setLastResponse(msg.text)
          onResponse?.(msg.text)
        }
        break

      case "error":
        isProcessingRef.current = false
        setCurrentStep("")
        if (!isPlayingAudioRef.current) {
          setStatus("error")
          // In continuous mode, recover after a short delay
          if (isContinuousRef.current) _scheduleRestart(2000)
        }
        onError?.(msg.message || "Unknown error")
        break

      case "pong":
        break
    }
  }, [onTranscript, onIntent, onResponse, onConfirmRequired, onComplete, onError, playAudioB64, _scheduleRestart, _clearRestartTimer])

  // ── CONNECT WEBSOCKET ──
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN ||
        wsRef.current?.readyState === WebSocket.CONNECTING) return

    const ws = new WebSocket(`${wsUrl}/ws/voice/${userId}`)
    wsRef.current = ws

    ws.onopen = () => {
      console.log("🔌 ActOS WebSocket connected")
      if (pendingTextCommandRef.current) {
        ws.send(JSON.stringify({
          type: "text_command",
          text: pendingTextCommandRef.current,
          session_id: `sess_${userId}`,
        }))
        setStatus("processing")
        pendingTextCommandRef.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg: VoiceEvent = JSON.parse(event.data)
        handleServerMessage(msg)
      } catch (err) {
        console.error("Failed to parse WS message:", err)
      }
    }

    ws.onerror = () => {
      console.error("❌ WebSocket error")
      setStatus("error")
      onError?.("WebSocket connection failed")
    }

    ws.onclose = () => {
      console.log("🔌 WebSocket disconnected")
      if (!isContinuousRef.current) setStatus("idle")
      // In continuous mode, auto-reconnect after 2s
      else {
        setTimeout(() => {
          if (isContinuousRef.current) connect()
        }, 2000)
      }
    }
  }, [userId, wsUrl, handleServerMessage, onError])

  // ── AUTO-STOP (called from VAD loop) ──
  const _autoStopListening = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop()
      setStatus("processing")
    }
  }, [])

  // ── START RECORDING ──
  const startListening = useCallback(async () => {
    // Guards
    if (isProcessingRef.current || isPlayingAudioRef.current) return
    if (mediaRecorderRef.current?.state === "recording") return
    if (status === "confirming") return

    _cleanupRecording() // cleanup any stale recording
    _clearRestartTimer()

    try {
      lastVoiceTimeRef.current = Date.now()
      hasSpokenRef.current = false
      setCurrentStep("")

      connect()

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      currentStreamRef.current = stream

      // Web Audio API setup
      const AudioCtx = (window.AudioContext || (window as any).webkitAudioContext)
      const ctx = new AudioCtx()
      audioContextRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 64
      source.connect(analyser)
      analyserRef.current = analyser

      // VAD animation loop
      const updateWaveform = () => {
        if (!analyserRef.current) return
        const data = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(data)
        setWaveformData(Array.from(data).map(v => v / 255))

        const avgVolume = data.reduce((a, b) => a + b, 0) / data.length / 255
        const now = Date.now()

        if (avgVolume > VAD_VOLUME_THRESHOLD) {
          lastVoiceTimeRef.current = now
          hasSpokenRef.current = true
        }

        // Stop after silence post-speech
        if (hasSpokenRef.current && (now - lastVoiceTimeRef.current > VAD_SILENCE_AFTER_SPEECH)) {
          _autoStopListening()
          return
        }

        // Timeout without any speech
        if (!hasSpokenRef.current && (now - lastVoiceTimeRef.current > VAD_MAX_SILENCE_BEFORE_SPEECH)) {
          _autoStopListening()
          return
        }

        animFrameRef.current = requestAnimationFrame(updateWaveform)
      }
      updateWaveform()

      // MediaRecorder setup
      const mimes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4", ""]
      const mimeType = mimes.find(m => !m || (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(m))) || ""
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      audioChunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        const actualMimeType = recorder.mimeType || mimeType || "audio/webm"
        const containerFormat = actualMimeType.split("/")[1]?.split(";")[0] || "webm"
        const blob = new Blob(audioChunksRef.current, { type: actualMimeType })

        _cleanupRecording()

        // Skip silence/noise
        if (blob.size < MIN_AUDIO_BYTES) {
          console.log(`🔇 Audio too small (${blob.size}B) — skipping`)
          if (isContinuousRef.current && !isProcessingRef.current) _scheduleRestart(300)
          else setStatus("idle")
          return
        }

        // Convert to base64
        const arrayBuffer = await blob.arrayBuffer()
        const base64 = btoa(
          new Uint8Array(arrayBuffer).reduce((data, byte) => data + String.fromCharCode(byte), "")
        )

        // Send to backend
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: "audio_chunk",
            data: base64,
            format: containerFormat,
            session_id: `sess_${userId}`,
          }))
          wsRef.current.send(JSON.stringify({ type: "audio_end" }))
        } else {
          // WS not ready — restart mic if continuous
          if (isContinuousRef.current) _scheduleRestart(1000)
          else setStatus("idle")
        }
      }

      recorder.start()
      setStatus("listening")
      console.log("🎙️ Listening...")

    } catch (err: any) {
      console.error("❌ Mic error:", err)
      setStatus("error")
      onError?.(`Microphone access denied: ${err?.message || "Unknown error"}`)
    }
  }, [connect, userId, onError, status, _cleanupRecording, _clearRestartTimer, _scheduleRestart, _autoStopListening])

  // ── START CONTINUOUS MODE ──
  const startContinuous = useCallback(() => {
    isContinuousRef.current = true
    setIsContinuous(true)
    isProcessingRef.current = false
    startListening()
  }, [startListening])

  // ── STOP CONTINUOUS MODE ──
  const stopListening = useCallback(() => {
    isContinuousRef.current = false
    setIsContinuous(false)
    isProcessingRef.current = false
    _clearRestartTimer()
    cancelAnimationFrame(animFrameRef.current)

    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop()
    }
    _cleanupRecording()

    if (!isPlayingAudioRef.current) {
      setStatus("idle")
    }
    setCurrentStep("")
  }, [_cleanupRecording, _clearRestartTimer])

  // ── SEND TEXT COMMAND ──
  const sendTextCommand = useCallback((text: string) => {
    setCurrentStep("")
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "text_command",
        text,
        session_id: `sess_${userId}`,
      }))
      setStatus("processing")
      isProcessingRef.current = true
    } else {
      pendingTextCommandRef.current = text
      connect()
    }
  }, [connect, userId])

  // ── CONFIRM ACTION ──
  const confirmAction = useCallback((confirmed: boolean) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "confirm",
        confirmed,
        session_id: `sess_${userId}`,
      }))
    }
    if (!confirmed) {
      pendingIntentRef.current = null
      setPendingIntent(null)
      setCurrentStep("")
      if (isContinuousRef.current) _scheduleRestart(500)
      else setStatus("idle")
    } else {
      setStatus("processing")
      isProcessingRef.current = true
    }
  }, [userId, _scheduleRestart])

  // ── WS PING KEEPALIVE ──
  useEffect(() => {
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }))
      }
    }, 20000)
    return () => clearInterval(interval)
  }, [])

  // ── Keep refs in sync ──
  useEffect(() => { startListeningRef.current = startListening }, [startListening])
  useEffect(() => { stopListeningRef.current = stopListening }, [stopListening])

  // ── Cleanup on unmount ──
  useEffect(() => {
    return () => {
      isContinuousRef.current = false
      _clearRestartTimer()
      wsRef.current?.close()
      cancelAnimationFrame(animFrameRef.current)
      _cleanupRecording()
    }
  }, [_cleanupRecording, _clearRestartTimer])

  return {
    status,
    transcript,
    lastResponse,
    currentStep,
    detectedLanguage,
    pendingIntent,
    waveformData,
    startListening,
    stopListening,
    startContinuous,
    sendTextCommand,
    confirmAction,
    isContinuous,
    isListening: status === "listening",
    isProcessing: status === "processing",
    isSpeaking: status === "speaking",
    isConfirming: status === "confirming",
  }
}
