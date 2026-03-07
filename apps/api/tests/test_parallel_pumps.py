import pytest
from app.services.parallel_pumps import (
    PumpCurvePoint,
    SystemCurve,
    PumpInput,
    ParallelPumpsResult,
    calculate_parallel_pumps,
)


def test_single_pump_finds_operating_point():
    """Single pump on a system curve finds the correct operating point."""
    pump = PumpInput(
        name="Pump A",
        points=[
            PumpCurvePoint(q=0, h=50),
            PumpCurvePoint(q=10, h=45),
            PumpCurvePoint(q=20, h=35),
            PumpCurvePoint(q=30, h=20),
        ],
        bep_q=18.0,
    )
    system = SystemCurve(static_head=5.0, resistance=0.04)
    result = calculate_parallel_pumps(pumps=[pump], system=system)
    # H_sys = 5 + 0.04*Q^2, pump curve intersects around Q=20, H=21
    assert result.operating_point.h > 5
    assert result.operating_point.q_total > 0
    assert len(result.pumps) == 1
    assert result.pumps[0].q > 0


def test_two_identical_pumps_double_flow():
    """Two identical pumps in parallel should roughly double the flow vs single pump."""
    points = [
        PumpCurvePoint(q=0, h=50),
        PumpCurvePoint(q=10, h=45),
        PumpCurvePoint(q=20, h=35),
        PumpCurvePoint(q=30, h=20),
    ]
    pump_a = PumpInput(name="Pump A", points=points, bep_q=18.0)
    pump_b = PumpInput(name="Pump B", points=points, bep_q=18.0)
    system = SystemCurve(static_head=5.0, resistance=0.01)

    single = calculate_parallel_pumps(pumps=[pump_a], system=system)
    double = calculate_parallel_pumps(pumps=[pump_a, pump_b], system=system)

    # Two identical pumps should produce roughly 2x flow (not exactly due to system curve shape)
    assert double.operating_point.q_total > single.operating_point.q_total * 1.5


def test_dominated_pump_flagged_as_off_curve():
    """Pump operating far outside BEP should be flagged as off_curve."""
    # Strong pump: high shutoff, steep drop — will dominate system at high H
    strong_pump = PumpInput(
        name="Strong",
        points=[
            PumpCurvePoint(q=0, h=80),
            PumpCurvePoint(q=15, h=65),
            PumpCurvePoint(q=30, h=40),
        ],
        bep_q=25.0,
    )
    # Weak pump: low shutoff, bep_q=2 so at operating point Q >> bep_q -> off_curve
    weak_pump = PumpInput(
        name="Weak",
        points=[
            PumpCurvePoint(q=0, h=50),
            PumpCurvePoint(q=10, h=42),
            PumpCurvePoint(q=20, h=28),
        ],
        bep_q=2.0,  # very low BEP so ratio will be >> 1.2
    )
    system = SystemCurve(static_head=5.0, resistance=0.02)
    result = calculate_parallel_pumps(pumps=[strong_pump, weak_pump], system=system)

    pump_results = {p.name: p for p in result.pumps}
    assert "Weak" in pump_results
    assert pump_results["Weak"].alert == "off_curve"


def test_zero_contribution_pump_alert():
    """Pump whose shutoff head is below the operating head contributes Q=0."""
    # Strong pump: high shutoff, will push system H above weak pump's h_max
    strong_pump = PumpInput(
        name="Strong",
        points=[
            PumpCurvePoint(q=0, h=100),
            PumpCurvePoint(q=20, h=80),
            PumpCurvePoint(q=40, h=50),
        ],
        bep_q=30.0,
    )
    # Weak pump: max head only 20m — at operating H it returns Q=0
    weak_pump = PumpInput(
        name="Weak",
        points=[
            PumpCurvePoint(q=0, h=20),
            PumpCurvePoint(q=5, h=15),
            PumpCurvePoint(q=10, h=8),
        ],
        bep_q=5.0,
    )
    system = SystemCurve(static_head=5.0, resistance=0.01)
    result = calculate_parallel_pumps(pumps=[strong_pump, weak_pump], system=system)

    pump_results = {p.name: p for p in result.pumps}
    # Operating H will be >> 20m, so Weak pump Q=0 -> bep_ratio=0 -> off_curve
    assert "Weak" in pump_results
    assert pump_results["Weak"].alert in ("off_curve", "reverse_flow")


