import { cookies } from "next/headers"
import { redirect } from "next/navigation"

import { SESSION_COOKIE_NAME } from "@/lib/auth/session"

import { getBackendUrl } from "@/lib/backend-url"

import { createStockAssistantClient } from "./create-client"
import { ApiError } from "./errors"

const BASE_URL = `${getBackendUrl()}/api`
const CLEAR_SESSION_PATH = "/api/auth/clear-session"

type BackendErrorBody = {
  message?: string
}

function redirectToSignIn(clearSession = false) {
  redirect(clearSession ? CLEAR_SESSION_PATH : "/auth/sign-in")
}

async function serverRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value

  if (!token) {
    redirectToSignIn()
  }

  const endpoint_path = `${BASE_URL}${path}`

  const response = await fetch(endpoint_path, {
    ...init,
    headers: {
      "content-type": "application/json",
      "authorization": `Bearer ${token}`,
      ...init?.headers,
    },
    cache: "no-store",
  })

  if (!response.ok) {
    let message = `API error: ${response.status}`

    try {
      const body = (await response.json()) as BackendErrorBody

      if (body.message) {
        message = body.message
      }
    }
    catch {
      // keep default message
    }

    if (response.status === 401) {
      redirectToSignIn(true)
    }

    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

export const serverApi = createStockAssistantClient(serverRequest)
