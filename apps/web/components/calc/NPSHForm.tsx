"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { CalcInput, CalcSelect, CalcLabel, CalcHint, CalcError, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

interface NPSHResult {
  npsha_m: number
  npshr_m: number | null
  safety_margin_m: number | null
  cavitation_risk: boolean
  formula: string
}

interface FormState {
  p_atm: string
  p_vapor: string
  z_s_m: string
  h_loss_m: string
  fluid_density_kg_m3: string
  npshr_m: string
}

type PressureUnit = "kPa" | "bar" | "psi" | "kgf/cm2" | "MPa"

const PRESSURE_UNITS: { value: PressureUnit; label: string }[] = [
  { value: "kPa", label: "kPa" },
  { value: "bar", label: "bar" },
  { value: "psi", label: "psi" },
  { value: "kgf/cm2", label: "kgf/cm\u00B2" },
  { value: "MPa", label: "MPa" },
]

const TO_KPA: Record<PressureUnit, number> = {
  "kPa": 1,
  "bar": 100,
  "psi": 6.89476,
  "kgf/cm2": 98.0665,
  "MPa": 1000,
}

const ATM_DEFAULTS: Record<PressureUnit, string> = {
  "kPa": "101.325",
  "bar": "1.01325",
  "psi": "14.696",
  "kgf/cm2": "1.0332",
  "MPa": "0.101325",
}

const FLUID_PRESETS = [
  { value: "", label: "Custom (manual input)" },
  { value: "water", label: "Water" },
  { value: "seawater", label: "Seawater" },
  { value: "diesel", label: "Diesel" },
]

function toKpa(value: number, unit: PressureUnit): number {
  return value * TO_KPA[unit]
}

function fromKpa(value: number, unit: PressureUnit): number {
  return value / TO_KPA[unit]
}

