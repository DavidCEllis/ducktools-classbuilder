from dataclasses import dataclass
from ducktools.classbuilder.prefab import Prefab

class_register = {}


def register(cls):
    class_register[cls.__name__] = cls
    return cls


# Order is important here
@dataclass(slots=True)
@register
class DataCoords:
    x: float = 0.0
    y: float = 0.0


@register
class SlotCoords(Prefab):
    x: float = 0.0
    y: float = 0.0


print(DataCoords())
print(SlotCoords())

print(f"{DataCoords is class_register[DataCoords.__name__] = }")
print(f"{SlotCoords is class_register[SlotCoords.__name__] = }")
