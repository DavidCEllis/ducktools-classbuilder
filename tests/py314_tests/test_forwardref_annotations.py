# Bare forwardrefs only work in 3.14 or later

from ducktools.classbuilder.annotations import get_ns_annotations, get_func_annotations, evaluate_forwardref

import pathlib

from typing import Annotated, ClassVar

from _test_support import EqualToForwardRef, SimpleEqualToForwardRef
from _type_support import matches_type

global_type = int


def test_bare_forwardref():
    class Ex:
        a: str
        b: pathlib.Path
        c: plain_forwardref

    annos = get_ns_annotations(Ex.__dict__)

    assert annos == {
        'a': matches_type(str),
        'b': matches_type(pathlib.Path),
        'c': matches_type("plain_forwardref")
    }


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

        return annos

    annos = make_func()

    # Confirm the annotations all evaluate
    assert evaluate_forwardref(annos['a_val']) == str
    assert evaluate_forwardref(annos["b_val"]) == int
    assert evaluate_forwardref(annos["c_val"]) == float


def test_func_annotations():
    def forwardref_func(x: unknown) -> str:
        return ''

    annos = get_func_annotations(forwardref_func)
    assert annos == {
        'x': EqualToForwardRef("unknown", owner=forwardref_func),
        'return': matches_type(str),
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

