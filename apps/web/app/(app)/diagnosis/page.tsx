import { DiagnosisForm } from "@/components/diagnosis/DiagnosisForm"
import { getTranslations } from "next-intl/server"

export default async function DiagnosisPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("diagnosis.title")}</h1>
      <p className="text-sm text-white/60">{t("diagnosis.proDescription")}</p>
      <DiagnosisForm />
    </div>
  )
}
