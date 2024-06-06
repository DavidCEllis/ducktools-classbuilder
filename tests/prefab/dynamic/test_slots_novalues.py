import pytest
from ducktools.classbuilder.prefab import prefab


def test_existing_slots():
    @prefab
    class SlotPrefab:
        __slots__ = ("x", "y")
        x: int
        y: str

    sp = SlotPrefab(1, "demo")
    sp2 = SlotPrefab(1, "demo")
    assert sp.x == 1
    assert sp.y == "demo"

    assert sp == sp2
