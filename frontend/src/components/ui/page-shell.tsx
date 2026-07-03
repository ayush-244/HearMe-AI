import { cn } from "@/lib/utils"

type MaxWidth = "narrow" | "default" | "wide" | "full"

const maxWidthClasses: Record<MaxWidth, string> = {
  narrow: "max-w-3xl mx-auto",
  default: "max-w-5xl mx-auto",
  wide: "max-w-6xl mx-auto",
  full: "",
}

interface PageShellProps {
  children: React.ReactNode
  className?: string
  maxWidth?: MaxWidth
}

export function PageShell({ children, className, maxWidth = "default" }: PageShellProps) {
  return (
    <div className={cn("p-6 lg:p-8 space-y-6", maxWidthClasses[maxWidth], className)}>
      {children}
    </div>
  )
}
