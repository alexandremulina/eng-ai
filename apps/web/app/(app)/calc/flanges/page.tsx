import { FlangeTable } from "@/components/calc/FlangeTable"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "ASME B16.5 Flanges — EngBrain" }

export default function FlangesPage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">ASME B16.5 Flanges</h1>
      <p className="text-sm text-white/50 mb-6">Flange dimensions by NPS and pressure class</p>
      <FlangeTable />
    </div>
  )
}
