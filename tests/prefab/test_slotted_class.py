import pytest

from ducktools.classbuilder.annotations import get_ns_annotations
from ducktools.classbuilder.prefab import prefab, attribute, SlotFields

import pytest

from utils import graalpy_fails  # type: ignore


@graalpy_fails
def test_basic_slotted():
    @prefab
    class SlottedPrefab:
        __slots__ = SlotFields(
            x=42,
            y=attribute(default=3.14, type=float, doc="Digits of pi"),
        )

    assert SlottedPrefab.__slots__ == {"x": None, "y": "Digits of pi"}

    ex = SlottedPrefab()

    assert ex.x == 42
    assert ex.y == 3.14


@graalpy_fails
def test_class_unchanged():
    # By using slots to define the class prefab_classes does not need to create
    # a new class.
    # Dataclasses and Attrs require recreating a class and would fail this test
    # with their method of slots.
    cache = {}

    def save_class(cls):
        cache[cls.__name__] = cls
        return cls

    @prefab
    @save_class
    class Slotted:
        __slots__ = SlotFields(x="example_data")

    assert Slotted is cache["Slotted"]

    ex = Slotted(x="new example data")

    assert ex.x == "new example data"


@graalpy_fails
def test_actually_slotted():
    @prefab
    class Slotted:
        __slots__ = SlotFields(x=attribute(default="example_data"))
        x: str

    inst = Slotted()

    with pytest.raises(AttributeError):
        inst.y = "This Doesn't Work!"

    @prefab
    class UnSlotted:
        x: str = "example_data"

    inst = UnSlotted()
    inst.x = "This Works!"


@graalpy_fails
def test_slotted_inheritance():
    # This is an example that didn't work in attrs/dataclasses
    # https://github.com/python/cpython/issues/90562
    # Prefabs don't replace the class so this still works

    @prefab
    class A:
        __slots__ = SlotFields(break_graal=False)

        def test(self):
            return type(self)

    @prefab
    class B(A):
        def test(self):
            return super().test()

    assert B().test() is B

    # Additional tests to prove slottedness of base class
    ex = A(break_graal=True)
    with pytest.raises(AttributeError):
        ex.attrib = True

    # As a subclass, B now has a dict and this should work
    exb = B()
    exb.attrib = True


@graalpy_fails
def test_slotted_frozen():
    @prefab(frozen=True)
    class A:
        __slots__ = SlotFields(x=attribute())

    ex = A("test")

    with pytest.raises(TypeError):
        ex.x = "Can't set attributes on frozen instance"

    with pytest.raises(TypeError):
        ex.y = "Can't set attributes on frozen instance"

    assert ex.x == "test"
