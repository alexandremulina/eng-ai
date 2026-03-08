"use client"
import { useState } from "react"
import { GALVANIC_SERIES, checkGalvanicCompatibility, GalvanicResult } from "@/lib/galvanic"

const MATERIALS = Object.keys(GALVANIC_SERIES)

export function GalvanicForm() {
  const [mat1, setMat1] = useState("")
  const [mat2, setMat2] = useState("")
  const [result, setResult] = useState<GalvanicResult | null>(null)

  function check() {
    if (!mat1 || !mat2 || mat1 === mat2) return
    setResult(checkGalvanicCompatibility(mat1, mat2))
  }

  const riskColors = { low: "text-green-400", medium: "text-yellow-400", high: "text-red-400" }
  const riskBg = { low: "bg-green-900/30 border-green-500/30", medium: "bg-yellow-900/30 border-yellow-500/30", high: "bg-red-900/30 border-red-500/30" }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        {[
          { id: "galvanic-mat1", label: "Material 1", value: mat1, set: setMat1 },
          { id: "galvanic-mat2", label: "Material 2", value: mat2, set: setMat2 },
        ].map(({ id, label, value, set }) => (
          <div key={id} className="space-y-1">
            <label htmlFor={id} className="block text-sm font-medium text-white/80">{label}</label>
            <select
              id={id}
              value={value}
              onChange={e => { set(e.target.value); setResult(null) }}
              className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40"
            >
              <option value="">Select material...</option>
              {MATERIALS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
        ))}
        <button
          onClick={check}
          disabled={!mat1 || !mat2 || mat1 === mat2}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors"
          aria-label="Check galvanic compatibility between the two selected materials"
        >
          Check Compatibility
        </button>
      </div>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${riskBg[result.risk]}`}>
          <div className="flex items-center justify-between">
            <span className={`text-lg font-bold uppercase ${riskColors[result.risk]}`}>
              {result.risk} risk
            </span>
            <span className="text-white/60 text-sm">{result.potential_mv} mV difference</span>
          </div>
          <div className="text-sm text-white/70 space-y-1">
            <p>Anode (corrodes): <span className="text-red-400 font-medium">{result.anode}</span></p>
            <p>Cathode (protected): <span className="text-green-400 font-medium">{result.cathode}</span></p>
          </div>
          <p className="text-sm text-white/80">{result.recommendation}</p>
        </div>
      )}
    </div>
  )
}
