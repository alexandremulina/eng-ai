"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useTranslations } from "next-intl"

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations("common")

  useEffect(() => {
    console.error("App error:", error)
  }, [error])

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center" role="alert">
      <h2 className="text-lg font-semibold text-white mb-2">{t("error")}</h2>
      <p className="text-sm text-white/60 mb-6 max-w-md">
        {error.message || t("error")}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
        >
          {t("tryAgain")}
        </button>
        <Link
          href="/calc"
          className="rounded-lg border border-white/20 px-4 py-2 text-sm font-medium text-white/80 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
        >
          {t("backToCalculators")}
        </Link>
      </div>
    </div>
  )
}
