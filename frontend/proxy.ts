import { NextRequest, NextResponse } from "next/server"

import { SESSION_COOKIE_NAME } from "@/lib/auth/session"

const PUBLIC_PATHS = ["/", "/auth"]

function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.some((path) => {
    if (path === "/") {
      return pathname === "/"
    }

    return pathname.startsWith(path)
  })
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const hasSession = Boolean(request.cookies.get(SESSION_COOKIE_NAME)?.value)

  if (isPublicPath(pathname)) {
    if (hasSession && pathname.startsWith("/auth")) {
      return NextResponse.redirect(new URL("/", request.url))
    }

    return NextResponse.next()
  }

  if (!hasSession) {
    const signInUrl = new URL("/auth/sign-in", request.url)

    signInUrl.searchParams.set("next", pathname)

    return NextResponse.redirect(signInUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
