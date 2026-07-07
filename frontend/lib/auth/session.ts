import type { ResponseCookie } from "next/dist/compiled/@edge-runtime/cookies"

export const SESSION_COOKIE_NAME = "session"

export const sessionCookieOptions: Partial<ResponseCookie> = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax",
  path: "/",
  maxAge: 60 * 60 * 24 * 7,
}
