from dataclasses import dataclass
from ducktools.classbuilder import slotclass, SlotFields

class_register = {}


def register(cls):
    class_register[cls.__name__] = cls
    return cls


@dataclass(slots=True)
@register
class DataCoords:
    x: float = 0.0
    y: float = 0.0


@slotclass
@register
class SlotCoords:
    __slots__ = SlotFields(x=0.0, y=0.0)
    # Type hints don't affect class construction, these are optional.
    x: float
    y: float


print(DataCoords())
print(SlotCoords())

print(f"{DataCoords is class_register[DataCoords.__name__] = }")
print(f"{SlotCoords is class_register[SlotCoords.__name__] = }")
