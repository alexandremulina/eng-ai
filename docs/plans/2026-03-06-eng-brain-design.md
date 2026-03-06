# EngBrain — Design Document
**Date:** 2026-03-06
**Status:** Approved

## Overview

Mobile-first PWA for pump engineers (internal corporate + autonomous consultants). Covers technical calculations, norm consulting via AI, and visual failure diagnosis. SaaS model with free/pro/enterprise tiers. Multi-language: PT / EN / ES.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router) + Tailwind + shadcn/ui — PWA |
| Backend | FastAPI (Python) — Railway |
| Database | Supabase (Postgres + pgvector + Auth + Storage) |
| AI | OpenRouter (routed per task) |
| Payments | Stripe |
| i18n | next-intl (PT / EN / ES) |

---

## Modules

### 1. Engineering Calculations

Python backend handles all calculations. LLMs never perform math directly.

**Libraries:** `fluids`, `scipy`, `numpy`, `pint`, `decimal`

**Calculators (MVP):**
- NPSH (available vs required) — cavitation prevention
- Head loss — Darcy-Weisbach
- Shaft power — hydraulic and mechanical efficiency
- Performance curve — operating point interpolation
- Unit conversion — `pint` (GPM↔m³/h, PSI↔bar↔kPa, etc.)
- Pipe sizing — optimal diameter by velocity/loss

**Flow:**
```
Frontend (form) → FastAPI → fluids/scipy → result with units → Frontend
```

**Precision:** results returned with configurable decimal places (4 for pressure, 2 for power). Units always explicit in JSON response.

**Offline (PWA):** simple unit conversions and quick estimates via Service Worker (JS/WASM). Complex calculations require connection.

---

### 2. Norm Consultant (RAG)

AI-powered Q&A grounded in technical standards (API 610, API 682, ASME B73, ISO 5199, etc.)

**RAG Architecture:**
```
PDF norms → chunks → embeddings → Supabase pgvector
User question → embeddings → semantic search → relevant excerpts
Excerpts + question → LLM → answer with exact citation
```

**Features:**
- Pre-loaded public norm base (legally permitted)
- User PDF upload (private manuals — Pro plan)
- Responses always include exact citation (norm + section + page)
- Query history per user

---

### 3. Photo Diagnosis (Computer Vision)

Engineer photographs component (mechanical seal, casing, impeller) and receives failure analysis + recommendation.

**Flow:**
```
Photo (mobile) → Supabase Storage → FastAPI → OpenRouter (Vision LLM) → diagnosis
```

**Features:**
- Failure analysis: corrosion, abrasion, fatigue, cavitation, wear
- Plate OCR: reads ID plate → auto-fetches pump specs
- Chart reading: interprets photographed performance curves
- Exportable PDF report: photo + diagnosis + probable cause + recommended action

**Response structure:** `root_cause`, `severity`, `immediate_action`, `preventive_action`, `confidence_level`

**UI disclaimer:** always shown — photo diagnosis is auxiliary, does not replace certified technical inspection.

---

### 4. Auth + SaaS

**Auth:** Supabase Auth — email/password + OAuth (Google, Microsoft)

**Plans:**

| Plan | Price | Limits |
|---|---|---|
| Free | $0 | 50 calculations/month, 10 AI queries/month, no PDF upload, no reports |
| Pro | $19/month | Unlimited + PDF upload (500MB) + PDF reports + full history |
| Enterprise | $99/month/org | Pro + isolated RAG base + SSO + multi-user + SLA |

**Stripe:** Hosted Checkout + Webhooks → Supabase updates user plan automatically. 14-day Pro trial, no card required.

**Usage control:** `usage_events` table in Supabase — FastAPI checks limit before each AI call.

---

### 5. UX / UI

**Theme:** Dark mode default (factory/field environments, variable lighting). Manual toggle always visible.
- Background: `#0F1117`
- Accent: `#0066FF` (industrial blue)
- Status: `#00C853` (green)

**Navigation pattern — Hybrid A+B:**
- Bottom nav (mobile): quick access to main modules
- Central FAB (+): opens AI Copilot as sheet/drawer
- Command palette (Cmd+K): keyboard access to any tool (desktop)

**Component principles:**
- Large inputs — usable with gloves in the field
- Results in large typography — primary number prominent, unit secondary
- Toasts for errors, never blocking modals
- Responsive tables that collapse cleanly on mobile

---

## LLM Routing (OpenRouter)

| Task | Model |
|---|---|
| Technical reasoning / calculation | `deepseek/deepseek-r1` |
| Norm RAG | `google/gemini-2.5-pro` |
| Vision / photo diagnosis | `google/gemini-2.5-pro` or `qwen/qwen2.5-vl-72b-instruct` |
| Report generation | `anthropic/claude-sonnet-4-6` |
| Fallback (speed/cost) | `meta-llama/llama-3.3-70b-instruct` |

Models selected dynamically by OpenRouter based on availability and cost. LLMs always generate reasoning or structured output — Python executes all math.

---

## Key Constraints

- **Precision:** Python handles all numeric computation; decimal precision configurable per calculation type
- **Offline:** PWA Service Worker caches UI + basic calculations; AI features require connection
- **Security:** Supabase RLS isolates user data; Enterprise RAG bases isolated per organization
- **Reliability:** AI responses always include confidence level; safety disclaimers on diagnosis features
