class InvalidUnitsError(ValueError):
    pass    
TRANSPORT_FACTORS = {
    "car": 0.192,
    "bus": 0.089,
    "motorcycle": 0.135,
    "electric-train": 0.041,
    "thermo-train": 0.093,
    "bicycle": 0.0,
    "other": 0.15,  # Average fallback
}


FUEL_FACTORS = {
    "gas": 2.31,
    "petroleum": 2.31,
    "coal": 2.65,
    "charcoal": 1.89,
    "electricity": 0.475,
    "wood": 1.25,
}

def _clean_units(units):
    if units is None or units == "":
        raise InvalidUnitsError("A numeric value is required.")
    try:
        value = float(units)
    except (TypeError, ValueError):
        raise InvalidUnitsError(f"'{units}' is not a valid number.")
    if value < 0:
        raise InvalidUnitsError("Value cannot be negative.")
    return value


class EmissionSource:
    FACTOR = 0.0
    def __init__(self, units):
        self.units = _clean_units(units)

    def emission(self):
        return round(self.units * self.FACTOR, 4)

    def __repr__(self):
        return f"{self.__class__.__name__}(units={self.units}, emission={self.emission()})"


class Electricity(EmissionSource):
    FACTOR = 0.475


class Fuel(EmissionSource):
    FACTOR = 2.31  


class EnhancedFuel(EmissionSource):
    """Fuel class that differentiates between fuel types"""
    def __init__(self, units, fuel_type="gas"):
        self.units = _clean_units(units)
        self.fuel_type = fuel_type
        self.FACTOR = FUEL_FACTORS.get(fuel_type, 2.31)
    
    def __repr__(self):
        return f"Fuel(type={self.fuel_type}, units={self.units}, emission={self.emission()})"


class Transport(EmissionSource):
    """Transport class that differentiates between transport types"""
    def __init__(self, units, transport_type="car"):
        self.units = _clean_units(units)
        self.transport_type = transport_type
        self.FACTOR = TRANSPORT_FACTORS.get(transport_type, 0.15)
    
    def __repr__(self):
        return f"Transport(type={self.transport_type}, units={self.units}, emission={self.emission()})"


class Diet(EmissionSource):
    FACTOR = 2.5


class Trees(EmissionSource):
    FACTOR = -21.0/12
    

class Buildings(EmissionSource):
    FACTOR = 15.0 


class CarbonFootprint:
    def __init__(self):
        self.sources = []

    def add(self, source: EmissionSource):
        if not isinstance(source, EmissionSource):
            raise TypeError("add() expects an EmissionSource instance.")
        self.sources.append(source)
        return self

    def total(self):
        return round(sum(s.emission() for s in self.sources), 4)

    def breakdown(self):
        return {s.__class__.__name__: s.emission() for s in self.sources}
