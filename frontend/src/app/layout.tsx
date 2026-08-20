import type { Metadata } from "next"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import SessionProvider from "@/components/providers/SessionProvider"
import "./globals.css"

export const metadata: Metadata = {
  title: "ActOS — AI Voice Operating System",
  description: "The world's most advanced multilingual AI voice OS. Control any app, browser, or device through natural speech.",
  keywords: ["AI voice assistant", "multilingual AI", "voice automation", "ActOS", "AI OS"],
  openGraph: {
    title: "ActOS — AI Voice Operating System",
    description: "Speak it. It happens.",
    type: "website",
  },
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions)

  return (
    <html lang="en">
      <head>
        <link rel="preload" as="font" href="/fonts/SamsungSharpSans-Bold.otf" crossOrigin="anonymous" />
        <link rel="preload" as="font" href="/fonts/SamsungSharpSans-Medium.otf" crossOrigin="anonymous" />
        <link rel="preload" as="font" href="/fonts/SamsungSharpSans-Regular.otf" crossOrigin="anonymous" />
      </head>
      <body className="bg-void text-white antialiased">
        <SessionProvider session={session}>
          {children}
        </SessionProvider>
      </body>
    </html>
  )
}
