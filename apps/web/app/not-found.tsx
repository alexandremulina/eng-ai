import Link from "next/link"
import { getTranslations } from "next-intl/server"

export default async function NotFound() {
  const t = await getTranslations("common")
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-6 text-center" style={{ backgroundColor: "var(--color-surface, #0F1117)" }}>
      <h1 className="text-2xl font-bold text-white mb-2">{t("notFound")}</h1>
      <p className="text-white/60 mb-6">{t("notFoundDescription")}</p>
      <Link
        href="/calc"
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40"
      >
        {t("goToCalculators")}
      </Link>
    </div>
  )
}
