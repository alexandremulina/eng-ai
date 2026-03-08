"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Calculator, BookOpen, Camera, User } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/calc", labelKey: "nav.calc", icon: Calculator, comingSoon: false },
  { href: "/norms", labelKey: "nav.norms", icon: BookOpen, comingSoon: true },
  { href: "/diagnosis", labelKey: "nav.diagnosis", icon: Camera, comingSoon: true },
  { href: "/account", labelKey: "nav.account", icon: User, comingSoon: true },
]

export function BottomNav() {
  const pathname = usePathname()
  const t = useTranslations()
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 pb-safe"
      style={{ backgroundColor: "var(--color-surface-secondary, #1A1D27)" }}
      aria-label="Main navigation"
    >
      <div className="flex items-center justify-around h-16">
        {NAV_ITEMS.map(({ href, labelKey, icon: Icon, comingSoon }) => {
          const isActive = pathname.startsWith(href)
          const content = (
            <>
              <Icon size={22} aria-hidden />
              <span>{t(labelKey)}</span>
              {comingSoon && (
                <span className="text-[10px] text-white/40 font-normal">{t("common.soon")}</span>
              )}
            </>
          )
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center gap-0.5 text-xs px-4 py-2 rounded-lg transition-colors",
                isActive ? "text-blue-500" : "text-white/50 hover:text-white/80"
              )}
              aria-current={isActive ? "page" : undefined}
              title={comingSoon ? t("common.comingSoon") : undefined}
            >
              {content}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
