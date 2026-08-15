"""
Carbon footprint calculation engine.

Provides:
  - Emission factor tables
  - Per-source calculators (Transport, Fuel, Buildings, Trees, …)
  - CarbonFootprint aggregator
  - Pure API helpers for real-time / batch calculation (no I/O)
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union


class InvalidUnitsError(ValueError):
    """Raised when an activity value is missing, non-numeric, or negative."""


# ---------------------------------------------------------------------------
# Emission factors (kg CO₂e per unit of activity)
# ---------------------------------------------------------------------------

TRANSPORT_FACTORS: Dict[str, float] = {
    "car": 0.192,
    "bus": 0.089,
    "motorcycle": 0.135,
    "electric-train": 0.041,
    "thermo-train": 0.093,
    "bicycle": 0.0,
    "other": 0.15,
}

FUEL_FACTORS: Dict[str, float] = {
    "gas": 2.31,
    "petroleum": 2.31,
    "coal": 2.65,
    "charcoal": 1.89,
    "electricity": 0.475,
    "wood": 1.25,
}

# Household / offset (kg CO₂e per count, monthly-ish scale)
BUILDINGS_FACTOR = 15.0
ADULTS_FACTOR = 45.0
LIVESTOCK_FACTOR = 18.0
PETS_FACTOR = 40.0
# Typical tree sequestration ~21 kg/year → monthly
TREES_FACTOR = -21.0 / 12
DIET_FACTOR = 2.5


def list_factors() -> Dict[str, Any]:
    """Return all factor tables for discovery / UI tooltips."""
    return {
        "transport": dict(TRANSPORT_FACTORS),
        "fuel": dict(FUEL_FACTORS),
        "buildings": BUILDINGS_FACTOR,
        "adults": ADULTS_FACTOR,
        "livestock": LIVESTOCK_FACTOR,
        "pets": PETS_FACTOR,
        "trees": TREES_FACTOR,
        "diet": DIET_FACTOR,
        "units": {
            "transport": "kg CO₂e per trip-frequency unit",
            "fuel": "kg CO₂e per currency/expense unit (scaled)",
            "buildings": "kg CO₂e per house",
            "adults": "kg CO₂e per adult",
            "livestock": "kg CO₂e per animal",
            "pets": "kg CO₂e per pet",
            "trees": "kg CO₂e offset per tree (monthly)",
        },
    }


def _clean_units(units: Any) -> float:
    if units is None or units == "":
        raise InvalidUnitsError("A numeric value is required.")
    try:
        value = float(units)
    except (TypeError, ValueError):
        raise InvalidUnitsError(f"'{units}' is not a valid number.")
    if value < 0:
        raise InvalidUnitsError("Value cannot be negative.")
    return value


def _to_number(value: Any, default: float = 0.0) -> float:
    """Lenient parse for API payloads; never raises."""
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Source classes
# ---------------------------------------------------------------------------

class EmissionSource:
    FACTOR: float = 0.0

    def __init__(self, units: Any):
        self.units = _clean_units(units)

    def emission(self) -> float:
        return round(self.units * self.FACTOR, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "units": self.units,
            "factor": self.FACTOR,
            "kg_co2e": self.emission(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(units={self.units}, emission={self.emission()})"


class Electricity(EmissionSource):
    FACTOR = FUEL_FACTORS["electricity"]


class Fuel(EmissionSource):
    FACTOR = FUEL_FACTORS["gas"]


class EnhancedFuel(EmissionSource):
    def __init__(self, units: Any, fuel_type: str = "gas"):
        self.units = _clean_units(units)
        self.fuel_type = fuel_type if fuel_type in FUEL_FACTORS else "gas"
        self.FACTOR = FUEL_FACTORS.get(self.fuel_type, 2.31)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["fuel_type"] = self.fuel_type
        return d

    def __repr__(self) -> str:
        return f"EnhancedFuel(type={self.fuel_type}, units={self.units}, emission={self.emission()})"


class Transport(EmissionSource):
    def __init__(self, units: Any, transport_type: str = "car"):
        self.units = _clean_units(units)
        self.transport_type = transport_type if transport_type in TRANSPORT_FACTORS else "other"
        self.FACTOR = TRANSPORT_FACTORS.get(self.transport_type, 0.15)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["transport_type"] = self.transport_type
        return d

    def __repr__(self) -> str:
        return f"Transport(type={self.transport_type}, units={self.units}, emission={self.emission()})"


class Diet(EmissionSource):
    FACTOR = DIET_FACTOR


class Trees(EmissionSource):
    FACTOR = TREES_FACTOR


class Buildings(EmissionSource):
    FACTOR = BUILDINGS_FACTOR


class Adults(EmissionSource):
    FACTOR = ADULTS_FACTOR


class Livestock(EmissionSource):
    FACTOR = LIVESTOCK_FACTOR


class Pets(EmissionSource):
    FACTOR = PETS_FACTOR


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

class CarbonFootprint:
    def __init__(self) -> None:
        self.sources: list[EmissionSource] = []

    def add(self, source: EmissionSource) -> "CarbonFootprint":
        if not isinstance(source, EmissionSource):
            raise TypeError("add() expects an EmissionSource instance.")
        self.sources.append(source)
        return self

    def total(self) -> float:
        return round(sum(s.emission() for s in self.sources), 4)

    def breakdown(self) -> Dict[str, float]:
        """Sum emissions by class name (e.g. Transport, EnhancedFuel)."""
        out: Dict[str, float] = {}
        for s in self.sources:
            key = s.__class__.__name__
            out[key] = round(out.get(key, 0.0) + s.emission(), 4)
        return out

    def detailed_breakdown(self) -> list[Dict[str, Any]]:
        return [s.to_dict() for s in self.sources]

    def to_result(self, inputs: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        total_kg = self.total()
        return {
            "total_kg_co2e": total_kg,
            "total_t_co2e": round(total_kg / 1000.0, 6),
            "breakdown": self.breakdown(),
            "detailed": self.detailed_breakdown(),
            "inputs": dict(inputs) if inputs else {},
        }


# ---------------------------------------------------------------------------
# Real-time / batch calculation API (pure functions — no DB, no Flask)
# ---------------------------------------------------------------------------

def normalize_inputs(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Normalize form or JSON body into typed inputs.

    Accepts keys used by the home form and flexible aliases:
      transport | transport_type
      frequency | frequency_custom (if frequency == 'multiple')
      fuel | fuel_type
      energy_expense | energy
      house_no | houses
      trees, adults, livestock, pets
    """
    transport_type = (
        payload.get("transport")
        or payload.get("transport_type")
        or "other"
    )
    if transport_type not in TRANSPORT_FACTORS:
        transport_type = "other"

    frequency_raw = payload.get("frequency")
    if frequency_raw == "multiple" or str(frequency_raw).lower() == "multiple":
        frequency = _to_number(
            payload.get("frequency_custom") or payload.get("times_per_week"),
            default=1.0,
        )
    else:
        frequency = _to_number(frequency_raw, default=1.0)
    if frequency <= 0:
        frequency = 1.0

    fuel_type = payload.get("fuel") or payload.get("fuel_type") or "electricity"
    if fuel_type not in FUEL_FACTORS:
        fuel_type = "electricity"

    return {
        "transport": transport_type,
        "frequency": frequency,
        "fuel": fuel_type,
        "energy_expense": _to_number(
            payload.get("energy_expense") or payload.get("energy"), default=0.0
        ),
        "house_no": _to_number(
            payload.get("house_no") or payload.get("houses"), default=0.0
        ),
        "trees": _to_number(payload.get("trees"), default=0.0),
        "adults": _to_number(payload.get("adults"), default=0.0),
        "livestock": _to_number(payload.get("livestock"), default=0.0),
        "pets": _to_number(payload.get("pets"), default=0.0),
    }


