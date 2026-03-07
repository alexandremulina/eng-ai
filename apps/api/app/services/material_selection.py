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


_TABLE: dict[str, dict[str, dict[str, tuple[Rating, str]]]] = {
    "water": {
        "casing":          {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "impeller":        {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "wear_ring":       {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", "")},
        "shaft":           {"SS 316": ("recommended", ""), "Alloy 20": ("recommended", ""), "Carbon Steel": ("conditional", "use with coating")},
        "mechanical_seal": {"Carbon/SiC": ("recommended", ""), "Carbon/Ceramic": ("recommended", ""), "Viton": ("recommended", ""), "EPDM": ("recommended", "")},
    },
    "seawater": {
        "casing":          {"Cast Iron": ("conditional", "risk of corrosion without coating"), "SS 316": ("recommended", ""), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "impeller":        {"Cast Iron": ("incompatible", "galvanic corrosion risk"), "SS 316": ("conditional", "check chloride levels"), "Bronze": ("recommended", ""), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "wear_ring":       {"SS 316": ("conditional", ""), "Bronze": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "shaft":           {"SS 316": ("conditional", "pitting risk"), "Duplex SS": ("recommended", ""), "Super Duplex": ("recommended", "")},
        "mechanical_seal": {"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("recommended", ""), "Viton": ("recommended", ""), "EPDM": ("incompatible", "")},
    },
    "sulfuric_acid": {
        "casing":          {"Cast Iron": ("incompatible", ""), "SS 316": ("conditional", "< 5% or > 93% concentration"), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", ""), "PTFE-lined": ("recommended", "")},
        "impeller":        {"Cast Iron": ("incompatible", ""), "SS 316": ("conditional", "narrow concentration range"), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "wear_ring":       {"SS 316": ("conditional", ""), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "shaft":           {"SS 316": ("conditional", ""), "Alloy 20": ("recommended", ""), "Hastelloy C": ("recommended", "")},
        "mechanical_seal": {"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("conditional", "< 60% conc"), "PTFE": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "hydrochloric_acid": {
        "casing":          {"Cast Iron": ("incompatible", ""), "SS 316": ("incompatible", ""), "Hastelloy C": ("recommended", ""), "Rubber-lined": ("recommended", ""), "PTFE-lined": ("recommended", "")},
        "impeller":        {"Cast Iron": ("incompatible", ""), "SS 316": ("incompatible", ""), "Hastelloy C": ("recommended", ""), "Rubber": ("recommended", "< 60°C")},
        "wear_ring":       {"Hastelloy C": ("recommended", ""), "PTFE": ("recommended", "")},
        "shaft":           {"Hastelloy C": ("recommended", ""), "SS 316": ("incompatible", "")},
        "mechanical_seal": {"SiC/SiC": ("recommended", ""), "Carbon/SiC": ("incompatible", ""), "PTFE": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "caustic_soda": {
        "casing":          {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Carbon Steel": ("recommended", "< 60°C"), "Duplex SS": ("recommended", "")},
        "impeller":        {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Carbon Steel": ("conditional", ""), "Duplex SS": ("recommended", "")},
        "wear_ring":       {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", "")},
        "shaft":           {"SS 316": ("recommended", ""), "Carbon Steel": ("conditional", "")},
        "mechanical_seal": {"Carbon/SiC": ("recommended", ""), "SiC/SiC": ("recommended", ""), "EPDM": ("recommended", ""), "Viton": ("incompatible", "")},
    },
    "diesel": {
        "casing":          {"Cast Iron": ("recommended", ""), "Carbon Steel": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "impeller":        {"Cast Iron": ("recommended", ""), "Carbon Steel": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "wear_ring":       {"Cast Iron": ("recommended", ""), "SS 316": ("recommended", ""), "Bronze": ("recommended", "")},
        "shaft":           {"Carbon Steel": ("recommended", ""), "SS 316": ("recommended", "")},
        "mechanical_seal": {"Carbon/SiC": ("recommended", ""), "Viton": ("recommended", ""), "NBR": ("recommended", ""), "EPDM": ("incompatible", "")},
    },
}

COMPONENTS = ["casing", "impeller", "wear_ring", "shaft", "mechanical_seal"]


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
        materials = [
            MaterialRating(material=mat, rating=rating, note=note)
            for mat, (rating, note) in comp_data.items()
        ]
        result.append(ComponentRecommendation(component=component, materials=materials))
    return result
