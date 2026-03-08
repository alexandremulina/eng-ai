# UX/UI Improvements — Design Document
**Date:** 2026-03-08
**Status:** Approved

## Overview

Four-layer improvement pass over the EngBrain frontend. Ordered by dependency: bugs first, component consistency second, stub pages third, polish last.

---

## Layer 1 — Quick Fixes

| File | Change |
|---|---|
| `i18n/en.json`, `pt.json`, `es.json` | Remove duplicate `headLoss` key (first occurrence has wrong NPSH content) |
| `app/(app)/loading.tsx` | Replace hardcoded `"Loading…"` with `t("common.loading")` |
| `app/(app)/calc/page.tsx` | Restore `headLoss` and `convert` to calculator list with i18n keys |
| `i18n/*.json` | Add missing keys: `calc.headLoss.title/description`, `calc.convert.title/description`, `common.loading` |

---

## Layer 2 — Component Migration + Validation

All calculator forms migrate to the design-system components introduced in the current changes.

**Forms to migrate:** `BoltTorqueForm`, `GalvanicForm`, `MaterialSelectionForm`, `FlangeTable`, `ParallelPumpsForm`

**Per-form changes:**
- Replace raw `input`/`label` with `CalcInput`/`CalcLabel`/`CalcHint`/`CalcError`
- Replace raw result `div` with `CalcCard`
- Replace `select` with `CalcSelect`
- Add client-side `validate()` function called before submit
- Field-level inline errors via `CalcError` + `aria-invalid` + `aria-describedby`
- `setResult(null)` on any input change

**ParallelPumpsForm exception:** H-Q point grid inputs remain as raw `input` elements (dense grid layout incompatible with `h-12` CalcInput) but use CSS variable tokens (`bg-[var(--color-input-bg)]`, `border-[var(--color-border-subtle)]`) instead of raw opacity classes.

---

## Layer 3 — Stub Pages (Locked Preview)

### Norms (`/norms`)
- Page header
- Search field (disabled, placeholder: "Search norm or standard…")
- 3 mock result cards (API 610, ASME B73, ISO 5199) with content blurred via `filter: blur(4px) select-none pointer-events-none`
- Overlay with Pro badge + CTA button "Upgrade to Pro"

### Diagnosis (`/diagnosis`)
- Page header
- File upload area (disabled): dashed border, image icon, text "Drag or select a component photo (JPG, PNG, PDF)"
- Mock result card with fields `root_cause`, `severity`, `immediate_action` blurred
- Overlay with Pro badge + CTA button "Upgrade to Pro"

### Account (`/account`)
- Page header
- Current plan card: "Free plan" + usage meter (e.g. "10 / 50 calculations this month", "3 / 10 AI queries this month") — static values for now
- Plan comparison table: Free / Pro ($19/mo) / Enterprise ($99/mo/org) — columns highlight differences
- "Upgrade" CTA on Pro column — links to `/account/upgrade` (placeholder, no Stripe yet)

---

## Layer 4 — Flow + Visual Polish

### Empty states
All calculator pages: when no result has been computed yet, show a subtle placeholder below the form — small icon + text "Fill in the fields and calculate to see the result". Removes visual emptiness without adding noise.

### Result card entrance animation
When the result `CalcCard` mounts, animate: `opacity 0→1` + `translateY(8px→0)` over 200ms ease-out. Implemented via Tailwind `animate-in` (tailwindcss-animate) or a simple CSS class.

### Primary result number styling
In result cards, the main numeric value uses `text-3xl font-bold text-white`; the unit uses `text-lg text-white/60` — visually separating value from unit.

### Calculate button loading state
Replace text-only loading state with an inline spinner (16px rotating border div) + "Calculating…" text side by side. Button dimensions unchanged.

---

## Out of Scope

- Stripe integration on Account page
- Actual Pro/Enterprise gating logic
- Norms RAG backend
- Diagnosis AI backend
- i18n for stub page mock content (can be static strings for now)
