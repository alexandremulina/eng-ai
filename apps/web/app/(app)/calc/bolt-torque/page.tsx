import { BoltTorqueForm } from "@/components/calc/BoltTorqueForm"
import Link from "next/link"
import { ChevronLeft } from "lucide-react"

export const metadata = { title: "Bolt Torque — EngBrain" }

export default function BoltTorquePage() {
  return (
    <div className="p-4">
      <Link href="/calc" className="flex items-center gap-1 text-sm text-white/50 hover:text-white/80 mb-4 transition-colors">
        <ChevronLeft size={16} /> Back to Calculators
      </Link>
      <h1 className="text-xl font-bold text-white mb-1">Bolt Torque Calculator</h1>
      <p className="text-sm text-white/50 mb-6">Tightening torque, preload force and proof load</p>
      <BoltTorqueForm />
    </div>
  )
}
