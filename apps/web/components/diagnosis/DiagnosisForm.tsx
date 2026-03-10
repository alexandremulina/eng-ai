"use client"
import { useState, useRef } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
import { ImageIcon } from "lucide-react"

interface DiagnosisResult {
  root_cause: string
  severity: string
  immediate_action: string
  preventive_action: string
}

export function DiagnosisForm() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [notes, setNotes] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DiagnosisResult | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFile(f: File | undefined) {
    if (!f) return
    const allowed = ["image/jpeg", "image/png", "image/webp"]
    if (!allowed.includes(f.type)) {
      toast.error("Use JPEG, PNG, or WebP images")
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      toast.error("Image too large (max 10MB)")
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) { toast.error("Upload an image first"); return }
    setLoading(true)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append("file", file)
      if (notes.trim()) formData.append("notes", notes.trim())
      const data = await api.diagnose(formData) as DiagnosisResult
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        toast.error("Monthly diagnosis limit reached.")
      } else if (err instanceof ApiError) {
        toast.error(err.message)
      } else {
        toast.error("Diagnosis failed. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  const RESULT_FIELDS = [
    { key: "root_cause" as const, label: "Root Cause" },
    { key: "severity" as const, label: "Severity" },
    { key: "immediate_action" as const, label: "Immediate Action" },
    { key: "preventive_action" as const, label: "Preventive Action" },
  ]

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        {/* Upload area */}
        <div
          onClick={() => inputRef.current?.click()}
          className="rounded-lg border-2 border-dashed border-white/20 hover:border-blue-500/50 p-8 flex flex-col items-center gap-3 cursor-pointer transition-colors"
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={e => handleFile(e.target.files?.[0])}
          />
          {preview ? (
            <img src={preview} alt="Upload preview" className="max-h-48 rounded-lg object-contain" />
          ) : (
            <>
              <ImageIcon size={32} className="text-white/40" />
              <p className="text-sm text-white/50 text-center">Click to upload an image of the component</p>
              <p className="text-xs text-white/30">JPEG, PNG, or WebP — max 10MB</p>
            </>
          )}
        </div>

        {/* Notes */}
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Additional notes — symptoms, operating conditions, history (optional)"
          rows={2}
          className="w-full px-4 py-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm placeholder:text-white/30 focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40 resize-none"
        />

        <button
          type="submit"
          disabled={loading || !file}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
              Analyzing…
            </>
          ) : "Analyze Component"}
        </button>
      </form>

      {!result && !loading && (
        <CalcEmptyState>Upload a photo of a damaged component to get AI-powered diagnosis</CalcEmptyState>
      )}

      {result && (
        <CalcCard className="space-y-3 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <h3 className="text-base font-semibold text-white">Diagnosis Result</h3>
          <div className="space-y-3">
            {RESULT_FIELDS.map(({ key, label }) => {
              const value = result[key]
              if (!value) return null
              return (
                <div key={key}>
                  <p className="text-xs text-white/40 font-medium uppercase tracking-wide">{label}</p>
                  <p className="text-sm text-white/80 mt-0.5 leading-relaxed">{value}</p>
                </div>
              )
            })}
          </div>
        </CalcCard>
      )}
    </div>
  )
}
