from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Rating = Literal["recommended", "conditional", "incompatible"]


@dataclass
class MaterialRating:
    material: str
    rating: Rating
    note: str = ""


@dataclass
class ComponentRecommendation:
    component: str
    materials: list[MaterialRating]


@dataclass
class _MaterialEntry:
    """Internal entry with limits for temperature/concentration filtering."""
    rating: Rating
    note: str
    max_temp_c: float | None = None
    min_conc_pct: float | None = None
    max_conc_pct: float | None = None


def _e(rating: Rating, note: str = "",
       max_temp: float | None = None,
       min_conc: float | None = None,
       max_conc: float | None = None) -> _MaterialEntry:
    return _MaterialEntry(rating=rating, note=note,
                          max_temp_c=max_temp, min_conc_pct=min_conc, max_conc_pct=max_conc)


_TABLE: dict[str, dict[str, dict[str, _MaterialEntry]]] = {
    "water": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("recommended"),
            "Alloy 20": _e("recommended"),
            "Carbon Steel": _e("conditional", "use with coating"),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "Carbon/Ceramic": _e("recommended"),
            "Viton": _e("recommended"),
            "EPDM": _e("recommended"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "EPDM": _e("recommended"),
            "NBR": _e("recommended"),
            "PTFE": _e("recommended"),
        },
    },
    "seawater": {
        "casing": {
            "Cast Iron": _e("conditional", "risk of corrosion without coating"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible", "galvanic corrosion risk"),
            "SS 316": _e("conditional", "check chloride levels"),
            "Bronze": _e("recommended"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "wear_ring": {
            "SS 316": _e("conditional"),
            "Bronze": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("conditional", "pitting risk"),
            "Duplex SS": _e("recommended"),
            "Super Duplex": _e("recommended"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("recommended"),
            "Viton": _e("recommended"),
            "EPDM": _e("incompatible"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "EPDM": _e("conditional", "check temp", max_temp=60.0),
            "NBR": _e("conditional", "limited life"),
            "PTFE": _e("recommended"),
        },
    },
    "sulfuric_acid": {
        "casing": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("conditional", "only < 5% or > 93% concentration", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
            "PTFE-lined": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("conditional", "narrow concentration range", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "wear_ring": {
            "SS 316": _e("conditional", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("conditional", max_conc=5.0),
            "Alloy 20": _e("recommended"),
            "Hastelloy C": _e("recommended"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("conditional", "< 60% concentration", max_conc=60.0),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "PTFE": _e("recommended"),
            "Viton": _e("conditional", "< 70% concentration", max_conc=70.0),
            "EPDM": _e("incompatible"),
            "NBR": _e("incompatible"),
        },
    },
    "hydrochloric_acid": {
        "casing": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("incompatible"),
            "Hastelloy C": _e("recommended"),
            "Rubber-lined": _e("recommended"),
            "PTFE-lined": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("incompatible"),
            "SS 316": _e("incompatible"),
            "Hastelloy C": _e("recommended"),
            "Rubber": _e("recommended", "< 60°C", max_temp=60.0),
        },
        "wear_ring": {
            "Hastelloy C": _e("recommended"),
            "PTFE": _e("recommended"),
        },
        "shaft": {
            "Hastelloy C": _e("recommended"),
            "SS 316": _e("incompatible"),
        },
        "mechanical_seal": {
            "SiC/SiC": _e("recommended"),
            "Carbon/SiC": _e("incompatible"),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
            "EPDM": _e("incompatible"),
            "NBR": _e("incompatible"),
        },
    },
    "caustic_soda": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("recommended", "< 60°C", max_temp=60.0),
            "Duplex SS": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("conditional", "< 60°C", max_temp=60.0),
            "Duplex SS": _e("recommended"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
        },
        "shaft": {
            "SS 316": _e("recommended"),
            "Carbon Steel": _e("conditional", "< 60°C", max_temp=60.0),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "SiC/SiC": _e("recommended"),
            "EPDM": _e("recommended"),
            "Viton": _e("incompatible"),
        },
        "o_rings": {
            "EPDM": _e("recommended"),
            "PTFE": _e("recommended"),
            "Viton": _e("incompatible"),
            "NBR": _e("conditional", "< 40°C", max_temp=40.0),
        },
    },
    "diesel": {
        "casing": {
            "Cast Iron": _e("recommended"),
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "impeller": {
            "Cast Iron": _e("recommended"),
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "wear_ring": {
            "Cast Iron": _e("recommended"),
            "SS 316": _e("recommended"),
            "Bronze": _e("recommended"),
        },
        "shaft": {
            "Carbon Steel": _e("recommended"),
            "SS 316": _e("recommended"),
        },
        "mechanical_seal": {
            "Carbon/SiC": _e("recommended"),
            "Viton": _e("recommended"),
            "NBR": _e("recommended"),
            "EPDM": _e("incompatible"),
        },
        "o_rings": {
            "Viton": _e("recommended"),
            "NBR": _e("recommended"),
            "EPDM": _e("incompatible"),
            "PTFE": _e("recommended"),
        },
    },
}

COMPONENTS = ["casing", "impeller", "wear_ring", "shaft", "mechanical_seal", "o_rings"]


def _evaluate_rating(entry: _MaterialEntry, temp_c: float, concentration_pct: float) -> MaterialRating:
    """Evaluate a material entry against actual operating conditions."""
    if entry.rating == "incompatible":
        return MaterialRating(material="", rating="incompatible", note=entry.note)

    if entry.max_temp_c is not None and temp_c > entry.max_temp_c:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible above {entry.max_temp_c}°C (operating at {temp_c}°C)",
        )

    if entry.max_conc_pct is not None and concentration_pct > entry.max_conc_pct:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible above {entry.max_conc_pct}% concentration (operating at {concentration_pct}%)",
        )
    if entry.min_conc_pct is not None and concentration_pct < entry.min_conc_pct:
        return MaterialRating(
            material="",
            rating="incompatible",
            note=f"Incompatible below {entry.min_conc_pct}% concentration (operating at {concentration_pct}%)",
        )

    return MaterialRating(material="", rating=entry.rating, note=entry.note)


def select_materials(
    fluid: str,
    concentration_pct: float,
    temp_c: float,
) -> list[ComponentRecommendation]:
    if fluid not in _TABLE:
        raise ValueError(f"Unknown fluid '{fluid}'. Available: {list(_TABLE.keys())}")

    fluid_data = _TABLE[fluid]
    result = []
    for component in COMPONENTS:
        if component not in fluid_data:
            continue
        comp_data = fluid_data[component]
        materials = []
        for mat_name, entry in comp_data.items():
            evaluated = _evaluate_rating(entry, temp_c, concentration_pct)
            materials.append(MaterialRating(
                material=mat_name,
                rating=evaluated.rating,
                note=evaluated.note,
            ))
        result.append(ComponentRecommendation(component=component, materials=materials))
    return result
