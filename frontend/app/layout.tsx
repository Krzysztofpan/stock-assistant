import { QueryProvider } from "@/providers/query-provider"

import "./globals.css"
import { Figtree } from "next/font/google"
import { cn } from "@/lib/utils"
import { Metadata } from "next"

const figtree = Figtree({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: {
    default: "Stock Assistant",
    template: "%s | Stock Assistant",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={cn("font-sans", figtree.variable)}>
      <body className="min-h-full flex flex-col">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  )
}
