from libs import physics_lib


class Quantity:
    def __init__(self, name, amount=0):
        self.name = name
        self.amount = amount

    @property
    def units(self) -> dict:
        return units[self.name]

    def get_in(self, unit_name):
        return self.amount / self.units[unit_name][1]

    def set_in(self, unit_name, value):
        self.amount = value * self.units[unit_name][1]

    def add_in(self, unit_name, value):
        self.amount += value * self.units[unit_name][1]

    def repr_in(self, unit_name):
        return f"{self.get_in(unit_name)} {self.units[unit_name][0]}"

    def __add__(self, other):
        if self.name != other.name:
            raise TypeError(f"Tried to add {other.name} to {self.name}.")

        return Quantity(self.name, self.amount + other.amount)

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        return Quantity(self.name, self.amount * other)

    def __truediv__(self, other):
        return self * (1 / other)

    def __neg__(self):
        return Quantity(self.name, self.amount)


units = {
    "length": {
        "pixel": ("px", 1),
        "ru": ("ru", physics_lib.rn)
    },
    "force": {
        "rewton": ("R", 1),
        "gauss": ("G", physics_lib.cf)
    },
    "energy": {
        "tsei": ("T", 1),
        "revion": ("R", physics_lib.cp)
    }
}


def get_limit_distance(bond):
    return Quantity("length", physics_lib.limit_distance_pixel(bond))


def get_perfect_distance(bond):
    return Quantity("length", physics_lib.perfect_distance_pixel(bond))


def get_min_potential(bond):
    return Quantity("energy", physics_lib.resting_potential(bond))
