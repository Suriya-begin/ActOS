"use client"
import { useEffect, useState } from "react"

const BOOT_LINES = [
  { text: "Initializing Neural Inference Core...", delay: 0 },
  { text: "Loading Samsung Samsung voice biometric module...", delay: 280 },
  { text: "Connecting to WebSocket voice gateway (ws://localhost:8000)...", delay: 520 },
  { text: "Bootstrapping LangGraph agent orchestration layer...", delay: 780 },
  { text: "Mounting PostgreSQL memory index + Pinecone embeddings...", delay: 1040 },
  { text: "Starting CrewAI multi-agent task scheduler...", delay: 1280 },
  { text: "Verifying zero-trust security protocols...", delay: 1520 },
  { text: "ActOS v2.0 ready — all systems nominal.", delay: 1800 },
]

export default function Loading() {
  const [progress, setProgress] = useState(0)
  const [visibleLines, setVisibleLines] = useState<number[]>([])

  useEffect(() => {
    const start = Date.now()
    const duration = 2800

    const tick = () => {
      const elapsed = Date.now() - start
      const pct = Math.min(100, Math.round((elapsed / duration) * 100))
      setProgress(pct)
      if (pct < 100) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)

    BOOT_LINES.forEach((line, i) => {
      setTimeout(() => setVisibleLines(prev => [...prev, i]), line.delay + 200)
    })
  }, [])

  return (
    <div className="fixed inset-0 bg-void flex flex-col items-center justify-center overflow-hidden z-50">
      {/* Animated grid */}
      <div className="absolute inset-0 bg-grid-cyan bg-grid animate-grid-pan opacity-60 pointer-events-none" />

      {/* Aurora blobs */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-aurora-1 blur-[100px] pointer-events-none animate-aurora" />
      <div className="absolute bottom-0 right-0 w-[600px] h-[400px] bg-aurora-2 blur-[120px] pointer-events-none animate-aurora" style={{ animationDelay: "-6s" }} />

      {/* Scan line overlay */}
      <div className="absolute inset-0 pointer-events-none scanline-overlay overflow-hidden" />

      {/* Center content */}
      <div className="relative z-10 flex flex-col items-center w-full max-w-lg px-8">

        {/* Animated Logo Ring */}
        <div className="relative w-32 h-32 mb-10">
          {/* Outer rotating ring */}
          <div className="absolute inset-0 rounded-full border border-dashed border-cyan/20 animate-spin-slower" />
          {/* Mid ring */}
          <div className="absolute inset-3 rounded-full border border-cyan/30 animate-halo" />
          {/* Inner glow circle */}
          <div className="absolute inset-6 rounded-full bg-gradient-to-br from-cyan/20 to-teal/10 border border-cyan/40 animate-orb-pulse flex items-center justify-center">
            {/* Hexagonal logo mark */}
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" className="drop-shadow-[0_0_12px_rgba(94,160,255,0.8)]">
              <polygon
                points="20,2 36,11 36,29 20,38 4,29 4,11"
                stroke="#5ea0ff"
                strokeWidth="1.5"
                fill="rgba(94,160,255,0.08)"
              />
              <polygon
                points="20,8 30,14 30,26 20,32 10,26 10,14"
                stroke="#00e5c8"
                strokeWidth="1"
                fill="rgba(0,229,200,0.05)"
              />
              <text x="50%" y="55%" textAnchor="middle" dominantBaseline="middle" fill="#ffffff" fontSize="11" fontWeight="700" fontFamily="Samsung Sharp Sans, sans-serif" letterSpacing="0.5">OS</text>
            </svg>
          </div>
          {/* Pulse rings */}
          <div className="absolute inset-0 rounded-full border border-cyan/20 animate-voice-ping" />
          <div className="absolute inset-0 rounded-full border border-cyan/10 animate-voice-ping" style={{ animationDelay: "0.5s" }} />
        </div>

        {/* Brand name */}
        <h1 className="font-display font-bold text-3xl tracking-[0.25em] uppercase mb-1">
          <span className="text-gradient-cyan">Act</span>
          <span className="text-white">OS</span>
        </h1>
        <p className="text-[10px] tracking-[0.35em] uppercase text-[#3d5277] mb-10">
          Neural Voice Operating System
        </p>

        {/* Progress bar */}
        <div className="w-full mb-2">
          <div className="flex justify-between items-center mb-2">
            <span className="text-[10px] tracking-widest uppercase text-[#3d5277] font-bold">System Boot</span>
            <span className="text-[11px] font-mono text-cyan tabular-nums">{progress}%</span>
          </div>
          <div className="w-full h-[2px] bg-surface rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan via-teal to-cyan"
              style={{ width: `${progress}%`, transition: "width 0.1s linear",
                boxShadow: "0 0 8px rgba(94,160,255,0.8), 0 0 20px rgba(0,229,200,0.4)" }}
            />
          </div>
        </div>

        {/* Boot log terminal */}
        <div className="w-full mt-6 font-mono">
          {BOOT_LINES.map((line, i) => (
            <div
              key={i}
              className="flex items-start gap-2 text-[10px] leading-6 transition-all duration-300"
              style={{ opacity: visibleLines.includes(i) ? 1 : 0, transform: visibleLines.includes(i) ? "translateY(0)" : "translateY(4px)" }}
            >
              <span className="text-teal shrink-0">›</span>
              <span className={i === BOOT_LINES.length - 1 ? "text-teal font-bold" : "text-[#3d5277]"}>
                {line.text}
                {i === visibleLines[visibleLines.length - 1] && i < BOOT_LINES.length - 1 && (
                  <span className="inline-block w-[6px] h-[10px] bg-cyan ml-1 animate-blink" />
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
