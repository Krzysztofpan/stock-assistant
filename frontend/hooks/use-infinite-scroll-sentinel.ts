"use client"

import { useEffect, useRef } from "react"

type UseInfiniteScrollSentinelOptions = {
  fetchNextPage: () => Promise<unknown>
  hasNextPage: boolean | undefined
  isFetchingNextPage: boolean
  enabled?: boolean
  scrollRootSelector?: string
  rootMargin?: string
}

export function useInfiniteScrollSentinel({ fetchNextPage, hasNextPage, isFetchingNextPage, enabled = true, scrollRootSelector, rootMargin = "100px" }: UseInfiniteScrollSentinelOptions) {
  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!enabled) {
      return
    }

    const sentinel = sentinelRef.current

    if (!sentinel) {
      return
    }

    const scrollRoot = scrollRootSelector ? sentinel.closest(scrollRootSelector) : null

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]

        if (entry?.isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      {
        root: scrollRoot,
        rootMargin,
        threshold: 0,
      },
    )

    observer.observe(sentinel)

    return () => observer.disconnect()
  }, [enabled, fetchNextPage, hasNextPage, isFetchingNextPage, scrollRootSelector, rootMargin])

  return sentinelRef
}
