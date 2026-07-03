"use client"

import { memo, useMemo, type ComponentPropsWithoutRef } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import { cn } from "@/lib/utils"
import { CodeBlock, extractCodeBlock } from "@/components/chat/code-block"

interface ChatMarkdownProps {
  content: string
  className?: string
}

function MarkdownPre({ children, ...props }: ComponentPropsWithoutRef<"pre">) {
  const block = extractCodeBlock(children)
  if (block) {
    const codeElement = Array.isArray(children) ? children[0] : children
    return <CodeBlock language={block.language}>{codeElement}</CodeBlock>
  }
  return (
    <pre
      className="chat-code-pre my-3 overflow-x-auto rounded-lg border border-border bg-muted/60 p-4 text-sm scrollbar-thin"
      {...props}
    >
      {children}
    </pre>
  )
}

function MarkdownCode({ className, children, ...props }: ComponentPropsWithoutRef<"code">) {
  const isBlock = Boolean(className?.startsWith("language-"))
  if (isBlock) {
    return (
      <code className={cn("hljs", className)} {...props}>
        {children}
      </code>
    )
  }
  return (
    <code className="chat-inline-code" {...props}>
      {children}
    </code>
  )
}

function MarkdownLink({ href, children, ...props }: ComponentPropsWithoutRef<"a">) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="font-medium text-primary underline underline-offset-2 transition-opacity hover:opacity-80"
      {...props}
    >
      {children}
    </a>
  )
}

export const ChatMarkdown = memo(function ChatMarkdown({ content, className }: ChatMarkdownProps) {
  const components = useMemo(
    () => ({
      pre: MarkdownPre,
      code: MarkdownCode,
      a: MarkdownLink,
    }),
    []
  )

  return (
    <div className={cn("chat-markdown", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
})
