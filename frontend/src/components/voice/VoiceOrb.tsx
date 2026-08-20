"use client"
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"

type Status = "idle" | "listening" | "processing" | "speaking" | "confirming" | "error"

interface VoiceOrbProps {
  status?: Status
  waveformData?: number[]
  onRecordToggle?: () => void
}

const STATUS_COLORS: Record<Status, string> = {
  idle:       "text-[#3d5277]",
  listening:  "text-teal",
  processing: "text-cyan",
  speaking:   "text-gold",
  confirming: "text-cyan",
  error:      "text-danger",
}

const STATUS_LABELS: Record<Status, string> = {
  idle:       "Tap to activate",
  listening:  "Listening...",
  processing: "Processing...",
  speaking:   "Speaking...",
  confirming: "Confirm Action...",
  error:      "Voice Error",
}

export default function VoiceOrb({ status: propStatus, waveformData, onRecordToggle }: VoiceOrbProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [localStatus, setLocalStatus] = useState<Status>("idle")
  const status = propStatus !== undefined ? propStatus : localStatus
  const angleRef = useRef(0)
  const angle2Ref = useRef(Math.PI)
  const amplitudesRef = useRef(Array(72).fill(0))
  const frameRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")!
    const cx = 150, cy = 150, BASE_R = 82
    const ACTIVE = ["listening", "speaking", "processing"]
    const isActive = ACTIVE.includes(status)

    const draw = () => {
      ctx.clearRect(0, 0, 300, 300)
      const time = Date.now() / 1000

      // ── Background glow ──
      const bgGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, BASE_R + 50)
      if (status === "listening") {
        bgGlow.addColorStop(0, "rgba(0,229,200,0.06)")
        bgGlow.addColorStop(1, "transparent")
      } else if (status === "speaking") {
        bgGlow.addColorStop(0, "rgba(240,180,48,0.05)")
        bgGlow.addColorStop(1, "transparent")
      } else if (status === "error") {
        bgGlow.addColorStop(0, "rgba(255,77,106,0.05)")
        bgGlow.addColorStop(1, "transparent")
      } else {
        bgGlow.addColorStop(0, "rgba(94,160,255,0.04)")
        bgGlow.addColorStop(1, "transparent")
      }
      ctx.beginPath()
      ctx.arc(cx, cy, BASE_R + 60, 0, Math.PI * 2)
      ctx.fillStyle = bgGlow
      ctx.fill()

      // ── Static orbit rings ──
      const ringAlphas = isActive ? [0.12, 0.06, 0.03] : [0.05, 0.025, 0.01]
      for (let i = 0; i < 3; i++) {
        ctx.beginPath()
        ctx.arc(cx, cy, BASE_R + 18 + i * 22, 0, Math.PI * 2)
        const col = status === "listening" ? `rgba(0,229,200,${ringAlphas[i]})` : `rgba(94,160,255,${ringAlphas[i]})`
        ctx.strokeStyle = col; ctx.lineWidth = i === 0 ? 0.75 : 0.4; ctx.stroke()
      }

      // ── Rotating halo arcs ──
      const arcColor = status === "listening" ? "rgba(0,229,200,0.7)" : status === "speaking" ? "rgba(240,180,48,0.6)" : status === "error" ? "rgba(255,77,106,0.6)" : "rgba(94,160,255,0.45)"
      ctx.beginPath()
      ctx.arc(cx, cy, BASE_R + 4, angleRef.current, angleRef.current + Math.PI * 0.5)
      ctx.strokeStyle = arcColor; ctx.lineWidth = 1.5; ctx.stroke()

      ctx.beginPath()
      ctx.arc(cx, cy, BASE_R + 4, angle2Ref.current, angle2Ref.current + Math.PI * 0.3)
      ctx.strokeStyle = arcColor.replace("0.7", "0.35").replace("0.45", "0.25"); ctx.lineWidth = 0.75; ctx.stroke()

      const speed = status === "listening" ? 0.05 : status === "processing" ? 0.07 : 0.012
      angleRef.current += speed
      angle2Ref.current -= speed * 0.7

      // ── Waveform ring ──
      for (let i = 0; i < 72; i++) {
        let target: number
        if (waveformData && waveformData.length > 0) {
          target = waveformData[i % waveformData.length] * 50 + 3
        } else if (status === "listening") {
          target = Math.abs(Math.sin(time * 3.5 + i * 0.22)) * 26 + Math.random() * 12
        } else if (status === "processing") {
          target = Math.abs(Math.sin(time * 5 + i * 0.18)) * 14 + 4
        } else if (status === "speaking") {
          target = Math.abs(Math.sin(time * 4 + i * 0.25)) * 20 + 5
        } else {
          target = Math.abs(Math.sin(time * 0.8 + i * 0.15)) * 4 + 2
        }
        amplitudesRef.current[i] += (target - amplitudesRef.current[i]) * 0.18
      }

      const waveGrad = ctx.createLinearGradient(cx - BASE_R, cy, cx + BASE_R, cy)
      if (status === "listening") {
        waveGrad.addColorStop(0, "rgba(0,229,200,0.4)")
        waveGrad.addColorStop(0.5, "rgba(0,229,200,0.8)")
        waveGrad.addColorStop(1, "rgba(0,229,200,0.4)")
      } else {
        waveGrad.addColorStop(0, "rgba(94,160,255,0.3)")
        waveGrad.addColorStop(0.5, "rgba(94,160,255,0.65)")
        waveGrad.addColorStop(1, "rgba(94,160,255,0.3)")
      }

      ctx.beginPath()
      for (let i = 0; i <= 72; i++) {
        const idx = i % 72
        const a = (idx / 72) * Math.PI * 2 - Math.PI / 2
        const r = BASE_R + amplitudesRef.current[idx]
        const x = cx + Math.cos(a) * r
        const y = cy + Math.sin(a) * r
        if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y)
      }
      ctx.closePath()
      ctx.strokeStyle = waveGrad
      ctx.lineWidth = isActive ? 1.8 : 1
      ctx.stroke()

      // ── Center radial fill ──
      const centerCol = status === "listening" ? "0,229,200"
        : status === "speaking" ? "240,180,48"
        : status === "error" ? "255,77,106"
        : "94,160,255"
      const fill = ctx.createRadialGradient(cx, cy, 0, cx, cy, BASE_R)
      fill.addColorStop(0, `rgba(${centerCol},${isActive ? 0.18 : 0.07})`)
      fill.addColorStop(0.6, `rgba(${centerCol},${isActive ? 0.06 : 0.02})`)
      fill.addColorStop(1, "transparent")
      ctx.beginPath(); ctx.arc(cx, cy, BASE_R, 0, Math.PI * 2)
      ctx.fillStyle = fill; ctx.fill()

      // ── Inner solid circle ──
      const innerR = 36
      const innerGrad = ctx.createRadialGradient(cx - 8, cy - 8, 0, cx, cy, innerR)
      innerGrad.addColorStop(0, `rgba(${centerCol},0.3)`)
      innerGrad.addColorStop(1, `rgba(${centerCol},0.1)`)
      ctx.beginPath(); ctx.arc(cx, cy, innerR, 0, Math.PI * 2)
      ctx.fillStyle = innerGrad; ctx.fill()
      ctx.strokeStyle = `rgba(${centerCol},0.5)`; ctx.lineWidth = 1; ctx.stroke()

      frameRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(frameRef.current)
  }, [status, waveformData])

  const isListening = status === "listening"

  return (
    <div className="relative flex flex-col items-center gap-3 select-none">
      {/* Ping rings behind the orb */}
      {isListening && (
        <div className="absolute inset-0 flex items-start justify-center" style={{ paddingTop: "12px" }}>
          <div className="w-[300px] h-[300px] relative">
            <div className="absolute inset-[-12px] rounded-full border border-teal/15 animate-voice-ping" />
            <div className="absolute inset-[-24px] rounded-full border border-teal/08 animate-voice-ping" style={{ animationDelay: "0.6s" }} />
          </div>
        </div>
      )}

      <canvas ref={canvasRef} width={300} height={300} className="relative z-10" />

      {/* Center button overlay */}
      <div className="absolute z-20 flex flex-col items-center justify-center" style={{ top: 0, left: "50%", transform: "translateX(-50%)", width: 300, height: 300 }}>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.92 }}
          onClick={() => {
            if (onRecordToggle) {
              onRecordToggle()
            } else {
              setLocalStatus(s => s === "idle" ? "listening" : "idle")
            }
          }}
          className="relative w-[72px] h-[72px] rounded-full flex items-center justify-center transition-all duration-300"
          style={{
            background: isListening
              ? "linear-gradient(135deg, #00e5c8, #5ea0ff)"
              : status === "error"
              ? "linear-gradient(135deg, #ff4d6a, #cc3355)"
              : "linear-gradient(135deg, #5ea0ff, #00e5c8)",
            boxShadow: isListening
              ? "0 0 30px rgba(0,229,200,0.5), 0 0 60px rgba(0,229,200,0.2)"
              : "0 0 20px rgba(94,160,255,0.4), 0 0 40px rgba(94,160,255,0.15)"
          }}
        >
          {status === "listening" ? (
            // Stop icon
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <rect x="5" y="5" width="12" height="12" rx="2" fill="#020408" />
            </svg>
          ) : (
            // Mic icon
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <rect x="9" y="2" width="6" height="12" rx="3" fill="#020408" />
              <path d="M5 10a7 7 0 0014 0" stroke="#020408" strokeWidth="2" fill="none" strokeLinecap="round" />
              <line x1="12" y1="17" x2="12" y2="22" stroke="#020408" strokeWidth="2" strokeLinecap="round" />
              <line x1="8" y1="22" x2="16" y2="22" stroke="#020408" strokeWidth="2" strokeLinecap="round" />
            </svg>
          )}
        </motion.button>
      </div>

      {/* Status text */}
      <div className="relative z-10 flex flex-col items-center gap-0.5">
        <span className="text-[10px] font-bold tracking-[0.25em] uppercase text-[#3d5277]">ActOS</span>
        <span className={`text-[11px] tracking-widest font-medium transition-colors duration-300 ${STATUS_COLORS[status]}`}>
          {STATUS_LABELS[status]}
        </span>
      </div>
    </div>
  )
}
