import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import { SESSION_COOKIE_NAME } from "@/lib/auth/session"

async function clearSessionAndRedirect() {
  (await cookies()).delete(SESSION_COOKIE_NAME)
  redirect("/auth/sign-in")
}

export async function GET() {
  return clearSessionAndRedirect()
}

export async function POST() {
  return clearSessionAndRedirect()
}
