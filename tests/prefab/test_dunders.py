"""Test the non-init dunder methods"""

import pytest
from ducktools.classbuilder.prefab import attribute, prefab, SlotFields


# Classes with REPR checks
@prefab
class Coordinate:
    x: float
    y: float

@prefab
class Coordinate3D(Coordinate):
    z: float

@prefab
class CoordinateTime:
    t: float

@prefab
class Coordinate4D(CoordinateTime, Coordinate3D):
    pass

@prefab
class CoordinateNoXRepr:
    x: float = attribute(repr=False)
    y: float


@prefab
class NoXReprNoXInit:
    _type = attribute(default=None, init=False, repr=False)


# Tests
def test_repr():
    expected_repr = "Coordinate(x=1, y=2)"
    assert repr(Coordinate(1, 2)) == expected_repr


def test_repr_exclude():
    expected_repr = "<generated class CoordinateNoXRepr; y=2>"
    assert repr(CoordinateNoXRepr(1, 2)) == expected_repr


def test_repr_init_exclude():
    x = NoXReprNoXInit()
    assert x._type == None

    expected_repr = "NoXReprNoXInit()"
    assert repr(NoXReprNoXInit()) == expected_repr


def test_iter():
    @prefab(iter=True)
    class CoordinateIter:
        x: float
        y: float

    x = CoordinateIter(1, 2)

    y = list(x)
    assert y == [1, 2]


def test_iter_exclude():
    @prefab(iter=True)
    class IterExcludeEmpty:
        x: int = attribute(default=6, exclude_field=True)
        y: int = attribute(default=9, iter=False)

        def __prefab_post_init__(self, x):
            self.x = x

    assert list(IterExcludeEmpty()) == []

    @prefab(iter=True)
    class IterExclude:
        __slots__ = SlotFields(
            x=attribute(default=6, exclude_field=True),
            y=attribute(default=9, iter=False),
            z=attribute(default="LTUE", iter=True),
        )

        def __prefab_post_init__(self, x):
            self.x = x

    assert list(IterExclude()) == ["LTUE"]


def test_eq():
    x = Coordinate4D(1, 2, 3, 4)
    y = Coordinate4D(1, 2, 3, 4)

    assert (x.x, x.y, x.z, x.t) == (y.x, y.y, y.z, y.t)
    assert x == y


def test_neq():
    x = Coordinate4D(1, 2, 3, 4)
    y = Coordinate4D(5, 6, 7, 8)

    assert (x.x, x.y, x.z, x.t) != (y.x, y.y, y.z, y.t)
    assert x != y


def test_match_args():
    assert Coordinate4D.__match_args__ == ("x", "y", "z", "t")


def test_match_args_disabled():
    @prefab(match_args=False)
    class NoMatchArgs:
        x: float
        y: float

    with pytest.raises(AttributeError):
        _ = NoMatchArgs.__match_args__


def test_dunders_not_overwritten():
    @prefab
    class DundersExist:
        x: int
        y: int

        __match_args__ = ("x",)  # type: ignore

        def __init__(self, x, y):
            self.x = 2 * x
            self.y = 3 * y

        def __repr__(self):
            return "NOT_REPLACED"

        def __eq__(self, other):
            return True

        def __iter__(self):
            yield self.x


    x = DundersExist(0, 0)
    y = DundersExist(1, 1)

    # __match_args__
    assert DundersExist.__match_args__ == ("x",)

    # __init__
    assert (x.x, x.y) == (0, 0)
    assert (y.x, y.y) == (2, 3)

    # __repr__
    assert repr(x) == repr(y) == "NOT_REPLACED"

    # __eq__
    assert x == y

    # __iter__
    for item in y:
        assert item is y.x
