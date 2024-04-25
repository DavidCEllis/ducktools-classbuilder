import sys
import pytest

from typing import ClassVar
from typing_extensions import Annotated

from ducktools.classbuilder import Field, SlotFields, fieldclass

from ducktools.classbuilder import (
    is_classvar,
    annotationclass,
    annotation_gatherer,
    make_annotation_gatherer,
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

    annos = annotation_gatherer(ExampleAnnotated)

    # ClassVar values ignored in gathering
    # Instance variables removed from class
    for key in "abc":
        assert key in annos

    for key in "defgh":
        assert key not in annos

    # Instance variables not removed from class
    # Field replaced with default value on class
    for key in "abcdefgh":
        assert ExampleAnnotated.__dict__[key] == key


def test_make_annotation_gatherer():
    @fieldclass
    class NewField(Field):
        __slots__ = SlotFields(newval=False)

    gatherer = make_annotation_gatherer(
        field_type=NewField,
        leave_default_values=False,
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

    annos = gatherer(ExampleAnnotated)
    annotations = ExampleAnnotated.__annotations__

    assert annos["blank_field"] == NewField(type=str)

    # ClassVar values ignored in gathering
    for key in "abc":
        assert annos[key] == NewField(default=key, type=annotations[key])
        assert key not in ExampleAnnotated.__dict__

    for key in "defgh":
        assert key not in annos

    # Instance variables not removed from class
    # NewField replaced with default value on class
    for key in "defgh":
        assert ExampleAnnotated.__dict__[key] == key


def test_annotationclass():
    @annotationclass()
    class ExampleAnnotated:
        a: str = "a"
        b: "list[str]" = "b"
        c: Annotated[str, ""] = Field(default="c")

        d: ClassVar[str] = "d"
        e: Annotated[ClassVar[str], ""] = "e"
        f: "Annotated[ClassVar[str], '']" = "f"
        g: Annotated[Annotated[ClassVar[str], ""], ""] = "g"
        h: Annotated[CV[str], ''] = "h"

    for key in "abcdefgh":
        assert key in ExampleAnnotated.__dict__

    ex = ExampleAnnotated()
    for char in "abcdefgh":
        assert getattr(ex, char) == char

    ex2 = ExampleAnnotated()
    ex3 = ExampleAnnotated("i", "j", "k")

    assert ex == ex2
    assert ex != ex3

    prefix = "test_annotationclass.<locals>."
    assert repr(ex) == f"{prefix}ExampleAnnotated(a='a', b='b', c='c')"


def test_annotated_syntax_error():
    with pytest.raises(SyntaxError):
        @annotationclass
        class ExampleAnnotated:
            a: str = "a"
            b: "list[str]"
            c: Annotated[str, ""] = Field(default="c")
