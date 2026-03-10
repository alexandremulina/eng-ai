"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { CalcInput, CalcLabel, CalcHint, CalcError, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

interface NPSHResult {
  npsha_m: number
  npshr_m: number | null
  safety_margin_m: number | null
  cavitation_risk: boolean
  formula: string
}

interface FormState {
  p_atm_kpa: string
  p_vapor_kpa: string
  z_s_m: string
  h_loss_m: string
  fluid_density_kg_m3: string
  npshr_m: string
}

const FIELDS = [
  { key: "p_atm_kpa", label: "Atmospheric Pressure (kPa)", placeholder: "101.325", hint: "Absolute pressure at fluid surface" },
  { key: "p_vapor_kpa", label: "Vapor Pressure (kPa)", placeholder: "2.338", hint: "Fluid vapor pressure at operating temperature" },
  { key: "z_s_m", label: "Suction Head (m)", placeholder: "5.0", hint: "Positive: fluid above pump, Negative: fluid below pump" },
  { key: "h_loss_m", label: "Suction Line Losses (m)", placeholder: "2.0", hint: "Total friction losses in suction piping" },
  { key: "fluid_density_kg_m3", label: "Fluid Density (kg/m³)", placeholder: "998.2", hint: "Water at 20°C = 998.2 kg/m³" },
  { key: "npshr_m", label: "NPSHr from pump curve (m)", placeholder: "Optional", hint: "Required NPSH from manufacturer's pump curve" },
] as const

export function NPSHForm() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<NPSHResult | null>(null)
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [form, setForm] = useState<FormState>({
    p_atm_kpa: "101.325",
    p_vapor_kpa: "2.338",
    z_s_m: "5",
    h_loss_m: "2",
    fluid_density_kg_m3: "998.2",
    npshr_m: "",
  })

  function set(key: keyof FormState, value: string) {
    setForm(prev => ({ ...prev, [key]: value }))
    setErrors(prev => ({ ...prev, [key]: undefined }))
    setResult(null)
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {}
    const required: (keyof FormState)[] = ["p_atm_kpa", "p_vapor_kpa", "z_s_m", "h_loss_m", "fluid_density_kg_m3"]
    for (const key of required) {
      const v = form[key].trim()
      if (!v) { next[key] = "Required"; continue }
      const n = Number(v)
      if (Number.isNaN(n)) next[key] = "Enter a number"
    }
    if (form.npshr_m.trim()) {
      const n = Number(form.npshr_m)
      if (Number.isNaN(n)) next.npshr_m = "Enter a number or leave empty"
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    setResult(null)
    try {
      const body: Record<string, number> = {
        p_atm_kpa: Number(form.p_atm_kpa),
        p_vapor_kpa: Number(form.p_vapor_kpa),
        z_s_m: Number(form.z_s_m),
        h_loss_m: Number(form.h_loss_m),
        fluid_density_kg_m3: Number(form.fluid_density_kg_m3),
      }
      if (form.npshr_m) {
        body.npshr_m = Number(form.npshr_m)
      }
      const data = await api.npsh(body) as NPSHResult
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        toast.error("Monthly calculation limit reached. Upgrade to Pro for unlimited access.")
      } else if (err instanceof ApiError) {
        toast.error(err.message)
      } else {
        toast.error("Calculation failed. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        {FIELDS.map(({ key, label, placeholder, hint }) => (
          <div key={key} className="space-y-1">
            <CalcLabel htmlFor={key}>{label}</CalcLabel>
            <CalcInput
              id={key}
              type="text"
              inputMode="decimal"
              placeholder={placeholder}
              value={form[key]}
              onChange={e => set(key, e.target.value)}
              aria-describedby={errors[key] ? `${key}-error` : undefined}
              aria-invalid={errors[key] ? "true" : undefined}
            />
            {errors[key] && (
              <CalcError id={`${key}-error`}>{errors[key]}</CalcError>
            )}
            {!errors[key] && <CalcHint>{hint}</CalcHint>}
          </div>
        ))}
        <button
          type="submit"
          disabled={loading}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
              Calculating…
            </>
          ) : "Calculate NPSHa"}
        </button>
      </form>

      {!result && (
        <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
      )}

      {result && (
        <CalcCard className="space-y-3 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-white">NPSHa Result</h3>
            {result.cavitation_risk ? (
              <span className="px-2 py-1 rounded text-xs font-medium bg-red-900/50 text-red-400 border border-red-500/30">
                CAVITATION RISK
              </span>
            ) : (
              <span className="px-2 py-1 rounded text-xs font-medium bg-green-900/50 text-green-400 border border-green-500/30">
                Safe
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">{result.npsha_m.toFixed(2)}</span>
            <span className="text-lg text-white/60">m</span>
          </div>
          {result.safety_margin_m !== null && (
            <p className="text-sm text-white/60">
              Safety margin:{" "}
              <span className={result.safety_margin_m < 0 ? "text-red-400" : "text-green-400"}>
                {result.safety_margin_m > 0 ? "+" : ""}{result.safety_margin_m} m
              </span>
            </p>
          )}
          <details className="text-xs text-white/40 cursor-pointer">
            <summary className="hover:text-white/60 transition-colors">Show formula</summary>
            <pre className="mt-2 whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
              {result.formula}
            </pre>
          </details>
        </CalcCard>
      )}
    </div>
  )
}
