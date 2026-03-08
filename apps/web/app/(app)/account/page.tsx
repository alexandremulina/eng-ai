import { getTranslations } from "next-intl/server"
import { Check } from "lucide-react"

const PLANS = [
  {
    key: "free",
    price: "$0",
    current: true,
    highlight: false,
    features: ["50 calculations / month", "10 AI queries / month", "3 languages (PT/EN/ES)", "PWA offline mode"],
    cta: null,
  },
  {
    key: "pro",
    price: "$19/mo",
    current: false,
    highlight: true,
    features: ["Unlimited calculations", "Unlimited AI queries", "PDF upload (500 MB)", "Exportable PDF reports", "Full history"],
    cta: "/account/upgrade",
  },
  {
    key: "enterprise",
    price: "$99/mo/org",
    current: false,
    highlight: false,
    features: ["Everything in Pro", "Isolated RAG base", "SSO + multi-user", "Priority SLA"],
    cta: "mailto:contact@engbrain.io",
  },
]

export default async function AccountPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-xl font-bold text-white">{t("account.title")}</h1>

      {/* Current plan + usage */}
      <div className="rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)] p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-wide font-medium">{t("account.currentPlan")}</p>
            <p className="text-lg font-bold text-white mt-0.5">Free</p>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/60 border border-white/10">Active</span>
        </div>
        <div className="space-y-3">
          <UsageMeter label={t("account.calculations")} used={10} limit={50} />
          <UsageMeter label={t("account.aiQueries")} used={3} limit={10} />
        </div>
      </div>

      {/* Plan comparison */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-white/60">{t("account.plans")}</p>
        {PLANS.map(plan => (
          <div
            key={plan.key}
            className={[
              "rounded-lg border p-4 space-y-3",
              plan.highlight
                ? "border-blue-500/40 bg-blue-950/20"
                : "border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)]",
            ].join(" ")}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-base font-semibold text-white capitalize">{plan.key}</p>
                <p className="text-sm text-white/50">{plan.price}</p>
              </div>
              {plan.current && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400 border border-green-500/30">
                  {t("account.currentPlan")}
                </span>
              )}
              {plan.highlight && !plan.current && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 border border-blue-500/30">
                  Popular
                </span>
              )}
            </div>
            <ul className="space-y-1.5">
              {plan.features.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-white/70">
                  <Check size={14} className="text-green-400 mt-0.5 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            {plan.cta && (
              <a
                href={plan.cta}
                className="block w-full text-center rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors py-2.5 text-sm font-medium text-white"
              >
                {t("account.upgrade")}
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function UsageMeter({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = Math.min((used / limit) * 100, 100)
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-white/60">{label}</span>
        <span className="text-white/40">{used} / {limit}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