export function NPSHForm() {
  const [loading, setLoading] = useState(false)
  const [loadingFluid, setLoadingFluid] = useState(false)
  const [result, setResult] = useState<NPSHResult | null>(null)
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({})
  const [pressureUnit, setPressureUnit] = useState<PressureUnit>("kPa")
  const [fluidPreset, setFluidPreset] = useState("")
  const [fluidTemp, setFluidTemp] = useState("20")
  const [form, setForm] = useState<FormState>({
    p_atm: "101.325",
    p_vapor: "2.338",
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

  function handleUnitChange(unit: PressureUnit) {
    // Convert current pressure values to new unit
    const oldUnit = pressureUnit
    const atmInKpa = toKpa(Number(form.p_atm) || 0, oldUnit)
    const vpInKpa = toKpa(Number(form.p_vapor) || 0, oldUnit)
    setPressureUnit(unit)
    setForm(prev => ({
      ...prev,
      p_atm: fromKpa(atmInKpa, unit).toPrecision(6),
      p_vapor: fromKpa(vpInKpa, unit).toPrecision(4),
    }))
    setResult(null)
  }

  async function loadFluidProperties(fluid: string, tempC: number) {
    if (!fluid) return
    setLoadingFluid(true)
    try {
      const data = await api.fluidProperties({ fluid, temp_c: tempC }) as {
        density_kg_m3: number
        vapor_pressure_kpa: number
      }
      const vpInUnit = fromKpa(data.vapor_pressure_kpa, pressureUnit)
      setForm(prev => ({
        ...prev,
        p_vapor: vpInUnit.toPrecision(4),
        fluid_density_kg_m3: data.density_kg_m3.toFixed(1),
      }))
    } catch {
      toast.error("Failed to load fluid properties")
    } finally {
      setLoadingFluid(false)
    }
  }

  function handleFluidPreset(fluid: string) {
    setFluidPreset(fluid)
    setResult(null)
    if (!fluid) return
    const t = Number(fluidTemp)
    if (!Number.isNaN(t)) {
      loadFluidProperties(fluid, t)
    }
  }

  function handleTempChange(temp: string) {
    setFluidTemp(temp)
    const t = Number(temp)
    if (fluidPreset && !Number.isNaN(t)) {
      loadFluidProperties(fluidPreset, t)
    }
  }

  function validate(): boolean {
    const next: Partial<Record<keyof FormState, string>> = {}
    const required: (keyof FormState)[] = ["p_atm", "p_vapor", "z_s_m", "h_loss_m", "fluid_density_kg_m3"]
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
        p_atm_kpa: toKpa(Number(form.p_atm), pressureUnit),
        p_vapor_kpa: toKpa(Number(form.p_vapor), pressureUnit),
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

  const unitLabel = PRESSURE_UNITS.find(u => u.value === pressureUnit)?.label ?? pressureUnit

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        {/* Pressure Unit Selector */}
        <div className="space-y-1">
          <CalcLabel htmlFor="pressure-unit">Pressure Unit</CalcLabel>
          <CalcSelect
            id="pressure-unit"
            value={pressureUnit}
            onChange={e => handleUnitChange(e.target.value as PressureUnit)}
          >
            {PRESSURE_UNITS.map(u => (
              <option key={u.value} value={u.value}>{u.label}</option>
            ))}
          </CalcSelect>
        </div>

        {/* Fluid Preset */}
        <div className="space-y-1">
          <CalcLabel htmlFor="fluid-preset">Fluid (optional preset)</CalcLabel>
          <div className="grid grid-cols-2 gap-2">
            <CalcSelect
              id="fluid-preset"
              value={fluidPreset}
              onChange={e => handleFluidPreset(e.target.value)}
            >
              {FLUID_PRESETS.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </CalcSelect>
            {fluidPreset && (
              <CalcInput
                id="fluid-temp"
                type="text"
                inputMode="decimal"
                placeholder="Temperature °C"
                value={fluidTemp}
                onChange={e => handleTempChange(e.target.value)}
              />
            )}
          </div>
          {loadingFluid && (
            <CalcHint>Loading fluid properties...</CalcHint>
          )}
        </div>

        {/* Atmospheric Pressure */}
        <div className="space-y-1">
          <CalcLabel htmlFor="p_atm">Atmospheric Pressure ({unitLabel})</CalcLabel>
          <CalcInput
            id="p_atm"
            type="text"
            inputMode="decimal"
            placeholder={ATM_DEFAULTS[pressureUnit]}
            value={form.p_atm}
            onChange={e => set("p_atm", e.target.value)}
            aria-invalid={errors.p_atm ? "true" : undefined}
          />
          {errors.p_atm && <CalcError id="p_atm-error">{errors.p_atm}</CalcError>}
          {!errors.p_atm && <CalcHint>Absolute pressure at fluid surface</CalcHint>}
        </div>

        {/* Vapor Pressure */}
        <div className="space-y-1">
          <CalcLabel htmlFor="p_vapor">Vapor Pressure ({unitLabel})</CalcLabel>
          <CalcInput
            id="p_vapor"
            type="text"
            inputMode="decimal"
            placeholder="2.338"
            value={form.p_vapor}
            onChange={e => set("p_vapor", e.target.value)}
            aria-invalid={errors.p_vapor ? "true" : undefined}
          />
          {errors.p_vapor && <CalcError id="p_vapor-error">{errors.p_vapor}</CalcError>}
          {!errors.p_vapor && <CalcHint>Fluid vapor pressure at operating temperature</CalcHint>}
        </div>

        {/* Suction Head */}
        <div className="space-y-1">
          <CalcLabel htmlFor="z_s_m">Suction Head (m)</CalcLabel>
          <CalcInput
            id="z_s_m"
            type="text"
            inputMode="decimal"
            placeholder="5.0"
            value={form.z_s_m}
            onChange={e => set("z_s_m", e.target.value)}
            aria-invalid={errors.z_s_m ? "true" : undefined}
          />
          {errors.z_s_m && <CalcError id="z_s_m-error">{errors.z_s_m}</CalcError>}
          {!errors.z_s_m && <CalcHint>Positive: fluid above pump, Negative: fluid below pump</CalcHint>}
        </div>

        {/* Suction Line Losses */}
        <div className="space-y-1">
          <CalcLabel htmlFor="h_loss_m">Suction Line Losses (m)</CalcLabel>
          <CalcInput
            id="h_loss_m"
            type="text"
            inputMode="decimal"
            placeholder="2.0"
            value={form.h_loss_m}
            onChange={e => set("h_loss_m", e.target.value)}
            aria-invalid={errors.h_loss_m ? "true" : undefined}
          />
          {errors.h_loss_m && <CalcError id="h_loss_m-error">{errors.h_loss_m}</CalcError>}
          {!errors.h_loss_m && <CalcHint>Total friction losses in suction piping</CalcHint>}
        </div>

        {/* Fluid Density */}
        <div className="space-y-1">
          <CalcLabel htmlFor="fluid_density_kg_m3">Fluid Density (kg/m³)</CalcLabel>
          <CalcInput
            id="fluid_density_kg_m3"
            type="text"
            inputMode="decimal"
            placeholder="998.2"
            value={form.fluid_density_kg_m3}
            onChange={e => set("fluid_density_kg_m3", e.target.value)}
            aria-invalid={errors.fluid_density_kg_m3 ? "true" : undefined}
          />
          {errors.fluid_density_kg_m3 && <CalcError id="fluid_density_kg_m3-error">{errors.fluid_density_kg_m3}</CalcError>}
          {!errors.fluid_density_kg_m3 && <CalcHint>Water at 20°C = 998.2 kg/m³</CalcHint>}
        </div>

        {/* NPSHr */}
        <div className="space-y-1">
          <CalcLabel htmlFor="npshr_m">NPSHr from pump curve (m)</CalcLabel>
          <CalcInput
            id="npshr_m"
            type="text"
            inputMode="decimal"
            placeholder="Optional"
            value={form.npshr_m}
            onChange={e => set("npshr_m", e.target.value)}
            aria-invalid={errors.npshr_m ? "true" : undefined}
          />
          {errors.npshr_m && <CalcError id="npshr_m-error">{errors.npshr_m}</CalcError>}
          {!errors.npshr_m && <CalcHint>Required NPSH from manufacturer's pump curve</CalcHint>}
        </div>

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
