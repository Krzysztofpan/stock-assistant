"use server"

import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import {
  SESSION_COOKIE_NAME,
  sessionCookieOptions,
} from "@/lib/auth/session"

import { getBackendUrl } from "@/lib/backend-url"

import type { AuthActionState } from "./types"

type TokenResponse = {
  access_token: string
  token_type: string
}

type BackendErrorBody = {
  message?: string
}

async function readBackendError(response: Response) {
  try {
    const body = (await response.json()) as BackendErrorBody

    return body.message ?? "Something went wrong"
  }
  catch {
    return "Something went wrong"
  }
}

export async function signIn(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const email = String(formData.get("email") ?? "").trim().toLowerCase()
  const password = String(formData.get("password") ?? "")

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  const form = new URLSearchParams()

  form.set("username", email)
  form.set("password", password)

  const response = await fetch(`${getBackendUrl()}/auth/sign-in`, {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
    },
    body: form.toString(),
    cache: "no-store",
  })

  if (!response.ok) {
    return { error: await readBackendError(response) }
  }

  const data = (await response.json()) as TokenResponse;

  (await cookies()).set(SESSION_COOKIE_NAME, data.access_token, sessionCookieOptions)

  redirect("/dashboard")
}

export async function signUp(
  _prevState: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const name = String(formData.get("name") ?? "").trim()
  const email = String(formData.get("email") ?? "").trim().toLowerCase()
  const password = String(formData.get("password") ?? "")
  const passwordRepeat = String(formData.get("passwordRepeat") ?? "")

  if (!name || !email || !password || !passwordRepeat) {
    return { error: "All fields are required" }
  }

  const response = await fetch(`${getBackendUrl()}/auth/sign-up`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      name,
      email,
      password,
      password_repeat: passwordRepeat,
    }),
    cache: "no-store",
  })

  if (!response.ok) {
    return { error: await readBackendError(response) }
  }

  redirect("/auth/sign-in")
}

export async function signOut() {
  (await cookies()).delete(SESSION_COOKIE_NAME)
  redirect("/auth/sign-in")
}
