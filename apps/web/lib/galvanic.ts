// Galvanic potential in mV vs SCE (approximate, passive range midpoint)
// Source: NACE / MIL-STD-889C
export const GALVANIC_SERIES: Record<string, number> = {
  "Zinc":                  -1000,
  "Aluminum 1100":          -750,
  "Aluminum 6061":          -730,
  "Carbon Steel":           -620,
  "Cast Iron":              -610,
  "SS 304 (active)":        -530,
  "SS 316 (active)":        -500,
  "Lead-Tin Solder":        -480,
  "Lead":                   -460,
  "Tin":                    -440,
  "Muntz Metal":            -380,
  "Yellow Brass":           -360,
  "Admiralty Brass":        -330,
  "Aluminum Bronze":        -320,
  "Red Brass":              -310,
  "Bronze (92Cu-8Sn)":      -300,
  "Copper":                 -280,
  "Nickel Silver":          -270,
  "Cupronickel (70-30)":    -200,
  "Monel 400":              -150,
  "SS 316 (passive)":        -50,
  "SS 304 (passive)":        -80,
  "Titanium Grade 2":        -50,
  "Hastelloy C":             -30,
  "Platinum":                  0,
  "Graphite":                 50,
}

export type GalvanicRisk = "low" | "medium" | "high"

export interface GalvanicResult {
  anode: string
  cathode: string
  potential_mv: number
  risk: GalvanicRisk
  recommendation: string
}

export function checkGalvanicCompatibility(mat1: string, mat2: string): GalvanicResult {
  const v1 = GALVANIC_SERIES[mat1]
  const v2 = GALVANIC_SERIES[mat2]
  if (v1 === undefined || v2 === undefined) {
    throw new Error("Unknown material")
  }
  const diff = Math.abs(v1 - v2)
  const anode = v1 < v2 ? mat1 : mat2
  const cathode = v1 < v2 ? mat2 : mat1

  let risk: GalvanicRisk
  let recommendation: string

  if (diff < 50) {
    risk = "low"
    recommendation = "Compatible — minimal galvanic corrosion risk."
  } else if (diff < 250) {
    risk = "medium"
    recommendation = `Moderate risk. ${anode} will corrode preferentially. Consider insulating gasket or coating.`
  } else {
    risk = "high"
    recommendation = `High risk. ${anode} will corrode rapidly. Isolate materials with non-conductive gasket, coating, or use intermediate alloy.`
  }

  return { anode, cathode, potential_mv: diff, risk, recommendation }
}
