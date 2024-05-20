from typing import ClassVar, Annotated
from ducktools.classbuilder import SlotMakerMeta, SlotFields, NOTHING

import pytest


def test_slots_created():
    class ExampleAnnotated(metaclass=SlotMakerMeta):
        a: str = "a"
        b: "list[str]" = "b"  # Yes this is the wrong type, I know.
        c: Annotated[str, ""] = "c"

        d: ClassVar[str] = "d"
        e: Annotated[ClassVar[str], ""] = "e"
        f: "Annotated[ClassVar[str], '']" = "f"
        g: Annotated[Annotated[ClassVar[str], ""], ""] = "g"

    assert hasattr(ExampleAnnotated, "__slots__")

    slots = ExampleAnnotated.__slots__  # noqa
    assert slots == SlotFields({char: char for char in "abc"})


def test_slots_correct_subclass():
    class ExampleBase(metaclass=SlotMakerMeta):
        a: str
        b: str = "b"
        c: str = "c"

    class ExampleChild(ExampleBase):
        d: str = "d"

    assert ExampleBase.__slots__ == SlotFields(a=NOTHING, b="b", c="c")  # noqa
    assert ExampleChild.__slots__ == SlotFields(d="d")  # noqa

    inst = ExampleChild()

    inst.a = "a"
    inst.b = "b"
    inst.c = "c"
    inst.d = "d"

    with pytest.raises(AttributeError):
        inst.e = "e"
