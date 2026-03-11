# EngBrain v2 — Feedback Flávia + Melhorias Técnicas

**Data:** 2026-03-10
**Origem:** Conversa com Flávia Santoro (engenheira de bombas) + revisão técnica

## 1. Título NPSHa (quick fix)

Renomear em 3 idiomas:
- EN: "NPSHa Calculator" / "Net Positive Suction Head Available"
- PT: "Calculadora NPSHa" / "NPSH disponível"
- ES: "Calculadora NPSHa" / "NPSH disponible"

**Arquivos:** `i18n/en.json`, `i18n/pt.json`, `i18n/es.json`

## 2. Sistema de Unidades Global

### Problema
Frontend hardcoded em kPa. Engenheiros brasileiros usam kg/cm². Sem seletor de unidade.

### Solução
- `UnitPreferencesProvider` (React Context) com persistência em localStorage
- Unidades de pressão: kPa (default), bar, psi, kg/cm², MPa
- Cada form usa preference como default, permite override local
- Conversão no frontend antes de enviar ao backend (API permanece em SI)
- Adicionar `kg/cm2: "kilogram_force / centimeter**2"` no `UNIT_MAP` (backend `units.py`)

### Arquivos
- Novo: `components/UnitPreferencesProvider.tsx`
- Editar: `apps/api/app/services/units.py` (adicionar kg/cm2)
- Editar: `components/calc/NPSHForm.tsx` (dropdown de unidade)
- Editar: todos os forms de cálculo que usam pressão

## 3. Filtro por Temperatura/Concentração na Seleção de Materiais (P0 — Segurança)

### Problema
Backend aceita `temp_c` e `concentration_pct` mas ignora ambos. Retorna mesmos materiais sempre. Recomendação errada pode causar falha em campo.

### Solução
Refatorar `material_selection.py`:

```python
# Cada material ganha metadata de limites
{
    "name": "Carbon Steel",
    "max_temp_c": 60,
    "min_concentration_pct": 0,
    "max_concentration_pct": 50,
    "notes": "Use with coating above 40°C",
    "rating": "conditional"  # muda para "incompatible" se fora dos limites
}
```

- Materiais fora da faixa → `incompatible` com motivo explícito
- Notas i18n retornadas na response
- Frontend exibe badge/tooltip com condição

### Arquivos
- Editar: `apps/api/app/services/material_selection.py`
- Editar: `apps/web/components/calc/MaterialSelectionForm.tsx`
- Editar: i18n files (notas de materiais)

## 4. Presets de Fluido no NPSH

### Problema
Engenheiro precisa pesquisar vapor pressure e density na internet.

### Solução
- Dropdown "Fluido comum": Água, Água quente, Diesel, Gasolina, etc.
- Campo temperatura do fluido
- Ao selecionar fluido + temperatura → preenche `vapor_pressure` e `density` automaticamente
- Tabela de propriedades no backend: água de 5°C a 100°C (interpolação linear)

### Arquivos
- Novo endpoint: `/calculations/fluid-properties?fluid=water&temp_c=25`
- Novo: `apps/api/app/services/fluid_properties.py`
- Editar: `components/calc/NPSHForm.tsx`

## 5. Explicações no Material Selection

### Problema
UI mostra "condicional" sem explicar a condição.

### Solução
- Backend retorna campo `notes` por material: "Usar com revestimento", "Somente abaixo de 60°C"
- Frontend: tooltip ou texto secundário abaixo do material
- Notas em i18n (3 idiomas)

### Arquivos
- Editar: `apps/api/app/services/material_selection.py` (adicionar notes)
- Editar: `components/calc/MaterialSelectionForm.tsx` (renderizar notes)

## 6. Aço Carbono — Visibilidade

### Status
Já existe no backend para água (shaft), soda cáustica e diesel. Verificar:
- UI renderiza corretamente?
- Adicionar para água em casing/impeller (condicional, com revestimento)
- Garantir destaque visual adequado

## Escopo Fora (YAGNI)

- Pump curves (já funciona)
- Login/conta para salvar preferences (localStorage)
- Unidades para todos os campos (foco em pressão agora)
- Expansão da tabela de materiais além do necessário

## Prioridade de Implementação

| Ordem | Item | Risco |
|-------|------|-------|
| 1 | Título NPSHa | Nenhum |
| 2 | Filtro temp/concentração materiais | Segurança |
| 3 | kg/cm² + seletor de unidade | UX |
| 4 | Presets de fluido NPSH | UX |
| 5 | Explicações materiais + visibilidade aço carbono | UX |
