import { forwardRef } from "react"
import { cn } from "@/lib/utils"
import { SURFACE } from "@/lib/design-tokens"

interface SurfaceCardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean
  padding?: "none" | "sm" | "md" | "lg"
}

const paddingClasses = {
  none: "",
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
}

const SurfaceCard = forwardRef<HTMLDivElement, SurfaceCardProps>(
  ({ className, interactive = false, padding = "md", children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        interactive ? SURFACE.cardInteractive : SURFACE.card,
        paddingClasses[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
SurfaceCard.displayName = "SurfaceCard"

export { SurfaceCard }
