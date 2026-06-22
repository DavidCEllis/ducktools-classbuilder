from ducktools.classbuilder.methods import _AttachedMethod
from ducktools.classbuilder.prefab import prefab


def test_method_callable():
    @prefab
    class Example:
        a: int
        b: int

    eq = Example.__dict__["__eq__"]

    assert isinstance(eq, _AttachedMethod)

    ex1 = Example(1, 1)
    ex2 = Example(1, 1)
    ex3 = Example(1, 2)

    assert eq(ex1, ex2)
    assert not eq(ex1, ex3)
