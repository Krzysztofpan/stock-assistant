"use client"

import { useLayoutEffect, useState, type RefObject } from "react"

export function useIsTruncated<T extends HTMLElement>(
  ref: RefObject<T | null>,
  watch?: unknown,
) {
  const [isTruncated, setIsTruncated] = useState(false)

  useLayoutEffect(() => {
    const el = ref.current

    if (!el) return

    const check = () => {
      setIsTruncated(el.scrollWidth > el.clientWidth)
    }

    check()

    const observer = new ResizeObserver(check)

    observer.observe(el)

    if (el.parentElement) observer.observe(el.parentElement)

    return () => observer.disconnect()
  }, [ref, watch])

  return isTruncated
}
