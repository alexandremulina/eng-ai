"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"
import { CalcInput, CalcSelect, CalcLabel, CalcError, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

const FLUIDS = [
  { value: "water", label: "Water" },
  { value: "seawater", label: "Seawater" },
  { value: "sulfuric_acid", label: "Sulfuric Acid (H₂SO₄)" },
  { value: "hydrochloric_acid", label: "Hydrochloric Acid (HCl)" },
  { value: "caustic_soda", label: "Caustic Soda (NaOH)" },
  { value: "diesel", label: "Diesel / Fuel Oil" },
]

const RATING_STYLE: Record<string, string> = {
  recommended: "bg-green-900/30 text-green-400 border-green-500/30",
  conditional:  "bg-yellow-900/30 text-yellow-400 border-yellow-500/30",
  incompatible: "bg-red-900/30 text-red-400 border-red-500/30",
}

interface MaterialEntry { material: string; rating: string; note: string }
interface ComponentResult { component: string; materials: MaterialEntry[] }
interface SelectionResult { fluid: string; components: ComponentResult[] }

const COMPONENT_LABELS: Record<string, string> = {
  casing: "Casing", impeller: "Impeller", wear_ring: "Wear Ring",
  shaft: "Shaft", mechanical_seal: "Mechanical Seal", o_rings: "O-Rings",
}

export function MaterialSelectionForm() {
  const { token } = useSession()
  const [fluid, setFluid] = useState("")
  const [concentration, setConcentration] = useState("100")
  const [temp, setTemp] = useState("25")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SelectionResult | null>(null)
  const [errors, setErrors] = useState<{ concentration?: string; temp?: string }>({})

  function validate(): boolean {
    const next: { concentration?: string; temp?: string } = {}
    const c = Number(concentration)
    if (Number.isNaN(c) || c < 0 || c > 100) next.concentration = "Enter 0–100"
    const t = Number(temp)
    if (Number.isNaN(t) || t < -273 || t > 500) next.temp = "Enter a valid temperature (°C)"
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token || !fluid) { toast.error("Select a fluid and log in"); return }
    if (!validate()) return
    setLoading(true)
    try {
      const data = await api.materialSelection({ fluid, concentration_pct: Number(concentration), temp_c: Number(temp) }, token) as SelectionResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Request failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-1">
          <CalcLabel htmlFor="material-fluid">Fluid</CalcLabel>
          <CalcSelect id="material-fluid" value={fluid} onChange={e => { setFluid(e.target.value); setResult(null) }}>
            <option value="">Select fluid...</option>
            {FLUIDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
          </CalcSelect>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <CalcLabel htmlFor="material-concentration">Concentration (%)</CalcLabel>
            <CalcInput
              id="material-concentration"
              type="text"
              inputMode="decimal"
              value={concentration}
              onChange={e => { setConcentration(e.target.value); setErrors(prev => ({ ...prev, concentration: undefined })) }}
              aria-invalid={errors.concentration ? "true" : undefined}
              aria-describedby={errors.concentration ? "material-concentration-error" : undefined}
            />
            {errors.concentration && <CalcError id="material-concentration-error">{errors.concentration}</CalcError>}
          </div>
          <div className="space-y-1">
            <CalcLabel htmlFor="material-temp">Temperature (°C)</CalcLabel>
            <CalcInput
              id="material-temp"
              type="text"
              inputMode="decimal"
              value={temp}
              onChange={e => { setTemp(e.target.value); setErrors(prev => ({ ...prev, temp: undefined })) }}
              aria-invalid={errors.temp ? "true" : undefined}
              aria-describedby={errors.temp ? "material-temp-error" : undefined}
            />
            {errors.temp && <CalcError id="material-temp-error">{errors.temp}</CalcError>}
          </div>
        </div>
        <button type="submit" disabled={loading || !fluid} className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2" aria-busy={loading}>
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
              Calculating…
            </>
          ) : "Select Materials"}
        </button>
      </form>

      {!result && (
        <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
      )}

      {result && (
        <div className="space-y-4 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          {result.components.map(comp => (
            <CalcCard key={comp.component} className="overflow-hidden p-0">
              <div className="p-3 border-b border-white/10">
                <h3 className="text-sm font-semibold text-white">{COMPONENT_LABELS[comp.component] ?? comp.component}</h3>
              </div>
              <div className="divide-y divide-white/5">
                {comp.materials.map(m => (
                  <div key={m.material} className="flex items-center justify-between p-3">
                    <div>
                      <p className="text-sm text-white">{m.material}</p>
                      {m.note && <p className="text-xs text-white/40 mt-0.5">{m.note}</p>}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${RATING_STYLE[m.rating] ?? ""}`}>
                      {m.rating}
                    </span>
                  </div>
                ))}
              </div>
            </CalcCard>
          ))}
        </div>
      )}
    </div>
  )
}
