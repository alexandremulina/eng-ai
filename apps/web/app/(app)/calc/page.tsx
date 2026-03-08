import Link from "next/link"
import { getTranslations } from "next-intl/server"
import { cn } from "@/lib/utils"

const CALCULATORS = [
  { href: "/calc/parallel-pumps", key: "parallelPumps", badge: "New" },
  { href: "/calc/npsh", key: "npsh", badge: "Essential" },
  { href: "/calc/material-selection", key: "materialSelection", badge: "New" },
  { href: "/calc/galvanic", key: "galvanic", badge: "New" },
  { href: "/calc/bolt-torque", key: "boltTorque", badge: "New" },
  { href: "/calc/flanges", key: "flanges", badge: "New" },
  { href: "/calc/head-loss", key: "headLoss", badge: "Soon" },
  { href: "/calc/convert", key: "convert", badge: "Soon" },
] as const

export default async function CalcPage() {
  const t = await getTranslations("calc")
  const tCommon = await getTranslations("common")
  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold text-white mb-4">{t("title")}</h1>
      {CALCULATORS.map(c => (
        <Link
          key={c.href}
          href={c.href}
          className="block rounded-lg border border-[var(--color-border-subtle)] p-4 hover:border-blue-500/50 transition-colors bg-[var(--color-surface-secondary)]"
        >
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">{t(`${c.key}.title`)}</h2>
              <p className="text-sm text-[var(--color-text-hint)] mt-1">{t(`${c.key}.description`)}</p>
            </div>
            {c.badge && (
              <span className={cn(
                "text-xs px-2 py-0.5 rounded-full border",
                c.badge === "Essential"
                  ? "bg-blue-900/50 text-blue-400 border-blue-500/30"
                  : c.badge === "Soon"
                    ? "bg-white/5 text-white/40 border-white/10"
                    : "bg-blue-900/50 text-blue-400 border-blue-500/30"
              )}>
                {c.badge === "Essential"
                  ? tCommon("badgeEssential")
                  : c.badge === "Soon"
                    ? tCommon("soon")
                    : tCommon("badgeNew")}
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}
