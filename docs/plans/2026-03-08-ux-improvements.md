# UX/UI Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 4-layer UX/UI improvements: quick fixes, component migration + validation, stub pages with locked preview, and visual polish.

**Architecture:** All UI components use design tokens defined in `globals.css`. Reusable form primitives live in `components/ui/calc-form.tsx` and `components/ui/calc-card.tsx`. i18n via `next-intl` with keys in `i18n/en.json`, `pt.json`, `es.json`.

**Tech Stack:** Next.js 15 (App Router), Tailwind CSS, `tw-animate-css` (already installed), `next-intl`, `sonner` (toasts), shadcn/ui base components.

---

## LAYER 1 — Quick Fixes

### Task 1: Fix duplicate `headLoss` i18n key + add missing keys

**Files:**
- Modify: `apps/web/i18n/en.json`
- Modify: `apps/web/i18n/pt.json`
- Modify: `apps/web/i18n/es.json`

**Context:** `en.json` has two `"headLoss"` keys — the first has wrong NPSH content. JSON parsers use the last key, so the bad one silently shadows nothing, but it's still invalid and confusing. Also `"common.loading"` exists in en.json but `loading.tsx` uses a hardcoded string.

**Step 1: Remove the first (bad) `headLoss` block from `en.json`**

In `apps/web/i18n/en.json`, find and remove this block (it appears before the correct one):
```json
"headLoss": {
  "title": "NPSH Calculator",
  "subtitle": "Net Positive Suction Head available",
  "result": "NPSHa Result",
  "safe": "Safe",
  "risk": "Cavitation Risk",
  "calculate": "Calculate NPSHa",
  "calculating": "Calculating..."
},
```

The correct `headLoss` block (keep this one):
```json
"headLoss": {
  "title": "Head Loss",
  "description": "Darcy-Weisbach friction losses in piping"
},
```

**Step 2: Verify `en.json` is valid JSON**

```bash
node -e "JSON.parse(require('fs').readFileSync('apps/web/i18n/en.json','utf8')); console.log('valid')"
```
Expected: `valid`

**Step 3: Apply same fix to `pt.json` and `es.json`**

In `apps/web/i18n/pt.json`, find and remove the first `headLoss` block (with NPSH content). Do the same for `es.json`. Validate each:
```bash
node -e "JSON.parse(require('fs').readFileSync('apps/web/i18n/pt.json','utf8')); console.log('valid')"
node -e "JSON.parse(require('fs').readFileSync('apps/web/i18n/es.json','utf8')); console.log('valid')"
```

**Step 4: Commit**
```bash
git add apps/web/i18n/
git commit -m "fix: remove duplicate headLoss i18n key in all locales"
```

---

### Task 2: Fix hardcoded string in `loading.tsx`

**Files:**
- Modify: `apps/web/app/(app)/loading.tsx`

**Context:** `loading.tsx` has `<p>Loading…</p>` hardcoded. `"common.loading"` already exists in all locale files. But `loading.tsx` is a Server Component — use `getTranslations` from `next-intl/server`.

**Step 1: Update `loading.tsx`**

Replace the entire file content:
```tsx
import { getTranslations } from "next-intl/server"

export default async function AppLoading() {
  const t = await getTranslations("common")
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-4" aria-live="polite" aria-busy="true">
      <div className="flex flex-col items-center gap-3">
        <div
          className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-blue-500"
          aria-hidden
        />
        <p className="text-sm text-white/60">{t("loading")}</p>
      </div>
    </div>
  )
}
```

**Step 2: Commit**
```bash
git add "apps/web/app/(app)/loading.tsx"
git commit -m "fix: use i18n for loading text instead of hardcoded string"
```

---

### Task 3: Restore `headLoss` and `convert` to calculator list

**Files:**
- Modify: `apps/web/app/(app)/calc/page.tsx`

**Context:** The previous commit removed `headLoss` and `convert` from the `CALCULATORS` array (routes `/calc/head-loss` and `/calc/convert`). These routes don't have pages built yet, but they should remain listed with a "Soon" badge so users know they're coming.

**Step 1: Add the two items back to `CALCULATORS` in `calc/page.tsx`**

Add to the end of the `CALCULATORS` array:
```tsx
{ href: "/calc/head-loss", key: "headLoss", badge: "Soon" },
{ href: "/calc/convert", key: "convert", badge: "Soon" },
```

