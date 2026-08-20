"use client"
import { useSession, signOut as nextAuthSignOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useCallback } from "react"

export function useAuth() {
  const { data: session, status } = useSession()
  const router = useRouter()

  const signOut = useCallback(async () => {
    await nextAuthSignOut({ redirect: false })
    router.push("/auth/sign-in")
  }, [router])

  const user = session?.user
    ? {
        id:        session.user.id        || "",
        email:     session.user.email     || "",
        firstName: session.user.firstName || "",
        lastName:  session.user.lastName  || "",
        fullName:  session.user.name      || session.user.email || "",
        avatar:    session.user.image     || "",
        initials:  ((session.user.firstName?.[0] || session.user.name?.[0] || session.user.email?.[0]) ?? "A").toUpperCase(),
        apiToken:  session.user.apiToken  || "",
        provider:  session.user.provider  || "credentials",
      }
    : null

  return {
    user,
    isLoaded:    status !== "loading",
    isSignedIn:  status === "authenticated",
    signOut,
  }
}
