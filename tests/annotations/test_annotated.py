# This module commits intentional typing related crimes, ignore any errors
# type: ignore

"""
Tests to check that typing.Annotated
does not interfere when wrapping ClassVar
"""

import sys

from typing import Annotated, ClassVar

from ducktools.classbuilder import (
    Field, SlotFields, NOTHING,
    annotation_gatherer, make_annotation_gatherer
)

from ducktools.classbuilder.annotations import (
    is_classvar,
    get_ns_annotations,
)

CV = ClassVar


def test_is_classvar():
    icv = is_classvar

    assert icv(ClassVar)
    assert icv(ClassVar[str])

    # 3.10 and earlier do not support plain typing.ClassVar in Annotated
    if sys.version_info >= (3, 11):
        assert icv(Annotated[ClassVar, ""])

    assert icv(Annotated[ClassVar[str], ""])

    assert not icv(str)
    assert not icv(Annotated[str, "..."])


def test_annotation_gatherer():
    class ExampleAnnotated:
        a: str = "a"
        b: "list[str]" = "b"
        c: Annotated[str, ""] = Field(default="c")

        d: ClassVar[str] = "d"
        e: Annotated[ClassVar[str], ""] = "e"
        f: "Annotated[ClassVar[str], '']" = "f"
        g: Annotated[Annotated[ClassVar[str], ""], ""] = "g"
        h: Annotated[CV[str], ''] = "h"

    annos, modifications = annotation_gatherer(ExampleAnnotated)

    # ClassVar values ignored in gathering
    # Instance variables removed from class
    for key in "abc":
        assert key in annos

    for key in "defgh":
        assert key not in annos

    # Instance variables to be removed from class
    assert modifications["a"] is NOTHING
    assert modifications["b"] is NOTHING
    assert modifications["c"] is NOTHING


def test_make_annotation_gatherer():
    class NewField(Field):
        __slots__ = SlotFields(newval=False)

    gatherer = make_annotation_gatherer(
        field_type=NewField,
        leave_default_values=True,
    )

    class ExampleAnnotated:
        blank_field: str
        a: str = "a"
        b: "list[str]" = "b"
        c: Annotated[str, ""] = NewField(default="c")

        d: ClassVar[str] = "d"
        e: Annotated[ClassVar[str], ""] = "e"
        f: "Annotated[ClassVar[str], '']" = "f"
        g: Annotated[Annotated[ClassVar[str], ""], ""] = "g"
        h: Annotated[CV[str], ''] = "h"

    annos, modifications = gatherer(ExampleAnnotated)
    annotations = get_ns_annotations(vars(ExampleAnnotated))

    assert annos["blank_field"] == NewField(type=str)

    # ABC should be present in annos and in the class
    for key in "abc":
        assert annos[key] == NewField(default=key, type=annotations[key])

    assert modifications["c"] == "c"

    # Opposite for classvar
    for key in "defgh":
        assert key not in annos
        assert key not in modifications