The full updated array:
```tsx
const CALCULATORS = [
  { href: "/calc/parallel-pumps", key: "parallelPumps", badge: "New" },
  { href: "/calc/npsh", key: "npsh", badge: "Essential" },
  { href: "/calc/material-selection", key: "materialSelection", badge: "New" },
  { href: "/calc/galvanic", key: "galvanic", badge: "New" },
  { href: "/calc/bolt-torque", key: "boltTorque", badge: "New" },
  { href: "/calc/flanges", key: "flanges", badge: "New" },
  { href: "/calc/head-loss", key: "headLoss", badge: "Soon" },
  { href: "/calc/convert", key: "convert", badge: "Soon" },
] as const
```

**Step 2: Update badge rendering in `CalcPage` to handle "Soon"**

In the badge `<span>`, update the ternary to handle 3 values:
```tsx
{c.badge && (
  <span className={cn(
    "text-xs px-2 py-0.5 rounded-full border",
    c.badge === "Essential"
      ? "bg-blue-900/50 text-blue-400 border-blue-500/30"
      : c.badge === "Soon"
        ? "bg-white/5 text-white/40 border-white/10"
        : "bg-blue-900/50 text-blue-400 border-blue-500/30"
  )}>
    {c.badge === "Essential"
      ? tCommon("badgeEssential")
      : c.badge === "Soon"
        ? tCommon("soon")
        : tCommon("badgeNew")}
  </span>
)}
```

Add `import { cn } from "@/lib/utils"` at the top if not present.

**Step 3: Commit**
```bash
git add "apps/web/app/(app)/calc/page.tsx"
git commit -m "fix: restore head-loss and convert to calculator list with Soon badge"
```

---

## LAYER 2 — Component Migration + Validation

### Task 4: Migrate `BoltTorqueForm`

**Files:**
- Modify: `apps/web/components/calc/BoltTorqueForm.tsx`

**Context:** `BoltTorqueForm` has 2 `<select>` + 1 `<fieldset>` of radio buttons (condition). No text inputs so no validation needed. Migrate selects to `CalcSelect`, labels to `CalcLabel`, result card to `CalcCard`. Add `setResult(null)` on change.

**Step 1: Add imports**
```tsx
import { CalcSelect, CalcLabel } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
```

**Step 2: Migrate grade select**

Replace:
```tsx
<label htmlFor="bolt-grade" className="block text-sm font-medium text-white/80">Bolt Grade</label>
<select id="bolt-grade" value={grade} onChange={e => setGrade(e.target.value)} className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40">
```

With:
```tsx
<CalcLabel htmlFor="bolt-grade">Bolt Grade</CalcLabel>
<CalcSelect id="bolt-grade" value={grade} onChange={e => { setGrade(e.target.value); setResult(null) }}>
```

Close with `</CalcSelect>` instead of `</select>`.

**Step 3: Migrate diameter select**

Same pattern — `CalcLabel` + `CalcSelect` with `setResult(null)` on change.

**Step 4: Migrate result card**

Replace:
```tsx
<div className="rounded-lg border border-white/10 p-4 space-y-3" style={{ backgroundColor: "#1A1D27" }}>
```
With:
```tsx
<CalcCard className="space-y-3">
```
And close with `</CalcCard>`.

**Step 5: Add inline spinner to submit button**

Replace the button content:
```tsx
<button
  type="submit"
  disabled={loading}
  className="w-full h-12 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium transition-colors flex items-center justify-center gap-2"
  aria-busy={loading}
>
  {loading ? (
    <>
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
      Calculating…
    </>
  ) : "Calculate Torque"}
</button>
```

**Step 6: Commit**
```bash
git add apps/web/components/calc/BoltTorqueForm.tsx
git commit -m "refactor: migrate BoltTorqueForm to CalcSelect/CalcCard + spinner"
```

---

### Task 5: Migrate `GalvanicForm`

**Files:**
- Modify: `apps/web/components/calc/GalvanicForm.tsx`

**Context:** Two `<select>` dropdowns, no text input, instant result (no API call, no loading state). Migrate to `CalcSelect`/`CalcLabel`/`CalcCard`. No validation needed (selects always have a valid value when non-empty; the button is already disabled when either is empty or both equal).

**Step 1: Add imports**
```tsx
import { CalcSelect, CalcLabel } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
```

