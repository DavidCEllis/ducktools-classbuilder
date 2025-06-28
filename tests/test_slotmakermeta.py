from typing import Annotated, ClassVar, List

from ducktools.classbuilder import Field, SlotFields, NOTHING, SlotMakerMeta, GATHERED_DATA

import pytest

from utils import graalpy_fails  # type: ignore


@graalpy_fails
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
    expected_slots = {"a": None, "b": None, "c": None}

    assert slots == expected_slots

    expected_fields = {
        "a": Field(default="a", type=str), 
        "b": Field(default="b", type="List[str]"), 
        "c": Field(default="c", type=Annotated[str, ""]),
    }

    fields, modifications = getattr(ExampleAnnotated, GATHERED_DATA)

    assert fields == expected_fields
    assert modifications == {}


@graalpy_fails
def test_slots_correct_subclass():
    class ExampleBase(metaclass=SlotMakerMeta):
        a: str
        b: str = "b"
        c: str = "c"

    class ExampleChild(ExampleBase):
        d: str = "d"

    assert ExampleBase.__slots__ == {"a": None, "b": None, "c": None}
    assert ExampleChild.__slots__ == {"d": None}

    inst = ExampleChild()

    inst.a = "a"
    inst.b = "b"
    inst.c = "c"
    inst.d = "d"

    with pytest.raises(AttributeError):
        inst.e = "e"


@graalpy_fails
def test_slots_attribute():
    # In the case where an unannotated field is declared, ignore
    # annotations without field values.
    class ExampleBase(metaclass=SlotMakerMeta):
        x: str = "x"
        y: str = Field(default="y")
        z = Field(default="z")

    assert ExampleBase.__slots__ == {"y": None, "z": None}


@graalpy_fails
def test_made_doc():
    class ExampleBase(metaclass=SlotMakerMeta):
        x: str = Field(doc="Test")

    assert ExampleBase.__slots__ == {"x": "Test"}
