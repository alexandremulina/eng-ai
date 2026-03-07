export interface FlangeDimensions {
  nps: string
  class: number
  od_mm: number
  bolt_circle_mm: number
  num_bolts: number
  bolt_hole_mm: number
  thickness_mm: number
  rf_od_mm: number
  rf_height_mm: number
}

export const FLANGE_DATA: FlangeDimensions[] = [
  // Class 150
  { nps: "1/2",   class: 150, od_mm: 89,  bolt_circle_mm: 60.3,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 11.2,  rf_od_mm: 35,  rf_height_mm: 1.6 },
  { nps: "3/4",   class: 150, od_mm: 98,  bolt_circle_mm: 69.9,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 12.7,  rf_od_mm: 43,  rf_height_mm: 1.6 },
  { nps: "1",     class: 150, od_mm: 108, bolt_circle_mm: 79.4,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 14.3,  rf_od_mm: 51,  rf_height_mm: 1.6 },
  { nps: "1-1/2", class: 150, od_mm: 127, bolt_circle_mm: 98.4,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 17.5,  rf_od_mm: 70,  rf_height_mm: 1.6 },
  { nps: "2",     class: 150, od_mm: 152, bolt_circle_mm: 120.7, num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 19.1,  rf_od_mm: 92,  rf_height_mm: 1.6 },
  { nps: "3",     class: 150, od_mm: 191, bolt_circle_mm: 152.4, num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 23.9,  rf_od_mm: 127, rf_height_mm: 1.6 },
  { nps: "4",     class: 150, od_mm: 229, bolt_circle_mm: 190.5, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 23.9,  rf_od_mm: 157, rf_height_mm: 1.6 },
  { nps: "6",     class: 150, od_mm: 279, bolt_circle_mm: 241.3, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 25.4,  rf_od_mm: 216, rf_height_mm: 1.6 },
  { nps: "8",     class: 150, od_mm: 343, bolt_circle_mm: 298.5, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 28.6,  rf_od_mm: 270, rf_height_mm: 1.6 },
  { nps: "10",    class: 150, od_mm: 406, bolt_circle_mm: 362.0, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 30.2,  rf_od_mm: 324, rf_height_mm: 1.6 },
  { nps: "12",    class: 150, od_mm: 483, bolt_circle_mm: 431.8, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 31.8,  rf_od_mm: 381, rf_height_mm: 1.6 },
  // Class 300
  { nps: "1/2",   class: 300, od_mm: 95,  bolt_circle_mm: 66.7,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 14.3,  rf_od_mm: 35,  rf_height_mm: 1.6 },
  { nps: "3/4",   class: 300, od_mm: 117, bolt_circle_mm: 82.6,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 15.9,  rf_od_mm: 43,  rf_height_mm: 1.6 },
  { nps: "1",     class: 300, od_mm: 124, bolt_circle_mm: 88.9,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 17.5,  rf_od_mm: 51,  rf_height_mm: 1.6 },
  { nps: "1-1/2", class: 300, od_mm: 156, bolt_circle_mm: 114.3, num_bolts: 4,  bolt_hole_mm: 22.4, thickness_mm: 22.4,  rf_od_mm: 70,  rf_height_mm: 1.6 },
  { nps: "2",     class: 300, od_mm: 165, bolt_circle_mm: 127.0, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 25.4,  rf_od_mm: 92,  rf_height_mm: 1.6 },
  { nps: "3",     class: 300, od_mm: 210, bolt_circle_mm: 168.3, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 31.8,  rf_od_mm: 127, rf_height_mm: 1.6 },
  { nps: "4",     class: 300, od_mm: 254, bolt_circle_mm: 200.0, num_bolts: 8,  bolt_hole_mm: 22.4, thickness_mm: 38.1,  rf_od_mm: 157, rf_height_mm: 1.6 },
  { nps: "6",     class: 300, od_mm: 318, bolt_circle_mm: 269.9, num_bolts: 12, bolt_hole_mm: 22.4, thickness_mm: 44.5,  rf_od_mm: 216, rf_height_mm: 1.6 },
  { nps: "8",     class: 300, od_mm: 381, bolt_circle_mm: 330.2, num_bolts: 12, bolt_hole_mm: 25.4, thickness_mm: 50.8,  rf_od_mm: 270, rf_height_mm: 1.6 },
  { nps: "10",    class: 300, od_mm: 444, bolt_circle_mm: 387.4, num_bolts: 16, bolt_hole_mm: 28.6, thickness_mm: 57.2,  rf_od_mm: 324, rf_height_mm: 1.6 },
  { nps: "12",    class: 300, od_mm: 521, bolt_circle_mm: 450.9, num_bolts: 16, bolt_hole_mm: 28.6, thickness_mm: 63.5,  rf_od_mm: 381, rf_height_mm: 1.6 },
  // Class 600
  { nps: "1/2",   class: 600, od_mm: 95,  bolt_circle_mm: 66.7,  num_bolts: 4,  bolt_hole_mm: 15.9, thickness_mm: 22.4,  rf_od_mm: 35,  rf_height_mm: 6.4 },
  { nps: "1",     class: 600, od_mm: 124, bolt_circle_mm: 88.9,  num_bolts: 4,  bolt_hole_mm: 19.1, thickness_mm: 25.4,  rf_od_mm: 51,  rf_height_mm: 6.4 },
  { nps: "2",     class: 600, od_mm: 165, bolt_circle_mm: 127.0, num_bolts: 8,  bolt_hole_mm: 19.1, thickness_mm: 38.1,  rf_od_mm: 92,  rf_height_mm: 6.4 },
  { nps: "4",     class: 600, od_mm: 273, bolt_circle_mm: 215.9, num_bolts: 8,  bolt_hole_mm: 25.4, thickness_mm: 54.0,  rf_od_mm: 157, rf_height_mm: 6.4 },
  { nps: "6",     class: 600, od_mm: 356, bolt_circle_mm: 292.1, num_bolts: 12, bolt_hole_mm: 28.6, thickness_mm: 63.5,  rf_od_mm: 216, rf_height_mm: 6.4 },
  { nps: "8",     class: 600, od_mm: 419, bolt_circle_mm: 349.2, num_bolts: 12, bolt_hole_mm: 31.8, thickness_mm: 76.2,  rf_od_mm: 270, rf_height_mm: 6.4 },
  { nps: "10",    class: 600, od_mm: 508, bolt_circle_mm: 431.8, num_bolts: 16, bolt_hole_mm: 34.9, thickness_mm: 88.9,  rf_od_mm: 324, rf_height_mm: 6.4 },
  { nps: "12",    class: 600, od_mm: 559, bolt_circle_mm: 489.0, num_bolts: 20, bolt_hole_mm: 34.9, thickness_mm: 101.6, rf_od_mm: 381, rf_height_mm: 6.4 },
]

export const NPS_OPTIONS = [...new Set(FLANGE_DATA.map(f => f.nps))]
export const CLASS_OPTIONS = [...new Set(FLANGE_DATA.map(f => f.class))].sort((a, b) => a - b)

export function getFlangeDimensions(nps: string, cls: number): FlangeDimensions | null {
  return FLANGE_DATA.find(f => f.nps === nps && f.class === cls) ?? null
}
