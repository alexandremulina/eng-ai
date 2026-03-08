import { getTranslations } from "next-intl/server"
import Link from "next/link"
import { Zap } from "lucide-react"

export default async function UpgradePage() {
  const t = await getTranslations()
  return (
    <div className="p-4 flex flex-col items-center justify-center min-h-[60vh] text-center gap-4">
      <Zap size={40} className="text-blue-400" />
      <div>
        <h1 className="text-xl font-bold text-white mb-2">{t("account.upgradeTitle")}</h1>
        <p className="text-sm text-white/60 max-w-xs">{t("account.upgradeDescription")}</p>
      </div>
      <Link
        href="/account"
        className="rounded-lg border border-white/20 px-5 py-2.5 text-sm font-medium text-white/80 hover:bg-white/10 transition-colors"
      >
        {t("common.back")}
      </Link>
    </div>
  )
}
