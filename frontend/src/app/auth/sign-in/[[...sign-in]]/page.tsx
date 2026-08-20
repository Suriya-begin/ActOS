"use client"
import { useState, useEffect } from "react"
import { signIn } from "next-auth/react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"

export default function SignInPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard"

  const [email,        setEmail]        = useState("")
  const [password,     setPassword]     = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error,        setError]        = useState("")
  const [loading,      setLoading]      = useState(false)
  const [googleLoading,setGoogleLoading]= useState(false)
  const [focusedInput, setFocusedInput] = useState<string | null>(null)

  useEffect(() => {
    const errParam = searchParams.get("error")
    if (errParam) {
      if (errParam === "OAuthSignin" || errParam === "OAuthCallback" || errParam === "OAuthCreateAccountOrLink" || errParam === "OAuthAccountNotLinked") {
        setError("Google OAuth configuration is missing or invalid.")
      } else {
        setError("Authentication error: " + errParam)
      }
    }
  }, [searchParams])

  const handleGoogle = async () => {
    setGoogleLoading(true)
    setError("")
    await signIn("google", { callbackUrl })
    setGoogleLoading(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    const result = await signIn("credentials", {
      email,
      password,
      redirect: false,
    })
    setLoading(false)
    if (result?.error) {
      setError("Incorrect email or password. Please try again.")
    } else if (result?.ok) {
      router.push(callbackUrl)
      router.refresh()
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.2 } }
  }
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 15 } }
  }

  return (
    <div className="min-h-screen bg-[#020408] flex overflow-hidden font-sans text-white relative selection:bg-cyan-500/30">
      
      {/* Dynamic Background Effects */}
      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[10%] right-[-10%] w-[50vw] h-[50vw] rounded-full mix-blend-screen filter blur-[120px] opacity-30 animate-blob" 
             style={{ background: "radial-gradient(circle, rgba(94,160,255,0.8) 0%, transparent 70%)", animation: "drift 25s infinite alternate ease-in-out" }} />
        <div className="absolute bottom-[-10%] left-[-10%] w-[45vw] h-[45vw] rounded-full mix-blend-screen filter blur-[120px] opacity-20 animate-blob" 
             style={{ background: "radial-gradient(circle, rgba(0,229,200,0.8) 0%, transparent 70%)", animation: "drift 30s infinite alternate-reverse ease-in-out" }} />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-20 mix-blend-overlay" />
      </div>

      <div className="w-full flex flex-col lg:flex-row relative z-10 container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl">
        
        {/* LEFT PANEL - Branding */}
        <motion.div 
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, ease: "easeOut" }}
          className="hidden lg:flex flex-1 flex-col justify-center pr-12 lg:pr-24 py-12"
        >
          <div className="mb-12">
            <Link href="/" className="inline-flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 p-[1px] shadow-[0_0_30px_rgba(56,189,248,0.3)] group-hover:shadow-[0_0_40px_rgba(56,189,248,0.5)] transition-all duration-500">
                <div className="w-full h-full bg-[#020408] rounded-[11px] flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="url(#paint0_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="url(#paint1_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="url(#paint2_linear)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <defs>
                      <linearGradient id="paint0_linear" x1="2" y1="7" x2="22" y2="7" gradientUnits="userSpaceOnUse"><stop stopColor="#38bdf8"/><stop offset="1" stopColor="#818cf8"/></linearGradient>
                      <linearGradient id="paint1_linear" x1="2" y1="19.5" x2="22" y2="19.5" gradientUnits="userSpaceOnUse"><stop stopColor="#38bdf8"/><stop offset="1" stopColor="#818cf8"/></linearGradient>
                      <linearGradient id="paint2_linear" x1="2" y1="14.5" x2="22" y2="14.5" gradientUnits="userSpaceOnUse"><stop stopColor="#38bdf8"/><stop offset="1" stopColor="#818cf8"/></linearGradient>
                    </defs>
                  </svg>
                </div>
              </div>
              <span className="text-2xl font-bold tracking-tight text-white">Act<span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">OS</span></span>
            </Link>
          </div>
          
          <h1 className="text-5xl lg:text-6xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            Welcome <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500">Back.</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-md leading-relaxed mb-12 font-light">
            Re-enter the command center. Your personalized AI agents and voice-automated workflows are waiting for your instruction.
          </p>

          <div className="space-y-6">
            {[
              { title: "Multimodal AI Reasoning", desc: "GPT-4o powered intent engine seamlessly integrated." },
              { title: "Sub-second Execution", desc: "Average 1.2s pipeline latency across all nodes." },
            ].map((feature, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + (i * 0.2) }}
                className="flex items-start gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] backdrop-blur-sm"
              >
                <div className="mt-1 w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]" />
                <div>
                  <h3 className="text-sm font-semibold text-white mb-1">{feature.title}</h3>
                  <p className="text-xs text-slate-400">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* RIGHT PANEL - Form */}
        <div className="flex-1 flex items-center justify-center py-12 lg:py-0 w-full">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.6, type: "spring", bounce: 0.4 }}
            className="w-full max-w-[440px] relative"
          >
            {/* Glow behind form */}
            <div className="absolute inset-0 bg-gradient-to-tl from-blue-500/20 to-cyan-500/20 blur-3xl rounded-[40px] -z-10" />
            
            <div className="bg-[#0a0e17]/80 backdrop-blur-2xl border border-white/[0.08] rounded-[32px] p-8 sm:p-10 shadow-2xl overflow-hidden relative">
              {/* Top accent line */}
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-blue-500 to-transparent opacity-50" />
              
              <div className="mb-8">
                <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Sign in</h2>
                <p className="text-sm text-slate-400 font-medium">Access your AI command center.</p>
              </div>

              <motion.button
                onClick={handleGoogle}
                disabled={googleLoading}
                whileHover={{ scale: 1.01, backgroundColor: "rgba(255,255,255,0.06)" }}
                whileTap={{ scale: 0.98 }}
                className="w-full flex items-center justify-center gap-3 py-3.5 rounded-2xl font-semibold text-sm border border-white/10 bg-white/[0.03] text-white transition-all duration-200 mb-6 disabled:opacity-50 relative group overflow-hidden"
              >
                <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                {googleLoading ? (
                  <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                )}
                Continue with Google
              </motion.button>

              <div className="flex items-center gap-4 mb-6">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent to-white/10" />
                <span className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">or</span>
                <div className="flex-1 h-px bg-gradient-to-l from-transparent to-white/10" />
              </div>

              <motion.form 
                variants={containerVariants} 
                initial="hidden" 
                animate="show" 
                onSubmit={handleSubmit} 
                className="flex flex-col gap-5" 
                noValidate
              >
                <motion.div variants={itemVariants} className="relative group">
                  <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 mb-2 pl-1 transition-colors group-focus-within:text-blue-400">Email Address</label>
                  <div className="relative">
                    <svg className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${focusedInput === 'email' ? 'text-blue-400' : 'text-slate-500'}`} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                    <input 
                      type="email" required autoComplete="email" placeholder="hello@example.com" 
                      value={email} onChange={e => { setEmail(e.target.value); setError("") }}
                      onFocus={() => setFocusedInput('email')} onBlur={() => setFocusedInput(null)}
                      className="w-full bg-white/[0.02] border border-white/[0.05] text-white text-sm pl-12 pr-4 py-3.5 rounded-xl outline-none focus:bg-white/[0.04] focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all placeholder-slate-600 font-medium" 
                    />
                  </div>
                </motion.div>

                <motion.div variants={itemVariants} className="relative group">
                  <div className="flex justify-between items-center mb-2 pl-1 pr-1">
                    <label className="block text-[11px] uppercase tracking-wider font-semibold text-slate-400 transition-colors group-focus-within:text-blue-400">Password</label>
                  </div>
                  <div className="relative">
                    <svg className={`absolute left-4 top-1/2 -translate-y-1/2 transition-colors duration-300 ${focusedInput === 'password' ? 'text-blue-400' : 'text-slate-500'}`} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    <input 
                      type={showPassword ? "text" : "password"} required autoComplete="current-password" placeholder="••••••••" 
                      value={password} onChange={e => { setPassword(e.target.value); setError("") }}
                      onFocus={() => setFocusedInput('password')} onBlur={() => setFocusedInput(null)}
                      className="w-full bg-white/[0.02] border border-white/[0.05] text-white text-sm pl-12 pr-12 py-3.5 rounded-xl outline-none focus:bg-white/[0.04] focus:border-blue-500/50 focus:ring-4 focus:ring-blue-500/10 transition-all placeholder-slate-600 font-medium tracking-[0.2em]" 
                    />
                    <button type="button" onClick={() => setShowPassword(s => !s)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors">
                      {showPassword
                        ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                        : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      }
                    </button>
                  </div>
                </motion.div>

                <AnimatePresence>
                  {error && (
                    <motion.div 
                      initial={{ opacity: 0, y: -10, scale: 0.95 }} 
                      animate={{ opacity: 1, y: 0, scale: 1 }} 
                      exit={{ opacity: 0, scale: 0.95 }}
                      className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl"
                    >
                      <svg className="shrink-0 text-red-400 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                      <span className="text-red-400 text-xs font-medium leading-relaxed">{error}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.button 
                  variants={itemVariants}
                  type="submit" disabled={loading}
                  whileHover={loading ? {} : { scale: 1.02 }}
                  whileTap={loading ? {} : { scale: 0.98 }}
                  className="w-full relative group mt-2"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur-lg opacity-40 group-hover:opacity-70 transition-opacity duration-300" />
                  <div className="relative flex items-center justify-center gap-2 py-4 rounded-2xl font-bold text-sm text-white transition-all duration-300 bg-gradient-to-r from-blue-600 to-cyan-500 shadow-[inset_0_1px_rgba(255,255,255,0.2)] disabled:opacity-70 disabled:cursor-not-allowed">
                    {loading
                      ? <><svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Authenticating...</>
                      : <>Sign In <svg className="ml-1 group-hover:translate-x-1 transition-transform" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></>
                    }
                  </div>
                </motion.button>
              </motion.form>

              <div className="mt-8 text-center">
                <p className="text-xs text-slate-400">
                  New to ActOS?{" "}
                  <Link href="/auth/sign-up" className="text-white font-semibold hover:text-blue-400 transition-colors relative after:absolute after:bottom-0 after:left-0 after:right-0 after:h-px after:bg-blue-400 after:origin-right after:scale-x-0 hover:after:scale-x-100 hover:after:origin-left after:transition-transform after:duration-300 pb-1">
                    Create an account
                  </Link>
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
