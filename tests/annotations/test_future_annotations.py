# This module commits intentional typing related crimes, ignore any errors
# type: ignore

from __future__ import annotations

from ducktools.classbuilder.annotations import get_ns_annotations

from pathlib import Path

global_type = int

def test_bare_forwardref():
    class Ex:
        a: str
        b: Path
        c: plain_forwardref

    annos = get_ns_annotations(Ex.__dict__)

    assert annos == {'a': "str", 'b': "Path", 'c': "plain_forwardref"}


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

    # Only global types can be evaluated
    assert annos == {"a_val": "inner_type", "b_val": "global_type", "c_val": "hyper_type"}

    # No extra evaluation
    assert get_ns_annotations(cls.__dict__) == {
        "a_val": "inner_type", "b_val": "global_type", "c_val": "hyper_type"
    }


def test_not_evaluated():
    class EvalCheck:
        def __class_getitem__(cls, item):
            raise KeyError("This should not be raised")
        def __getattr__(self, key):
            raise AttributeError("This should also not be raised")

    class DontEval:
        a: EvalCheck['str']  # The test is that the exception does not occur as this is not evaluated
        b: EvalCheck.missing_attribute

    get_ns_annotations(DontEval.__dict__)
