"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * Card for calculator sections and result blocks. Uses surface-secondary and border-subtle tokens.
 */
const CalcCard = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border p-4",
        "bg-[var(--color-surface-secondary)] border-[var(--color-border-subtle)]",
        className
      )}
      {...props}
    />
  )
)
CalcCard.displayName = "CalcCard"

export { CalcCard }