**Step 2: Migrate the mapped selects**

The form iterates `[{ id, label, value, set }]`. Replace the inner `label`/`select` with `CalcLabel`/`CalcSelect`:
```tsx
<CalcLabel htmlFor={id}>{label}</CalcLabel>
<CalcSelect id={id} value={value} onChange={e => { set(e.target.value); setResult(null) }}>
  <option value="">Select material...</option>
  {MATERIALS.map(m => <option key={m} value={m}>{m}</option>)}
</CalcSelect>
```

**Step 3: Migrate result card**

Find the result container:
```tsx
<div className={`rounded-lg border p-4 space-y-3 ${riskBg[result.risk]}`}>
```
Replace with `CalcCard` — but keep the dynamic background class since `riskBg` overrides the default. Pass the risk class via `className`:
```tsx
<CalcCard className={`space-y-3 ${riskBg[result.risk]}`}>
```
Close with `</CalcCard>`.

**Step 4: Commit**
```bash
git add apps/web/components/calc/GalvanicForm.tsx
git commit -m "refactor: migrate GalvanicForm to CalcSelect/CalcCard"
```

---

### Task 6: Migrate `MaterialSelectionForm`

**Files:**
- Modify: `apps/web/components/calc/MaterialSelectionForm.tsx`

**Context:** Already has validation logic. Just swap raw classes to design-system components. Has 1 `<select>` (fluid), 2 `<input type="text">` (concentration, temp), and a results table.

**Step 1: Add imports**
```tsx
import { CalcInput, CalcSelect, CalcLabel, CalcError } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
```

**Step 2: Migrate fluid select**

Replace:
```tsx
<label htmlFor="material-fluid" className="block text-sm font-medium text-white/80">Fluid</label>
<select id="material-fluid" ... className="w-full h-12 px-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-500/40">
```
With:
```tsx
<CalcLabel htmlFor="material-fluid">Fluid</CalcLabel>
<CalcSelect id="material-fluid" ...>
```

**Step 3: Migrate concentration and temp inputs**

Replace the raw `<input>` elements with `<CalcInput>`. Keep `aria-invalid` and `aria-describedby` already there. Replace raw error `<p>` with `<CalcError>`:
```tsx
<CalcLabel htmlFor="material-concentration">Concentration (%)</CalcLabel>
<CalcInput
  id="material-concentration"
  type="text"
  inputMode="decimal"
  value={concentration}
  onChange={e => { setConcentration(e.target.value); setErrors(p => ({ ...p, concentration: undefined })); setResult(null) }}
  aria-invalid={errors.concentration ? "true" : undefined}
  aria-describedby={errors.concentration ? "material-concentration-error" : undefined}
/>
{errors.concentration && <CalcError id="material-concentration-error">{errors.concentration}</CalcError>}
```

Same for `temp`.

**Step 4: Migrate result container**

