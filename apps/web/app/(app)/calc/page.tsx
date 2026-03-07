import Link from "next/link"

const CALCULATORS = [
  {
    href: "/calc/parallel-pumps",
    title: "Parallel Pump Association",
    description: "Operating point for multiple pumps in parallel — including different models",
    badge: "New",
  },
  {
    href: "/calc/npsh",
    title: "NPSH Calculator",
    description: "Net Positive Suction Head — prevent cavitation",
    badge: "Essential",
  },
  {
    href: "/calc/material-selection",
    title: "Material Selection",
    description: "Compatible materials by fluid, concentration and temperature",
    badge: "New",
  },
  {
    href: "/calc/galvanic",
    title: "Galvanic Corrosion Check",
    description: "Assess compatibility between two materials in contact",
    badge: "New",
  },
  {
    href: "/calc/bolt-torque",
    title: "Bolt Torque Calculator",
    description: "Tightening torque and preload by grade, diameter and condition",
    badge: "New",
  },
  {
    href: "/calc/flanges",
    title: "ASME B16.5 Flanges",
    description: "Flange dimensions by NPS and pressure class",
    badge: "New",
  },
  {
    href: "/calc/head-loss",
    title: "Head Loss",
    description: "Darcy-Weisbach friction losses in piping",
    badge: null,
  },
  {
    href: "/calc/convert",
    title: "Unit Converter",
    description: "GPM, bar, kPa, m³/h and more",
    badge: null,
  },
]

export default function CalcPage() {
  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold text-white mb-4">Calculators</h1>
      {CALCULATORS.map(c => (
        <Link
          key={c.href}
          href={c.href}
          className="block rounded-lg border border-white/10 p-4 hover:border-blue-500/50 transition-colors"
          style={{ backgroundColor: "#1A1D27" }}
        >
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">{c.title}</h2>
              <p className="text-sm text-white/50 mt-1">{c.description}</p>
            </div>
            {c.badge && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 border border-blue-500/30">
                {c.badge}
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}
