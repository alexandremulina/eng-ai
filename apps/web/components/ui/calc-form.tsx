"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

const inputBase =
  "w-full rounded-lg border bg-[var(--color-input-bg)] border-[var(--color-border-subtle)] text-white placeholder-[var(--color-text-hint)] focus:outline-none focus:border-[var(--color-brand)] focus-visible:ring-2 focus-visible:ring-[var(--color-brand)]/40 transition-colors aria-invalid:border-red-500/50"

export interface CalcInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  inputSize?: "sm" | "md"
}

const CalcInput = React.forwardRef<HTMLInputElement, CalcInputProps>(
  ({ className, inputSize = "md", ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        inputBase,
        inputSize === "sm" && "h-10 px-3 text-sm",
        inputSize === "md" && "h-12 px-3 text-lg",
        className
      )}
      {...props}
    />
  )
)
CalcInput.displayName = "CalcInput"

export interface CalcSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  inputSize?: "sm" | "md"
}

const CalcSelect = React.forwardRef<HTMLSelectElement, CalcSelectProps>(
  ({ className, inputSize = "md", ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        inputBase,
        inputSize === "sm" && "h-10 px-3 text-sm",
        inputSize === "md" && "h-12 px-3 text-lg",
        className
      )}
      {...props}
    />
  )
)
CalcSelect.displayName = "CalcSelect"

const CalcLabel = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn("block text-sm font-medium text-[var(--color-text-muted)]", className)}
      {...props}
    />
  )
)
CalcLabel.displayName = "CalcLabel"

const CalcHint = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-xs text-[var(--color-text-hint)]", className)} {...props} />
  )
)
CalcHint.displayName = "CalcHint"

const CalcError = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p ref={ref} className={cn("text-xs text-red-400", className)} role="alert" {...props} />
  )
)
CalcError.displayName = "CalcError"

export { CalcInput, CalcSelect, CalcLabel, CalcHint, CalcError }
