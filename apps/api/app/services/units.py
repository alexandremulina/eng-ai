from pint import UnitRegistry, DimensionalityError, UndefinedUnitError

ureg = UnitRegistry()

class ConversionError(Exception):
    pass


# Map friendly aliases to pint units
UNIT_MAP = {
    "gpm": "gallon / minute",
    "m3/h": "meter**3 / hour",
    "m3/s": "meter**3 / second",
    "l/s": "liter / second",
    "psi": "pound_force_per_square_inch",
    "bar": "bar",
    "kPa": "kilopascal",
    "MPa": "megapascal",
    "kgf/cm2": "kilogram_force / centimeter**2",
    "degC": "degC",
    "degF": "degF",
    "K": "kelvin",
    "m": "meter",
    "mm": "millimeter",
    "inch": "inch",
    "ft": "foot",
    "kg/m3": "kilogram / meter**3",
    "mPa*s": "millipascal * second",
    "cP": "centipoise",
    "kW": "kilowatt",
    "hp": "horsepower",
    "rpm": "revolution / minute",
}


def convert_unit(value: float, from_unit: str, to_unit: str, decimals: int = 6) -> float:
    """Convert value between engineering units with pint precision."""
    try:
        from_pint = UNIT_MAP.get(from_unit, from_unit)
        to_pint = UNIT_MAP.get(to_unit, to_unit)
        quantity = ureg.Quantity(value, from_pint)
        converted = quantity.to(to_pint).magnitude
        return round(float(converted), decimals)
    except DimensionalityError as e:
        raise ConversionError(f"Cannot convert {from_unit} to {to_unit}: incompatible dimensions") from e
    except UndefinedUnitError as e:
        raise ConversionError(f"Unknown unit: {e}") from e
    except Exception as e:
        raise ConversionError(f"Conversion error: {e}") from e
