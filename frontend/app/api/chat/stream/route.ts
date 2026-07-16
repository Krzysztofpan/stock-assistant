import { SESSION_COOKIE_NAME } from "@/lib/auth/session"
import { getBackendUrl } from "@/lib/backend-url"
import { MAX_CHAT_MESSAGE_LENGTH } from "@/services/stockAssistantService/schemas"
import { cookies } from "next/headers"
import { NextResponse } from "next/server"

type ChatStreamRequestBody = {
  message: string
  conversation_id: string
  new_conversation?: boolean
}
const SSE_HEADERS = new Headers([
  ["content-type", "text/event-stream"],
  ["cache-control", "no-cache, no-transform"],
  ["connection", "keep-alive"],
  ["x-accel-buffering", "no"],
])

export async function POST(request: Request) {
  const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value

  if (!token) {
    return new NextResponse("Unauthorized", { status: 401 })
  }

  let body: ChatStreamRequestBody

  try {
    body = (await request.json()) as ChatStreamRequestBody
  }
  catch {
    return new NextResponse("Invalid JSON body", { status: 400 })
  }
  const message = body.message?.trim()

  if (!message || !body.conversation_id) {
    return new NextResponse("message and conversation_id are required", { status: 400 })
  }

  if (message.length > MAX_CHAT_MESSAGE_LENGTH) {
    return new NextResponse(
      `message can have at most ${MAX_CHAT_MESSAGE_LENGTH} characters`,
      { status: 400 },
    )
  }

  const backendResponse = await fetch(`${getBackendUrl()}/api/chat/stream`, {
    method: "POST",
    headers: {
      "authorization": `Bearer ${token}`,
      "accept": "text/event-stream",
      "content-type": "application/json",
    },
    body: JSON.stringify({
      message,
      conversation_id: body.conversation_id,
      new_conversation: body.new_conversation ?? false,
    }),
    cache: "no-store",
    signal: request.signal,
  })

  if (!backendResponse.ok) {
    const errorText = await backendResponse.text()

    return new NextResponse(errorText || "Upstream error", {
      status: backendResponse.status,
      headers: {
        "content-type": backendResponse.headers.get("content-type") ?? "text/plain",
      },
    })
  }
  if (!backendResponse.body) {
    return new NextResponse("SSE connection failed", { status: 502 })
  }

  return new NextResponse(backendResponse.body, {
    status: 200,
    headers: SSE_HEADERS,
  })
}
