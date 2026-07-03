import { cn } from "@/lib/utils"
import { TYPOGRAPHY, ICON_SIZE } from "@/lib/design-tokens"
import type { LucideIcon } from "lucide-react"

interface PageHeaderProps {
  title: string
  description?: string
  icon?: LucideIcon
  iconClassName?: string
  className?: string
}

export function PageHeader({ title, description, icon: Icon, iconClassName, className }: PageHeaderProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <h1 className={cn(TYPOGRAPHY.pageTitle, "flex items-center gap-3")}>
        {Icon && <Icon className={cn(ICON_SIZE.page, "text-muted-foreground shrink-0", iconClassName)} />}
        {title}
      </h1>
      {description && <p className={TYPOGRAPHY.bodyMuted}>{description}</p>}
    </div>
  )
}
