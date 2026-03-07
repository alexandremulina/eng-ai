import { BottomNav } from "@/components/nav/BottomNav"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-surface, #0F1117)" }}>
      <main className="pb-20">{children}</main>
      <BottomNav />
    </div>
  )
}
