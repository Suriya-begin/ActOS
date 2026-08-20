import { NextAuthOptions } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const authOptions: NextAuthOptions = {
  providers: [
    // ── Google OAuth ──────────────────────────────────────────
    GoogleProvider({
      clientId:     process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),

    // ── Email + Password (FastAPI backend) ────────────────────
    CredentialsProvider({
      name: "Email",
      credentials: {
        email:    { label: "Email",    type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null
        try {
          const res = await fetch(`${API}/api/auth/login`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
              email:    credentials.email,
              password: credentials.password,
            }),
          })
          if (!res.ok) return null
          const data = await res.json()
          return {
            id:         data.user.id,
            email:      data.user.email,
            name:       data.user.fullName,
            image:      null,
            firstName:  data.user.firstName,
            lastName:   data.user.lastName,
            token:      data.access_token,
          } as any
        } catch {
          return null
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user, account }) {
      // For Google sign-in, register/sign-in the user in our backend database first
      if (account?.provider === "google" && token.email) {
        try {
          const res = await fetch(`${API}/api/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: token.email,
              first_name: token.name?.split(" ")[0] || "",
              last_name: token.name?.split(" ").slice(1).join(" ") || "",
            }),
          })
          if (res.ok) {
            const data = await res.json()
            token.id        = data.user.id
            token.firstName = data.user.firstName ?? ""
            token.lastName  = data.user.lastName ?? ""
            token.apiToken  = data.access_token
            token.provider  = "google"
          }
        } catch (err) {
          console.error("Error authenticating Google user in backend:", err)
        }
      } else if (user) {
        // On initial credentials sign-in, persist extra fields into the JWT
        token.id        = user.id
        token.firstName = (user as any).firstName ?? ""
        token.lastName  = (user as any).lastName  ?? ""
        token.apiToken  = (user as any).token     ?? ""
      }
      return token
    },

    async session({ session, token }) {
      if (session.user) {
        ;(session.user as any).id        = token.id        as string
        ;(session.user as any).firstName = token.firstName as string
        ;(session.user as any).lastName  = token.lastName  as string
        ;(session.user as any).apiToken  = token.apiToken  as string
        ;(session.user as any).provider  = token.provider  as string
      }
      return session
    },
  },

  pages: {
    signIn:  "/auth/sign-in",
    signOut: "/",
    error:   "/auth/sign-in",
  },

  session: {
    strategy:   "jwt",
    maxAge:     60 * 60 * 24 * 7, // 7 days
  },

  secret: process.env.NEXTAUTH_SECRET,

  debug: process.env.NODE_ENV === "development",
}
