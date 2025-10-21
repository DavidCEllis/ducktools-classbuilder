# Bare forwardrefs only work in 3.14 or later

from ducktools.classbuilder.annotations import get_ns_annotations, get_func_annotations

import pathlib

from typing import Annotated, ClassVar


global_type = int


def test_bare_forwardref():
    class Ex:
        a: str
        b: pathlib.Path
        c: plain_forwardref

    annos = get_ns_annotations(Ex.__dict__)

    assert annos == {
        'a': "str",
        'b': "pathlib.Path",
        'c': "plain_forwardref",
    }


def test_inner_outer_ref():
    # If types can't be evaluated - all are given as strings
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

    assert annos['a_val'] == "inner_type"
    assert annos['b_val'] == "global_type"
    assert annos['c_val'] == "hyper_type"


def test_inner_outer_ref_resolved():
    # If types can be resolved - they are resolved
    def make_func():
        inner_type = str

        class Inner:
            a_val: inner_type = "hello"
            b_val: global_type = 42
            c_val: hyper_type = 3.14

        hyper_type = float

        annos = get_ns_annotations(Inner.__dict__)

        return annos

    annos = make_func()

    assert annos['a_val'] == str
    assert annos['b_val'] == int
    assert annos['c_val'] == float



def test_func_annotations():
    def forwardref_func(x: unknown) -> str:
        return ''

    annos = get_func_annotations(forwardref_func)
    assert annos == {
        'x': "unknown",
        'return': "str",
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
        'a': str,
        'b': "str",
        'c': list[str],
        'd': "list[str]",
        'e': ClassVar[str],
        'f': "ClassVar[str]",
        'g': "ClassVar[forwardref]",
        'h': "Annotated[ClassVar[str], '']",
        'i': "Annotated[ClassVar[forwardref], '']",
        'j': "CV[str]",
    }

