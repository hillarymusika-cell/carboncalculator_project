class InvalidUnitsError(ValueError):
    pass    
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
