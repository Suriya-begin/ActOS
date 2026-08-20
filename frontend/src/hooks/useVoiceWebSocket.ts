"use client"
import { useEffect, useRef, useState, useCallback } from "react"

type WSStatus = "disconnected" | "connecting" | "connected" | "listening"
type WSMessage = { type: string; text?: string; data?: string; language?: string }

export function useVoiceWebSocket(userId: string) {
  const ws = useRef<WebSocket | null>(null)
  const [wsStatus, setWsStatus]     = useState<WSStatus>("disconnected")
  const [transcript, setTranscript] = useState("")
  const [result, setResult]         = useState("")
  const [agentStatus, setAgentStatus] = useState("")

  const connect = useCallback(() => {
    const url = `${process.env.NEXT_PUBLIC_WS_URL}/ws/voice/${userId}`
    setWsStatus("connecting")
    ws.current = new WebSocket(url)

    ws.current.onopen  = () => setWsStatus("connected")
    ws.current.onclose = () => setWsStatus("disconnected")

    ws.current.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data)
      if (msg.type === "transcript")  setTranscript(msg.text || "")
      if (msg.type === "result")      setResult(msg.text || "")
      if (msg.type === "status")      setAgentStatus(msg.text || "")
      if (msg.type === "audio_reply") {
        // Decode base64 audio and play
        const audioData = atob(msg.data || "")
        const audioArray = new Uint8Array(audioData.length)
        for (let i = 0; i < audioData.length; i++) audioArray[i] = audioData.charCodeAt(i)
        const blob = new Blob([audioArray], { type: "audio/mpeg" })
        const audio = new Audio(URL.createObjectURL(blob))
        audio.play()
      }
    }
  }, [userId])

  const sendAudioChunk = useCallback((chunk: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const base64 = btoa(
        new Uint8Array(chunk).reduce((data, byte) => data + String.fromCharCode(byte), "")
      )
      ws.current.send(JSON.stringify({ type: "audio_chunk", data: base64 }))
    }
  }, [])

  const endAudio = useCallback(() => {
    ws.current?.send(JSON.stringify({ type: "audio_end" }))
  }, [])

  const confirmAction = useCallback(() => {
    ws.current?.send(JSON.stringify({ type: "confirm_action" }))
  }, [])

  useEffect(() => { connect(); return () => ws.current?.close() }, [connect])

  return { wsStatus, transcript, result, agentStatus, sendAudioChunk, endAudio, confirmAction }
}
