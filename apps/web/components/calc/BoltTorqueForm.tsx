"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"

const GRADES = ["ASTM A193 B7", "ASTM A193 B8", "ISO 8.8", "ISO 10.9", "ISO 12.9", "SAE Grade 5", "SAE Grade 8", "A2-70", "A4-80"]
const DIAMETERS = [6, 8, 10, 12, 14, 16, 20, 24, 27, 30, 36, 42, 48]
const CONDITIONS = [{ value: "dry", label: "Dry" }, { value: "lubricated", label: "Lubricated (oil/grease)" }, { value: "cadmium", label: "Cadmium-plated" }]

interface BoltResult {
  grade: string
  diameter_mm: number
  condition: string
  diameter_used_mm: number
  proof_load_mpa: number
  shear_strength_mpa: number
  preload_kn: number
  torque_nm: number
  torque_ftlb: number
}

export function BoltTorqueForm() {
  const { token } = useSession()
  const [grade, setGrade] = useState(GRADES[0])
  const [diameter, setDiameter] = useState(20)
  const [condition, setCondition] = useState("dry")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BoltResult | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) { toast.error("Please log in"); return }
    setLoading(true)
    try {
      const data = await api.boltTorque({ grade, diameter_mm: diameter, condition }, token) as BoltResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Calculation failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="bolt-grade" className="block text-sm font-medium text-white/80">Bolt Grade</label>
          <select id="bolt-grade" value={grade} onChange={e => setGrade(e.target.value)} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40">
            {GRADES.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <div className="space-y-1">
          <label htmlFor="bolt-diameter" className="block text-sm font-medium text-white/80">Nominal Diameter (mm)</label>
          <select id="bolt-diameter" value={diameter} onChange={e => setDiameter(Number(e.target.value))} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40">
            {DIAMETERS.map(d => <option key={d} value={d}>M{d}</option>)}
          </select>
        </div>
        <fieldset className="space-y-2">
          <legend className="block text-sm font-medium text-white/80">Condition</legend>
          <div className="space-y-2">
            {CONDITIONS.map(c => (
              <label key={c.value} className="flex items-center gap-3 p-3 rounded-lg border border-white/10 cursor-pointer hover:border-blue-500/50 transition-colors focus-within:ring-2 focus-within:ring-blue-500/40">
                <input type="radio" name="condition" value={c.value} checked={condition === c.value} onChange={() => setCondition(c.value)} className="accent-blue-500" aria-describedby={`condition-${c.value}`} />
                <span id={`condition-${c.value}`} className="text-white/80 text-sm">{c.label}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <button type="submit" disabled={loading} className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors" aria-busy={loading}>
          {loading ? "Calculating..." : "Calculate Torque"}
        </button>
      </form>

      {result && (
        <div className="rounded-lg border border-white/10 p-4 space-y-3" style={{ backgroundColor: "#1A1D27" }}>
          <h3 className="text-base font-semibold text-white">Result — {result.grade} M{result.diameter_mm} ({result.condition})</h3>
          <div className="text-4xl font-bold text-blue-400">{result.torque_nm} N·m</div>
          <p className="text-sm text-white/50">{result.torque_ftlb} ft·lb</p>
          {result.diameter_used_mm !== result.diameter_mm && (
            <p className="text-xs text-yellow-400/70">
              Note: snapped to nearest standard size M{result.diameter_used_mm}
            </p>
          )}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-sm">
            <div>
              <p className="text-white/40">Preload Force</p>
              <p className="text-white font-medium">{result.preload_kn} kN</p>
            </div>
            <div>
              <p className="text-white/40">Proof Load</p>
              <p className="text-white font-medium">{result.proof_load_mpa} MPa</p>
            </div>
            <div>
              <p className="text-white/40">Shear Strength</p>
              <p className="text-white font-medium">{result.shear_strength_mpa} MPa</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
