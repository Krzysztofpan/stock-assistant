"use client"

import type { MessageItem } from "@/services/stockAssistantService/types"
import { useEffect, useLayoutEffect, useRef, useState } from "react"

const SCROLL_EPSILON = 2
const ANCHOR_STABLE_FRAMES = 2
const SCROLL_UP_THRESHOLD = 50
const BOTTOM_SCROLL_PADDING = 128

type UseMessageListScrollOptions = {
  messages: MessageItem[]
  isFetchingNextPage: boolean
  isAiTyping?: boolean
}

function getDocumentScrollHeight() {
  return Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
}

function getMaxScrollTop() {
  return Math.max(0, getDocumentScrollHeight() - window.innerHeight)
}

function isWindowAtBottom(threshold = SCROLL_EPSILON) {
  return getMaxScrollTop() - window.scrollY <= threshold
}

function scrollToBottom(bottomEl: HTMLElement) {
  bottomEl.scrollIntoView({ block: "end", behavior: "instant" })
  window.scrollTo({ top: getMaxScrollTop() })
}

function scrollToLatestMessage(
  message: MessageItem,
  container: HTMLElement,
  bottomEl: HTMLElement,
) {
  if (message.role === "ai") {
    const messageEl = container.querySelector(`[data-message-id="${message.id}"]`)
    const availableHeight = window.innerHeight - BOTTOM_SCROLL_PADDING

    if (messageEl instanceof HTMLElement && messageEl.offsetHeight > availableHeight) {
      messageEl.scrollIntoView({ block: "start", behavior: "instant" })

      return
    }
  }

  scrollToBottom(bottomEl)
}

export function useMessageListScroll({ messages, isFetchingNextPage, isAiTyping = false }: UseMessageListScrollOptions) {
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const lastHandledMessageIdRef = useRef<number | null>(null)
  const scrollHeightBeforeFetchRef = useRef<number | null>(null)

  const [isAnchored, setIsAnchored] = useState(false)
  const [userScrolledUp, setUserScrolledUp] = useState(false)

  useEffect(() => {
    const previousScrollRestoration = history.scrollRestoration

    history.scrollRestoration = "manual"

    return () => {
      history.scrollRestoration = previousScrollRestoration
    }
  }, [])

  useEffect(() => {
    if (!isAnchored) {
      return
    }

    const onScroll = () => {
      setUserScrolledUp(!isWindowAtBottom(SCROLL_UP_THRESHOLD))
    }

    window.addEventListener("scroll", onScroll, { passive: true })

    return () => window.removeEventListener("scroll", onScroll)
  }, [isAnchored])

  useLayoutEffect(() => {
    if (messages.length === 0 || isAnchored) {
      return
    }

    const container = containerRef.current
    const bottomEl = bottomRef.current

    if (!container || !bottomEl) {
      return
    }

    let raf = 0
    let stableFrames = 0
    let cancelled = false

    const finish = () => {
      if (cancelled) {
        return
      }

      cancelled = true
      scrollToBottom(bottomEl)
      lastHandledMessageIdRef.current = messages.at(-1)?.id ?? null
      setIsAnchored(true)
    }

    const tryAnchor = () => {
      if (cancelled) {
        return
      }

      scrollToBottom(bottomEl)
      stableFrames = isWindowAtBottom() ? stableFrames + 1 : 0

      if (stableFrames >= ANCHOR_STABLE_FRAMES) {
        finish()

        return
      }

      raf = requestAnimationFrame(tryAnchor)
    }

    const onLayoutChange = () => {
      if (cancelled) {
        return
      }

      stableFrames = 0
      scrollToBottom(bottomEl)
    }

    const resizeObserver = new ResizeObserver(onLayoutChange)

    resizeObserver.observe(container)
    resizeObserver.observe(bottomEl)

    void document.fonts.ready.then(() => {
      if (!cancelled) {
        onLayoutChange()
      }
    })

    tryAnchor()

    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
      resizeObserver.disconnect()
    }
  }, [messages.length, isAnchored])

  useLayoutEffect(() => {
    if (!isAnchored || messages.length === 0) {
      return
    }

    const lastMessage = messages.at(-1)

    if (!lastMessage || lastMessage.id === lastHandledMessageIdRef.current) {
      return
    }

    const container = containerRef.current
    const bottomEl = bottomRef.current

    if (!container || !bottomEl) {
      return
    }

    lastHandledMessageIdRef.current = lastMessage.id
    scrollToLatestMessage(lastMessage, container, bottomEl)
    setUserScrolledUp(false)
  }, [messages, isAnchored])

  useLayoutEffect(() => {
    if (!isAnchored || !isAiTyping) {
      return
    }

    const bottomEl = bottomRef.current

    if (!bottomEl) {
      return
    }

    scrollToBottom(bottomEl)
    setUserScrolledUp(false)
  }, [isAiTyping, isAnchored])

  useLayoutEffect(() => {
    if (isFetchingNextPage) {
      scrollHeightBeforeFetchRef.current = getDocumentScrollHeight()

      return
    }

    const previousScrollHeight = scrollHeightBeforeFetchRef.current

    if (previousScrollHeight === null) {
      return
    }

    scrollHeightBeforeFetchRef.current = null

    const diff = getDocumentScrollHeight() - previousScrollHeight

    if (diff > 0) {
      window.scrollBy(0, diff)
    }
  }, [isFetchingNextPage, messages.length])

  return {
    containerRef,
    bottomRef,
    isAnchored,
    userScrolledUp,
  }
}
