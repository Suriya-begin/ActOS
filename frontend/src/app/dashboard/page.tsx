"use client"
import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import Link from "next/link"
import { useActOSStore } from "@/store/actosStore"
import VoiceOrb from "@/components/voice/VoiceOrb"
import { useVoice } from "@/hooks/useVoice"
import { useAuth } from "@/hooks/useAuth"
import {
  Activity, Database, LayoutGrid, Cpu, CheckSquare, Shield, Settings,
  Play, Square, RefreshCw, Search, PlusCircle, AlertTriangle, Key, Sliders, Trash2, ChevronRight, Bell, LogOut,
} from "lucide-react"

// ─── Sub-Components ──────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { bg: string; text: string; dot: string; ping?: boolean }> = {
    online:  { bg: "bg-teal/10 border-teal/20", text: "text-teal", dot: "bg-teal", ping: true },
    busy:    { bg: "bg-gold/10 border-gold/20", text: "text-gold", dot: "bg-gold" },
    offline: { bg: "bg-[#1a2840] border-[rgba(94,160,255,0.08)]", text: "text-[#3d5277]", dot: "bg-[#3d5277]" },
  }
  const s = map[status] || map.offline
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-wider ${s.bg} ${s.text}`}>
      <span className="relative flex w-1.5 h-1.5">
        {s.ping && <span className={`animate-status-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${s.dot}`} />}
        <span className={`relative inline-flex rounded-full w-1.5 h-1.5 ${s.dot}`} />
      </span>
      {status}
    </span>
  )
}

function KPICard({ label, value, sub, delta, icon: Icon, color }: {
  label: string; value: string; sub: string; delta?: string; icon: any; color: string
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
      className="relative group bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 hover:border-cyan/25 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card overflow-hidden">
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"
        style={{ background: "radial-gradient(circle at 80% 20%, rgba(94,160,255,0.04), transparent 60%)" }} />
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon size={16} />
        </div>
        {delta && <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${delta.startsWith("↑") ? "bg-teal/10 text-teal" : "bg-danger/10 text-danger"}`}>{delta}</span>}
      </div>
      <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#3d5277] mb-1.5">{label}</p>
      <p className="font-display font-extrabold text-[28px] leading-none text-white mb-1">{value}</p>
      <p className="text-[11px] text-[#7a92b8]">{sub}</p>
    </motion.div>
  )
}

// ─── Main Component ──────────────────────────────────

