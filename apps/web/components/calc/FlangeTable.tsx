"use client"
import { useState } from "react"
import { NPS_OPTIONS, CLASS_OPTIONS, getFlangeDimensions, FlangeDimensions } from "@/lib/flanges"
import { CalcSelect, CalcLabel, CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

export function FlangeTable() {
  const [nps, setNps] = useState("")
  const [cls, setCls] = useState<number | "">("")
  const dims: FlangeDimensions | null = nps && cls ? getFlangeDimensions(nps, Number(cls)) : null

  const rows: [string, string][] = dims ? [
    ["Flange OD", `${dims.od_mm} mm`],
    ["Bolt Circle Diameter", `${dims.bolt_circle_mm} mm`],
    ["Number of Bolts", `${dims.num_bolts}`],
    ["Bolt Hole Diameter", `${dims.bolt_hole_mm} mm`],
    ["Flange Thickness (min)", `${dims.thickness_mm} mm`],
    ["Raised Face OD", `${dims.rf_od_mm} mm`],
    ["Raised Face Height", `${dims.rf_height_mm} mm`],
  ] : []

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <CalcLabel htmlFor="flange-nps">NPS</CalcLabel>
          <CalcSelect
            id="flange-nps"
            value={nps}
            onChange={e => setNps(e.target.value)}
          >
            <option value="">Select NPS</option>
            {NPS_OPTIONS.map(n => <option key={n} value={n}>{n}"</option>)}
          </CalcSelect>
        </div>
        <div className="space-y-1">
          <CalcLabel htmlFor="flange-class">Pressure Class</CalcLabel>
          <CalcSelect
            id="flange-class"
            value={cls}
            onChange={e => setCls(Number(e.target.value))}
          >
            <option value="">Select class</option>
            {CLASS_OPTIONS.map(c => <option key={c} value={c}>{c}#</option>)}
          </CalcSelect>
        </div>
      </div>

      {dims && (
        <CalcCard className="overflow-hidden p-0 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <div className="p-3 border-b border-white/10">
            <h3 className="text-sm font-semibold text-white">NPS {dims.nps}" — Class {dims.class}# (ASME B16.5)</h3>
          </div>
          <table className="w-full text-sm">
            <tbody>
              {rows.map(([label, value]) => (
                <tr key={label} className="border-b border-white/5 last:border-0">
                  <td className="p-3 text-white/50">{label}</td>
                  <td className="p-3 text-white font-medium text-right">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CalcCard>
      )}

      {(!nps || !cls) && (
        <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
      )}

      {nps && cls && !dims && (
        <p className="text-sm text-yellow-400">No data available for NPS {nps}" Class {cls}#.</p>
      )}
    </div>
  )
}