Per component result card:
```tsx
// Replace:
<div className="rounded-lg border border-white/10 overflow-hidden" style={{ backgroundColor: "#1A1D27" }}>
// With:
<CalcCard className="overflow-hidden p-0">
```
Close with `</CalcCard>`. Adjust inner padding if needed (the card has `p-4` by default — use `p-0` override and keep inner divs' own padding).

**Step 5: Commit**
```bash
git add apps/web/components/calc/MaterialSelectionForm.tsx
git commit -m "refactor: migrate MaterialSelectionForm to design-system components"
```

---

### Task 7: Migrate `FlangeTable`

**Files:**
- Modify: `apps/web/components/calc/FlangeTable.tsx`

**Context:** Two selects (NPS, class), instant result table (no API, no submit). Migrate to `CalcSelect`/`CalcLabel`/`CalcCard`.

**Step 1: Add imports**
```tsx
import { CalcSelect, CalcLabel } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
```

**Step 2: Migrate NPS and class selects**
```tsx
<CalcLabel htmlFor="flange-nps">NPS</CalcLabel>
<CalcSelect id="flange-nps" value={nps} onChange={e => setNps(e.target.value)}>
  <option value="">Select NPS</option>
  {NPS_OPTIONS.map(n => <option key={n} value={n}>{n}"</option>)}
</CalcSelect>
```
Same for class select.

**Step 3: Migrate result card**

Replace:
```tsx
<div className="rounded-lg border border-white/10 overflow-hidden" style={{ backgroundColor: "#1A1D27" }}>
```
With:
```tsx
<CalcCard className="overflow-hidden p-0">
```
Close with `</CalcCard>`.

**Step 4: Commit**
```bash
git add apps/web/components/calc/FlangeTable.tsx
git commit -m "refactor: migrate FlangeTable to CalcSelect/CalcCard"
```

---

### Task 8: Migrate `ParallelPumpsForm` (partial — tokens only)

**Files:**
- Modify: `apps/web/components/calc/ParallelPumpsForm.tsx`

**Context:** The H-Q point grid inputs are too dense for `CalcInput` (h-12). Instead, replace raw opacity classes with CSS variable tokens. Migrate labeled sections to `CalcLabel` and result card to `CalcCard`.

**Step 1: Add imports**
```tsx
import { CalcLabel } from "@/components/ui/calc-form"
import { CalcCard } from "@/components/ui/calc-card"
```

**Step 2: Replace raw classes on all standalone inputs with token classes**

For every `input` that uses `bg-white/5 border border-white/10`, replace with:
```
bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)]
```

For placeholders: replace `placeholder:text-white/30` or `placeholder:text-white/40` with `placeholder:text-[var(--color-text-hint)]`.

**Step 3: Replace section labels**

Replace:
```tsx
<label htmlFor="parallel-static-head" className="text-xs text-white/60 block">Static Head (m)</label>
```
With:
```tsx
<CalcLabel htmlFor="parallel-static-head" className="text-xs">Static Head (m)</CalcLabel>
```

**Step 4: Migrate result card**

Find the result container (a `div` with `rounded-lg border border-white/10` + inline `backgroundColor`) and replace with `<CalcCard>`.

**Step 5: Commit**
```bash
git add apps/web/components/calc/ParallelPumpsForm.tsx
git commit -m "refactor: use design tokens in ParallelPumpsForm, migrate result to CalcCard"
```

---

## LAYER 3 — Stub Pages (Locked Preview)

### Task 9: Norms page with locked preview

**Files:**
- Modify: `apps/web/app/(app)/norms/page.tsx`

**Context:** Show a search field + 3 blurred mock result cards with a Pro upgrade overlay. All static — no data fetching.

**Step 1: Replace `norms/page.tsx` with:**
```tsx
import { getTranslations } from "next-intl/server"
import Link from "next/link"
import { Lock } from "lucide-react"

export default async function NormsPage() {
  const t = await getTranslations()

  const MOCK_RESULTS = [
    { norm: "API 610", section: "Section 6.1.3", excerpt: "Minimum continuous stable flow shall be defined by the pump manufacturer based on acceptable vibration levels, temperature rise, and internal recirculation..." },
    { norm: "ASME B73.1", section: "Section 4.2", excerpt: "Pump casings shall be hydrostatically tested at 1.5 times the maximum allowable working pressure. Test duration shall not be less than 30 minutes..." },
    { norm: "ISO 5199", section: "Clause 5.3", excerpt: "The NPSH available (NPSHa) shall exceed the NPSH required (NPSHr) by a margin of at least 0.5 m under all specified operating conditions..." },
  ]

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("norms.title")}</h1>

      {/* Search field — disabled */}
      <div className="relative">
        <input
          type="text"
          disabled
          placeholder={t("norms.placeholder")}
          className="w-full h-12 px-4 rounded-lg bg-[var(--color-input-bg)] border border-[var(--color-border-subtle)] text-white/40 placeholder:text-white/30 cursor-not-allowed"
        />
      </div>

      {/* Mock results with blur overlay */}
      <div className="relative">
        <div className="space-y-3 select-none pointer-events-none" style={{ filter: "blur(3px)" }}>
          {MOCK_RESULTS.map(r => (
            <div
              key={r.norm}
              className="rounded-lg border border-[var(--color-border-subtle)] p-4 bg-[var(--color-surface-secondary)] space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded-full border border-blue-500/20">{r.norm}</span>
                <span className="text-xs text-white/40">{r.section}</span>
              </div>
              <p className="text-sm text-white/70 leading-relaxed">{r.excerpt}</p>
            </div>
          ))}
        </div>

        {/* Pro overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 rounded-lg bg-[var(--color-surface)]/80 backdrop-blur-sm">
          <Lock size={28} className="text-blue-400" />
          <div className="text-center">
            <p className="text-sm font-semibold text-white mb-1">{t("norms.proTitle")}</p>
            <p className="text-xs text-white/60 max-w-xs">{t("norms.proDescription")}</p>
          </div>
          <Link
            href="/account"
            className="rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors px-5 py-2.5 text-sm font-medium text-white"
          >
            {t("account.upgrade")}
          </Link>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Add missing i18n keys to all 3 locale files**

In `i18n/en.json` under `"norms"`:
```json
"proTitle": "Unlock Norm Consultant",
"proDescription": "Search API, ASME, ISO standards with AI-powered answers and exact citations."
```

In `pt.json`:
```json
"proTitle": "Desbloqueie o Consultor de Normas",
"proDescription": "Pesquise normas API, ASME, ISO com respostas via IA e citações exatas."
```

In `es.json`:
```json
"proTitle": "Desbloquea el Consultor de Normas",
"proDescription": "Busca normas API, ASME, ISO con respuestas de IA y citas exactas."
```

**Step 3: Commit**
```bash
git add "apps/web/app/(app)/norms/page.tsx" apps/web/i18n/
git commit -m "feat: norms stub page with locked Pro preview"
```

---

### Task 10: Diagnosis page with locked preview

**Files:**
- Modify: `apps/web/app/(app)/diagnosis/page.tsx`

**Step 1: Replace `diagnosis/page.tsx` with:**
```tsx
import { getTranslations } from "next-intl/server"
import Link from "next/link"
import { ImageIcon, Lock } from "lucide-react"

export default async function DiagnosisPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold text-white">{t("diagnosis.title")}</h1>

      {/* Upload area — disabled */}
      <div className="rounded-lg border-2 border-dashed border-white/20 p-8 flex flex-col items-center gap-3 cursor-not-allowed opacity-50">
        <ImageIcon size={32} className="text-white/40" />
        <p className="text-sm text-white/50 text-center">{t("diagnosis.uploadHint")}</p>
        <p className="text-xs text-white/30">{t("diagnosis.uploadFormats")}</p>
      </div>

      {/* Mock result with blur overlay */}
      <div className="relative">
        <div className="select-none pointer-events-none rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)] p-4 space-y-3" style={{ filter: "blur(3px)" }}>
          <h3 className="text-sm font-semibold text-white">Diagnosis Result</h3>
          <div className="space-y-2">
            {[
              { label: "Root Cause", value: "Cavitation — suction pressure below vapor pressure at operating temperature" },
              { label: "Severity", value: "High — immediate action required" },
              { label: "Immediate Action", value: "Reduce flow demand or increase suction head. Check NPSH available." },
              { label: "Preventive Action", value: "Install suction strainer. Review system curve and operating point." },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-white/40 font-medium uppercase tracking-wide">{label}</p>
                <p className="text-sm text-white/80 mt-0.5">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Pro overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 rounded-lg bg-[var(--color-surface)]/80 backdrop-blur-sm">
          <Lock size={28} className="text-blue-400" />
          <div className="text-center">
            <p className="text-sm font-semibold text-white mb-1">{t("diagnosis.proTitle")}</p>
            <p className="text-xs text-white/60 max-w-xs">{t("diagnosis.proDescription")}</p>
          </div>
          <Link
            href="/account"
            className="rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors px-5 py-2.5 text-sm font-medium text-white"
          >
            {t("account.upgrade")}
          </Link>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Add missing i18n keys to all 3 locale files**

In `i18n/en.json` under `"diagnosis"`:
```json
"uploadHint": "Drag or select a component photo",
"uploadFormats": "JPG, PNG, PDF — mechanical seal, impeller, casing",
"proTitle": "Unlock Photo Diagnosis",
"proDescription": "Upload a photo of any pump component and get AI-powered failure analysis with recommended actions."
```

In `pt.json`:
```json
"uploadHint": "Arraste ou selecione uma foto do componente",
"uploadFormats": "JPG, PNG, PDF — vedação mecânica, rotor, carcaça",
"proTitle": "Desbloqueie o Diagnóstico por Foto",
"proDescription": "Envie uma foto de qualquer componente de bomba e receba análise de falha via IA com ações recomendadas."
```

In `es.json`:
```json
"uploadHint": "Arrastra o selecciona una foto del componente",
"uploadFormats": "JPG, PNG, PDF — sello mecánico, impulsor, carcasa",
"proTitle": "Desbloquea el Diagnóstico por Foto",
"proDescription": "Sube una foto de cualquier componente de bomba y recibe análisis de fallo con IA y acciones recomendadas."
```

**Step 3: Commit**
```bash
git add "apps/web/app/(app)/diagnosis/page.tsx" apps/web/i18n/
git commit -m "feat: diagnosis stub page with locked Pro preview"
```

---

### Task 11: Account page with plan cards

**Files:**
- Modify: `apps/web/app/(app)/account/page.tsx`

**Context:** Show current plan (Free), static usage meters, and a plan comparison table. No Stripe integration — just static UI.

**Step 1: Replace `account/page.tsx` with:**
```tsx
import { getTranslations } from "next-intl/server"
import { Check } from "lucide-react"

const PLANS = [
  {
    key: "free",
    price: "$0",
    current: true,
    features: ["50 calculations / month", "10 AI queries / month", "3 languages (PT/EN/ES)", "PWA offline mode"],
    cta: null,
  },
  {
    key: "pro",
    price: "$19/mo",
    current: false,
    highlight: true,
    features: ["Unlimited calculations", "Unlimited AI queries", "PDF upload (500 MB)", "Exportable PDF reports", "Full history"],
    cta: "/account/upgrade",
  },
  {
    key: "enterprise",
    price: "$99/mo/org",
    current: false,
    features: ["Everything in Pro", "Isolated RAG base", "SSO + multi-user", "Priority SLA"],
    cta: "mailto:contact@engbrain.io",
  },
]

export default async function AccountPage() {
  const t = await getTranslations()

  return (
    <div className="p-4 space-y-6">
      <h1 className="text-xl font-bold text-white">{t("account.title")}</h1>

      {/* Current plan + usage */}
      <div className="rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)] p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-white/40 uppercase tracking-wide font-medium">{t("account.currentPlan")}</p>
            <p className="text-lg font-bold text-white mt-0.5">Free</p>
          </div>
          <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/60 border border-white/10">Active</span>
        </div>
        <div className="space-y-3">
          <UsageMeter label={t("account.calculations")} used={10} limit={50} />
          <UsageMeter label={t("account.aiQueries")} used={3} limit={10} />
        </div>
      </div>

      {/* Plan comparison */}
      <div className="space-y-3">
        <p className="text-sm font-medium text-white/60">{t("account.plans")}</p>
        {PLANS.map(plan => (
          <div
            key={plan.key}
            className={[
              "rounded-lg border p-4 space-y-3",
              plan.highlight
                ? "border-blue-500/40 bg-blue-950/20"
                : "border-[var(--color-border-subtle)] bg-[var(--color-surface-secondary)]",
            ].join(" ")}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-base font-semibold text-white capitalize">{plan.key}</p>
                <p className="text-sm text-white/50">{plan.price}</p>
              </div>
              {plan.current && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400 border border-green-500/30">
                  {t("account.currentPlan")}
                </span>
              )}
              {plan.highlight && !plan.current && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900/50 text-blue-400 border border-blue-500/30">
                  Popular
                </span>
              )}
            </div>
            <ul className="space-y-1.5">
              {plan.features.map(f => (
                <li key={f} className="flex items-start gap-2 text-sm text-white/70">
                  <Check size={14} className="text-green-400 mt-0.5 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
            {plan.cta && (
              <a
                href={plan.cta}
                className="block w-full text-center rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors py-2.5 text-sm font-medium text-white"
              >
                {t("account.upgrade")}
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function UsageMeter({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = Math.min((used / limit) * 100, 100)
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-white/60">{label}</span>
        <span className="text-white/40">{used} / {limit}</span>
      </div>
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-blue-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
```

**Step 2: Add i18n keys to all 3 locale files**

In `en.json` under `"account"`:
```json
"currentPlan": "Current plan",
"calculations": "Calculations",
"aiQueries": "AI queries",
"plans": "Available plans"
```

In `pt.json`:
```json
"currentPlan": "Plano atual",
"calculations": "Cálculos",
"aiQueries": "Consultas IA",
"plans": "Planos disponíveis"
```

In `es.json`:
```json
"currentPlan": "Plan actual",
"calculations": "Cálculos",
"aiQueries": "Consultas IA",
"plans": "Planes disponibles"
```

**Step 3: Commit**
```bash
git add "apps/web/app/(app)/account/page.tsx" apps/web/i18n/
git commit -m "feat: account stub page with plan comparison and usage meters"
```

---

## LAYER 4 — Visual Polish

### Task 12: Empty states in all calculator pages

**Files:**
- Modify: `apps/web/components/ui/calc-form.tsx`
- Modify: all `apps/web/app/(app)/calc/*/page.tsx` calculator pages that show results conditionally

**Context:** When no result has been computed yet, show a subtle placeholder below the form. The cleanest approach is a reusable `CalcEmptyState` component exported from `calc-form.tsx`.

**Step 1: Add `CalcEmptyState` to `calc-form.tsx`**

Add at the bottom of `apps/web/components/ui/calc-form.tsx`:
```tsx
import { BarChart2 } from "lucide-react"

const CalcEmptyState = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col items-center gap-2 py-8 text-center text-white/30",
        className
      )}
      {...props}
    >
      <BarChart2 size={28} aria-hidden />
      <p className="text-sm">{children}</p>
    </div>
  )
)
CalcEmptyState.displayName = "CalcEmptyState"

export { CalcInput, CalcSelect, CalcLabel, CalcHint, CalcError, CalcEmptyState }
```

**Step 2: Add `CalcEmptyState` to each form**

In each form component (`NPSHForm`, `BoltTorqueForm`, `GalvanicForm`, `MaterialSelectionForm`, `FlangeTable`, `ParallelPumpsForm`), after the form and before the result block, add:

```tsx
{!result && (
  <CalcEmptyState>Fill in the fields and calculate to see the result</CalcEmptyState>
)}
{result && (
  <CalcCard ...>
    {/* existing result content */}
  </CalcCard>
)}
```

For `FlangeTable` and `GalvanicForm` (instant result, no submit), use `!dims` and `!result` respectively.

**Step 3: Commit**
```bash
git add apps/web/components/ui/calc-form.tsx apps/web/components/calc/
git commit -m "feat: add empty state placeholder to all calculator forms"
```

---

### Task 13: Result card entrance animation + primary number styling

**Files:**
- Modify: `apps/web/app/globals.css`
- Modify: `apps/web/components/ui/calc-card.tsx`
- Modify: result rendering in all calc form components

**Context:** `tw-animate-css` is installed but not imported. Add import, then use `animate-in fade-in-0 slide-in-from-bottom-2` on result cards.

**Step 1: Import `tw-animate-css` in `globals.css`**

Add at the very top of `apps/web/app/globals.css`:
```css
@import "tw-animate-css";
```

**Step 2: Add animation classes to `CalcCard` result usage**

In each form, the result `CalcCard` should have animation classes:
```tsx
<CalcCard className="space-y-3 animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
```

Apply this to every result `CalcCard` across all 6 form components.

**Step 3: Style primary result numbers**

In each result card where there's a primary numeric value, apply:
- Value: `text-3xl font-bold text-white`
- Unit: `text-lg text-white/60 ml-1`

Example pattern in `NPSHForm` result:
```tsx
<div className="flex items-baseline gap-1">
  <span className="text-3xl font-bold text-white">{result.npsha_m.toFixed(2)}</span>
  <span className="text-lg text-white/60">m</span>
</div>
```

Apply the same pattern to primary values in `BoltTorqueForm` (torque_nm), `GalvanicForm` (voltage difference), `MaterialSelectionForm` (none — table format, skip).

**Step 4: Commit**
```bash
git add apps/web/app/globals.css apps/web/components/ui/calc-card.tsx apps/web/components/calc/
git commit -m "feat: result card entrance animation and primary number styling"
```

---

### Task 14: Inline spinner on all Calculate buttons

**Files:**
- Modify: all form components with a submit button

**Context:** Replace text-only loading state with spinner + text side by side. Pattern established in Task 4.

**Step 1: Apply spinner pattern to remaining forms**

For `MaterialSelectionForm`:
```tsx
<button type="submit" disabled={loading || !fluid} ... className="... flex items-center justify-center gap-2" aria-busy={loading}>
  {loading ? (
    <>
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden />
      {t("common.loading")}
    </>
  ) : "Select Materials"}
</button>
```

Apply same to `NPSHForm` and `ParallelPumpsForm` (these already have loading states).

**Step 2: Commit**
```bash
git add apps/web/components/calc/
git commit -m "feat: inline spinner on all calculate buttons"
```
