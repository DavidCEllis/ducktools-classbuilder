# Bare forwardrefs only work in 3.14 or later

from ducktools.classbuilder.annotations import get_ns_annotations
from annotationlib import ForwardRef

from pathlib import Path

global_type = int

def test_bare_forwardref():
    class Ex:
        a: str
        b: Path
        c: plain_forwardref

    annos = get_ns_annotations(Ex.__dict__)

    assert annos == {'a': str, 'b': Path, 'c': ForwardRef("plain_forwardref")}


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
    assert annos == {"a_val": str, "b_val": int, "c_val": ForwardRef("hyper_type")}

    # Correctly evaluated if it exists
    assert get_ns_annotations(cls.__dict__) == {
        "a_val": str, "b_val": int, "c_val": float
    }
