import { getTranslations } from "next-intl/server"
import Link from "next/link"
import { ImageIcon, Lock } from "lucide-react"

const MOCK_RESULT = [
  { label: "Root Cause", value: "Cavitation — suction pressure below vapor pressure at operating temperature" },
  { label: "Severity", value: "High — immediate action required" },
  { label: "Immediate Action", value: "Reduce flow demand or increase suction head. Check NPSH available." },
  { label: "Preventive Action", value: "Install suction strainer. Review system curve and operating point." },
]

export default async function DiagnosisPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("diagnosis.title")}</h1>

      {/* Upload area — disabled */}
      <div className="rounded-lg border-2 border-dashed border-white/20 p-8 flex flex-col items-center gap-3 cursor-not-allowed opacity-50">
        <ImageIcon size={32} className="text-white/40" />
        <p className="text-sm text-white/50 text-center">{t("diagnosis.uploadHint")}</p>
        <p className="text-xs text-white/30">{t("diagnosis.uploadFormats")}</p>
      </div>

      {/* Mock result with blur overlay */}
      <div className="relative">
        <div
          className="select-none pointer-events-none rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)] p-4 space-y-3"
          style={{ filter: "blur(3px)" }}
          aria-hidden="true"
        >
          <h3 className="text-sm font-semibold text-white">Diagnosis Result</h3>
          <div className="space-y-2">
            {MOCK_RESULT.map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-white/40 font-medium uppercase tracking-wide">{label}</p>
                <p className="text-sm text-white/80 mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Pro overlay */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center gap-4 rounded-lg bg-[var(--color-surface)]/80 backdrop-blur-sm"
          role="region"
          aria-label="Pro feature"
        >
          <Lock size={28} className="text-blue-400" />
          <div className="text-center">
            <p className="text-sm font-semibold text-white mb-1">{t("diagnosis.proTitle")}</p>
            <p className="text-xs text-white/60 max-w-xs">{t("diagnosis.proDescription")}</p>
          </div>
          <Link
            href="/account"
            className="rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors px-5 py-2.5 text-sm font-medium text-white"
          >
            {t("account.upgrade")}
          </Link>
        </div>
      </div>
    </div>
  )
}
