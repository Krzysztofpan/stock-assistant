import { SESSION_COOKIE_NAME } from "@/lib/auth/session"
import { getBackendUrl } from "@/lib/backend-url"
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

export async function GET(request: Request) {
  const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value

  if (!token) {
    return new NextResponse("Unauthorized", { status: 401 })
  }

  const backendResponse = await fetch(`${getBackendUrl()}/api/conversations/events`, {
    headers: {
      authorization: `Bearer ${token}`,
      accept: "text/event-stream",
    },
    cache: "no-store",
    signal: request.signal,
  })

  if (!backendResponse.ok || !backendResponse.body) {
    return new NextResponse("SSE connection failed", {
      status: backendResponse.status || 502,
    })
  }

  return new NextResponse(backendResponse.body, {
    status: 200,
    headers: new Headers([
      ["content-type", "text/event-stream"],
      ["cache-control", "no-cache, no-transform"],
      ["connection", "keep-alive"],
    ]),
  })
}
