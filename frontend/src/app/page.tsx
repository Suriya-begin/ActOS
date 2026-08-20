"use client"
import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { useAuth } from "@/hooks/useAuth"

// ─── Animated Counter ────────────────────────────────────────
function Counter({ to, suffix = "", prefix = "", duration = 2200 }: { to: number; suffix?: string; prefix?: string; duration?: number }) {
  const [val, setVal] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return
      obs.disconnect()
      const start = performance.now()
      const tick = (now: number) => {
        const p = Math.min((now - start) / duration, 1)
        setVal(Math.floor((1 - Math.pow(1 - p, 3)) * to))
        if (p < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }, { threshold: 0.3 })
    if (ref.current) obs.observe(ref.current)
    return () => obs.disconnect()
  }, [to, duration])
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>
}

// ─── Typewriter Demo ─────────────────────────────────────────
const DEMOS = [
  { cmd: '"Send a message to Sarah saying I\'ll be late"',       result: "Message sent to Sarah ✓" },
  { cmd: '"Book a cab to the airport at 6 AM tomorrow"',        result: "Cab booked for 6:00 AM ✓" },
  { cmd: '"Summarize my unread emails from this week"',         result: "Found 12 emails, summary ready ✓" },
  { cmd: '"Set a reminder for my 3 PM meeting"',                result: "Reminder set for 3:00 PM ✓" },
  { cmd: '"Search and book the cheapest flight to London"',     result: "3 options found, showing best deal ✓" },
  { cmd: '"Play focus music and block distractions for 2 hours"', result: "Focus mode activated ✓" },
]

