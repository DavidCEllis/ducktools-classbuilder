# This syntax only exists in Python 3.12 or later.
from ducktools.classbuilder.annotations import get_ns_annotations

from _type_support import matches_type


def test_312_generic():
    class X[T]:
        test_var = T  # Need access outside of class to test

        x: list[T]
        y: "list[T]"

    assert get_ns_annotations(vars(X)) == {
        "x": matches_type(list[X.test_var]),
        "y": "list[T]",
    }
