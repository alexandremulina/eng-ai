import { ParallelPumpsForm } from "@/components/calc/ParallelPumpsForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Parallel Pumps — EngBrain" }

export default function ParallelPumpsPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Parallel Pump Association</h1>
      <p className="text-sm text-white/50 mb-6">Find the operating point for multiple pumps in parallel — including different pump models</p>
      <ParallelPumpsForm />
    </div>
  )
}