def test_input_validation_too_few_points():
    """Pump with fewer than 3 points should raise ValueError."""
    pump = PumpInput(
        name="Short",
        points=[
            PumpCurvePoint(q=0, h=50),
            PumpCurvePoint(q=10, h=40),
        ],
    )
    system = SystemCurve(static_head=5.0, resistance=0.02)
    with pytest.raises(ValueError, match="at least 3"):
        calculate_parallel_pumps(pumps=[pump], system=system)


def test_input_validation_negative_q():
    """Pump with negative Q values should raise ValueError."""
    pump = PumpInput(
        name="BadPump",
        points=[
            PumpCurvePoint(q=-5, h=60),
            PumpCurvePoint(q=10, h=45),
            PumpCurvePoint(q=20, h=30),
        ],
    )
    system = SystemCurve(static_head=5.0, resistance=0.02)
    with pytest.raises(ValueError, match="non-negative"):
        calculate_parallel_pumps(pumps=[pump], system=system)


def test_no_intersection_raises_value_error():
    """System curve above max pump head should raise ValueError."""
    pump = PumpInput(
        name="Pump A",
        points=[
            PumpCurvePoint(q=0, h=20),
            PumpCurvePoint(q=10, h=15),
            PumpCurvePoint(q=20, h=5),
        ],
        bep_q=10.0,
    )
    system = SystemCurve(static_head=50.0, resistance=0.01)  # way above pump max head
    with pytest.raises(ValueError, match="no_intersection"):
        calculate_parallel_pumps(pumps=[pump], system=system)


def test_combined_curve_points_returned():
    """Result includes combined curve points for charting."""
    points = [
        PumpCurvePoint(q=0, h=40),
        PumpCurvePoint(q=10, h=35),
        PumpCurvePoint(q=20, h=25),
        PumpCurvePoint(q=30, h=10),
    ]
    pump_a = PumpInput(name="A", points=points, bep_q=15.0)
    pump_b = PumpInput(name="B", points=points, bep_q=15.0)
    system = SystemCurve(static_head=5.0, resistance=0.02)
    result = calculate_parallel_pumps(pumps=[pump_a, pump_b], system=system)
    assert len(result.combined_curve_points) > 5
    assert len(result.system_curve_points) > 5


def test_input_validation_duplicate_q():
    """Duplicate Q values should raise ValueError."""
    with pytest.raises(ValueError, match="duplicate Q"):
        calculate_parallel_pumps(
            pumps=[PumpInput(
                name="Dup",
                points=[
                    PumpCurvePoint(q=0, h=50),
                    PumpCurvePoint(q=10, h=40),
                    PumpCurvePoint(q=10, h=30),  # duplicate Q=10
                ],
                bep_q=10.0,
            )],
            system=SystemCurve(static_head=5.0, resistance=0.04),
        )


def test_input_validation_non_monotone_curve():
    """Non-monotonically decreasing H-Q curve should raise ValueError."""
    with pytest.raises(ValueError, match="monotonically decreasing"):
        calculate_parallel_pumps(
            pumps=[PumpInput(
                name="Hump",
                points=[
                    PumpCurvePoint(q=0, h=40),
                    PumpCurvePoint(q=10, h=50),  # H increases — invalid
                    PumpCurvePoint(q=20, h=30),
                ],
                bep_q=10.0,
            )],
            system=SystemCurve(static_head=5.0, resistance=0.04),
        )