function TerminalDemo() {
  const [idx, setIdx] = useState(0)
  const [phase, setPhase] = useState<"typing" | "thinking" | "done" | "clearing">("typing")
  const [text, setText] = useState("")
  const full = DEMOS[idx].cmd
  const result = DEMOS[idx].result

  useEffect(() => {
    if (phase === "typing") {
      if (text.length < full.length) {
        const t = setTimeout(() => setText(full.slice(0, text.length + 1)), 42)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => setPhase("thinking"), 600)
        return () => clearTimeout(t)
      }
    }
    if (phase === "thinking") {
      const t = setTimeout(() => setPhase("done"), 1200)
      return () => clearTimeout(t)
    }
    if (phase === "done") {
      const t = setTimeout(() => setPhase("clearing"), 2400)
      return () => clearTimeout(t)
    }
    if (phase === "clearing") {
      const t = setTimeout(() => {
        setText("")
        setIdx(i => (i + 1) % DEMOS.length)
        setPhase("typing")
      }, 300)
      return () => clearTimeout(t)
    }
  }, [phase, text, full])

  return (
    <div className="relative rounded-2xl overflow-hidden border border-[rgba(94,160,255,0.15)]"
      style={{ background: "rgba(4,9,18,0.95)", boxShadow: "0 0 60px rgba(94,160,255,0.08), 0 20px 60px rgba(0,0,0,0.5)" }}>
      {/* Title bar */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-[rgba(94,160,255,0.08)]">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-[rgba(255,77,106,0.6)]" />
          <div className="w-3 h-3 rounded-full bg-[rgba(240,180,48,0.6)]" />
          <div className="w-3 h-3 rounded-full bg-[rgba(0,229,200,0.6)]" />
        </div>
        <span className="ml-3 text-[9px] uppercase tracking-widest text-[#3d5277] font-bold">ActOS — AI Pipeline</span>
        <div className="ml-auto flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
          <span className="text-[9px] text-teal font-bold uppercase tracking-widest">Live</span>
        </div>
      </div>
      {/* Body */}
      <div className="p-6 space-y-3 min-h-[160px]" style={{ fontFamily: "'Courier New', monospace", fontSize: "13px" }}>
        <div className="flex items-start gap-3">
          <span className="text-cyan shrink-0">🎙</span>
          <span className="text-white">{text}<span className="animate-blink">|</span></span>
        </div>
        {(phase === "thinking" || phase === "done") && (
          <div className="flex items-center gap-2 pl-7">
            <span className="text-[#f0b430]">→</span>
            <span className="text-[#f0b430]">
              {phase === "thinking"
                ? <span className="flex items-center gap-1.5">Processing<span className="inline-flex gap-0.5 ml-1">{[0,1,2].map(i => <span key={i} className="w-1 h-1 rounded-full bg-[#f0b430] animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />)}</span></span>
                : "Intent classified · Agents dispatched"
              }
            </span>
          </div>
        )}
        {phase === "done" && (
          <div className="flex items-start gap-2 pl-7">
            <span className="text-teal">✓</span>
            <span className="text-teal font-medium">{result}</span>
          </div>
        )}
      </div>
      {/* Progress bar */}
      <div className="h-0.5 bg-[rgba(94,160,255,0.06)]">
        <div className="h-full bg-gradient-to-r from-cyan to-teal transition-all duration-1000"
          style={{ width: phase === "typing" ? `${(text.length / full.length) * 60}%` : phase === "thinking" ? "80%" : phase === "done" ? "100%" : "0%" }} />
      </div>
    </div>
  )
}

// ─── Data ────────────────────────────────────────────────────
const STATS = [
  { label: "Commands Processed",  value: 2500000, suffix: "+",  prefix: "", color: "#5ea0ff", icon: "⚡" },
  { label: "Intent Accuracy",      value: 98,      suffix: "%",  prefix: "", color: "#00e5c8", icon: "🎯" },
  { label: "Avg. Response Time",   value: 1,       suffix: ".2s",prefix: "", color: "#f0b430", icon: "⏱" },
  { label: "Integrations",         value: 50,      suffix: "+",  prefix: "", color: "#5ea0ff", icon: "🔗" },
]

const CAPABILITIES = [
  { label: "Messaging & Email",      icon: "💬", desc: "WhatsApp, Gmail, Slack" },
  { label: "Calendar & Scheduling", icon: "📅", desc: "Google Calendar, reminders" },
  { label: "Browser Automation",    icon: "🌐", desc: "Web research, form fill" },
  { label: "Music & Media",         icon: "🎵", desc: "Spotify, YouTube" },
  { label: "Travel & Booking",      icon: "✈️", desc: "Flights, cabs, hotels" },
  { label: "Smart Search",          icon: "🔍", desc: "Web research & summaries" },
  { label: "File Management",       icon: "📁", desc: "Read, write, organize" },
  { label: "Smart Home",            icon: "🏠", desc: "IoT device control" },
  { label: "Finance & Payments",    icon: "💳", desc: "Invoices, transfers" },
  { label: "Code & Dev Tools",      icon: "💻", desc: "GitHub, CI/CD" },
  { label: "Note Taking",           icon: "📝", desc: "Notion, Obsidian" },
  { label: "Voice Biometrics",      icon: "🔐", desc: "Secure authentication" },
]

const HOW = [
  { n: "01", title: "Speak Naturally",     desc: "Say anything in any language. ActOS captures your voice in real-time.", icon: "🎙️", c: "#5ea0ff" },
  { n: "02", title: "AI Understands",      desc: "GPT-4o extracts intent, context, entities, and urgency from your words.", icon: "🧠", c: "#00e5c8" },
  { n: "03", title: "Agents Execute",      desc: "Specialized AI agents take action across apps, browsers, and services.", icon: "⚡", c: "#f0b430" },
  { n: "04", title: "Voice Confirms",      desc: "Natural voice feedback confirms what was done. Memory updated for next time.", icon: "✅", c: "#5ea0ff" },
]

const TECH = [
  "GPT-4o", "Whisper v3", "ElevenLabs TTS", "LangGraph", "CrewAI",
  "FastAPI", "PostgreSQL", "Pinecone", "Redis", "Playwright",
  "Next.js 14", "WebSocket", "NextAuth.js", "Python 3.11", "TypeScript",
]

// ─── Main ────────────────────────────────────────────────────
export default function LandingPage() {
  const [mounted, setMounted] = useState(false)
  const { isSignedIn, isLoaded } = useAuth()

  useEffect(() => { setMounted(true) }, [])
  if (!mounted) return null

  return (
    <main className="relative min-h-screen bg-void flex flex-col overflow-x-hidden font-sans">

      {/* ══ BACKGROUND SYSTEM ══════════════════════════════════ */}
      <div className="fixed inset-0 pointer-events-none z-0">
        {/* Deep navy-black base */}
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse 130% 90% at 60% 0%, rgba(5,14,36,1) 0%, rgba(2,4,8,1) 55%)"
        }} />
        {/* Animated grid */}
        <div className="absolute inset-0" style={{
          backgroundImage: "linear-gradient(rgba(94,160,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(94,160,255,0.03) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
          animation: "gridPan 14s linear infinite"
        }} />
        {/* Hero glow */}
        <div className="absolute top-[-15%] left-[20%] w-[900px] h-[600px]" style={{
          background: "radial-gradient(ellipse, rgba(94,160,255,0.12) 0%, rgba(0,229,200,0.04) 40%, transparent 70%)",
          filter: "blur(90px)",
          animation: "auroraDrift 22s ease infinite"
        }} />
        {/* Left violet glow */}
        <div className="absolute top-[40%] left-[-5%] w-[450px] h-[450px]" style={{
          background: "radial-gradient(circle, rgba(124,58,237,0.07) 0%, transparent 70%)",
          filter: "blur(80px)",
          animation: "auroraDrift 28s ease infinite",
          animationDelay: "-10s"
        }} />
        {/* Right teal glow */}
        <div className="absolute bottom-[5%] right-[-5%] w-[550px] h-[450px]" style={{
          background: "radial-gradient(circle, rgba(0,229,200,0.07) 0%, transparent 70%)",
          filter: "blur(100px)",
          animation: "auroraDrift 20s ease infinite",
          animationDelay: "-18s"
        }} />
        {/* Scan line */}
        <div className="absolute inset-0 scanline-overlay overflow-hidden" />
      </div>

      {/* ══ NAVBAR ═════════════════════════════════════════════ */}
      <nav className="relative z-30 sticky top-0 h-[68px] flex items-center justify-between px-6 md:px-12 glass-heavy border-b border-[rgba(94,160,255,0.07)]">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative">
            <svg width="32" height="32" viewBox="0 0 40 40" fill="none">
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" stroke="#5ea0ff" strokeWidth="1.5" fill="rgba(94,160,255,0.08)" />
              <polygon points="20,9 29,14 29,26 20,31 11,26 11,14" stroke="#00e5c8" strokeWidth="1" fill="rgba(0,229,200,0.06)" />
            </svg>
          </div>
          <span className="font-display font-bold text-[22px] tracking-widest">
            <span className="text-gradient-cyan">Act</span><span className="text-white">OS</span>
          </span>
        </Link>

        {/* Center nav */}
        <div className="hidden md:flex items-center gap-8 text-[11px] font-bold uppercase tracking-widest text-[#5a7095]">
          {[["#capabilities", "Capabilities"], ["#how", "How It Works"], ["#stack", "Stack"]].map(([href, label]) => (
            <a key={label} href={href} className="hover:text-white transition-colors duration-200">{label}</a>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-teal/20 bg-teal/5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-status-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
            </span>
            <span className="text-[9px] tracking-widest uppercase text-teal font-bold">Systems Online</span>
          </div>
          {isLoaded && isSignedIn ? (
            <Link href="/dashboard"
              className="text-[11px] uppercase tracking-widest font-bold text-void px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
              style={{ background: "linear-gradient(135deg, #5ea0ff, #00e5c8)", boxShadow: "0 0 20px rgba(94,160,255,0.3)" }}>
              Dashboard →
            </Link>
          ) : (
            <>
              <Link href="/auth/sign-in"
                className="text-[11px] uppercase tracking-widest font-bold text-[#7a92b8] hover:text-white px-4 py-2.5 rounded-xl border border-[rgba(94,160,255,0.12)] hover:border-cyan/30 transition-all">
                Sign In
              </Link>
              <Link href="/auth/sign-up"
                className="text-[11px] uppercase tracking-widest font-bold text-void px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5"
                style={{ background: "linear-gradient(135deg, #5ea0ff, #00e5c8)", boxShadow: "0 0 20px rgba(94,160,255,0.25)" }}>
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* ══ HERO ═══════════════════════════════════════════════ */}
      <section className="relative z-10 flex flex-col lg:flex-row items-center justify-between min-h-[88vh] max-w-7xl mx-auto w-full px-6 md:px-12 gap-16 py-16">

        {/* Left: Text */}
        <div className="flex-1 flex flex-col items-start">
          {/* Badge */}
          <div className="inline-flex items-center gap-2.5 mb-8 px-4 py-2 rounded-full border border-[rgba(94,160,255,0.2)] bg-[rgba(94,160,255,0.05)] animate-fade-slide-up">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-status-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
            </span>
            <span className="text-[9px] tracking-[0.3em] uppercase font-bold text-cyan">AI Voice Operating System · v2.0</span>
          </div>

          {/* Headline */}
          <h1 className="font-display font-extrabold leading-[0.9] tracking-tight mb-6 animate-fade-slide-up"
            style={{ fontSize: "clamp(52px, 7vw, 88px)", animationDelay: "0.05s" }}>
            <span className="block text-white">Your Voice.</span>
            <span className="block text-gradient-cyan">Any Action.</span>
            <span className="block text-white" style={{ fontSize: "60%", opacity: 0.5, marginTop: "0.15em", fontWeight: 700 }}>Instantly.</span>
          </h1>

          {/* Subtitle */}
          <p className="text-[#7a92b8] text-lg leading-relaxed max-w-lg mb-8 animate-fade-slide-up" style={{ animationDelay: "0.1s" }}>
            ActOS is the world&apos;s most advanced <strong className="text-white font-semibold">AI Voice Operating System</strong> — 
            speak naturally in any language and watch intelligent agents execute complex tasks across every app and service.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap gap-2 mb-10 animate-fade-slide-up" style={{ animationDelay: "0.15s" }}>
            {["Multilingual AI", "50+ Integrations", "Sub-second latency", "Privacy-first"].map(tag => (
              <span key={tag} className="px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-widest border border-[rgba(94,160,255,0.15)] text-[#7a92b8]" style={{ background: "rgba(10,22,40,0.6)" }}>
                {tag}
              </span>
            ))}
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-3 animate-fade-slide-up" style={{ animationDelay: "0.2s" }}>
            <Link href="/auth/sign-up"
              className="group relative flex items-center justify-center gap-3 px-8 py-4 rounded-2xl font-display font-bold text-sm tracking-widest uppercase text-void overflow-hidden transition-all duration-300 hover:-translate-y-0.5"
              style={{ background: "linear-gradient(135deg, #5ea0ff 0%, #00e5c8 100%)", boxShadow: "0 0 30px rgba(94,160,255,0.35), 0 4px 20px rgba(0,0,0,0.3)" }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polygon points="5,3 19,12 5,21" /></svg>
              Start Free
              <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            <Link href="/auth/sign-in"
              className="flex items-center justify-center gap-3 px-8 py-4 rounded-2xl font-display font-bold text-sm tracking-widest uppercase text-white border border-[rgba(94,160,255,0.2)] hover:border-cyan/40 hover:bg-[rgba(94,160,255,0.05)] transition-all duration-300 hover:-translate-y-0.5">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" /></svg>
              Sign In
            </Link>
          </div>

          <p className="mt-5 text-[11px] text-[#3d5277] animate-fade-slide-up" style={{ animationDelay: "0.25s" }}>
            No credit card required · Free forever · Works on any device
          </p>
        </div>

        {/* Right: Visual */}
        <div className="flex-1 flex flex-col items-center gap-8 animate-fade-slide-up" style={{ animationDelay: "0.15s" }}>
          {/* Orbital system */}
          <div className="relative flex items-center justify-center w-[340px] h-[340px]">
            {/* Outer rings */}
            <div className="absolute inset-0 rounded-full border border-dashed border-[rgba(94,160,255,0.06)] animate-spin-slower" />
            <div className="absolute inset-8 rounded-full border border-[rgba(94,160,255,0.1)] animate-halo" />
            <div className="absolute inset-16 rounded-full border border-[rgba(0,229,200,0.14)] animate-halo-reverse" />
            <div className="absolute inset-24 rounded-full border border-[rgba(94,160,255,0.2)] animate-halo" style={{ animationDuration: "5s" }} />
            {/* Core */}
            <div className="relative w-[90px] h-[90px] rounded-full animate-float" style={{
              background: "radial-gradient(circle at 35% 35%, rgba(94,160,255,0.3), rgba(0,229,200,0.1) 60%, transparent)",
              boxShadow: "0 0 60px rgba(94,160,255,0.5), 0 0 120px rgba(94,160,255,0.2)",
              border: "1px solid rgba(94,160,255,0.4)",
            }}>
              <div className="absolute inset-0 flex items-center justify-center">
                <svg width="38" height="38" viewBox="0 0 40 40" fill="none">
                  <polygon points="20,4 33,12 33,28 20,36 7,28 7,12" stroke="#5ea0ff" strokeWidth="1.5" fill="rgba(94,160,255,0.1)" />
                  <polygon points="20,10 27,14 27,26 20,30 13,26 13,14" stroke="#00e5c8" strokeWidth="1" fill="rgba(0,229,200,0.06)" />
                </svg>
              </div>
            </div>
            {/* Ping rings */}
            <div className="absolute w-[90px] h-[90px] rounded-full border border-cyan/20 animate-voice-ping" />
            <div className="absolute w-[90px] h-[90px] rounded-full border border-teal/10 animate-voice-ping" style={{ animationDelay: "0.75s" }} />
            {/* Orbiting capability dots */}
            {[
              { angle: 0,   color: "#5ea0ff", icon: "💬", label: "Message" },
              { angle: 60,  color: "#00e5c8", icon: "📅", label: "Calendar" },
              { angle: 120, color: "#f0b430", icon: "🌐", label: "Browse" },
              { angle: 180, color: "#5ea0ff", icon: "📧", label: "Email" },
              { angle: 240, color: "#00e5c8", icon: "🎵", label: "Music" },
              { angle: 300, color: "#f0b430", icon: "✈️", label: "Travel" },
            ].map(({ angle, color, icon, label }) => {
              const rad = (angle - 90) * Math.PI / 180
              const r = 130
              const x = 170 + r * Math.cos(rad)
              const y = 170 + r * Math.sin(rad)
              return (
                <div key={label} className="absolute flex flex-col items-center gap-1"
                  style={{ left: x - 22, top: y - 22 }}>
                  <div className="w-11 h-11 rounded-xl flex items-center justify-center text-lg border transition-all"
                    style={{
                      background: `${color}12`,
                      borderColor: `${color}30`,
                      boxShadow: `0 0 12px ${color}20`,
                    }}>
                    {icon}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Terminal demo */}
          <div className="w-full max-w-md">
            <TerminalDemo />
          </div>
        </div>
      </section>

      {/* ══ STATS ══════════════════════════════════════════════ */}
      <div className="relative z-10 border-t border-b border-[rgba(94,160,255,0.07)] py-12 px-6"
        style={{ background: "linear-gradient(180deg, rgba(6,13,22,0.5) 0%, rgba(2,4,8,0.7) 100%)" }}>
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {STATS.map(s => (
            <div key={s.label} className="text-center">
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="font-display font-extrabold text-4xl mb-1" style={{ color: s.color, textShadow: `0 0 20px ${s.color}50` }}>
                <Counter to={s.value} suffix={s.suffix} />
              </div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-[#3d5277] font-bold">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ══ CAPABILITIES ═══════════════════════════════════════ */}
      <section id="capabilities" className="relative z-10 py-28 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[10px] uppercase tracking-[0.35em] text-cyan font-bold mb-4">What ActOS Does</p>
            <h2 className="font-display font-extrabold text-white mb-4" style={{ fontSize: "clamp(30px, 5vw, 50px)", lineHeight: 1.1 }}>
              One Voice. <span className="text-gradient-cyan">Infinite Actions.</span>
            </h2>
            <p className="text-[#7a92b8] text-base max-w-xl mx-auto leading-relaxed">
              ActOS connects to every app and service you use — controlled entirely through natural conversation.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-16">
            {CAPABILITIES.map(c => (
              <div key={c.label}
                className="group flex flex-col gap-2 p-4 rounded-2xl border border-[rgba(94,160,255,0.1)] bg-[rgba(10,22,40,0.5)] hover:border-[rgba(94,160,255,0.25)] hover:bg-[rgba(10,22,40,0.8)] transition-all duration-300 hover:-translate-y-0.5 cursor-default">
                <span className="text-2xl">{c.icon}</span>
                <span className="text-[13px] font-bold text-white">{c.label}</span>
                <span className="text-[11px] text-[#3d5277]">{c.desc}</span>
              </div>
            ))}
          </div>

          {/* Deep feature cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {[
              { icon: "🎙️", tag: "Speech Engine",   title: "Real-Time Voice Intelligence",  desc: "OpenAI Whisper large-v3 transcribes your voice with 98% accuracy in any language. Native streaming via WebSocket — no delay, no lag.", accent: "#5ea0ff" },
              { icon: "🤖", tag: "Agentic Core",     title: "Multi-Agent Orchestration",     desc: "Specialized LangGraph agents coordinate across WhatsApp, browser, calendar, email — each an expert, all working in sync.", accent: "#00e5c8" },
              { icon: "🧬", tag: "Memory System",    title: "Persistent Intelligence",       desc: "Every interaction teaches ActOS about you. PostgreSQL + Pinecone vector store builds a rich, searchable memory of your preferences.", accent: "#f0b430" },
            ].map(f => (
              <div key={f.title}
                className="group relative p-7 rounded-3xl border overflow-hidden transition-all duration-300 hover:-translate-y-1.5"
                style={{ background: `${f.accent}08`, borderColor: `${f.accent}25` }}>
                <div className="absolute top-0 left-0 right-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${f.accent}50, transparent)` }} />
                <div className="text-3xl mb-4">{f.icon}</div>
                <p className="text-[9px] uppercase tracking-[0.25em] font-bold mb-2" style={{ color: f.accent }}>{f.tag}</p>
                <h3 className="font-display font-bold text-lg text-white mb-3">{f.title}</h3>
                <p className="text-[#7a92b8] text-sm leading-relaxed">{f.desc}</p>
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-3xl pointer-events-none"
                  style={{ background: `radial-gradient(circle at 50% 0%, ${f.accent}06, transparent 60%)` }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ HOW IT WORKS ═══════════════════════════════════════ */}
      <section id="how" className="relative z-10 py-28 px-6"
        style={{ background: "linear-gradient(180deg, transparent, rgba(5,12,28,0.6) 50%, transparent)" }}>
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[10px] uppercase tracking-[0.35em] text-teal font-bold mb-4">The Pipeline</p>
            <h2 className="font-display font-extrabold text-white mb-4" style={{ fontSize: "clamp(30px, 5vw, 50px)", lineHeight: 1.1 }}>
              From <span className="text-gradient-cyan">Word</span> to <span className="text-gradient-cyan">Result</span> in 1.2s
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-14 left-[12%] right-[12%] h-px"
              style={{ background: "linear-gradient(90deg, #5ea0ff40, #00e5c840, #f0b43040, #5ea0ff40)" }} />
            {HOW.map((h, i) => (
              <div key={h.n} className="flex flex-col items-center text-center">
                <div className="relative w-[72px] h-[72px] rounded-2xl mb-5 flex items-center justify-center text-3xl border transition-all"
                  style={{ background: `${h.c}12`, borderColor: `${h.c}25`, boxShadow: `0 0 20px ${h.c}15` }}>
                  {h.icon}
                  <div className="absolute -top-2.5 -right-2.5 w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-extrabold text-void"
                    style={{ background: h.c }}>
                    {h.n}
                  </div>
                </div>
                <h3 className="font-display font-bold text-[15px] text-white mb-2">{h.title}</h3>
                <p className="text-[#7a92b8] text-xs leading-relaxed">{h.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ LIVE DEMO TERMINAL ═════════════════════════════════ */}
      <section className="relative z-10 py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-[10px] uppercase tracking-[0.35em] text-cyan font-bold mb-3">Live Session</p>
            <h2 className="font-display font-extrabold text-white" style={{ fontSize: "clamp(26px, 4vw, 42px)" }}>
              See ActOS <span className="text-gradient-cyan">Think in Real-Time</span>
            </h2>
          </div>
          <div className="rounded-3xl border border-[rgba(94,160,255,0.12)] overflow-hidden"
            style={{ background: "rgba(4,9,18,0.95)", boxShadow: "0 0 60px rgba(94,160,255,0.08), 0 20px 60px rgba(0,0,0,0.5)" }}>
            {/* Title bar */}
            <div className="flex items-center gap-2 px-5 py-3.5 border-b border-[rgba(94,160,255,0.08)]">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(255,77,106,0.6)" }} />
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(240,180,48,0.6)" }} />
                <div className="w-3 h-3 rounded-full" style={{ background: "rgba(0,229,200,0.6)" }} />
              </div>
              <span className="ml-3 text-[9px] uppercase tracking-widest text-[#3d5277] font-bold">ActOS Neural Pipeline — Session Active</span>
              <div className="ml-auto flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-teal animate-pulse" />
                <span className="text-[9px] text-teal font-bold uppercase tracking-widest">Active</span>
              </div>
            </div>
            <div className="p-7 font-mono text-[12.5px] space-y-3" style={{ fontFamily: "'Courier New', monospace" }}>
              {[
                { c: "#5ea0ff", t: '🎙  User: "Find me the best laptop under $1500 and order it"' },
                { c: "#f0b430", t: "→  STT: Transcribed in 320ms" },
                { c: "#f0b430", t: '→  NLU: intent=purchase_product | item=laptop | budget=$1500' },
                { c: "#7a92b8", t: "→  Memory: User prefers MacBook, fast SSD, work usage — recalled" },
                { c: "#7a92b8", t: "→  Research Agent: Scanning Amazon, B&H, Costco..." },
                { c: "#00e5c8", t: "→  Found: MacBook Air M3 — $1,299 (best match, in stock) ✓" },
                { c: "#00e5c8", t: "→  Checkout Agent: Proceeding with saved payment method..." },
                { c: "#00e5c8", t: '🔊  TTS: "Done! MacBook Air M3 ordered for $1,299. Arrives in 2 days."' },
                { c: "#3d5277", t: "⏱  Total: 1.34s · Status: SUCCESS · Confidence: 97.2%" },
              ].map((l, i) => (
                <div key={i} style={{ color: l.c, opacity: 0.92 }}>{l.t}</div>
              ))}
              <div className="flex items-center gap-2 pt-1">
                <span style={{ color: "#00e5c8" }}>$</span>
                <span className="w-2 h-[14px] inline-block animate-blink" style={{ background: "rgba(94,160,255,0.7)" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ TECH STACK ═════════════════════════════════════════ */}
      <section id="stack" className="relative z-10 py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-[10px] uppercase tracking-[0.35em] text-[#3d5277] font-bold mb-3">Built With</p>
          <h2 className="font-display font-bold text-white text-2xl mb-10">
            Enterprise-Grade <span className="text-gradient-cyan">Technology Stack</span>
          </h2>
          <div className="flex flex-wrap justify-center gap-2.5">
            {TECH.map(t => (
              <div key={t}
                className="px-4 py-2.5 rounded-xl text-[11px] font-bold uppercase tracking-widest border border-[rgba(94,160,255,0.1)] bg-[rgba(10,22,40,0.6)] text-[#7a92b8] hover:text-white hover:border-[rgba(94,160,255,0.25)] transition-all duration-200 hover:-translate-y-0.5 cursor-default">
                {t}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ CTA BANNER ═════════════════════════════════════════ */}
      <section className="relative z-10 py-28 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="relative rounded-3xl p-14 border border-[rgba(94,160,255,0.18)] overflow-hidden text-center"
            style={{
              background: "linear-gradient(135deg, rgba(5,14,36,0.95) 0%, rgba(8,20,42,0.98) 100%)",
              boxShadow: "0 0 80px rgba(94,160,255,0.12), inset 0 0 60px rgba(0,229,200,0.02)",
            }}>
            <div className="absolute inset-0" style={{
              backgroundImage: "linear-gradient(rgba(94,160,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(94,160,255,0.03) 1px, transparent 1px)",
              backgroundSize: "36px 36px"
            }} />
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[200px] pointer-events-none" style={{
              background: "radial-gradient(ellipse, rgba(94,160,255,0.1) 0%, transparent 70%)",
              filter: "blur(50px)"
            }} />
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-px" style={{ background: "linear-gradient(90deg, transparent, rgba(94,160,255,0.4), transparent)" }} />
              <div className="absolute bottom-0 left-0 right-0 h-px" style={{ background: "linear-gradient(90deg, transparent, rgba(0,229,200,0.2), transparent)" }} />
            </div>
            <div className="relative z-10">
              <span className="inline-block px-4 py-2 rounded-full border border-[rgba(94,160,255,0.2)] bg-[rgba(94,160,255,0.06)] text-[9px] uppercase tracking-[0.3em] text-cyan font-bold mb-6">
                Free to Get Started
              </span>
              <h2 className="font-display font-extrabold text-white mb-4" style={{ fontSize: "clamp(26px, 4vw, 46px)", lineHeight: 1.1 }}>
                Ready to Command
                <br /><span className="text-gradient-cyan">Your Digital World?</span>
              </h2>
              <p className="text-[#7a92b8] text-base mb-10 max-w-md mx-auto leading-relaxed">
                Create your account in under 60 seconds and start executing voice commands immediately.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/auth/sign-up"
                  className="group relative flex items-center justify-center gap-3 px-10 py-4 rounded-2xl font-display font-bold text-sm tracking-widest uppercase text-void overflow-hidden transition-all duration-300 hover:-translate-y-1"
                  style={{ background: "linear-gradient(135deg, #5ea0ff 0%, #00e5c8 100%)", boxShadow: "0 0 30px rgba(94,160,255,0.4)" }}>
                  Create Free Account
                  <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>
                <Link href="/dashboard"
                  className="flex items-center justify-center gap-3 px-10 py-4 rounded-2xl font-display font-bold text-sm tracking-widest uppercase text-white border border-[rgba(94,160,255,0.2)] hover:border-cyan/40 hover:bg-[rgba(94,160,255,0.05)] transition-all duration-300 hover:-translate-y-1">
                  View Dashboard
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ TICKER ═════════════════════════════════════════════ */}
      <div className="relative z-10 border-t border-b border-[rgba(94,160,255,0.06)] py-3.5 overflow-hidden">
        <div className="flex gap-0 animate-ticker whitespace-nowrap" style={{ width: "max-content" }}>
          {[...TECH, ...TECH, ...TECH].map((t, i) => (
            <span key={i} className="inline-flex items-center gap-4 px-6 text-[10px] uppercase tracking-[0.2em] text-[#3d5277] font-bold">
              <svg width="4" height="4" viewBox="0 0 4 4"><circle cx="2" cy="2" r="2" fill="#5ea0ff" opacity="0.4" /></svg>
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* ══ FOOTER ═════════════════════════════════════════════ */}
      <footer className="relative z-10 px-8 py-10 border-t border-[rgba(94,160,255,0.06)]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <svg width="22" height="22" viewBox="0 0 40 40" fill="none">
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" stroke="#5ea0ff" strokeWidth="1.5" fill="rgba(94,160,255,0.06)" />
            </svg>
            <span className="font-display font-bold text-sm tracking-widest">
              <span className="text-gradient-cyan">Act</span><span className="text-white">OS</span>
            </span>
            <span className="text-[10px] text-[#3d5277]">© 2026 · AI Voice OS</span>
          </div>
          <div className="flex items-center gap-8 text-[10px] text-[#3d5277] uppercase tracking-widest font-bold">
            <Link href="/auth/sign-in" className="hover:text-[#5ea0ff] transition-colors">Sign In</Link>
            <Link href="/auth/sign-up" className="hover:text-[#5ea0ff] transition-colors">Sign Up</Link>
            <Link href="/dashboard" className="hover:text-[#5ea0ff] transition-colors">Dashboard</Link>
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-status-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal" />
            </span>
            <span className="text-[10px] text-teal font-bold uppercase tracking-widest">All Systems Operational</span>
          </div>
        </div>
      </footer>
    </main>
  )
}
