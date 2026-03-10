"use client"
import { useState } from "react"
import { toast } from "sonner"
import { api, ApiError } from "@/lib/api"
import { CalcEmptyState } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"

interface NormCitation {
  norm: string
  section: string
  text: string
}

interface NormsResult {
  answer: string
  citations: NormCitation[]
}

export function NormsForm() {
  const [question, setQuestion] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<NormsResult | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = question.trim()
    if (q.length < 5) { toast.error("Type at least 5 characters"); return }
    setLoading(true)
    setResult(null)
    try {
      const data = await api.queryNorms({ question: q, language: "en" }) as NormsResult
      setResult(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        toast.error("Monthly query limit reached.")
      } else if (err instanceof ApiError) {
        toast.error(err.message)
      } else {
        toast.error("Query failed. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-4">
        <textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder={"e.g. What are the hydrostatic test requirements per API 610?\ne.g. Compare vibration limits between API 610 and ISO 5199"}
          rows={3}
          className="w-full px-4 py-3 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white text-sm placeholder:text-white/30 focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40 resize-none"
        />
        <button
          type="submit"
          disabled={loading || question.trim().length < 5}
          className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
          aria-busy={loading}
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
              Searching…
            </>
          ) : "Ask Question"}
        </button>
      </form>

      {!result && !loading && (
        <div className="space-y-3">
          <CalcEmptyState>Ask a specific question about engineering standards</CalcEmptyState>
          <div className="grid grid-cols-1 gap-2">
            {[
              "What are the minimum flow requirements per API 610?",
              "Hydrostatic test pressure and duration per ASME B73.1?",
              "Compare allowable vibration limits: API 610 vs ISO 5199",
            ].map(q => (
              <button
                key={q}
                type="button"
                onClick={() => { setQuestion(q); setResult(null) }}
                className="text-left text-xs text-white/40 hover:text-white/70 px-3 py-2 rounded-lg border border-white/5 hover:border-white/15 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-4 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
          <CalcCard className="space-y-3">
            <h3 className="text-sm font-semibold text-white">Answer</h3>
            <p className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
          </CalcCard>

          {result.citations?.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-white/60">Citations</h3>
              {result.citations.map((c, i) => (
                <CalcCard key={i} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded-full border border-blue-500/20">{c.norm}</span>
                    <span className="text-xs text-white/40">{c.section}</span>
                  </div>
                  <p className="text-sm text-white/70 leading-relaxed">{c.text}</p>
                </CalcCard>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
