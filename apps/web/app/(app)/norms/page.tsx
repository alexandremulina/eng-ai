import { getTranslations } from "next-intl/server"
import Link from "next/link"
import { Lock } from "lucide-react"

const MOCK_RESULTS = [
  { norm: "API 610", section: "Section 6.1.3", excerpt: "Minimum continuous stable flow shall be defined by the pump manufacturer based on acceptable vibration levels, temperature rise, and internal recirculation..." },
  { norm: "ASME B73.1", section: "Section 4.2", excerpt: "Pump casings shall be hydrostatically tested at 1.5 times the maximum allowable working pressure. Test duration shall not be less than 30 minutes..." },
  { norm: "ISO 5199", section: "Clause 5.3", excerpt: "The NPSH available (NPSHa) shall exceed the NPSH required (NPSHr) by a margin of at least 0.5 m under all specified operating conditions..." },
]

export default async function NormsPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("norms.title")}</h1>

      {/* Search field — disabled */}
      <div className="relative">
        <input
          type="text"
          disabled
          placeholder={t("norms.placeholder")}
          className="w-full h-12 px-4 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white/40 placeholder:text-white/30 cursor-not-allowed"
        />
      </div>

      {/* Mock results with blur overlay */}
      <div className="relative">
        <div className="space-y-3 select-none pointer-events-none" style={{ filter: "blur(3px)" }} aria-hidden="true">
          {MOCK_RESULTS.map(r => (
            <div
              key={r.norm}
              className="rounded-lg border border-[var(--color-border-subtle)] p-4 bg-[var(--color-surface-secondary)] space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded-full border border-blue-500/20">{r.norm}</span>
                <span className="text-xs text-white/40">{r.section}</span>
              </div>
              <p className="text-sm text-white/70 leading-relaxed">{r.excerpt}</p>
            </div>
          ))}
        </div>

        {/* Pro overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 rounded-lg bg-[var(--color-surface)]/80 backdrop-blur-sm" role="region" aria-label="Pro feature">
          <Lock size={28} className="text-blue-400" />
          <div className="text-center">
            <p className="text-sm font-semibold text-white mb-1">{t("norms.proTitle")}</p>
            <p className="text-xs text-white/60 max-w-xs">{t("norms.proDescription")}</p>
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
