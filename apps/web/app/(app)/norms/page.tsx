import { NormsForm } from "@/components/norms/NormsForm"
import { getTranslations } from "next-intl/server"

export default async function NormsPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("norms.title")}</h1>
      <p className="text-sm text-white/60">{t("norms.proDescription")}</p>
      <NormsForm />
    </div>
  )
}