def build_footprint(inputs: Mapping[str, Any]) -> CarbonFootprint:
    """Build a CarbonFootprint from normalized inputs. Raises InvalidUnitsError."""
    calc = CarbonFootprint()
    calc.add(Transport(inputs["frequency"], transport_type=inputs["transport"]))

    if inputs["energy_expense"] > 0:
        calc.add(EnhancedFuel(inputs["energy_expense"], fuel_type=inputs["fuel"]))
    if inputs["house_no"] > 0:
        calc.add(Buildings(inputs["house_no"]))
    if inputs["trees"] > 0:
        calc.add(Trees(inputs["trees"]))
    if inputs["adults"] > 0:
        calc.add(Adults(inputs["adults"]))
    if inputs["livestock"] > 0:
        calc.add(Livestock(inputs["livestock"]))
    if inputs["pets"] > 0:
        calc.add(Pets(inputs["pets"]))
    return calc


def calculate_from_inputs(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Real-time calculation entry point.

    Parameters
    ----------
    payload : mapping
        Raw form fields or JSON body.

    Returns
    -------
    dict
        {
          "total_kg_co2e": float,
          "total_t_co2e": float,
          "breakdown": { "Transport": ..., "EnhancedFuel": ..., ... },
          "detailed": [ { type, units, factor, kg_co2e, ... }, ... ],
          "inputs": { normalized inputs },
        }

    Raises
    ------
    InvalidUnitsError
        If a required numeric field is invalid.
    """
    inputs = normalize_inputs(payload)
    calc = build_footprint(inputs)
    return calc.to_result(inputs)


def calculate_single(
    source: str,
    units: Union[int, float, str],
    *,
    transport_type: str = "car",
    fuel_type: str = "gas",
) -> Dict[str, Any]:
    """
    Calculate a single emission source (useful for live field previews).

    source: transport | fuel | electricity | buildings | adults |
            livestock | pets | trees | diet
    """
    key = (source or "").strip().lower()
    mapping = {
        "transport": lambda: Transport(units, transport_type=transport_type),
        "fuel": lambda: EnhancedFuel(units, fuel_type=fuel_type),
        "electricity": lambda: Electricity(units),
        "buildings": lambda: Buildings(units),
        "adults": lambda: Adults(units),
        "livestock": lambda: Livestock(units),
        "pets": lambda: Pets(units),
        "trees": lambda: Trees(units),
        "diet": lambda: Diet(units),
    }
    if key not in mapping:
        raise InvalidUnitsError(
            f"Unknown source '{source}'. "
            f"Valid: {', '.join(sorted(mapping))}."
        )
    item = mapping[key]()
    return item.to_dict()
