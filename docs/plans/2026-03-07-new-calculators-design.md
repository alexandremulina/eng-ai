# EngBrain — New Calculators Design
**Date:** 2026-03-07
**Status:** Approved

## Overview

5 new modules based on field engineer feedback (Flávia Santoro). Priority order: parallel pump association (differentiator) → material selection → galvanic corrosion → bolt torque → ASME flanges.

---

## Module 1: Parallel Pump Association (Different Pumps)

**Differentiator:** no existing tool handles mixed-pump parallel association with operating point detection and safety alerts.

### Backend

**Endpoint:** `POST /calculations/parallel-pumps`

**Input:**
```json
{
  "pumps": [
    {
      "name": "Pump A",
      "points": [{"q": 0, "h": 45}, {"q": 10, "h": 40}, {"q": 20, "h": 30}],
      "bep_q": 15
    }
  ],
  "system_curve": {
    "static_head": 10,
    "resistance": 0.08
  }
}
```

**Algorithm:**
1. `scipy.interpolate.CubicSpline` per pump → `H(Q)` function
2. Invert to `Q(H)` per pump
3. Combined curve: `Q_total(H) = Q1(H) + Q2(H) + ... Qn(H)` (horizontal addition)
4. System curve: `H_sys(Q) = H_static + R * Q^2`
5. `scipy.optimize.brentq` → find intersection (operating point)
6. Back-calculate each pump's Q at operating H
7. Detect: Q < 0 (reverse flow), Q outside BEP ±20% (off-curve warning)

**Output:**
```json
{
  "operating_point": {"q_total": 28.5, "h": 22.3, "unit_q": "m3/h", "unit_h": "m"},
  "pumps": [
    {"name": "Pump A", "q": 15.2, "h": 22.3, "bep_ratio": 1.01, "alert": null},
    {"name": "Pump B", "q": 13.3, "h": 22.3, "bep_ratio": 0.78, "alert": "off_curve"}
  ],
  "combined_curve_points": [...],
  "system_curve_points": [...]
}
```

**Alerts:**
- `reverse_flow`: pump Q < 0 at operating H — pump must be isolated
- `off_curve`: pump operating outside BEP ±20%
- `no_intersection`: system curve never intersects combined curve

### Datasheet Extraction (AI)

**Endpoint:** `POST /calculations/parallel-pumps/extract-curve`

**Input:** multipart file upload (PDF or image)

**Flow:**
1. If PDF: extract first page as image (pdf2image)
2. Send image to OpenRouter Vision LLM (gemini-2.5-pro)
3. Prompt: extract H-Q curve data points as JSON array `[{"q": float, "h": float}]`
4. Validate: minimum 3 points, H decreasing as Q increases
5. Return extracted points → frontend pre-fills the editable table

**UI:** upload button opens file picker → extracted points populate table → user reviews/edits before calculating.

### Frontend

- `app/(app)/calc/parallel-pumps/page.tsx`
- `components/calc/ParallelPumpsForm.tsx`
- Per-pump card: name input + upload button + editable H-Q table (add/remove rows)
- `+ Add pump` button (max 4 pumps for MVP)
- System curve section: static head + resistance coefficient (or two operating points to auto-calculate R)
- Output: Recharts `LineChart` with individual curves + combined curve + system curve + operating point marker
- Results table: pump name, Q, H, BEP%, alert badge
- Alert banners for reverse flow / off-curve warnings

---

## Module 2: Material Selection

**Endpoint:** `POST /calculations/material-selection`

**Input:** fluid name, concentration (%), temperature (°C), pressure (bar)

**Logic:**
1. Lookup hardcoded compatibility table (Python dict: fluid → material → rating)
2. Ratings: `recommended` / `conditional` / `incompatible`
3. LLM fallback for fluids not in table (with explicit disclaimer)

**Components covered:** casing, impeller, wear ring, shaft, mechanical seal faces, O-rings

**Output table:**

| Component | Cast Iron | SS 316 | Duplex | Alloy 20 | PTFE |
|---|---|---|---|---|---|
| Casing | recommended | recommended | conditional | ... | - |
| Impeller | incompatible | recommended | recommended | ... | - |

**Frontend:** `app/(app)/calc/material-selection/page.tsx` — fluid autocomplete, temp/pressure inputs, result as color-coded table.

---

## Module 3: Galvanic Corrosion

**No API call needed — pure frontend lookup.**

**Data:** hardcoded galvanic series (NACE / MIL-STD-889) as TS constant:
```ts
// mV vs SCE, approximate midpoint of passive range
const GALVANIC_SERIES: Record<string, number> = {
  "Carbon Steel": -620,
  "Cast Iron": -610,
  "SS 304 (active)": -530,
  "SS 316 (passive)": -50,
  "Bronze": -300,
  ...
}
```

**Logic:**
- Difference > 250mV → High risk (red)
- 50–250mV → Medium risk (yellow)
- < 50mV → Low risk (green)
- Always show: which material is anode (corrodes), recommendation

**Frontend:** two multi-selects → instant result, no loading state.

---

## Module 4: Bolt Torque

**Endpoint:** `POST /calculations/bolt-torque`

**Formula:** `T = K × Fi × d`
- `K`: nut factor (0.20 dry, 0.15 lubricated, 0.12 cadmium-plated)
- `Fi`: preload = 0.75 × proof load × tensile stress area
- `d`: nominal diameter (m)

**Grades supported:** ASTM A193 B7, A2-70, A4-80, SAE Gr5, SAE Gr8, ISO 8.8 / 10.9 / 12.9

**Output:** tightening torque (N·m + ft·lb), preload force (kN), shear strength, proof load

**Frontend:** grade dropdown + diameter dropdown + condition radio → result card.

---

## Module 5: ASME B16.5 Flange Dimensions

**No API call needed — pure frontend lookup.**

**Data:** hardcoded dimensional table (TS constant):
- NPS: ½" to 24"
- Classes: 150 / 300 / 600 / 900 / 1500 / 2500#
- Fields: OD, bolt circle diameter, number of bolts, bolt hole diameter, flange thickness, raised face OD, raised face height

**Frontend:** two selects (NPS + class) → dimensional table renders instantly.

---

## Navigation

Add to `app/(app)/calc/page.tsx` calculator list:
- Parallel Pump Association (new — featured)
- Material Selection (new)
- Galvanic Corrosion Check (new)
- Bolt Torque (new)
- ASME B16.5 Flanges (new)
- NPSH (existing)
- Head Loss (existing, coming soon)

---

## Implementation Order

1. Backend: parallel pumps service + endpoint + extraction endpoint + tests
2. Frontend: ParallelPumpsForm + chart output
3. Backend: bolt torque service + endpoint + tests
4. Frontend: bolt torque UI
5. Frontend: galvanic corrosion (pure frontend)
6. Frontend: ASME flanges (pure frontend)
7. Backend: material selection service + endpoint + tests
8. Frontend: material selection UI
9. Update calc index page with all new entries