export default function DashboardPage() {
  const [activeView, setActiveView] = useState("overview")
  const [toast, setToast] = useState<string | null>(null)
  const { agentStatus, setAgentStatus } = useActOSStore()
  const { user, signOut } = useAuth()

  const {
    status: voiceStatus,
    transcript,
    lastResponse,
    currentStep,
    detectedLanguage,
    waveformData,
    startListening,
    stopListening,
    startContinuous,
    sendTextCommand,
    isListening,
    isContinuous,
    isProcessing,
    isSpeaking,
    isConfirming,
    confirmAction,
    pendingIntent,
  } = useVoice({ userId: user?.id || "dashboard_guest" })
  const [textCommand, setTextCommand] = useState("")

  // Toggle: clicking mic always starts CONTINUOUS mode (auto-listens between commands)
  const handleRecordToggle = () => {
    if (isContinuous || isListening) {
      stopListening()
    } else {
      startContinuous()  // ← continuous mode: auto-restarts after each command
    }
  }
  const handleSendTextCommand = () => {
    if (!textCommand.trim()) return
    sendTextCommand(textCommand)
    setTextCommand("")
  }

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2800)
  }

  // Memory state
  const [memorySearch, setMemorySearch] = useState("")
  const [memories, setMemories] = useState([
    { id: "1", category: "contact", key: "Amma", value: "+91-98401-23456 (WhatsApp)" },
    { id: "2", category: "preference", key: "Music", value: "AR Rahman, Lofi, Anirudh (Spotify)" },
    { id: "3", category: "routine", key: "Morning", value: "7am: Read Tamil news, brief calendar events" },
    { id: "4", category: "contact", key: "Ravi", value: "+91-99520-65432 (WhatsApp)" },
    { id: "5", category: "preference", key: "Language", value: "Prefers responses in Tamil and Tanglish" },
  ])
  const [newMemCategory, setNewMemCategory] = useState("contact")
  const [newMemKey, setNewMemKey] = useState("")
  const [newMemValue, setNewMemValue] = useState("")

  const handleAddMemory = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMemKey || !newMemValue) return
    setMemories([{ id: Date.now().toString(), category: newMemCategory, key: newMemKey, value: newMemValue }, ...memories])
    setNewMemKey("")
    setNewMemValue("")
    showToast("Memory committed to Pinecone index.")
  }

  // Tasks state
  const [tasks, setTasks] = useState([
    { id: "tsk_1", agent: "Messaging", cmd: "Ravi ku Swiggy status message podu", status: "Completed", date: "2m ago" },
    { id: "tsk_2", agent: "Browser", cmd: "Amazon la AirPods price monitor pannu", status: "Running", date: "Just now" },
    { id: "tsk_3", agent: "Calendar", cmd: "3pm Zoom meeting set pannu", status: "Completed", date: "45m ago" },
    { id: "tsk_4", agent: "Email", cmd: "Swiggy invoice filter panni Amma ku forward pannu", status: "Pending", date: "1h ago" },
  ])
  const [taskAgent, setTaskAgent] = useState("Browser")
  const [taskCmd, setTaskCmd] = useState("")

  const handleQueueTask = (e: React.FormEvent) => {
    e.preventDefault()
    if (!taskCmd) return
    setTasks([{ id: "tsk_" + Date.now(), agent: taskAgent, cmd: taskCmd, status: "Pending", date: "Queued now" }, ...tasks])
    setTaskCmd("")
    showToast(`Task queued to ${taskAgent} Agent.`)
  }

  // Security state
  const [approvals, setApprovals] = useState([
    { id: "app_1", action: "Swiggy Payment Authorization", detail: "Authorize payment of ₹850.00 to Swiggy via UPI", source: "Messaging Agent" },
    { id: "app_2", action: "Contact Delete Request", detail: "Remove contact 'Ravi' from long-term memory store", source: "Research Agent" },
  ])

  const handleApprove = (id: string) => { setApprovals(a => a.filter(x => x.id !== id)); showToast("Action approved and executed.") }
  const handleDeny = (id: string) => { setApprovals(a => a.filter(x => x.id !== id)); showToast("Action denied and logged.") }

  // Settings state
  const [apiKey, setApiKey] = useState("sk-proj-••••••••••••••••••••")
  const [voiceId, setVoiceId] = useState("21m00Tcm4TlvDq8ikWAM")
  const [speechSpeed, setSpeechSpeed] = useState(1.0)
  const [debugMode, setDebugMode] = useState(true)
  const [ttsEnabled, setTtsEnabled] = useState(true)

  const handleSaveSettings = () => showToast("Configuration saved successfully.")

  const sidebarItems = [
    { label: "Overview",  icon: LayoutGrid,  view: "overview" },
    { label: "Agents",    icon: Cpu,         view: "agents" },
    { label: "Memory",    icon: Database,    view: "memory" },
    { label: "Tasks",     icon: CheckSquare, view: "tasks" },
    { label: "Security",  icon: Shield,      view: "security" },
    { label: "Settings",  icon: Settings,    view: "settings" },
  ]

  const agentList = [
    { key: "messaging", name: "Messaging Agent", desc: "Automates WhatsApp and Telegram via Playwright accessibility layer.", detail: "Playwright · WhatsApp" },
    { key: "browser",   name: "Browser Agent",   desc: "Headless Chromium browser control for web research, shopping, and queries.", detail: "Playwright · Chromium" },
    { key: "calendar",  name: "Calendar Agent",  desc: "Google Calendar sync, event scheduling, and smart reminders.", detail: "Google Calendar API" },
    { key: "research",  name: "Research Agent",  desc: "CrewAI multi-agent research pipelines for fact lookup and summaries.", detail: "CrewAI · LangChain" },
    { key: "email",     name: "Email Agent",     desc: "Reads, categorizes, and drafts email replies with NLU intent.", detail: "IMAP · GPT-4o" },
  ]

  return (
    <div className="min-h-screen bg-void text-white font-sans flex flex-col relative overflow-hidden">

      {/* ── BACKGROUND ── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-grid-cyan bg-grid opacity-40" />
        <div className="absolute top-0 right-1/3 w-[500px] h-[400px] blur-[120px]"
          style={{ background: "radial-gradient(circle, rgba(94,160,255,0.06) 0%, transparent 70%)" }} />
      </div>

      {/* ── TOAST ── */}
      <AnimatePresence>
        {toast && (
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className="fixed top-5 left-1/2 -translate-x-1/2 z-[100] px-5 py-3 glass border border-teal/30 rounded-xl text-sm text-teal font-bold shadow-glow-teal flex items-center gap-3">
            <svg width="14" height="14" viewBox="0 0 22 22" fill="none"><path d="M5 11l4 4 8-8" stroke="#00e5c8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            {toast}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── TOPBAR ── */}
      <header className="relative z-30 flex items-center justify-between px-6 h-[60px] border-b border-[rgba(94,160,255,0.1)] glass-heavy sticky top-0">
        <div className="flex items-center gap-5">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-all">
            <svg width="24" height="24" viewBox="0 0 40 40" fill="none">
              <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" stroke="#5ea0ff" strokeWidth="1.5" fill="rgba(94,160,255,0.06)"/>
              <polygon points="20,9 29,14 29,26 20,31 11,26 11,14" stroke="#00e5c8" strokeWidth="1" fill="rgba(0,229,200,0.04)"/>
            </svg>
            <span className="font-display font-bold text-base tracking-widest">
              <span className="text-gradient-cyan">Act</span><span className="text-white">OS</span>
            </span>
          </Link>

          {/* Tab nav */}
          <nav className="hidden md:flex items-center gap-0.5 p-1 bg-surface/40 border border-[rgba(94,160,255,0.08)] rounded-xl">
            {sidebarItems.map(item => (
              <button
                key={item.view}
                onClick={() => setActiveView(item.view)}
                className={`flex items-center gap-1.5 text-[11px] font-bold tracking-widest uppercase px-3 py-1.5 rounded-lg transition-all duration-200 ${
                  activeView === item.view
                    ? "bg-surface text-cyan border border-[rgba(94,160,255,0.15)] shadow-[0_0_12px_rgba(94,160,255,0.08)]"
                    : "text-[#3d5277] hover:text-white"
                }`}
              >
                <item.icon size={12} />
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {/* Notification bell */}
          {approvals.length > 0 && (
            <button onClick={() => setActiveView("security")}
              className="relative p-2 rounded-xl border border-danger/20 bg-danger/5 text-danger hover:bg-danger/10 transition-all">
              <Bell size={15} />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-danger rounded-full text-[9px] font-bold flex items-center justify-center text-white">
                {approvals.length}
              </span>
            </button>
          )}
          {/* User chip */}
          <div className="flex items-center gap-2.5 px-3 py-1.5 bg-surface/60 border border-[rgba(94,160,255,0.1)] rounded-xl">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan to-teal flex items-center justify-center text-[10px] font-bold text-void shrink-0 overflow-hidden">
              {user?.avatar && user.avatar.startsWith("http")
                ? <img src={user.avatar} alt="" className="w-full h-full object-cover" />
                : <span>{user?.initials || user?.firstName?.[0] || "A"}</span>
              }
            </div>
            <span className="text-xs font-medium text-[#7a92b8] max-w-[120px] truncate hidden sm:block">
              {user?.fullName || user?.email || "User"}
            </span>
          </div>

        </div>
      </header>

      {/* ── BODY ── */}
      <div className="relative z-10 flex flex-1 overflow-hidden">

        {/* ── SIDEBAR ── */}
        <aside className="w-52 border-r border-[rgba(94,160,255,0.08)] bg-[rgba(6,13,22,0.5)] p-4 flex flex-col gap-5 shrink-0 overflow-y-auto">
          {/* Nav */}
          <div>
            <p className="text-[9px] font-bold tracking-[0.25em] uppercase text-[#3d5277] mb-2.5 px-2">Navigation</p>
            <div className="flex flex-col gap-0.5">
              {sidebarItems.map(item => (
                <button
                  key={item.view}
                  onClick={() => setActiveView(item.view)}
                  className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-[12px] font-medium tracking-wide w-full text-left transition-all duration-200 relative ${
                    activeView === item.view
                      ? "bg-surface text-cyan border border-[rgba(94,160,255,0.12)]"
                      : "text-[#7a92b8] hover:bg-surface/30 hover:text-white"
                  }`}
                >
                  {activeView === item.view && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-cyan rounded-r-full" />
                  )}
                  <item.icon size={14} />
                  {item.label}
                  {item.view === "security" && approvals.length > 0 && (
                    <span className="ml-auto text-[9px] font-bold bg-danger/20 text-danger px-1.5 py-0.5 rounded-md">{approvals.length}</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Agent status panel */}
          <div>
            <p className="text-[9px] font-bold tracking-[0.25em] uppercase text-[#3d5277] mb-2.5 px-2">Agent Status</p>
            <div className="flex flex-col gap-1">
              {Object.keys(agentStatus).map(key => (
                <div key={key} className="flex items-center justify-between px-2.5 py-2 bg-surface/40 border border-[rgba(94,160,255,0.06)] rounded-xl">
                  <span className="text-[10px] text-[#7a92b8] capitalize">{key}</span>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      agentStatus[key] === "online" ? "bg-teal" : agentStatus[key] === "busy" ? "bg-gold" : "bg-[#3d5277]"
                    } ${agentStatus[key] === "online" ? "animate-pulse" : ""}`} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        {/* ── MAIN CONTENT ── */}
        <main className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">

            {/* ════ VIEW: OVERVIEW ════ */}
            {activeView === "overview" && (
              <motion.div key="overview" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-display font-bold text-xl text-white">System Overview</h2>
                    <p className="text-[11px] text-[#3d5277] mt-0.5">ActOS Neural Voice OS — Real-time dashboard</p>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-teal/10 border border-teal/20 rounded-full">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-status-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-teal" />
                    </span>
                    <span className="text-[10px] tracking-widest uppercase text-teal font-bold">Live</span>
                  </div>
                </div>

                {/* KPIs */}
                <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
                  <KPICard label="Commands Today" value="247" sub="↑ 18% vs yesterday" delta="↑ 18%" icon={Activity} color="bg-cyan/10 text-cyan" />
                  <KPICard label="NLU Accuracy" value="96.3%" sub="Rolling 7-day average" delta="↑ 2.1%" icon={Shield} color="bg-teal/10 text-teal" />
                  <KPICard label="Avg. Latency" value="1.2s" sub="STT + LLM + TTS pipeline" icon={Sliders} color="bg-gold/10 text-gold" />
                  <KPICard label="Memory Items" value={`${memories.length}`} sub="PostgreSQL + Pinecone" icon={Database} color="bg-neon/10 text-plasma" />
                </div>

                {/* Main grid */}
                <div className="grid grid-cols-1 xl:grid-cols-[1fr_300px] gap-6">
                  <div className="flex flex-col gap-5">
                    {/* Voice orb panel */}
                    <div className="relative bg-panel border border-[rgba(94,160,255,0.15)] rounded-2xl p-6 overflow-hidden flex flex-col items-center shadow-inner-cyan">
                      {/* Scanline */}
                      <div className="absolute inset-0 scanline-overlay overflow-hidden pointer-events-none rounded-2xl" />

                      {/* Top status bar */}
                      <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-10">
                        <div className="flex items-center gap-2">
                          <span className="relative flex h-2 w-2">
                            <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${
                              isContinuous ? "bg-teal animate-status-ping" : "bg-[#3d5277]"
                            }`} />
                            <span className={`relative inline-flex rounded-full h-2 w-2 ${
                              isContinuous ? "bg-teal" : "bg-[#3d5277]"
                            }`} />
                          </span>
                          <span className="text-[9px] font-bold uppercase tracking-[0.25em] text-teal">
                            {isContinuous ? "Voice Assistant Active" : "Voice Assistant Idle"}
                          </span>
                        </div>
                        {/* Language badge */}
                        {detectedLanguage && (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded-md bg-cyan/10 border border-cyan/20 text-cyan tracking-wider">
                            {detectedLanguage}
                          </span>
                        )}
                      </div>

                      <VoiceOrb status={voiceStatus} waveformData={waveformData} onRecordToggle={handleRecordToggle} />

                      {/* Live agent step indicator */}
                      <AnimatePresence>
                        {currentStep && (
                          <motion.div
                            key={currentStep}
                            initial={{ opacity: 0, y: -6 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 6 }}
                            className="w-full max-w-md mt-2 px-4 py-2 bg-cyan/5 border border-cyan/20 rounded-xl text-center"
                          >
                            <p className="text-[11px] text-cyan font-medium animate-pulse">{currentStep}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* ── CONTINUOUS MODE TOGGLE ── */}
                      <div className="w-full max-w-md mt-4 flex flex-col gap-2 z-10">
                        <button
                          id="continuous-mode-btn"
                          onClick={handleRecordToggle}
                          className={`w-full flex items-center justify-center gap-3 py-3 rounded-2xl font-display font-bold text-sm tracking-widest uppercase transition-all duration-300 hover:-translate-y-0.5 ${
                            isContinuous
                              ? "bg-gradient-to-r from-teal/20 to-cyan/20 border border-teal/40 text-teal shadow-[0_0_20px_rgba(0,229,200,0.2)]"
                              : "bg-gradient-to-r from-cyan to-teal text-void shadow-[0_0_20px_rgba(94,160,255,0.3)]"
                          }`}
                        >
                          {isContinuous ? (
                            <>
                              <span className="relative flex h-2.5 w-2.5">
                                <span className="animate-status-ping absolute inline-flex h-full w-full rounded-full bg-teal opacity-75" />
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal" />
                              </span>
                              🟢 Continuous Mode ON — Click to Stop
                            </>
                          ) : (
                            <>
                              🎙️ Start Continuous Listening
                            </>
                          )}
                        </button>
                        <p className="text-[10px] text-center text-[#3d5277]">
                          {isContinuous
                            ? "Listening continuously — speak any command, ActOS will auto-process and keep listening"
                            : "Continuous mode keeps mic open between commands — perfect for multi-step tasks"}
                        </p>
                      </div>

                      {/* Text command input bar */}
                      <div className="w-full max-w-md mt-3 flex items-center gap-2 bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 z-10">
                        <input
                          type="text"
                          id="voice-text-command"
                          placeholder="Type a command in any language..."
                          value={textCommand}
                          onChange={(e) => setTextCommand(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") handleSendTextCommand() }}
                          className="bg-transparent border-none text-[12px] text-white outline-none w-full placeholder-[#3d5277]"
                        />
                        <button
                          id="send-text-command-btn"
                          onClick={handleSendTextCommand}
                          className="px-3 py-1.5 bg-gradient-to-r from-cyan to-teal text-void rounded-lg text-[10px] font-bold uppercase tracking-wider hover:opacity-90 transition-all shrink-0"
                        >
                          Send
                        </button>
                      </div>

                      {/* Transcript + response display */}
                      <AnimatePresence>
                        {(transcript || lastResponse || voiceStatus !== "idle" || isProcessing) && (
                          <motion.div
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="w-full mt-3 p-4 bg-surface/70 border border-[rgba(94,160,255,0.1)] rounded-xl"
                          >
                            {/* Status pill */}
                            {voiceStatus !== "idle" && (
                              <div className="flex items-center justify-center gap-2 mb-2">
                                <span className={`text-[9px] uppercase tracking-widest font-bold px-2.5 py-1 rounded-full border ${
                                  voiceStatus === "listening" ? "bg-teal/10 border-teal/30 text-teal" :
                                  voiceStatus === "processing" ? "bg-cyan/10 border-cyan/30 text-cyan" :
                                  voiceStatus === "speaking" ? "bg-gold/10 border-gold/30 text-gold" :
                                  voiceStatus === "confirming" ? "bg-danger/10 border-danger/30 text-danger" :
                                  "bg-surface border-[rgba(94,160,255,0.1)] text-[#7a92b8]"
                                } animate-pulse`}>
                                  {voiceStatus === "listening" ? "🎙️ Listening" :
                                   voiceStatus === "processing" ? "⚙️ Processing" :
                                   voiceStatus === "speaking" ? "🔊 Speaking" :
                                   voiceStatus === "confirming" ? "⚠️ Confirm Required" :
                                   voiceStatus}
                                </span>
                              </div>
                            )}
                            {/* Transcript */}
                            {transcript && (
                              <p className="text-sm text-cyan italic mb-2 text-center">&quot;{transcript}&quot;</p>
                            )}
                            {/* Response */}
                            {lastResponse && (
                              <p className="text-sm text-white font-medium text-center">{lastResponse}</p>
                            )}
                            {/* Confirmation buttons */}
                            {isConfirming && pendingIntent && (
                              <div className="flex gap-2 mt-3">
                                <button
                                  onClick={() => confirmAction(true)}
                                  className="flex-1 text-[10px] uppercase font-bold tracking-widest py-2 bg-teal text-void rounded-xl hover:opacity-85 transition-all"
                                >
                                  ✅ Yes, Do It
                                </button>
                                <button
                                  onClick={() => confirmAction(false)}
                                  className="flex-1 text-[10px] uppercase font-bold tracking-widest py-2 border border-danger text-danger rounded-xl hover:bg-danger/10 transition-all"
                                >
                                  ❌ Cancel
                                </button>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* ── DEMO TASK QUICK-LAUNCH ── */}
                    <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#3d5277]">Demo Tasks — Quick Launch</h3>
                          <p className="text-[9px] text-[#3d5277] mt-0.5">Click any task to test the system end-to-end</p>
                        </div>
                        <span className="text-[9px] font-bold px-2 py-0.5 rounded-md bg-cyan/10 border border-cyan/20 text-cyan">5 Tests</span>
                      </div>
                      <div className="grid grid-cols-1 gap-2">
                        {[
                          { emoji: "🎵", label: "Play YouTube Song",    cmd: "Open YouTube and play AR Rahman Jai Ho song",                        tag: "Browser" },
                          { emoji: "🔍", label: "Google Search",         cmd: "Search Google for best laptops under 50000 rupees",                  tag: "Browser" },
                          { emoji: "💬", label: "Open WhatsApp Web",     cmd: "Open whatsapp web in the browser",                                  tag: "Browser" },
                          { emoji: "⏭️", label: "Skip YouTube Ad",        cmd: "Skip the YouTube ad",                                               tag: "Browser" },
                          { emoji: "📰", label: "Summarize BBC News",     cmd: "Summarize the page at https://www.bbc.com/news",                    tag: "Research" },
                        ].map((demo, i) => (
                          <button
                            key={i}
                            onClick={() => sendTextCommand(demo.cmd)}
                            disabled={isProcessing || isSpeaking}
                            className="group flex items-center gap-3 p-3 bg-panel/60 border border-[rgba(94,160,255,0.07)] rounded-xl hover:border-cyan/25 hover:bg-surface/60 transition-all duration-200 text-left disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            <span className="text-xl shrink-0">{demo.emoji}</span>
                            <div className="flex-1 min-w-0">
                              <p className="text-[12px] text-white font-medium">{demo.label}</p>
                              <p className="text-[10px] text-[#3d5277] truncate">{demo.cmd}</p>
                            </div>
                            <span className="text-[9px] font-bold px-2 py-0.5 rounded-md bg-surface border border-[rgba(94,160,255,0.1)] text-[#3d5277] shrink-0">
                              {demo.tag}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Recent tasks */}
                    <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#3d5277]">Recent Operations</h3>
                        <button onClick={() => setActiveView("tasks")} className="text-[10px] text-cyan flex items-center gap-1 hover:opacity-75">View all <ChevronRight size={10} /></button>
                      </div>
                      <div className="flex flex-col gap-2">
                        {tasks.slice(0, 4).map(task => (
                          <div key={task.id} className="flex items-center gap-3 p-3 bg-panel/60 border border-[rgba(94,160,255,0.05)] rounded-xl">
                            <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-surface shrink-0">
                              <CheckSquare size={13} className="text-[#3d5277]" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-[12px] text-white font-medium truncate">{task.cmd}</p>
                              <p className="text-[10px] text-[#3d5277]">{task.date} · {task.agent} Agent</p>
                            </div>
                            <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${
                              task.status === "Completed" ? "bg-teal/10 text-teal" :
                              task.status === "Running" ? "bg-gold/10 text-gold animate-pulse" : "bg-cyan/10 text-cyan"
                            }`}>{task.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right column */}
                  <div className="flex flex-col gap-5">
                    {/* Memory snapshot */}
                    <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-[10px] font-bold tracking-[0.2em] uppercase text-[#3d5277]">Memory Snapshot</h3>
                        <button onClick={() => setActiveView("memory")} className="text-[10px] text-cyan flex items-center gap-1 hover:opacity-75">Manage <ChevronRight size={10} /></button>
                      </div>
                      <div className="flex flex-col gap-2">
                        {memories.slice(0, 4).map(m => (
                          <div key={m.id} className="p-3 bg-panel/50 border border-[rgba(94,160,255,0.05)] rounded-xl">
                            <span className={`text-[9px] font-bold uppercase tracking-widest ${m.category === "contact" ? "text-teal" : m.category === "preference" ? "text-cyan" : "text-gold"}`}>
                              {m.category}
                            </span>
                            <p className="text-[12px] text-white font-medium mt-0.5">{m.key}</p>
                            <p className="text-[10px] text-[#7a92b8] truncate">{m.value}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Approvals widget */}
                    {approvals.length > 0 && (
                      <div className="bg-surface border border-danger/20 rounded-2xl p-5">
                        <div className="flex items-center gap-2 text-danger mb-4">
                          <AlertTriangle size={14} />
                          <h3 className="text-[10px] font-bold tracking-[0.2em] uppercase">Action Required</h3>
                        </div>
                        <div className="flex flex-col gap-2.5">
                          {approvals.map(app => (
                            <div key={app.id} className="p-3 bg-panel border border-[rgba(255,77,106,0.12)] rounded-xl">
                              <p className="text-[11px] font-bold text-white mb-0.5">{app.action}</p>
                              <p className="text-[10px] text-[#7a92b8] mb-2.5">{app.detail}</p>
                              <div className="flex gap-2">
                                <button onClick={() => handleApprove(app.id)} className="flex-1 text-[9px] uppercase font-bold tracking-widest py-1.5 bg-teal text-void rounded-lg hover:opacity-85 transition-all">Approve</button>
                                <button onClick={() => handleDeny(app.id)} className="flex-1 text-[9px] uppercase font-bold tracking-widest py-1.5 border border-danger text-danger rounded-lg hover:bg-danger/10 transition-all">Deny</button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* ════ VIEW: AGENTS ════ */}
            {activeView === "agents" && (
              <motion.div key="agents" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div>
                  <h2 className="font-display font-bold text-xl text-white mb-1">AI Agent Grid</h2>
                  <p className="text-[11px] text-[#3d5277]">Start, stop, and monitor specialized automation agents.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {agentList.map(a => (
                    <motion.div key={a.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
                      className="group bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 hover:border-cyan/20 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-card flex flex-col justify-between">
                      <div>
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className={`relative w-10 h-10 rounded-xl border flex items-center justify-center shrink-0 transition-all ${
                              agentStatus[a.key] === "online" ? "bg-teal/10 border-teal/30" :
                              agentStatus[a.key] === "busy" ? "bg-gold/10 border-gold/30" :
                              "bg-surface border-[rgba(94,160,255,0.1)]"
                            }`}>
                              <Cpu size={16} className={agentStatus[a.key] === "online" ? "text-teal" : agentStatus[a.key] === "busy" ? "text-gold" : "text-[#3d5277]"} />
                              {agentStatus[a.key] === "online" && (
                                <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-teal rounded-full border-2 border-surface animate-status-ping" />
                              )}
                            </div>
                            <div>
                              <h3 className="font-display font-bold text-[14px] text-white leading-tight">{a.name}</h3>
                              <span className="text-[9px] text-[#3d5277] tracking-widest uppercase">{a.detail}</span>
                            </div>
                          </div>
                          <StatusBadge status={agentStatus[a.key]} />
                        </div>
                        <p className="text-[12px] text-[#7a92b8] leading-relaxed mb-5">{a.desc}</p>
                      </div>
                      {/* Controls */}
                      <div className="flex gap-2">
                        {agentStatus[a.key] === "offline" ? (
                          <button onClick={() => { setAgentStatus(a.key, "online"); showToast(`${a.name} started.`) }}
                            className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest px-4 py-2.5 bg-gradient-to-r from-cyan to-teal text-void rounded-xl hover:opacity-90 transition-all shadow-glow-cyan">
                            <Play size={11} fill="currentColor" /> Start Agent
                          </button>
                        ) : (
                          <>
                            <button onClick={() => { setAgentStatus(a.key, "offline"); showToast(`${a.name} stopped.`) }}
                              className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest px-4 py-2.5 bg-surface text-danger border border-danger/20 rounded-xl hover:bg-danger/10 transition-all">
                              <Square size={11} fill="currentColor" /> Stop
                            </button>
                            <button onClick={() => { setAgentStatus(a.key, "busy"); showToast(`${a.name} set to busy.`) }}
                              className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest px-4 py-2.5 border border-[rgba(94,160,255,0.1)] text-[#7a92b8] hover:text-white rounded-xl hover:bg-surface/50 transition-all">
                              <RefreshCw size={11} /> Restart
                            </button>
                          </>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* ════ VIEW: MEMORY ════ */}
            {activeView === "memory" && (
              <motion.div key="memory" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div>
                  <h2 className="font-display font-bold text-xl text-white mb-1">Long-Term Memory Engine</h2>
                  <p className="text-[11px] text-[#3d5277]">Structured facts in PostgreSQL with Pinecone semantic vector search.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
                  {/* Add form */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-4 h-fit">
                    <h3 className="font-display font-bold text-[13px] flex items-center gap-2 text-cyan">
                      <PlusCircle size={15} /> Remember New Fact
                    </h3>
                    <form onSubmit={handleAddMemory} className="flex flex-col gap-3">
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">Category</label>
                        <select value={newMemCategory} onChange={e => setNewMemCategory(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 text-xs text-white focus:border-cyan/50 outline-none cursor-pointer">
                          <option value="contact">Contact Information</option>
                          <option value="preference">User Preference</option>
                          <option value="routine">Daily Routine</option>
                          <option value="habit">Habit / Context</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">Key (Alias)</label>
                        <input type="text" required placeholder="e.g. Swiggy Preferred Store"
                          value={newMemKey} onChange={e => setNewMemKey(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 text-xs text-white focus:border-cyan/50 outline-none" />
                      </div>
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">Value (Content)</label>
                        <textarea required rows={3} placeholder="e.g. McDonald's near Guindy"
                          value={newMemValue} onChange={e => setNewMemValue(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 text-xs text-white focus:border-cyan/50 outline-none resize-none" />
                      </div>
                      <button type="submit"
                        className="w-full text-[10px] uppercase font-bold tracking-widest py-2.5 bg-gradient-to-r from-cyan to-teal text-void rounded-xl hover:opacity-90 transition-all mt-1">
                        Commit to Memory
                      </button>
                    </form>
                  </div>

                  {/* Memory list */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-4">
                    <div className="flex items-center gap-3 bg-void border border-[rgba(94,160,255,0.1)] rounded-xl px-3.5 py-2.5">
                      <Search size={14} className="text-[#3d5277] shrink-0" />
                      <input type="text" placeholder="Semantic vector search across memories..."
                        value={memorySearch} onChange={e => setMemorySearch(e.target.value)}
                        className="bg-transparent border-none text-[12px] text-white outline-none w-full placeholder-[#3d5277]" />
                    </div>
                    <div className="flex flex-col gap-2 overflow-y-auto max-h-[420px]">
                      {memories
                        .filter(m => m.key.toLowerCase().includes(memorySearch.toLowerCase()) || m.value.toLowerCase().includes(memorySearch.toLowerCase()))
                        .map(m => (
                          <div key={m.id} className="flex justify-between items-center p-3.5 bg-panel border border-[rgba(94,160,255,0.05)] rounded-xl hover:border-cyan/10 transition-all">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-md ${
                                  m.category === "contact" ? "bg-teal/10 text-teal" :
                                  m.category === "preference" ? "bg-cyan/10 text-cyan" : "bg-gold/10 text-gold"
                                }`}>{m.category}</span>
                                <span className="text-[12px] font-bold text-white">{m.key}</span>
                              </div>
                              <p className="text-[11px] text-[#7a92b8] truncate">{m.value}</p>
                            </div>
                            <button onClick={() => { setMemories(memories.filter(x => x.id !== m.id)); showToast("Memory removed.") }}
                              className="ml-3 p-2 text-[#3d5277] hover:text-danger hover:bg-danger/5 rounded-lg transition-all shrink-0">
                              <Trash2 size={13} />
                            </button>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ════ VIEW: TASKS ════ */}
            {activeView === "tasks" && (
              <motion.div key="tasks" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div>
                  <h2 className="font-display font-bold text-xl text-white mb-1">Automation Task Controller</h2>
                  <p className="text-[11px] text-[#3d5277]">Queue background automation tasks and monitor real-time execution status.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
                  {/* Queue form */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-4 h-fit">
                    <h3 className="font-display font-bold text-[13px] flex items-center gap-2 text-cyan">
                      <PlusCircle size={15} /> Queue Automation Task
                    </h3>
                    <form onSubmit={handleQueueTask} className="flex flex-col gap-3">
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">Target Agent</label>
                        <select value={taskAgent} onChange={e => setTaskAgent(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 text-xs text-white focus:border-cyan/50 outline-none cursor-pointer">
                          <option value="Browser">Browser Agent (Playwright)</option>
                          <option value="Messaging">WhatsApp / Messaging</option>
                          <option value="Calendar">Calendar Sync</option>
                          <option value="Email">Email Processing</option>
                          <option value="Research">Research Pipeline</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">NLU Command / Task Description</label>
                        <textarea required rows={4} placeholder="e.g. Scrape Samsung phone prices on Flipkart and notify if below ₹25000"
                          value={taskCmd} onChange={e => setTaskCmd(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2 text-xs text-white focus:border-cyan/50 outline-none resize-none" />
                      </div>
                      <button type="submit"
                        className="w-full text-[10px] uppercase font-bold tracking-widest py-2.5 bg-gradient-to-r from-cyan to-teal text-void rounded-xl hover:opacity-90 transition-all mt-1">
                        Push to Event Queue
                      </button>
                    </form>
                  </div>

                  {/* Task monitor */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-4">
                    <h3 className="font-display font-bold text-[13px] text-white flex items-center gap-2">
                      <Activity size={14} className="text-cyan" /> Live Execution Queue
                    </h3>
                    <div className="flex flex-col gap-2">
                      {tasks.map(t => (
                        <div key={t.id} className="flex justify-between items-center p-4 bg-panel border border-[rgba(94,160,255,0.06)] rounded-xl hover:border-cyan/10 transition-all">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] text-cyan uppercase tracking-wider font-semibold">{t.agent}</span>
                              <span className="text-[9px] text-[#3d5277]">{t.id} · {t.date}</span>
                            </div>
                            <p className="text-[12px] text-white font-medium truncate">{t.cmd}</p>
                          </div>
                          <span className={`ml-3 shrink-0 text-[10px] font-bold px-3 py-1 rounded-full ${
                            t.status === "Completed" ? "bg-teal/15 text-teal" :
                            t.status === "Running" ? "bg-gold/15 text-gold animate-pulse" : "bg-cyan/15 text-cyan"
                          }`}>{t.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ════ VIEW: SECURITY ════ */}
            {activeView === "security" && (
              <motion.div key="security" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div>
                  <h2 className="font-display font-bold text-xl text-white mb-1">Zero-Trust Security Gate</h2>
                  <p className="text-[11px] text-[#3d5277]">Manage authorizations, JWT sessions, and voice biometric thresholds.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
                  {/* Approvals */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-4">
                    <h3 className="font-display font-bold text-[13px] flex items-center gap-2 text-white">
                      <Shield size={14} className="text-danger" /> Pending Authorizations
                    </h3>
                    {approvals.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-16 text-center">
                        <div className="w-14 h-14 rounded-2xl bg-teal/10 border border-teal/20 flex items-center justify-center mb-4">
                          <Shield size={24} className="text-teal" />
                        </div>
                        <p className="text-sm font-bold text-white mb-1">System Secure</p>
                        <p className="text-[11px] text-[#3d5277]">No pending security actions require authorization.</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-3">
                        {approvals.map(app => (
                          <div key={app.id} className="flex justify-between items-start p-4 bg-panel border border-[rgba(255,77,106,0.15)] rounded-2xl">
                            <div className="flex gap-3 min-w-0 flex-1">
                              <div className="w-9 h-9 rounded-xl bg-danger/10 border border-danger/20 flex items-center justify-center shrink-0">
                                <AlertTriangle size={14} className="text-danger" />
                              </div>
                              <div className="min-w-0">
                                <h4 className="text-[12px] font-bold text-white mb-0.5">{app.action}</h4>
                                <p className="text-[11px] text-[#7a92b8] mb-1.5">{app.detail}</p>
                                <span className="text-[9px] text-[#3d5277] uppercase tracking-widest">{app.source}</span>
                              </div>
                            </div>
                            <div className="flex flex-col gap-1.5 shrink-0 ml-3">
                              <button onClick={() => handleApprove(app.id)}
                                className="text-[9px] uppercase font-bold tracking-wider px-4 py-1.5 bg-teal text-void rounded-lg hover:opacity-85 transition-all">Approve</button>
                              <button onClick={() => handleDeny(app.id)}
                                className="text-[9px] uppercase font-bold tracking-wider px-4 py-1.5 border border-danger text-danger rounded-lg hover:bg-danger/10 transition-all">Deny</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Security stats */}
                  <div className="flex flex-col gap-4">
                    {/* Voice biometric bar */}
                    <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5">
                      <h3 className="font-display font-bold text-[13px] text-white mb-4">Voice Biometric Match</h3>
                      <div className="flex items-end justify-between mb-2">
                        <span className="text-[11px] text-[#7a92b8]">Speaker Verification</span>
                        <span className="font-display font-bold text-2xl text-teal">98.4%</span>
                      </div>
                      <div className="w-full bg-void rounded-full h-2 overflow-hidden">
                        <div className="bg-gradient-to-r from-teal to-cyan h-2 rounded-full" style={{ width: "98.4%", boxShadow: "0 0 8px rgba(0,229,200,0.6)" }} />
                      </div>
                      <p className="text-[10px] text-[#3d5277] mt-2">Whisper voice print match against stored biometric profile</p>
                    </div>

                    {/* Security audit table */}
                    <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5">
                      <h3 className="font-display font-bold text-[13px] text-white mb-4">Security Audit</h3>
                      <div className="flex flex-col gap-0">
                        {[
                          { label: "Zero Trust Mode", value: "Active", color: "text-teal" },
                          { label: "JWT Session", value: "Expires in 24h", color: "text-cyan" },
                          { label: "Encryption", value: "AES-GCM-256", color: "text-cyan" },
                          { label: "Auth Provider", value: "NextAuth.js", color: "text-[#7a92b8]" },
                          { label: "API TLS", value: "TLS 1.3", color: "text-cyan" },
                          { label: "Last Audit", value: "2 minutes ago", color: "text-[#7a92b8]" },
                        ].map((row, i, arr) => (
                          <div key={row.label} className={`flex justify-between items-center py-2.5 text-[11px] ${i < arr.length - 1 ? "border-b border-[rgba(94,160,255,0.05)]" : ""}`}>
                            <span className="text-[#7a92b8]">{row.label}</span>
                            <span className={`font-bold ${row.color}`}>{row.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* ════ VIEW: SETTINGS ════ */}
            {activeView === "settings" && (
              <motion.div key="settings" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-6">
                <div>
                  <h2 className="font-display font-bold text-xl text-white mb-1">System Configuration</h2>
                  <p className="text-[11px] text-[#3d5277]">Configure API credentials, voice synthesis, and developer options.</p>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* API credentials */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-5">
                    <h3 className="font-display font-bold text-[13px] flex items-center gap-2 text-cyan">
                      <Key size={14} /> API Credentials
                    </h3>
                    <div className="flex flex-col gap-4">
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">OpenAI API Key</label>
                        <input type="password" value={apiKey} onChange={e => setApiKey(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2.5 text-xs text-white focus:border-cyan/50 outline-none transition-all" />
                      </div>
                      <div>
                        <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277] block mb-1.5">ElevenLabs Voice ID</label>
                        <input type="text" value={voiceId} onChange={e => setVoiceId(e.target.value)}
                          className="w-full bg-void border border-[rgba(94,160,255,0.15)] rounded-xl px-3 py-2.5 text-xs text-white focus:border-cyan/50 outline-none transition-all" />
                      </div>
                      <button onClick={handleSaveSettings}
                        className="w-full text-[10px] uppercase font-bold tracking-widest py-2.5 bg-gradient-to-r from-cyan to-teal text-void rounded-xl hover:opacity-90 transition-all">
                        Save Configuration
                      </button>
                    </div>
                  </div>

                  {/* Voice & system settings */}
                  <div className="bg-surface border border-[rgba(94,160,255,0.1)] rounded-2xl p-5 flex flex-col gap-5">
                    <h3 className="font-display font-bold text-[13px] flex items-center gap-2 text-cyan">
                      <Sliders size={14} /> Voice &amp; System Controls
                    </h3>
                    <div className="flex flex-col gap-5">
                      {/* Speed slider */}
                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <label className="text-[9px] uppercase font-bold tracking-[0.2em] text-[#3d5277]">Speech Playback Speed</label>
                          <span className="font-display font-bold text-sm text-cyan">{speechSpeed}x</span>
                        </div>
                        <input type="range" min="0.5" max="2.0" step="0.1" value={speechSpeed} onChange={e => setSpeechSpeed(parseFloat(e.target.value))}
                          className="w-full h-1.5 bg-void rounded-lg appearance-none cursor-pointer accent-cyan" />
                        <div className="flex justify-between text-[9px] text-[#3d5277] mt-1"><span>0.5x</span><span>2.0x</span></div>
                      </div>

                      {/* TTS toggle */}
                      <div className="flex justify-between items-center py-3 border-t border-b border-[rgba(94,160,255,0.06)]">
                        <div>
                          <p className="text-xs font-bold text-white mb-0.5">ElevenLabs TTS</p>
                          <p className="text-[10px] text-[#3d5277]">Voice synthesis for ActOS responses</p>
                        </div>
                        <button onClick={() => setTtsEnabled(!ttsEnabled)}
                          className={`relative w-11 h-6 rounded-full border transition-all duration-300 ${ttsEnabled ? "bg-teal/20 border-teal/40" : "bg-surface border-[rgba(94,160,255,0.1)]"}`}>
                          <span className={`absolute top-0.5 w-5 h-5 rounded-full transition-all duration-300 ${ttsEnabled ? "left-[22px] bg-teal" : "left-0.5 bg-[#3d5277]"}`} />
                        </button>
                      </div>

                      {/* Debug toggle */}
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="text-xs font-bold text-white mb-0.5">Developer Debug Logs</p>
                          <p className="text-[10px] text-[#3d5277]">Print WebSocket events to console</p>
                        </div>
                        <button onClick={() => setDebugMode(!debugMode)}
                          className={`relative w-11 h-6 rounded-full border transition-all duration-300 ${debugMode ? "bg-cyan/20 border-cyan/40" : "bg-surface border-[rgba(94,160,255,0.1)]"}`}>
                          <span className={`absolute top-0.5 w-5 h-5 rounded-full transition-all duration-300 ${debugMode ? "left-[22px] bg-cyan" : "left-0.5 bg-[#3d5277]"}`} />
                        </button>
                      </div>

                      {/* Infrastructure status */}
                      <div className="p-3 bg-panel border border-[rgba(94,160,255,0.08)] rounded-xl">
                        <p className="text-[9px] uppercase tracking-[0.2em] font-bold text-[#3d5277] mb-2.5">Infrastructure Status</p>
                        <div className="flex flex-col gap-1.5">
                          {[
                            { name: "PostgreSQL :5432", status: "Connected" },
                            { name: "Redis :6379", status: "Connected" },
                            { name: "FastAPI :8000", status: "Running" },
                          ].map(row => (
                            <div key={row.name} className="flex justify-between items-center text-[11px]">
                              <span className="text-[#7a92b8]">{row.name}</span>
                              <span className="text-teal font-bold flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-teal inline-block animate-pulse" />{row.status}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
