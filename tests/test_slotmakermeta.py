from typing import ClassVar, List
from typing_extensions import Annotated
from ducktools.classbuilder import Field, SlotFields, NOTHING, SlotMakerMeta

import pytest


def test_slots_created():
    class ExampleAnnotated(metaclass=SlotMakerMeta):
        a: str = "a"
        b: "List[str]" = "b"  # Yes this is the wrong type, I know.
        c: Annotated[str, ""] = "c"

        d: ClassVar[str] = "d"
        e: Annotated[ClassVar[str], ""] = "e"
        f: "Annotated[ClassVar[str], '']" = "f"
        g: Annotated[Annotated[ClassVar[str], ""], ""] = "g"

    assert hasattr(ExampleAnnotated, "__slots__")

    slots = ExampleAnnotated.__slots__  # noqa
    expected_slots = SlotFields({
        "a": Field(default="a", type=str),
        "b": Field(default="b", type=List[str]),
        "c": Field(default="c", type=Annotated[str, ""])
    })

    assert slots == expected_slots


def test_slots_correct_subclass():
    class ExampleBase(metaclass=SlotMakerMeta):
        a: str
        b: str = "b"
        c: str = "c"

    class ExampleChild(ExampleBase):
        d: str = "d"

    assert ExampleBase.__slots__ == SlotFields(    # noqa
        a=Field(type=str),
        b=Field(default="b", type=str),
        c=Field(default="c", type=str),
    )
    assert ExampleChild.__slots__ == SlotFields(d=Field(default="d", type=str))  # noqa

    inst = ExampleChild()

    inst.a = "a"
    inst.b = "b"
    inst.c = "c"
    inst.d = "d"

    with pytest.raises(AttributeError):
        inst.e = "e"


def test_slots_attribute():
    # In the case where an unannotated field is declared, ignore
    # annotations without field values.
    class ExampleBase(metaclass=SlotMakerMeta):
        x: str = "x"
        y: str = Field(default="y")
        z = Field(default="z")

    assert ExampleBase.__slots__ == SlotFields(  # noqa
        y=Field(default="y", type=str),
        z=Field(default="z"),
    )
