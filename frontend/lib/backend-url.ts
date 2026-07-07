export function getBackendUrl(): string {
  if (process.env.BACKEND_URL) {
    return process.env.BACKEND_URL.replace(/\/$/, "")
  }

  const host = process.env.BACKEND_HOST ?? "localhost"
  const port = process.env.BACKEND_PORT ?? "8000"

  return `http://${host}:${port}`
}

export function getPublicBackendUrl(): string {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) {
    return process.env.NEXT_PUBLIC_BACKEND_URL.replace(/\/$/, "")
  }

  return getBackendUrl()
}
