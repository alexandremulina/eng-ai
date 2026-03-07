from __future__ import annotations
from dataclasses import dataclass

# Nut factor K per condition (dimensionless)
NUT_FACTOR = {
    "dry": 0.20,
    "lubricated": 0.15,
    "cadmium": 0.12,
}

# Grade → proof load (MPa)
# Sources: ASTM A193, ISO 898-1, SAE J429
GRADE_DATA: dict[str, dict] = {
    "ASTM A193 B7":  {"proof_mpa": 862,  "tensile_mpa": 1034},
    "ASTM A193 B8":  {"proof_mpa": 207,  "tensile_mpa": 517},
    "ISO 8.8":       {"proof_mpa": 600,  "tensile_mpa": 800},
    "ISO 10.9":      {"proof_mpa": 830,  "tensile_mpa": 1040},
    "ISO 12.9":      {"proof_mpa": 970,  "tensile_mpa": 1220},
    "SAE Grade 5":   {"proof_mpa": 585,  "tensile_mpa": 827},
    "SAE Grade 8":   {"proof_mpa": 827,  "tensile_mpa": 1034},
    "A2-70":         {"proof_mpa": 450,  "tensile_mpa": 700},
    "A4-80":         {"proof_mpa": 600,  "tensile_mpa": 800},
}

# Tensile stress area for standard metric threads (mm²) — ISO 898
TENSILE_STRESS_AREA: dict[float, float] = {
    6.0:  20.1,
    8.0:  36.6,
    10.0: 58.0,
    12.0: 84.3,
    14.0: 115.0,
    16.0: 157.0,
    20.0: 245.0,
    24.0: 353.0,
    27.0: 459.0,
    30.0: 561.0,
    36.0: 817.0,
    42.0: 1120.0,
    48.0: 1470.0,
}


@dataclass
class BoltTorqueResult:
    grade: str
    diameter_mm: float
    condition: str
    proof_load_mpa: float
    preload_kn: float
    torque_nm: float
    torque_ftlb: float


def calculate_bolt_torque(
    grade: str,
    diameter_mm: float,
    condition: str = "dry",
) -> BoltTorqueResult:
    if grade not in GRADE_DATA:
        raise ValueError(f"Unknown grade '{grade}'. Available: {list(GRADE_DATA.keys())}")
    if condition not in NUT_FACTOR:
        raise ValueError(f"Unknown condition '{condition}'. Available: {list(NUT_FACTOR.keys())}")

    available = sorted(TENSILE_STRESS_AREA.keys())
    closest = min(available, key=lambda x: abs(x - diameter_mm))
    stress_area_mm2 = TENSILE_STRESS_AREA[closest]

    proof_mpa = GRADE_DATA[grade]["proof_mpa"]
    k = NUT_FACTOR[condition]
    d_m = diameter_mm / 1000

    preload_n = 0.75 * proof_mpa * 1e6 * (stress_area_mm2 * 1e-6)
    preload_kn = preload_n / 1000

    torque_nm = k * preload_n * d_m
    torque_ftlb = torque_nm * 0.737562

    return BoltTorqueResult(
        grade=grade,
        diameter_mm=diameter_mm,
        condition=condition,
        proof_load_mpa=proof_mpa,
        preload_kn=round(preload_kn, 2),
        torque_nm=round(torque_nm, 1),
        torque_ftlb=round(torque_ftlb, 1),
    )
