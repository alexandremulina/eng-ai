import Link from "next/link"
import { getTranslations } from "next-intl/server"

export default async function NormsPage() {
  const t = await getTranslations()
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold text-white">{t("norms.title")}</h1>
      <p className="text-[var(--color-text-hint)] mt-2">{t("common.comingSoon")}</p>
    </div>
  )
}
