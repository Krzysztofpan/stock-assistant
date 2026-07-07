import type { ReactNode } from "react"

export default function MainLayout({ children }: { children: ReactNode }) {
  return <main className="mx-auto flex w-full max-w-3xl flex-1 p-6">{children}</main>
}
