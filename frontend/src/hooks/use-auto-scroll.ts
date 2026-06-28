"use client"

import { useCallback, useEffect, useRef, useState } from "react"

const SCROLL_THRESHOLD = 100

export function useAutoScroll(deps: any[] = []) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [showJumpButton, setShowJumpButton] = useState(false)
  const userScrolledRef = useRef(false)

  const checkIfAtBottom = useCallback(() => {
    const el = containerRef.current
    if (!el) return true
    const diff = el.scrollHeight - el.scrollTop - el.clientHeight
    return diff < SCROLL_THRESHOLD
  }, [])

  const scrollToBottom = useCallback((smooth = true) => {
    const el = containerRef.current
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? "smooth" : "instant" })
    setIsAtBottom(true)
    setShowJumpButton(false)
    userScrolledRef.current = false
  }, [])

  const handleScroll = useCallback(() => {
    const atBottom = checkIfAtBottom()
    setIsAtBottom(atBottom)
    setShowJumpButton(!atBottom)
    if (!atBottom) {
      userScrolledRef.current = true
    } else {
      userScrolledRef.current = false
    }
  }, [checkIfAtBottom])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    el.addEventListener("scroll", handleScroll, { passive: true })
    return () => el.removeEventListener("scroll", handleScroll)
  }, [handleScroll])

  useEffect(() => {
    if (!userScrolledRef.current) {
      scrollToBottom(false)
    }
  }, deps)

  return { containerRef, isAtBottom, showJumpButton, scrollToBottom }
}
