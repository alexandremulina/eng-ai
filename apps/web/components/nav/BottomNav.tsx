"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Calculator, BookOpen, Camera, User } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { href: "/calc", label: "Calc", icon: Calculator },
  { href: "/norms", label: "Norms", icon: BookOpen },
  { href: "/diagnosis", label: "Diagnosis", icon: Camera },
  { href: "/account", label: "Account", icon: User },
]

export function BottomNav() {
  const pathname = usePathname()
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 pb-safe"
         style={{ backgroundColor: "var(--color-surface-secondary, #1A1D27)" }}>
      <div className="flex items-center justify-around h-16">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-col items-center gap-1 text-xs px-4 py-2 rounded-lg transition-colors",
                isActive ? "text-blue-500" : "text-white/50 hover:text-white/80"
              )}
            >
              <Icon size={22} />
              <span>{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
