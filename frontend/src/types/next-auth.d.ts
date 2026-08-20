/**
 * Extend NextAuth types so TypeScript knows about our custom fields
 */
import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    user: {
      id:        string
      name?:     string | null
      email?:    string | null
      image?:    string | null
      firstName: string
      lastName:  string
      apiToken:  string
      provider:  string
    }
  }

  interface User {
    firstName?: string
    lastName?:  string
    token?:     string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id?:        string
    firstName?: string
    lastName?:  string
    apiToken?:  string
    provider?:  string
  }
}
