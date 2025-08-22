# Bare forwardrefs only work in 3.14 or later

from ducktools.classbuilder.annotations import get_ns_annotations, get_func_annotations

from pathlib import Path
from typing import Annotated, ClassVar

from _test_support import EqualToForwardRef, SimpleEqualToForwardRef

global_type = int


def test_bare_forwardref():
    class Ex:
        a: str
        b: Path
        c: plain_forwardref

    annos = get_ns_annotations(Ex.__dict__)

    assert annos == {'a': str, 'b': Path, 'c': EqualToForwardRef("plain_forwardref")}


def test_inner_outer_ref():

    def make_func():
        inner_type = str

        class Inner:
            a_val: inner_type = "hello"
            b_val: global_type = 42
            c_val: hyper_type = 3.14

        # Try to get annotations before hyper_type exists
        annos = get_ns_annotations(Inner.__dict__)

        hyper_type = float

        return Inner, annos

    cls, annos = make_func()

    # Forwardref given as string if used before it can be evaluated
    assert annos == {"a_val": str, "b_val": int, "c_val": EqualToForwardRef("hyper_type")}

    # Correctly evaluated if it exists
    assert get_ns_annotations(cls.__dict__) == {
        "a_val": str, "b_val": int, "c_val": float
    }


def test_func_annotations():
    def forwardref_func(x: unknown) -> str:
        return ''

    annos = get_func_annotations(forwardref_func)
    assert annos == {
        'x': EqualToForwardRef("unknown", owner=forwardref_func),
        'return': str
    }


def test_ns_annotations():
    # The 3.14 annotations version of test_ns_annotations
    CV = ClassVar

    class AnnotatedClass:
        a: str
        b: "str"
        c: list[str]
        d: "list[str]"
        e: ClassVar[str]
        f: "ClassVar[str]"
        g: "ClassVar[forwardref]"
        h: "Annotated[ClassVar[str], '']"
        i: "Annotated[ClassVar[forwardref], '']"
        j: "CV[str]"

    annos = get_ns_annotations(vars(AnnotatedClass))

    assert annos == {
        'a': SimpleEqualToForwardRef("str"),
        'b': "str",
        'c': SimpleEqualToForwardRef("list[str]"),
        'd': "list[str]",
        'e': SimpleEqualToForwardRef("ClassVar[str]"),
        'f': "ClassVar[str]",
        'g': "ClassVar[forwardref]",
        'h': "Annotated[ClassVar[str], '']",
        'i': "Annotated[ClassVar[forwardref], '']",
        'j': "CV[str]",
    }

