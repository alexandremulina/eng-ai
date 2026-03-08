"use client"
import { useState, useRef } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { useSession } from "@/lib/useSession"
import { CalcLabel, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from "recharts"

interface HQPoint { q: number; h: number }
interface PumpData { name: string; points: HQPoint[]; bep_q: string }
interface PumpResult { name: string; q: number; h: number; bep_ratio: number | null; alert: string | null }
interface ParallelResult {
  operating_point: { q_total: number; h: number }
  pumps: PumpResult[]
  combined_curve_points: HQPoint[]
  system_curve_points: HQPoint[]
  individual_curve_points: HQPoint[][]
}

const PUMP_COLORS = ["#0066FF", "#00C853", "#FF6B35", "#A855F7"]
const EMPTY_PUMP = (): PumpData => ({ name: "", points: [{ q: 0, h: 0 }, { q: 0, h: 0 }, { q: 0, h: 0 }], bep_q: "" })

export function ParallelPumpsForm() {
  const { token } = useSession()
  const [pumps, setPumps] = useState<PumpData[]>([EMPTY_PUMP()])
  const [staticHead, setStaticHead] = useState("5")
  const [resistance, setResistance] = useState("0.04")
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState<number | null>(null)
  const [result, setResult] = useState<ParallelResult | null>(null)
  const fileRefs = useRef<(HTMLInputElement | null)[]>([])

  function updatePump(i: number, field: keyof PumpData, value: string) {
    setPumps(prev => prev.map((p, idx) => idx === i ? { ...p, [field]: value } : p))
  }

  function updatePoint(pumpIdx: number, ptIdx: number, field: "q" | "h", value: string) {
    setPumps(prev => prev.map((p, i) => {
      if (i !== pumpIdx) return p
      const pts = p.points.map((pt, j) => j === ptIdx ? { ...pt, [field]: Number(value) } : pt)
      return { ...p, points: pts }
    }))
  }

  function addPoint(pumpIdx: number) {
    setPumps(prev => prev.map((p, i) => i === pumpIdx ? { ...p, points: [...p.points, { q: 0, h: 0 }] } : p))
  }

  function removePoint(pumpIdx: number, ptIdx: number) {
    setPumps(prev => prev.map((p, i) => {
      if (i !== pumpIdx || p.points.length <= 3) return p
      return { ...p, points: p.points.filter((_, j) => j !== ptIdx) }
    }))
  }

  function addPump() {
    if (pumps.length >= 4) return
    setPumps(prev => [...prev, EMPTY_PUMP()])
  }

  function removePump(i: number) {
    if (pumps.length <= 1) return
    setPumps(prev => prev.filter((_, idx) => idx !== i))
  }

  async function extractCurve(pumpIdx: number, file: File) {
    if (!token) { toast.error("Please log in"); return }
    setExtracting(pumpIdx)
    try {
      const formData = new FormData()
      formData.append("file", file)
      const data = await api.extractPumpCurve(formData, token) as { points: HQPoint[] }
      setPumps(prev => prev.map((p, i) => i === pumpIdx ? { ...p, points: data.points } : p))
      toast.success(`Extracted ${data.points.length} points from datasheet`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Extraction failed — enter points manually")
    } finally {
      setExtracting(null)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!token) { toast.error("Please log in"); return }
    setLoading(true)
    try {
      const body = {
        pumps: pumps.map(p => ({
          name: p.name || "Pump",
          points: p.points,
          bep_q: p.bep_q ? Number(p.bep_q) : null,
        })),
        system_curve: { static_head: Number(staticHead), resistance: Number(resistance) },
      }
      const data = await api.parallelPumps(body, token) as ParallelResult
      setResult(data)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Calculation failed")
    } finally {
      setLoading(false)
    }
  }

  const combinedData = result ? result.combined_curve_points.map(pt => ({ q: pt.q, h: pt.h })) : []
  const systemData = result ? result.system_curve_points.map(pt => ({ q: pt.q, h: pt.h })) : []
  const individualData = result ? result.individual_curve_points.map(curve =>
    curve.map(pt => ({ q: pt.q, h: pt.h }))
  ) : []

  const ALERT_LABEL: Record<string, string> = {
    off_curve: "Off BEP", reverse_flow: "Reverse Flow",
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-6">
        {/* Pumps */}
        {pumps.map((pump, pi) => (
          <CalcCard key={pi} className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: PUMP_COLORS[pi] }} />
                <span className="text-sm font-semibold text-white">Pump {pi + 1}</span>
              </div>
              {pumps.length > 1 && (
                <button type="button" onClick={() => removePump(pi)} className="text-xs text-red-400 hover:text-red-300 focus-visible:ring-2 focus-visible:ring-blue-500/40 rounded" aria-label={`Remove pump ${pi + 1}`}>Remove</button>
              )}
            </div>

            <input
              id={`pump-${pi}-name`}
              type="text"
              placeholder="Pump name / tag (optional)"
              value={pump.name}
              onChange={e => updatePump(pi, "name", e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40"
              aria-label={`Pump ${pi + 1} name`}
            />

            {/* Upload */}
            <div>
              <input
                type="file"
                accept="image/*,.pdf"
                ref={el => { fileRefs.current[pi] = el }}
                className="hidden"
                onChange={e => { const f = e.target.files?.[0]; if (f) extractCurve(pi, f) }}
              />
              <button
                type="button"
                onClick={() => fileRefs.current[pi]?.click()}
                disabled={extracting === pi}
                className="w-full h-10 rounded-lg border border-dashed border-white/20 text-white/50 text-sm hover:border-blue-500/50 hover:text-white/70 transition-colors disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-blue-500/40"
                aria-label={`Upload datasheet for pump ${pi + 1} to auto-fill curve`}
              >
                {extracting === pi ? "Extracting curve..." : "Upload datasheet (PDF or image) to auto-fill"}
              </button>
            </div>

            {/* H-Q table */}
            <div>
              <div className="grid grid-cols-[1fr_1fr_auto] gap-2 mb-2">
                <span className="text-xs text-white/40 text-center">Q (m³/h)</span>
                <span className="text-xs text-white/40 text-center">H (m)</span>
                <span className="w-6" />
              </div>
              {pump.points.map((pt, ptIdx) => (
                <div key={ptIdx} className="grid grid-cols-[1fr_1fr_auto] gap-2 mb-2">
                  <input
                    type="number"
                    step="any"
                    value={pt.q}
                    onChange={e => updatePoint(pi, ptIdx, "q", e.target.value)}
                    className="h-10 px-2 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40 text-center"
                    aria-label={`Pump ${pi + 1} point ${ptIdx + 1} flow Q m³/h`}
                  />
                  <input
                    type="number"
                    step="any"
                    value={pt.h}
                    onChange={e => updatePoint(pi, ptIdx, "h", e.target.value)}
                    className="h-10 px-2 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40 text-center"
                    aria-label={`Pump ${pi + 1} point ${ptIdx + 1} head H m`}
                  />
                  <button type="button" onClick={() => removePoint(pi, ptIdx)} className="w-6 h-10 text-white/30 hover:text-red-400 text-lg leading-none focus-visible:ring-2 focus-visible:ring-blue-500/40 rounded" aria-label={`Remove point ${ptIdx + 1} from pump ${pi + 1}`}>×</button>
                </div>
              ))}
              <button type="button" onClick={() => addPoint(pi)} className="text-xs text-blue-400 hover:text-blue-300 focus-visible:ring-2 focus-visible:ring-blue-500/40 rounded" aria-label={`Add H-Q point to pump ${pi + 1}`}>+ Add point</button>
            </div>

            <input
              id={`pump-${pi}-bep`}
              type="text"
              inputMode="decimal"
              placeholder="BEP flow — Best Efficiency Point Q (m³/h) — optional"
              value={pump.bep_q}
              onChange={e => updatePump(pi, "bep_q", e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40 placeholder:text-[var(--color-text-hint)]"
              aria-label={`Pump ${pi + 1} best efficiency point flow (optional)`}
            />
          </CalcCard>
        ))}

        {pumps.length < 4 && (
          <button type="button" onClick={addPump} className="w-full h-10 rounded-lg border border-dashed border-blue-500/30 text-blue-400 text-sm hover:border-blue-500/60 transition-colors focus-visible:ring-2 focus-visible:ring-blue-500/40" aria-label="Add another pump">
            + Add pump
          </button>
        )}

        {/* System curve */}
        <CalcCard className="space-y-3">
          <h3 className="text-sm font-semibold text-white">System Curve — H = H_static + R × Q²</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <CalcLabel htmlFor="parallel-static-head" className="text-xs">Static Head (m)</CalcLabel>
              <input id="parallel-static-head" type="text" inputMode="decimal" value={staticHead} onChange={e => setStaticHead(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40" aria-describedby="parallel-static-head-desc" />
              <span id="parallel-static-head-desc" className="sr-only">Static head in meters for system curve</span>
            </div>
            <div className="space-y-1">
              <CalcLabel htmlFor="parallel-resistance" className="text-xs">Resistance R</CalcLabel>
              <input id="parallel-resistance" type="text" inputMode="decimal" value={resistance} onChange={e => setResistance(e.target.value)}
                className="w-full h-10 px-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40" aria-describedby="parallel-resistance-desc" />
              <span id="parallel-resistance-desc" className="sr-only">Resistance coefficient for system curve H = H_static + R × Q²</span>
            </div>
          </div>
        </CalcCard>

        <button type="submit" disabled={loading}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors focus-visible:ring-2 focus-visible:ring-blue-500/40"
          aria-busy={loading}
        >
          {loading ? "Calculating..." : "Calculate Operating Point"}
        </button>
      </form>

      {!result && (
        <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Alert banners */}
          {result.pumps.some(p => p.alert === "reverse_flow") && (
            <div className="rounded-lg border border-red-500/50 bg-red-900/20 p-3 flex items-start gap-2">
              <span className="text-red-400 font-bold text-sm mt-0.5">⚠</span>
              <div>
                <p className="text-red-400 font-semibold text-sm">Reverse Flow Detected</p>
                <p className="text-red-300/70 text-xs mt-0.5">
                  {result.pumps.filter(p => p.alert === "reverse_flow").map(p => p.name).join(", ")} must be isolated — operating head exceeds this pump's shutoff head.
                </p>
              </div>
            </div>
          )}
          {result.pumps.some(p => p.alert === "off_curve") && (
            <div className="rounded-lg border border-yellow-500/50 bg-yellow-900/20 p-3 flex items-start gap-2">
              <span className="text-yellow-400 font-bold text-sm mt-0.5">⚠</span>
              <div>
                <p className="text-yellow-400 font-semibold text-sm">Off Best Efficiency Point</p>
                <p className="text-yellow-300/70 text-xs mt-0.5">
                  {result.pumps.filter(p => p.alert === "off_curve").map(p => p.name).join(", ")} operating outside BEP ±20%. Check for vibration, wear, or overheating.
                </p>
              </div>
            </div>
          )}
          {/* Operating point */}
          <CalcCard>
            <h3 className="text-sm font-semibold text-white mb-3">System Operating Point</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-white/40">Total Flow</p>
                <p className="text-3xl font-bold text-blue-400">{result.operating_point.q_total} <span className="text-lg font-normal text-white/50">m³/h</span></p>
              </div>
              <div>
                <p className="text-xs text-white/40">Operating Head</p>
                <p className="text-3xl font-bold text-blue-400">{result.operating_point.h} <span className="text-lg font-normal text-white/50">m</span></p>
              </div>
            </div>
          </CalcCard>

          {/* Per-pump table */}
          <CalcCard className="overflow-hidden p-0">
            <div className="p-3 border-b border-[var(--color-border-subtle)]">
              <h3 className="text-sm font-semibold text-white">Individual Pump Results</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border-subtle)]">
                  <th className="p-3 text-left text-white/40 font-medium">Pump</th>
                  <th className="p-3 text-right text-white/40 font-medium">Q (m³/h)</th>
                  <th className="p-3 text-right text-white/40 font-medium">BEP%</th>
                  <th className="p-3 text-right text-white/40 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {result.pumps.map((p, i) => (
                  <tr key={i} className="border-b border-[var(--color-border-subtle)]/50 last:border-0">
                    <td className="p-3 text-white flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PUMP_COLORS[i] }} />
                      {p.name}
                    </td>
                    <td className="p-3 text-right text-white">{p.q}</td>
                    <td className="p-3 text-right text-white/60">
                      {p.bep_ratio != null ? `${(p.bep_ratio * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="p-3 text-right">
                      {p.alert ? (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/30 text-red-400 border border-red-500/30">
                          {ALERT_LABEL[p.alert] ?? p.alert}
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400 border border-green-500/30">OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CalcCard>

          {/* Chart */}
          <CalcCard>
            <h3 className="text-sm font-semibold text-white mb-4">Performance Curves</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="q" type="number" domain={["auto", "auto"]} stroke="rgba(255,255,255,0.3)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} label={{ value: "Q (m³/h)", position: "insideBottom", offset: -2, fill: "rgba(255,255,255,0.3)", fontSize: 11 }} />
                <YAxis dataKey="h" type="number" domain={["auto", "auto"]} stroke="rgba(255,255,255,0.3)" tick={{ fill: "rgba(255,255,255,0.4)", fontSize: 11 }} label={{ value: "H (m)", angle: -90, position: "insideLeft", fill: "rgba(255,255,255,0.3)", fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1A1D27", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} labelStyle={{ color: "rgba(255,255,255,0.6)" }} itemStyle={{ color: "rgba(255,255,255,0.8)" }} formatter={(value: unknown) => [typeof value === "number" ? `${value.toFixed(1)} m` : String(value), undefined]} labelFormatter={(label: unknown) => `Q = ${Number(label).toFixed(1)} m³/h`} />
                <Legend wrapperStyle={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }} />
                {result && individualData.map((curve, i) => (
                  <Line key={result.pumps[i]?.name ?? `Pump ${i+1}`} data={curve} type="monotone" dataKey="h" name={result.pumps[i]?.name ?? `Pump ${i+1}`} stroke={PUMP_COLORS[i]} strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
                ))}
                {result && <Line data={combinedData} type="monotone" dataKey="h" name="Combined" stroke="#FFFFFF" strokeWidth={2.5} dot={false} />}
                {result && <Line data={systemData} type="monotone" dataKey="h" name="System" stroke="#FF6B35" strokeWidth={2} dot={false} />}
                {result && <ReferenceLine x={result.operating_point.q_total} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />}
                {result && <ReferenceLine y={result.operating_point.h} stroke="rgba(255,255,255,0.3)" strokeDasharray="3 3" />}
              </LineChart>
            </ResponsiveContainer>
          </CalcCard>
        </div>
      )}
    </div>
  )
}
